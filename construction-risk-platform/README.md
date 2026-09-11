# 🦺 SiteSentinel AI — Agentic Construction Risk Intelligence Platform

A complete Flask implementation of the *Agentic AI for Safety Monitoring with Construction Risk Analytics* spec — with a **live simulation engine** that generates realistic real-time construction data (no external data sources needed) and a **"Site Works" field-ops interface** (asphalt panels, hazard tape, stencil numerals, survey-mark diamonds, drawing title blocks) built entirely with dependency-free HTML/CSS/JS.

## 🚀 Run it

```bash
cd construction-risk-platform
pip install flask
python3 app.py
# → open http://localhost:5000
```

The simulation boots instantly, seeds ~20 minutes of history, and a background thread
advances the world every **5 seconds** (weather drift, equipment faults, hazard lifecycle,
claim progression, alert escalation, agent findings).

## 🤖 The agent system (as per spec)

| Module | Where it lives | What it does in the app |
|---|---|---|
| **Site Risk Agent** | `engine/agents.py` + zone map | Zone scans, wind/rain thresholds, equipment telemetry (load/temp/vibration), site risk scoring |
| **Safety Agent** | Safety dashboard | PPE vision detections (helmets, vests, harness), unsafe-behaviour coaching, accident-prone zone heat ranking |
| **Compliance Agent** | Compliance dashboard | BOCW 1996 / NBC 2016 / IS / CEA / CPCB checks, permits, overdue inspections, failing audits |
| **Insurance Agent** | Insurance dashboard | EMR scoring, claim register & severity mix, exposure utilisation, claim documentation packs |
| **Reporting Agent** | Reports page | 5 report types composed live from sim state: Executive Summary, Daily Site Report, Compliance Audit Pack, Project Health, Insurance Claim Packet |
| **Risk Intelligence Engine** | `engine/simulator.py` | Orchestrates everything: weighted risk model (weather/equipment/hazards/behaviour/compliance), 24h incident prediction, pattern mining, recommendations |

## 🖥 Pages

1. **Risk Command Center** — fleet gauge, live risk pulse + engine forecast, AI incident forecasts, site leaderboard, agent activity feed, risk radar, patterns, recommendations
2. **Sites** — 8 site cards (Kolkata-region projects) with rings, sparklines, env pills
3. **Site Detail** — interactive **live zone map** (click zones, animated hazard pins, swaying crane), factor breakdown, environmental telemetry, equipment table, hazard queue
4. **Safety Intelligence** — PPE donut, live CAM violation stream, hottest zones matrix, incident register
5. **Compliance** — standards register with filters, inspection radar, status donut, per-site rates
6. **Insurance** — claims register, severity mix, EMR-weighted site risk, cost outflow, doc packs
7. **AI Agents** — animated orchestration topology, per-agent vitals, searchable activity log, "run full cycle" button
8. **Reports** — report kind picker + print-ready paper view (Print → PDF)
9. **Alerts & Workflow** — 5-stage escalation pipeline, channel fan-out (Email/SMS/Slack), workflow replay modal, acknowledge action
10. **Global** — notification drawer (bell), live site-feed ticker, IST clock, toast system

## 🛠 Tech

- **Backend:** Python + Flask, threaded simulation singleton (`engine/simulator.py`), snapshot builders (`engine/payloads.py`), feed generators (`engine/agents.py`)
- **Frontend:** Jinja2 templates, one custom CSS design system (construction-site theme: cut-corner tags, hazard-tape strips, corner-bracket panels, engineering title block, stamped report paper), **zero JS libraries** — charts (line, gauge, ring, donut, bars, radar, sparkline), zone map, orchestration diagram and icons are all hand-rolled SVG
- **Live updates:** every page polls its JSON API (4–8 s); tick loop mutates state under a lock and readers get consistent snapshots

## 🔌 API

`/api/overview` · `/api/sites` · `/api/sites/<id>` · `/api/safety` · `/api/compliance` · `/api/insurance` · `/api/agents` · `POST /api/agents/run` · `/api/alerts` · `POST /api/alerts/<id>/ack` · `/api/ticker` · `/api/report?doc=daily&site=SITE-101`

## ⚠️ Data

All data is **randomly generated to replicate real-time behaviour** — plausible site names, Indian regulatory references (BOCW Act, NBC 2016, IS codes), ₹-denominated insurance values and realistic diurnal risk patterns. Refreshing restarts the world with a fresh random state.
