# Web first, then Android and iOS

One codebase serves all three:

| Layer | Used by | Notes |
|---|---|---|
| JSON API (`/api/*`, FastAPI) | web, Android, iOS | All logic (profit calc, forecast, advice, Telugu + English text) lives here, so apps never re-implement it. |
| Web UI (`app/static`) | browser, installable PWA, native wrapper | Mobile-first, Telugu / English / Both, works offline for the shell (service worker). |

## Step 1: publish the website (HTTPS required for PWA install and for store apps)
Run `uvicorn app.main:app --host 0.0.0.0` behind HTTPS (any VPS, Render, Railway, Fly.io...).
Phones can then use "Add to Home screen" (PWA) immediately.

## Step 2: store apps with Capacitor (same web code)
```bash
cd mobile && npm install
# point the app at your hosted API: edit app/static/config.js -> window.API_BASE = "https://your.domain";
# set FARMER_CORS_ORIGINS on the server if you use custom schemes/domains
npx cap add android && npx cap add ios      # once
npx cap sync && npx cap open android        # Android Studio -> build AAB -> Play Console
npx cap open ios                            # Xcode (needs a Mac) -> App Store Connect
```
Change `appId` in `mobile/capacitor.config.json` to your own reverse-domain id before publishing.

Not done / needs you: the native projects were NOT generated or built in this repo (needs Android Studio / Xcode),
store accounts (Google Play one-time fee, Apple Developer yearly fee), app icons/splash PNGs, privacy policy URL.

## Before real users
- Add login (per-farmer data). Today the API is single-user with no authentication.
- Have a native Telugu speaker review the wording in `app/static/i18n.js` and `app/i18n.py`.
- Verify MSP values in `app/msp.json` and the live Agmarknet mapping with your data.gov.in key.
