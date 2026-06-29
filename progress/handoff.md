# Handoff — read this first, read ONLY what it tells you

> Last updated: 2026-06-29
> Project: DXC Airport Queue Management POC
> Location: `projects/dxc-poc/`

---

## What's done

| Phase | Status | Key output |
|-------|--------|------------|
| Requirements | DONE | `requirements/dxc-poc-queue-management.md` |
| Research | DONE | `projects/dxc-poc/research/domain-briefing.md` |
| Architecture | FROZEN+EXTENDED | `decisions/decision-log.md` (D1-D11, + immigration, + new endpoints) |
| Data layer (ETL) | DONE | `data/etl/` with IMMIGRATION area, full date coverage |
| Shared config | DONE | `backend/config.py` (6 area types, terminal data per airport) |
| Backend (FastAPI) | DONE | `backend/app.py` — 14 endpoints (10 original + 4 new) |
| SimPy simulation | DONE | `backend/sim/checkpoint_sim.py` |
| UI (Streamlit) | DONE | 8 pages: Command Center, Journey, Queues, Forecast, Anomalies, Staffing, WhatIf, Analytics |
| API tests | DONE | `tests/test_api.py` (4 tests passing) |
| Docker | DONE | `Dockerfile.api`, `Dockerfile.ui`, `docker-compose.yml` |
| Docs | NOT STARTED | — |

---

## Key facts
- **6 area types:** SECURITY_TSA, SECURITY_PRECHECK, CHECKIN, IMMIGRATION, GATE, BAGGAGE
- **5 airports with terminals:** ATL, DEN, ORD, LAX, DFW
- **14 API endpoints** on port 8000, 8 UI pages on port 8501
- **Demo clock:** default `2021-11-24 07:00:00` (Thanksgiving surge)
- **All data synthetic, seeded RNG, reproducible**

---

## What to do next
1. Write README + demo script (docs/)
2. Add tests for new endpoints
3. Keep adding features
