"""Price providers.

live : Agmarknet daily mandi prices via data.gov.in (needs DATA_GOV_API_KEY).
demo : deterministic synthetic series so the app works offline. Always labelled
       source='demo' and never mixed with live data in a forecast.
"""
import hashlib
import math
import os
from datetime import date, datetime, timedelta

import httpx

from . import crops, db

AGMARK_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
DEMO_MARKETS = [("Telangana", "Warangal"), ("Andhra Pradesh", "Guntur"),
                ("Karnataka", "Hubli"), ("Maharashtra", "Nashik")]
MIN_POINTS = 14


def _seed(*parts) -> float:
    h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(h[:4], "big") / 2**32  # [0,1)


def seed_demo(crop: str, days: int = 120) -> int:
    """Idempotently generate `days` of synthetic daily prices per demo market."""
    base = crops.CROPS[crop][1]
    today = date.today()
    with db.conn() as c:
        if c.execute("SELECT 1 FROM price_history WHERE crop=? AND source='demo' AND date=? LIMIT 1",
                     (crop, today.isoformat())).fetchone():
            return 0
    rows = []
    for state, market in DEMO_MARKETS:
        mk = 0.92 + 0.16 * _seed(crop, market)
        for i in range(days):
            d = today - timedelta(days=days - 1 - i)
            season = 0.10 * math.sin(2 * math.pi * (d.timetuple().tm_yday / 365.0))
            trend = 0.0007 * (i - days / 2)
            noise = 0.03 * (_seed(crop, market, d.isoformat()) - 0.5)
            modal = round(base * mk * (1 + season + trend + noise), 2)
            rows.append((d.isoformat(), crop, state, market, "", round(modal * .93, 2),
                         round(modal * 1.07, 2), modal, "demo"))
    with db.conn() as c:
        c.executemany("INSERT OR REPLACE INTO price_history VALUES (?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def refresh_live(crop: str, state: str | None = None, limit: int = 500) -> dict:
    """Pull today's mandi prices from Agmarknet; returns {'ok', 'rows', 'error'}."""
    key = os.environ.get("DATA_GOV_API_KEY")
    if not key:
        return {"ok": False, "rows": 0, "error": "DATA_GOV_API_KEY not set"}
    params = {"api-key": key, "format": "json", "limit": limit,
              "filters[commodity]": crops.CROPS[crop][0]}
    if state:
        params["filters[state]"] = state
    try:
        r = httpx.get(AGMARK_URL, params=params, timeout=20)
        r.raise_for_status()
        records = r.json().get("records", [])
    except (httpx.HTTPError, ValueError) as e:
        return {"ok": False, "rows": 0, "error": f"{type(e).__name__}: {e}"}
    rows = []
    for x in records:
        try:
            d = datetime.strptime(x["arrival_date"], "%d/%m/%Y").date().isoformat()
            modal = float(x["modal_price"])
        except (KeyError, ValueError, TypeError):
            continue
        if modal <= 0:
            continue
        rows.append((d, crop, x.get("state", ""), x.get("market", ""), x.get("variety", ""),
                     _f(x.get("min_price")), _f(x.get("max_price")), modal, "live"))
    with db.conn() as c:
        c.executemany("INSERT OR REPLACE INTO price_history VALUES (?,?,?,?,?,?,?,?,?)", rows)
    return {"ok": True, "rows": len(rows), "error": None}


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def series(crop: str, state: str | None = None, days: int = 120) -> dict:
    """Daily mean modal price. Uses live data if >= MIN_POINTS days, else demo."""
    since = (date.today() - timedelta(days=days)).isoformat()
    out = {}
    for source in ("live", "demo"):
        if source == "demo":
            seed_demo(crop)
        q = ("SELECT date, AVG(modal_price) p, COUNT(*) n FROM price_history "
             "WHERE crop=? AND source=? AND date>=?")
        args = [crop, source, since]
        if state:
            q += " AND state=?"
            args.append(state)
        q += " GROUP BY date ORDER BY date"
        with db.conn() as c:
            rows = c.execute(q, args).fetchall()
        if len(rows) >= MIN_POINTS or source == "demo":
            out = {"source": source, "dates": [r["date"] for r in rows],
                   "prices": [round(r["p"], 2) for r in rows],
                   "markets": [r["n"] for r in rows]}
            break
    return out


def market_table(crop: str, source: str) -> list[dict]:
    """Latest price per market (best place to sell right now)."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT state, market, date, AVG(modal_price) modal, MIN(min_price) lo, MAX(max_price) hi "
            "FROM price_history WHERE crop=? AND source=? AND date=("
            " SELECT MAX(date) FROM price_history WHERE crop=? AND source=?) "
            "GROUP BY state, market ORDER BY modal DESC", (crop, source, crop, source)).fetchall()
    return [{k: (round(r[k], 2) if isinstance(r[k], float) else r[k]) for k in r.keys()} for r in rows]
