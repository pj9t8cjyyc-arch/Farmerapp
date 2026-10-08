"""Sign in with Google (Gmail) or with a phone number and an SMS code; bearer-token sessions; per-farmer data scoping.

Safety rules implemented here:
- Google: the ID token is verified on the server (signature, audience, issuer, expiry, verified e-mail); see google_login.py;
- codes are random 6 digits, stored only as an HMAC (never in clear), valid 5 minutes, burned after 5 wrong tries;
- send limits: 30 s between sends, 5 per hour per number, 20 per hour per IP; the response never reveals whether a number is registered;
- session tokens are random 256-bit values, stored only as a SHA-256 hash, 90-day sliding expiry, at most 10 per farmer;
- FARMER_AUTH=off switches login off for single-user / self-hosted use (everything belongs to farmer 1).
"""
import hashlib
import hmac
import logging
import os
import re
import secrets
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from . import db, google_login, otp_providers

log = logging.getLogger("farmer.auth")
router = APIRouter(prefix="/api/auth")

OTP_TTL, RESEND_GAP, SENDS_PER_HOUR, IP_SENDS_PER_HOUR, MAX_ATTEMPTS = 300, 30, 5, 20, 5
SESSION_SECONDS, MAX_SESSIONS = 90 * 86400, 10
_RUNTIME_SECRET = secrets.token_hex(32)   # used only when FARMER_SECRET is not set (codes then stop working after a restart)
_warned = False


def required() -> bool:
    return os.environ.get("FARMER_AUTH", "on") != "off"


def _secret() -> bytes:
    global _warned
    s = os.environ.get("FARMER_SECRET")
    if not s and not _warned:
        log.warning("FARMER_SECRET is not set: using a temporary secret. Set it in production.")
        _warned = True
    return (s or _RUNTIME_SECRET).encode()


def _hash_code(phone: str, code: str) -> str:
    return hmac.new(_secret(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def normalize_phone(raw: str) -> str:
    """Return E.164 (+91XXXXXXXXXX for Indian 10-digit numbers) or raise ValueError."""
    s = re.sub(r"[\s\-().]", "", raw or "")
    if re.fullmatch(r"[6-9]\d{9}", s):
        return "+91" + s
    if re.fullmatch(r"(91|0091)[6-9]\d{9}", s):
        return "+91" + s[-10:]
    if re.fullmatch(r"\+[1-9]\d{7,14}", s):
        return s
    raise ValueError("invalid phone number")


def _client_ip(request: Request) -> str:
    if os.environ.get("FARMER_TRUST_PROXY") == "1" and request.headers.get("x-forwarded-for"):
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else ""


# ---------------- codes ----------------
def request_code(phone: str, ip: str, now: int | None = None) -> dict:
    now = now or int(time.time())
    if not otp_providers.sms_ready():
        raise HTTPException(503, "Phone sign-in is not available.")
    with db.conn() as c:
        last = c.execute("SELECT MAX(created) m FROM otps WHERE phone=?", (phone,)).fetchone()["m"]
        if last and now - last < RESEND_GAP:
            raise HTTPException(429, "Please wait before asking for another code.", headers={"Retry-After": str(RESEND_GAP - (now - last))})
        if c.execute("SELECT COUNT(*) n FROM otps WHERE phone=? AND created>?", (phone, now - 3600)).fetchone()["n"] >= SENDS_PER_HOUR:
            raise HTTPException(429, "Too many codes requested. Try again in an hour.")
        if ip and c.execute("SELECT COUNT(*) n FROM otps WHERE ip=? AND created>?", (ip, now - 3600)).fetchone()["n"] >= IP_SENDS_PER_HOUR:
            raise HTTPException(429, "Too many requests from this network. Try again later.")
        code = f"{secrets.randbelow(10**6):06d}"
        c.execute("UPDATE otps SET consumed=1 WHERE phone=? AND consumed=0", (phone,))   # only the newest code works
        row = c.execute("INSERT INTO otps (phone, code_hash, channel, ip, created, expires) VALUES (?,?,'sms',?,?,?)",
                        (phone, _hash_code(phone, code), ip, now, now + OTP_TTL)).lastrowid
    try:
        otp_providers.get().send(phone, code)
    except otp_providers.SendError as e:
        with db.conn() as c:
            c.execute("DELETE FROM otps WHERE id=?", (row,))
        log.error("code delivery failed: %s", e)
        raise HTTPException(502, "Could not send the code. Try Google sign-in or try again later.") from None
    out = {"ok": True, "cooldown_s": RESEND_GAP}
    if os.environ.get("FARMER_OTP_PROVIDER", "console") == "console" and os.environ.get("FARMER_DEV_OTP") == "1":
        out["dev_code"] = code   # development convenience; never enabled with a real provider
    return out


def verify_code(phone: str, code: str, now: int | None = None) -> tuple[str, int, bool]:
    """Check the code; returns (session token, farmer id, is_new_farmer)."""
    now = now or int(time.time())
    with db.conn() as c:
        row = c.execute("SELECT * FROM otps WHERE phone=? AND consumed=0 AND expires>? ORDER BY id DESC LIMIT 1", (phone, now)).fetchone()
        if not row:
            raise HTTPException(400, "That code has expired. Ask for a new one.")
        if row["attempts"] >= MAX_ATTEMPTS:
            raise HTTPException(429, "Too many wrong attempts. Ask for a new code.")
        if not hmac.compare_digest(row["code_hash"], _hash_code(phone, code)):
            c.execute("UPDATE otps SET attempts=attempts+1 WHERE id=?", (row["id"],))
            c.commit()
            raise HTTPException(400, "Wrong code.")
        c.execute("UPDATE otps SET consumed=1 WHERE id=?", (row["id"],))
    fid, new = _get_or_create_farmer(now, phone=phone)
    return _new_session(fid, now), fid, new


def google_login_session(credential: str, now: int | None = None) -> tuple[str, int, bool, str]:
    """Verify a Google ID token; returns (session token, farmer id, is_new_farmer, e-mail)."""
    now = now or int(time.time())
    try:
        g = google_login.verify(credential)
    except google_login.GoogleError as e:
        if str(e) == "not configured":
            raise HTTPException(503, "Google sign-in is not available.") from None
        log.info("Google sign-in rejected: %s", e)
        raise HTTPException(401, "Google sign-in failed.") from None
    fid, new = _get_or_create_farmer(now, google=g)
    return _new_session(fid, now), fid, new, g["email"]


# ---------------- farmers and sessions ----------------
def claim_legacy(c, fid: int) -> None:
    """Data created before accounts existed (farmer_id NULL) is adopted by the first farmer."""
    for t in db.OWNED_TABLES:
        c.execute(f"UPDATE {t} SET farmer_id=? WHERE farmer_id IS NULL", (fid,))
    old = c.execute("SELECT district, lat, lon, onboarded FROM farm WHERE id=1").fetchone()
    if old:
        c.execute("INSERT OR IGNORE INTO farmer_farm (farmer_id, district, lat, lon, onboarded) VALUES (?,?,?,?,?)",
                  (fid, old["district"], old["lat"], old["lon"], old["onboarded"]))


def _get_or_create_farmer(now: int, *, phone: str | None = None, google: dict | None = None) -> tuple[int, bool]:
    col, val = ("phone", phone) if phone else ("google_sub", google["sub"])   # col is one of two constants
    with db.conn() as c:
        row = c.execute(f"SELECT id FROM farmers WHERE {col}=?", (val,)).fetchone()
        if row:
            if google:
                c.execute("UPDATE farmers SET email=? WHERE id=?", (google["email"], row["id"]))
            return row["id"], False
        first = c.execute("SELECT COUNT(*) n FROM farmers").fetchone()["n"] == 0
        fid = c.execute("INSERT INTO farmers (phone, email, google_sub, created_at) VALUES (?,?,?,?)",
                        (phone, google and google["email"], google and google["sub"], now)).lastrowid
        if first:
            claim_legacy(c, fid)
        return fid, True


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _new_session(fid: int, now: int) -> str:
    token = secrets.token_urlsafe(32)
    with db.conn() as c:
        c.execute("INSERT INTO sessions (token_hash, farmer_id, created, expires, last_used) VALUES (?,?,?,?,?)",
                  (_token_hash(token), fid, now, now + SESSION_SECONDS, now))
        c.execute("DELETE FROM sessions WHERE farmer_id=? AND token_hash NOT IN "
                  "(SELECT token_hash FROM sessions WHERE farmer_id=? ORDER BY last_used DESC LIMIT ?)", (fid, fid, MAX_SESSIONS))
    return token


def _local_farmer() -> int:
    """Login switched off: everything belongs to farmer 1 (created on first use, adopting any legacy data)."""
    with db.conn() as c:
        if not c.execute("SELECT 1 FROM farmers WHERE id=1").fetchone():
            c.execute("INSERT INTO farmers (id, phone, created_at) VALUES (1, 'local', ?)", (int(time.time()),))
            claim_legacy(c, 1)
    return 1


def farmer_id(authorization: str | None = Header(None)) -> int:
    """FastAPI dependency: the signed-in farmer's id, or 401."""
    if not required():
        return _local_farmer()
    token = authorization[7:] if authorization and authorization.lower().startswith("bearer ") else None
    if token:
        now = int(time.time())
        with db.conn() as c:
            row = c.execute("SELECT farmer_id, expires FROM sessions WHERE token_hash=?", (_token_hash(token),)).fetchone()
            if row and row["expires"] > now:
                c.execute("UPDATE sessions SET last_used=?, expires=? WHERE token_hash=?", (now, now + SESSION_SECONDS, _token_hash(token)))
                return row["farmer_id"]
    raise HTTPException(401, "Please sign in.", headers={"WWW-Authenticate": "Bearer"})


def delete_account(fid: int) -> None:
    with db.conn() as c:
        for t in (*db.OWNED_TABLES, "sessions"):
            c.execute(f"DELETE FROM {t} WHERE farmer_id=?", (fid,))
        c.execute("DELETE FROM farmer_farm WHERE farmer_id=?", (fid,))
        phone = c.execute("SELECT phone FROM farmers WHERE id=?", (fid,)).fetchone()
        c.execute("DELETE FROM farmers WHERE id=?", (fid,))
        if phone and phone["phone"]:
            c.execute("DELETE FROM otps WHERE phone=?", (phone["phone"],))


# ---------------- routes ----------------
class RequestIn(BaseModel):
    phone: str = Field(max_length=24)


class GoogleIn(BaseModel):
    credential: str = Field(min_length=20, max_length=4096)


class VerifyIn(BaseModel):
    phone: str = Field(max_length=24)
    code: str = Field(pattern=r"^\d{6}$")


class DeleteIn(BaseModel):
    confirm: bool = False


@router.get("/config")
def config():
    ids = google_login.client_ids()
    return {"required": required(), "phone": otp_providers.sms_ready(), "google_client_id": ids[0] if ids else None,
            "dev": os.environ.get("FARMER_OTP_PROVIDER", "console") == "console" and os.environ.get("FARMER_DEV_OTP") == "1"}


@router.post("/request")
def request_otp(body: RequestIn, request: Request):
    try:
        phone = normalize_phone(body.phone)
    except ValueError:
        raise HTTPException(422, "Enter a valid mobile number.") from None
    return request_code(phone, _client_ip(request))


@router.post("/verify")
def verify(body: VerifyIn):
    try:
        phone = normalize_phone(body.phone)
    except ValueError:
        raise HTTPException(422, "Enter a valid mobile number.") from None
    token, fid, new = verify_code(phone, body.code)
    return {"token": token, "farmer": {"id": fid, "phone": phone}, "new": new}


@router.post("/google")
def google(body: GoogleIn):
    token, fid, new, email = google_login_session(body.credential)
    return {"token": token, "farmer": {"id": fid, "email": email}, "new": new}


@router.get("/me")
def me(fid: int = Depends(farmer_id)):
    with db.conn() as c:
        return dict(c.execute("SELECT id, phone, email FROM farmers WHERE id=?", (fid,)).fetchone())


@router.post("/logout")
def logout(authorization: str | None = Header(None), fid: int = Depends(farmer_id)):
    if authorization and authorization.lower().startswith("bearer "):
        with db.conn() as c:
            c.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(authorization[7:]),))
    return {"ok": True}


@router.post("/delete-account")
def delete_me(body: DeleteIn, fid: int = Depends(farmer_id)):
    if not body.confirm:
        raise HTTPException(422, "confirm must be true")
    delete_account(fid)
    return {"deleted": True}
