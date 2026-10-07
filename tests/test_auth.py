"""Phone login, sessions, per-farmer data isolation. Providers are mocked; nothing touches the network."""
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import auth, clock, db, main, otp_providers

T0 = 1_800_000_000
PHONE_A, PHONE_B = "9876543210", "9123456780"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))
    db.init()
    for k, v in {"FARMER_AUTH": "on", "FARMER_OTP_PROVIDER": "console", "FARMER_DEV_OTP": "1", "FARMER_SECRET": "test-secret"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(main.wx, "get", lambda lat, lon: {"ok": False, "error": "test"})
    return TestClient(main.app)


def login(client, phone=PHONE_A, channel="whatsapp"):
    r = client.post("/api/auth/request", json={"phone": phone, "channel": channel})
    assert r.status_code == 200, r.text
    v = client.post("/api/auth/verify", json={"phone": phone, "code": r.json()["dev_code"]})
    assert v.status_code == 200, v.text
    return {"Authorization": "Bearer " + v.json()["token"]}


def test_phone_normalization():
    ok = {"9876543210": "+919876543210", "98765 43210": "+919876543210", "+91 98765-43210": "+919876543210",
          "919876543210": "+919876543210", "09876543210"[1:]: "+919876543210", "+14155550123": "+14155550123"}
    for raw, want in ok.items():
        assert auth.normalize_phone(raw) == want
    for bad in ("", "12345", "5876543210", "abcdefghij", "+0123456789", "98765432101234567"):
        with pytest.raises(ValueError):
            auth.normalize_phone(bad)


def test_private_endpoints_need_sign_in_public_ones_do_not(client):
    for path in ("/api/plots", "/api/today", "/api/overview", "/api/expenses", "/api/farm", "/api/prices/maize", "/api/auth/me"):
        assert client.get(path).status_code == 401, path
    assert client.post("/api/calc/profit", json={}).status_code == 401
    for path in ("/api/meta", "/api/districts", "/api/msp", "/api/auth/config"):
        assert client.get(path).status_code == 200, path
    assert client.get("/api/plots", headers={"Authorization": "Bearer nonsense"}).status_code == 401
    cfg = client.get("/api/auth/config").json()
    assert cfg["required"] is True and set(cfg["channels"]) == {"whatsapp", "sms"}


def test_login_flow_and_logout(client):
    h = login(client)
    me = client.get("/api/auth/me", headers=h).json()
    assert me["phone"] == "+919876543210"
    assert client.get("/api/plots", headers=h).status_code == 200
    assert client.post("/api/auth/logout", headers=h).status_code == 200
    assert client.get("/api/plots", headers=h).status_code == 401           # token is dead after logout


def test_code_is_stored_hashed_and_dev_code_only_for_console_dev(client, monkeypatch):
    r = client.post("/api/auth/request", json={"phone": PHONE_A, "channel": "sms"}).json()
    code = r["dev_code"]
    with db.conn() as c:
        row = dict(c.execute("SELECT * FROM otps").fetchone())
    assert code not in map(str, row.values()) and len(row["code_hash"]) == 64
    monkeypatch.setenv("FARMER_DEV_OTP", "0")
    assert "dev_code" not in client.post("/api/auth/request", json={"phone": PHONE_B, "channel": "sms"}).json()
    monkeypatch.setenv("FARMER_DEV_OTP", "1"); monkeypatch.setenv("FARMER_OTP_PROVIDER", "twilio")
    assert client.get("/api/auth/config").json()["dev"] is False


def test_wrong_code_attempts_lock_out_and_right_code_then_fails(client):
    code = client.post("/api/auth/request", json={"phone": PHONE_A, "channel": "sms"}).json()["dev_code"]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(auth.MAX_ATTEMPTS):
        assert client.post("/api/auth/verify", json={"phone": PHONE_A, "code": wrong}).status_code == 400
    assert client.post("/api/auth/verify", json={"phone": PHONE_A, "code": code}).status_code == 429   # burned
    assert client.post("/api/auth/verify", json={"phone": PHONE_A, "code": "12345"}).status_code == 422  # not six digits


def test_expiry_cooldown_hourly_and_ip_limits(client):
    code = auth.request_code("+919876543210", "sms", "1.1.1.1", now=T0)["dev_code"]
    with pytest.raises(HTTPException) as e:
        auth.verify_code("+919876543210", code, now=T0 + auth.OTP_TTL + 1)
    assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:
        auth.request_code("+919876543210", "sms", "1.1.1.1", now=T0 + 5)             # too soon
    assert e.value.status_code == 429
    for i in range(1, auth.SENDS_PER_HOUR):                                           # 5 per hour in total
        auth.request_code("+919876543210", "sms", "1.1.1.1", now=T0 + i * 40)
    with pytest.raises(HTTPException) as e:
        auth.request_code("+919876543210", "sms", "1.1.1.1", now=T0 + 400)
    assert e.value.status_code == 429
    assert auth.request_code("+919876543210", "sms", "1.1.1.1", now=T0 + 3700)["ok"]   # an hour later it works again
    for i in range(auth.IP_SENDS_PER_HOUR):                                           # one IP, many numbers
        auth.request_code(f"+9199000000{i:02d}", "sms", "9.9.9.9", now=T0 + 10)
    with pytest.raises(HTTPException) as e:
        auth.request_code("+919900009999", "sms", "9.9.9.9", now=T0 + 20)
    assert e.value.status_code == 429


def test_only_newest_code_works(client):
    first = auth.request_code("+919876543210", "sms", "", now=T0)["dev_code"]
    second = auth.request_code("+919876543210", "sms", "", now=T0 + 31)["dev_code"]
    if first != second:
        with pytest.raises(HTTPException):
            auth.verify_code("+919876543210", first, now=T0 + 40)
    assert auth.verify_code("+919876543210", second, now=T0 + 40)[0]


def test_provider_failure_returns_502_and_leaves_no_code(client, monkeypatch):
    class Boom:
        channels = ("sms",)
        def send(self, *a): raise otp_providers.SendError("HTTPStatusError")
    monkeypatch.setattr(otp_providers, "get", lambda: Boom())
    r = client.post("/api/auth/request", json={"phone": PHONE_A, "channel": "sms"})
    assert r.status_code == 502 and "dev_code" not in r.text
    with db.conn() as c:
        assert c.execute("SELECT COUNT(*) n FROM otps").fetchone()["n"] == 0
    assert client.post("/api/auth/request", json={"phone": PHONE_A, "channel": "carrier-pigeon"}).status_code == 422


def test_session_cap_per_farmer_keeps_newest(client):
    login(client)
    with db.conn() as c:
        fid = c.execute("SELECT id FROM farmers").fetchone()["id"]
    tokens = [auth._new_session(fid, T0 + i) for i in range(auth.MAX_SESSIONS + 3)]
    with db.conn() as c:
        assert c.execute("SELECT COUNT(*) n FROM sessions WHERE farmer_id=?", (fid,)).fetchone()["n"] == auth.MAX_SESSIONS
    # the oldest tokens were dropped, the newest still work
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer " + tokens[-1]}).status_code == 200
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer " + tokens[0]}).status_code == 401


# ---------------- data isolation ----------------
def seed(client, h, crop):
    pid = client.post("/api/plots", headers=h, json={"crop": crop, "area_acre": 2, "sowing_date": clock.today().isoformat()}).json()["id"]
    eid = client.post("/api/expenses", headers=h, json={"crop": crop, "date": clock.today().isoformat(), "category": "seed", "amount": 1000}).json()["id"]
    sid = client.post("/api/sales", headers=h, json={"crop": crop, "date": clock.today().isoformat(), "qty_quintal": 2, "price_per_quintal": 2000}).json()["id"]
    aid = client.post("/api/activities", headers=h, json={"crop": crop, "plot_id": pid, "kind": "irrigation"}).json()["id"]
    return pid, eid, sid, aid


def test_farmers_only_see_their_own_data(client):
    ha, hb = login(client, PHONE_A), login(client, PHONE_B)
    pa, ea, sa, aa = seed(client, ha, "maize")
    pb, eb, sb, ab = seed(client, hb, "chilli")
    for path, key in (("/api/plots", "crop"), ("/api/expenses", "crop"), ("/api/sales", "crop"), ("/api/activities", "crop")):
        assert {r[key] for r in client.get(path, headers=ha).json()} == {"maize"}, path
        assert {r[key] for r in client.get(path, headers=hb).json()} == {"chilli"}, path
    assert [c["crop"] for c in client.get("/api/overview", headers=ha).json()["crops"]] == ["maize"]
    assert client.get("/api/dashboard", headers=hb).json()["total_cost"] == 1000
    assert [p["crop"] for p in client.get("/api/today", headers=ha).json()["plots"]] == ["maize"]
    assert client.get("/api/plan/chilli", headers=ha).json()["plot"] is None            # A has no chilli plot
    # B cannot touch A's rows
    assert client.delete(f"/api/expenses/{ea}", headers=hb).status_code == 404
    assert client.delete(f"/api/sales/{sa}", headers=hb).status_code == 404
    assert client.delete(f"/api/activities/{aa}", headers=hb).status_code == 404
    assert client.delete(f"/api/plots/{pa}", headers=hb).status_code == 404
    assert client.patch(f"/api/plots/{pa}", headers=hb, json={"area_acre": 99}).status_code == 404
    assert client.post(f"/api/plots/{pa}/harvest", headers=hb).status_code == 404
    assert client.post("/api/activities", headers=hb, json={"crop": "maize", "plot_id": pa, "kind": "harvest"}).status_code == 404
    assert client.get("/api/plots?crop=maize", headers=ha).json()[0]["status"] == "active"
    assert client.get("/api/plots?crop=maize", headers=ha).json()[0]["area_acre"] == 2


def test_farm_profile_is_per_farmer(client):
    ha, hb = login(client, PHONE_A), login(client, PHONE_B)
    client.put("/api/farm", headers=ha, json={"district": "Guntur", "lat": 16.3, "lon": 80.44})
    assert client.get("/api/farm", headers=hb).json() == {"district": "", "lat": None, "lon": None, "onboarded": False}
    assert client.get("/api/farm", headers=ha).json()["district"] == "Guntur"


def test_delete_account_removes_only_that_farmers_data(client):
    ha, hb = login(client, PHONE_A), login(client, PHONE_B)
    seed(client, ha, "maize"); seed(client, hb, "chilli")
    assert client.post("/api/auth/delete-account", headers=ha, json={"confirm": False}).status_code == 422
    assert client.post("/api/auth/delete-account", headers=ha, json={"confirm": True}).json() == {"deleted": True}
    assert client.get("/api/plots", headers=ha).status_code == 401
    with db.conn() as c:
        left = {t: c.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"] for t in (*db.OWNED_TABLES, "farmers", "sessions")}
        assert c.execute("SELECT COUNT(*) n FROM otps WHERE phone='+919876543210'").fetchone()["n"] == 0
    assert left == {"plots": 1, "expenses": 1, "sales": 1, "activities": 1, "farmers": 1, "sessions": 1}
    assert client.get("/api/plots", headers=hb).status_code == 200


def test_first_farmer_adopts_legacy_data_second_does_not(client):
    with db.conn() as c:
        c.execute("INSERT INTO plots (crop, area_acre) VALUES ('maize', 3)")
        c.execute("INSERT INTO expenses (date, crop, category, amount) VALUES ('2026-01-01','maize','seed',500)")
        c.execute("INSERT INTO farm (id, district, lat, lon, onboarded) VALUES (1,'Warangal',17.97,79.59,1)")
    ha = login(client, PHONE_A)
    assert [p["area_acre"] for p in client.get("/api/plots", headers=ha).json()] == [3]
    assert client.get("/api/farm", headers=ha).json()["district"] == "Warangal"
    assert client.get("/api/plots", headers=login(client, PHONE_B)).json() == []


def test_security_headers(client):
    r = client.get("/")
    assert "script-src 'self'" in r.headers["content-security-policy"] and r.headers["x-content-type-options"] == "nosniff"
    assert client.get("/api/meta").headers["cache-control"] == "no-store"


# ---------------- provider request shapes (mocked HTTP) ----------------
class Capture:
    def __init__(self): self.calls = []
    def __call__(self, url, **kw):
        self.calls.append((url, kw))
        return httpx.Response(200, request=httpx.Request("POST", url))


def test_twilio_sms_and_whatsapp_requests(monkeypatch):
    for k, v in {"TWILIO_ACCOUNT_SID": "ACxxx", "TWILIO_AUTH_TOKEN": "tok", "TWILIO_SMS_FROM": "+15005550006",
                 "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"}.items():
        monkeypatch.setenv(k, v)
    cap = Capture(); monkeypatch.setattr(httpx, "post", cap)
    t = otp_providers.Twilio()
    t.send("+919876543210", "123456", "sms")
    url, kw = cap.calls[-1]
    assert url == "https://api.twilio.com/2010-04-01/Accounts/ACxxx/Messages.json" and kw["auth"] == ("ACxxx", "tok")
    assert kw["data"]["To"] == "+919876543210" and kw["data"]["From"] == "+15005550006" and "123456" in kw["data"]["Body"]
    t.send("+919876543210", "123456", "whatsapp")
    d = cap.calls[-1][1]["data"]
    assert d["To"] == "whatsapp:+919876543210" and d["From"] == "whatsapp:+14155238886" and "123456" in d["Body"]
    monkeypatch.setenv("TWILIO_WHATSAPP_CONTENT_SID", "HXabc")
    t.send("+919876543210", "123456", "whatsapp")
    d = cap.calls[-1][1]["data"]
    assert d["ContentSid"] == "HXabc" and d["ContentVariables"] == '{"1": "123456"}' and "Body" not in d


def test_meta_whatsapp_request_and_error_does_not_leak(monkeypatch):
    monkeypatch.setenv("META_WA_TOKEN", "EAAtoken"); monkeypatch.setenv("META_WA_PHONE_ID", "1055")
    cap = Capture(); monkeypatch.setattr(httpx, "post", cap)
    otp_providers.MetaWhatsApp().send("+919876543210", "654321", "whatsapp")
    url, kw = cap.calls[-1]
    assert url == "https://graph.facebook.com/v20.0/1055/messages" and kw["headers"]["Authorization"] == "Bearer EAAtoken"
    body = kw["json"]
    assert body["to"] == "919876543210" and body["type"] == "template" and body["template"]["name"] == "farmer_login_code"
    assert body["template"]["components"][0]["parameters"][0]["text"] == "654321"
    assert body["template"]["components"][1]["sub_type"] == "url"

    def fail(url, **kw):
        raise httpx.HTTPStatusError("bad: 654321 EAAtoken", request=httpx.Request("POST", url), response=httpx.Response(400))
    monkeypatch.setattr(httpx, "post", fail)
    with pytest.raises(otp_providers.SendError) as e:
        otp_providers.MetaWhatsApp().send("+919876543210", "654321", "whatsapp")
    assert "654321" not in str(e.value) and "EAAtoken" not in str(e.value)


def test_allowed_channels(monkeypatch):
    monkeypatch.setenv("FARMER_OTP_PROVIDER", "meta")
    assert otp_providers.allowed_channels() == []                                   # settings missing -> nothing offered
    monkeypatch.setenv("META_WA_TOKEN", "x"); monkeypatch.setenv("META_WA_PHONE_ID", "1")
    assert otp_providers.allowed_channels() == ["whatsapp"]                         # Meta cannot send SMS
    monkeypatch.setenv("FARMER_OTP_PROVIDER", "console"); monkeypatch.setenv("FARMER_OTP_CHANNELS", "sms")
    assert otp_providers.allowed_channels() == ["sms"]
    monkeypatch.setenv("FARMER_OTP_PROVIDER", "nope")
    assert otp_providers.allowed_channels() == []
