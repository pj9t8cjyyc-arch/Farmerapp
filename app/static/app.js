const $ = id => document.getElementById(id);
const BASE = window.API_BASE || "";
const rs = n => n == null ? "–" : "₹" + Number(n).toLocaleString("en-IN", {maximumFractionDigits: 0});
const sign = v => (v >= 0 ? "+ " : "− ") + rs(Math.abs(v));
const charts = {};
// view = "all" (whole farm) or a crop key; crop is null in the all view
let meta, view = "all", crop = null, targetVal = "20000";
let S = {ov: null, dash: null, prices: null, exp: [], sales: [], plots: [], fert: null, calc: null, msp: {}};

async function api(path, opt) {
  const r = await fetch(BASE + path, opt);
  if (!r.ok) { let m = r.statusText; try { m = JSON.stringify((await r.json()).detail); } catch {} throw new Error(m); }
  return r.json();
}
const post = (p, b) => api(p, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b)});
function el(t, txt, cls) { const e = document.createElement(t); if (txt != null) e.textContent = txt; if (cls) e.className = cls; return e; }
const tips = (box, list) => box.replaceChildren(...list.map(m => el("div", pick(m), "tip " + m.level)));
function chart(id, cfg) { charts[id]?.destroy(); if (window.Chart) charts[id] = new Chart($(id), cfg); }
function table(t, head, rows, cls) {
  t.replaceChildren(); const h = el("tr"); head.forEach(x => h.append(el("th", x))); t.append(h);
  rows.forEach((r, i) => { const tr = el("tr", null, cls ? cls[i] : ""); r.forEach(c => { const td = el("td"); c instanceof Node ? td.append(c) : td.textContent = c; tr.append(td); }); t.append(tr); });
}
function delBtn(url) { const b = el("button", "✕", "s"); b.title = L("del"); b.onclick = async () => { await api(url, {method: "DELETE"}); load(); }; return b; }
const num = v => v === "" || v == null || isNaN(v) ? null : Number(v);
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
};
const daysAgo = d => Math.max(0, Math.round((Date.now() - new Date(d)) / 864e5));

// ---------- view switching ----------
function setView(v) {
  view = v; crop = v === "all" ? null : v; store.set("view", v);
  document.body.dataset.view = v === "all" ? "all" : "crop";
  S.calc = null; S.fert = null;
  if (crop) restoreCalc();
}
async function go(v) {
  try { setView(v); await load(); window.scrollTo({top: 0}); if (crop) calcRun(); }
  catch (e) { alert(L("errPrefix") + ": " + e.message); }
}
function renderChips() {
  const nav = $("chips"); nav.replaceChildren();
  const mk = (label, on, fn, cls, dot) => {
    const b = el("button", null, "chip" + (on ? " on" : "") + (cls ? " " + cls : ""));
    if (dot) b.append(el("i", null, "dot " + dot));
    b.append(document.createTextNode(label)); b.setAttribute("aria-pressed", on); b.onclick = fn; nav.append(b);
  };
  mk(L("allCrops"), view === "all", () => go("all"));
  const list = [...(S.ov?.crops || [])];
  if (crop && !list.some(c => c.crop === crop)) list.push({crop, status: "pending"});
  list.forEach(c => mk(cropName(c.crop), c.crop === view, () => go(c.crop), "", {profit: "green", loss: "red", pending: "grey"}[c.status]));
  mk("+ " + L("addCrop"), false, async () => { await go("all"); $("addCrop").scrollIntoView({behavior: "smooth"}); }, "add");
  nav.querySelector(".on")?.scrollIntoView({inline: "center", block: "nearest"});
}

// ---------- render (pure: uses cached state, so a language switch needs no refetch) ----------
function renderCards() {
  const ov = S.ov, box = $("cropCards"), none = $("emptyNote");
  none.hidden = ov.crops.length > 0; none.textContent = L("noCrops");
  box.replaceChildren(...ov.crops.map(c => {
    const b = el("button", null, "cc"); b.type = "button"; b.onclick = () => go(c.crop);
    const nm = el("div", null, "nm"); nm.append(el("i", null, "dot " + {profit: "green", loss: "red", pending: "grey"}[c.status]), el("span", cropName(c.crop)));
    const pending = c.status === "pending";
    const big = el("div", pending ? rs(c.total_cost) : sign(c.profit), "big num " + (pending ? "" : c.profit >= 0 ? "pos" : "neg"));
    const tr = c.expected_change_pct;
    const price = el("div", null, "sm");
    price.append(document.createTextNode(L("priceNow") + ": " + rs(c.current_price) + "  "));
    if (tr != null) price.append(el("span", (tr >= 0 ? "▲ +" : "▼ ") + tr.toFixed(1) + "% · " + L("next14"), tr >= 0 ? "up" : "dn"));
    b.append(nm, el("div", pending ? L("spentSoFar") : L("profit"), "sm"), big,
      el("div", L("acreN", {a: c.area_acre}) + " · " + L("totalCost") + " " + rs(c.total_cost) + (pending ? "" : " · " + L("revenue") + " " + rs(c.revenue)), "sm"), price);
    if (c.last_activity) b.append(el("div", L("lastAct", {d: c.last_activity}), "sm"));
    return b;
  }));
}
function renderHead() {
  const d = S.dash, cur = (S.ov.crops.find(c => c.crop === crop)) || {};
  $("headTitle").textContent = cropName(crop);
  $("headInfo").textContent = L("acreN", {a: cur.area_acre ?? 0}) + " · " + L("totalCost") + " " + rs(d.total_cost) + " · " + L("revenue") + " " + rs(d.revenue);
  const t = $("plotTbl");
  if (!S.plots.length) { t.replaceChildren(el("caption", L("noPlots"), "mut")); return; }
  table(t, [L("acres"), L("sowing"), L("note"), ""], S.plots.map(p => [p.area_acre,
    p.sowing_date ? L("sown", {d: p.sowing_date, n: daysAgo(p.sowing_date)}) : L("notSown"), p.note, delBtn("/api/plots/" + p.id)]));
}
function render() {
  document.querySelectorAll("[data-i]").forEach(e => e.textContent = L(e.dataset.i));
  document.querySelectorAll("#lang button").forEach(b => b.classList.toggle("on", b.dataset.l === LANG));
  if (meta) {
    const fill = (sel, items, name) => { const keep = sel.value; sel.replaceChildren(...items.map(c => { const o = el("option", name(c)); o.value = c; return o; })); if (keep) sel.value = keep; };
    fill(document.querySelector("#fe [name=category]"), meta.categories, catName);
    fill($("plotCrop"), meta.crops, cropName);
    if (crop) $("plotCrop").value = crop;
  }
  renderChips();
  $("calcTitle").textContent = L("calcTitle", {crop: crop || ""});
  renderCalc();
  const d = S.dash, ov = S.ov; if (!d || !ov) return;
  const all = view === "all";
  const demo = all ? ov.crops.some(c => c.price_source === "demo") : S.prices?.source !== "live";
  $("src").textContent = all && !ov.crops.length ? "" : L(demo ? (all ? "demoMix" : "demo") : "live"); $("src").className = "badge " + (demo ? "" : "live");
  $("src").style.display = $("src").textContent ? "" : "none";
  if (!all && S.prices) $("src").title = S.prices.note + (S.prices.refresh && !S.prices.refresh.ok ? " | " + S.prices.refresh.error : "");
  const k = all
    ? [["wholeFarm", L("acreN", {a: ov.totals.area_acre})], ["totalCost", rs(d.total_cost)], ["revenue", rs(d.revenue)], ["profit", sign(d.profit), d.profit >= 0 ? "pos" : "neg"]]
    : [["totalCost", rs(d.total_cost)], ["revenue", rs(d.revenue)], ["profit", sign(d.profit), d.profit >= 0 ? "pos" : "neg"],
       ["costAcre", rs(d.cost_per_acre)], ["costQ", rs(d.cost_per_quintal)], ["avgSale", rs(d.avg_sale_price)], ["mktNow", rs(d.current_price)]];
  $("kpis").replaceChildren(...k.map(([a, b, c]) => { const x = el("div", null, "card kpi"); x.style.margin = 0; x.append(el("b", b, c), el("span", L(a))); return x; }));
  tips($("cost"), d.cost_insights);
  const cats = Object.keys(d.expense_by_category);
  chart("catChart", {type: "doughnut", data: {labels: cats.map(catName), datasets: [{data: cats.map(c => d.expense_by_category[c])}]}});
  chart("monChart", {type: "bar", data: {labels: d.monthly_expenses.map(m => m.month), datasets: [{label: "₹", data: d.monthly_expenses.map(m => m.total), backgroundColor: "#2f7d32"}]}, options: {plugins: {legend: {display: false}}}});
  const withCrop = all ? [L("cropCol")] : [];
  table($("exp"), [L("date"), ...withCrop, L("category"), "₹", L("note"), ""], S.exp.slice(0, 15).map(e =>
    [e.date, ...(all ? [cropName(e.crop)] : []), catName(e.category), rs(e.amount), e.note, delBtn("/api/expenses/" + e.id)]));
  table($("sal"), [L("date"), ...withCrop, L("qtyShort"), L("rsQ"), L("market"), ""], S.sales.slice(0, 15).map(e =>
    [e.date, ...(all ? [cropName(e.crop)] : []), e.qty_quintal, rs(e.price_per_quintal), e.market, delBtn("/api/sales/" + e.id)]));
  if (all) return renderCards();
  renderHead();
  const p = S.prices;
  if (d.current_price) { const sl = $("slider"); sl.min = Math.round(d.current_price * 0.4 / 10) * 10; sl.max = Math.round(d.current_price * 1.6 / 10) * 10; sl.value = $("price").value || sl.value; }
  const mspM = S.msp[crop], mb = $("useMsp");
  mb.style.display = mspM || d.current_price ? "" : "none";
  mb.textContent = mspM ? L("useMsp", {season: mspM.season, price: mspM.price}) : L("useMarket", {price: Math.round(d.current_price || 0)});
  const fc = d.forecast, n = p.dates.length, fd = [];
  if (fc.ok) { const last = new Date(p.dates[n - 1]); for (let i = 1; i <= fc.horizon_days; i++) { const x = new Date(last); x.setDate(x.getDate() + i); fd.push(x.toISOString().slice(0, 10)); } }
  const pad = a => Array(n).fill(null).concat(a || []);
  chart("priceChart", {type: "line", data: {labels: p.dates.concat(fd), datasets: [
    {label: L("actual"), data: p.prices.concat(fd.map(() => null)), borderColor: "#2f7d32", pointRadius: 0, tension: .2},
    ...(fc.ok ? [{label: L("forecast"), data: pad(fc.forecast), borderColor: "#e08a00", borderDash: [6, 4], pointRadius: 0},
      {data: pad(fc.upper), borderColor: "transparent", backgroundColor: "rgba(224,138,0,.15)", pointRadius: 0, fill: "+1"},
      {data: pad(fc.lower), borderColor: "transparent", pointRadius: 0}] : [])]},
    options: {responsive: true, interaction: {mode: "index", intersect: false}, plugins: {legend: {labels: {filter: i => i.text}}}, scales: {x: {ticks: {maxTicksLimit: 6}}}}});
  $("fcinfo").textContent = fc.ok ? L("fcNote", {ch: fc.expected_change_pct, mape: fc.backtest_mape_pct ?? "n/a"}) : "";
  tips($("sell"), d.sell_advice);
  table($("mk"), [L("state"), L("market"), L("modal"), L("min"), L("max")], d.markets_today.map(m => [m.state, m.market, rs(m.modal), rs(m.lo), rs(m.hi)]));
  const f = S.fert, fb = $("fert"); fb.replaceChildren();
  if (f) {
    const r = f.soil_ratings, rr = x => L(x);
    fb.append(el("div", L("soilRatings", {v: [r.n, r.p, r.k].map(rr).join("/")}), "tip info"),
      el("div", L("nutrients", f.nutrient_kg), "tip info"),
      el("div", L("products", {dap: f.products_kg.DAP, urea: f.products_kg.Urea, mop: f.products_kg.MOP}), "tip good"),
      ...f.tips.map(m => el("div", pick(m), "tip " + m.level)));
  }
}

// ---------- profit calculator (numbers are remembered per crop) ----------
let calcSeq = 0;
function saveCalc() {
  if (!crop) return; const f = $("fc").elements;
  store.set("calc:" + crop, JSON.stringify({i: f.invested_per_acre.value, y: f.yield_q_per_acre.value, o: f.other_per_quintal.value, p: $("price").value, t: targetVal}));
}
function restoreCalc() {
  const f = $("fc").elements; let v = {}; try { v = JSON.parse(store.get("calc:" + crop) || "{}"); } catch {}
  f.invested_per_acre.value = v.i ?? ""; f.yield_q_per_acre.value = v.y ?? ""; f.other_per_quintal.value = v.o ?? "0";
  $("price").value = v.p ?? (S.msp[crop]?.price ?? ""); $("slider").value = $("price").value; targetVal = v.t ?? "20000";
}
function calcInputs() {
  const f = $("fc").elements;
  return {invested_per_acre: num(f.invested_per_acre.value), yield_q_per_acre: num(f.yield_q_per_acre.value),
    other_per_quintal: num(f.other_per_quintal.value) ?? 0, price: num($("price").value), target: num(targetVal)};
}
async function calcRun() {
  if (!crop) return;
  saveCalc();
  const i = calcInputs(), seq = ++calcSeq;
  if (!(i.invested_per_acre > 0 && i.yield_q_per_acre > 0 && i.price > 0)) { S.calc = null; return renderCalc(); }
  try {
    const r = await post("/api/calc/profit", {...i, target_profit_per_acre: i.target, target: undefined});
    if (seq === calcSeq) { S.calc = r; renderCalc(); }
  } catch (e) { if (seq === calcSeq) { S.calc = {error: e.message}; renderCalc(); } }
}
const DOT = {profit: "green", small: "org", loss: "red"};
function renderCalc() {
  const out = $("calcOut"), r = S.calc;
  out.replaceChildren();
  if (!r) return void out.append(el("div", L("fillCalc"), "mut"));
  if (r.error) return void out.append(el("div", L("errPrefix") + ": " + r.error, "tip warn"));
  const lab = {profit: "resProfit", small: "resSmall", loss: "resLoss"}[r.status];
  const res = el("div", null, "res " + r.status);
  res.append(el("div", L(lab), "sec"), el("div", L("perAcre") + ": " + sign(r.profit_per_acre), "big"));
  out.append(res);
  const row = (k, v, cls) => { const d = el("div", null, "row"); d.append(el("span", k), el("b", v, cls)); return d; };
  const rows = el("div"); rows.append(
    row(L("perAcre"), sign(r.profit_per_acre), r.profit_per_acre >= 0 ? "pos" : "neg"),
    row(L("perQuintal"), sign(r.profit_per_quintal), r.profit_per_quintal >= 0 ? "pos" : "neg"),
    row(L("roi"), Math.round(r.roi_pct) + "%", r.roi_pct >= 0 ? "pos" : "neg"), row(L("breakEven"), rs(r.break_even_price), "bl"));
  out.append(rows);
  out.append(el("div", L("targetTitle"), "sec"));
  const g = el("div"); g.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:8px;align-items:end";
  const ti = el("input"); ti.id = "target"; ti.type = "number"; ti.inputMode = "decimal"; ti.min = 0; ti.value = targetVal;
  ti.oninput = () => { targetVal = ti.value; calcRun(); };
  const w1 = el("div"); w1.append(el("label", L("targetIn")), ti);
  const w2 = el("div"); w2.append(el("label", L("sellAtLeast")), el("b", r.price_for_target != null ? rs(r.price_for_target) : "–", "bl")); w2.lastChild.style.fontSize = "22px";
  g.append(w1, w2); out.append(g);
  out.append(el("div", L("atPrices"), "sec"));
  const t = el("table");
  table(t, [L("priceQ"), L("perQuintal"), L("perAcre")], r.scenarios.map(s => {
    const c = el("span"); const d = el("i", null, "dot " + DOT[s.status]); d.style.marginRight = "6px";
    c.append(d, document.createTextNode(rs(s.price) + (s.yours ? " (" + L("yours") + ")" : "")));
    return [c, sign(s.profit_per_quintal), sign(s.profit_per_acre)];
  }), r.scenarios.map(s => s.status + (s.yours ? " yours" : "")));
  out.append(t);
  const lg = el("div", null, "legend");
  [["green", "resProfit"], ["org", "resSmall"], ["red", "resLoss"], ["blue", "moneyOut"]].forEach(([c, k]) => { const s = el("span"); s.append(el("i", null, "dot " + c), document.createTextNode(L(k))); lg.append(s); });
  out.append(lg, el("div", L("mspNote"), "mut"));
}

// ---------- data loading / wiring ----------
async function load(refresh) {
  const q = crop ? "?crop=" + crop : "";
  const common = [api("/api/overview"), api("/api/dashboard" + q), api("/api/expenses" + q), api("/api/sales" + q)];
  const [ov, d, ex, sa] = await Promise.all(common);
  Object.assign(S, {ov, dash: d, exp: ex, sales: sa, prices: null, plots: []});
  if (crop) {
    [S.prices, S.plots] = await Promise.all([api(`/api/prices/${crop}?days=90${refresh ? "&refresh=true" : ""}`), api("/api/plots?crop=" + crop)]);
    if (!$("price").value && d.current_price) { $("price").value = Math.round(d.current_price / 10) * 10; $("slider").value = $("price").value; }
  }
  render();
}
function formData(f) { const o = {}; new FormData(f).forEach((v, k) => { if (v !== "") o[k] = /^(date|sowing_date|note|market|category|crop)$/.test(k) ? v : Number(v); }); return o; }
function wire(id, url, after) {
  $(id).onsubmit = async e => {
    e.preventDefault();
    try { const r = await post(url, {crop, ...formData(e.target)}); if (after) { after(r); render(); } else { e.target.reset(); setDates(); load(); } }
    catch (x) { alert(L("errPrefix") + ": " + x.message); }
  };
}
function setDates() { document.querySelectorAll("input[name=date]").forEach(i => { if (!i.value) i.value = new Date().toISOString().slice(0, 10); }); }
wire("fe", "/api/expenses"); wire("fs", "/api/sales"); wire("ff", "/api/fertilizer/advice", r => S.fert = r);
$("fp").onsubmit = async e => {  // adding a plot also adds the crop to "My crops" and opens it
  e.preventDefault();
  try { const d = formData(e.target); await post("/api/plots", d); e.target.reset(); await go(d.crop); }
  catch (x) { alert(L("errPrefix") + ": " + x.message); }
};
document.querySelectorAll("#lang button").forEach(b => b.onclick = () => { setLang(b.dataset.l); render(); });
$("refresh").onclick = () => load(true).catch(e => alert(e.message));
$("fc").addEventListener("input", calcRun);
$("price").addEventListener("input", () => { $("slider").value = $("price").value; calcRun(); });
$("slider").addEventListener("input", () => { $("price").value = $("slider").value; calcRun(); });
$("useMsp").onclick = () => {
  const m = S.msp[crop], v = m ? m.price : Math.round(S.dash?.current_price || 0);
  if (v) { $("price").value = v; $("slider").value = v; calcRun(); }
};
(async () => {
  try {
    [meta, S.msp, S.ov] = await Promise.all([api("/api/meta"), api("/api/msp"), api("/api/overview")]);
    const saved = store.get("view"), keys = S.ov.crops.map(c => c.crop);
    setView(saved === "all" || keys.includes(saved) ? saved : keys.length === 1 ? keys[0] : "all");
    render(); setDates(); await load(); if (crop) calcRun();
  } catch (e) { alert(L("errPrefix") + ": " + e.message); }
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
})();
