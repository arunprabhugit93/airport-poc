# Project status

> Update this at the END of every session. It's how the next session knows
> where to pick up. Keep it short and current.

## Current state
- **ACTIVE PROJECT: DXC Airport Queue Management POC**
- Project lives in `projects/dxc-poc/`
- Requirements written: `requirements/dxc-poc-queue-management.md`
- **Research COMPLETE:** `projects/dxc-poc/research/domain-briefing.md`
- Agents linked: `.claude/agents → agents/`
- **ARCHITECTURE FROZEN (2026-06-28).** Decisions D1-D11 in
  `decisions/decision-log.md`. Three contracts frozen under
  `projects/dxc-poc/architecture/`: `data-contract.md`, `api-contract.md`,
  `ui-spec.md`. All 6 open questions resolved by the Architect.
- **DATA LAYER COMPLETE:** `projects/dxc-poc/data/airport.duckdb` now builds
  end-to-end via `python -m data.etl.run_etl` and contains full-history
  `tsa_throughput`, `airport_ops`, `queue_predictions`, `anomaly_events`, and
  `staffing_recommendations`.
- **BACKEND SLICE COMPLETE:** FastAPI app implemented at
  `projects/dxc-poc/backend/app.py`; `Dockerfile.api` added; smoke tests pass in
  `projects/dxc-poc/tests/test_api.py`.

## Next actions (specialists may start)
1. **ui-engineer** → build the 6-page Streamlit dashboard per
   `projects/dxc-poc/architecture/ui-spec.md`, wired only to the FastAPI
   endpoints.
2. **test-engineer** → expand beyond the current API smoke suite to cover ETL
   contract invariants, KPI correctness, and simulation sanity (D10).
3. **doc-writer** → README + `docs/demo-script.md` (D11), including the local
   run flow now that `Dockerfile.api` and the backend contract are real.
4. Optional backend follow-up → add `Dockerfile.ui`, richer endpoint tests, and
   decide whether `pyod` remains an optional local dependency or gets a pinned
   install path documented for full anomaly-model coverage.

## Architect decisions on the 6 open questions (now closed)
1. Demo data mode → **batch replay via virtual demo clock** (`DEMO_NOW`).
2. Granularity → **both**: real daily TSA + deterministic checkpoint-hour
   disaggregation.
3. Staffing optimiser → **heuristic M/M/c rule engine + SimPy validation** (no ILP).
4. Map → **Plotly `scatter_geo`** (not Folium) as Page-1 hero.
5. Alerts → **in-dashboard only** (threshold-driven banners).
6. Demo target → **Docker Compose** (`data`/`api`/`dashboard`, ports 8000/8501);
   bare-Python dev path also supported.

## Key assets found
- **REAL DATA:** ERAU TSA FOIA dataset — ATL, DEN, ORD, LAX, DFW — 2020–2022 — CC BY 4.0
  https://datacommons.erau.edu/datasets/4dsy9vxxgx/1
- **SIMULATED DATA:** Kaggle Airport Operations Multi-Table
  https://www.kaggle.com/datasets/sinanshereef/airport-operations-multi-table-dataset
- **BEST SIMULATOR REPO:** aschatz1995/Airport-Security-Wait-Sim (SimPy, Python)
- **STACK CHOSEN (pending Architect freeze):** DuckDB + FastAPI + Darts + PyOD + Streamlit + Docker

## Session log
| Date | What happened |
|------|---------------|
| 2026-06-28 | Built as airport queue POC, then generalised to a domain-agnostic skeleton. Airport content stripped. 7 generic agents. Pushed to GitHub. |
| 2026-06-28 | DXC POC kicked off. Requirements written. Research complete. 6 AI use-case categories enumerated. Datasets and repos verified. Domain briefing written. |
| 2026-06-28 | **Architecture FROZEN by Solution Architect.** Decision log D1-D11 populated. Three contracts written: data-contract.md (5 tables + enums + shared constants), api-contract.md (10 endpoints, top-5 full shapes), ui-spec.md (6 Streamlit pages). All 6 open questions resolved. Specialists cleared to start: data-engineer first, then backend + ui in parallel, then test. |
| 2026-06-28 | **Data + backend implemented.** ETL now builds a full-history DuckDB and emits forecasts for both `SECURITY_TSA` and `SECURITY_PRECHECK`, aligning with the default demo clock. FastAPI contract implemented at `backend/app.py`, `Dockerfile.api` added, generated artifacts ignored, and `pytest projects/dxc-poc/tests/test_api.py` passes (4 tests). |
