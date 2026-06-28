# DXC POC — Airport Queue Management System

## Project context
- **Client:** DXC Technology (Proof of Concept)
- **Output folder:** `projects/dxc-poc/`
- **Goal:** Demonstrate AI-powered airport queue management with real and simulated data,
  covering every plausible AI use-case, built to impress a DXC audience and drive a
  full engagement.

---

## Problem statement
Airport security and check-in queues are unpredictable and under-managed. Passengers
miss flights; airports waste staff. This POC shows how AI can predict, monitor, and
optimise queues across every airport workflow — from kerb to gate.

---

## Datasets to use (primary)

### 1. TSA FOIA Throughput Dataset (REAL DATA — preferred)
- **What:** TSA passenger throughput per checkpoint, per hour, for ~5 major US airports,
  2020–2022. Obtained via Freedom of Information Act.
- **Source:** https://www.tsa.gov/foia/readingroom or community re-posts on GitHub/Kaggle.
  Search GitHub for "TSA throughput FOIA" and Kaggle for "TSA checkpoint throughput".
- **Use:** Real wait-time and throughput signals; lane-level queue modelling;
  COVID recovery trend analysis; capacity planning.

### 2. Kaggle Airport Operations Dataset (SIMULATED — secondary)
- **What:** Simulated airport operations data including passenger flows, gate assignments,
  delays, staffing levels.
- **Search:** https://www.kaggle.com/search?q=airport+operations+queue
- **Use:** Fill gaps where real data is thin (e.g. check-in, baggage, immigration);
  stress-test models with synthetic edge cases.

### 3. Additional sources to discover during research
- BTS (Bureau of Transportation Statistics) on-time data: https://www.transtats.bts.gov/
- OpenSky Network / FlightAware ADS-B feeds (flight schedule context).
- Any airport authority open data portals.
- FAA ASPM (Aviation System Performance Metrics).

---

## AI use-cases to cover (researcher must enumerate ALL plausible ones)

Organise findings under these categories — discover sub-cases within each:

### A. Queue Prediction & Wait-time Forecasting
- Short-term (next 15–60 min) wait-time forecast per checkpoint/lane
- Day-of-week and time-of-day demand prediction
- Event-driven surge prediction (holidays, large events, flight bunching)
- COVID / health-policy impact modelling

### B. Staffing & Lane Optimisation
- Optimal lane open/close scheduling (minimise cost, maximise throughput)
- Staff allocation recommendations (TSA officers per lane per shift)
- Pre-TSA PreCheck vs standard lane balancing

### C. Anomaly & Incident Detection
- Real-time queue spike detection (something broke / slow officer)
- Unusual throughput drop (equipment failure, medical incident)
- Comparative anomaly across airports (systemic vs local)

### D. Passenger Flow & Routing
- Dynamic signage / passenger re-routing to shorter queues
- Gate-to-security reverse flow (risk of missing flight)
- Connecting-passenger risk scoring

### E. Capacity Planning & Scenario Modelling
- Long-term capacity demand forecasting (new terminal, airline changes)
- "What-if" scenario simulation (add a lane, change PreCheck ratio)
- Infrastructure investment ROI modelling

### F. Dashboard & Alerting
- Real-time operational dashboard (today's queues, predicted vs actual)
- Management dashboard (KPIs: avg wait, throughput, SLA breach rate)
- Predictive alert system (queue will exceed X min in Y minutes)
- Historical analytics & benchmarking across airports

---

## Open-source repos & prior art to find

Researcher must search GitHub and other sources for:
1. Airport / TSA queue simulation or prediction repos
2. General queue prediction / time-series forecasting stacks that fit
3. Dashboard frameworks used in airport/transport ops
4. Any FOIA TSA dataset loaders or notebooks already published

For each repo found, assess: license, last commit date, stars, fit, integration effort.

---

## Target deliverables for the POC

1. **Data pipeline** — ingest TSA FOIA + Kaggle data, normalise to a common schema
2. **ML models** — at minimum: wait-time forecasting, anomaly detection, staffing optimiser
3. **REST API** — serve predictions and current queue state
4. **Dashboard UI** — real-time + historical + predictive, multi-airport view
5. **Demo script** — a walk-through of every AI use-case for a DXC audience

---

## Constraints & preferences
- **Stack:** Python backend preferred; React or similar for UI; PostgreSQL or DuckDB for
  storage (lightweight for POC).
- **Hosting:** Local / Docker for the demo; cloud-ready architecture.
- **Timeline:** POC, not production — prioritise impressiveness and completeness of
  use-case coverage over production hardening.
- **License:** All dependencies must be open-source (MIT, Apache 2, BSD).

---

## Success criteria
A DXC stakeholder can:
1. See real TSA data flowing through the system.
2. Get a predicted wait-time for the next hour at each checkpoint.
3. See an anomaly flagged when queue spikes.
4. Simulate "what happens if I open an extra lane."
5. View all insights on a single dashboard.
