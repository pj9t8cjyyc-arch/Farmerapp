# Sign-in with a mobile number

Farmers sign in with their phone number and a 6-digit code sent on **WhatsApp** or by **SMS**. No passwords.
Every farmer's crops, expenses, sales and history are private to their account.

## Which channel?
| | WhatsApp | SMS |
|---|---|---|
| Reach | Most farmers already use it | Works on every phone |
| India set-up | Meta business account + an approved *authentication* template | TRAI **DLT registration** (sender ID and message template) through your SMS provider; usually the slowest step |
| Cost | Per-message price set by Meta/your provider | Per-SMS price set by your provider |
| Later reminders | Same channel can carry them (needs approved templates) | Possible, but each reminder needs a registered template |

Recommendation: offer **WhatsApp first and SMS as the fallback** (`FARMER_OTP_CHANNELS=whatsapp,sms`). Check each provider's current prices and approval times yourself; they change.

## Switching it on
Set environment variables on the server, then restart.

Always:
```
FARMER_SECRET=<long random string>      # signs login codes; keep it secret and stable
FARMER_TRUST_PROXY=1                    # only if you run behind a proxy that sets X-Forwarded-For
FARMER_CORS_ORIGINS=https://yourdomain  # plus capacitor://localhost for the store apps
```

### Option A: Twilio (SMS and WhatsApp)
```
FARMER_OTP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...  TWILIO_AUTH_TOKEN=...
TWILIO_SMS_FROM=+1...            # or TWILIO_MESSAGING_SERVICE_SID=MG...
TWILIO_WHATSAPP_FROM=whatsapp:+1...
TWILIO_WHATSAPP_CONTENT_SID=HX...   # approved template with one variable {{1}} = the code
FARMER_SMS_TEMPLATE="<your DLT-registered text with {code}>"   # India: must match the registered template exactly
```

### Option B: Meta WhatsApp Cloud API (WhatsApp only)
```
FARMER_OTP_PROVIDER=meta
META_WA_TOKEN=...  META_WA_PHONE_ID=...
META_WA_TEMPLATE=farmer_login_code  META_WA_LANG=en   # approved authentication template with a copy-code button
```

### Development
```
FARMER_OTP_PROVIDER=console  FARMER_DEV_OTP=1
```
Nothing is sent; the code is shown on screen as "Test code". Never use this in production.

### Single-user / self-hosted
`FARMER_AUTH=off` turns sign-in off and everything belongs to one farmer.

## What protects farmers
- Codes: random, valid 5 minutes, stored only as an HMAC, burned after 5 wrong tries; the newest code wins.
- Limits: 30 s between codes, 5 per hour per number, 20 per hour per IP; answers never reveal whether a number is registered.
- Sessions: random 256-bit tokens stored hashed, 90 days sliding, max 10 per farmer, "Log out" ends them.
- Data: every query is filtered by farmer id; plots and activities are ownership-checked (tested with two farmers).
- Account deletion: *My account → Delete my account and data* removes everything for that farmer (required by app stores).
- Headers: strict Content-Security-Policy, `nosniff`, `no-store` on API answers.

## Not verified here
The Twilio and Meta requests follow the providers' public documentation and are tested only against a mocked HTTP layer.
Send yourself a real code on each channel before launch. Template names, content SIDs and DLT registration are yours to set up.
