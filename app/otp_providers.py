"""Ways to deliver the SMS login code. Pick one with FARMER_OTP_PROVIDER:

console : development only. Nothing is sent; with FARMER_DEV_OTP=1 the code is returned to the app and logged.
twilio  : SMS through Twilio's Messages API.

The code is never logged by the real provider. The Twilio class was written against its public docs
and has only been tested with a mocked HTTP layer; try it with your own credentials before launch.
"""
import logging
import os

import httpx

log = logging.getLogger("farmer.otp")
SMS_TEXT = "{code} is your Farmer App login code. It is valid for 5 minutes. Do not share it with anyone."


class SendError(Exception):
    pass


def _post(url: str, **kw):
    try:
        r = httpx.post(url, timeout=10, **kw)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise SendError(type(e).__name__) from None   # never include the response (it may echo the code or credentials)


class Console:
    def send(self, phone: str, code: str) -> None:
        if os.environ.get("FARMER_DEV_OTP") == "1":
            log.warning("DEV login code for %s: %s", phone, code)


class Twilio:
    def __init__(self):
        self.sid, self.token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]

    def send(self, phone: str, code: str) -> None:
        data = {"To": phone, "Body": os.environ.get("FARMER_SMS_TEMPLATE", SMS_TEXT).format(code=code)}
        if os.environ.get("TWILIO_MESSAGING_SERVICE_SID"):
            data["MessagingServiceSid"] = os.environ["TWILIO_MESSAGING_SERVICE_SID"]
        else:
            data["From"] = os.environ["TWILIO_SMS_FROM"]
        _post(f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json", data=data, auth=(self.sid, self.token))


def get():
    name = os.environ.get("FARMER_OTP_PROVIDER", "console")
    cls = {"console": Console, "twilio": Twilio}.get(name)
    if cls is None:
        raise SendError(f"unknown provider {name}")
    try:
        return cls()
    except KeyError as e:   # a required environment setting is missing
        raise SendError(f"missing setting {e.args[0]}") from None


def sms_ready() -> bool:
    """True when the configured provider can send (so the app may offer the phone-number option)."""
    try:
        get()
        return True
    except SendError:
        return False
