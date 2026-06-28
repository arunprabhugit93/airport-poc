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

## Next actions (specialists may start)
1. **data-engineer** → build DuckDB at `projects/dxc-poc/data/airport.duckdb` per
   `data-contract.md`: ETL TSA FOIA + Kaggle, run disaggregation + M/M/c wait
   derivation, train models, write predictions/anomalies/staffing tables.
2. **backend-engineer** + **ui-engineer** → run in PARALLEL once the DuckDB file
   exists. Backend builds FastAPI per `api-contract.md`; UI builds the 6 Streamlit
   pages per `ui-spec.md`.
3. **test-engineer** → verify both contracts + model/sim sanity (D10).
4. **doc-writer** → README + `docs/demo-script.md` (D11).

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
