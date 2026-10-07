// One-minute setup: language -> place -> crops -> (per crop) acres, planting date, water source.
// Also used to add more crops later ("add") and to fix a plot's details ("edit"). Uses helpers from app.js.
const WZ = {mode: "first", step: "lang", farm: {district: "", lat: null, lon: null}, picks: [], i: 0, crops: {}, plotId: null, busy: false, err: "", locOk: false};
const WHEN = [["notyet", "wzNotYet"], ["week", "wzWeek"], ["weeks", "wzWeeks"], ["months", "wzMonths"], ["pick", "wzPick"]];
const WATER = [["rainfed", "wzRain"], ["borewell", "wzBore"], ["canal", "wzCanal"], ["drip", "wzDrip"]];
const isoDay = n => { const d = new Date(Date.now() + 5.5 * 36e5); d.setUTCDate(d.getUTCDate() - n); return d.toISOString().slice(0, 10); };
const WHEN_DAYS = {week: 3, weeks: 21, months: 45};

function wzCrop(c) { return WZ.crops[c] ||= {area: 1, when: null, date: "", water: "borewell", last: null}; }
function wzDate(c) { const x = wzCrop(c); return x.when === "pick" ? (x.date || null) : x.when in WHEN_DAYS ? isoDay(WHEN_DAYS[x.when]) : null; }
function wzReady(c) { const x = wzCrop(c); return x.area > 0 && x.when && (x.when !== "pick" || x.date); }

function openWizard(mode = "first", opts = {}) {
  Object.assign(WZ, {mode, busy: false, err: "", i: 0, picks: [], crops: {}, plotId: null});
  if (mode === "first") WZ.step = "lang";
  else if (mode === "add") WZ.step = "crops";
  else if (mode === "place") WZ.step = "place";
  else if (mode === "edit") {   // opts.plot: an existing plot row
    const p = opts.plot; WZ.plotId = p.id; WZ.picks = [p.crop]; WZ.step = "crop";
    WZ.crops[p.crop] = {area: p.area_acre, when: p.sowing_date ? "pick" : null, date: p.sowing_date || "", water: p.irrigation || "borewell"};
  }
  $("wizard").hidden = false; document.body.style.overflow = "hidden"; wzRender();
}
function closeWizard() { $("wizard").hidden = true; document.body.style.overflow = ""; }
function wzGo(step) { WZ.step = step; WZ.err = ""; wzRender(); $("wizard").scrollTo({top: 0}); }

function wzDots() {
  const steps = WZ.mode === "first" ? ["lang", "place", "crops", "crop", "done"] : WZ.mode === "add" ? ["crops", "crop", "done"] : ["crop"];
  if (WZ.mode === "place") steps.splice(0, 1, "place");
  const d = el("div", null, "wz-dots"); steps.forEach(s => d.append(el("i", null, s === WZ.step ? "on" : "")));
  return d;
}
function wzOpt(label, on, fn, cls) { const b = el("button", label, "opt" + (on ? " on" : "") + (cls ? " " + cls : "")); b.type = "button"; b.onclick = fn; return b; }
function wzGoBtn(label, fn, enabled = true) { const b = el("button", label, "go"); b.type = "button"; b.disabled = !enabled; b.onclick = fn; return b; }

function wzRender() {
  const root = el("div", null, "wz"), top = el("div", null, "wz-top");
  top.append(wzDots());
  const seg = el("div", null, "seg");
  [["te", "తె"], ["en", "EN"], ["both", "తె·EN"]].forEach(([l, t]) => { const b = el("button", t, LANG === l ? "on" : ""); b.type = "button"; b.onclick = () => { setLang(l); render(); wzRender(); }; seg.append(b); });
  top.append(seg);
  if (WZ.mode !== "first") { const x = el("button", "✕", "ico"); x.type = "button"; x.setAttribute("aria-label", L("wzClose")); x.onclick = closeWizard; top.append(x); }
  root.append(top);
  ({lang: wzLang, place: wzPlace, crops: wzCrops, crop: wzCropStep, done: wzDone})[WZ.step](root);
  $("wizard").replaceChildren(root);
}

function wzLang(root) {
  root.append(el("h2", L("wzWelcome")), el("div", L("wzLang"), "sub"));
  [["te", "తెలుగు"], ["en", "English"], ["both", "తెలుగు · English"]].forEach(([l, t]) => root.append(wzOpt(t, LANG === l, () => { setLang(l); render(); wzRender(); })));
  const skip = el("button", L("wzSkip"), "link"); skip.type = "button"; skip.onclick = () => { store.set("skipSetup", "1"); closeWizard(); };
  root.append(wzGoBtn(L("wzNext"), () => wzGo("place")), skip);
}

function wzPlace(root) {
  root.append(el("h2", L("wzPlace")), el("div", L("wzWhyLoc"), "sub"));
  const use = wzOpt(L("wzUseLoc"), WZ.locOk, () => {
    if (!navigator.geolocation) { WZ.err = L("wzLocFail"); return wzRender(); }
    navigator.geolocation.getCurrentPosition(
      p => { Object.assign(WZ.farm, {lat: +p.coords.latitude.toFixed(3), lon: +p.coords.longitude.toFixed(3), district: ""}); WZ.locOk = true; WZ.err = ""; wzRender(); },
      () => { WZ.err = L("wzLocFail"); wzRender(); }, {timeout: 10000, maximumAge: 6e5});
  });
  root.append(use);
  if (WZ.locOk) root.append(el("div", L("wzLocOk"), "pos"));
  root.append(el("div", L("wzOrDistrict"), "sub"));
  const sel = el("select"); sel.append(Object.assign(el("option", L("wzChoose")), {value: ""}));
  (WZ.districts || []).forEach(d => sel.append(Object.assign(el("option", LANG === "en" ? `${d.name}, ${d.state}` : LANG === "te" ? d.te : `${d.te} · ${d.name}`), {value: d.name})));
  sel.value = WZ.farm.district || "";
  sel.onchange = () => { const d = (WZ.districts || []).find(x => x.name === sel.value); if (d) { Object.assign(WZ.farm, {district: d.name, lat: d.lat, lon: d.lon}); WZ.locOk = false; } wzRender(); };
  root.append(sel);
  if (WZ.err) root.append(el("div", WZ.err, "err"));
  const has = WZ.farm.lat != null;
  if (WZ.mode === "place") {   // location only: save to the farm profile and refresh
    root.append(wzGoBtn(L("wzSave"), async () => {
      try { await api("/api/farm", {method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify(WZ.farm)}); closeWizard(); await load(); }
      catch (e) { WZ.err = L("wzErr", {e: e.message}); wzRender(); }
    }, has));
    return;
  }
  const skip = el("button", L("wzSkip"), "link"); skip.type = "button"; skip.onclick = () => wzGo("crops");
  root.append(wzGoBtn(L("wzNext"), () => wzGo("crops"), has), skip, wzBack("lang"));
}

function wzBack(step) { const b = el("button", "← " + L("wzBack"), "link"); b.type = "button"; b.onclick = () => wzGo(step); return b; }

function wzCrops(root) {
  root.append(el("h2", L("wzCrops")));
  const g = el("div", null, "grid3");
  (meta?.crops || Object.keys(CROPS_TE)).forEach(c => {
    const b = el("button", null, "opt crop" + (WZ.picks.includes(c) ? " on" : "")); b.type = "button";
    b.append(el("span", cropEm(c), "em"), el("span", cropLines(c)));
    b.onclick = () => { WZ.picks = WZ.picks.includes(c) ? WZ.picks.filter(x => x !== c) : [...WZ.picks, c]; wzRender(); };
    g.append(b);
  });
  root.append(g);
  if (!WZ.picks.length) root.append(el("div", L("wzPickOne"), "sub"));
  root.append(wzGoBtn(L("wzNext"), () => { WZ.i = 0; wzGo("crop"); }, WZ.picks.length > 0));
  if (WZ.mode === "first") root.append(wzBack("place"));
}

function wzCropStep(root) {
  const c = WZ.picks[WZ.i], x = wzCrop(c), n = WZ.picks.length;
  if (WZ.mode !== "edit") root.append(el("div", L("wzCropOf", {i: WZ.i + 1, n}), "sub"));
  const head = el("h2", null); head.append(el("span", cropEm(c) + " "), document.createTextNode(WZ.mode === "edit" ? L("wzEdit", {crop: c}) : L("wzAcres", {crop: c})));
  root.append(head);
  const st = el("div", null, "stepper"), inp = el("input"); inp.type = "number"; inp.inputMode = "decimal"; inp.min = 0.1; inp.step = "any"; inp.value = x.area;
  const bump = d => { x.area = Math.max(0.5, Math.round((x.area + d) * 10) / 10); inp.value = x.area; wzRender(); };
  const minus = el("button", "−"), plus = el("button", "+"); minus.type = plus.type = "button"; minus.onclick = () => bump(-0.5); plus.onclick = () => bump(0.5);
  inp.oninput = () => { x.area = parseFloat(inp.value) || 0; };
  inp.onchange = wzRender;
  st.append(minus, inp, plus); root.append(st);
  const pre = el("div", null, "chips-row"); [0.5, 1, 2, 3, 5, 10].forEach(v => pre.append(wzOpt(v + "", x.area === v, () => { x.area = v; wzRender(); })));
  root.append(pre, el("div", L("wzWhen"), "sub"));
  const when = el("div", null, "chips-row");
  WHEN.forEach(([k, key]) => when.append(wzOpt(L(key), x.when === k, () => { x.when = k; wzRender(); })));
  root.append(when);
  if (x.when === "pick") { const d = el("input"); d.type = "date"; d.max = isoDay(0); d.value = x.date; d.onchange = () => { x.date = d.value; wzRender(); }; root.append(d); }
  const dt = wzDate(c);
  if (dt) root.append(el("div", L("wzApprox", {d: new Date(dt).toLocaleDateString(LANG === "te" ? "te-IN" : "en-IN", {day: "numeric", month: "short", year: "numeric"})}), "sub"));
  root.append(el("div", L("wzWater"), "sub"));
  const wr = el("div", null, "chips-row"); WATER.forEach(([k, key]) => wr.append(wzOpt(L(key), x.water === k, () => { x.water = k; wzRender(); })));
  root.append(wr);
  if (x.water !== "rainfed" && x.when && x.when !== "notyet" && WZ.mode !== "edit") {   // soil water can only be estimated from the last watering
    root.append(el("div", L("wzLastWater"), "sub"));
    const lw = el("div", null, "chips-row");
    [[1, "wzLW1"], [3, "wzLW3"], [6, "wzLW6"], [10, "wzLW10"], ["n", "wzLWn"]].forEach(([k, key]) => lw.append(wzOpt(L(key), x.last === k, () => { x.last = k; wzRender(); })));
    root.append(lw);
  }
  if (WZ.err) root.append(el("div", WZ.err, "err"));
  const last = WZ.i === n - 1 || WZ.mode === "edit";
  root.append(wzGoBtn(WZ.busy ? L("wzSaving") : L(last ? (WZ.mode === "edit" ? "wzSave" : "wzNext") : "wzNext"), () => last ? wzSubmit() : (WZ.i++, wzRender()), wzReady(c) && !WZ.busy));
  if (WZ.i > 0) { const b = el("button", "← " + L("wzBack"), "link"); b.type = "button"; b.onclick = () => { WZ.i--; wzRender(); }; root.append(b); }
}

async function wzSubmit() {
  WZ.busy = true; WZ.err = ""; wzRender();
  try {
    const list = WZ.picks.map(c => { const x = wzCrop(c); return {crop: c, area_acre: x.area, planted_on: wzDate(c), irrigation: x.water, last_watered_on: typeof x.last === "number" ? isoDay(x.last) : null}; });
    if (WZ.mode === "edit") { const l = list[0]; await api("/api/plots/" + WZ.plotId, {method: "PATCH", headers: {"Content-Type": "application/json"}, body: JSON.stringify({area_acre: l.area_acre, sowing_date: l.planted_on, irrigation: l.irrigation})}); closeWizard(); await load(); return; }
    if (WZ.mode === "first") await post("/api/onboard", {...WZ.farm, crops: list});
    else for (const l of list) await post("/api/plots", {crop: l.crop, area_acre: l.area_acre, sowing_date: l.planted_on, irrigation: l.irrigation, last_watered_on: l.last_watered_on});
    WZ.busy = false; WZ.acres = list.reduce((a, l) => a + l.area_acre, 0); WZ.n = list.length; wzGo("done");
  } catch (e) { WZ.busy = false; WZ.err = L("wzErr", {e: e.message}); wzRender(); }
}

function wzDone(root) {
  root.append(el("h2", "✅ " + L("wzDone")), el("div", L("wzSummary", {n: WZ.n, a: Math.round(WZ.acres * 10) / 10}), "sub"));
  root.append(wzGoBtn(L("wzOpen"), async () => { closeWizard(); store.set("skipSetup", ""); await go("today"); }));
}
