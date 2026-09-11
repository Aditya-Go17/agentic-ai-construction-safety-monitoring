"""
Simulation engine — generates random-but-realistic live construction data,
runs the agent feed, scores risk and powers every dashboard.

A background thread calls tick() every TICK_SECONDS; Flask routes read
immutable snapshots via build_*_payload() functions.
"""
import random
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone

TICK_SECONDS = 5
IST = timezone(timedelta(hours=5, minutes=30))
SEV_WEIGHT = {"LOW": 6, "MODERATE": 16, "HIGH": 34, "CRITICAL": 70}
BANDS = [(35, "LOW", "#8fd14f"), (55, "MODERATE", "#ffcf3f"), (75, "HIGH", "#ff8a1e"), (101, "CRITICAL", "#ff4d3d")]

HAZARD_TYPES = [
    ("Unstable trench wall", "Excavation"), ("Missing guardrail", "Fall"),
    ("Exposed live cable", "Electrical"), ("Overloaded crane radius", "Lifting"),
    ("Loose scaffolding clamp", "Fall"), ("Waterlogged pit edge", "Ground"),
    ("Falling-object risk", "Struck-by"), ("Defective ladder", "Fall"),
    ("Protruding rebar bundle", "Impalement"), ("Gas pocket near shaft", "Atmospheric"),
    ("Obstructed fire lane", "Fire"), ("Unshored deep cut", "Collapse"),
]

ZONE_SLOTS = [
    (40, 40, 230, 62), (40, 140, 230, 230), (40, 410, 230, 72),
    (310, 40, 200, 168), (310, 248, 200, 122), (310, 410, 200, 72),
    (550, 40, 210, 218), (550, 298, 210, 184),
]
ZONE_BASE_RISK = [24, 62, 38, 58, 46, 42, 52, 18]

ZONES_BY_TYPE = {
    "highrise": ["Worker Welfare Zone", "Excavation Pit", "Loading Bay", "Crane Pad A",
                 "Rebar & Steel Yard", "Concrete Pour Deck", "Scaffold — East Face", "Material Storage"],
    "metro": ["Site Office Zone", "TBM Launch Shaft", "Loading Bay", "Cross-Passage Face",
              "Muck Conveyor Yard", "Grouting Station", "Vent Shaft Head", "Rail Layout Bay"],
    "bridge": ["Welfare Zone", "Pier Workstream", "Loading Bay", "Cable Crane Pad",
               "Steel Truss Yard", "Formwork Gallery", "Over-water Trestle", "Barge Mooring Deck"],
    "industrial": ["Control Bldg Zone", "Heavy Eqp Laydown", "Truck Bay", "Struct Erection Bay",
                   "Casting Yard", "Hot-Work Zone", "Chemical Storage", "Tank Farm"],
    "marine": ["Crew Jetty Access", "Jetty Front Edge", "Aggregate Yard", "Piling Barge Deck",
               "Cofferdam Cell", "Crane Pad B", "Dredger Mooring", "Fuel Storage"],
    "residential": ["Welfare Zone", "Footing Trench", "Loading Bay", "Tower Crane Pad",
                    "Brick & Mortar Yard", "Plaster Station", "Scaffold — Block A", "Material Storage"],
}

EQ_BY_TYPE = {
    "highrise": ["Tower Crane TC-01", "Tower Crane TC-02", "Passenger Hoist PH-02", "Concrete Pump CP-01", "Diesel Gen DG-01"],
    "metro": ["TBM 'Bagmati'", "Loco & Muck Train LT-02", "Gantry Crane GC-01", "Grout Plant GP-01", "Ventilation Fan VF-03"],
    "bridge": ["Cable Crane CC-01", "Barge Crane BC-02", "Hydraulic Rig HR-04", "Welding Set WS-07", "Gen Set DG-03"],
    "industrial": ["Gantry Crane GC-02", "Forklift FL-05", "Batching Plant BP-01", "Mobile Crane MC-11", "Compressor CP-06"],
    "marine": ["Piling Rig PR-02", "Dredger Pump DP-01", "Floating Crane FC-01", "Tug Winch TW-03", "Gen Set DG-05"],
    "residential": ["Tower Crane TC-03", "Mini Excavator EX-08", "Mixer Machine MM-04", "Material Hoist MH-01", "Bar Bending Machine BB-02"],
}

SITES_DEF = [
    dict(id="SITE-101", short="SKY-TWR", name="Bengal Skyline Tower 42", stype="highrise",
         typelabel="High-Rise · 42 Floors", city="Salt Lake Sector V, Kolkata",
         contractor="Meridian Infra Pvt. Ltd.", workers=186, base=58, cameras=14, contract_cr=310),
    dict(id="SITE-102", short="MET-JOK", name="Metro Purple Line Ext.", stype="metro",
         typelabel="Underground Metro · Tunnelling", city="Joka–Taratala Corridor",
         contractor="EastBridge Metro JV", workers=240, base=72, cameras=22, contract_cr=1850),
    dict(id="SITE-103", short="RIV-RED", name="Riverside Redevelopment", stype="highrise",
         typelabel="Mixed-Use · 3 Towers", city="Howrah Maidan", 
         contractor="Ganges BuildCon", workers=142, base=47, cameras=11, contract_cr=420),
    dict(id="SITE-104", short="ITP-P3", name="Newtown IT Park Phase III", stype="residential",
         typelabel="Commercial Campus", city="New Town, Kolkata",
         contractor="Meridian Infra Pvt. Ltd.", workers=210, base=36, cameras=12, contract_cr=560),
    dict(id="SITE-105", short="SETU-RT", name="Vidyasagar Setu Retrofit", stype="bridge",
         typelabel="Bridge · Cable-Stayed", city="Hooghly River Crossing",
         contractor="Hooghly Bridge Co.", workers=64, base=66, cameras=9, contract_cr=240),
    dict(id="SITE-106", short="STL-EXP", name="Steel Plant Expansion Blk-C", stype="industrial",
         typelabel="Heavy Industrial", city="Durgapur",
         contractor="Damodar Steel Works", workers=320, base=61, cameras=26, contract_cr=980),
    dict(id="SITE-107", short="PORT-JET", name="Ganga Jetty Modernisation", stype="marine",
         typelabel="Marine · Port Jetty", city="Haldia Dock Complex",
         contractor="Bengal Marine Engg.", workers=98, base=69, cameras=8, contract_cr=310),
    dict(id="SITE-108", short="HIL-RES", name="Hillcrest Residences", stype="residential",
         typelabel="Residential · 4 Blocks", city="Siliguri",
         contractor="Ganges BuildCon", workers=120, base=33, cameras=7, contract_cr=180),
]

COMPLIANCE_CATALOG = [
    ("Scaffolding certification", "IS 3696-1:1987", 30),
    ("Crane inspection certificate", "IS 3177 / BOCW §46", 45),
    ("Excavation shoring permit", "NBC 2016 Pt-7 §10", 14),
    ("Electrical earthing audit", "CEA Reg. 2010 §35", 60),
    ("Fire extinguisher placement", "NBC 2016 Pt-4 §A-6", 30),
    ("Working-at-height permit", "BOCW Act 1996 §32", 7),
    ("PPE issuance register", "BOCW Act 1996 §35", 15),
    ("Noise limit compliance", "CPCB / Noise Rules 2000", 30),
    ("Welfare facilities audit", "BOCW Act 1996 §42", 45),
    ("Waste & debris disposal", "C&B Waste Rules 2016", 30),
    ("Lifting plan approval", "IS 3177:2020", 20),
    ("First-aid & emergency drill", "BOCW Act 1996 §46", 60),
]

CLAIM_TYPES = ["Fall injury", "Struck by object", "Electrocution", "Machinery injury",
               "Slip & trip", "Heat stroke", "Third-party property", "Fire damage"]
CLAIM_STATUS = ["Filed", "Under Review", "Survey Scheduled", "Approved", "Settled"]
INCIDENT_TYPES = ["Fall from height", "Struck by object", "Electrocution", "Caught between",
                  "Slip / Trip", "Machinery contact", "Heat stress", "Vehicle strike"]

PATTERNS_DEF = [
    ("PPE violations peak 14:00–16:00", "Helmet & vest non-compliance spikes 2.3× during shift changeover hours across 6 sites.", 84, 37, "+6%"),
    ("Crane holds correlate with wind > 32 km/h", "All 11 lifting-related near-misses occurred on days with gusts above the 32 km/h threshold.", 76, 11, "+2%"),
    ("Monday incident rate 1.8× weekly mean", "Week-opening rush and unverified weekend repairs drive early-week risk.", 69, 23, "+4%"),
    ("Rainfall > 40 mm/24h precedes trench hazards", "70% of excavation hazards were logged within 48h of heavy rain events.", 88, 15, "+9%"),
    ("Electrical hazards cluster near material yards", "Temporary cabling across storage zones accounts for 46% of electrical findings.", 61, 19, "-3%"),
]


def now():
    return datetime.now(IST)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Simulator:
    def __init__(self):
        self.rng = random.Random()
        self.lock = threading.RLock()
        self.started = now()
        self.ticks = 0
        self.ticker_items = []
        self.patterns = [dict(title=t, detail=d, confidence=c + self.rng.uniform(-3, 3),
                              occurrences=o, trend=tr) for t, d, c, o, tr in PATTERNS_DEF]
        self.agent_feed = deque(maxlen=80)
        self.alerts = deque(maxlen=60)
        self.alert_seq = 4100
        self.agent_state = {k: dict(status="ANALYSING", task="Booting models…",
                                    events=self.rng.randint(1200, 9000), latency=self.rng.randint(40, 180),
                                    confidence=self.rng.uniform(88, 97), last_finding="Initialising…")
                            for k in ["site_risk", "safety", "compliance", "insurance", "reporting", "engine"]}
        self._build_sites()
        self._bootstrap_history()
        self._seed_alerts()
        self.recompute()
        # align bootstrapped history level with the freshly computed score
        # so the live series joins smoothly (no visual discontinuity)
        for s in self.sites:
            delta = s["score"] - s["hist"][-1]["v"]
            for p in s["hist"]:
                p["v"] = clamp(p["v"] + delta, 6, 96)
        self._push_feed(6)

    # ------------------------------------------------------------------ setup
    def _build_sites(self):
        self.sites = []
        for d in SITES_DEF:
            r = random.Random(hash(d["id"]) & 0xffffffff)
            zones = []
            names = ZONES_BY_TYPE[d["stype"]]
            for i, slot in enumerate(ZONE_SLOTS):
                x, y, w, h = slot
                zones.append(dict(name=names[i], x=x, y=y, w=w, h=h,
                                  base=ZONE_BASE_RISK[i] + (d["base"] - 45) * 0.5 + r.uniform(-6, 6),
                                  risk=0, hazards=0))
            equipment = []
            for i, ename in enumerate(EQ_BY_TYPE[d["stype"]]):
                st = r.choices(["OK", "WATCH", "FAULT"], weights=[78, 16, 6])[0]
                equipment.append(dict(name=ename, zone=zones[min(3 + i % 4, len(zones) - 1)]["name"],
                                      status=st, load=r.uniform(35, 88), temp=r.uniform(48, 78),
                                      vib=r.uniform(1.2, 4.4), service_days=r.randint(-4, 40)))
            checks = []
            chosen = r.sample(COMPLIANCE_CATALOG, 8)
            for title, ref, freq in chosen:
                due = r.randint(-9, 40)
                status = r.choices(["PASS", "RISK", "FAIL"], weights=[70, 22, 8])[0]
                if due < -2 and r.random() < 0.5:
                    status = "FAIL" if r.random() < 0.5 else "RISK"
                checks.append(dict(title=title, ref=ref, due_days=due, status=status,
                                   last_done=r.randint(5, 60)))
            claims = []
            for i in range(r.randint(0, 3)):
                claims.append(self._new_claim(r, d, age_days=r.randint(2, 60)))
            incidents = []
            n_inc = max(0, int(r.gauss((d["base"] - 25) / 6, 1.4)))
            for i in range(n_inc):
                incidents.append(dict(
                    ts=now() - timedelta(days=r.uniform(0.5, 30)),
                    type=r.choice(INCIDENT_TYPES),
                    severity=r.choices(["LOW", "MODERATE", "HIGH"], weights=[45, 38, 17])[0],
                    zone=r.choice(zones)["name"], lost_days=r.randint(0, 12),
                    cost_l=r.uniform(0.4, 22), ppe_related=r.random() < 0.42))
            env = dict(wind=r.uniform(8, 30), temp=r.uniform(27, 35), humidity=r.uniform(62, 88),
                       aqi=r.uniform(85, 165), noise=r.uniform(68, 96), vib=r.uniform(0.4, 2.6),
                       rain24=r.uniform(0, 28))
            self.sites.append(dict(
                **d, zones=zones, equipment=equipment, checks=checks, incidents=incidents,
                claims=claims, env=env,
                ppe={k: clamp(r.gauss(88 - (d["base"] - 45) * 0.35, 4), 55, 99)
                     for k in ["helmet", "vest", "harness", "goggles", "boots"]},
                workers_now=int(d["workers"] * r.uniform(0.62, 0.95)),
                insurance=dict(policy=f"POL-{r.randint(70000, 99000)}-CN",
                               insurer=r.choice(["Bharat General Ins.", "Eastern Assurance Co.", "GangaRe Insurance"]),
                               coverage_cr=d["contract_cr"] * r.uniform(0.85, 1.15),
                               premium_cr=d["contract_cr"] * r.uniform(0.008, 0.02),
                               emr=clamp(r.gauss(0.6 + d["base"] / 100, 0.12), 0.72, 1.48),
                               deductible_l=r.choice([5, 10, 15, 25])),
                hazards=[],
                hist=deque(maxlen=240),
            ))
            self._spawn_hazards(self.sites[-1], initial=True)

    def _new_claim(self, r, sdef, age_days=5, incident=None):
        sev = r.choices(["LOW", "MODERATE", "HIGH", "CRITICAL"], weights=[18, 42, 30, 10])[0]
        cost_base = {"LOW": (0.8, 3), "MODERATE": (2.5, 12), "HIGH": (10, 45), "CRITICAL": (40, 160)}[sev]
        st = r.choices(CLAIM_STATUS, weights=[18, 30, 22, 18, 12])[0]
        return dict(id=f"CL-{r.randint(2100, 2989)}", site=sdef["id"], site_short=sdef["short"],
                    type=r.choice(CLAIM_TYPES), severity=sev,
                    cost_l=r.uniform(*cost_base), status=st,
                    filed=(now() - timedelta(days=age_days)).isoformat(),
                    surveyor=r.choice(["A. Bhattacharya", "S. Mitra", "R. Sen", "P. Chatterjee", "D. Ghosh"]),
                    confidence=r.uniform(72, 96))

    def _spawn_hazards(self, s, initial=False):
        r = self.rng
        n = r.randint(2, 5) if initial else (1 if r.random() < 0.16 + (s["base"] - 40) / 400 else 0)
        for _ in range(n):
            z = r.choice(s["zones"])
            htype, cat = r.choice(HAZARD_TYPES)
            sev = r.choices(["LOW", "MODERATE", "HIGH", "CRITICAL"],
                            weights=[26, 38, 26, 10])[0]
            s["hazards"].append(dict(
                id=f"HZ-{r.randint(7000, 9799)}", site=s["id"], site_short=s["short"],
                zone=z["name"], type=htype, cat=cat, severity=sev,
                detected_by=r.choice(["Site Risk Agent", "Safety Agent", "Foreman report", "Vision CAM"]),
                age_min=r.uniform(0, 400) if initial else 0, status="OPEN",
                action=r.choice(["Barricade + signage", "Crew rebrief", "Work hold pending fix",
                                 "Isolation requested", "PPE enforcement drive"])))
        s["hazards"] = s["hazards"][:14]

    def _bootstrap_history(self):
        for s in self.sites:
            val = s["base"] + self.rng.uniform(-6, 6)
            t0 = now() - timedelta(minutes=5 * 239)
            for i in range(240):
                hour = (t0 + timedelta(minutes=5 * i)).hour
                diurnal = 9 * ((hour - 6) / 12 - 0.5) ** 2 * 2.4 - 2.5  # busier midday
                val = val * 0.96 + (s["base"] + diurnal) * 0.04 + self.rng.gauss(0, 1.4)
                s["hist"].append(dict(t=(t0 + timedelta(minutes=5 * i)).isoformat(), v=clamp(val, 8, 97)))

    def _seed_alerts(self):
        for s in self.sites[:5]:
            h = next((h for h in s["hazards"] if h["severity"] in ("HIGH", "CRITICAL")), None)
            if h:
                self._make_alert(s["id"], s["short"], h["severity"],
                                 f"{h['type']} detected in {h['zone']}", channels=["EMAIL", "SMS", "SLACK"],
                                 stage=self.rng.randint(2, 4))

    def _make_alert(self, site_id, site_short, severity, title, channels=None, stage=0):
        self.alert_seq += 1
        a = dict(id=f"AL-{self.alert_seq}", ts=now().isoformat(), site=site_id, site_short=site_short,
                 title=title, severity=severity,
                 channels=channels or self.rng.sample(["EMAIL", "SMS", "SLACK"], k=self.rng.randint(1, 3)),
                 stage=stage, ack=stage >= 1,
                 owner=self.rng.choice(["R. Kapoor (PM)", "A. Das (Site Mgr)", "M. Iqbal (HSE)", "S. Roy (Safety Lead)"]),
                 timeline=[(now(), "Detected by agent pipeline", "done")])
        self.alerts.appendleft(a)

    # ------------------------------------------------------------------ scoring
    def band(self, v):
        for hi, name, col in BANDS:
            if v < hi:
                return name, col
        return "CRITICAL", "#ff4d3d"

    def band_name(self, v):
        return self.band(v)[0]

    def subscores(self, s):
        env = s["env"]
        weather = (clamp((env["wind"] - 12) * 3.4, 0, 60) + clamp((env["rain24"] - 5) * 1.3, 0, 30)
                   + clamp((env["aqi"] - 100) * 0.35, 0, 12) + clamp((env["temp"] - 33) * 2.4, 0, 14))
        eq_bad = sum({"WATCH": 0.5, "FAULT": 1.0}.get(e["status"], 0) for e in s["equipment"])
        eq_over = sum(clamp((e["load"] - 80) * 2.2, 0, 14) for e in s["equipment"])
        equipment = clamp(eq_bad * 24 + eq_over, 2, 98)
        hazard = clamp(sum(SEV_WEIGHT[h["severity"]] for h in s["hazards"] if h["status"] == "OPEN") / 3.2, 2, 98)
        behaviour = clamp(100 - (sum(s["ppe"].values()) / 5) * 1.05, 2, 98)
        comp = clamp(sum({"PASS": 0, "RISK": 1, "FAIL": 1.9}.get(c["status"], 0) for c in s["checks"]) * 9
                     + sum(4 for c in s["checks"] if c["due_days"] < 0), 2, 98)
        score = (0.20 * weather + 0.20 * equipment + 0.30 * hazard + 0.14 * behaviour + 0.16 * comp)
        return dict(weather=weather, equipment=equipment, hazards=hazard,
                    behaviour=behaviour, compliance=comp, score=clamp(score, 5, 97))

    def recompute(self):
        for s in self.sites:
            subs = self.subscores(s)
            s["sub"] = subs
            s["score"] = subs["score"]
            bandname, col = self.band(s["score"])
            s["band"], s["band_color"] = bandname, col
            for z in s["zones"]:
                zone_hz = sum(SEV_WEIGHT[h["severity"]] for h in s["hazards"]
                              if h["status"] == "OPEN" and h["zone"] == z["name"])
                zone_ct = sum(1 for h in s["hazards"]
                              if h["status"] == "OPEN" and h["zone"] == z["name"])
                z["risk"] = clamp(z["base"] * 0.55 + zone_hz * 1.1 + (s["score"] - 45) * 0.35
                                  + self.rng.uniform(-2, 2), 3, 97)
                z["hazards"] = zone_ct
            vals = [h["v"] for h in list(s["hist"])[-24:]] or [s["score"]]
            slope = (vals[-1] - vals[0]) / max(len(vals) - 1, 1)
            prob = clamp(0.30 * s["score"] + 9 * slope + 14 + self.rng.gauss(0, 2.5), 4, 93)
            s["prediction"] = dict(prob=prob, slope=slope,
                                   dclass="Elevated" if prob > 55 else ("Watch" if prob > 35 else "Nominal"))
            s["exposure_util"] = self.exposure_util(s)

    def exposure_util(self, s):
        claimed = sum(c["cost_l"] for c in s["claims"]) / 100.0
        return clamp(claimed / max(s["insurance"]["coverage_cr"], 1) * 100, 0, 100)

    def fleet_score(self):
        tw = sum(s["workers"] for s in self.sites)
        return sum(s["score"] * s["workers"] for s in self.sites) / max(tw, 1)

    def open_hazards(self):
        return [h for s in self.sites for h in s["hazards"] if h["status"] == "OPEN"]

    def rand_site(self):
        return self.rng.choice(self.sites)

    # ------------------------------------------------------------------ feed
    def _push_feed(self, n=1):
        from .agents import GENERATORS
        for _ in range(n):
            total = sum(w for w, _ in GENERATORS)
            pick = self.rng.uniform(0, total)
            acc = 0
            for w, fn in GENERATORS:
                acc += w
                if pick <= acc:
                    try:
                        agent, sev, msg = fn(self.rng, self)
                    except Exception:
                        continue
                    self.agent_feed.appendleft(dict(
                        ts=now().isoformat(), agent=agent, severity=sev, msg=msg))
                    st = self.agent_state[agent]
                    st["events"] += self.rng.randint(3, 26)
                    st["last_finding"] = msg
                    break

    # ------------------------------------------------------------------ tick
    def tick(self):
        with self.lock:
            self.ticks += 1
            r = self.rng
            for s in self.sites:
                e = s["env"]
                e["wind"] = clamp(e["wind"] + r.gauss(0, 2.4) + (r.uniform(3, 9) if r.random() < 0.02 else 0), 2, 52)
                e["temp"] = clamp(e["temp"] + r.gauss(0, 0.35), 22, 41)
                e["humidity"] = clamp(e["humidity"] + r.gauss(0, 1.6), 40, 98)
                e["aqi"] = clamp(e["aqi"] + r.gauss(0, 4), 45, 240)
                e["noise"] = clamp(e["noise"] + r.gauss(0, 2.2), 58, 108)
                e["vib"] = clamp(e["vib"] + r.gauss(0, 0.18), 0.2, 5)
                e["rain24"] = clamp(e["rain24"] + r.gauss(0, 2.6) + (r.uniform(6, 18) if r.random() < 0.015 else 0), 0, 120)
                s["workers_now"] = clamp(s["workers_now"] + r.randint(-3, 3), int(s["workers"] * .5), s["workers"])
                for k in s["ppe"]:
                    s["ppe"][k] = clamp(s["ppe"][k] + r.gauss(0, 0.55) + (r.uniform(1, 2.4) if r.random() < 0.05 else 0), 52, 99)
                for eq in s["equipment"]:
                    eq["load"] = clamp(eq["load"] + r.gauss(0, 3.4), 8, 112)
                    eq["temp"] = clamp(eq["temp"] + (eq["load"] - 60) * 0.01 + r.gauss(0, 1.1), 38, 96)
                    eq["vib"] = clamp(eq["vib"] + r.gauss(0, 0.22) + (0.05 if eq["load"] > 95 else 0), 0.6, 7)
                    if r.random() < 0.02:
                        order = ["OK", "WATCH", "FAULT"]
                        i = order.index(eq["status"])
                        if r.random() < 0.65 and i < 2:
                            eq["status"] = order[i + 1]
                            if eq["status"] == "FAULT":
                                self._make_alert(s["id"], s["short"], "HIGH",
                                                 f"{eq['name']} fault — vibration/temperature anomaly",
                                                 channels=["EMAIL", "SLACK"], stage=1)
                        elif i > 0 and r.random() < 0.5:
                            eq["status"] = order[i - 1]
                # hazards lifecycle
                for h in s["hazards"]:
                    h["age_min"] += TICK_SECONDS / 60 * 12  # sim-accelerated age
                    if h["status"] == "OPEN" and r.random() < 0.10:
                        h["status"] = "MITIGATION"
                    elif h["status"] == "MITIGATION" and r.random() < 0.06:
                        h["status"] = "RESOLVED"
                s["hazards"] = [h for h in s["hazards"] if h["status"] != "RESOLVED" or r.random() < .8][-14:]
                self._spawn_hazards(s)
                new_crit = [h for h in s["hazards"] if h["status"] == "OPEN" and h["severity"] == "CRITICAL" and h["age_min"] < 0.4]
                for h in new_crit:
                    self._make_alert(s["id"], s["short"], "CRITICAL",
                                     f"{h['type']} in {h['zone']} — immediate action required",
                                     channels=["EMAIL", "SMS", "SLACK"], stage=0)
                # compliance drift
                for c in s["checks"]:
                    c["due_days"] -= 1 / (86400 / TICK_SECONDS) * 60  # slow drift
                    if r.random() < 0.004:
                        c["status"] = r.choices(["PASS", "RISK", "FAIL"], weights=[70, 22, 8])[0]
                # claims progression
                for c in s["claims"]:
                    if r.random() < 0.02:
                        i = CLAIM_STATUS.index(c["status"])
                        if i < len(CLAIM_STATUS) - 1:
                            c["status"] = CLAIM_STATUS[i + 1]
                if r.random() < 0.006 and len(s["claims"]) < 6:
                    s["claims"].append(self._new_claim(r, s, age_days=0))
                    self._make_alert(s["id"], s["short"], "MODERATE",
                                     f"New insurance claim filed — {s['claims'][-1]['type']}",
                                     channels=["EMAIL"], stage=1)
            # advance alerts workflow
            for a in list(self.alerts):
                if a["stage"] < 4 and self.rng.random() < 0.05:
                    a["stage"] += 1
                    a["timeline"].append((now(), self._stage_label(a["stage"]), "done"))
                    if a["stage"] == 4:
                        a["resolved_ts"] = now().isoformat()
            # agent states
            for k, st in self.agent_state.items():
                st["latency"] = clamp(st["latency"] + self.rng.gauss(0, 6), 28, 320)
                st["confidence"] = clamp(st["confidence"] + self.rng.gauss(0, 0.3), 84, 98.5)
                st["status"] = self._agent_status(k)
            self.recompute()
            self._push_feed(self.rng.randint(1, 3))
            # histories
            fleet = self.fleet_score()
            for s in self.sites:
                s["hist"].append(dict(t=now().isoformat(), v=s["score"]))
            self.ticker_items = self._build_ticker()
            if self.ticks % 96 == 0:
                for pt in self.patterns:
                    pt["occurrences"] += self.rng.randint(0, 2)

    def _agent_status(self, key):
        crit = any(h["severity"] == "CRITICAL" and h["status"] == "OPEN"
                   for s in self.sites for h in s["hazards"])
        if key == "engine":
            return "ORCHESTRATING"
        if crit and key in ("site_risk", "safety", "compliance"):
            return "ALERT"
        return "ANALYSING" if self.rng.random() < 0.85 else "SYNTHESISING"

    def _stage_label(self, stage):
        return ["Detected by agent pipeline", "Triaged & risk-scored", "Escalated to site management",
                "Corrective action assigned", "Resolved & verified"][stage]

    def _build_ticker(self):
        items = []
        for a in list(self.alerts)[:8]:
            items.append(f"{a['severity']} · {a['site_short']} — {a['title']}")
        top = sorted(self.sites, key=lambda s: -s["score"])[:3]
        for s in top:
            _, col = self.band(s["score"])
            items.append(f"{s['short']} risk index {s['score']:.0f} ({s['band']}) · {s['city']}")
        w = self.sites[0]["env"]
        items.append(f"Kolkata weather · wind {w['wind']:.0f} km/h · AQI {w['aqi']:.0f} · rain {w['rain24']:.0f} mm/24h")
        return items

    def run_cycle(self):
        """Force a full agent analysis cycle — used by the 'Run cycle' button."""
        with self.lock:
            for s in self.sites:
                self.recompute()
            self._push_feed(7)
            self.agent_state["engine"]["events"] += 42
            self.agent_state["engine"]["task"] = "Full analysis cycle completed"
            self.ticker_items = self._build_ticker()
            return dict(cycle_id=f"C-{self.ticks:06d}",
                        sites_analysed=len(self.sites),
                        hazards_reviewed=len(self.open_hazards()),
                        checks_validated=sum(len(s["checks"]) for s in self.sites),
                        reports_staged=5)


# ------------------------------------------------------------------ singleton
SIM = None
_TTHREAD = None


def get_sim():
    global SIM, _TTHREAD
    if SIM is None:
        SIM = Simulator()
        SIM.tick()
        def loop():
            while True:
                time.sleep(TICK_SECONDS)
                try:
                    SIM.tick()
                except Exception as e:  # keep the sim alive no matter what
                    print("tick error:", e)
        _TTHREAD = threading.Thread(target=loop, daemon=True)
        _TTHREAD.start()
    return SIM
