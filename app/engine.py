"""Crop plan engine: where each plot is in its season, what fertilizer is due (with quantities for the
plot's area), whether to irrigate (simple FAO-56 style soil-water balance from live weather), and the
alerts/tasks shown on the Today screen. Pure functions: weather, activities and 'today' are passed in,
so everything here is unit-tested without network access."""
from datetime import date, timedelta

from . import advice, clock, crops
from .i18n import msg
from .knowledge import KB, kc_at, stage_at

SOON_DAYS = 7         # a fertilizer window starting within this many days is "soon"
MISSED_AFTER = 21     # an unlogged window that ended this long ago is no longer nagged about
PRODUCT_NAMES = {"Urea": ("Urea", "యూరియా"), "DAP": ("DAP", "DAP"), "MOP": ("MOP (potash)", "MOP (పొటాష్)"),
                 "Gypsum": ("Gypsum", "జిప్సం")}
URGENCY = {"now": 0, "soon": 1, "later": 2}


def _d(iso):
    return clock.parse(iso)


def _fmt(d: date) -> str:
    return f"{d.day} {d.strftime('%b')}"


def _window(a: date, b: date) -> str:
    return _fmt(a) if a == b else f"{_fmt(a)}–{_fmt(b)}"


def _acts(plot: dict, acts: list[dict], kind: str) -> list[dict]:
    return [a for a in acts if a["kind"] == kind and a["crop"] == plot["crop"]
            and a["plot_id"] in (None, plot["id"])]


def plot_state(plot: dict, today: date) -> dict:
    """Where the plot is in its season. planted is None when the farmer has not entered a planting date."""
    kb = KB[plot["crop"]]
    planted = _d(plot.get("sowing_date"))
    out = {"plot_id": plot["id"], "crop": plot["crop"], "area_acre": plot["area_acre"], "planted": plot.get("sowing_date"),
           "irrigation": plot.get("irrigation") or "borewell", "season": plot.get("season") or clock.season_of(planted)}
    if not planted:
        return {**out, "das": None, "stage": None, "progress_pct": 0, "harvest_from": None, "harvest_to": None}
    das = (today - planted).days
    st = stage_at(plot["crop"], das)
    lo, hi = kb["duration_days"]
    return {**out, "das": das, "stage": {"key": st["key"], "en": st["en"], "te": st["te"]},
            "progress_pct": max(0, min(100, round(das / hi * 100))),
            "harvest_from": (planted + timedelta(lo)).isoformat(), "harvest_to": (planted + timedelta(hi)).isoformat()}


def _products(plot: dict, n_kg: float, p_kg: float, k_kg: float, extra: dict | None) -> dict:
    prod = advice.products_for(n_kg, p_kg, k_kg)
    if extra:
        prod[extra["name"]] = extra["kg_per_ha"] * plot["area_acre"] / advice.ACRE_PER_HA
    return {k: v for k, v in prod.items() if v >= 0.5}


def _product_text(prod: dict, area: float) -> tuple[str, str]:
    one = round(area, 1) == 1.0   # per-acre figure is only shown when it differs from the total
    parts = [(f"{PRODUCT_NAMES[k][0]} {round(v)} kg" + ("" if one else f" ({round(v / area)} kg/acre)"),
              f"{PRODUCT_NAMES[k][1]} {round(v)} కి.గ్రా" + ("" if one else f" ({round(v / area)} కి.గ్రా/ఎకరా)")) for k, v in prod.items()]
    return ", ".join(p[0] for p in parts), ", ".join(p[1] for p in parts)


def fertilizer_events(plot: dict, acts: list[dict], today: date) -> list[dict]:
    """Every fertilizer step for the plot with dates, quantities and status:
    done | assumed (window ended before the plot was added) | overdue | due | soon | later | missed."""
    planted = _d(plot.get("sowing_date"))
    if not planted:
        return []
    need, _ = advice.nutrient_need(plot["crop"], plot["area_acre"], plot.get("soil_n"), plot.get("soil_p"), plot.get("soil_k"))
    created = _d(plot.get("created_on")) or today
    done_keys = {a["task_key"]: a for a in _acts(plot, acts, "fertilizer") if _d(a["date"]) >= planted - timedelta(7)}
    out = []
    for e in KB[plot["crop"]]["fertilizer"]:
        start, end = planted + timedelta(e["das"][0]), planted + timedelta(e["das"][1])
        prod = _products(plot, need["n"] * e["N"], need["p"] * e["P"], need["k"] * e["K"], e.get("extra"))
        if e["key"] in done_keys:
            status = "done"
        elif end < created:
            status = "assumed"
        elif today > end + timedelta(MISSED_AFTER):
            status = "missed"
        elif today > end:
            status = "overdue"
        elif today >= start:
            status = "due"
        elif (start - today).days <= SOON_DAYS:
            status = "soon"
        else:
            status = "later"
        en, te = _product_text(prod, plot["area_acre"])
        out.append({"key": e["key"], "label": e["en"], "label_te": e["te"], "from": start.isoformat(), "to": end.isoformat(),
                    "status": status, "products_kg": {k: round(v, 1) for k, v in prod.items()},
                    "products_text": en, "products_text_te": te,
                    "done_on": done_keys[e["key"]]["date"] if e["key"] in done_keys else None})
    return out


def _eff_rain(mm: float) -> float:
    """Effective rain: small showers (< 5 mm) are lost to evaporation, otherwise 80% reaches the roots."""
    return 0.8 * mm if mm >= 5 else 0.0


def _pop_weight(pop) -> float:  # forecast rain is discounted by its probability
    return 1.0 if pop is None else min(1.0, pop / 70)


def irrigation_status(plot: dict, acts: list[dict], weather: dict, today: date) -> dict:
    """Decide whether to water. Soil water deficit D accumulates from the last watering (or last 14 days):
    D += crop water use (ET0 x Kc) - effective rain, never below 0. Water when D reaches the crop's limit."""
    crop, kb = plot["crop"], KB[plot["crop"]]["irrigation"]
    planted = _d(plot.get("sowing_date"))
    waterings = [a for a in _acts(plot, acts, "irrigation") if planted and _d(a["date"]) >= planted]
    last = max((_d(a["date"]) for a in waterings), default=None)
    base = {"mode": kb["mode"], "count": len(waterings), "last": last.isoformat() if last else None,
            "days_since": (today - last).days if last else None, "limit_mm": kb["depletion_mm"] or None}
    if not planted:
        return {**base, "state": "no_date"}
    das = (today - planted).days
    if das < 0:
        return {**base, "state": "not_planted"}
    lo = KB[crop]["duration_days"][0]
    stop_from = planted + timedelta(lo - kb["stop_before_harvest_days"])
    if kb["mode"] == "ponded":
        return {**base, "state": "ponded", "stop_from": stop_from.isoformat()}
    if kb["stop_before_harvest_days"] and today >= stop_from:
        return {**base, "state": "stop", "stop_from": stop_from.isoformat()}
    rainfed = (plot.get("irrigation") or "borewell") == "rainfed"
    if last is None and not rainfed:   # we cannot know the soil water without a last watering date: ask, do not guess
        return {**base, "state": "never", "gap_days": kb["interval_days"]}
    if not weather.get("ok"):
        gap = kb["interval_days"]
        if rainfed:
            return {**base, "state": "unknown", "gap_days": gap}
        return {**base, "state": "fallback_now" if base["days_since"] >= gap else "fallback", "gap_days": gap}
    days = {d["date"]: d for d in weather["days"]}
    first = _d(weather["days"][0]["date"])
    start = max(last or planted, today - timedelta(14), first - timedelta(1))
    deficit, cur = 0.0, start + timedelta(1)
    while cur <= today:
        w = days.get(cur.isoformat())
        if w and w["et0"] is not None:
            deficit = max(0.0, deficit + w["et0"] * kc_at(crop, (cur - planted).days) - _eff_rain(w["rain"] or 0))
        cur += timedelta(1)
    limit = kb["depletion_mm"]
    out = {**base, "deficit_mm": round(deficit, 1), "weather_asof": weather.get("fetched_at")}
    fut, hit, cur = deficit, None, today + timedelta(1)
    while cur.isoformat() in days:
        w = days[cur.isoformat()]
        if w["et0"] is not None:
            fut = max(0.0, fut + w["et0"] * kc_at(crop, (cur - planted).days) - _eff_rain(w["rain"] or 0) * _pop_weight(w["pop"]))
        if hit is None and fut >= limit:
            hit = cur
        cur += timedelta(1)
    out["next_date"] = hit.isoformat() if hit else None
    out["in_days"] = (hit - today).days if hit else None
    if rainfed:
        return {**out, "state": "rainfed_dry" if deficit >= limit else "rainfed_ok"}
    if deficit >= limit:
        return {**out, "state": "now"}
    if hit and (hit - today).days <= 2:
        return {**out, "state": "soon"}
    return {**out, "state": "ok"}


def alerts(weather: dict, has_location: bool, today: date) -> list[dict]:
    if not has_location:
        return [msg("a.noloc", "info")]
    if not weather.get("ok"):
        return [msg("a.noweather", "warn")]
    out = []
    horizon = [d for d in weather["days"] if today <= _d(d["date"]) <= today + timedelta(3)]
    rain = max(horizon, key=lambda d: d["rain"] or 0, default=None)
    if rain and (rain["rain"] or 0) >= 25:
        out.append(msg("a.rain", "warn", date=_fmt(_d(rain["date"])), mm=round(rain["rain"])))
    hot = max(horizon, key=lambda d: d["tmax"] or 0, default=None)
    if hot and (hot["tmax"] or 0) >= 40:
        out.append(msg("a.heat", "warn", date=_fmt(_d(hot["date"])), t=round(hot["tmax"])))
    return out


def tasks_for_plot(plot: dict, acts: list[dict], weather: dict, today: date) -> list[dict]:
    """All tasks for one plot (urgency now|soon|later); the Today screen shows now/soon only."""
    crop, tasks = plot["crop"], []

    def add(kind, key, urgency, m, action=None, due=None):
        tasks.append({"kind": kind, "key": key, "crop": crop, "plot_id": plot["id"], "urgency": urgency,
                      "due": due.isoformat() if due else None, **m, "action": action})

    st = plot_state(plot, today)
    if st["das"] is None:
        add("setup", "set_date", "now", msg("t.set_date", "warn", crop=crop), {"kind": "setup"})
        return tasks
    for e in fertilizer_events(plot, acts, today):
        if e["status"] not in ("due", "overdue", "soon", "later"):
            continue
        code = {"due": "t.fert_due", "overdue": "t.fert_overdue", "soon": "t.fert_soon", "later": "t.fert_later"}[e["status"]]
        m = msg(code, "warn" if e["status"] == "overdue" else "info", crop=crop, label=(e["label"], e["label_te"]),
                window=_window(_d(e["from"]), _d(e["to"])), products=(e["products_text"], e["products_text_te"]))
        add("fertilizer", e["key"], "now" if e["status"] in ("due", "overdue") else "soon" if e["status"] == "soon" else "later",
            m, {"kind": "fertilizer", "task_key": e["key"], "qty": round(sum(e["products_kg"].values()), 1), "unit": "kg"}, _d(e["from"]))
    irr = irrigation_status(plot, acts, weather, today)
    water = {"kind": "irrigation", "task_key": "", "qty": None, "unit": ""}
    s = irr["state"]
    if s == "now":
        add("irrigation", "water", "now", msg("t.irrigate_now", "warn", crop=crop, d=round(irr["deficit_mm"]), t=irr["limit_mm"]), water, today)
    elif s == "soon":
        nd = _d(irr["next_date"])
        add("irrigation", "water", "soon", msg("t.irrigate_soon", crop=crop, date=_fmt(nd), n=irr["in_days"]), water, nd)
    elif s == "ok":
        m = (msg("t.irrigate_ok", crop=crop, d=round(irr["deficit_mm"]), t=irr["limit_mm"], date=_fmt(_d(irr["next_date"])))
             if irr["next_date"] else msg("t.irrigate_ok2", crop=crop, d=round(irr["deficit_mm"]), t=irr["limit_mm"]))
        add("irrigation", "water", "later", m, water)
    elif s == "fallback_now":
        add("irrigation", "water", "now", msg("t.irrigate_fallback_now", "warn", crop=crop, n=irr["days_since"], g=irr["gap_days"]), water, today)
    elif s == "fallback":
        add("irrigation", "water", "later", msg("t.irrigate_fallback", crop=crop, n=irr["days_since"], g=irr["gap_days"]), water)
    elif s == "never":
        add("irrigation", "water", "soon", msg("t.irrigate_never", crop=crop), {"kind": "plan"})
    elif s == "rainfed_dry":
        add("irrigation", "water", "soon", msg("t.rainfed_dry", "warn", crop=crop, d=round(irr["deficit_mm"])), water)
    elif s == "rainfed_ok":
        add("irrigation", "water", "later", msg("t.rainfed_ok", crop=crop, d=round(irr["deficit_mm"])))
    elif s == "ponded":
        days_left = (_d(irr["stop_from"]) - today).days
        add("irrigation", "water", "later", msg("t.ponded", crop=crop, n=KB[crop]["irrigation"]["stop_before_harvest_days"]), water)
        if days_left <= 3:
            add("irrigation", "stop", "soon" if days_left > 0 else "now", msg("t.stop_irrigation", crop=crop, date=_fmt(_d(irr["stop_from"]))), None, _d(irr["stop_from"]))
    elif s == "stop":
        add("irrigation", "stop", "now", msg("t.stop_irrigation", crop=crop, date=_fmt(_d(irr["stop_from"]))), None, _d(irr["stop_from"]))
    hf = _d(st["harvest_from"])
    harvest = {"kind": "harvest", "task_key": "", "qty": None, "unit": ""}
    if today >= hf:
        add("harvest", "harvest", "now", msg("t.harvest_now", "warn", crop=crop, date=_fmt(hf)), harvest, hf)
    elif (hf - today).days <= 14:
        add("harvest", "harvest", "soon", msg("t.harvest_soon", crop=crop, date=_fmt(hf)), None, hf)
    return tasks


def sort_tasks(tasks: list[dict]) -> list[dict]:
    return sorted(tasks, key=lambda t: (URGENCY[t["urgency"]], t["due"] or "9999"))


def calendar(plot: dict, acts: list[dict], today: date) -> dict:
    """Full timeline for the plot: stage bands, fertilizer steps, critical irrigation windows, harvest window."""
    planted = _d(plot.get("sowing_date"))
    kb = KB[plot["crop"]]
    if not planted:
        return {"stages": [], "critical_irrigation": [], "fertilizer": []}
    iso = lambda n: (planted + timedelta(n)).isoformat()
    return {"stages": [{"key": s["key"], "en": s["en"], "te": s["te"], "from": iso(s["das"][0]), "to": iso(s["das"][1])} for s in kb["stages"]],
            "critical_irrigation": [{"en": w["en"], "te": w["te"], "from": iso(w["das"][0]), "to": iso(w["das"][1])} for w in kb["irrigation"]["critical"]],
            "fertilizer": fertilizer_events(plot, acts, today)}


def tips(crop: str) -> list[dict]:
    return [{"text": t["en"], "text_te": t["te"], "level": "info"} for t in KB[crop].get("tips", [])]
