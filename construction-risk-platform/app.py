"""Agentic Construction Risk Intelligence Platform — Flask application."""
import random
from datetime import timedelta

from flask import Flask, jsonify, redirect, render_template, request, url_for

from engine import payloads
from engine.icons import icons
from engine.simulator import get_sim, now, clamp

app = Flask(__name__)


def sim():
    return get_sim()


# ------------------------------------------------------------------ pages
@app.context_processor
def ctx():
    s = sim()
    fleet = round(s.fleet_score(), 1)
    band, col = s.band(fleet)
    return dict(fleet=fleet, fleet_band=band, fleet_color=col,
                icons=icons, page_title="Command Center")


@app.route("/")
def dashboard():
    data = payloads.overview(sim())
    return render_template("dashboard.html", d=data, page_title="Command Center")


@app.route("/sites")
def sites():
    data = payloads.sites_payload(sim())
    return render_template("sites.html", d=data, page_title="Sites")


@app.route("/sites/<sid>")
def site_detail(sid):
    data = payloads.site_detail(sim(), sid)
    if not data:
        return redirect(url_for("sites"))
    return render_template("site_detail.html", d=data, page_title=data["site"]["name"])


@app.route("/safety")
def safety():
    data = payloads.safety_payload(sim())
    return render_template("safety.html", d=data, page_title="Safety Intelligence")


@app.route("/compliance")
def compliance():
    data = payloads.compliance_payload(sim())
    return render_template("compliance.html", d=data, page_title="Compliance")


@app.route("/insurance")
def insurance():
    data = payloads.insurance_payload(sim())
    return render_template("insurance.html", d=data, page_title="Insurance")


@app.route("/reports")
def reports():
    s = sim()
    kind = request.args.get("doc", "exec")
    sid = request.args.get("site", sim().sites[0]["id"])
    salt = request.args.get("salt", "")
    doc = build_report(s, kind, sid, salt)
    data = dict(doc=doc, kinds=REPORT_KINDS,
                sites=[dict(id=x["id"], short=x["short"], name=x["name"]) for x in s.sites],
                current=dict(kind=kind, site=sid, salt=salt))
    return render_template("reports.html", d=data, page_title="Reports")


@app.route("/agents")
def agents():
    data = payloads.agents_payload(sim())
    return render_template("agents.html", d=data, page_title="AI Agents")


@app.route("/alerts")
def alerts():
    data = payloads.alerts_payload(sim())
    return render_template("alerts.html", d=data, page_title="Alerts & Workflow")


# ------------------------------------------------------------------ apis
@app.route("/api/overview")
def api_overview():
    return jsonify(payloads.overview(sim()))


@app.route("/api/sites")
def api_sites():
    return jsonify(payloads.sites_payload(sim()))


@app.route("/api/sites/<sid>")
def api_site(sid):
    d = payloads.site_detail(sim(), sid)
    return jsonify(d) if d else (jsonify(dict(error="not found")), 404)


@app.route("/api/safety")
def api_safety():
    return jsonify(payloads.safety_payload(sim()))


@app.route("/api/compliance")
def api_compliance():
    return jsonify(payloads.compliance_payload(sim()))


@app.route("/api/insurance")
def api_insurance():
    return jsonify(payloads.insurance_payload(sim()))


@app.route("/api/agents")
def api_agents():
    return jsonify(payloads.agents_payload(sim()))


@app.route("/api/agents/run", methods=["POST"])
def api_agents_run():
    return jsonify(sim().run_cycle())


@app.route("/api/alerts")
def api_alerts():
    return jsonify(payloads.alerts_payload(sim()))


@app.route("/api/alerts/<aid>/ack", methods=["POST"])
def api_alert_ack(aid):
    s = sim()
    for a in s.alerts:
        if a["id"] == aid:
            a["ack"] = True
            return jsonify(dict(ok=True))
    return jsonify(dict(ok=False)), 404


@app.route("/api/ticker")
def api_ticker():
    return jsonify(payloads.ticker_payload(sim()))


@app.route("/api/report")
def api_report():
    s = sim()
    kind = request.args.get("doc", "exec")
    sid = request.args.get("site", s.sites[0]["id"])
    doc = build_report(s, kind, sid, request.args.get("salt", ""))
    return jsonify(doc)


# ------------------------------------------------------------------ reports
REPORT_KINDS = [
    dict(id="exec", name="Executive Risk Summary", icon="chart", desc="Fleet-wide risk posture for leadership", cadence="Weekly"),
    dict(id="daily", name="Daily Site Report", icon="sun", desc="Per-site operations, hazards & actions log", cadence="Daily · 18:00 IST"),
    dict(id="audit", name="Compliance Audit Pack", icon="clipboard", desc="Audit-ready regulatory evidence bundle", cadence="Monthly"),
    dict(id="health", name="Project Health Report", icon="pulse", desc="Schedule, safety & cost correlation view", cadence="Fortnightly"),
    dict(id="claim", name="Insurance Claim Packet", icon="shield", desc="Claim support file auto-compiled by agents", cadence="On event"),
]


def build_report(s, kind, sid, salt):
    r = random.Random(f"{kind}-{sid}-{salt}")
    raw = next((x for x in s.sites if x["id"] == sid), s.sites[0])
    site = dict(id=raw["id"], short=raw["short"], name=raw["name"], typelabel=raw["typelabel"],
                city=raw["city"], contractor=raw["contractor"], workers_now=raw["workers_now"],
                score=raw["score"], band=raw["band"], env=raw["env"], ppe=raw["ppe"],
                hazards=raw["hazards"], equipment=raw["equipment"], checks=raw["checks"],
                claims=raw["claims"], incidents=raw["incidents"],
                prediction=raw["prediction"], exposure_util=raw["exposure_util"],
                insurance=raw["insurance"])
    fleet = s.fleet_score()
    band, col = s.band(fleet)
    base = dict(kind=kind, title=next((k["name"] for k in REPORT_KINDS if k["id"] == kind), "Report"),
                ref=f"REP-{now().strftime('%Y%m%d')}-{r.randint(100, 999)}",
                date=now().strftime("%d %B %Y, %H:%M IST"), site=site,
                fleet=round(fleet), band=band,
                summary="", sections=[], footer="Auto-generated by Reporting Agent · reviewed by Risk Intelligence Engine · retention 7 years")
    open_h = [h for h in site["hazards"] if h["status"] == "OPEN"]
    crit = [h for h in s.open_hazards() if h["severity"] == "CRITICAL"]
    if kind == "exec":
        base["summary"] = (f"Fleet risk index stands at {fleet:.0f}/100 ({band}) across {len(s.sites)} active sites "
                           f"and {sum(x['workers_now'] for x in s.sites)} workers on shift. {len(crit)} critical hazards "
                           f"require executive attention; {len([a for a in s.alerts if a['stage'] < 4])} escalations are in-flight.")
        base["sections"] = [
            ("1 · Fleet Risk Posture", [
                f"Weighted fleet risk index: {fleet:.0f}/100 — band {band}.",
                f"Highest-risk unit: {max(s.sites, key=lambda x: x['score'])['name']} ({max(s.sites, key=lambda x: x['score'])['score']:.0f}/100).",
                f"Average PPE compliance: {sum(sum(x['ppe'].values())/5 for x in s.sites)/len(s.sites):.1f}% (target ≥ 95%).",
                f"30-day incident count: {sum(len(x['incidents']) for x in s.sites)}; trend {'elevated' if fleet > 55 else 'stable'}.",
            ]),
            ("2 · Sites Requiring Attention", [
                f"{x['short']} — index {x['score']:.0f} ({x['band']}), dominant factor: {max(x['sub'], key=lambda k: x['sub'][k] if k != 'score' else -1)}."
                for x in sorted(s.sites, key=lambda x: -x["score"])[:3]
            ]),
            ("3 · Predictive Outlook (24h)", [
                f"{x['short']}: {x['prediction']['prob']:.0f}% incident probability ({x['prediction']['dclass']})."
                for x in sorted(s.sites, key=lambda x: -x["prediction"]["prob"])[:4]
            ]),
            ("4 · Recommendations", [rec["title"] + " — " + rec["detail"] for rec in payloads.build_recommendations(s, sorted(s.sites, key=lambda x: -x['score']))[:4]]),
        ]
    elif kind == "daily":
        base["summary"] = (f"Operations summary for {site['name']} ({site['city']}): {site['workers_now']} workers on shift, "
                           f"{len(open_h)} open hazards, site risk index {site['score']:.0f}/100 ({site['band']}). "
                           f"Weather: wind {site['env']['wind']:.0f} km/h, rainfall {site['env']['rain24']:.0f} mm/24h, AQI {site['env']['aqi']:.0f}.")
        base["sections"] = [
            ("1 · Site Conditions", [
                f"Environmental envelope logged by Site Risk Agent — wind {site['env']['wind']:.0f} km/h, "
                f"temperature {site['env']['temp']:.0f}°C, humidity {site['env']['humidity']:.0f}%, noise {site['env']['noise']:.0f} dB.",
                f"Crane operations {'RESTRICTED — winds above 32 km/h threshold' if site['env']['wind'] > 32 else 'cleared — within operating envelope'}.",
            ]),
            ("2 · Open Hazards", [
                f"[{h['severity']}] {h['id']} — {h['type']} at {h['zone']} ({h['status']}, action: {h['action']})"
                for h in open_h[:6]] or ["No open hazards — all zones nominal."]),
            ("3 · PPE & Behaviour", [
                f"Helmet {site['ppe']['helmet']:.1f}% · vest {site['ppe']['vest']:.1f}% · harness {site['ppe']['harness']:.1f}% · goggles {site['ppe']['goggles']:.1f}% · boots {site['ppe']['boots']:.1f}%.",
                f"{len([e for e in site['equipment'] if e['status'] != 'OK'])} equipment unit(s) on WATCH/FAULT status."]),
            ("4 · Compliance Notes", [
                f"{c['title']} ({c['ref']}) — {c['status']}, due in {c['due_days']:.0f}d."
                for c in site["checks"] if c["status"] != "PASS"] or ["All periodic checks PASS — no regulatory debt."]),
            ("5 · Tomorrow's Focus", [
                r.choice(["Re-brief night shift on exclusion-zone discipline.",
                          "Third-party scaffold inspection requested for east face.",
                          "Dewatering pump pre-positioning at excavation pit.",
                          "Mock drill scheduled 10:00 IST — emergency egress route check.",
                          "Hydraulic oil sample dispatch for predictive lab analysis."])]),
        ]
    elif kind == "audit":
        rows = sorted(payloads.compliance_payload(s)["rows"], key=lambda x: x["status"] != "FAIL")
        base["summary"] = (f"Regulatory posture across {len(s.sites)} sites: {payloads.compliance_payload(s)['kpis']['rate']}% checks passing. "
                           f"{len([x for x in rows if x['status'] == 'FAIL'])} failures and {len([x for x in rows if x['due_days'] < 0])} overdue inspections compiled for audit review.")
        base["sections"] = [
            ("A · Framework Coverage", [f"{f[0]} — {f[1]}" for f in payloads.compliance_payload(s)["framework"]]),
            ("B · Findings Requiring Closure", [
                f"[{x['status']}] {x['title']} at {x['site']} — {x['ref']}, due in {x['due_days']}d"
                for x in rows if x["status"] != "PASS"][:8] or ["No adverse findings."]),
            ("C · Evidence Index", [
                f"Inspection registers: {r.randint(24, 60)} artifacts · permit hashes: {r.randint(10, 30)} · CAM clips: {r.randint(40, 120)}",
                "Chain-of-custody verified by Compliance Agent; hash-stamped manifest attached (Annex-1)."]),
        ]
    elif kind == "health":
        base["summary"] = (f"{site['name']}: risk-schedule-cost correlation reviewed. Site index {site['score']:.0f} ({site['band']}) "
                           f"with {site['prediction']['prob']:.0f}% 24h incident probability. Insurance exposure utilisation {site['exposure_util']:.0f}%.")
        base["sections"] = [
            ("1 · Safety vs Schedule", [
                f"{len(site['incidents'])} incidents in last 30d causing {sum(i['lost_days'] for i in site['incidents'])} lost person-days.",
                f"Hazard closure rate: {r.randint(62, 94)}% within 48h of detection."]),
            ("2 · Cost of Risk", [
                f"Open claims value: ₹{sum(c['cost_l'] for c in site['claims']):.0f} L across {len(site['claims'])} claim(s).",
                f"EMR trajectory: {site['insurance']['emr']:.2f} — {'favourable for renewal negotiation' if site['insurance']['emr'] < 1.05 else 'renewal premium loading likely'}."]),
            ("3 · Engine Prognosis", [
                f"Next-24h incident probability {site['prediction']['prob']:.0f}% ({site['prediction']['dclass']}).",
                r.choice(["Correlation flagged: hazard density vs pour-schedule compression (R² 0.71).",
                          "Crew fatigue index normal; night-shift overtime within limits.",
                          "Equipment age-mix driving 22% of hazard inflow — capex plan advised."])]),
        ]
    elif kind == "claim":
        claims = sorted(site["claims"], key=lambda c: -c["cost_l"])[:2] or [dict(id="CL-0000", type="No open claims", severity="LOW", cost_l=0, status="—", surveyor="—", filed=now().strftime("%Y-%m-%d"), confidence=100)]
        base["summary"] = (f"Claim support packet for {site['name']} — policy {site['insurance']['policy']} "
                           f"({site['insurance']['insurer']}, cover ₹{site['insurance']['coverage_cr']:.0f} Cr). "
                           f"Auto-compiled evidence: telemetry, CAM footage index, permits and agent findings.")
        base["sections"] = [
            ("1 · Claim Reference", [
                f"{c['id']} · {c['type']} · severity {c['severity']} · est. ₹{c['cost_l']:.0f} L · status {c['status']} · filed {c['filed']}"
                for c in claims]),
            ("2 · Evidence Bundle", [
                f"Site telemetry logs (24h window) — hash {r.randrange(10**12, 10**13):x}",
                f"CAM footage index — {r.randint(4, 18)} clips referenced to incident timeline",
                f"Permit & training register extracts — {r.randint(3, 9)} documents",
                "Agent findings snapshot at time of incident (Site Risk + Safety Agent)"]),
            ("3 · Admissibility Opinion", [
                f"Insurance Agent confidence: {claims[0]['confidence']:.0f}% — "
                + r.choice(["documentation complete; recommend fast-track survey.",
                            "minor gaps in witness statements; supervisor debrief attached.",
                            "PPE telemetry supports non-negligence position."])]),
        ]
    return base


if __name__ == "__main__":
    sim()  # boot simulation + background thread
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
