# Architecture Decision Log — DXC Airport Queue Management AI POC

> **STATUS: FROZEN — 2026-06-28.** All four specialists (data-engineer,
> backend-engineer, ui-engineer, test-engineer) build against this sheet and the
> three contracts it references. Do **not** silently overwrite a frozen row —
> append a dated entry under "Change history" instead.
>
> **Companion contracts (also frozen):**
> - Data contract: `projects/dxc-poc/architecture/data-contract.md`
> - API contract:  `projects/dxc-poc/architecture/api-contract.md`
> - UI spec:       `projects/dxc-poc/architecture/ui-spec.md`

## Status
**ACTIVE PROJECT: DXC Airport Queue Management POC.** Architecture frozen.
Specialists may start: data-engineer first, then backend-engineer + ui-engineer
in parallel, then test-engineer.

---

## Resolved: Architect answers to the 6 open questions

| # | Open question | Decision |
|---|---------------|----------|
| Q1 | Demo data mode: simulated live feed vs batch replay? | **Batch replay driven by a virtual "demo clock."** A configurable `DEMO_NOW` timestamp walks across the historical TSA window; "current" = the slice at `DEMO_NOW`. Gives a live feel with zero streaming infra. See D1, D7. |
| Q2 | Granularity: airport-level daily vs checkpoint-level hourly? | **Both.** Real TSA data is loaded at airport-daily (ground truth). A deterministic **hourly + checkpoint disaggregation profile** synthesises checkpoint-hour rows from the daily total, so the dashboard can show checkpoint-level hourly without PDF extraction. See D2, D3. |
| Q3 | Staffing optimiser: ILP or heuristic? | **Heuristic rule engine + SimPy validation for V1.** No ILP/OR-Tools. Demand forecast → required-lanes formula (M/M/c wait target) → SimPy confirms the wait SLA. Keeps deps light, explainable in a demo. See D4-B, D7. |
| Q4 | Multi-airport map as hero view? | **Yes — Plotly `scatter_geo`** (not Folium) on Page 1. One less JS dep, renders natively in Streamlit, colour-coded by SLA status. See D6. |
| Q5 | Alert delivery: in-dashboard only or email/Slack? | **In-dashboard only.** Threshold-based alerts computed server-side, surfaced as Streamlit banners/badges. No SMTP/Slack — out of POC scope. See D8. |
| Q6 | Docker vs local? | **Docker Compose is the demo target** (`docker compose up`), but every service also runs bare via `uv`/`pip` for dev. See D9. |

---

## Decision sheet (FROZEN)

### D1 — Overall system approach
**Choice:** A single-repo, three-service analytics POC that ingests **real TSA
throughput data + simulated Kaggle airport-ops data** into DuckDB, runs a **suite
of ML models** (forecasting, anomaly detection, staffing optimisation, what-if
simulation) behind a **FastAPI** service, and presents everything through a
**6-page Streamlit dashboard**. The POC demonstrates, end-to-end, the five DXC
success criteria: real data flowing, next-hour wait forecast, live anomaly flag,
"add-a-lane" what-if, all on one dashboard.

The "live" experience is produced by a **virtual demo clock** (`DEMO_NOW`) that
replays historical data as if it were happening now — no streaming infrastructure.

**Rejected alternatives:**
- *Real-time streaming ingest (Kafka/socket feed):* no real live TSA feed exists;
  building one is theatre that adds infra risk with no analytical value.
- *Notebook-only deliverable:* not demoable as a "system"; fails the
  single-dashboard success criterion.

**Rationale:** Maximise use-case coverage and demo legibility per the briefing's
"risk is integration breadth, not technical depth." Three clean services keep the
four specialists from colliding.

**Assumptions:** Audience is DXC stakeholders evaluating capability, not a
production load test. Single-node, single-user demo.

---

### D2 — Data sources + ingestion strategy
**Choice:** Two primary sources, ingested by a **plain Python + Pandas + DuckDB
ETL** (`projects/dxc-poc/data/`), no orchestrator.

1. **TSA FOIA throughput (REAL, primary):** clone `mikelor/TsaThroughput-Data`
   (Apache-2.0) processed CSVs; fall back to the ERAU enriched CSV
   (CC BY 4.0) for mobility/COVID regressors. Airports **ATL, DEN, ORD, LAX,
   DFW**, daily, ~2020-02-15 → 2022-10-15. Loaded to `tsa_throughput`.
2. **Kaggle Airport Operations Multi-Table (SIMULATED, secondary):** check-in,
   baggage, gate, workforce-shift tables → normalised into `airport_ops`. Fills
   queue areas TSA data does not cover (CHECKIN, BAGGAGE, GATE).

**Derived/transform step (the "disaggregation profile"):** a deterministic,
documented transform converts each airport-daily `pax` total into
**checkpoint × hour** rows using a fixed intraday curve (TSA-typical bimodal
05:00-08:00 / 16:00-19:00 peaks) and a per-airport checkpoint split. This
populates the hourly view consumed by forecasting/anomaly models. The profile
constants live in `data-contract.md` so output is reproducible and testable.

**Wait-time derivation:** TSA data is throughput, not wait time. Wait time is
derived via an **M/M/c approximation** from throughput (arrival rate λ), lane
count (servers c), and a fixed per-lane service rate μ. Constants in
`data-contract.md`. This is stated openly in the demo as a modelled estimate.

**Rejected alternatives:**
- *PDF→hourly extraction (mikelor pipeline) as V1 source:* slow, brittle; the
  disaggregation profile gives the same demo value deterministically.
- *Airflow/Dagster ETL:* explicitly out of scope; overkill at POC scale.

**Rationale:** Real data leads (credibility); simulation fills gaps; a documented
deterministic transform gives hourly/checkpoint granularity without scraping PDFs.

**Risks:** ⚠️ Derived wait times are modelled, not measured — must be labelled as
such in UI and demo script (D11). ⚠️ Kaggle schema may drift; data-engineer pins
the downloaded snapshot into `projects/dxc-poc/data/raw/` and commits a checksum.

**Assumptions:** Datasets downloadable at build time; raw files cached in-repo so
the build is reproducible offline.

---

### D3 — Storage + schema
**Choice:** **DuckDB**, single file `projects/dxc-poc/data/airport.duckdb`.
In-process, zero server, reads CSV/Parquet directly. Five canonical tables, fully
specified in `data-contract.md`:

| Table | Purpose | Grain |
|-------|---------|-------|
| `tsa_throughput` | Real TSA pax + regressors | airport × date (+ derived checkpoint × hour rows) |
| `airport_ops` | Simulated check-in/baggage/gate/staffing | airport × area × timestamp |
| `queue_predictions` | Model forecast output | airport × checkpoint × horizon_minute × model |
| `anomaly_events` | Detected anomalies | event row |
| `staffing_recommendations` | Optimiser output | airport × date × hour × checkpoint |

Two enums are frozen in `data-contract.md`: **airport codes**
(ATL, DEN, ORD, LAX, DFW) and **queue area types** (SECURITY_TSA,
SECURITY_PRECHECK, CHECKIN, GATE, BAGGAGE).

**Rejected alternatives:**
- *PostgreSQL/TimescaleDB:* needs a server + container + tuning; no real-time
  write throughput requirement at POC scale (briefing §5).
- *SQLite:* no columnar analytics; weak for the aggregation/window queries the
  KPI page needs.

**Rationale:** DuckDB is the briefing's chosen store; single-file DB is trivial to
ship in the `data` service and mount read-only into `api`.

**Risks:** ⚠️ Concurrent write from ETL while API reads — mitigated by the build
order (ETL fully populates the file before `api` starts; API opens read-only).

**Assumptions:** DB regenerated by the ETL, never hand-edited. It is a build
artifact, not committed.

---

### D4 — ML model suite
**Choice:** One model module per family under
`projects/dxc-poc/backend/models/`, each exposing `train()` / `predict()` and
persisting fitted models to `projects/dxc-poc/backend/models/store/*.pkl`
(joblib). No MLflow server — flat file store, loaded once at API startup.

**D4-A Forecasting** (use-cases A1-A5):
- **Prophet** — daily/weekly seasonality + COVID & mobility regressors (A2-A4).
  Default model for the demo.
- **Darts** (`NBEATSModel` + `RNNModel`/LSTM) — short-horizon hourly wait (A1),
  multi-airport (A5). Exposed via the model selector (UI Page 2).
- Library: `darts`, `prophet`. One forecast row-set per `(airport, checkpoint,
  model)` written to `queue_predictions`.

**D4-B Staffing optimiser** (use-cases B1-B4): **heuristic rule engine**, not ILP.
For each forecast hour: required lanes `c` = smallest c such that M/M/c expected
wait ≤ SLA target (default 10 min), bounded by physical lane cap per checkpoint.
PreCheck balance via fixed ratio rule. Output → `staffing_recommendations`.
SimPy (D7) validates the recommendation's wait outcome.

**D4-C Anomaly detection** (use-cases C1-C4):
- **PyOD** `ECOD` + `IForest` — batch throughput-drop / cross-airport anomalies
  (C2, C3).
- **River** `HalfSpaceTrees` (or online z-score) — streaming spike detection over
  the demo-clock window (C1).
- **STL** residual threshold (statsmodels) — seasonal "weird day" (C4).
- All detections written to `anomaly_events` with `detector`, `severity`, `score`.

**Libraries (all MIT/Apache/BSD):** `darts`, `prophet`, `pyod`, `river`,
`statsmodels`, `scikit-learn`, `simpy`, `joblib`.

**Rejected alternatives:**
- *ILP staffing (PuLP/OR-Tools):* heavier dep, harder to explain live; heuristic +
  SimPy validation is more demo-legible (Q3).
- *Deep multivariate-only forecasting:* slower to train, less interpretable than
  Prophet for the headline demo.
- *MLflow model registry:* server overhead unjustified for a handful of pickles.

**Rationale:** Covers every briefing use-case family with the exact libraries the
research prescribed; flat pickle store keeps serving trivial.

**Risks:** ⚠️ Darts/Prophet train time can dominate the build — models are trained
**once at ETL/seed time**, persisted, and only loaded by the API. ⚠️ Sparse
hourly data per checkpoint — forecasting falls back to airport-level when a
checkpoint series is too short (documented in model module).

**Assumptions:** Training is offline/batch; API never trains on request.

---

### D5 — Backend / API
**Choice:** **FastAPI** (`projects/dxc-poc/backend/`), Uvicorn, auto-OpenAPI at
`/docs` (a demo asset). Reads DuckDB read-only + loads model pickles at startup.
Full request/response shapes in `api-contract.md`. Endpoint surface:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness + model/DB load status |
| GET | `/airports` | All 5 airports + current SLA status |
| GET | `/queues/current` | Current queue state per airport/checkpoint (at `DEMO_NOW`) |
| GET | `/queues/forecast` | Predicted wait next N min (`airport`, `horizon`, `model`) |
| GET | `/anomalies/recent` | Recent anomaly events (`airport`, `hours`) |
| GET | `/staffing/recommend` | Staffing recommendation (`airport`, `date`) |
| POST | `/simulate/what-if` | Lane/PreCheck scenario simulation (SimPy) |
| GET | `/dashboard/kpis` | Aggregated KPIs (`airport`, `date_from`, `date_to`) |
| GET | `/models` | Available forecast models for the selector |
| GET | `/config/clock` | Current `DEMO_NOW` (and POST to advance it) |

Top-5 request/response shapes are specified in `api-contract.md` §Top-5.

**Rejected alternatives:**
- *Flask:* no built-in async or auto OpenAPI; the `/docs` page is a deliberate
  demo asset (constraint).
- *GraphQL:* over-engineered for fixed dashboard queries.

**Rationale:** FastAPI is the mandated framework; typed Pydantic models double as
the contract the UI builds against.

**Risks:** ⚠️ Model load at startup adds boot latency — acceptable for a single
demo container; healthcheck gates readiness.

**Assumptions:** Single worker, single user. No auth (POC, local network).

---

### D6 — UI / Dashboard
**Choice:** **Streamlit** multipage app (`projects/dxc-poc/ui/`), one file per
page under `ui/pages/`, all data via the FastAPI endpoints (never touches DuckDB
directly). Charts: **Plotly** (incl. `scatter_geo` map). Six pages, fully
specified in `ui-spec.md`:

1. Real-Time Operations Dashboard (map hero, live queue state, next-60-min, alerts)
2. Forecast & Prediction (multi-airport forecast chart + model selector)
3. Anomaly Detection (timeline, type breakdown, cross-airport compare)
4. Staffing Optimiser (date/airport/constraints in → schedule out)
5. What-If Simulator (lane slider + PreCheck ratio → simulated outcome)
6. Historical Analytics & KPIs (date range + airport filter → KPI cards + trends)

**Rejected alternatives:**
- *Grafana / Superset:* weak Python/ML integration; can't host the what-if SimPy
  call or model selector inline (briefing §5).
- *React SPA:* far more build effort; Streamlit gives a running UI fastest, which
  is the POC priority.
- *Folium for the map:* Plotly `scatter_geo` avoids an extra JS dep and themes
  consistently with the other charts (Q4).

**Rationale:** Streamlit is mandated and gives the tightest ML/chart integration
for a single-sprint demo.

**Risks:** ⚠️ Streamlit reruns whole script on interaction — heavy calls are
`@st.cache_data`'d against API responses with a short TTL.

**Assumptions:** UI is read-only over the API except the what-if POST and clock
advance.

---

### D7 — Simulation engine
**Choice:** **SimPy** discrete-event model (`backend/sim/checkpoint_sim.py`),
adapted from `aschatz1995/Airport-Security-Wait-Sim`. Models a checkpoint as
`c` lane resources with stochastic (exponential) service; passenger arrivals from
the forecast/observed arrival rate λ. Exposed two ways:

1. **What-if API** (`POST /simulate/what-if`): caller supplies airport,
   checkpoint, base arrival rate (or "use current"), `num_lanes`,
   `precheck_ratio`, `service_rate`, `duration_min`. Returns mean/p95 wait,
   max queue length, lane utilisation, SLA-breach minutes — for baseline vs
   scenario.
2. **Staffing validation** (internal): confirms the D4-B heuristic's recommended
   lane count actually meets the wait SLA before it's written.

Scenarios exposed: **add/remove lanes**, **change PreCheck ratio**, **change
arrival surge multiplier**, **change service rate**.

**Rejected alternatives:**
- *Closed-form M/M/c only (no DES):* used for the fast heuristic, but a live
  what-if simulation is more convincing and handles non-Poisson surges.
- *Importing the Java MOSIP sim:* language mismatch; SimPy stays in-process.

**Rationale:** SimPy is mandated; one engine serves both the interactive what-if
page and offline staffing validation.

**Risks:** ⚠️ Long `duration_min` × many lanes can be slow — API caps
`duration_min ≤ 240` and `num_lanes ≤ 20`, runs synchronously with a timeout.

**Assumptions:** Service-time distribution is exponential with a documented
default μ; surfaced as an editable parameter.

---

### D8 — Alerting
**Choice:** **In-dashboard threshold alerts only.** Alert rules are evaluated
server-side in an `/alerts`-style helper baked into `/queues/current` and
`/queues/forecast` responses (each queue carries `sla_status` ∈
`OK | WARNING | BREACH` and a `predicted_breach_in_min`). The UI renders these as
coloured banners/badges on Page 1. Thresholds are **config-driven**
(`backend/config.py`): default WARNING ≥ 8 min, BREACH ≥ 10 min wait; anomaly
severity HIGH always raises a banner.

**Rejected alternatives:**
- *Email/Slack/SMS delivery:* needs external creds/infra; no value in a local
  demo (Q5).
- *Separate alert microservice:* unnecessary; thresholds are pure functions of
  already-served data.

**Rationale:** Satisfies success criterion #3 ("see an anomaly flagged when queue
spikes") with zero external dependencies.

**Risks:** ⚠️ None material. Thresholds are demo-tunable in one config file.

**Assumptions:** SLA target = "95% cleared < 10 min" (briefing vocabulary).

---

### D9 — Containerisation
**Choice:** **Docker Compose**, three services + a shared volume:

| Service | Image base | Command | Port | Depends on |
|---------|-----------|---------|------|------------|
| `data` | python:3.12-slim | runs ETL + model training, writes `airport.duckdb`, then exits (`restart: "no"`) | — | — |
| `api` | python:3.12-slim | `uvicorn app:app --host 0.0.0.0 --port 8000` | **8000** | `data` (service_completed_successfully) |
| `dashboard` | python:3.12-slim | `streamlit run Home.py --server.port 8501` | **8501** | `api` (healthy) |

Shared named volume `airportdata` mounts `projects/dxc-poc/data/` so `data`
writes the DuckDB file and `api` reads it. `api` is gated on `data` completing;
`dashboard` is gated on `api` healthcheck (`GET /health`). One
`docker compose up` brings the whole demo up; dashboard at
`http://localhost:8501`, API docs at `http://localhost:8000/docs`.

**Rejected alternatives:**
- *Single mega-container:* couples build/serve lifecycles; can't gate API on data
  readiness cleanly.
- *Kubernetes:* absurd for a local POC.

**Rationale:** Mirrors the briefing's named-service intent (`api`, `dashboard`,
`data`) and gives a one-command demo (Q6).

**Risks:** ⚠️ First `up` is slow (model training in `data`). Mitigated: trained
pickles + DuckDB persist on the volume, so subsequent `up`s skip retraining
(idempotent seed checks for existing artifacts).

**Assumptions:** Docker Desktop available on the demo machine; ports 8000/8501
free.

---

### D10 — Testing scope
**Choice:** **pytest** (`projects/dxc-poc/tests/`). The test-engineer verifies:

1. **Data contract** — every table in `data-contract.md` exists with the exact
   columns/types; enum columns contain only allowed values; row counts > 0;
   no null in declared NOT-NULL columns.
2. **ETL determinism** — disaggregation profile reproduces identical
   checkpoint-hour totals from the same daily input; hourly sums reconcile to the
   daily `pax` (± rounding).
3. **API contract** — each endpoint in `api-contract.md` returns HTTP 200 and a
   payload matching the documented JSON shape (field names + types); bad params
   return 4xx; `/health` reports DB + models loaded.
4. **Model sanity** — forecast returns the requested horizon length, monotone
   timestamps, non-negative waits; anomaly detector flags an injected synthetic
   spike; staffing rec lane count is within physical caps.
5. **Simulation sanity** — more lanes ⇒ non-increasing mean wait; higher arrival
   surge ⇒ non-decreasing wait (monotonicity checks, not exact values).
6. **Smoke / integration** — `docker compose up` reaches all healthchecks;
   dashboard pages load without exception against a live API.

Out of scope: load/perf testing, security testing, exhaustive numerical accuracy.

**Rejected alternatives:**
- *Full numerical-accuracy validation of forecasts:* not meaningful on a POC with
  modelled wait times; sanity + monotonicity is the right bar.

**Rationale:** Protects the two frozen contracts (the collision surface between
specialists) and proves the five success criteria run.

**Assumptions:** Tests run against the seeded DuckDB + a live API process.

---

### D11 — Demo script structure
**Choice:** A linear DXC walk-through (`projects/dxc-poc/docs/demo-script.md`,
authored by doc-writer) mapped to the 6 UI pages and the 5 success criteria:

1. **Open on Page 1 (Real-Time Ops):** map of 5 airports colour-coded by SLA;
   point to **real TSA data** flowing (criterion #1). Advance the **demo clock**
   to show queues update.
2. **Next-hour forecast (Page 2):** pick ATL security, show **predicted wait next
   60 min**, switch model in the selector (criterion #2).
3. **Anomaly flag (Page 3 + Page 1 banner):** advance clock to a seeded spike;
   show the **anomaly banner + timeline** (criterion #3).
4. **What-if (Page 5):** drag the lane slider from 4→6, change PreCheck ratio;
   show **simulated wait drop** baseline-vs-scenario (criterion #4).
5. **Staffing (Page 4):** show the recommended lane schedule for the surge day.
6. **KPIs (Page 6):** date-range KPIs across airports — avg wait, throughput, SLA
   breach rate — the management view (criterion #5: all on one dashboard).
7. **Close on `/docs`:** show the live OpenAPI as proof of a real, callable API.

**Rejected alternatives:**
- *Feature-by-feature tour with no narrative:* less persuasive than a
  criterion-driven story.

**Rationale:** Ties every click to a success criterion so the value lands with a
non-technical DXC audience.

**Assumptions:** Demo runs from the seeded DB with a pre-chosen `DEMO_NOW` near a
known surge/anomaly so the story is repeatable.

---

## Cross-cutting standards (binding on all specialists)
- **Language/runtime:** Python 3.12.
- **Dependency licenses:** MIT / Apache-2.0 / BSD only. No GPL deps shipped
  (junzis/atdelay is GPL — *reference only, do not import*).
- **Layout:** data → `projects/dxc-poc/data/`, backend+models+sim →
  `backend/`, UI → `ui/`, tests → `tests/`, docs → `docs/`.
- **Contracts are law:** if code and a contract disagree, the contract wins.
  Contract changes are append-only with a dated change-history entry.
- **DuckDB file** `projects/dxc-poc/data/airport.duckdb` is a build artifact
  (git-ignored); raw source snapshots in `data/raw/` are committed with checksums.
- **No secrets, no auth, no external network at serve time** (all data local).

---

## Change history
_Append dated entries here when a frozen decision changes._
_Format: `### YYYY-MM-DD — <what changed and why>`_

### 2026-06-28 — Initial freeze
Architecture frozen for the DXC Airport Queue Management POC: D1-D11 plus the
data/API/UI contracts. Resolved all 6 open questions from the research briefing
(batch-replay demo clock; dual daily+disaggregated-hourly granularity; heuristic
staffing + SimPy validation; Plotly map; in-dashboard alerts; Docker Compose
target). Specialists cleared to start.
