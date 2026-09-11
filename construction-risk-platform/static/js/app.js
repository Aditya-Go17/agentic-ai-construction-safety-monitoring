/* ═══════════════════ SiteSentinel AI — shared app helpers ═══════════════════ */
(function () {
  const A = {};

  A.q = (s, r) => (r || document).querySelector(s);
  A.qa = (s, r) => Array.from((r || document).querySelectorAll(s));
  A.esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* icons */
  const P = {
    gauge: '<polyline points="3 13 8.5 7.5 12.5 11 17 5"/><path d="M17 5h3v3"/><path d="M3 3v16a2 2 0 0 0 2 2h16"/>',
    helmet: '<path d="M2 18h20"/><path d="M4 18v-4a8 8 0 0 1 16 0v4"/><path d="M9 6.2V10M15 6.2V10M9 10h6"/>',
    clipboard: '<rect x="5" y="4" width="14" height="18" rx="2"/><path d="M9 4a2 2 0 0 1 6 0"/><path d="M9 11h6M9 15h4"/>',
    shield: '<path d="M12 2l8 3.5V11c0 5-3.4 8.6-8 11-4.6-2.4-8-6-8-11V5.5z"/><path d="M8.5 11.5l2.5 2.5 4.5-4.5"/>',
    doc: '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/><path d="M9 13h6M9 17h6"/>',
    cpu: '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    radar: '<circle cx="12" cy="12" r="2"/><path d="M16.2 7.8a6 6 0 1 0 1.7 5"/><path d="M19.1 4.9A10 10 0 1 0 21.6 13"/>',
    site: '<path d="M3 21h18"/><path d="M5 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16"/><path d="M15 9h3a2 2 0 0 1 2 2v10"/><path d="M8 7h3M8 11h3M8 15h3"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    alert: '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    users: '<path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>',
    wind: '<path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/><path d="M17.7 7.7A2.5 2.5 0 1 1 19.5 12H2"/>',
    temp: '<path d="M14 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0z"/>',
    drop: '<path d="M12 2.7S5.5 9.7 5.5 14a6.5 6.5 0 0 0 13 0c0-4.3-6.5-11.3-6.5-11.3z"/>',
    noise: '<path d="M11 5L6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/>',
    wave: '<path d="M2 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0"/>',
    cam: '<path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2"/>',
    pattern: '<circle cx="5" cy="6" r="2.5"/><circle cx="19" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M7 7.5l3.5 8M17 7.5l-3.5 8M7.5 6h9"/>',
    bulb: '<path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.2 1 2V17h6v-.3c0-.8.4-1.5 1-2A7 7 0 0 0 12 2z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    pulse: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    check: '<path d="M20 6L9 17l-5-5"/>',
    x: '<path d="M18 6L6 18M6 6l12 12"/>',
    print: '<path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>',
    refresh: '<path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.5 9a9 9 0 0 1 14.9-3.4L23 10M1 14l4.6 4.4A9 9 0 0 0 20.5 15"/>',
    arrow: '<path d="M5 12h14M12 5l7 7-7 7"/>',
    menu: '<path d="M3 12h18M3 6h18M3 18h18"/>',
    play: '<path d="M6 4l14 8-14 8z"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    crane: '<path d="M4 22h9"/><path d="M6 22V4l12 4"/><path d="M18 8v3M18 11h-2.5a1.5 1.5 0 0 0 0 3H18"/><path d="M2 8h4"/>',
  };
  A.icon = (name, cls) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" class="${cls || ""}">${P[name] || P.alert}</svg>`;

  /* severity helpers */
  const SEV = { CRITICAL: "crit", HIGH: "high", MODERATE: "mod", LOW: "low", INFO: "info" };
  A.sevChip = s => `<span class="chip ${SEV[s] || "mut"}"><span class="cdot"></span>${A.esc(s)}</span>`;
  A.bandChip = b => `<span class="chip ${SEV[b === "MODERATE" ? "MODERATE" : b] || "mut"}"><span class="cdot"></span>${A.esc(b)}</span>`;
  A.bandColor = v => v < 35 ? "#8fd14f" : v < 55 ? "#ffcf3f" : v < 75 ? "#ff8a1e" : "#ff4d3d";
  A.agentDot = (color, txt) => `<div class="feed-avatar" style="background:${color}22;color:${color};border:1px solid ${color}55">${txt}</div>`;

  /* time */
  A.timeIST = iso => {
    try {
      return new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(new Date(iso));
    } catch (e) { return "--:--"; }
  };
  A.ago = iso => {
    const m = (Date.now() - new Date(iso).getTime()) / 60000;
    if (m < 1) return "now";
    if (m < 60) return Math.floor(m) + "m ago";
    const h = m / 60;
    if (h < 24) return Math.floor(h) + "h ago";
    return Math.floor(h / 24) + "d ago";
  };

  /* animated counter */
  A.countUp = (node, val, dec) => {
    dec = dec || 0;
    const prev = parseFloat(node.dataset.v || "0");
    if (prev === val) { node.textContent = val.toLocaleString("en-IN", { minimumFractionDigits: dec, maximumFractionDigits: dec }); return; }
    node.dataset.v = val;
    const t0 = performance.now(), dur = 650;
    function step(t) {
      const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      node.textContent = (prev + (val - prev) * e).toLocaleString("en-IN", { minimumFractionDigits: dec, maximumFractionDigits: dec });
      if (k < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  };

  /* polling */
  A.poll = (url, ms, fn) => {
    let busy = false;
    const run = async () => {
      if (busy || document.hidden) return;
      busy = true;
      try { const r = await fetch(url); if (r.ok) fn(await r.json()); } catch (e) { /* keep trying */ }
      busy = false;
    };
    run(); const id = setInterval(run, ms);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) run(); });
    return id;
  };

  /* feed renderer (shared) */
  A.renderFeed = (el, items, lastTsRef) => {
    if (!el) return;
    let last = el.dataset.lastTs ? new Date(el.dataset.lastTs).getTime() : 0;
    const fresh = items.filter(f => new Date(f.ts).getTime() > last);
    if (!fresh.length && el.children.length) return;
    const frag = document.createElement("div");
    fresh.slice(0, 14).forEach(f => {
      const div = document.createElement("div");
      div.className = "feed-item";
      div.innerHTML = `
        ${A.agentDot(f.color, (f.agent_name || "").split(" ").map(w => w[0]).slice(0, 2).join(""))}
        <div class="feed-body">
          <div class="feed-meta"><span class="feed-agent" style="color:${f.color}">${A.esc(f.agent_name)}</span>${A.sevChip(f.severity)}<span class="feed-time">${A.ago(f.ts)}</span></div>
          <div class="feed-msg">${A.esc(f.msg)}</div>
        </div>`;
      frag.appendChild(div);
    });
    if (fresh.length) {
      el.prepend(frag);
      el.dataset.lastTs = items[0].ts;
      while (el.children.length > 26) el.removeChild(el.lastChild);
    }
  };

  /* ticker */
  A.setTicker = items => {
    const track = A.q("#tickerTrack");
    if (!track || !items || !items.length) return;
    const sig = items.join("|");
    if (track.dataset.sig === sig) return;
    track.dataset.sig = sig;
    const html = items.map(t => `<span class="tk-item"><span class="tk-dot"></span>${A.esc(t)}</span>`).join("");
    track.innerHTML = html + html;
  };

  /* toast */
  A.toast = (msg, ms) => {
    let holder = A.q(".toasts");
    if (!holder) { holder = document.createElement("div"); holder.className = "toasts"; document.body.appendChild(holder); }
    const t = document.createElement("div");
    t.className = "toast";
    t.innerHTML = `${A.icon("check")}<span>${A.esc(msg)}</span>`;
    holder.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .4s"; setTimeout(() => t.remove(), 400); }, ms || 3200);
  };

  /* modal */
  A.modal = html => {
    let back = A.q("#modalBack");
    if (!back) {
      back = document.createElement("div"); back.id = "modalBack"; back.className = "modal-back";
      back.innerHTML = `<div class="modal" id="modalBox"></div>`;
      back.addEventListener("click", e => { if (e.target === back) A.closeModal(); });
      document.body.appendChild(back);
    }
    A.q("#modalBox").innerHTML = `<div style="display:flex;justify-content:flex-end;margin:-6px -6px 0 0"><button class="bell" onclick="App.closeModal()" style="width:32px;height:32px">${A.icon("x")}</button></div>` + html;
    back.classList.add("open");
  };
  A.closeModal = () => { const b = A.q("#modalBack"); if (b) b.classList.remove("open"); };
  document.addEventListener("keydown", e => { if (e.key === "Escape") A.closeModal(); });

  /* notifications drawer */
  A.openDrawer = async () => {
    const d = A.q("#drawer"), b = A.q("#drawerBack");
    d.classList.add("open"); b.classList.add("open");
    const body = A.q("#drawerBody");
    try {
      const r = await fetch("/api/alerts");
      const data = await r.json();
      body.innerHTML = data.alerts.slice(0, 14).map(a => `
        <div class="notif-item">
          <div class="n-top">${A.sevChip(a.severity)}<span style="font-size:10px;color:#6f6a5c;font-family:monospace;margin-left:auto">${A.ago(a.ts)}</span></div>
          <div class="n-title">${A.esc(a.title)}</div>
          <div class="n-meta"><b style="color:#a8a292">${A.esc(a.site_short)}</b><span>${a.channels.map(c => `<span class="channel-tag ch-${c}">${c}</span>`).join("")}</span>
          <button class="btn sm ${a.ack ? "ghost" : ""}" style="margin-left:auto" onclick="App.ack('${a["id"]}')">${a.ack ? "Acknowledged" : "Acknowledge"}</button></div>
        </div>`).join("") || '<div class="empty">No notifications — all clear.</div>';
    } catch (e) { body.innerHTML = '<div class="empty">Could not load notifications.</div>'; }
  };
  A.closeDrawer = () => { A.q("#drawer").classList.remove("open"); A.q("#drawerBack").classList.remove("open"); };
  A.ack = async id => { try { await fetch(`/api/alerts/${id}/ack`, { method: "POST" }); } catch (e) {} A.openDrawer(); };

  /* workflow modal */
  A.showWorkflowById = id => { const a = (window.__ALERTS || {})[id]; if (a) A.showWorkflow(a); };
  A.showWorkflow = a => {
    const stages = ["Detected", "Triaged", "Escalated", "Action", "Resolved"];
    const stepHtml = `<div class="stepper mb8">${stages.map((s, i) =>
      `<div class="step ${i < a.stage ? "done" : ""} ${i === a.stage ? "active" : ""}"><div class="dot">${i < a.stage ? A.icon("check") : ""}</div><div class="lbl">${s}</div></div>`).join("")}</div>`;
    const vt = a.timeline.map((t, i) => `<div class="vstep done"><div class="vd"></div><div class="vt">${A.esc(t.label)}</div>
      <div class="vs">${["Agent pipeline flagged the issue from live telemetry.", "Risk Intelligence Engine scored severity & impact.", `Notifications dispatched via ${a.channels.join(", ")} to ${A.esc(a.owner)}.`, "Corrective action assigned on ground crew schedule.", "Closure verified by Compliance Agent — evidence archived."][i] || ""}</div>
      <div class="vt2">${A.timeIST(t.t)} IST</div></div>`).join("");
    A.modal(`
      <div class="flex" style="margin-bottom:14px">${A.sevChip(a.severity)}<b style="font-size:15px">${A.esc(a.title)}</b></div>
      <div class="mut" style="font-size:12px;margin-bottom:14px">${A.esc(a.site_short)} · Alert ${A.esc(a.id)} · owner: ${A.esc(a.owner)}</div>
      ${stepHtml}
      <div class="card" style="margin-top:16px;background:var(--card2)"><div class="vstepper">${vt}</div></div>
      <div class="flex" style="margin-top:14px;justify-content:flex-end">
        <span class="mut" style="font-size:11px;margin-right:auto">${a.ack ? "Acknowledged" : "Pending acknowledgement"}</span>
        <button class="btn ghost sm" onclick="App.ack('${a["id"]}');App.closeModal()">${a.ack ? "Re-notify team" : "Acknowledge"}</button>
      </div>`);
  };

  /* boot: clock, ticker, drawer wiring */
  document.addEventListener("DOMContentLoaded", () => {
    const clock = A.q("#clock");
    if (clock) {
      const f = new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", weekday: "short", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
      setInterval(() => clock.textContent = f.format(new Date()) + " IST", 1000);
      clock.textContent = f.format(new Date()) + " IST";
    }
    const bell = A.q("#bellBtn"), db = A.q("#drawerBack"), menu = A.q("#menuBtn");
    if (bell) bell.addEventListener("click", A.openDrawer);
    if (db) db.addEventListener("click", A.closeDrawer);
    if (menu) menu.addEventListener("click", () => A.q("#sidebar").classList.toggle("open"));
    A.poll("/api/ticker", 6000, d => {
      A.setTicker(d.items);
      const c = A.q("#bellCount"); if (c) { c.textContent = d.bell; c.style.display = d.bell > 0 ? "grid" : "none"; }
      const f = A.q("#fleetMini"); if (f) f.textContent = d.fleet + " · " + d.band;
    });
  });

  window.App = A;
})();
