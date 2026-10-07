"""Bundle the real website (app/static) + real backend answers into ONE self-contained HTML page
for sharing as a read-only preview (e.g. a Claude artifact). Nothing is re-implemented by hand:
GET answers are snapshots from the running FastAPI app; the two calculators are ports of
advice.profit_calc / advice.fertilizer_plan. Usage: python scripts/build_preview.py OUT.html [--local-chart]
"""
import json, os, re, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["FARMER_DB"] = os.path.join(tempfile.mkdtemp(), "preview.db")
os.environ.pop("DATA_GOV_API_KEY", None)
os.environ["FARMER_AUTH"] = "off"            # the preview is a single sample farmer
os.environ["FARMER_SAMPLE_WEATHER"] = "1"   # offline sample weather (labelled "sample" in the UI)
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from datetime import timedelta  # noqa: E402
from app import advice, clock, crops, i18n  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app)
SEED = {  # sample farm: one profit, one loss, one with no sales yet
    "maize": dict(area=1.5, sown="2026-07-01",
                  exp=[("2026-07-02", "seed", 6200), ("2026-07-05", "fertilizer", 15400), ("2026-07-20", "pesticide", 5100),
                       ("2026-08-03", "labour", 14800), ("2026-08-12", "irrigation", 4600), ("2026-09-02", "machinery", 7300),
                       ("2026-10-01", "transport", 2200)], sales=[("2026-10-02", 28, 2430, "Nizamabad")]),
    "chilli": dict(area=2, sown="2026-06-10",
                   exp=[("2026-06-12", "seed", 9000), ("2026-06-20", "fertilizer", 38000), ("2026-07-15", "pesticide", 26000),
                        ("2026-08-10", "labour", 52000), ("2026-08-25", "irrigation", 9000), ("2026-09-10", "machinery", 6000),
                        ("2026-09-28", "transport", 5000)], sales=[("2026-10-03", 10, 14000, "Guntur")]),
    "onion": dict(area=1, sown="2026-08-15",
                  exp=[("2026-08-16", "seed", 12000), ("2026-08-20", "fertilizer", 9000), ("2026-09-15", "labour", 8000)], sales=[]),
}
TODAY = clock.today()
ago = lambda n: (TODAY - timedelta(n)).isoformat()
PLAN_SEED = {  # crop: (planted days ago, water source, last watered days ago, fertilizer steps already logged)
    "maize": (40, "borewell", 8, ["basal"]),
    "chilli": (55, "drip", 3, ["basal", "top1"]),
    "onion": (12, "canal", 4, []),
}
assert c.put("/api/farm", json={"district": "Guntur", "lat": 16.3, "lon": 80.44}).status_code == 200
for k, v in SEED.items():
    planted, water, watered, logged = PLAN_SEED[k]
    pid = c.post("/api/plots", json={"crop": k, "area_acre": v["area"], "sowing_date": ago(planted), "irrigation": water}).json()["id"]
    c.post("/api/activities", json={"crop": k, "plot_id": pid, "kind": "irrigation", "date": ago(watered)})
    for key in logged:
        c.post("/api/activities", json={"crop": k, "plot_id": pid, "kind": "fertilizer", "task_key": key, "qty": 50, "unit": "kg", "date": ago(planted - 2)})
    for d, cat, amt in v["exp"]:
        assert c.post("/api/expenses", json={"crop": k, "date": d, "category": cat, "amount": amt}).status_code == 201
    for d, q, p, m in v["sales"]:
        assert c.post("/api/sales", json={"crop": k, "date": d, "qty_quintal": q, "price_per_quintal": p, "market": m}).status_code == 201

snap = {}
def grab(path):
    r = c.get(path); assert r.status_code == 200, path
    snap[path] = r.json()
for p in ("/api/meta", "/api/msp", "/api/overview", "/api/dashboard", "/api/expenses", "/api/sales", "/api/farm", "/api/districts", "/api/today", "/api/auth/config", "/api/auth/me"):
    grab(p)
for k in SEED:
    for p in (f"/api/dashboard?crop={k}", f"/api/expenses?crop={k}", f"/api/sales?crop={k}", f"/api/plots?crop={k}", f"/api/prices/{k}?days=90", f"/api/plan/{k}"):
        grab(p)
for k in crops.CROPS:  # crops the viewer may add are not seeded; keep lookups safe
    for p in (f"/api/dashboard?crop={k}", f"/api/prices/{k}?days=90", f"/api/plan/{k}"):
        if p not in snap:
            grab(p)

fert = {"crops": {k: v[2:5] for k, v in crops.CROPS.items()}, "factor": advice.FACTOR, "rating": advice.RATING,
        "msgs": {k: i18n.msg(f"fert.{k}", "warn" if k in ("acid", "alk") else "info")
                 for k in ("nosoil", "acid", "alk", "split", "confirm")}}

SHIM = """(() => {
const D = %s, F = %s;
const reply = (o, ok = true) => Promise.resolve(new Response(JSON.stringify(ok ? o : {detail: o}), {status: ok ? 200 : 400, headers: {"Content-Type": "application/json"}}));
let tm; function toast(t) { let e = document.getElementById("pvToast"); if (!e) { e = document.createElement("div"); e.id = "pvToast";
  e.style.cssText = "position:fixed;left:50%%;bottom:90px;transform:translateX(-50%%);background:#17261a;color:#fff;padding:8px 14px;border-radius:10px;font-size:13px;z-index:99;max-width:90vw;text-align:center"; document.body.append(e); }
  e.textContent = t; e.hidden = false; clearTimeout(tm); tm = setTimeout(() => e.hidden = true, 2800); }
function profit(b) {
  const inv = b.invested_per_acre, yl = b.yield_q_per_acre, oth = b.other_per_quintal || 0, price = b.price, r2 = x => Math.round(x * 100) / 100;
  const st = a => a < 0 ? "loss" : (a / inv * 100 < 15 ? "small" : "profit");
  const at = p => { const q = p - inv / yl - oth, a = q * yl; return {price: r2(p), profit_per_quintal: r2(q), profit_per_acre: r2(a), status: st(a)}; };
  const base = at(price);
  const ps = [...new Set([.75, .85, 1.1, 1.25].map(m => Math.round(price * m / 50) * 50))].filter(p => p > 0 && p !== Math.round(price));
  const sc = ps.map(p => ({...at(p), yours: false})); sc.push({...base, yours: true}); sc.sort((a, b) => a.price - b.price);
  const out = {...base, invested_per_acre: inv, yield_q_per_acre: yl, other_per_quintal: oth, revenue_per_acre: r2(price * yl),
    roi_pct: Math.round(base.profit_per_acre / inv * 1000) / 10, break_even_price: r2(inv / yl + oth), scenarios: sc};
  if (b.target_profit_per_acre != null) out.price_for_target = r2((inv + b.target_profit_per_acre) / yl + oth);
  return out;
}
function fert(b) {
  const [n, p, k] = F.crops[b.crop], rate = (x, v) => v == null ? "medium" : v < F.rating[x][0] ? "low" : v > F.rating[x][1] ? "high" : "medium";
  const r = {n: rate("n", b.soil_n), p: rate("p", b.soil_p), k: rate("k", b.soil_k)}, ha = b.area_acre / 2.47105;
  const need = {n: n * F.factor[r.n] * ha, p: p * F.factor[r.p] * ha, k: k * F.factor[r.k] * ha};
  const dap = need.p / .46, urea = Math.max(need.n - dap * .18, 0) / .46, mop = need.k / .6, r1 = x => Math.round(x * 10) / 10;
  const tips = []; if (b.soil_n == null && b.soil_p == null && b.soil_k == null) tips.push(F.msgs.nosoil);
  if (b.ph != null) { if (b.ph < 5.5) tips.push(F.msgs.acid); else if (b.ph > 8.5) tips.push(F.msgs.alk); }
  tips.push(F.msgs.split, F.msgs.confirm);
  return {crop: b.crop, area_acre: b.area_acre, soil_ratings: r, nutrient_kg: {n: r1(need.n), p: r1(need.p), k: r1(need.k)},
    products_kg: {DAP: r1(dap), Urea: r1(urea), MOP: r1(mop)}, tips};
}
window.fetch = (u, o = {}) => {
  const path = String(u).replace(/^https?:\\/\\/[^/]+/, "").replace("&refresh=true", ""), m = (o.method || "GET").toUpperCase();
  if (m === "GET") return path in D ? reply(D[path]) : reply("Not part of this preview", false);
  if (path === "/api/calc/profit") return reply(profit(JSON.parse(o.body)));
  if (path === "/api/fertilizer/advice") return reply(fert(JSON.parse(o.body)));
  if (path === "/api/onboard") return reply({plot_ids: []});
  if (path === "/api/auth/request") return reply({ok: true, cooldown_s: 30, dev_code: "123456"});
  if (path === "/api/auth/verify") return JSON.parse(o.body).code === "123456" ? reply({token: "preview", farmer: {id: 1, phone: "+919876543210"}, new: false}) : reply("Wrong code.", false);
  if (path === "/api/auth/logout") return reply({ok: true});
  if (path === "/api/farm") return reply(D["/api/farm"]);
  toast("Preview only: saving is turned off here"); return reply("Preview only: saving is turned off", false);
};
})();""" % (json.dumps(snap, ensure_ascii=False, separators=(",", ":")), json.dumps(fert, ensure_ascii=False, separators=(",", ":")))

static = ROOT / "app" / "static"
html = (static / "index.html").read_text(encoding="utf-8")
body = html[html.index("<body"):html.index("<script src=")]
body = re.sub(r"<body[^>]*>", "", body)
chart_src = (static / "vendor" / "chart.umd.js").as_uri() if "--local-chart" in sys.argv else \
    "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"
out = f"""<title>Farmer App</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Telugu:wght@400;600;700&display=swap">
<style>{(static / "style.css").read_text(encoding="utf-8")}
.pv{{background:var(--ac-soft);color:var(--fg);font-size:12px;text-align:center;padding:4px 8px}}
.pv button{{width:auto;min-height:0;padding:1px 10px;margin-left:8px;font-size:12px}}</style>
<div class="pv">Preview with sample farm data and sample weather. Saving is turned off here.
<button type="button" onclick="openWizard('first')">Try first-time setup</button>
<button type="button" onclick="S.auth={{required:true,channels:['whatsapp','sms'],dev:true}};openLogin()">Try sign-in (code 123456)</button>
<button type="button" onclick="openAccount()">Account menu</button></div>
{body}
<script>{SHIM}</script>
<script>{(static / "i18n.js").read_text(encoding="utf-8")}</script>
<script src="{chart_src}"></script>
<script>{(static / "wizard.js").read_text(encoding="utf-8")}</script>
<script>{(static / "auth.js").read_text(encoding="utf-8")}</script>
<script>{(static / "app.js").read_text(encoding="utf-8")}</script>
"""
Path(sys.argv[1]).write_text(out, encoding="utf-8")
print("wrote", sys.argv[1], f"{len(out)/1024:.0f} KB", "| snapshot keys:", len(snap))
