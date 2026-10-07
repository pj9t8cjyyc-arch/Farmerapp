import os
import tempfile

os.environ["FARMER_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
os.environ.pop("DATA_GOV_API_KEY", None)
os.environ["FARMER_AUTH"] = "off"   # these tests exercise the app in single-user mode; tests/test_auth.py covers login

import numpy as np
from fastapi.testclient import TestClient

from app import advice, forecast
from app.main import app

c = TestClient(app)


def test_expense_validation():
    ok = {"crop": "Chilli", "date": "2026-06-01", "category": "fertilizer", "amount": 1200}
    assert c.post("/api/expenses", json=ok).status_code == 201
    for bad in ({**ok, "amount": -5}, {**ok, "crop": "bogus"}, {**ok, "category": "x"},
                {**ok, "crop": "x'; DROP TABLE expenses;--"}):
        assert c.post("/api/expenses", json=bad).status_code == 422
    assert len(c.get("/api/expenses?crop=chilli").json()) == 1


def test_dashboard_pnl():
    c.post("/api/plots", json={"crop": "chilli", "area_acre": 2})
    c.post("/api/expenses", json={"crop": "chilli", "date": "2026-06-02", "category": "labour", "amount": 800})
    c.post("/api/sales", json={"crop": "chilli", "date": "2026-07-01", "qty_quintal": 1, "price_per_quintal": 5000})
    d = c.get("/api/dashboard?crop=chilli").json()
    assert d["total_cost"] == 2000 and d["revenue"] == 5000 and d["profit"] == 3000
    assert d["cost_per_acre"] == 1000 and d["price_source"] == "demo"
    assert d["forecast"]["ok"] and d["sell_advice"]
    assert c.get("/api/dashboard?crop=zzz").status_code == 404


def test_prices_and_forecast_demo_flagged():
    p = c.get("/api/prices/onion").json()
    assert p["source"] == "demo" and "synthetic" in p["note"] and len(p["prices"]) > 60
    f = c.get("/api/forecast/onion?horizon=7").json()
    assert len(f["forecast"]) == 7 and all(l <= u for l, u in zip(f["lower"], f["upper"]))
    assert f["backtest_mape_pct"] is not None


def test_forecast_trend_and_short_series():
    up = forecast.forecast(list(np.linspace(100, 200, 40)), 5)
    assert up["forecast"][-1] > up["last_price"]
    assert not forecast.forecast([1, 2, 3])["ok"]


def test_fertilizer_math():
    base = advice.fertilizer_plan("wheat", 2.47105)  # exactly 1 ha
    assert base["nutrient_kg"] == {"n": 120.0, "p": 60.0, "k": 40.0}
    rich = advice.fertilizer_plan("wheat", 2.47105, soil_n=700, soil_p=40, soil_k=300)
    assert rich["nutrient_kg"]["n"] == 60.0 and rich["products_kg"]["MOP"] < base["products_kg"]["MOP"]
    assert c.post("/api/fertilizer/advice", json={"crop": "wheat", "area_acre": 1}).status_code == 200
    assert c.post("/api/fertilizer/advice", json={"crop": "wheat", "area_acre": 0}).status_code == 422


def test_refresh_without_key_is_graceful():
    r = c.get("/api/prices/tomato?refresh=true").json()
    assert r["refresh"]["ok"] is False and r["source"] == "demo"


def test_profit_calc_matches_worked_example():
    r = c.post("/api/calc/profit", json={"invested_per_acre": 45000, "yield_q_per_acre": 30,
                                         "price": 2410, "target_profit_per_acre": 20000}).json()
    assert r["break_even_price"] == 1500 and r["profit_per_quintal"] == 910
    assert r["profit_per_acre"] == 27300 and r["roi_pct"] == 60.7
    assert round(r["price_for_target"]) == 2167 and r["status"] == "profit"
    assert sum(s["yours"] for s in r["scenarios"]) == 1


def test_profit_calc_loss_small_and_other_charges():
    r = c.post("/api/calc/profit", json={"invested_per_acre": 45000, "yield_q_per_acre": 30,
                                         "other_per_quintal": 100, "price": 1550}).json()
    assert r["break_even_price"] == 1600 and r["status"] == "loss"
    r = c.post("/api/calc/profit", json={"invested_per_acre": 45000, "yield_q_per_acre": 30, "price": 1600}).json()
    assert r["status"] == "small"  # ROI 6.7% < 15%
    assert c.post("/api/calc/profit", json={"invested_per_acre": 0, "yield_q_per_acre": 30, "price": 1}).status_code == 422


def test_bilingual_advice_and_msp():
    d = c.get("/api/dashboard?crop=chilli").json()
    for m in d["sell_advice"] + d["cost_insights"]:
        assert m["text"] and m["text_te"] and "{" not in m["text_te"]
    f = c.post("/api/fertilizer/advice", json={"crop": "wheat", "area_acre": 1}).json()
    assert all(t["text_te"] for t in f["tips"])
    assert c.get("/api/msp").json()["maize"]["price"] == 2410


def test_cors_for_native_app_and_static_assets():
    h = {"Origin": "capacitor://localhost", "Access-Control-Request-Method": "POST"}
    r = c.options("/api/calc/profit", headers=h)
    assert r.headers.get("access-control-allow-origin") == "capacitor://localhost"
    assert c.options("/api/calc/profit", headers={**h, "Origin": "https://evil.example"}).headers.get("access-control-allow-origin") is None
    for f in ("/", "/app.js", "/i18n.js", "/sw.js", "/manifest.webmanifest", "/vendor/chart.umd.js"):
        assert c.get(f).status_code == 200, f


def test_overview_multi_crop_and_filters():
    c.post("/api/plots", json={"crop": "maize", "area_acre": 1.5, "sowing_date": "2026-07-01"})
    c.post("/api/expenses", json={"crop": "maize", "date": "2026-07-02", "category": "seed", "amount": 3000})
    c.post("/api/sales", json={"crop": "maize", "date": "2026-10-01", "qty_quintal": 10, "price_per_quintal": 2400})
    o = c.get("/api/overview").json()
    by = {x["crop"]: x for x in o["crops"]}
    assert {"chilli", "maize"} <= set(by)
    assert by["maize"]["profit"] == 21000 and by["maize"]["status"] == "profit" and by["maize"]["area_acre"] == 1.5
    assert by["chilli"]["current_price"] and by["maize"]["price_source"] == "demo"
    assert round(o["totals"]["profit"], 2) == round(sum(x["profit"] for x in o["crops"]), 2)
    assert [p["crop"] for p in c.get("/api/plots?crop=maize").json()] == ["maize"]
    assert c.get("/api/plots?crop=zzz").status_code == 404
