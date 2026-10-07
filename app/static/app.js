const $ = id => document.getElementById(id);
const BASE = window.API_BASE || "";
const rs = n => n == null ? "–" : "₹" + Number(n).toLocaleString("en-IN", {maximumFractionDigits: 0});
const sign = v => (v >= 0 ? "+ " : "− ") + rs(Math.abs(v));
const charts = {};
// view: "today" (home), "all" (whole-farm money overview) or a crop key. tab = open section of a crop (kept while swapping crops)
let meta, view = "today", crop = null, tab = "sum", moneyMode = "exp", targetVal = "20000", showAllTasks = false;
let S = {ov: null, today: null, plan: null, dash: null, prices: null, exp: [], sales: [], plots: [], fert: null, calc: null, msp: {}, farm: null, loadedAt: 0};
const TABS = [["sum", "tSum", "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"],
  ["plan", "tPlan", "M4 6h16v14H4zM4 10h16M8 3v4M16 3v4M8 14h3"],
  ["profit", "tProfit", "M6 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM8 7h8M8 12h2M12 12h2M8 16h2M12 16h2"],
  ["prices", "tPrices", "M3 17l6-6 4 4 8-9M15 6h6v6"],
  ["money", "tMoney", "M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM3 10h18M16 15h2"]];
const KIND_EM = {irrigation: "💧", fertilizer: "🧪", harvest: "🌾", setup: "📝"};

async function api(path, opt = {}) {
  const tok = store.get("token");
  const r = await fetch(BASE + path, {...opt, headers: {...(opt.headers || {}), ...(tok ? {Authorization: "Bearer " + tok} : {})}});
  if (r.status === 401 && !path.startsWith("/api/auth/")) { store.set("token", ""); openLogin(); const e = new Error("login required"); e.status = 401; throw e; }
  if (!r.ok) {
    let m = r.statusText; try { const d = (await r.json()).detail; m = typeof d === "string" ? d : JSON.stringify(d); } catch {}
    const e = new Error(m); e.status = r.status; throw e;
  }
  return r.json();
}
const oops = e => { if (e.message !== "login required") oops(e); };
const post = (p, b) => api(p, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b)});
function el(t, txt, cls) { const e = document.createElement(t); if (txt != null) e.textContent = txt; if (cls) e.className = cls; return e; }
const pk = (en, te) => LANG === "en" ? en : LANG === "te" ? te : te + "\n" + en;       // two lines in "both" mode
// text in the chosen language; in "both" mode Telugu leads and English follows in a smaller muted line
function bi(en, te, cls, tag = "div") {
  const e = el(tag, null, cls);
  if (LANG === "both") e.append(document.createTextNode(te), el("span", en, "bi-en"));
  else e.textContent = LANG === "te" ? te : en;
  return e;
}
const tips = (box, list) => box.replaceChildren(...list.map(m => bi(m.text, m.text_te, "tip " + m.level)));
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
function chart(id, cfg) {
  charts[id]?.destroy();
  if (!window.Chart) return;
  Chart.defaults.color = css("--mut"); Chart.defaults.borderColor = css("--bd");
  charts[id] = new Chart($(id), cfg);
}
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
const cropKeys = () => (S.ov?.crops || []).map(c => c.crop);
const STATUS_DOT = {profit: "green", loss: "red", pending: "grey"};
const locale = () => LANG === "te" ? "te-IN" : "en-IN";
const fmtD = iso => new Date(iso + "T00:00:00").toLocaleDateString(locale(), {day: "numeric", month: "short"});
const fmtRange = (a, b) => a === b ? fmtD(a) : fmtD(a) + " – " + fmtD(b);
function ago(iso) {
  const m = Math.max(0, Math.round((Date.now() - new Date(iso)) / 6e4));
  return m < 1 ? L("agoNow") : m < 60 ? L("agoMin", {n: m}) : L("agoHr", {n: Math.round(m / 60)});
}
let toastTimer;
function toast(text, undo) {
  const t = $("toast"); t.replaceChildren(el("span", text));
  if (undo) { const b = el("button", L("undo")); b.type = "button"; b.onclick = async () => { t.hidden = true; await undo(); }; t.append(b); }
  t.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => t.hidden = true, 7000);
}

// ---------- view / tab switching ----------
function setView(v) {
  view = v; crop = v === "today" || v === "all" ? null : v; store.set("view", v);
  S.calc = null; S.fert = null; S.plan = null;
  if (crop) restoreCalc();
}
async function go(v, dir) {
  try {
    setView(v); await load(); window.scrollTo({top: 0});
    const m = $("main"); m.classList.remove("swap-l", "swap-r"); void m.offsetWidth; if (dir) m.classList.add(dir > 0 ? "swap-l" : "swap-r");
    if (crop) calcRun();
  } catch (e) { oops(e); }
}
const order = () => ["today", "all", ...cropKeys()];
function step(dir) {  // swipe / arrows: Today -> All -> crop 1 -> crop 2 -> ... -> Today
  const keys = order(); if (keys.length < 2) return;
  go(keys[(keys.indexOf(view) + dir + keys.length) % keys.length], dir);
}
const keysDir = k => order().indexOf(k) > order().indexOf(view) ? 1 : -1;
function setTab(t) { tab = t; store.set("tab", t); renderTabs(); applyVisibility(); window.scrollTo({top: 0}); }
function applyVisibility() {
  const key = view === "today" ? "today" : view === "all" ? "all" : tab;
  document.body.dataset.view = view === "today" || view === "all" ? view : "crop"; document.body.dataset.tab = tab;
  document.querySelectorAll("[data-t]").forEach(e => { e.hidden = !e.dataset.t.split(" ").includes(key); });
  $("fe").hidden = moneyMode !== "exp"; $("fs").hidden = moneyMode !== "sale";
}

// ---------- header: crop tabs, section tabs ----------
function renderChips() {
  const nav = $("chips"); nav.replaceChildren();
  const mk = (kids, on, fn, cls) => {
    const b = el("button", null, "chip" + (on ? " on" : "") + (cls ? " " + cls : "")); b.type = "button";
    b.append(...kids); b.setAttribute("aria-pressed", on); b.onclick = fn; nav.append(b);
  };
  mk([el("span", "☀️", "em"), el("span", lines("Today", "ఈరోజు"))], view === "today", () => go("today", -1));
  mk([el("span", "🌾", "em"), el("span", lines("All crops", "అన్ని పంటలు"))], view === "all", () => go("all", keysDir("all")));
  const list = [...(S.ov?.crops || [])];
  if (crop && !list.some(c => c.crop === crop)) list.push({crop, status: "pending"});
  list.forEach(c => {
    const st = el("span", null, "st"); st.append(el("span", cropEm(c.crop), "em"), el("i", null, "dot " + STATUS_DOT[c.status]));
    mk([st, el("span", cropLines(c.crop))], c.crop === view, () => go(c.crop, keysDir(c.crop)));
  });
  mk([el("span", "+", "em"), el("span", L("addCrop"))], false, () => openWizard("add"), "add");
  nav.querySelector(".on")?.scrollIntoView({inline: "center", block: "nearest"});
}
function renderTabs() {
  const nav = $("tabs"); nav.replaceChildren();
  TABS.forEach(([id, key, d]) => {
    const b = el("button", null, "tab"); b.type = "button"; b.setAttribute("role", "tab"); b.setAttribute("aria-selected", id === tab);
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + d + '"/></svg>';  // static icon paths only
    b.append(el("span", lines(STR[key][0], STR[key][1]))); b.onclick = () => setTab(id); nav.append(b);
  });
}

// ---------- Today ----------
const wxEm = d => (d.rain || 0) >= 10 ? "🌧️" : (d.rain || 0) >= 2 ? "🌦️" : (d.pop || 0) >= 40 ? "⛅" : "☀️";
function renderTodayWx() {
  const T = S.today, box = $("todayWx"); if (!T) return;
  box.replaceChildren();
  const w = T.weather;
  if (T.farm.lat == null) {
    box.append(el("div", L("noLocCard")));
    const b = el("button", L("setLoc"), "ghost"); b.type = "button"; b.onclick = () => openWizard("place"); box.append(b); return;
  }
  if (!w.ok) { box.append(el("div", L("wxDown"), "mut")); return; }
  const c = w.current, top = el("div", null, "wx-top");
  top.append(el("span", Math.round(c.temp) + "°C", "wx-temp"), el("span", L("humidity", {h: Math.round(c.humidity)}), "mut"), el("span", L("wind", {w: Math.round(c.wind)}), "mut"));
  const strip = el("div", null, "wx-days"), today = T.as_of.slice(0, 10);
  w.days.filter(d => d.date >= today).slice(0, 7).forEach(d => {
    const x = el("div", null, "wx-day" + (d.date === today ? " today" : ""));
    x.append(el("span", new Date(d.date + "T00:00:00").toLocaleDateString(locale(), {weekday: "short"})), el("span", wxEm(d), "em"),
      el("b", Math.round(d.tmax) + "°"), el("span", (d.rain || 0) >= 1 ? Math.round(d.rain) + "mm" : "–", "r"));
    strip.append(x);
  });
  box.append(top, strip, el("div", w.source === "sample" ? L("wxSample") : L("wxUpdated", {t: ago(w.fetched_at)}) + (w.stale ? " ⚠" : ""), "mut"));
  box.lastChild.style.marginTop = "8px";
}
const snoozeKey = t => `snooze:${t.crop}:${t.plot_id}:${t.kind}:${t.key}`;
const snoozed = t => store.get(snoozeKey(t)) === S.today.as_of.slice(0, 10);
function taskCard(t, today) {
  const row = el("div", null, "task " + t.urgency);
  row.append(el("div", KIND_EM[t.kind] || "•", "ic"));
  const tt = el("div", null, "tt");
  tt.append(el("div", cropEm(t.crop) + " " + cropName(t.crop), "who"), bi(t.text, t.text_te, "what"));
  if (t.due && t.urgency !== "now") tt.append(el("div", L("dueOn", {d: fmtD(t.due)}), "who"));
  row.append(tt);
  const act = el("div", null, "act"), a = t.action;
  const label = !a ? "actOk" : {irrigation: "actWatered", fertilizer: "actDone", harvest: "actHarvested", setup: "actSetDate", plan: "actOpenPlan"}[a.kind];
  const main = el("button", (a ? {irrigation: "💧 ", fertilizer: "✓ ", harvest: "✓ "}[a.kind] || "" : "") + L(label)); main.type = "button"; main.onclick = () => doAction(t); act.append(main);
  if (today && a && a.kind !== "setup" && a.kind !== "plan") { const l = el("button", L("actLater"), "later"); l.type = "button"; l.onclick = () => { store.set(snoozeKey(t), S.today.as_of.slice(0, 10)); renderToday(); }; act.append(l); }
  row.append(act); return row;
}
async function doAction(t) {
  const a = t.action;
  if (!a) { store.set(snoozeKey(t), (S.today?.as_of || "").slice(0, 10)); return S.today ? renderToday() : null; }
  if (a.kind === "plan") { tab = "plan"; store.set("tab", "plan"); return go(t.crop, 1); }
  try {
    if (a.kind === "setup") { const p = (await api("/api/plots?crop=" + t.crop)).find(x => x.id === t.plot_id); return openWizard("edit", {plot: p}); }
    const r = await post("/api/activities", {crop: t.crop, plot_id: t.plot_id, kind: a.kind, task_key: a.task_key || "", qty: a.qty ?? null, unit: a.unit || ""});
    toast(L("saved") + " ✓", a.kind === "harvest" ? null : async () => { await api("/api/activities/" + r.id, {method: "DELETE"}); load(); });
    await load();
  } catch (e) { oops(e); }
}
function renderToday() {
  const T = S.today, ov = S.ov; if (!T || !ov) return;
  renderTodayWx();
  $("todayAlerts").replaceChildren(...T.alerts.filter(m => m.code !== "a.noloc").map(m => bi(m.text, m.text_te, "alert")));
  const box = $("todayTasks"); box.replaceChildren(el("h2", L("todayTitle")));
  const list = T.tasks.filter(t => !snoozed(t)), shown = showAllTasks ? list : list.slice(0, 3);
  if (!list.length) box.append(el("div", T.plots.length ? L("allDone") : L("noCrops"), "what"));
  else shown.forEach(t => box.append(taskCard(t, true)));
  if (list.length > 3) { const b = el("button", showAllTasks ? L("showLess") : L("showAll", {n: list.length}), "ghost"); b.type = "button"; b.onclick = () => { showAllTasks = !showAllTasks; renderToday(); }; box.append(b); }
  const cards = $("todayCrops"); cards.replaceChildren();
  if (!T.plots.length) { const b = el("button", L("setupFarm"), "big-btn"); b.type = "button"; b.onclick = () => openWizard(ov.crops.length ? "add" : "first"); cards.append(b); return; }
  T.plots.forEach(p => {
    const o = ov.crops.find(c => c.crop === p.crop) || {}, b = el("button", null, "cc"); b.type = "button"; b.onclick = () => go(p.crop, keysDir(p.crop));
    const nm = el("div", null, "nm"); nm.append(el("span", cropEm(p.crop), "em"), el("span", cropLines(p.crop)));
    b.append(nm);
    if (p.das == null) b.append(el("div", L("noDateYet"), "sm"));
    else {
      b.append(el("div", pk(p.stage.en, p.stage.te) + " · " + L("dayN", {n: p.das}), "sm"));
      const bg = el("div", null, "bar-bg prog"); const fg = el("div", null, "bar-fg"); fg.style.width = p.progress_pct + "%"; bg.append(fg); b.append(bg);
      b.append(el("div", L("harvestAbout", {d: fmtD(p.harvest_from)}), "sm"));
    }
    const tr = o.expected_change_pct, price = el("div", null, "sm");
    price.append(document.createTextNode(L("priceNow") + ": " + rs(o.current_price) + "  "));
    if (tr != null) price.append(el("span", (tr >= 0 ? "▲ +" : "▼ ") + tr.toFixed(1) + "%", tr >= 0 ? "up" : "dn"));
    b.append(price, el("div", L("acreN", {a: p.area_acre}), "sm")); cards.append(b);
  });
}

// ---------- Plan (crop tab) ----------
const WATER_KEY = {rainfed: "wzRain", borewell: "wzBore", canal: "wzCanal", drip: "wzDrip"};
async function logActivity(body, undoable = true) {
  try {
    const r = await post("/api/activities", body);
    toast(L("saved") + " ✓", undoable ? async () => { await api("/api/activities/" + r.id, {method: "DELETE"}); load(); } : null);
    await load();
  } catch (e) { oops(e); }
}
function renderPlan() {
  const P = S.plan, ids = ["planBanner", "planTasks", "irrig", "fertSched", "stages", "planTips", "guideline"];
  ids.forEach(i => $(i).replaceChildren());
  if (!P) return;
  if (!P.plot) {
    const b = el("button", L("addPlot"), "big-btn"); b.type = "button"; b.onclick = () => openWizard("add");
    $("planBanner").append(el("div", L("noPlot")), b); return;
  }
  const st = P.state, p = P.plot;
  // banner
  const ban = $("planBanner"), head = el("div", null, "wx-top");
  head.append(el("b", st.stage ? pk(st.stage.en, st.stage.te) : L("noDateYet")), st.das != null ? el("span", L("dayN", {n: st.das}), "mut") : el("span"));
  ban.append(el("div", L("stageLbl"), "mut"), head);
  if (st.das != null) { const bg = el("div", null, "bar-bg"), fg = el("div", null, "bar-fg"); fg.style.width = st.progress_pct + "%"; bg.append(fg); ban.append(bg, el("div", L("harvestAbout", {d: fmtD(st.harvest_from)}), "mut")); }
  ban.append(el("div", L("acreN", {a: p.area_acre}) + " · " + L(WATER_KEY[p.irrigation] || "wzBore") + (p.sowing_date ? " · " + fmtD(p.sowing_date) : ""), "mut"));
  const row = el("div", null, "row2"), ed = el("button", "✏️ " + L("edit"), "ghost"), hv = el("button", L("markHarvested"), "ghost");
  ed.type = hv.type = "button"; ed.onclick = () => openWizard("edit", {plot: p});
  hv.onclick = () => logActivity({crop: crop, plot_id: p.id, kind: "harvest"}, false);
  row.append(ed, hv); row.style.gridTemplateColumns = "1fr 1fr"; ban.append(row);
  // next steps
  const nt = $("planTasks"); nt.append(el("h2", L("nextSteps")));
  P.tasks.filter(t => !(t.kind === "irrigation" && t.key === "water" && t.urgency === "later")).slice(0, 6).forEach(t => nt.append(taskCard(t, false)));
  if (nt.children.length === 1) nt.replaceChildren();
  // irrigation
  const ir = $("irrig"), I = P.irrigation; ir.append(el("h2", "💧 " + L("waterTitle")));
  const wt = P.tasks.find(t => t.kind === "irrigation");
  if (wt) ir.append(bi(wt.text, wt.text_te, "tip " + (wt.urgency === "now" ? "warn" : "info")));
  if (I.deficit_mm != null && I.limit_mm) {
    const pct = Math.min(100, Math.round(I.deficit_mm / I.limit_mm * 100)), bg = el("div", null, "bar-bg"), fg = el("div", null, "bar-fg " + (pct >= 100 ? "full" : pct >= 70 ? "hot" : "water"));
    fg.style.width = pct + "%"; bg.append(fg);
    ir.append(bg, el("div", L("deficit", {d: Math.round(I.deficit_mm), t: I.limit_mm}) + ". " + L("deficitHelp"), "mut"));
  }
  const lastTxt = I.last ? (I.days_since === 0 ? L("todayWord") : L("daysAgoN", {n: I.days_since})) : "";
  ir.append(el("div", I.count ? L("waterCount", {n: I.count, d: lastTxt}) : L("waterNever"), "mut"));
  const wb = el("button", "💧 " + L("wateredToday"), "big-btn"); wb.type = "button"; wb.style.marginTop = "10px";
  wb.onclick = () => logActivity({crop, plot_id: p.id, kind: "irrigation"});
  const r2 = el("div", null, "row2"), dd = el("input"); dd.type = "date"; dd.max = new Date().toISOString().slice(0, 10); dd.value = dd.max;
  const ob = el("button", L("wateredOther"), "ghost"); ob.type = "button"; ob.style.margin = "0";
  ob.onclick = () => logActivity({crop, plot_id: p.id, kind: "irrigation", date: dd.value});
  r2.append(dd, ob); ir.append(wb, r2);
  // fertilizer schedule
  const fs = $("fertSched"); fs.append(el("h2", "🧪 " + L("fertTitle")));
  const TAG = {due: "stDue", overdue: "stOverdue", soon: "stSoon", later: "stLater", assumed: "stAssumed", missed: "stMissed"};
  P.calendar.fertilizer.forEach(e => {
    if (e.status === "assumed" || e.status === "missed") {   // earlier steps: one quiet line
      const q = el("div", null, "sched compact"), l = el("div"); l.append(el("span", L(TAG[e.status]), "tag"), el("span", pk(e.label, e.label_te).replace("\n", " · ")));
      q.append(l); fs.append(q); return;
    }
    const r = el("div", null, "sched"), left = el("div");
    const tag = e.status === "done" ? L("stDone", {d: fmtD(e.done_on)}) : L(TAG[e.status]);
    const tg = el("span", tag, "tag " + e.status);
    left.append(el("div"), el("small", fmtRange(e.from, e.to)), el("small", pk(e.products_text, e.products_text_te)));
    left.firstChild.append(tg, el("b", pk(e.label, e.label_te)));
    r.append(left);
    if (["due", "overdue", "soon", "later"].includes(e.status)) {
      const b = el("button", "✓ " + L("actDone")); b.type = "button";
      b.onclick = () => logActivity({crop, plot_id: p.id, kind: "fertilizer", task_key: e.key, qty: Object.values(e.products_kg).reduce((a, v) => a + v, 0), unit: "kg"});
      r.append(b);
    }
    fs.append(r);
  });
  // stages + key watering
  const sg = $("stages"); sg.append(el("summary", L("stagesTitle")));
  const today = new Date().toISOString().slice(0, 10);
  P.calendar.stages.forEach(s => { const r = el("div", null, "stage-row" + (today >= s.from && today < s.to ? " cur" : "")); r.append(el("span", pk(s.en, s.te)), el("span", fmtRange(s.from, s.to))); sg.append(r); });
  P.calendar.critical_irrigation.forEach(w => { const r = el("div", null, "stage-row"); r.append(el("span", "💧 " + L("keyWater") + ": " + pk(w.en, w.te)), el("span", fmtRange(w.from, w.to))); sg.append(r); });
  if (P.tips.length) { const t = $("planTips"); t.append(el("h2", L("tipsTitle"))); P.tips.forEach(m => t.append(bi(m.text, m.text_te, "tip info"))); }
  if (!P.reviewed) $("guideline").textContent = L("guideline");
}

// ---------- render (pure: uses cached state, so a language switch needs no refetch) ----------
function renderCards() {
  const ov = S.ov, box = $("cropCards"), none = $("emptyNote");
  none.hidden = ov.crops.length > 0 || view !== "all"; none.textContent = L("noCrops");
  box.replaceChildren(...ov.crops.map(c => {
    const b = el("button", null, "cc"); b.type = "button"; b.onclick = () => go(c.crop, 1);
    const nm = el("div", null, "nm"); nm.append(el("span", cropEm(c.crop), "em"), el("span", cropLines(c.crop)));
    const pending = c.status === "pending";
    const big = el("div", pending ? rs(c.total_cost) : sign(c.profit), "big num " + (pending ? "" : c.profit >= 0 ? "pos" : "neg"));
    const tr = c.expected_change_pct, price = el("div", null, "sm");
    price.append(document.createTextNode(L("priceNow") + ": " + rs(c.current_price) + "  "));
    if (tr != null) price.append(el("span", (tr >= 0 ? "▲ +" : "▼ ") + tr.toFixed(1) + "% · " + L("next14"), tr >= 0 ? "up" : "dn"));
    b.append(nm, el("div", pending ? L("spentSoFar") : L("profit"), "sm"), big,
      el("div", L("acreN", {a: c.area_acre}) + " · " + L("totalCost") + " " + rs(c.total_cost) + (pending ? "" : " · " + L("revenue") + " " + rs(c.revenue)), "sm"), price);
    return b;
  }));
}
function renderCropBar() {  // visible on every crop tab: which crop is open + previous / next arrows
  const keys = cropKeys(), i = keys.indexOf(crop);
  const nav = (txt, key, to) => { const b = el("button", txt, "nav"); b.type = "button"; b.title = L(key) + ": " + cropName(to); b.setAttribute("aria-label", L(key) + ": " + cropName(to)); b.onclick = () => go(to, key === "nextCrop" ? 1 : -1); return b; };
  const prev = keys.length > 1 ? keys[(i - 1 + keys.length) % keys.length] : null, next = keys.length > 1 ? keys[(i + 1) % keys.length] : null;
  const name = el("div", null, "hero-name"); name.append(el("span", cropEm(crop), "em"), el("b", cropLines(crop)));
  $("cropBar").replaceChildren(...(prev ? [nav("‹", "prevCrop", prev)] : []), name, ...(next ? [nav("›", "nextCrop", next)] : []));
}
function renderHero() {
  const d = S.dash, c = S.ov.crops.find(x => x.crop === crop) || {status: "pending", area_acre: 0}, pending = c.status === "pending";
  const pill = el("span", L(pending ? "noSales" : c.status === "loss" ? "resLoss" : "resProfit"), "pill " + c.status);
  const price = el("div", null, "hero-sub"), ch = d.forecast?.ok ? d.forecast.expected_change_pct : null;
  price.append(document.createTextNode(L("priceNow") + ": " + rs(d.current_price) + "  "));
  if (ch != null) price.append(el("span", (ch >= 0 ? "▲ +" : "▼ ") + ch.toFixed(1) + "% · " + L("next14"), ch >= 0 ? "up" : "dn"));
  $("hero").replaceChildren(pill,
    el("div", pending ? rs(d.total_cost) : sign(d.profit), "hero-big num " + (pending ? "" : d.profit >= 0 ? "pos" : "neg")),
    el("div", pending ? L("spentSoFar") : L("profit"), "hero-sub"),
    el("div", L("acreN", {a: c.area_acre}) + " · " + L("totalCost") + " " + rs(d.total_cost) + " · " + L("revenue") + " " + rs(d.revenue), "hero-sub"), price);
}
function renderPlots() {
  const t = $("plotTbl");
  if (!S.plots.length) { t.replaceChildren(el("caption", L("noPlots"), "mut")); return; }
  table(t, [L("acres"), L("sowing"), L("note"), ""], S.plots.map(p => [p.area_acre,
    p.sowing_date ? L("sown", {d: p.sowing_date, n: daysAgo(p.sowing_date)}) : L("notSown"), p.note, delBtn("/api/plots/" + p.id)]));
}
function kpis(box, list) {
  box.replaceChildren(...list.map(([a, b, c]) => { const x = el("div", null, "card kpi"); x.append(el("b", b, c), el("span", L(a))); return x; }));
}
function render() {
  document.querySelectorAll("[data-i]").forEach(e => e.textContent = L(e.dataset.i));
  document.querySelectorAll("#lang button").forEach(b => b.classList.toggle("on", b.dataset.l === LANG));
  document.querySelectorAll("#moneySeg button").forEach(b => { b.textContent = L(b.dataset.m === "exp" ? "mExp" : "mSale"); b.classList.toggle("on", b.dataset.m === moneyMode); });
  if (meta) {
    const fill = (sel, items, name) => { const keep = sel.value; sel.replaceChildren(...items.map(c => { const o = el("option", name(c)); o.value = c; return o; })); if (keep) sel.value = keep; };
    fill(document.querySelector("#fe [name=category]"), meta.categories, catName);
  }
  renderChips(); renderTabs(); applyVisibility();
  $("calcTitle").textContent = L("calcTitle", {crop: crop || ""});
  $("recTitle").textContent = L("recent");
  renderCalc();
  const ov = S.ov; if (!ov) return;
  const all = view === "all", dayView = view === "today";
  const demo = all || dayView ? ov.crops.some(c => c.price_source === "demo") : S.prices?.source !== "live";
  const strip = $("src"); strip.hidden = (all || dayView) && !ov.crops.length; strip.textContent = L(demo ? (all || dayView ? "demoMix" : "demo") : "live"); strip.className = "strip" + (demo ? "" : " live");
  if (!all && !dayView && S.prices) strip.title = S.prices.note + (S.prices.refresh && !S.prices.refresh.ok ? " | " + S.prices.refresh.error : "");
  const hint = $("hint"); hint.textContent = L("swipeHint"); hint.hidden = !!store.get("swiped") || ov.crops.length < 1;
  if (dayView) return renderToday();
  const d = S.dash; if (!d) return;
  tips($("cost"), d.cost_insights);
  const cats = Object.keys(d.expense_by_category);
  chart("catChart", {type: "doughnut", data: {labels: cats.map(catName), datasets: [{data: cats.map(c => d.expense_by_category[c])}]}});
  chart("monChart", {type: "bar", data: {labels: d.monthly_expenses.map(m => m.month), datasets: [{label: "₹", data: d.monthly_expenses.map(m => m.total), backgroundColor: "#2f7d32"}]}, options: {plugins: {legend: {display: false}}}});
  // one list for expenses and sales, newest first
  const rows = [...S.exp.map(e => ({date: e.date, kind: "exp", crop: e.crop, what: catName(e.category), amt: -e.amount, note: e.note, del: "/api/expenses/" + e.id})),
    ...S.sales.map(e => ({date: e.date, kind: "sale", crop: e.crop, what: e.qty_quintal + " q × " + rs(e.price_per_quintal), amt: e.qty_quintal * e.price_per_quintal, note: e.market, del: "/api/sales/" + e.id}))]
    .sort((a, b) => b.date.localeCompare(a.date)).slice(0, 20);
  table($("rec"), [L("date"), ...(all ? [L("cropCol")] : []), L("kind"), "₹", L("note"), ""], rows.map(r =>
    [r.date, ...(all ? [cropName(r.crop)] : []), L(r.kind === "exp" ? "kExp" : "kSale") + " · " + r.what,
     el("span", sign(r.amt), "num " + (r.amt >= 0 ? "pos" : "neg")), r.note || "", delBtn(r.del)]));
  if (all) { kpis($("kpisAll"), [["wholeFarm", L("acreN", {a: ov.totals.area_acre})], ["totalCost", rs(d.total_cost)], ["revenue", rs(d.revenue)], ["profit", sign(d.profit), d.profit >= 0 ? "pos" : "neg"]]); return renderCards(); }
  kpis($("kpisCrop"), [["costAcre", rs(d.cost_per_acre)], ["costQ", rs(d.cost_per_quintal)], ["avgSale", rs(d.avg_sale_price)], ["mktNow", rs(d.current_price)]]);
  renderCropBar(); renderHero(); renderPlots(); renderPlan();
  const p = S.prices;
  if (d.current_price) { const sl = $("slider"); sl.min = Math.round(d.current_price * 0.4 / 10) * 10; sl.max = Math.round(d.current_price * 1.6 / 10) * 10; sl.value = $("price").value || sl.value; }
  const mspM = S.msp[crop], mb = $("useMsp");
  mb.hidden = !(mspM || d.current_price);
  mb.textContent = mspM ? L("useMsp", {season: mspM.season, price: mspM.price}) : L("useMarket", {price: Math.round(d.current_price || 0)});
  const fc = d.forecast, n = p.dates.length, fd = [];
  if (fc.ok) { const last = new Date(p.dates[n - 1]); for (let i = 1; i <= fc.horizon_days; i++) { const x = new Date(last); x.setDate(x.getDate() + i); fd.push(x.toISOString().slice(0, 10)); } }
  const pad = a => Array(n).fill(null).concat(a || []);
  chart("priceChart", {type: "line", data: {labels: p.dates.concat(fd), datasets: [
    {label: L("actual"), data: p.prices.concat(fd.map(() => null)), borderColor: "#2f7d32", pointRadius: 0, tension: .2},
    ...(fc.ok ? [{label: L("forecast"), data: pad(fc.forecast), borderColor: "#e08a00", borderDash: [6, 4], pointRadius: 0},
      {data: pad(fc.upper), borderColor: "transparent", backgroundColor: "rgba(224,138,0,.15)", pointRadius: 0, fill: "+1"},
      {data: pad(fc.lower), borderColor: "transparent", pointRadius: 0}] : [])]},
    options: {responsive: true, interaction: {mode: "index", intersect: false}, plugins: {legend: {labels: {filter: i => i.text}}}, scales: {x: {ticks: {maxTicksLimit: 4, maxRotation: 0, autoSkip: true}}}}});
  $("fcinfo").textContent = fc.ok ? L("fcNote", {ch: fc.expected_change_pct, mape: fc.backtest_mape_pct ?? "n/a"}) : "";
  tips($("sell"), d.sell_advice);
  table($("mk"), [L("state"), L("market"), L("modal"), L("min"), L("max")], d.markets_today.map(m => [m.state, m.market, rs(m.modal), rs(m.lo), rs(m.hi)]));
  const f = S.fert, fb = $("fert"); fb.replaceChildren();
  if (f) {
    const r = f.soil_ratings, rr = x => L(x);
    fb.append(el("div", L("soilRatings", {v: [r.n, r.p, r.k].map(rr).join("/")}), "tip info"),
      el("div", L("nutrients", f.nutrient_kg), "tip info"),
      el("div", L("products", {dap: f.products_kg.DAP, urea: f.products_kg.Urea, mop: f.products_kg.MOP}), "tip good"),
      ...f.tips.map(m => bi(m.text, m.text_te, "tip " + m.level)));
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
  const g = el("div", null, "pair"); g.style.alignItems = "end";
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
  const sc = el("div", null, "scroll"); sc.append(t); out.append(sc);
  const lg = el("div", null, "legend");
  [["green", "resProfit"], ["org", "resSmall"], ["red", "resLoss"], ["blue", "moneyOut"]].forEach(([c, k]) => { const s = el("span"); s.append(el("i", null, "dot " + c), document.createTextNode(L(k))); lg.append(s); });
  out.append(lg, el("div", L("mspNote"), "mut"));
}

// ---------- data loading / live refresh / wiring ----------
async function load(refresh) {
  const q = crop ? "?crop=" + crop : "";
  if (view === "today") {
    const [ov, today] = await Promise.all([api("/api/overview"), api("/api/today")]);
    Object.assign(S, {ov, today, dash: null, prices: null, plan: null});
  } else {
    const [ov, d, ex, sa] = await Promise.all([api("/api/overview"), api("/api/dashboard" + q), api("/api/expenses" + q), api("/api/sales" + q)]);
    Object.assign(S, {ov, dash: d, exp: ex, sales: sa, prices: null, plots: [], plan: null});
    if (crop) {
      [S.prices, S.plots, S.plan] = await Promise.all([api(`/api/prices/${crop}?days=90${refresh ? "&refresh=true" : ""}`), api("/api/plots?crop=" + crop), api("/api/plan/" + crop)]);
      if (!$("price").value && d.current_price) { $("price").value = Math.round(d.current_price / 10) * 10; $("slider").value = $("price").value; }
    }
  }
  S.loadedAt = Date.now(); render();
}
// real-time: refresh every 5 minutes and when the app comes back to the foreground (not while typing or in the wizard)
function refreshLive() {
  if (document.visibilityState !== "visible" || !$("wizard").hidden || Date.now() - S.loadedAt < 60000) return;
  if (document.activeElement && /^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName)) return;
  load().catch(() => {});
}
setInterval(refreshLive, 5 * 60 * 1000);
setInterval(() => { if (view === "today" && document.visibilityState === "visible") renderTodayWx(); }, 60 * 1000);
document.addEventListener("visibilitychange", refreshLive);

function formData(f) { const o = {}; new FormData(f).forEach((v, k) => { if (v !== "") o[k] = /^(date|sowing_date|note|market|category|crop)$/.test(k) ? v : Number(v); }); return o; }
function wire(id, url, after) {
  $(id).onsubmit = async e => {
    e.preventDefault();
    try { const r = await post(url, {crop, ...formData(e.target)}); if (after) { after(r); render(); } else { e.target.reset(); setDates(); load(); } }
    catch (x) { oops(x); }
  };
}
function setDates() { document.querySelectorAll("input[name=date]").forEach(i => { if (!i.value) i.value = new Date().toISOString().slice(0, 10); }); }
wire("fe", "/api/expenses"); wire("fs", "/api/sales"); wire("ff", "/api/fertilizer/advice", r => S.fert = r);
document.querySelectorAll("#lang button").forEach(b => b.onclick = () => { setLang(b.dataset.l); render(); });
document.querySelectorAll("#moneySeg button").forEach(b => b.onclick = () => { moneyMode = b.dataset.m; render(); });
$("refresh").onclick = () => load(true).catch(oops);
$("fc").addEventListener("input", calcRun);
$("price").addEventListener("input", () => { $("slider").value = $("price").value; calcRun(); });
$("slider").addEventListener("input", () => { $("price").value = $("slider").value; calcRun(); });
$("useMsp").onclick = () => {
  const m = S.msp[crop], v = m ? m.price : Math.round(S.dash?.current_price || 0);
  if (v) { $("price").value = v; $("slider").value = v; calcRun(); }
};
// swipe left/right (or arrow keys) to change crop; ignored on scrollable/interactive areas
let tx = 0, ty = 0, ignore = true;
document.addEventListener("touchstart", e => {
  ignore = !$("wizard").hidden || !!e.target.closest("#chips,#tabs,.scroll,table,input,select,textarea,canvas,.seg,details");
  tx = e.touches[0].clientX; ty = e.touches[0].clientY;
}, {passive: true});
document.addEventListener("touchend", e => {
  if (ignore) return;
  const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
  if (Math.abs(dx) > 70 && Math.abs(dy) < 45 && Math.abs(dx) > 2 * Math.abs(dy)) { store.set("swiped", "1"); $("hint").hidden = true; step(dx < 0 ? 1 : -1); }
}, {passive: true});
document.addEventListener("keydown", e => {
  if (!$("wizard").hidden || e.target.closest("input,select,textarea") || e.altKey || e.ctrlKey || e.metaKey) return;
  if (e.key === "ArrowRight") step(1); else if (e.key === "ArrowLeft") step(-1);
});
$("acct").onclick = () => openAccount();
let swRegistered = false;
async function boot() {
  try {
    S.auth = await api("/api/auth/config");
    $("acct").hidden = !S.auth.required;
    if (S.auth.required && !store.get("token")) { openLogin(); return; }
    let districts;
    [meta, S.msp, S.ov, S.farm, districts] = await Promise.all([api("/api/meta"), api("/api/msp"), api("/api/overview"), api("/api/farm"), api("/api/districts")]);
    WZ.districts = districts;
    const saved = store.get("view") || "today", keys = cropKeys(), t = store.get("tab");
    if (TABS.some(x => x[0] === t)) tab = t;
    setView(saved === "today" || saved === "all" || keys.includes(saved) ? saved : "today");
    render(); setDates();
    if (!S.farm.onboarded && !store.get("skipSetup")) openWizard("first");
    await load(); if (crop) calcRun();
  } catch (e) { oops(e); }
  if (!swRegistered && "serviceWorker" in navigator) { swRegistered = true; navigator.serviceWorker.register("/sw.js").catch(() => {}); }
}
$("fc").addEventListener("submit", e => e.preventDefault());
boot();
