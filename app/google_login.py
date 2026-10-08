"""Google (Gmail) sign-in: check the ID token that Google's sign-in button gave the browser or native app.

We verify the RS256 signature against Google's published keys, then audience (our client id), issuer, expiry and
that Google has verified the e-mail. The stable account key is the token's `sub`, not the e-mail address.
GOOGLE_CLIENT_ID may list several ids separated by commas (web first, then Android / iOS) so native apps can use the same endpoint.
"""
import logging
import os
import time

import httpx
import jwt

log = logging.getLogger("farmer.google")
CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
ISSUERS = ("accounts.google.com", "https://accounts.google.com")
_cache = {"at": 0.0, "keys": {}}


class GoogleError(Exception):
    pass


def client_ids() -> list[str]:
    return [x.strip() for x in os.environ.get("GOOGLE_CLIENT_ID", "").split(",") if x.strip()]


def _refresh(now: float) -> None:
    _cache["at"] = now   # set first: a failing fetch must not be retried on every request
    r = httpx.get(CERTS_URL, timeout=10)
    r.raise_for_status()
    _cache["keys"] = {k["kid"]: jwt.PyJWK(k).key for k in r.json()["keys"]}


def _key_for(kid: str | None):
    """Google's signing key for this token. Unknown key ids trigger at most one re-fetch per 10 minutes (30 s while we hold no keys),
    so forged tokens cannot make us hammer Google."""
    now = time.time()
    age = now - _cache["at"]
    if age > 3600 or (kid not in _cache["keys"] and age > (600 if _cache["keys"] else 30)):
        try:
            _refresh(now)
        except (httpx.HTTPError, ValueError, KeyError, jwt.PyJWTError) as e:
            log.warning("could not fetch Google signing keys: %s", type(e).__name__)
    return _cache["keys"].get(kid)


def verify(token: str) -> dict:
    ids = client_ids()
    if not ids:
        raise GoogleError("not configured")
    try:
        key = _key_for(jwt.get_unverified_header(token).get("kid"))
        if key is None:
            raise GoogleError("unknown signing key")
        claims = jwt.decode(token, key, algorithms=["RS256"], audience=ids, leeway=10,
                            options={"require": ["exp", "iat", "aud", "iss", "sub"]})
    except jwt.PyJWTError as e:
        raise GoogleError(type(e).__name__) from None
    if claims["iss"] not in ISSUERS:
        raise GoogleError("wrong issuer")
    if claims.get("email_verified") not in (True, "true") or not claims.get("email"):
        raise GoogleError("e-mail not verified")
    return {"sub": str(claims["sub"]), "email": claims["email"].lower()}
