"""Live weather from Open-Meteo (free, no key): current conditions, 14 past + 7 forecast days incl. reference
evapotranspiration (ET0), which drives the irrigation advice. Cached for 30 minutes per location; if a refresh
fails the last good copy is returned with stale=True."""
import time

import httpx

from . import clock

URL = "https://api.open-meteo.com/v1/forecast"
TTL = 30 * 60
_cache: dict[tuple, tuple[float, dict]] = {}


def _raw(lat: float, lon: float) -> dict:
    r = httpx.get(URL, timeout=12, params={
        "latitude": lat, "longitude": lon, "timezone": "Asia/Kolkata", "past_days": 14, "forecast_days": 7,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,"
                 "et0_fao_evapotranspiration,wind_speed_10m_max"})
    r.raise_for_status()
    return r.json()


def _normalize(j: dict) -> dict:
    d, cur = j["daily"], j.get("current", {})
    days = []
    for i, day in enumerate(d["time"]):
        g = lambda k: (d.get(k) or [None] * len(d["time"]))[i]
        days.append({"date": day, "tmax": g("temperature_2m_max"), "tmin": g("temperature_2m_min"),
                     "rain": g("precipitation_sum") or 0.0, "pop": g("precipitation_probability_max"),
                     "et0": g("et0_fao_evapotranspiration"), "wind": g("wind_speed_10m_max")})
    return {"ok": True, "source": "open-meteo", "fetched_at": clock.now().isoformat(timespec="seconds"),
            "current": {"temp": cur.get("temperature_2m"), "humidity": cur.get("relative_humidity_2m"),
                        "rain": cur.get("precipitation"), "wind": cur.get("wind_speed_10m"), "code": cur.get("weather_code")},
            "days": days}


def get(lat: float | None, lon: float | None) -> dict:
    if lat is None or lon is None:
        return {"ok": False, "error": "no location"}
    key = (round(lat, 2), round(lon, 2))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    try:
        w = _normalize(_raw(lat, lon))
        _cache[key] = (time.time(), w)
        return w
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
        if hit:
            return {**hit[1], "stale": True}
        return {"ok": False, "error": f"{type(e).__name__}"}
