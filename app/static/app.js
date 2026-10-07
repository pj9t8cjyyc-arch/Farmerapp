const $ = id => document.getElementById(id);
const BASE = window.API_BASE || "";
const rs = n => n == null ? "–" : "₹" + Number(n).toLocaleString("en-IN", {maximumFractionDigits: 0});
const charts = {};
let meta, crop, S = {dash: null, prices: null, exp: [], sales: [], fert: null, calc: null, msp: {}};

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

// ---------- render (pure: uses cached state, so language switch needs no refetch) ----------
function render() {
  document.querySelectorAll("[data-i]").forEach(e => e.textContent = L(e.dataset.i));
  document.querySelectorAll("#lang button").forEach(b => b.classList.toggle("on", b.dataset.l === LANG));
  if (meta) {
    const sel = $("crop").value; $("crop").replaceChildren(...meta.crops.map(c => { const o = el("option", cropName(c)); o.value = c; return o; }));
    $("crop").value = sel || meta.crops[0];
    const cs = document.querySelector("#fe [name=category]"), cv = cs.value;
    cs.replaceChildren(...meta.categories.map(c => { const o = el("option", catName(c)); o.value = c; return o; })); if (cv) cs.value = cv;
  }
  $("calcTitle").textContent = L("calcTitle", {crop: crop || ""});
  renderCalc();
  const d = S.dash, p = S.prices; if (!d || !p) return;
  if (d.current_price) { const sl = $("slider"); sl.min = Math.round(d.current_price * 0.4 / 10) * 10; sl.max = Math.round(d.current_price * 1.6 / 10) * 10; sl.value = $("price").value || sl.value; }
  const live = p.source === "live";
  $("src").textContent = L(live ? "live" : "demo"); $("src").className = "badge " + (live ? "live" : "");
  $("src").title = p.note + (p.refresh && !p.refresh.ok ? " | " + p.refresh.error : "");
  const k = [["totalCost", rs(d.total_cost)], ["revenue", rs(d.revenue)], ["profit", rs(d.profit), d.profit >= 0 ? "pos" : "neg"],
    ["costAcre", rs(d.cost_per_acre)], ["costQ", rs(d.cost_per_quintal)], ["avgSale", rs(d.avg_sale_price)], ["mktNow", rs(d.current_price)]];
  $("kpis").replaceChildren(...k.map(([a, b, c]) => { const x = el("div", null, "card kpi"); x.style.margin = 0; x.append(el("b", b, c), el("span", L(a))); return x; }));
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
  tips($("sell"), d.sell_advice); tips($("cost"), d.cost_insights);
  const cats = Object.keys(d.expense_by_category);
  chart("catChart", {type: "doughnut", data: {labels: cats.map(catName), datasets: [{data: cats.map(c => d.expense_by_category[c])}]}});
  chart("monChart", {type: "bar", data: {labels: d.monthly_expenses.map(m => m.month), datasets: [{label: "₹", data: d.monthly_expenses.map(m => m.total), backgroundColor: "#2f7d32"}]}, options: {plugins: {legend: {display: false}}}});
  table($("mk"), [L("state"), L("market"), L("modal"), L("min"), L("max")], d.markets_today.map(m => [m.state, m.market, rs(m.modal), rs(m.lo), rs(m.hi)]));
  table($("exp"), [L("date"), L("category"), "₹", L("note"), ""], S.exp.slice(0, 15).map(e => [e.date, catName(e.category), rs(e.amount), e.note, delBtn("/api/expenses/" + e.id)]));
  table($("sal"), [L("date"), L("qtyShort"), L("rsQ"), L("market"), ""], S.sales.slice(0, 15).map(e => [e.date, e.qty_quintal, rs(e.price_per_quintal), e.market, delBtn("/api/sales/" + e.id)]));
  const f = S.fert, fb = $("fert"); fb.replaceChildren();
  if (f) {
    const r = f.soil_ratings, rr = x => L(x);
    fb.append(el("div", L("soilRatings", {v: [r.n, r.p, r.k].map(rr).join("/")}), "tip info"),
      el("div", L("nutrients", f.nutrient_kg), "tip info"),
      el("div", L("products", {dap: f.products_kg.DAP, urea: f.products_kg.Urea, mop: f.products_kg.MOP}), "tip good"),
      ...f.tips.map(m => el("div", pick(m), "tip " + m.level)));
  }
}

// ---------- profit calculator ----------
let calcSeq = 0;
function calcInputs() {
  const f = $("fc").elements;
  return {invested_per_acre: num(f.invested_per_acre.value), yield_q_per_acre: num(f.yield_q_per_acre.value),
    other_per_quintal: num(f.other_per_quintal.value) ?? 0, price: num($("price").value), target: num($("target")?.value ?? "20000")};
}
async function calcRun() {
  const i = calcInputs(), seq = ++calcSeq;
  if (!(i.invested_per_acre > 0 && i.yield_q_per_acre > 0 && i.price > 0)) { S.calc = null; return renderCalc(); }
  try {
    const r = await post("/api/calc/profit", {...i, target_profit_per_acre: i.target, target: undefined});
    if (seq === calcSeq) { S.calc = r; renderCalc(); }
  } catch (e) { if (seq === calcSeq) { S.calc = {error: e.message}; renderCalc(); } }
}
const sign = v => (v >= 0 ? "+ " : "− ") + rs(Math.abs(v));
const DOT = {profit: "green", small: "org", loss: "red"};
function renderCalc() {
  const out = $("calcOut"), r = S.calc, keepTarget = $("target")?.value ?? "20000";
  const m = S.msp[crop], b = $("useMsp");
  b.style.display = m ? "" : "none"; if (m) b.textContent = L("useMsp", {season: m.season, price: m.price});
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
  const ti = el("input"); ti.id = "target"; ti.type = "number"; ti.inputMode = "decimal"; ti.min = 0; ti.value = keepTarget; ti.oninput = calcRun;
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
  crop = $("crop").value;
  const [d, p, ex, sa] = await Promise.all([api("/api/dashboard?crop=" + crop), api(`/api/prices/${crop}?days=90${refresh ? "&refresh=true" : ""}`),
    api("/api/expenses?crop=" + crop), api("/api/sales?crop=" + crop)]);
  Object.assign(S, {dash: d, prices: p, exp: ex, sales: sa}); render();
}
function formData(f) { const o = {}; new FormData(f).forEach((v, k) => { if (v !== "") o[k] = /^(date|sowing_date|note|market|category)$/.test(k) ? v : Number(v); }); return o; }
function wire(id, url, after) {
  $(id).onsubmit = async e => {
    e.preventDefault();
    try { const r = await post(url, {crop, ...formData(e.target)}); if (after) { after(r); render(); } else { e.target.reset(); setDates(); load(); } }
    catch (x) { alert(L("errPrefix") + ": " + x.message); }
  };
}
function setDates() { document.querySelectorAll("input[name=date]").forEach(i => { if (!i.value) i.value = new Date().toISOString().slice(0, 10); }); }
wire("fe", "/api/expenses"); wire("fs", "/api/sales"); wire("fp", "/api/plots"); wire("ff", "/api/fertilizer/advice", r => S.fert = r);
document.querySelectorAll("#lang button").forEach(b => b.onclick = () => { setLang(b.dataset.l); render(); });
$("crop").onchange = () => { S.calc = null; load().then(calcRun); };
$("refresh").onclick = () => load(true).catch(e => alert(e.message));
$("fc").addEventListener("input", calcRun);
$("price").addEventListener("input", () => { $("slider").value = $("price").value; calcRun(); });
$("slider").addEventListener("input", () => { $("price").value = $("slider").value; calcRun(); });
$("useMsp").onclick = () => { const m = S.msp[crop]; if (m) { $("price").value = m.price; $("slider").value = m.price; calcRun(); } };
(async () => {
  [meta, S.msp] = await Promise.all([api("/api/meta"), api("/api/msp")]);
  crop = meta.crops[0]; render(); setDates();
  await load().catch(e => alert(e.message));
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
})();
