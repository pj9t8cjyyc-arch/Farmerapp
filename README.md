# Farmer App

Track expenses, sales and profit per crop; see market prices, a short-term price
forecast, and fertilizer / sell-hold advice on one dashboard.

## Run
```bash
pip install -r requirements.txt
export DATA_GOV_API_KEY=...    # optional; free key from data.gov.in -> live Agmarknet mandi prices
uvicorn app.main:app --reload  # open http://localhost:8000
pytest
```
Data is stored in SQLite (`FARMER_DB`, default `./farmer.db`).

## Farm assistant (v0.2)
- **One-minute setup** (first run): language, place (GPS or district), crops by picture, then per crop: acres (stepper), planting date (chips), water source, last watering. Season (kharif/rabi/summer) is worked out from the planting date.
- **Today screen**: weather now + 7 days, alerts (heavy rain, heat), and the top things to do with one-tap Done / Watered / Later (with undo).
- **Crop plan**: growth stage and progress, fertilizer schedule with product quantities for the plot's area, watering advice from a soil-water balance (live ET0 and rain, crop coefficient by stage), key watering windows, harvest window.
- **Live data**: weather via Open-Meteo (30-minute cache, stale fallback); mandi prices via Agmarknet refreshed every `FARMER_REFRESH_MINUTES` (default 180) when `DATA_GOV_API_KEY` is set; the app refreshes itself every 5 minutes and when reopened. Agmarknet publishes daily, so "real time" for prices means as soon as the market publishes.
- **Knowledge base**: `app/knowledge/crops.json` holds every crop's stages, fertilizer split and watering rules, flagged `reviewed: false` until an agriculture officer signs off. `knowledge.problems()` (run by the tests) checks it after every edit.
- `FARMER_SAMPLE_WEATHER=1` runs with clearly-labelled sample weather (offline demos).

## Features
- **Telugu / English / Both** language switch across the UI and all server advice (`text` + `text_te`).
- **Profit calculator** (`POST /api/calc/profit`): per-acre and per-quintal profit, ROI, break-even, price for a target profit, profit table at other prices, MSP shortcut (`app/msp.json`).
- **Installable PWA** (offline shell) and a Capacitor wrapper for Android/iOS: see `docs/MOBILE.md`.
- **Phone-first layout**: crop tabs with pictures at the top, section tabs (Summary / Profit / Prices / Expenses / Fertilizer) in a bottom bar, and crop swapping by tap, ‹ › arrows, swipe or arrow keys. The open section stays the same when you swap crops.
- **One farmer, many crops**: sticky crop tabs (with profit/loss dot) to swap instantly, an **All crops** overview with one card per crop (profit, cost, price now, 14-day trend), per-crop plots/sowing dates, and each crop remembers its own calculator numbers. `GET /api/overview` serves the cards.
- **Expenses / sales / plots** per crop (chilli, onion, tomato, paddy, wheat, cotton, maize, groundnut, turmeric); the crop picker drives the whole dashboard.
- **Dashboard**: cost, revenue, profit, cost/acre, cost/quintal, category + monthly charts, per-market prices.
- **Prices**: Agmarknet via data.gov.in (`/api/prices/{crop}?refresh=true`). Without an API key or enough live history (14+ days) the app falls back to **synthetic demo data, clearly badged "DEMO" and never mixed with live data**. The daily API returns the current day, so live history builds up as you refresh (e.g. a daily cron).
- **Forecast**: damped-trend Holt smoothing on daily mean modal price, with a 95% band and last-week backtest error (MAPE) shown. It uses price history only (no weather/arrivals/policy), so treat it as a trend indicator, not a guarantee.
- **Fertilizer**: NPK plan (DAP/Urea/MOP kg) adjusted by soil-test ratings; generic guideline doses, confirm with your local KVK.
- **Advice**: sell/hold (compares forecast vs model error and your cost per quintal) and cost-share warnings.
- `/api/weather?lat=&lon=` proxies Open-Meteo (7-day outlook).

## Caveats
- No login: single-user. Run on a trusted network or add auth before exposing publicly.
- Agmarknet commodity names and field mapping (`app/crops.py`, `app/prices.py`) follow the public schema but were not verified against the live API from the build environment. Test with your key.
- Next ideas: multi-farmer auth, Telugu/Hindi UI, MSP data, arrivals + weather features in the model, yield tracking.

## Shareable preview
`python scripts/build_preview.py preview.html` bundles the real site plus snapshots from the real backend (sample farm) into one read-only HTML page.
