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

## Features
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
