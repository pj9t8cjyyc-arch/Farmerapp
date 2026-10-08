# Signing in

Farmers sign in one of two ways. No passwords.

1. **Google (Gmail)**: one tap with their Google account.
2. **Mobile number + SMS code**: a 6-digit code sent by SMS.

Every farmer's crops, expenses, sales and history are private to their account. WhatsApp is not used.

**The two ways make two separate accounts.** The app does not link a Google account to a phone number, so someone who signs in with Google on one phone and with a number on another sees different data. Tell farmers to pick one way and keep to it. Linking is a possible later feature.

## Switching it on
Set environment variables on the server, then restart.

Always:
```
FARMER_SECRET=<long random string>      # signs login codes; keep it secret and stable
FARMER_TRUST_PROXY=1                    # only if you run behind a proxy that sets X-Forwarded-For
FARMER_CORS_ORIGINS=https://yourdomain  # plus capacitor://localhost for the store apps
```

### Google
1. Google Cloud console -> *APIs & Services* -> *Credentials* -> *Create credentials* -> *OAuth client ID* -> type **Web application**.
2. Add your site address (for example `https://yourdomain`, and `http://localhost:8000` for testing) under **Authorized JavaScript origins**.
3. Configure the OAuth consent screen (app name, support e-mail, privacy-policy link). Only name, e-mail and profile are requested.
```
GOOGLE_CLIENT_ID=1234-abc.apps.googleusercontent.com
# native apps later: add their client ids after the web one, comma separated
# GOOGLE_CLIENT_ID=1234-web.apps.googleusercontent.com,5678-android.apps.googleusercontent.com,9012-ios.apps.googleusercontent.com
```
Without `GOOGLE_CLIENT_ID` the Google button is hidden and the site's Content-Security-Policy stays closed to Google.

How it works: Google's button gives the browser a signed ID token; the server checks the signature against Google's published keys, that it was issued for **our** client id, by Google, not expired, and that Google verified the e-mail. The account is keyed on Google's permanent user id (`sub`), not the e-mail, so a changed address does not create a new account.

**Android / iOS apps:** Google does not allow its web sign-in button inside an embedded WebView, so the Capacitor apps need a native Google sign-in plugin that sends the resulting ID token to the same `POST /api/auth/google` endpoint (add the Android and iOS client ids to `GOOGLE_CLIENT_ID`). Mobile-number sign-in works unchanged in the apps.

### Mobile number + SMS (Twilio)
```
FARMER_OTP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...  TWILIO_AUTH_TOKEN=...
TWILIO_SMS_FROM=+1...            # or TWILIO_MESSAGING_SERVICE_SID=MG...
FARMER_SMS_TEMPLATE="<your DLT-registered text with {code}>"   # India: must match the registered template exactly
```
In India, SMS needs TRAI **DLT registration** (sender ID and message template) through your SMS provider; this is usually the slowest step. Check the provider's current prices yourself. If the provider settings are missing, the phone option is hidden and only Google is offered.

### Development
```
FARMER_OTP_PROVIDER=console  FARMER_DEV_OTP=1
```
Nothing is sent; the code is shown on screen as "Test code". Never use this in production.

### Single-user / self-hosted
`FARMER_AUTH=off` turns sign-in off and everything belongs to one farmer.

## What protects farmers
- Google: tokens are verified on the server (signature, audience, issuer, expiry, verified e-mail); Google's signing keys are cached and a forged key id cannot make the server re-fetch more than once per 10 minutes.
- SMS codes: random, valid 5 minutes, stored only as an HMAC, burned after 5 wrong tries; the newest code wins.
- Limits on SMS: 30 s between codes, 5 per hour per number, 20 per hour per IP; answers never reveal whether a number is registered.
- Sessions (both ways): random 256-bit tokens stored hashed, 90 days sliding, max 10 per farmer, "Log out" ends them.
- Data: every query is filtered by farmer id; plots and activities are ownership-checked (tested with two farmers).
- Account deletion: *My account -> Delete my account and data* removes everything for that farmer (required by app stores).
- Headers: strict Content-Security-Policy, `nosniff`, `no-store` on API answers.

## Not verified here
- Google sign-in was tested with tokens signed by a throw-away key and a stand-in for Google's script. It has **not** been run against Google itself (the build environment has no internet). Test with your own client id before launch.
- The Twilio request follows the provider's public documentation and is tested only against a mocked HTTP layer. Send yourself a real code before launch. DLT registration and the sender are yours to set up.
- ID tokens are valid for up to an hour and are not bound to a one-time nonce; always serve the site over HTTPS.
