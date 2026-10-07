"""Short-term price forecast: damped-trend Holt smoothing + honest backtest.

Uses ONLY the price history (no weather/arrival inputs). Accuracy is reported
as MAPE on a held-out tail so the farmer can see how far to trust it.
"""
import numpy as np

PHI = 0.9


def _fit(y: np.ndarray, a: float, b: float):
    level, trend = y[0], y[1] - y[0]
    sse = 0.0
    resid = []
    for t in range(1, len(y)):
        pred = level + PHI * trend
        e = y[t] - pred
        resid.append(e)
        sse += e * e
        new_level = a * y[t] + (1 - a) * pred
        trend = b * (new_level - level) + (1 - b) * PHI * trend
        level = new_level
    return level, trend, sse, np.array(resid)


def _best(y: np.ndarray):
    best = None
    for a in (0.2, 0.4, 0.6, 0.8):
        for b in (0.05, 0.1, 0.2, 0.4):
            r = _fit(y, a, b)
            if best is None or r[2] < best[2][2]:
                best = ((a, b), r[0:2], r)
    return best


def _project(level, trend, h):
    out, damp = [], 0.0
    for k in range(1, h + 1):
        damp += PHI ** k
        out.append(level + damp * trend)
    return np.array(out)


def forecast(prices: list[float], horizon: int = 14, holdout: int = 7) -> dict:
    y = np.asarray(prices, dtype=float)
    if len(y) < 14:
        return {"ok": False, "reason": "Need at least 14 days of price history"}
    horizon = max(1, min(horizon, 30))
    _, (level, trend), full = _best(y)
    point = _project(level, trend, horizon)
    sigma = float(np.std(full[3])) or 1e-9
    steps = np.arange(1, horizon + 1)
    band = 1.96 * sigma * np.sqrt(steps)
    # backtest on the tail
    mape = None
    if len(y) >= 14 + holdout:
        train, test = y[:-holdout], y[-holdout:]
        _, (l2, t2), _ = _best(train)
        pred = _project(l2, t2, holdout)
        mape = float(np.mean(np.abs((test - pred) / test)) * 100)
    last = float(y[-1])
    change_pct = float((point[-1] - last) / last * 100)
    return {
        "ok": True,
        "horizon_days": horizon,
        "last_price": round(last, 2),
        "forecast": [round(float(v), 2) for v in point],
        "lower": [round(float(max(v - b, 0)), 2) for v, b in zip(point, band)],
        "upper": [round(float(v + b), 2) for v, b in zip(point, band)],
        "expected_change_pct": round(change_pct, 2),
        "backtest_mape_pct": None if mape is None else round(mape, 2),
        "method": "damped-trend Holt smoothing on daily mean modal price",
    }
