from datetime import date
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import advice, crops, db, forecast, prices

app = FastAPI(title="Farmer App", version="0.1.0")
db.init()

Crop = str


def _crop(c: str) -> str:
    k = crops.key(c)
    if k not in crops.CROPS:
        raise HTTPException(404, f"Unknown crop '{c}'. Supported: {sorted(crops.CROPS)}")
    return k


class _Base(BaseModel):
    crop: str = Field(max_length=40)

    @field_validator("crop")
    @classmethod
    def _v(cls, v):
        if not crops.valid(v):
            raise ValueError(f"unsupported crop; choose from {sorted(crops.CROPS)}")
        return crops.key(v)


class ExpenseIn(_Base):
    date: date
    category: Literal[tuple(crops.CATEGORIES)]
    amount: float = Field(gt=0, lt=1e9)
    note: str = Field("", max_length=200)


class SaleIn(_Base):
    date: date
    qty_quintal: float = Field(gt=0, lt=1e7)
    price_per_quintal: float = Field(gt=0, lt=1e7)
    market: str = Field("", max_length=80)


class PlotIn(_Base):
    area_acre: float = Field(gt=0, lt=1e5)
    sowing_date: date | None = None
    note: str = Field("", max_length=200)


class FertIn(_Base):
    area_acre: float = Field(gt=0, lt=1e5)
    soil_n: float | None = Field(None, ge=0, le=5000)
    soil_p: float | None = Field(None, ge=0, le=1000)
    soil_k: float | None = Field(None, ge=0, le=5000)
    ph: float | None = Field(None, ge=0, le=14)


def _rows(sql, args=()):
    with db.conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def _add(table, data: dict):
    cols = ",".join(data)
    with db.conn() as c:
        cur = c.execute(f"INSERT INTO {table} ({cols}) VALUES ({','.join('?' * len(data))})",
                        [str(v) if isinstance(v, date) else v for v in data.values()])
        return cur.lastrowid


def _delete(table, id_):
    with db.conn() as c:
        if c.execute(f"DELETE FROM {table} WHERE id=?", (id_,)).rowcount == 0:
            raise HTTPException(404, "not found")
    return {"deleted": id_}


# ---- records -------------------------------------------------------------
@app.get("/api/meta")
def meta():
    return {"crops": sorted(crops.CROPS), "categories": crops.CATEGORIES}


@app.post("/api/expenses", status_code=201)
def add_expense(e: ExpenseIn):
    return {"id": _add("expenses", e.model_dump())}


@app.get("/api/expenses")
def list_expenses(crop: str | None = None):
    if crop:
        return _rows("SELECT * FROM expenses WHERE crop=? ORDER BY date DESC, id DESC", (_crop(crop),))
    return _rows("SELECT * FROM expenses ORDER BY date DESC, id DESC")


@app.delete("/api/expenses/{id_}")
def del_expense(id_: int):
    return _delete("expenses", id_)


@app.post("/api/sales", status_code=201)
def add_sale(s: SaleIn):
    return {"id": _add("sales", s.model_dump())}


@app.get("/api/sales")
def list_sales(crop: str | None = None):
    if crop:
        return _rows("SELECT * FROM sales WHERE crop=? ORDER BY date DESC, id DESC", (_crop(crop),))
    return _rows("SELECT * FROM sales ORDER BY date DESC, id DESC")


@app.delete("/api/sales/{id_}")
def del_sale(id_: int):
    return _delete("sales", id_)


@app.post("/api/plots", status_code=201)
def add_plot(p: PlotIn):
    return {"id": _add("plots", p.model_dump())}


@app.get("/api/plots")
def list_plots():
    return _rows("SELECT * FROM plots ORDER BY id DESC")


@app.delete("/api/plots/{id_}")
def del_plot(id_: int):
    return _delete("plots", id_)


# ---- prices / forecast / weather ----------------------------------------
@app.get("/api/prices/{crop}")
def get_prices(crop: str, state: str | None = None, days: int = Query(90, ge=14, le=365),
               refresh: bool = False):
    crop = _crop(crop)
    live = prices.refresh_live(crop, state) if refresh else None
    s = prices.series(crop, state, days)
    return {"crop": crop, **s, "refresh": live,
            "markets_today": prices.market_table(crop, s["source"]),
            "note": "source='demo' is synthetic sample data, NOT real market prices"
            if s["source"] == "demo" else "Agmarknet (data.gov.in) mandi prices, Rs/quintal"}


@app.get("/api/forecast/{crop}")
def get_forecast(crop: str, horizon: int = Query(14, ge=1, le=30), state: str | None = None):
    crop = _crop(crop)
    s = prices.series(crop, state, 120)
    return {"crop": crop, "source": s["source"], **forecast.forecast(s["prices"], horizon)}


@app.get("/api/weather")
def weather(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)):
    try:
        r = httpx.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 7,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum"})
        r.raise_for_status()
        return r.json()["daily"]
    except (httpx.HTTPError, KeyError, ValueError) as ex:
        raise HTTPException(502, f"weather provider unavailable: {type(ex).__name__}")


# ---- fertilizer ----------------------------------------------------------
@app.post("/api/fertilizer/advice")
def fert_advice(f: FertIn):
    return advice.fertilizer_plan(f.crop, f.area_acre, f.soil_n, f.soil_p, f.soil_k, f.ph)


# ---- dashboard -----------------------------------------------------------
@app.get("/api/dashboard")
def dashboard(crop: str | None = None):
    k = _crop(crop) if crop else None
    w, a = ("WHERE crop=?", (k,)) if k else ("", ())
    by_cat = {r["category"]: r["t"] for r in _rows(
        f"SELECT category, SUM(amount) t FROM expenses {w} GROUP BY category", a)}
    monthly = _rows(f"SELECT substr(date,1,7) month, SUM(amount) total FROM expenses {w} "
                    "GROUP BY month ORDER BY month", a)
    total_cost = sum(by_cat.values())
    sales = _rows(f"SELECT COALESCE(SUM(qty_quintal),0) q, COALESCE(SUM(qty_quintal*price_per_quintal),0) r "
                  f"FROM sales {w}", a)[0]
    acres = _rows(f"SELECT COALESCE(SUM(area_acre),0) a FROM plots {w}", a)[0]["a"]
    out = {
        "crop": k,
        "total_cost": round(total_cost, 2),
        "revenue": round(sales["r"], 2),
        "profit": round(sales["r"] - total_cost, 2),
        "quintals_sold": round(sales["q"], 2),
        "area_acre": acres,
        "cost_per_acre": round(total_cost / acres, 2) if acres else None,
        "cost_per_quintal": round(total_cost / sales["q"], 2) if sales["q"] else None,
        "avg_sale_price": round(sales["r"] / sales["q"], 2) if sales["q"] else None,
        "expense_by_category": {c: round(v, 2) for c, v in by_cat.items()},
        "monthly_expenses": monthly,
        "cost_insights": advice.cost_review(by_cat, total_cost),
    }
    if k:
        s = prices.series(k, None, 120)
        fc = forecast.forecast(s["prices"], 14)
        cur = s["prices"][-1] if s["prices"] else None
        out.update({"price_source": s["source"], "current_price": cur, "forecast": fc,
                    "markets_today": prices.market_table(k, s["source"]),
                    "sell_advice": advice.sell_advice(k, fc, out["cost_per_quintal"], cur)})
    return out


STATIC = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
