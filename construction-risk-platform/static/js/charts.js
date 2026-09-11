/* ═════════════════════════════════════════════════════════════════
   Charts — dependency-free SVG chart library for SiteSentinel AI
   line · gauge · ring · donut · hbars · vbars · radar · sparkline
   ═════════════════════════════════════════════════════════════════ */
(function () {
  const NS = "http://www.w3.org/2000/svg";

  function svgEl(tag, attrs, parent) {
    const el = document.createElementNS(NS, tag);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(el);
    return el;
  }
  function fmtNum(v) {
    if (Math.abs(v) >= 1000) return (v / 1000).toFixed(v % 1000 === 0 ? 0 : 1) + "k";
    return (Math.round(v * 10) / 10).toString();
  }
  function uid() { return "g" + Math.random().toString(36).slice(2, 9); }

  const Charts = {};

  /* ───────────────────────────── LINE ───────────────────────────── */
  Charts.line = function (container, opts) {
    const el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    const W = el.clientWidth || 600, H = opts.height || 190;
    const padL = 34, padR = 12, padT = 12, padB = 22;
    const series = opts.series.filter(s => s.data && s.data.length);
    if (!series.length) { el.innerHTML = '<div class="empty">No data yet…</div>'; return; }
    let all = [];
    series.forEach(s => all = all.concat(s.data.filter(v => v != null && !isNaN(v))));
    let yMin = opts.yMin !== undefined ? opts.yMin : Math.min(...all);
    let yMax = opts.yMax !== undefined ? opts.yMax : Math.max(...all);
    if (yMax === yMin) { yMax += 1; yMin -= 1; }
    if (opts.yMin === undefined || opts.yMax === undefined) {
      const pad = (yMax - yMin) * 0.12;
      yMin = Math.max(opts.absMin !== undefined ? opts.absMin : -Infinity, yMin - pad);
      yMax = yMax + pad;
    }
    const n = Math.max(...series.map(s => s.data.length));
    const X = i => padL + (W - padL - padR) * (i / Math.max(n - 1, 1));
    const Y = v => padT + (H - padT - padB) * (1 - (v - yMin) / (yMax - yMin));

    el.innerHTML = "";
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H }, el);
    const defs = svgEl("defs", {}, svg);

    // grid + y labels
    const ticks = 4;
    for (let i = 0; i <= ticks; i++) {
      const v = yMin + (yMax - yMin) * i / ticks, y = Y(v);
      svgEl("line", { x1: padL, y1: y, x2: W - padR, y2: y, stroke: "rgba(233,220,190,0.08)", "stroke-width": 1 }, svg);
      const t = svgEl("text", { x: padL - 6, y: y + 3.5, "text-anchor": "end", fill: "#6f6a5c", "font-size": 9.5, "font-family": "monospace" }, svg);
      t.textContent = opts.yFmt ? opts.yFmt(v) : fmtNum(v);
    }
    // x labels (sparse)
    if (opts.labels && opts.labels.length) {
      const lb = opts.labels, step = Math.max(1, Math.floor(lb.length / (W > 480 ? 6 : 3)));
      for (let i = 0; i < lb.length; i += step) {
        const t = svgEl("text", { x: X(i), y: H - 6, "text-anchor": "middle", fill: "#6f6a5c", "font-size": 9, "font-family": "monospace" }, svg);
        t.textContent = lb[i];
      }
    }
    const first = !el.dataset.drawn;
    series.forEach((s, si) => {
      const d = s.data;
      // build path skipping null gaps (e.g. leading nulls for forecast overlay)
      let path = "", started = false, lastIdx = -1, lastVal = null;
      d.forEach((v, i) => {
        if (v == null || isNaN(v)) return;
        path += `${started ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`;
        started = true; lastIdx = i; lastVal = v;
      });
      if (!started) return;
      if (s.fill !== false && !s.dash) {
        const gid = uid();
        const grad = svgEl("linearGradient", { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
        svgEl("stop", { offset: "0%", "stop-color": s.color, "stop-opacity": 0.34 }, grad);
        svgEl("stop", { offset: "100%", "stop-color": s.color, "stop-opacity": 0 }, grad);
        const firstIdx = d.findIndex(v => v != null && !isNaN(v));
        svgEl("path", { d: `${path} L${X(lastIdx)},${H - padB} L${X(firstIdx)},${H - padB} Z`, fill: `url(#${gid})`, stroke: "none" }, svg);
      }
      const p = svgEl("path", { d: path, fill: "none", stroke: s.color, "stroke-width": s.width || 2, "stroke-linecap": "round", "stroke-linejoin": "round" }, svg);
      if (s.dash) p.setAttribute("stroke-dasharray", "5 5");
      if (first && p.getTotalLength) {
        const len = p.getTotalLength ? p.getTotalLength() : 0;
        if (len) {
          p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
          p.getBoundingClientRect();
          p.style.transition = `stroke-dashoffset 0.9s ${si * 0.12}s ease`;
          p.style.strokeDashoffset = "0";
          setTimeout(() => { p.style.strokeDasharray = s.dash ? "5 5" : "none"; }, 1100 + si * 120);
        }
      } else if (s.dash) p.setAttribute("stroke-dasharray", "5 5");
      // last point dot
      const lx = X(lastIdx), ly = Y(lastVal);
      svgEl("circle", { cx: lx, cy: ly, r: 3.2, fill: s.color }, svg);
      svgEl("circle", { cx: lx, cy: ly, r: 6.5, fill: s.color, opacity: 0.25 }, svg);
    });
    // hover guide
    if (opts.hover !== false) {
      const guide = svgEl("line", { x1: 0, y1: padT, x2: 0, y2: H - padB, stroke: "rgba(242,239,228,0.25)", "stroke-dasharray": "3 3", opacity: 0 }, svg);
      const tip = document.createElement("div");
      tip.style.cssText = "position:absolute;pointer-events:none;background:rgba(22,20,15,0.95);border:1px solid rgba(233,220,190,0.25);border-radius:9px;padding:7px 10px;font-size:11px;display:none;z-index:5;white-space:nowrap;box-shadow:0 8px 24px rgba(0,0,0,.5)";
      tip.style.fontFamily = "inherit";
      el.style.position = "relative";
      el.appendChild(tip);
      svg.addEventListener("mousemove", ev => {
        const r = svg.getBoundingClientRect();
        const mx = (ev.clientX - r.left) * (W / r.width);
        const i = Math.round((mx - padL) / ((W - padL - padR) / Math.max(n - 1, 1)));
        if (i < 0 || i >= n) { tip.style.display = "none"; guide.setAttribute("opacity", 0); return; }
        const gx = X(i);
        guide.setAttribute("x1", gx); guide.setAttribute("x2", gx); guide.setAttribute("opacity", 1);
        let html = "";
        if (opts.labels && opts.labels[i]) html += `<div style="color:#948e7e;margin-bottom:3px">${opts.labels[i]}</div>`;
        series.forEach(s => {
          const v = s.data[i];
          if (v != null) html += `<div><span style="display:inline-block;width:8px;height:8px;border-radius:3px;background:${s.color};margin-right:6px"></span>${s.name || ""} <b style="float:right;margin-left:12px">${(opts.tipFmt || fmtNum)(v)}</b></div>`;
        });
        tip.innerHTML = html;
        tip.style.display = "block";
        const tw = tip.offsetWidth;
        let px = (gx / W) * r.width + 12;
        if (px + tw > r.width) px = (gx / W) * r.width - tw - 12;
        tip.style.left = px + "px";
        tip.style.top = "8px";
      });
      svg.addEventListener("mouseleave", () => { tip.style.display = "none"; guide.setAttribute("opacity", 0); });
    }
    el.dataset.drawn = "1";
  };

  /* ───────────────────────────── GAUGE ──────────────────────────── */
  Charts.gauge = function (container, opts) {
    const el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    const size = opts.size || 210, v = +opts.value || 0;
    const bands = opts.bands || [[35, "#8fd14f"], [55, "#ffcf3f"], [75, "#ff8a1e"], [101, "#ff4d3d"]];
    const color = (opts.color !== undefined) ? opts.color : bands.find(b => v < b[0])[1];
    const cx = size / 2, cy = size * 0.56, R = size * 0.40, thick = size * 0.075;
    const a0 = Math.PI * 0.86, a1 = Math.PI * 0.14; // gap at bottom
    const pt = (a, r) => [cx + r * Math.cos(a), cy - r * Math.sin(a)];
    const arc = (from, to, r) => {
      const [x1, y1] = pt(from, r), [x2, y2] = pt(to, r);
      return `M${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${Math.abs(from - to) > Math.PI ? 1 : 0} 1 ${x2.toFixed(2)},${y2.toFixed(2)}`;
    };
    const full = a0 - a1;
    const frac = Math.max(0.001, Math.min(1, v / 100));
    let svg = el.querySelector("svg");
    if (!svg || el.dataset.size != size) {
      el.innerHTML = "";
      el.dataset.size = size;
      svg = svgEl("svg", { viewBox: `0 0 ${size} ${size * 0.72}`, width: "100%" }, el);
      // background track
      svgEl("path", { d: arc(a0, a1, R), stroke: "rgba(233,220,190,0.1)", "stroke-width": thick, fill: "none", "stroke-linecap": "round" }, svg);
      // band ticks
      bands.forEach(b => {
        const f = b[0] / 100 * full;
        const [x1, y1] = pt(a0 - f + 0.012, R + thick / 2 + 3), [x2, y2] = pt(a0 - f + 0.012, R + thick / 2 + 8);
        svgEl("line", { x1, y1, x2, y2, stroke: b[1], "stroke-width": 2, opacity: 0.65 }, svg);
      });
      const val = svgEl("path", { d: arc(a0, a0 - full * frac, R), stroke: color, "stroke-width": thick, fill: "none", "stroke-linecap": "round" }, svg);
      val.style.transition = "stroke-dasharray 0.8s cubic-bezier(.2,.8,.2,1), stroke 0.5s";
      const lens = val.getTotalLength ? val.getTotalLength() : 200;
      val.style.strokeDasharray = `${lens * frac} ${lens}`;
      val.dataset.arc = arc(a0, a1, R); val.dataset.len = lens;
      const txt = svgEl("text", { x: cx, y: cy - R * 0.28, "text-anchor": "middle", fill: "#f2efe4", "font-size": size * 0.19, "font-weight": 800, "font-family": "inherit" }, svg);
      txt.textContent = opts.label !== undefined ? opts.label : Math.round(v);
      const sub = svgEl("text", { x: cx, y: cy - R * 0.28 + size * 0.085, "text-anchor": "middle", fill: color, "font-size": size * 0.062, "font-weight": 800, "letter-spacing": 1.5 }, svg);
      sub.textContent = opts.sub || "";
      el.__gauge = { val, txt, sub };
    } else {
      const g = el.__gauge;
      const frac2 = Math.max(0.001, Math.min(1, v / 100));
      const lens = +g.val.dataset.len;
      g.val.style.strokeDasharray = `${lens * frac2} ${lens}`;
      g.val.setAttribute("stroke", color);
      g.txt.textContent = opts.label !== undefined ? opts.label : Math.round(v);
      g.sub.textContent = opts.sub || "";
      g.sub.setAttribute("fill", color);
    }
  };

  /* ───────────────────────────── RING ───────────────────────────── */
  Charts.ring = function (container, opts) {
    const el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    const size = opts.size || 74, sw = opts.stroke || 7;
    const frac = Math.max(0.001, Math.min(1, (+opts.value || 0) / (opts.max || 100)));
    const R = (size - sw) / 2, C = 2 * Math.PI * R;
    let svg = el.querySelector("svg");
    if (!svg) {
      el.innerHTML = "";
      el.style.position = "relative";
      svg = svgEl("svg", { viewBox: `0 0 ${size} ${size}`, width: size, height: size }, el);
      svgEl("circle", { cx: size / 2, cy: size / 2, r: R, stroke: "rgba(233,220,190,0.12)", "stroke-width": sw, fill: "none" }, svg);
      const c = svgEl("circle", { cx: size / 2, cy: size / 2, r: R, stroke: opts.color || "#ffc400", "stroke-width": sw, fill: "none", "stroke-linecap": "round", transform: `rotate(-90 ${size / 2} ${size / 2})` }, svg);
      c.style.strokeDasharray = `${C * frac} ${C}`;
      c.style.transition = "stroke-dasharray 0.8s cubic-bezier(.2,.8,.2,1), stroke .5s";
      const t = svgEl("text", { x: size / 2, y: size / 2 + 5, "text-anchor": "middle", fill: "#f2efe4", "font-size": size * 0.26, "font-weight": 800 }, svg);
      t.textContent = Math.round(opts.value);
      el.__ring = { c, t, C };
    } else {
      const r = el.__ring;
      r.c.style.strokeDasharray = `${r.C * frac} ${r.C}`;
      r.c.setAttribute("stroke", opts.color || "#ffc400");
      r.t.textContent = Math.round(opts.value);
    }
  };

  /* ───────────────────────────── DONUT ──────────────────────────── */
  Charts.donut = function (container, opts) {
    const el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    const size = opts.size || 170, R = size * 0.36, th = size * 0.13;
    const total = opts.items.reduce((a, b) => a + b.value, 0);
    el.innerHTML = "";
    const svg = svgEl("svg", { viewBox: `0 0 ${size} ${size}`, width: "100%", style: "max-width:" + size + "px;margin:0 auto" }, el);
    let a = -Math.PI / 2;
    const first = !el.dataset.drawn;
    opts.items.forEach((it, idx) => {
      if (!it.value) return;
      const frac = it.value / total;
      const a2 = a + frac * Math.PI * 2;
      const large = frac > 0.5 ? 1 : 0;
      const x1 = size / 2 + R * Math.cos(a), y1 = size / 2 + R * Math.sin(a);
      const x2 = size / 2 + R * Math.cos(a2), y2 = size / 2 + R * Math.sin(a2);
      const p = svgEl("path", { d: `M${x1},${y1} A${R},${R} 0 ${large} 1 ${x2},${y2}`, stroke: it.color, "stroke-width": th, fill: "none", "stroke-linecap": "butt" }, svg);
      if (first && p.getTotalLength) { const L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.strokeDashoffset = L; p.getBoundingClientRect(); p.style.transition = `stroke-dashoffset .8s ${idx * .1}s ease`; p.style.strokeDashoffset = 0; }
      if (opts.hover) {
        p.style.cursor = "pointer";
        p.addEventListener("mouseenter", () => { p.setAttribute("stroke-width", th + 5); ctr.setAttribute("opacity", 0); hint.setAttribute("opacity", 1); });
        p.addEventListener("mouseleave", () => { p.setAttribute("stroke-width", th); ctr.setAttribute("opacity", 1); hint.setAttribute("opacity", 0); });
      }
      a = a2;
    });
    const ctr = svgEl("text", { x: size / 2, y: size / 2 + 2, "text-anchor": "middle", fill: "#f2efe4", "font-size": size * 0.17, "font-weight": 800 }, svg);
    ctr.textContent = opts.center !== undefined ? opts.center : total;
    const hint = svgEl("text", { x: size / 2, y: size / 2 + 2, "text-anchor": "middle", fill: "#f2efe4", "font-size": size * 0.1, "font-weight": 700, opacity: 0 }, svg);
    const cl = svgEl("text", { x: size / 2, y: size / 2 + size * 0.14, "text-anchor": "middle", fill: "#6f6a5c", "font-size": size * 0.062, "font-weight": 700, "letter-spacing": 1.2 }, svg);
    cl.textContent = opts.centerSub || "";
    el.dataset.drawn = "1";
    if (opts.legend !== false && opts.legendEl) {
      const lg = typeof opts.legendEl === "string" ? document.querySelector(opts.legendEl) : opts.legendEl;
      if (lg) lg.innerHTML = opts.items.map(it =>
        `<span style="display:inline-flex;align-items:center;gap:6px;font-size:11.5px;color:#a8a292"><i style="width:9px;height:9px;border-radius:3px;background:${it.color};display:inline-block"></i>${it.label} <b style="color:#f2efe4">${it.value}</b></span>`).join("");
    }
  };

  /* ───────────────────────────── HBARS ──────────────────────────── */
  Charts.hbars = function (container, opts) {
    const el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    const max = opts.max || Math.max(...opts.items.map(i => i.value), 1);
    el.innerHTML = opts.items.map(it => {
      const col = it.color || "#4db8ff";
      const pct = Math.max(2, Math.min(100, it.value / max * 100));
      return `<div style="display:grid;grid-template-columns:${opts.labelW || 118}px 1fr ${opts.valW || 46}px;gap:10px;align-items:center;padding:5.5px 0">
        <span style="font-size:11.8px;color:#a8a292;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600">${it.label}</span>
        <div class="mbar" style="height:8px"><i style="width:${first(el) ? 0 : pct}%;background:linear-gradient(90deg,${col}88,${col});transition:width .8s cubic-bezier(.2,.8,.2,1)" data-w="${pct}"></i></div>
        <span class="mono" style="font-size:11.5px;color:#f2efe4;text-align:right">${it.display !== undefined ? it.display : fmtNum(it.value)}${opts.suffix || ""}</span>
      </div>`;
    }).join("");
    requestAnimationFrame(() => el.querySelectorAll(".mbar i").forEach(i => i.style.width = i.dataset.w + "%"));
    function first(e) { return !e.dataset.drawn; }
    el.dataset.drawn = "1";
  };

  /* ───────────────────────────── VBARS ──────────────────────────── */
  Charts.vbars = function (container, opts) {
    const el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    const W = el.clientWidth || 400, H = opts.height || 170;
    const max = opts.max || Math.max(...opts.items.map(i => i.value), 1);
    const padB = 20, padT = 14;
    el.innerHTML = "";
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H }, el);
    const n = opts.items.length, slot = W / n, bw = Math.min(34, slot * 0.55);
    const first = !el.dataset.drawn;
    opts.items.forEach((it, i) => {
      const h = Math.max(3, (it.value / max) * (H - padT - padB));
      const x = slot * i + (slot - bw) / 2, y = H - padB - h;
      const gid = uid();
      const defs = svgEl("defs", {}, svg);
      const grad = svgEl("linearGradient", { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
      svgEl("stop", { offset: "0%", "stop-color": it.color || "#4db8ff", "stop-opacity": 1 }, grad);
      svgEl("stop", { offset: "100%", "stop-color": it.color || "#4db8ff", "stop-opacity": 0.25 }, grad);
      const r = svgEl("rect", { x, y: first ? H - padB : y, width: bw, height: first ? 0 : h, rx: 5, fill: `url(#${gid})` }, svg);
      r.style.transition = `y .7s ${i * 0.05}s cubic-bezier(.2,.8,.2,1), height .7s ${i * 0.05}s cubic-bezier(.2,.8,.2,1)`;
      if (first) requestAnimationFrame(() => { r.setAttribute("y", y); r.setAttribute("height", h); });
      const tv = svgEl("text", { x: x + bw / 2, y: y - 5, "text-anchor": "middle", fill: "#e6e0cf", "font-size": 10, "font-weight": 700, "font-family": "monospace" }, svg);
      tv.textContent = fmtNum(it.value);
      const tl = svgEl("text", { x: x + bw / 2, y: H - 6, "text-anchor": "middle", fill: "#6f6a5c", "font-size": 9.5, "font-weight": 600 }, svg);
      tl.textContent = it.label;
    });
    el.dataset.drawn = "1";
  };

  /* ───────────────────────────── RADAR ──────────────────────────── */
  Charts.radar = function (container, opts) {
    const el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    const size = opts.size || 250, cx = size / 2, cy = size / 2 + 4, R = size * 0.36;
    const axes = opts.axes, N = axes.length;
    el.innerHTML = "";
    const svg = svgEl("svg", { viewBox: `0 0 ${size} ${size * 0.96}`, width: "100%", style: "max-width:" + (size + 40) + "px;margin:0 auto" }, el);
    const ang = i => -Math.PI / 2 + i * 2 * Math.PI / N;
    for (let ring = 1; ring <= 4; ring++) {
      const r = R * ring / 4;
      const pts = axes.map((_, i) => `${cx + r * Math.cos(ang(i))},${cy + r * Math.sin(ang(i))}`).join(" ");
      svgEl("polygon", { points: pts, fill: "none", stroke: "rgba(233,220,190,0.1)", "stroke-width": 1 }, svg);
    }
    axes.forEach((ax, i) => {
      svgEl("line", { x1: cx, y1: cy, x2: cx + R * Math.cos(ang(i)), y2: cy + R * Math.sin(ang(i)), stroke: "rgba(233,220,190,0.08)" }, svg);
      const lx = cx + (R + 17) * Math.cos(ang(i)), ly = cy + (R + 15) * Math.sin(ang(i));
      const t = svgEl("text", { x: lx, y: ly + 3, "text-anchor": "middle", fill: "#948e7e", "font-size": 9.8, "font-weight": 700, "letter-spacing": 0.4 }, svg);
      t.textContent = ax.label;
    });
    (opts.series || []).forEach(s => {
      const pts = s.values.map((v, i) => {
        const r = R * Math.max(0.02, Math.min(1, v / (axes[i].max || 100)));
        return `${cx + r * Math.cos(ang(i))},${cy + r * Math.sin(ang(i))}`;
      }).join(" ");
      svgEl("polygon", { points: pts, fill: s.color + "2e", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round" }, svg);
      s.values.forEach((v, i) => {
        const r = R * Math.max(0.02, Math.min(1, v / (axes[i].max || 100)));
        svgEl("circle", { cx: cx + r * Math.cos(ang(i)), cy: cy + r * Math.sin(ang(i)), r: 3, fill: s.color }, svg);
      });
    });
  };

  /* ─────────────────────────── SPARKLINE ────────────────────────── */
  Charts.spark = function (container, opts) {
    const el = typeof container === "string" ? document.querySelector(container) : container;
    if (!el) return;
    const d = opts.data || [];
    if (d.length < 2) return;
    const W = el.clientWidth || 120, H = opts.height || el.clientHeight || 30;
    const mn = Math.min(...d), mx = Math.max(...d), rg = (mx - mn) || 1;
    const pts = d.map((v, i) => `${(i / (d.length - 1) * W).toFixed(1)},${(H - 3 - (v - mn) / rg * (H - 6)).toFixed(1)}`);
    const last = pts[pts.length - 1].split(",");
    el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" height="100%" preserveAspectRatio="none">
      <polyline points="${pts.join(" ")}" fill="none" stroke="${opts.color || "#4db8ff"}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="${last[0]}" cy="${last[1]}" r="2.4" fill="${opts.color || "#4db8ff"}"/></svg>`;
  };

  Charts.fmtNum = fmtNum;
  window.Charts = Charts;
})();
