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
| Architecture | FROZEN+EXTENDED | `decisions/decision-log.md` (D1-D11) |
| Data layer (ETL) | DONE | 6 area types (incl. IMMIGRATION), full 2020-2022 range |
| Backend (FastAPI) | DONE | 19 endpoints (10 original + 9 new) |
| UI (Streamlit) | DONE | 8 pages, dark ops-dashboard theme, Sankey/gauges/heatmaps |
| Tests | DONE | 16 API tests, all passing |
| Docs | DONE | README.md + docs/demo-script.md |
| Docker | DONE | Dockerfile.api, Dockerfile.ui, docker-compose.yml |

---

## API endpoints (19 total)

| # | Method | Path | Added |
|---|--------|------|-------|
| 1 | GET | `/health` | original |
| 2 | GET | `/airports` | original |
| 3 | GET | `/queues/current` | original |
| 4 | GET | `/queues/forecast` | original |
| 5 | GET | `/anomalies/recent` | original |
| 6 | GET | `/staffing/recommend` | original |
| 7 | POST | `/simulate/what-if` | original |
| 8 | GET | `/dashboard/kpis` | original |
| 9 | GET | `/models` | original |
| 10 | GET/POST | `/config/clock` | original |
| 11 | GET | `/queues/all-areas` | overhaul |
| 12 | GET | `/passenger-journey` | overhaul |
| 13 | GET | `/operations/recommendations` | overhaul |
| 14 | GET | `/queues/heatmap` | overhaul |
| 15 | GET | `/operations/shift-handoff` | v2 |
| 16 | GET | `/airports/{code}/terminals` | v2 |
| 17 | GET | `/airports/{code}/capacity` | v2 |
| 18 | GET | `/airports/{code}/scorecard` | v2 |
| 19 | GET | `/network/health` | v2 |

## UI pages (8 total)

1. Operations Command Center (network health grade, recommendations, map, gauges, queues, forecast, shift handoff)
2. Passenger Journey (Sankey diagram, timeline, bottleneck, stage cards)
3. Queue Intelligence (all-areas cards, heatmap, terminal breakdown, capacity utilization)
4. Predictive Intelligence (breach forecast, multi-model, CI bands)
5. Anomaly Intelligence (incident cards, impact, cross-airport)
6. Staff & Lane Optimizer (schedule, shifts, cost, gap analysis)
7. Scenario Simulator (gauge before/after, save/compare scenarios)
8. Analytics & Reporting (executive summary, trends, ranking, scorecard)

---

## Key facts
- **6 area types:** SECURITY_TSA, SECURITY_PRECHECK, CHECKIN, IMMIGRATION, GATE, BAGGAGE
- **5 airports with terminals:** ATL (2), DEN (4), ORD (4), LAX (9), DFW (5)
- **19 API endpoints** on port 8000, **8 UI pages** on port 8501
- **Demo clock:** default `2021-11-24 07:00:00` (Thanksgiving surge)
- **16 passing tests**
- **All data synthetic, seeded, reproducible**

---

## To run
```bash
cd projects/dxc-poc
python -m data.etl.run_etl           # build DuckDB (~30s)
uvicorn backend.app:app --port 8000  # API
cd ui && streamlit run Home.py       # Dashboard on :8501
```
