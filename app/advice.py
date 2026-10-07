"""Rule-based advice: fertilizer plan, sell/hold, cost review."""
from . import crops

# Indian soil-test ratings for available nutrients (kg/ha): (low_below, high_above)
RATING = {"n": (280, 560), "p": (10, 25), "k": (110, 280)}
FACTOR = {"low": 1.25, "medium": 1.0, "high": 0.5}
UREA_N, DAP_N, DAP_P, MOP_K = 0.46, 0.18, 0.46, 0.60
ACRE_PER_HA = 2.47105


def _rate(nutrient: str, v: float | None) -> str:
    if v is None:
        return "medium"
    lo, hi = RATING[nutrient]
    return "low" if v < lo else "high" if v > hi else "medium"


def fertilizer_plan(crop: str, area_acre: float, soil_n=None, soil_p=None, soil_k=None,
                    ph=None) -> dict:
    _, _, n, p, k, _ = crops.CROPS[crop]
    ratings = {"n": _rate("n", soil_n), "p": _rate("p", soil_p), "k": _rate("k", soil_k)}
    ha = area_acre / ACRE_PER_HA
    need = {"n": n * FACTOR[ratings["n"]] * ha, "p": p * FACTOR[ratings["p"]] * ha,
            "k": k * FACTOR[ratings["k"]] * ha}
    dap = need["p"] / DAP_P
    urea = max(need["n"] - dap * DAP_N, 0) / UREA_N
    mop = need["k"] / MOP_K
    tips = []
    if soil_n is None and soil_p is None and soil_k is None:
        tips.append("No soil test given: using the standard dose. A soil test (about Rs 100-300 at "
                    "a KVK/state lab) usually cuts fertilizer cost by trimming nutrients the soil already has.")
    if ph is not None:
        if ph < 5.5:
            tips.append("Soil is acidic (pH < 5.5): apply lime per local recommendation before fertilizer.")
        elif ph > 8.5:
            tips.append("Soil is alkaline/sodic (pH > 8.5): consider gypsum and organic matter.")
    tips.append("Split nitrogen into 2-3 doses (basal, vegetative, flowering) to reduce loss; "
                "add farmyard manure/compost to improve uptake.")
    tips.append("Doses are general guidelines, not a prescription; confirm with your local KVK/agri officer.")
    return {"crop": crop, "area_acre": area_acre, "soil_ratings": ratings,
            "nutrient_kg": {k_: round(v, 1) for k_, v in need.items()},
            "products_kg": {"DAP": round(dap, 1), "Urea": round(urea, 1), "MOP": round(mop, 1)},
            "tips": tips}


def sell_advice(crop: str, fc: dict, cost_per_quintal: float | None, current_price: float | None) -> list[dict]:
    out = []
    storable = crops.CROPS[crop][5]
    if fc.get("ok"):
        ch = fc["expected_change_pct"]
        mape = fc.get("backtest_mape_pct")
        trust = "" if mape is None else f" (model error on last week: ~{mape}%)"
        if mape is not None and abs(ch) < mape:
            out.append({"level": "info", "text": f"Forecast move ({ch:+.1f}%) is smaller than model error{trust}; "
                        "no clear signal. Sell based on cash needs."})
        elif ch >= 3 and storable:
            out.append({"level": "good", "text": f"Prices expected to rise {ch:+.1f}% in {fc['horizon_days']} days{trust}. "
                        "Consider holding stock if you have safe storage and no urgent cash need."})
        elif ch >= 3:
            out.append({"level": "info", "text": f"Rise of {ch:+.1f}% expected but {crop} is perishable; "
                        "do not hold long."})
        elif ch <= -3:
            out.append({"level": "warn", "text": f"Prices expected to fall {ch:+.1f}%{trust}. Consider selling sooner."})
        else:
            out.append({"level": "info", "text": f"Prices roughly flat ({ch:+.1f}%){trust}."})
    else:
        out.append({"level": "info", "text": fc.get("reason", "Forecast unavailable")})
    if cost_per_quintal and current_price:
        if current_price < cost_per_quintal:
            out.append({"level": "warn", "text": f"Current market price (Rs {current_price:.0f}/q) is below your cost "
                        f"(Rs {cost_per_quintal:.0f}/q). Compare markets and consider MSP/storage options."})
        else:
            m = (current_price - cost_per_quintal) / cost_per_quintal * 100
            out.append({"level": "good", "text": f"Current price gives about {m:.0f}% margin over your cost."})
    return out


def cost_review(by_cat: dict[str, float], total_cost: float) -> list[dict]:
    out = []
    if total_cost <= 0:
        return [{"level": "info", "text": "Add expenses to get cost insights."}]
    share = {c: v / total_cost * 100 for c, v in by_cat.items()}
    if share.get("fertilizer", 0) > 30:
        out.append({"level": "warn", "text": f"Fertilizer is {share['fertilizer']:.0f}% of your cost. "
                    "Get a soil test and use the fertilizer calculator to avoid over-application."})
    if share.get("pesticide", 0) > 20:
        out.append({"level": "warn", "text": f"Pesticide is {share['pesticide']:.0f}% of cost; consider scouting-based "
                    "spraying / IPM to cut sprays."})
    if share.get("labour", 0) > 40:
        out.append({"level": "info", "text": f"Labour is {share['labour']:.0f}% of cost; check if mechanisation or "
                    "group hiring helps."})
    if not out:
        out.append({"level": "good", "text": "No single cost category looks unusually high."})
    return out
