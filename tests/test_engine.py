"""Engine + plan API tests. Weather is faked, so no network is needed."""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app import advice, clock, db, engine, knowledge, main

TODAY = clock.today()
iso = lambda n: (TODAY + timedelta(n)).isoformat()


def fake_weather(et0=5.0, rain=None, tmax=34.0):
    """14 past days + today + 6 forecast days. rain: {day_offset: mm}."""
    rain = rain or {}
    return {"ok": True, "source": "test", "fetched_at": clock.now().isoformat(timespec="seconds"),
            "current": {"temp": 31, "humidity": 55, "rain": 0, "wind": 9, "code": 1},
            "days": [{"date": iso(n), "tmax": tmax, "tmin": 24, "rain": rain.get(n, 0.0), "pop": 90 if rain.get(n) else 10,
                      "et0": et0, "wind": 10} for n in range(-14, 7)]}


def plot(crop="maize", planted_days_ago=30, area=1.0, created_days_ago=None, irrigation="borewell", pid=1):
    return {"id": pid, "crop": crop, "area_acre": area, "sowing_date": iso(-planted_days_ago) if planted_days_ago is not None else None,
            "irrigation": irrigation, "season": "kharif", "soil_n": None, "soil_p": None, "soil_k": None, "ph": None,
            "created_on": iso(-(created_days_ago if created_days_ago is not None else planted_days_ago)) if planted_days_ago is not None else iso(0)}


def act(kind, days_ago, crop="maize", key="", pid=1):
    return {"id": 1, "date": iso(-days_ago), "crop": crop, "plot_id": pid, "kind": kind, "task_key": key, "qty": None, "unit": "", "note": ""}


def test_knowledge_base_is_consistent():
    assert knowledge.problems() == []


def test_plot_state_stage_and_progress():
    s = engine.plot_state(plot("maize", 50), TODAY)
    assert s["das"] == 50 and s["stage"]["key"] == "flowering" and 40 < s["progress_pct"] < 50
    assert engine.plot_state(plot("maize", None), TODAY)["stage"] is None


def test_fertilizer_quantities_match_nutrient_math():
    ev = {e["key"]: e for e in engine.fertilizer_events(plot("maize", 3, area=2.47105), [], TODAY)}  # exactly 1 ha
    assert ev["basal"]["status"] == "due"
    assert ev["basal"]["products_kg"]["DAP"] == pytest.approx(60 / 0.46, abs=0.1)         # all P at sowing
    assert ev["basal"]["products_kg"]["MOP"] == pytest.approx(40 / 0.6, abs=0.1)          # all K at sowing
    n_basal = 120 * 0.34 - (60 / 0.46) * 0.18
    assert ev["basal"]["products_kg"]["Urea"] == pytest.approx(n_basal / 0.46, abs=0.2)
    assert ev["top1"]["products_kg"] == {"Urea": pytest.approx(120 * 0.33 / 0.46, abs=0.1)} and ev["top1"]["status"] == "later"


def test_fertilizer_status_transitions_and_logging():
    st = lambda p, a=(): {e["key"]: e["status"] for e in engine.fertilizer_events(p, list(a), TODAY)}
    assert st(plot("maize", 28)) == {"basal": "missed", "top1": "due", "top2": "later"}
    assert st(plot("maize", 28, created_days_ago=0))["basal"] == "assumed"          # plot added after the window: not nagged
    assert st(plot("maize", 33))["top1"] == "overdue"
    assert st(plot("maize", 21))["top1"] == "soon"
    assert st(plot("maize", 28), [act("fertilizer", 1, key="top1")])["top1"] == "done"
    assert st(plot("maize", 28), [act("fertilizer", 1, key="top1", pid=99)])["top1"] == "due"   # other plot's log does not count


def test_gypsum_event_for_groundnut_uses_extra_product():
    ev = {e["key"]: e for e in engine.fertilizer_events(plot("groundnut", 42, area=2.47105), [], TODAY)}
    assert ev["gypsum"]["products_kg"] == {"Gypsum": pytest.approx(500, abs=0.1)} and ev["gypsum"]["status"] == "due"


def test_irrigation_water_balance():
    p = plot("maize", 30)     # vegetative, Kc 0.8 -> 4 mm/day at ET0 5; limit 40 mm
    now = engine.irrigation_status(p, [act("irrigation", 10)], fake_weather(), TODAY)
    assert now["state"] == "now" and now["deficit_mm"] == pytest.approx(40, abs=1)
    soon = engine.irrigation_status(p, [act("irrigation", 8)], fake_weather(), TODAY)
    assert soon["state"] == "soon" and soon["in_days"] == 2
    ok = engine.irrigation_status(p, [act("irrigation", 3)], fake_weather(), TODAY)
    assert ok["state"] == "ok" and (ok["in_days"] is None or ok["in_days"] >= 5) and ok["count"] == 1   # forecast covers 6 days only
    rained = engine.irrigation_status(p, [act("irrigation", 10)], fake_weather(rain={-1: 40}), TODAY)   # 40 mm yesterday refills the soil
    assert rained["state"] == "ok" and rained["deficit_mm"] < 10
    wait_rain = engine.irrigation_status(p, [act("irrigation", 8)], fake_weather(rain={1: 45}), TODAY)  # forecast rain delays watering
    assert wait_rain["state"] == "ok" and (wait_rain["in_days"] is None or wait_rain["in_days"] > 3)


def test_never_watered_asks_instead_of_guessing():
    assert engine.irrigation_status(plot("maize", 30), [], fake_weather(), TODAY)["state"] == "never"
    t = next(t for t in engine.tasks_for_plot(plot("maize", 30), [], fake_weather(), TODAY) if t["kind"] == "irrigation")
    assert t["action"] == {"kind": "plan"} and t["urgency"] == "soon"


def test_telugu_dative_follows_crop_name():
    from app.i18n import msg
    assert "మిర్చికి" in msg("t.irrigate_now", crop="chilli", d=1, t=1)["text_te"]
    assert "టమాటాకు" in msg("t.irrigate_now", crop="tomato", d=1, t=1)["text_te"]


def test_irrigation_special_modes():
    assert engine.irrigation_status(plot("paddy", 30), [], fake_weather(), TODAY)["state"] == "ponded"
    assert engine.irrigation_status(plot("onion", 95), [], fake_weather(), TODAY)["state"] == "stop"       # stop watering before harvest
    assert engine.irrigation_status(plot("maize", 30, irrigation="rainfed"), [], fake_weather(), TODAY)["state"] == "rainfed_dry"
    assert engine.irrigation_status(plot("maize", None), [], fake_weather(), TODAY)["state"] == "no_date"
    assert engine.irrigation_status(plot("maize", -5), [], fake_weather(), TODAY)["state"] == "not_planted"


def test_irrigation_falls_back_without_weather():
    down = {"ok": False}
    assert engine.irrigation_status(plot("maize", 30), [], down, TODAY)["state"] == "never"
    assert engine.irrigation_status(plot("maize", 30), [act("irrigation", 12)], down, TODAY)["state"] == "fallback_now"
    assert engine.irrigation_status(plot("maize", 30), [act("irrigation", 3)], down, TODAY)["state"] == "fallback"


def test_tasks_and_urgency_order():
    tasks = engine.sort_tasks(engine.tasks_for_plot(plot("maize", 40), [act("irrigation", 10)], fake_weather(), TODAY))
    kinds = [(t["kind"], t["key"], t["urgency"]) for t in tasks]
    assert ("irrigation", "water", "now") in kinds and ("fertilizer", "top1", "now") in kinds
    assert all(t["text"] and t["text_te"] and "{" not in t["text_te"] for t in tasks)
    assert [t["urgency"] for t in tasks] == sorted((t["urgency"] for t in tasks), key=engine.URGENCY.get)
    fert = next(t for t in tasks if t["kind"] == "fertilizer" and t["key"] == "top1")
    assert fert["action"] == {"kind": "fertilizer", "task_key": "top1", "qty": fert["action"]["qty"], "unit": "kg"} and fert["action"]["qty"] > 0
    assert engine.tasks_for_plot(plot("maize", None), [], fake_weather(), TODAY)[0]["key"] == "set_date"
    harvest = engine.tasks_for_plot(plot("maize", 100), [], fake_weather(), TODAY)
    assert any(t["kind"] == "harvest" and t["urgency"] == "now" for t in harvest)


def test_alerts():
    assert engine.alerts(fake_weather(rain={2: 60}), True, TODAY)[0]["code"] == "a.rain"
    assert engine.alerts(fake_weather(tmax=43), True, TODAY)[0]["code"] == "a.heat"
    assert engine.alerts(fake_weather(), True, TODAY) == []
    assert engine.alerts({"ok": False}, True, TODAY)[0]["code"] == "a.noweather"
    assert engine.alerts({"ok": False}, False, TODAY)[0]["code"] == "a.noloc"


# ---------------- API ----------------
@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("FARMER_AUTH", "off")
    db.init()
    monkeypatch.setattr(main.wx, "get", lambda lat, lon: fake_weather() if lat is not None else {"ok": False, "error": "no location"})
    return TestClient(main.app)


def test_onboarding_creates_farm_and_plots(client):
    assert client.get("/api/farm").json()["onboarded"] is False
    r = client.post("/api/onboard", json={"district": "Guntur", "lat": 16.3, "lon": 80.44, "crops": [
        {"crop": "maize", "area_acre": 1.5, "planted_on": iso(-28), "irrigation": "borewell"},
        {"crop": "chilli", "area_acre": 2, "planted_on": None, "irrigation": "drip"}]})
    assert r.status_code == 201 and len(r.json()["plot_ids"]) == 2
    f = client.get("/api/farm").json()
    assert f["onboarded"] and f["lat"] == 16.3
    plots = {p["crop"]: p for p in client.get("/api/plots").json()}
    assert plots["maize"]["season"] in ("kharif", "rabi", "summer") and plots["maize"]["created_on"] == TODAY.isoformat()
    assert plots["chilli"]["season"] == "" and plots["chilli"]["irrigation"] == "drip"
    water = client.get("/api/activities?kind=irrigation").json()
    assert len(water) == 0                                    # none given -> nothing invented
    client.post("/api/onboard", json={"crops": [{"crop": "onion", "area_acre": 1, "planted_on": iso(-10), "irrigation": "canal", "last_watered_on": iso(-2)},
                                                {"crop": "tomato", "area_acre": 1, "planted_on": iso(-10), "irrigation": "rainfed", "last_watered_on": iso(-2)}]})
    water = client.get("/api/activities?kind=irrigation").json()
    assert [w["crop"] for w in water] == ["onion"] and water[0]["date"] == iso(-2)       # rain-fed plots never get a watering log
    assert client.post("/api/onboard", json={"crops": []}).status_code == 422
    assert client.post("/api/onboard", json={"crops": [{"crop": "bogus", "area_acre": 1}]}).status_code == 422


def test_today_screen_logging_and_plan(client):
    client.post("/api/onboard", json={"district": "Guntur", "lat": 16.3, "lon": 80.44,
                                      "crops": [{"crop": "maize", "area_acre": 1.5, "planted_on": iso(-28)}]})
    t = client.get("/api/today").json()
    assert t["weather"]["ok"] and t["plots"][0]["stage"]["key"] == "vegetative"
    top = {(x["kind"], x["key"]) for x in t["tasks"]}
    assert ("fertilizer", "top1") in top and all(x["urgency"] != "later" for x in t["tasks"])
    # one tap "Done": logging the fertilizer step removes it from Today
    a = next(x for x in t["tasks"] if x["key"] == "top1")["action"]
    assert client.post("/api/activities", json={"crop": "maize", "plot_id": t["plots"][0]["plot_id"], **a}).status_code == 201
    assert ("fertilizer", "top1") not in {(x["kind"], x["key"]) for x in client.get("/api/today").json()["tasks"]}
    # no watering logged yet -> the app asks instead of guessing
    assert client.get("/api/plan/maize").json()["irrigation"]["state"] == "never"
    # watering resets the irrigation advice and counts waterings
    pid = t["plots"][0]["plot_id"]
    client.post("/api/activities", json={"crop": "maize", "plot_id": pid, "kind": "irrigation"})
    plan = client.get("/api/plan/maize").json()
    assert plan["irrigation"]["state"] == "ok" and plan["irrigation"]["count"] == 1 and plan["irrigation"]["days_since"] == 0
    assert {e["key"]: e["status"] for e in plan["calendar"]["fertilizer"]}["top1"] == "done"
    assert plan["reviewed"] is False and plan["state"]["das"] == 28
    assert client.get("/api/plan/zzz").status_code == 404
    assert client.get("/api/plan/onion").json()["plot"] is None


def test_today_without_location_and_harvest_flow(client):
    client.post("/api/plots", json={"crop": "maize", "area_acre": 1, "sowing_date": iso(-100)})
    t = client.get("/api/today").json()
    assert t["weather"]["ok"] is False and t["alerts"][0]["code"] == "a.noloc"
    h = next(x for x in t["tasks"] if x["kind"] == "harvest")
    pid = t["plots"][0]["plot_id"]
    assert client.post("/api/activities", json={"crop": "maize", "plot_id": pid, "kind": "harvest"}).status_code == 201
    t2 = client.get("/api/today").json()
    assert t2["plots"] == [] and t2["tasks"] == []                                    # harvested plots leave the Today screen
    assert client.get("/api/plots?crop=maize").json()[0]["status"] == "harvested"


def test_patch_plot_and_activity_validation(client):
    pid = client.post("/api/plots", json={"crop": "maize", "area_acre": 1}).json()["id"]
    assert client.patch(f"/api/plots/{pid}", json={"sowing_date": iso(-10), "irrigation": "rainfed"}).status_code == 200
    p = client.get("/api/plots?crop=maize").json()[0]
    assert p["sowing_date"] == iso(-10) and p["irrigation"] == "rainfed" and p["season"]
    assert client.patch(f"/api/plots/{pid}", json={}).status_code == 422
    assert client.patch("/api/plots/999", json={"area_acre": 2}).status_code == 404
    assert client.post("/api/activities", json={"crop": "maize", "kind": "bogus"}).status_code == 422
    assert client.post("/api/activities", json={"crop": "maize", "kind": "irrigation", "qty": -1}).status_code == 422
    assert len(client.get("/api/districts").json()) >= 20


def test_nutrient_helpers_agree_with_fertilizer_plan():
    need, _ = advice.nutrient_need("wheat", 2.47105)
    assert advice.fertilizer_plan("wheat", 2.47105)["nutrient_kg"] == {k: round(v, 1) for k, v in need.items()}
