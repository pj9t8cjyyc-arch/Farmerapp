"""Rule-based advice: fertilizer plan, sell/hold, cost review."""
from . import crops
from .i18n import msg

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


def nutrient_need(crop: str, area_acre: float, soil_n=None, soil_p=None, soil_k=None) -> tuple[dict, dict]:
    """Total N, P2O5, K2O (kg) for the area, adjusted by soil-test ratings. Returns (need_kg, ratings)."""
    _, _, n, p, k, _ = crops.CROPS[crop]
    ratings = {"n": _rate("n", soil_n), "p": _rate("p", soil_p), "k": _rate("k", soil_k)}
    ha = area_acre / ACRE_PER_HA
    return {"n": n * FACTOR[ratings["n"]] * ha, "p": p * FACTOR[ratings["p"]] * ha,
            "k": k * FACTOR[ratings["k"]] * ha}, ratings


def products_for(n_kg: float, p_kg: float, k_kg: float) -> dict:
    """Fertilizer products (kg) that supply the nutrients: DAP for P (it also carries 18% N), urea for the rest of N, MOP for K."""
    dap = p_kg / DAP_P
    return {"DAP": dap, "Urea": max(n_kg - dap * DAP_N, 0) / UREA_N, "MOP": k_kg / MOP_K}


def fertilizer_plan(crop: str, area_acre: float, soil_n=None, soil_p=None, soil_k=None,
                    ph=None) -> dict:
    need, ratings = nutrient_need(crop, area_acre, soil_n, soil_p, soil_k)
    prod = products_for(need["n"], need["p"], need["k"])
    dap, urea, mop = prod["DAP"], prod["Urea"], prod["MOP"]
    tips = []
    if soil_n is None and soil_p is None and soil_k is None:
        tips.append(msg("fert.nosoil"))
    if ph is not None:
        if ph < 5.5:
            tips.append(msg("fert.acid", "warn"))
        elif ph > 8.5:
            tips.append(msg("fert.alk", "warn"))
    tips += [msg("fert.split"), msg("fert.confirm")]
    return {"crop": crop, "area_acre": area_acre, "soil_ratings": ratings,
            "nutrient_kg": {k_: round(v, 1) for k_, v in need.items()},
            "products_kg": {"DAP": round(dap, 1), "Urea": round(urea, 1), "MOP": round(mop, 1)},
            "tips": tips}


def sell_advice(crop: str, fc: dict, cost_per_quintal: float | None, current_price: float | None) -> list[dict]:
    out = []
    storable = crops.CROPS[crop][5]
    if fc.get("ok"):
        ch, mape = fc["expected_change_pct"], fc.get("backtest_mape_pct")
        if mape is not None and abs(ch) < mape:
            out.append(msg("sell.no_signal", ch=ch, mape=mape))
        elif ch >= 3 and storable:
            out.append(msg("sell.hold", "good", ch=ch, days=fc["horizon_days"]))
        elif ch >= 3:
            out.append(msg("sell.perishable", crop=crop, ch=ch))
        elif ch <= -3:
            out.append(msg("sell.fall", "warn", ch=ch))
        else:
            out.append(msg("sell.flat", ch=ch))
    else:
        out.append(msg("sell.nofc"))
    if cost_per_quintal and current_price:
        if current_price < cost_per_quintal:
            out.append(msg("sell.below_cost", "warn", price=current_price, cost=cost_per_quintal))
        else:
            out.append(msg("sell.margin", "good",
                           m=(current_price - cost_per_quintal) / cost_per_quintal * 100))
    return out


def cost_review(by_cat: dict[str, float], total_cost: float) -> list[dict]:
    if total_cost <= 0:
        return [msg("cost.none")]
    share = {c: v / total_cost * 100 for c, v in by_cat.items()}
    out = []
    if share.get("fertilizer", 0) > 30:
        out.append(msg("cost.fert", "warn", p=share["fertilizer"]))
    if share.get("pesticide", 0) > 20:
        out.append(msg("cost.pest", "warn", p=share["pesticide"]))
    if share.get("labour", 0) > 40:
        out.append(msg("cost.labour", p=share["labour"]))
    return out or [msg("cost.ok", "good")]


SMALL_PROFIT_ROI = 15.0  # ROI % below which a profit is flagged "small"


def _status(profit_per_acre: float, invested: float) -> str:
    if profit_per_acre < 0:
        return "loss"
    return "small" if profit_per_acre / invested * 100 < SMALL_PROFIT_ROI else "profit"


def profit_calc(invested_per_acre: float, yield_q_per_acre: float, other_per_quintal: float,
                price: float, target_profit_per_acre: float | None = None) -> dict:
    """Per-acre profit calculator (all money in Rs, quantities in quintals)."""
    def at(p: float) -> dict:
        per_q = p - invested_per_acre / yield_q_per_acre - other_per_quintal
        per_acre = per_q * yield_q_per_acre
        return {"price": round(p, 2), "profit_per_quintal": round(per_q, 2),
                "profit_per_acre": round(per_acre, 2),
                "status": _status(per_acre, invested_per_acre)}

    break_even = invested_per_acre / yield_q_per_acre + other_per_quintal
    base = at(price)
    prices = sorted({round(price * m / 50) * 50 for m in (0.75, 0.85, 1.1, 1.25)} - {round(price)})
    scen = [{**at(p), "yours": False} for p in prices if p > 0]
    scen.append({**base, "yours": True})
    scen.sort(key=lambda r: r["price"])
    out = {**base, "invested_per_acre": invested_per_acre, "yield_q_per_acre": yield_q_per_acre,
           "other_per_quintal": other_per_quintal,
           "revenue_per_acre": round(price * yield_q_per_acre, 2),
           "roi_pct": round(base["profit_per_acre"] / invested_per_acre * 100, 1),
           "break_even_price": round(break_even, 2), "scenarios": scen}
    if target_profit_per_acre is not None:
        out["price_for_target"] = round(
            (invested_per_acre + target_profit_per_acre) / yield_q_per_acre + other_per_quintal, 2)
    return out
