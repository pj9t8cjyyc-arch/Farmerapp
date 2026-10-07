"""Ways to deliver a login code. Pick one with FARMER_OTP_PROVIDER:

console : development only. Nothing is sent; with FARMER_DEV_OTP=1 the code is returned to the app and logged.
twilio  : SMS and WhatsApp through Twilio's Messages API.
meta    : WhatsApp through Meta's WhatsApp Cloud API (approved 'authentication' template with a copy-code button).

The code is never logged by the real providers. These classes were written against the providers' public docs
and have only been tested with a mocked HTTP layer; try them with your own credentials before launch.
"""
import json
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
    channels = ("whatsapp", "sms")

    def send(self, phone: str, code: str, channel: str) -> None:
        if os.environ.get("FARMER_DEV_OTP") == "1":
            log.warning("DEV login code for %s via %s: %s", phone, channel, code)


class Twilio:
    channels = ("whatsapp", "sms")

    def __init__(self):
        self.sid, self.token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]

    def send(self, phone: str, code: str, channel: str) -> None:
        data = {}
        if channel == "whatsapp":
            data["From"], data["To"] = os.environ["TWILIO_WHATSAPP_FROM"], f"whatsapp:{phone}"
            content = os.environ.get("TWILIO_WHATSAPP_CONTENT_SID")   # approved template (needed outside the 24-hour window)
            if content:
                data["ContentSid"], data["ContentVariables"] = content, json.dumps({"1": code})
            else:
                data["Body"] = SMS_TEXT.format(code=code)
        else:
            data["To"], data["Body"] = phone, os.environ.get("FARMER_SMS_TEMPLATE", SMS_TEXT).format(code=code)
            if os.environ.get("TWILIO_MESSAGING_SERVICE_SID"):
                data["MessagingServiceSid"] = os.environ["TWILIO_MESSAGING_SERVICE_SID"]
            else:
                data["From"] = os.environ["TWILIO_SMS_FROM"]
        _post(f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json", data=data, auth=(self.sid, self.token))


class MetaWhatsApp:
    channels = ("whatsapp",)

    def __init__(self):
        self.token, self.phone_id = os.environ["META_WA_TOKEN"], os.environ["META_WA_PHONE_ID"]
        self.template, self.lang = os.environ.get("META_WA_TEMPLATE", "farmer_login_code"), os.environ.get("META_WA_LANG", "en")

    def send(self, phone: str, code: str, channel: str) -> None:
        body = {"messaging_product": "whatsapp", "to": phone.lstrip("+"), "type": "template",
                "template": {"name": self.template, "language": {"code": self.lang}, "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": code}]},
                    {"type": "button", "sub_type": "url", "index": "0", "parameters": [{"type": "text", "text": code}]}]}}
        _post(f"https://graph.facebook.com/v20.0/{self.phone_id}/messages", json=body, headers={"Authorization": f"Bearer {self.token}"})


def get():
    name = os.environ.get("FARMER_OTP_PROVIDER", "console")
    cls = {"console": Console, "twilio": Twilio, "meta": MetaWhatsApp}.get(name)
    if cls is None:
        raise SendError(f"unknown provider {name}")
    try:
        return cls()
    except KeyError as e:   # a required environment setting is missing
        raise SendError(f"missing setting {e.args[0]}") from None


def allowed_channels() -> list[str]:
    """Channels offered to farmers: what the provider supports, optionally narrowed by FARMER_OTP_CHANNELS."""
    try:
        have = list(get().channels)
    except SendError:
        have = []
    want = [c.strip() for c in os.environ.get("FARMER_OTP_CHANNELS", "whatsapp,sms").split(",") if c.strip()]
    return [c for c in want if c in have]
