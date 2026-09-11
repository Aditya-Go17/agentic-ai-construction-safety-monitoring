"""
Agent definitions + natural-language feed generators for the
Agentic Construction Risk Intelligence Platform.

Each generator returns (agent_key, severity, message) and is chosen to
reference *live* simulated state so the feed feels real.
"""
import random

AGENTS = {
    "site_risk": {
        "name": "Site Risk Agent",
        "short": "SRA",
        "icon": "radar",
        "color": "#4db8ff",
        "role": "Monitors site activity, environmental conditions and equipment hazards",
        "skills": ["Hazard detection", "Environmental risk", "Equipment telemetry", "Risk scoring"],
    },
    "safety": {
        "name": "Safety Agent",
        "short": "SA",
        "icon": "helmet",
        "color": "#ffc400",
        "role": "Worker PPE compliance, unsafe behaviour and accident-prone zone analytics",
        "skills": ["PPE vision checks", "Behaviour analysis", "Zone heat-mapping", "Alerting"],
    },
    "compliance": {
        "name": "Compliance Agent",
        "short": "CA",
        "icon": "clipboard",
        "color": "#3ec9a7",
        "role": "Regulatory validation, standards tracking and inspection management",
        "skills": ["BOCW / IS / NBC audits", "Permit validation", "Inspection scheduling"],
    },
    "insurance": {
        "name": "Insurance Agent",
        "short": "IA",
        "icon": "shield",
        "color": "#8fd14f",
        "role": "Exposure assessment, claim risk analytics and severity evaluation",
        "skills": ["Exposure modelling", "Claim scoring", "Cost projection", "Evidence packs"],
    },
    "reporting": {
        "name": "Reporting Agent",
        "short": "RA",
        "icon": "doc",
        "color": "#ff8a1e",
        "role": "Aggregates all agent findings into reports, briefings and audit packs",
        "skills": ["Daily reports", "Executive summaries", "Audit documentation"],
    },
    "engine": {
        "name": "Risk Intelligence Engine",
        "short": "RIE",
        "icon": "cpu",
        "color": "#ff4d3d",
        "role": "Orchestrates agents, consolidates findings, predicts incidents and patterns",
        "skills": ["Orchestration", "Prediction", "Pattern mining", "Recommendations"],
    },
}

AGENT_KEYS = ["site_risk", "safety", "compliance", "insurance", "reporting"]


def make_generators():
    """Return a list of (weight, fn(rng, sim) -> (agent_key, severity, msg))."""
    G = []

    def gen(weight):
        def deco(fn):
            G.append((weight, fn))
            return fn
        return deco

    # ---------------- SITE RISK AGENT ----------------
    @gen(26)
    def zone_scan(rng, sim):
        s = sim.rand_site()
        flagged = sum(1 for z in s["zones"] if z["risk"] >= 55)
        total = len(s["zones"])
        sev = "HIGH" if flagged >= 3 else ("MODERATE" if flagged else "INFO")
        return "site_risk", sev, (
            f"Zone scan complete at {s['name']} — {total - flagged}/{total} zones nominal"
            + (f", {flagged} flagged for review" if flagged else "")
        )

    @gen(18)
    def wind_check(rng, sim):
        s = sim.rand_site()
        w = s["env"]["wind"]
        if w > 32:
            return "site_risk", "HIGH", (
                f"Anemometer @ {s['name']}: gusts {w:.0f} km/h — above 32 km/h safe limit, "
                f"crane operations at {s['zones'][1]['name']} recommended for hold")
        return "site_risk", "INFO", (
            f"Anemometer @ {s['name']}: wind {w:.0f} km/h — within crane operating limits")

    @gen(16)
    def equipment_beat(rng, sim):
        s = sim.rand_site()
        eq = rng.choice(s["equipment"])
        if eq["status"] == "FAULT":
            return "site_risk", "CRITICAL", (
                f"{eq['name']} @ {s['name']} telemetry fault — vibration {eq['vib']:.1f} mm/s "
                f"(limit 4.5), unit locked out for inspection")
        if eq["status"] == "WATCH":
            return "site_risk", "MODERATE", (
                f"{eq['name']} @ {s['name']} running hot — {eq['temp']:.0f}°C, load {eq['load']:.0f}%, "
                f"scheduled for predictive-maintenance review")
        return "site_risk", "INFO", (
            f"Telemetry OK — {eq['name']} @ {s['name']}: load {eq['load']:.0f}%, "
            f"vibration {eq['vib']:.1f} mm/s")

    @gen(10)
    def rain_watch(rng, sim):
        s = sim.rand_site()
        r = s["env"]["rain24"]
        if r > 35:
            return "site_risk", "HIGH", (
                f"Rainfall {r:.0f} mm/24h at {s['name']} — waterlogging watch on "
                f"{s['zones'][0]['name']}, dewatering pumps advised")
        return "site_risk", "INFO", (
            f"Weather sync @ {s['name']}: AQI {s['env']['aqi']:.0f}, humidity "
            f"{s['env']['humidity']:.0f}% — conditions logged")

    # ---------------- SAFETY AGENT ----------------
    @gen(24)
    def ppe_vision(rng, sim):
        s = sim.rand_site()
        z = rng.choice(s["zones"])
        cam = rng.randint(1, s["cameras"])
        k = rng.randint(1, 3)
        item = rng.choice(["helmets", "hi-vis vests", "safety gloves"])
        return "safety", "HIGH" if item == "helmets" else "MODERATE", (
            f"CAM-{cam:02d} @ {s['name']}, {z['name']}: {k} worker(s) detected without "
            f"{item} — auto-flagged, hooters triggered")

    @gen(14)
    def harness_check(rng, sim):
        s = sim.rand_site()
        m = rng.randint(6, 14)
        n = rng.randint(0, 2)
        sev = "CRITICAL" if n else "INFO"
        msg = (f"Harness audit @ {s['name']} elevated deck: {m - n}/{m} workers anchored correctly"
               if not n else
               f"ALERT: {n} worker(s) unclipped at height @ {s['name']} — supervisor dispatched")
        return "safety", sev, msg

    @gen(12)
    def zone_heat(rng, sim):
        s = sim.rand_site()
        z = max(s["zones"], key=lambda x: x["risk"])
        return "safety", "MODERATE" if z["risk"] > 55 else "INFO", (
            f"Accident-prone zone re-scored @ {s['name']}: {z['name']} now "
            f"{z['risk']:.0f}/100 — {'added to watchlist' if z['risk'] > 55 else 'stable'}")

    @gen(9)
    def behaviour(rng, sim):
        s = sim.rand_site()
        z = rng.choice(s["zones"])
        acts = ["phone use inside active work zone", "walking under suspended load",
                "unauthorised shortcut through exclusion area", "impaired ladder angle detected"]
        return "safety", "MODERATE", (
            f"Behaviour model @ {s['name']}: {rng.choice(acts)} near {z['name']} — "
            f"coaching notice issued to crew lead")

    # ---------------- COMPLIANCE AGENT ----------------
    @gen(18)
    def inspection(rng, sim):
        s = sim.rand_site()
        c = rng.choice([c for c in s["checks"] if c["status"] != "PASS"] or s["checks"])
        if c["status"] == "FAIL":
            return "compliance", "CRITICAL", (
                f"{c['title']} @ {s['name']} FAILED audit ({c['ref']}) — corrective notice "
                f"drafted, re-inspection auto-scheduled")
        overdue = c["due_days"] < 0
        return "compliance", "HIGH" if overdue else "MODERATE", (
            f"Inspection tracker: {c['title']} @ {s['name']} "
            + (f"overdue by {abs(c['due_days'])}d — escalated to PM" if overdue
               else f"due in {c['due_days']}d ({c['ref']})"))

    @gen(12)
    def permit(rng, sim):
        s = sim.rand_site()
        p = rng.choice(["Hot-work permit", "Excavation shoring permit", "Working-at-height permit",
                        "Lifting plan clearance", "Confined-space entry permit"])
        return "compliance", "INFO", (
            f"Permit audit @ {s['name']}: {p} valid — next review "
            f"{rng.randint(2, 20)}d, blockchain-stamped copy archived")

    @gen(8)
    def bocw(rng, sim):
        s = sim.rand_site()
        return "compliance", "INFO", (
            f"BOCW Act welfare-facility checklist passed @ {s['name']} — drinking water, "
            f"creche & first-aid registers verified")

    # ---------------- INSURANCE AGENT ----------------
    @gen(14)
    def claim_rescore(rng, sim):
        s = sim.rand_site()
        claims = s["insurance"]["claims"]
        if not claims:
            return "insurance", "INFO", (
                f"Exposure review {s['name']}: ₹{s['insurance']['coverage_cr']:.0f} Cr covered, "
                f"utilization {sim.exposure_util(s):.0f}% — premium band stable")
        c = rng.choice(claims)
        return "insurance", "HIGH" if c["severity"] in ("HIGH", "CRITICAL") else "MODERATE", (
            f"Claim {c['id']} ({s['short']}) re-scored → {c['severity']} — "
            f"est. ₹{c['cost_l']:.0f} L, status: {c['status']}")

    @gen(10)
    def emr(rng, sim):
        s = sim.rand_site()
        emr = s["insurance"]["emr"]
        trend = "improving" if emr < 1.0 else ("stable" if emr < 1.2 else "needs intervention")
        return "insurance", "INFO" if emr < 1.2 else "MODERATE", (
            f"EMR projection {s['short']}: {emr:.2f} — {trend}; incident-frequency model "
            f"refreshed with last 30d data")

    @gen(7)
    def evidence(rng, sim):
        s = sim.rand_site()
        n = rng.randint(4, 18)
        return "insurance", "INFO", (
            f"Claim documentation pack auto-compiled for {s['short']} — {n} artifacts "
            f"(photos, telemetry logs, permits) hashed & attached")

    # ---------------- REPORTING AGENT ----------------
    @gen(12)
    def daily(rng, sim):
        s = sim.rand_site()
        return "reporting", "INFO", (
            f"Daily site report v{rng.randint(2, 9)} compiled for {s['short']} — "
            f"{rng.randint(6, 11)} sections, distributed to {rng.randint(4, 12)} stakeholders")

    @gen(10)
    def exec_sum(rng, sim):
        fleet = sim.fleet_score()
        band = sim.band_name(fleet)
        return "reporting", "HIGH" if band in ("HIGH", "CRITICAL") else "INFO", (
            f"Executive risk summary drafted — fleet index {fleet:.0f} ({band}), "
            f"{len(sim.open_hazards())} open hazards fleet-wide")

    @gen(8)
    def audit_pack(rng, sim):
        return "reporting", "INFO", (
            f"Audit-ready evidence pack updated — {rng.randint(24, 60)} artifacts, "
            f"chain-of-custody intact, retention 7y")

    # ---------------- INTELLIGENCE ENGINE ----------------
    @gen(10)
    def prediction(rng, sim):
        s = sim.rand_site()
        p = s["prediction"]["prob"]
        sev = "HIGH" if p > 55 else ("MODERATE" if p > 35 else "INFO")
        return "engine", sev, (
            f"Incident probability {s['short']} (24h): {p:.0f}% "
            f"({s['prediction']['class']}) — model v2.4, AUC 0.91")

    @gen(8)
    def pattern(rng, sim):
        pt = rng.choice(sim.patterns)
        return "engine", "MODERATE" if pt["confidence"] > 75 else "INFO", (
            f"Pattern confirmed: {pt['title']} (conf {pt['confidence']:.0f}%, "
            f"{pt['occurrences']} occurrences)")

    return G


GENERATORS = make_generators()
