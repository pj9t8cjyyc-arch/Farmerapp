import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import advice, auth, clock, crops, db, engine, forecast, places, prices
from . import weather as wx

_Date = date  # alias: a model field called "date" would shadow the type inside its own class body
REFRESH_MINUTES = int(os.environ.get("FARMER_REFRESH_MINUTES", "180"))


async def _refresh_prices_forever():
    """Real-time prices: when a data.gov.in key is set, pull fresh mandi prices for every crop the farmer grows."""
    while True:
        with db.conn() as c:
            grown = [r["crop"] for r in c.execute("SELECT DISTINCT crop FROM plots WHERE status='active'")]
        for k in grown:
            await asyncio.to_thread(prices.refresh_live, k)
        await asyncio.sleep(REFRESH_MINUTES * 60)


@asynccontextmanager
async def lifespan(_app):
    task = asyncio.create_task(_refresh_prices_forever()) if os.environ.get("DATA_GOV_API_KEY") else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Farmer App", version="0.2.0", lifespan=lifespan)
db.init()

# Native (Capacitor) apps call a hosted API from these origins; override for your own domains.
_origins = os.environ.get("FARMER_CORS_ORIGINS", "capacitor://localhost,http://localhost,https://localhost")
app.add_middleware(CORSMiddleware, allow_origins=[o for o in _origins.split(",") if o],
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type", "Authorization"])

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
       "frame-ancestors 'none'; base-uri 'none'; form-action 'self'")


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"
    if not request.url.path.startswith(("/docs", "/redoc", "/openapi")):
        resp.headers["Content-Security-Policy"] = CSP
    if request.url.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


public = APIRouter()                                            # no sign-in needed: static lists
private = APIRouter(dependencies=[Depends(auth.farmer_id)])      # everything else needs a signed-in farmer
Farmer = Depends(auth.farmer_id)
_last_refresh: dict[str, float] = {}

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


Water = Literal["rainfed", "borewell", "canal", "drip"]


class PlotIn(_Base):
    area_acre: float = Field(gt=0, lt=1e5)
    sowing_date: date | None = None  # planting date: sowing, or transplanting for transplanted crops
    irrigation: Water = "borewell"
    soil_n: float | None = Field(None, ge=0, le=5000)
    soil_p: float | None = Field(None, ge=0, le=1000)
    soil_k: float | None = Field(None, ge=0, le=5000)
    ph: float | None = Field(None, ge=0, le=14)
    note: str = Field("", max_length=200)
    last_watered_on: _Date | None = None  # logged as a first irrigation activity


class PlotPatch(BaseModel):
    area_acre: float | None = Field(None, gt=0, lt=1e5)
    sowing_date: date | None = None
    irrigation: Water | None = None
    soil_n: float | None = Field(None, ge=0, le=5000)
    soil_p: float | None = Field(None, ge=0, le=1000)
    soil_k: float | None = Field(None, ge=0, le=5000)
    ph: float | None = Field(None, ge=0, le=14)


class ActivityIn(_Base):
    kind: Literal["irrigation", "fertilizer", "spray", "harvest", "other"]
    date: _Date | None = None
    plot_id: int | None = None
    task_key: str = Field("", max_length=40)
    qty: float | None = Field(None, ge=0, lt=1e7)
    unit: str = Field("", max_length=12)
    note: str = Field("", max_length=200)


class FarmIn(BaseModel):
    district: str = Field("", max_length=60)
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)


class OnboardCrop(_Base):
    area_acre: float = Field(gt=0, lt=1e5)
    planted_on: date | None = None
    irrigation: Water = "borewell"
    last_watered_on: _Date | None = None


class OnboardIn(FarmIn):
    crops: list[OnboardCrop] = Field(min_length=1, max_length=12)


class FertIn(_Base):
    area_acre: float = Field(gt=0, lt=1e5)
    soil_n: float | None = Field(None, ge=0, le=5000)
    soil_p: float | None = Field(None, ge=0, le=1000)
    soil_k: float | None = Field(None, ge=0, le=5000)
    ph: float | None = Field(None, ge=0, le=14)


def _rows(sql, args=()):
    with db.conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def _add(table, data: dict, fid: int):
    data = {**data, "farmer_id": fid}
    cols = ",".join(data)
    with db.conn() as c:
        cur = c.execute(f"INSERT INTO {table} ({cols}) VALUES ({','.join('?' * len(data))})",
                        [str(v) if isinstance(v, date) else v for v in data.values()])
        return cur.lastrowid


def _delete(table, id_, fid: int):
    with db.conn() as c:
        if c.execute(f"DELETE FROM {table} WHERE id=? AND farmer_id=?", (id_, fid)).rowcount == 0:
            raise HTTPException(404, "not found")
    return {"deleted": id_}


def _owned_plot(fid: int, plot_id: int) -> dict:
    rows = _rows("SELECT * FROM plots WHERE id=? AND farmer_id=?", (plot_id, fid))
    if not rows:
        raise HTTPException(404, "not found")
    return rows[0]


# ---- records -------------------------------------------------------------
@public.get("/api/meta")
def meta():
    return {"crops": sorted(crops.CROPS), "categories": crops.CATEGORIES}


@private.post("/api/expenses", status_code=201)
def add_expense(e: ExpenseIn, fid: int = Farmer):
    return {"id": _add("expenses", e.model_dump(), fid)}


@private.get("/api/expenses")
def list_expenses(crop: str | None = None, fid: int = Farmer):
    if crop:
        return _rows("SELECT * FROM expenses WHERE farmer_id=? AND crop=? ORDER BY date DESC, id DESC", (fid, _crop(crop)))
    return _rows("SELECT * FROM expenses WHERE farmer_id=? ORDER BY date DESC, id DESC", (fid,))


@private.delete("/api/expenses/{id_}")
def del_expense(id_: int, fid: int = Farmer):
    return _delete("expenses", id_, fid)


@private.post("/api/sales", status_code=201)
def add_sale(s: SaleIn, fid: int = Farmer):
    return {"id": _add("sales", s.model_dump(), fid)}


@private.get("/api/sales")
def list_sales(crop: str | None = None, fid: int = Farmer):
    if crop:
        return _rows("SELECT * FROM sales WHERE farmer_id=? AND crop=? ORDER BY date DESC, id DESC", (fid, _crop(crop)))
    return _rows("SELECT * FROM sales WHERE farmer_id=? ORDER BY date DESC, id DESC", (fid,))


@private.delete("/api/sales/{id_}")
def del_sale(id_: int, fid: int = Farmer):
    return _delete("sales", id_, fid)


def _new_plot(data: dict, fid: int) -> int:
    data = dict(data)
    watered = data.pop("last_watered_on", None)
    d = clock.parse(str(data["sowing_date"])) if data.get("sowing_date") else None
    pid = _add("plots", {**data, "season": clock.season_of(d), "created_on": clock.today(), "status": "active"}, fid)
    if watered and data.get("irrigation") != "rainfed":
        _add("activities", {"date": watered, "crop": data["crop"], "plot_id": pid, "kind": "irrigation", "task_key": "", "qty": None, "unit": "", "note": "setup"}, fid)
    return pid


@private.post("/api/plots", status_code=201)
def add_plot(p: PlotIn, fid: int = Farmer):
    return {"id": _new_plot(p.model_dump(), fid)}


@private.patch("/api/plots/{id_}")
def patch_plot(id_: int, p: PlotPatch, fid: int = Farmer):
    data = p.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(422, "nothing to change")
    if "sowing_date" in data:
        data["season"] = clock.season_of(data["sowing_date"])
    with db.conn() as c:
        sets = ",".join(f"{k}=?" for k in data)
        if c.execute(f"UPDATE plots SET {sets} WHERE id=? AND farmer_id=?", [str(v) if isinstance(v, date) else v for v in data.values()] + [id_, fid]).rowcount == 0:
            raise HTTPException(404, "not found")
    return {"updated": id_}


@private.post("/api/plots/{id_}/harvest")
def harvest_plot(id_: int, fid: int = Farmer):
    with db.conn() as c:
        if c.execute("UPDATE plots SET status='harvested', harvested_on=? WHERE id=? AND farmer_id=?", (clock.today().isoformat(), id_, fid)).rowcount == 0:
            raise HTTPException(404, "not found")
    return {"harvested": id_}


@private.get("/api/plots")
def list_plots(crop: str | None = None, fid: int = Farmer):
    if crop:
        return _rows("SELECT * FROM plots WHERE farmer_id=? AND crop=? ORDER BY id DESC", (fid, _crop(crop)))
    return _rows("SELECT * FROM plots WHERE farmer_id=? ORDER BY id DESC", (fid,))


@private.delete("/api/plots/{id_}")
def del_plot(id_: int, fid: int = Farmer):
    return _delete("plots", id_, fid)


# ---- farm profile, one-minute onboarding, activity log ----------------------
def _farm(fid: int) -> dict:
    rows = _rows("SELECT district, lat, lon, onboarded FROM farmer_farm WHERE farmer_id=?", (fid,))
    f = rows[0] if rows else {"district": "", "lat": None, "lon": None, "onboarded": 0}
    f["onboarded"] = bool(f["onboarded"]) or bool(_rows("SELECT 1 FROM plots WHERE farmer_id=? LIMIT 1", (fid,)))
    return f


def _save_farm(f: FarmIn, fid: int):
    with db.conn() as c:
        c.execute("INSERT INTO farmer_farm (farmer_id, district, lat, lon, onboarded) VALUES (?,?,?,?,1) "
                  "ON CONFLICT(farmer_id) DO UPDATE SET district=excluded.district, lat=excluded.lat, lon=excluded.lon, onboarded=1",
                  (fid, f.district, f.lat, f.lon))


@public.get("/api/districts")
def districts():
    return places.listing()


@private.get("/api/farm")
def get_farm(fid: int = Farmer):
    return _farm(fid)


@private.put("/api/farm")
def put_farm(f: FarmIn, fid: int = Farmer):
    _save_farm(f, fid)
    return _farm(fid)


@private.post("/api/onboard", status_code=201)
def onboard(o: OnboardIn, fid: int = Farmer):
    """Location + crops in one call: creates the farm profile and one plot per crop."""
    _save_farm(o, fid)
    ids = [_new_plot({"crop": c.crop, "area_acre": c.area_acre, "sowing_date": c.planted_on, "irrigation": c.irrigation, "note": "",
                      "last_watered_on": c.last_watered_on}, fid)
           for c in o.crops]
    return {"plot_ids": ids}


@private.post("/api/activities", status_code=201)
def add_activity(a: ActivityIn, fid: int = Farmer):
    d = a.model_dump()
    d["date"] = d["date"] or clock.today()
    if a.plot_id is not None:
        _owned_plot(fid, a.plot_id)          # an activity can only be attached to the farmer's own plot
    if a.kind == "harvest" and a.plot_id:
        harvest_plot(a.plot_id, fid)
    return {"id": _add("activities", d, fid)}


@private.get("/api/activities")
def list_activities(crop: str | None = None, kind: str | None = None, fid: int = Farmer):
    q, args = "SELECT * FROM activities WHERE farmer_id=?", [fid]
    if crop:
        q += " AND crop=?"; args.append(_crop(crop))
    if kind:
        q += " AND kind=?"; args.append(kind)
    return _rows(q + " ORDER BY date DESC, id DESC", args)


@private.delete("/api/activities/{id_}")
def del_activity(id_: int, fid: int = Farmer):
    return _delete("activities", id_, fid)


# ---- Today screen and crop plan ----------------------------------------------
def _weather_for_farm(fid: int) -> tuple[dict, dict]:
    farm = _farm(fid)
    return farm, wx.get(farm["lat"], farm["lon"])


def _weather_public(w: dict, today: date) -> dict:
    if not w.get("ok"):
        return {"ok": False, "error": w.get("error")}
    days = [d for d in w["days"] if d["date"] >= (today - timedelta(1)).isoformat()]
    return {"ok": True, "source": w["source"], "fetched_at": w["fetched_at"], "stale": bool(w.get("stale")),
            "current": w["current"], "days": days}


@private.get("/api/today")
def today_view(fid: int = Farmer):
    t = clock.today()
    farm, w = _weather_for_farm(fid)
    plots = _rows("SELECT * FROM plots WHERE farmer_id=? AND status='active' ORDER BY id", (fid,))
    acts = _rows("SELECT * FROM activities WHERE farmer_id=?", (fid,))
    tasks, states = [], []
    for p in plots:
        tasks += engine.tasks_for_plot(p, acts, w, t)
        states.append(engine.plot_state(p, t))
    shown = [x for x in engine.sort_tasks(tasks) if x["urgency"] != "later"]
    return {"as_of": clock.now().isoformat(timespec="seconds"), "farm": farm, "weather": _weather_public(w, t),
            "alerts": engine.alerts(w, farm["lat"] is not None, t), "tasks": shown, "plots": states}


@private.get("/api/plan/{crop}")
def plan(crop: str, plot_id: int | None = None, fid: int = Farmer):
    k = _crop(crop)
    t = clock.today()
    rows = _rows("SELECT * FROM plots WHERE farmer_id=? AND crop=? AND status='active' ORDER BY id DESC", (fid, k))
    p = next((r for r in rows if r["id"] == plot_id), rows[0] if rows else None) if rows else None
    if not p:
        return {"plot": None, "crop": k}
    farm, w = _weather_for_farm(fid)
    acts = _rows("SELECT * FROM activities WHERE farmer_id=? AND crop=?", (fid, k))
    return {"plot": p, "crop": k, "state": engine.plot_state(p, t),
            "tasks": engine.sort_tasks(engine.tasks_for_plot(p, acts, w, t)),
            "irrigation": engine.irrigation_status(p, acts, w, t), "calendar": engine.calendar(p, acts, t),
            "tips": engine.tips(k), "reviewed": engine.KB[k]["reviewed"], "weather": _weather_public(w, t),
            "plots": [{"id": r["id"], "area_acre": r["area_acre"], "sowing_date": r["sowing_date"]} for r in rows]}


# ---- prices / forecast / weather ----------------------------------------
@private.get("/api/prices/{crop}")
def get_prices(crop: str, state: str | None = None, days: int = Query(90, ge=14, le=365),
               refresh: bool = False):
    crop = _crop(crop)
    live = None
    if refresh:   # at most one upstream call per crop every 5 minutes, however many farmers ask
        import time
        if time.time() - _last_refresh.get(crop, 0) > 300:
            _last_refresh[crop] = time.time()
            live = prices.refresh_live(crop, state)
        else:
            live = {"ok": True, "rows": 0, "error": None, "note": "refreshed less than 5 minutes ago"}
    s = prices.series(crop, state, days)
    return {"crop": crop, **s, "refresh": live,
            "markets_today": prices.market_table(crop, s["source"]),
            "note": "source='demo' is synthetic sample data, NOT real market prices"
            if s["source"] == "demo" else "Agmarknet (data.gov.in) mandi prices, Rs/quintal"}


@private.get("/api/forecast/{crop}")
def get_forecast(crop: str, horizon: int = Query(14, ge=1, le=30), state: str | None = None):
    crop = _crop(crop)
    s = prices.series(crop, state, 120)
    return {"crop": crop, "source": s["source"], **forecast.forecast(s["prices"], horizon)}


@private.get("/api/weather")
def weather(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)):
    try:
        r = httpx.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 7,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum"})
        r.raise_for_status()
        return r.json()["daily"]
    except (httpx.HTTPError, KeyError, ValueError) as ex:
        raise HTTPException(502, f"weather provider unavailable: {type(ex).__name__}")


# ---- profit calculator / MSP -------------------------------------------
class ProfitIn(BaseModel):
    invested_per_acre: float = Field(gt=0, lt=1e8)
    yield_q_per_acre: float = Field(gt=0, lt=1e5)
    other_per_quintal: float = Field(0, ge=0, lt=1e7)
    price: float = Field(gt=0, lt=1e7)
    target_profit_per_acre: float | None = Field(None, ge=0, lt=1e9)


@private.post("/api/calc/profit")
def calc_profit(p: ProfitIn):
    return advice.profit_calc(p.invested_per_acre, p.yield_q_per_acre, p.other_per_quintal,
                              p.price, p.target_profit_per_acre)


@public.get("/api/msp")
def msp():
    data = json.loads((Path(__file__).parent / "msp.json").read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


# ---- fertilizer ----------------------------------------------------------
@private.post("/api/fertilizer/advice")
def fert_advice(f: FertIn):
    return advice.fertilizer_plan(f.crop, f.area_acre, f.soil_n, f.soil_p, f.soil_k, f.ph)


# ---- whole-farm overview (one farmer, many crops) -------------------------
@private.get("/api/overview")
def overview(fid: int = Farmer):
    area = {r["crop"]: r["a"] for r in _rows("SELECT crop, SUM(area_acre) a FROM plots WHERE farmer_id=? GROUP BY crop", (fid,))}
    cost = {r["crop"]: r["t"] for r in _rows("SELECT crop, SUM(amount) t FROM expenses WHERE farmer_id=? GROUP BY crop", (fid,))}
    sold = {r["crop"]: (r["q"], r["r"]) for r in _rows(
        "SELECT crop, SUM(qty_quintal) q, SUM(qty_quintal*price_per_quintal) r FROM sales WHERE farmer_id=? GROUP BY crop", (fid,))}
    last = {r["crop"]: r["d"] for r in _rows(
        "SELECT crop, MAX(d) d FROM (SELECT crop, date d FROM expenses WHERE farmer_id=? UNION ALL SELECT crop, date FROM sales WHERE farmer_id=?) GROUP BY crop", (fid, fid))}
    out = []
    for k in sorted(set(area) | set(cost) | set(sold)):
        q, rev = sold.get(k, (0, 0))
        c = cost.get(k, 0)
        s = prices.series(k, None, 120)
        fc = forecast.forecast(s["prices"], 14)
        out.append({
            "crop": k, "area_acre": round(area.get(k, 0), 2), "total_cost": round(c, 2),
            "revenue": round(rev, 2), "profit": round(rev - c, 2), "quintals_sold": round(q, 2),
            "status": "pending" if rev == 0 else ("profit" if rev >= c else "loss"),
            "current_price": s["prices"][-1] if s["prices"] else None, "price_source": s["source"],
            "expected_change_pct": fc.get("expected_change_pct") if fc.get("ok") else None,
            "last_activity": last.get(k)})
    out.sort(key=lambda x: (-x["area_acre"], x["crop"]))
    tot = lambda f: round(sum(x[f] for x in out), 2)
    return {"crops": out, "totals": {"area_acre": tot("area_acre"), "total_cost": tot("total_cost"),
                                     "revenue": tot("revenue"), "profit": tot("profit")}}


# ---- dashboard -----------------------------------------------------------
@private.get("/api/dashboard")
def dashboard(crop: str | None = None, fid: int = Farmer):
    k = _crop(crop) if crop else None
    w, a = ("WHERE farmer_id=? AND crop=?", (fid, k)) if k else ("WHERE farmer_id=?", (fid,))
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
app.include_router(auth.router)
app.include_router(public)
app.include_router(private)
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
