"""Snapshot builders — turn live sim state into JSON payloads for pages & APIs."""
import random as _random
from datetime import timedelta
from .simulator import get_sim, now, clamp, SEV_WEIGHT


def _ago(ts_iso):
    t = datetime.fromisoformat(ts_iso)
    return (now() - t).total_seconds() / 60


from datetime import datetime  # noqa: E402


def site_brief(s):
    return dict(id=s["id"], short=s["short"], name=s["name"], typelabel=s["typelabel"],
                city=s["city"], contractor=s["contractor"], workers=s["workers"],
                workers_now=s["workers_now"], score=round(s["score"], 1), band=s["band"],
                band_color=s["band_color"], hazards=len([h for h in s["hazards"] if h["status"] == "OPEN"]),
                open_checks=len([c for c in s["checks"] if c["status"] != "PASS"]),
                trend=[round(h["v"], 1) for h in list(s["hist"])[-40:]],
                env=dict(wind=s["env"]["wind"], temp=s["env"]["temp"], rain24=s["env"]["rain24"], aqi=s["env"]["aqi"]),
                prediction=dict(prob=round(s["prediction"]["prob"]), dclass=s["prediction"]["dclass"],
                                slope=s["prediction"]["slope"]),
                cameras=s["cameras"],
                ppe_avg=round(sum(s["ppe"].values()) / 5, 1),
                claims_open=len([c for c in s["claims"] if c["status"] != "Settled"]))


def overview(sim):
    fleet = sim.fleet_score()
    band, col = sim.band(fleet)
    sites = sorted(sim.sites, key=lambda s: -s["score"])
    # fleet history from worker-weighted average
    hist_len = min(len(sites[0]["hist"]), 120)
    fleet_hist = []
    site_lists = [list(s["hist"])[-hist_len:] for s in sim.sites]
    tw = sum(s["workers"] for s in sim.sites)
    for i in range(hist_len):
        v = sum(lst[i]["v"] * s["workers"] for s, lst in zip(sim.sites, site_lists)) / tw
        fleet_hist.append(dict(t=site_lists[0][i]["t"], v=round(v, 1)))
    # forecast: extend last slope
    last = fleet_hist[-1]["v"]
    prev = fleet_hist[-6]["v"] if len(fleet_hist) > 6 else last
    slope = (last - prev) / 6
    forecast = [dict(t=(now() + timedelta(minutes=5 * (i + 1))).isoformat(),
                     v=round(clamp(last + slope * (i + 1) * 0.55, 5, 97), 1)) for i in range(10)]
    open_h = sim.open_hazards()
    kpis = dict(
        sites_active=len(sim.sites),
        workers_now=sum(s["workers_now"] for s in sim.sites),
        workers_total=sum(s["workers"] for s in sim.sites),
        open_hazards=len(open_h),
        critical_hazards=len([h for h in open_h if h["severity"] == "CRITICAL"]),
        incidents30=sum(len(s["incidents"]) for s in sim.sites),
        ppe_avg=round(sum(sum(s["ppe"].values()) / 5 for s in sim.sites) / len(sim.sites), 1),
        active_alerts=len([a for a in sim.alerts if a["stage"] < 4]),
        compliance_rate=round(sum(1 for s in sim.sites for c in s["checks"] if c["status"] == "PASS")
                              / max(sum(len(s["checks"]) for s in sim.sites), 1) * 100, 1),
        exposure_cr=round(sum(s["insurance"]["coverage_cr"] for s in sim.sites), 0),
        claims_open=len([c for s in sim.sites for c in s["claims"] if c["status"] != "Settled"]),
        emr=round(sum(s["insurance"]["emr"] for s in sim.sites) / len(sim.sites), 2),
    )
    sev_counts = {k: 0 for k in ("LOW", "MODERATE", "HIGH", "CRITICAL")}
    for h in open_h:
        sev_counts[h["severity"]] += 1
    incident_types = {}
    for s in sim.sites:
        for i in s["incidents"]:
            incident_types[i["type"]] = incident_types.get(i["type"], 0) + 1
    recommendations = build_recommendations(sim, sites)
    n = len(sim.sites)
    factor_avgs = {k: round(sum(s["sub"][k] for s in sim.sites) / n, 1)
                   for k in ("weather", "equipment", "hazards", "behaviour", "compliance")}
    return dict(
        fleet=round(fleet, 1), band=band, band_color=col,
        kpis=kpis, fleet_hist=fleet_hist, forecast=forecast,
        factor_avgs=factor_avgs,
        sites=[site_brief(s) for s in sites],
        hot_prediction=[dict(id=s["id"], short=s["short"], name=s["name"], prob=round(s["prediction"]["prob"]),
                             dclass=s["prediction"]["dclass"], slope=s["prediction"]["slope"],
                             top_factor=max(s["sub"], key=lambda k: s["sub"][k] if k != "score" else -1))
                        for s in sorted(sim.sites, key=lambda s: -s["prediction"]["prob"])[:4]],
        hazard_mix=sev_counts,
        incident_types=sorted(incident_types.items(), key=lambda kv: -kv[1]),
        feed=feed_items(sim, 14),
        patterns=sim.patterns,
        recommendations=recommendations,
        alerts=[alert_brief(a) for a in list(sim.alerts)[:6]],
        ppe_fleet={k: round(sum(s["ppe"][k] for s in sim.sites) / len(sim.sites), 1)
                   for k in ("helmet", "vest", "harness", "goggles", "boots")},
    )


def build_recommendations(sim, sites):
    recs = []
    actions = {
        "hazards": ("Clear open hazards", "Prioritise mitigation queue — {n} open findings, {c} critical", "CRITICAL"),
        "weather": ("Weather protocol", "Wind/rain thresholds near limits — stage outdoor lifts after re-check", "HIGH"),
        "equipment": ("Equipment maintenance", "Schedule predictive maintenance for units in WATCH/FAULT", "HIGH"),
        "behaviour": ("PPE enforcement drive", "Tool-box talk + camera enforcement on low-compliance shifts", "MODERATE"),
        "compliance": ("Close compliance gaps", "Overdue inspections detected — book validators within 48h", "HIGH"),
    }
    for s in sites[:3]:
        key = max(("weather", "equipment", "hazards", "behaviour", "compliance"),
                  key=lambda k: s["sub"][k])
        t, d, pr = actions[key]
        crit_n = sum(1 for h in s["hazards"] if h["severity"] == "CRITICAL")
        recs.append(dict(priority=pr, title=f"{t} — {s['short']}",
                         detail=d.format(n=s["hazards"], c=crit_n), site=s["id"]))
    fleet_ppe = sum(sum(s["ppe"].values()) / 5 for s in sim.sites) / len(sim.sites)
    if fleet_ppe < 88:
        recs.append(dict(priority="MODERATE", title="Fleet-wide PPE programme",
                         detail=f"Average PPE compliance is {fleet_ppe:.1f}% — target 95% via smart-helmet pilot", site=None))
    recs.append(dict(priority="LOW", title="Weekly executive briefing",
                     detail="Reporting Agent will circulate consolidated risk summary Friday 17:00 IST", site=None))
    return recs[:6]


def feed_items(sim, n=30):
    from .agents import AGENTS
    out = []
    for f in list(sim.agent_feed)[:n]:
        ag = AGENTS[f["agent"]]
        out.append(dict(ts=f["ts"], agent=f["agent"], agent_name=ag["name"], color=ag["color"],
                        severity=f["severity"], msg=f["msg"]))
    return out


def alert_brief(a):
    return dict(id=a["id"], ts=a["ts"], site=a["site"], site_short=a["site_short"], title=a["title"],
                severity=a["severity"], channels=a["channels"], stage=a["stage"], ack=a["ack"],
                owner=a["owner"],
                timeline=[dict(t=t.isoformat(), label=l) for t, l, _ in a["timeline"]],
                resolved_ts=a.get("resolved_ts"))


def agents_payload(sim):
    from .agents import AGENTS, AGENT_KEYS
    agents = []
    for k in AGENT_KEYS + ["engine"]:
        st = sim.agent_state[k]
        agents.append(dict(key=k, **AGENTS[k], status=st["status"], task=st.get("task", st["last_finding"]),
                           events=st["events"], latency=round(st["latency"]), confidence=round(st["confidence"], 1),
                           last_finding=st["last_finding"]))
    task_bank = {
        "site_risk": ["Scanning zone telemetry", "Fusing weather feeds", "Scoring equipment health", "Triangulating hazards"],
        "safety": ["Streaming vision CAM feeds", "Scoring PPE compliance", "Mapping accident-prone zones", "Dispatching coaching notices"],
        "compliance": ["Validating BOCW registers", "Tracking inspection due-dates", "Auditing permits", "Drafting corrective notices"],
        "insurance": ["Re-scoring open claims", "Modelling exposure bands", "Updating EMR projections", "Compiling evidence packs"],
        "reporting": ["Compiling daily reports", "Drafting executive summary", "Versioning audit packs", "Circulating health reports"],
        "engine": ["Orchestrating 5 agents", "Recomputing risk indices", "Mining incident patterns", "Forecasting 24h probabilities"],
    }
    for a in agents:
        bank = task_bank[a["key"]]
        a["task"] = bank[sim.ticks % len(bank)]
    return dict(agents=agents, feed=feed_items(sim, 40), ticks=sim.ticks,
                uptime_min=round((now() - sim.started).total_seconds() / 60))


def sites_payload(sim):
    return dict(sites=[site_brief(s) for s in sorted(sim.sites, key=lambda s: -s["score"])])


def site_detail(sim, sid):
    s = next((x for x in sim.sites if x["id"] == sid), None)
    if not s:
        return None
    hz = sorted([h for h in s["hazards"] if h["status"] != "RESOLVED"], key=lambda h: -SEV_WEIGHT[h["severity"]])
    return dict(site=dict(
        id=s["id"], short=s["short"], name=s["name"], typelabel=s["typelabel"], city=s["city"],
        contractor=s["contractor"], workers=s["workers"], workers_now=s["workers_now"],
        score=round(s["score"], 1), band=s["band"], band_color=s["band_color"],
        sub={k: round(v, 1) for k, v in s["sub"].items() if k != "score"},
        prediction=dict(prob=round(s["prediction"]["prob"]), dclass=s["prediction"]["dclass"]),
        zones=[dict(name=z["name"], x=z["x"], y=z["y"], w=z["w"], h=z["h"], risk=round(z["risk"]),
                    hazards=z["hazards"]) for z in s["zones"]],
        env={k: round(v, 1) for k, v in s["env"].items()},
        ppe={k: round(v, 1) for k, v in s["ppe"].items()},
        equipment=[dict(name=e["name"], zone=e["zone"], status=e["status"], load=round(e["load"]),
                        temp=round(e["temp"]), vib=round(e["vib"], 1), service_days=e["service_days"])
                   for e in s["equipment"]],
        hazards=[dict(id=h["id"], zone=h["zone"], type=h["type"], cat=h["cat"], severity=h["severity"],
                      status=h["status"], age_min=round(h["age_min"]), action=h["action"],
                      detected_by=h["detected_by"]) for h in hz],
        hist=[dict(t=h["t"], v=round(h["v"], 1)) for h in list(s["hist"])[-120:]],
        cameras=s["cameras"],
        insurance=dict(policy=s["insurance"]["policy"], insurer=s["insurance"]["insurer"],
                       coverage_cr=round(s["insurance"]["coverage_cr"]), emr=s["insurance"]["emr"],
                       premium_cr=round(s["insurance"]["premium_cr"], 2)),
        checks=[dict(title=c["title"], ref=c["ref"], status=c["status"],
                     due_days=round(c["due_days"])) for c in s["checks"]],
    ))


def safety_payload(sim):
    # synthesize a live violation stream from PPE state
    viol = []
    for s in sim.sites:
        cams = s["cameras"]
        for i in range(max(1, int((100 - s["ppe"]["helmet"]) / 9))):
            z = sim.rng.choice(s["zones"])
            viol.append(dict(ts=(now() - timedelta(minutes=sim.rng.uniform(1, 90))).isoformat(),
                             site=s["short"], site_id=s["id"], zone=z["name"],
                             cam=f"CAM-{sim.rng.randint(1, cams):02d}",
                             type=sim.rng.choice(["No helmet", "No hi-vis vest", "No gloves", "Unclipped harness", "Phone in work zone"]),
                             workers=sim.rng.randint(1, 3),
                             status=sim.rng.choice(["Auto-flagged", "Supervisor notified", "Coaching issued"])))
    viol.sort(key=lambda v: v["ts"], reverse=True)
    heat = []
    for s in sim.sites:
        for z in s["zones"]:
            heat.append(dict(site=s["short"], zone=z["name"], risk=round(z["risk"])))
    top_heat = sorted(heat, key=lambda x: -x["risk"])[:10]
    days, counts = violation_trend(sim)
    ppe_fleet = {k: round(sum(s["ppe"][k] for s in sim.sites) / len(sim.sites), 1)
                 for k in ("helmet", "vest", "harness", "goggles", "boots")}
    incidents = []
    for s in sim.sites:
        for i in s["incidents"]:
            incidents.append(dict(site=s["short"], type=i["type"], severity=i["severity"],
                                  zone=i["zone"], lost_days=i["lost_days"], ppe_related=i["ppe_related"],
                                  days_ago=round((now() - i["ts"]).days, 1)))
    return dict(
        kpis=dict(ppe_avg=round(sum(ppe_fleet.values()) / 5, 1),
                  violations_today=len(viol),
                  workers=sum(s["workers_now"] for s in sim.sites),
                  cams=sum(s["cameras"] for s in sim.sites),
                  ppe_incidents=len([i for i in incidents if i["ppe_related"]])),
        ppe=ppe_fleet, violations=viol[:18], heat=top_heat, trend_days=days, trend_counts=counts,
        incidents=incidents[-14:],
        zones_watch=[dict(site=s["short"], zone=max(s["zones"], key=lambda z: z["risk"])["name"],
                          risk=round(max(z["risk"] for z in s["zones"]))) for s in sim.sites])


def violation_trend(sim):
    import random as _random
    days, counts = [], []
    r = _random.Random(7)
    base = sum(100 - s["ppe"]["helmet"] for s in sim.sites) / 2
    for i in range(13, -1, -1):
        d = (now() - timedelta(days=i)).strftime("%d %b")
        days.append(d)
        counts.append(round(base * r.uniform(0.75, 1.25)))
    return days, counts


def compliance_payload(sim):
    rows = []
    for s in sim.sites:
        for c in s["checks"]:
            rows.append(dict(site=s["short"], site_id=s["id"], title=c["title"], ref=c["ref"],
                             status=c["status"], due_days=round(c["due_days"]), last_done=c["last_done"]))
    rows.sort(key=lambda r: (r["status"] != "FAIL", r["status"] != "RISK", r["due_days"]))
    inspections = [r for r in rows if r["due_days"] <= 5][:10]
    by_site = [dict(site=s["short"],
                    rate=round(100 * len([c for c in s["checks"] if c["status"] == "PASS"]) / len(s["checks"])))
               for s in sim.sites]
    counts = {k: len([r for r in rows if r["status"] == k]) for k in ("PASS", "RISK", "FAIL")}
    total = max(sum(counts.values()), 1)
    overdue = len([r for r in rows if r["due_days"] < 0])
    return dict(
        kpis=dict(rate=round(counts["PASS"] / total * 100, 1),
                  overdue=overdue, failing=counts["FAIL"],
                  audit_ready=round(clamp(100 - counts["FAIL"] * 4 - overdue * 1.5, 20, 99), 1),
                  standards=len(rows)),
        rows=rows[:20], inspections=inspections, by_site=by_site, counts=counts,
        framework=[("BOCW Act 1996", "Building & Other Construction Workers — welfare & safety"),
                   ("NBC 2016", "National Building Code — structural & fire safety"),
                   ("IS 3696", "BIS — scaffolding & ladders safety code"),
                   ("CEA Reg. 2010", "Central Electricity Authority — electrical safety"),
                   ("CPCB Norms", "Noise & air-quality limits for sites")],
    )


def insurance_payload(sim):
    claims = []
    for s in sim.sites:
        for c in s["claims"]:
            cc = dict(c)
            cc["filed"] = c["filed"][:10]
            claims.append(cc)
    claims.sort(key=lambda c: -c["cost_l"])
    open_claims = [c for c in claims if c["status"] != "Settled"]
    sev_counts = {k: 0 for k in ("LOW", "MODERATE", "HIGH", "CRITICAL")}
    for c in claims:
        sev_counts[c["severity"]] += 1
    months, costs = [], []
    r = _random.Random(11)
    for i in range(5, -1, -1):
        d = (now() - timedelta(days=30 * i)).strftime("%b")
        months.append(d)
        costs.append(round(r.uniform(8, 42) + (4 if i == 0 else 0)))
    by_site = [dict(site=s["short"], risk=round(clamp(s["insurance"]["emr"] * 42 + s["score"] * 0.45, 5, 97)),
                    emr=s["insurance"]["emr"],
                    coverage=round(s["insurance"]["coverage_cr"]),
                    util=round(s["exposure_util"] or 0)) for s in sim.sites]
    by_site.sort(key=lambda x: -x["risk"])
    total_cov = sum(s["insurance"]["coverage_cr"] for s in sim.sites)
    return dict(
        kpis=dict(exposure=round(total_cov), open_claims=len(open_claims),
                  est_cost=round(sum(c["cost_l"] for c in open_claims)),
                  emr=round(sum(s["insurance"]["emr"] for s in sim.sites) / len(sim.sites), 2),
                  premium=round(sum(s["insurance"]["premium_cr"] for s in sim.sites), 1)),
        claims=claims[:12], sev=sev_counts, months=months, costs=costs, by_site=by_site,
        packets=[dict(id=f"PK-{2100 + i}", site=s["short"], artifacts=sim.rng.randint(6, 22),
                      status=sim.rng.choice(["Ready", "Ready", "Draft"]))
                 for i, s in enumerate(sim.sites[:6])],
    )


def alerts_payload(sim):
    return dict(alerts=[alert_brief(a) for a in list(sim.alerts)[:30]],
                kpis=dict(active=len([a for a in sim.alerts if a["stage"] < 4]),
                          escalated=len([a for a in sim.alerts if 2 <= a["stage"] < 4]),
                          resolved=len([a for a in sim.alerts if a["stage"] == 4]),
                          critical=len([a for a in sim.alerts if a["severity"] == "CRITICAL" and a["stage"] < 4])))


def ticker_payload(sim):
    return dict(items=sim.ticker_items, bell=len([a for a in sim.alerts if not a["ack"] and a["stage"] < 4]),
                fleet=round(sim.fleet_score(), 1), band=sim.band_name(sim.fleet_score()))
