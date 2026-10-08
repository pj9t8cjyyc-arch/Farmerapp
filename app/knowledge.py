"""Loads the crop calendar knowledge base (app/knowledge/crops.json) and checks it is internally consistent."""
import json
from pathlib import Path

from . import crops

KB: dict = {k: v for k, v in json.loads(
    (Path(__file__).parent / "knowledge" / "crops.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}


def stage_at(crop: str, das: int) -> dict:
    stages = KB[crop]["stages"]
    for s in stages:
        if s["das"][0] <= das < s["das"][1]:
            return s
    return stages[0] if das < 0 else stages[-1]


def kc_at(crop: str, das: int) -> float:
    return stage_at(crop, max(das, 0))["kc"]


def problems() -> list[str]:
    """Return a list of consistency problems (empty = OK). Run by the test-suite after every edit of crops.json."""
    out = []
    for k in crops.CROPS:
        if k not in KB:
            out.append(f"{k}: missing from knowledge base")
            continue
        c = KB[k]
        st = c["stages"]
        if st[0]["das"][0] != 0:
            out.append(f"{k}: first stage must start at day 0")
        for a, b in zip(st, st[1:]):
            if a["das"][1] != b["das"][0]:
                out.append(f"{k}: stages {a['key']} -> {b['key']} are not contiguous")
        for s in st:
            if not (s["das"][0] < s["das"][1] and 0 < s["kc"] <= 1.5 and s["en"] and s["te"]):
                out.append(f"{k}: bad stage {s['key']}")
        dur = c["duration_days"]
        if not (dur[0] <= dur[1]) or st[-1]["das"][1] < dur[0]:
            out.append(f"{k}: duration {dur} does not match stages")
        for nut in "NPK":
            tot = sum(e[nut] for e in c["fertilizer"])
            if abs(tot - 1) > 0.02:
                out.append(f"{k}: {nut} fractions add up to {tot:.2f}, not 1")
        keys = [e["key"] for e in c["fertilizer"]]
        if len(set(keys)) != len(keys):
            out.append(f"{k}: duplicate fertilizer keys")
        for e in c["fertilizer"]:
            if not (e["das"][0] <= e["das"][1] and e["en"] and e["te"]):
                out.append(f"{k}: bad fertilizer event {e['key']}")
        ir = c["irrigation"]
        if ir["mode"] not in ("deficit", "ponded"):
            out.append(f"{k}: irrigation mode must be deficit or ponded")
        if ir["mode"] == "deficit" and not (ir["depletion_mm"] > 0 and ir["interval_days"] > 0):
            out.append(f"{k}: deficit crops need depletion_mm and interval_days")
        for w in ir["critical"]:
            if not (w["das"][0] < w["das"][1] and w["en"] and w["te"]):
                out.append(f"{k}: bad critical irrigation window")
    return out
