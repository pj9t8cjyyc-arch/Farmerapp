// Sign-in with a mobile number and a 6-digit code (sent on WhatsApp or SMS), plus the account sheet.
// Uses helpers from app.js. The session token lives in localStorage ("token") and is sent as a Bearer header.
const LG = {step: "phone", phone: "", channel: null, err: "", busy: false, dev: null, cooldown: 0, timer: null, sentOn: null};

function lgPhoneOk(p) { return /^[6-9]\d{9}$/.test(p); }
function lgMessage(e) {   // map the server's English message to a translated one
  const m = (e.message || "").toLowerCase(), s = e.status;
  if (s === 429) return L("lgTooMany");
  if (s === 502) return L("lgSendFail");
  if (m.includes("expired")) return L("lgExpired");
  if (s === 400) return L("lgWrong");
  if (s === 422) return L("lgBadPhone");
  return e.message;
}

function openLogin() {
  clearInterval(LG.timer);
  Object.assign(LG, {step: "phone", err: "", busy: false, dev: null, cooldown: 0});
  $("wizard").hidden = false; document.body.style.overflow = "hidden"; lgRender();
}
function lgHeader(root) {
  const top = el("div", null, "wz-top"); top.append(el("div", "🌾", "em"));
  const seg = el("div", null, "seg");
  [["te", "తె"], ["en", "EN"], ["both", "తె·EN"]].forEach(([l, t]) => { const b = el("button", t, LANG === l ? "on" : ""); b.type = "button"; b.onclick = () => { setLang(l); render(); lgRender(); }; seg.append(b); });
  top.append(seg); root.append(top);
}

function lgRender() {
  const root = el("div", null, "wz"); lgHeader(root);
  const channels = S.auth?.channels || [];
  if (LG.step === "phone") {
    root.append(el("h2", L("lgTitle")), el("label", L("lgPhone")));
    const g = el("div", null, "phone"), inp = el("input");
    inp.type = "tel"; inp.inputMode = "numeric"; inp.maxLength = 10; inp.autocomplete = "tel-national"; inp.id = "lgPhone"; inp.value = LG.phone; inp.placeholder = "98765 43210";
    inp.oninput = () => { inp.value = inp.value.replace(/\D/g, "").slice(0, 10); LG.phone = inp.value; LG.err = ""; };
    g.append(el("b", "+91"), inp); root.append(g);
    if (!channels.length) root.append(el("div", L("lgNone"), "err"));
    channels.forEach((c, i) => {
      const b = el("button", c === "whatsapp" ? L("lgWa") : L("lgSms"), i === 0 ? "go" : "opt"); b.type = "button"; b.disabled = LG.busy;
      b.onclick = () => lgSend(c); root.append(b);
    });
    if (LG.err) root.append(el("div", LG.err, "err"));
    root.append(el("div", L("lgPrivacy"), "sub"));
  } else {
    root.append(el("h2", L("lgCodeTitle")), el("div", L(LG.sentOn === "sms" ? "lgSentSms" : "lgSentWa", {p: "+91 " + LG.phone.slice(0, 5) + " " + LG.phone.slice(5)}), "sub"));
    const inp = el("input"); inp.type = "text"; inp.inputMode = "numeric"; inp.maxLength = 6; inp.autocomplete = "one-time-code"; inp.id = "lgCode"; inp.className = "otp"; inp.placeholder = "••••••";
    inp.oninput = () => { inp.value = inp.value.replace(/\D/g, "").slice(0, 6); LG.err = ""; if (inp.value.length === 6) lgVerify(inp.value); };
    root.append(inp);
    if (LG.dev) root.append(el("div", L("lgDev", {c: LG.dev}), "sub"));
    if (LG.err) root.append(el("div", LG.err, "err"));
    const re = el("button", LG.cooldown > 0 ? L("lgResendIn", {s: LG.cooldown}) : L("lgResend"), "opt"); re.type = "button"; re.id = "lgResend"; re.disabled = LG.cooldown > 0 || LG.busy;
    re.onclick = () => lgSend(LG.sentOn);
    const ch = el("button", L("lgChange"), "link"); ch.type = "button"; ch.onclick = () => { clearInterval(LG.timer); LG.step = "phone"; LG.err = ""; lgRender(); };
    root.append(re, ch);
  }
  $("wizard").replaceChildren(root);
  $("lgPhone")?.focus(); if (LG.step === "code") $("lgCode")?.focus();
}

async function lgSend(channel) {
  if (!lgPhoneOk(LG.phone)) { LG.err = L("lgBadPhone"); return lgRender(); }
  LG.busy = true; LG.err = ""; lgRender();
  try {
    const r = await post("/api/auth/request", {phone: LG.phone, channel});
    Object.assign(LG, {step: "code", sentOn: channel, dev: r.dev_code || null, cooldown: r.cooldown_s || 30, busy: false});
    clearInterval(LG.timer);
    LG.timer = setInterval(() => { LG.cooldown = Math.max(0, LG.cooldown - 1); if (LG.step === "code") { const b = $("lgResend"); if (b) { b.textContent = LG.cooldown > 0 ? L("lgResendIn", {s: LG.cooldown}) : L("lgResend"); b.disabled = LG.cooldown > 0; } } if (!LG.cooldown) clearInterval(LG.timer); }, 1000);
  } catch (e) { LG.busy = false; LG.err = lgMessage(e); }
  lgRender();
}

async function lgVerify(code) {
  LG.busy = true; lgRender();
  try {
    const r = await post("/api/auth/verify", {phone: LG.phone, code});
    clearLocal(); store.set("token", r.token); clearInterval(LG.timer); closeWizard(); boot();
  } catch (e) { LG.busy = false; LG.err = lgMessage(e); lgRender(); $("lgCode") && ($("lgCode").value = ""); }
}

// Per-person settings kept on the device (calculator numbers, snoozed tasks, skipped setup...) must not carry over to the next farmer.
function clearLocal() {
  try {
    for (const k of Object.keys(localStorage)) if (/^(calc:|snooze:)/.test(k) || ["view", "tab", "skipSetup", "token"].includes(k)) localStorage.removeItem(k);
  } catch {}
}

// ---------- account sheet ----------
async function openAccount(confirmDelete = false) {
  $("wizard").hidden = false; document.body.style.overflow = "hidden";
  let me = {phone: ""}; try { me = await api("/api/auth/me"); } catch { return; }
  const root = el("div", null, "wz"), top = el("div", null, "wz-top");
  const x = el("button", "✕", "ico"); x.type = "button"; x.setAttribute("aria-label", L("wzClose")); x.onclick = closeWizard;
  top.append(el("h2", L("acctTitle")), x); root.append(top, el("div", L("acctPhone", {p: me.phone}), "sub"));
  if (!confirmDelete) {
    const out = el("button", L("acctLogout"), "opt"); out.type = "button";
    out.onclick = async () => { try { await post("/api/auth/logout", {}); } catch {} clearLocal(); closeWizard(); location.reload(); };
    const del = el("button", L("acctDelete"), "opt danger"); del.type = "button"; del.onclick = () => openAccount(true);
    root.append(out, del);
  } else {
    const yes = el("button", L("acctDeleteYes"), "go danger"); yes.type = "button";
    yes.onclick = async () => { try { await post("/api/auth/delete-account", {confirm: true}); } catch (e) { return oops(e); } clearLocal(); closeWizard(); location.reload(); };
    const no = el("button", L("acctCancel"), "opt"); no.type = "button"; no.onclick = () => openAccount(false);
    root.append(el("div", L("acctDeleteWarn"), "tip warn"), yes, no);
  }
  $("wizard").replaceChildren(root);
}
