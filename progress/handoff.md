# Handoff — read this first

> Last updated: 2026-06-29
> Platform: DXC Airport Operations

---

## Repos

| Repo | Purpose | Clone to |
|------|---------|----------|
| [airport-poc](https://github.com/arunprabhugit93/airport-poc) | Process skeleton (you're here) — agents, requirements, research, decisions | `~/Projects/airport-poc/` |
| [dxc-airport-queue-mgmt](https://github.com/arunprabhugit93/dxc-airport-queue-mgmt) | App code — backend, Next.js frontend, data, tests | `~/Projects/dxc-airport-queue-mgmt/` |

---

## Platform status

| Module | Status | Backend | Frontend | API Endpoints |
|--------|--------|---------|----------|---------------|
| Queue Management | DONE | `backend/` (FastAPI, port 8000) | `frontend/src/app/` (Next.js, port 3000) | 19 endpoints, 16 tests |
| Flight Operations | NOT STARTED | — | Placeholder tab in nav | — |
| Baggage Handling | NOT STARTED | — | Placeholder tab in nav | — |
| Comms | NOT STARTED | — | Placeholder tab in nav | — |
| Maintenance | NOT STARTED | — | Placeholder tab in nav | — |
| Retail | NOT STARTED | — | Placeholder tab in nav | — |

## Tech stack
- **Frontend:** Next.js 16 + React + TypeScript + Tailwind CSS + shadcn/ui + Recharts
- **Backend:** Python 3.12, FastAPI, DuckDB, SimPy
- **Data:** Synthetic (seeded), 6 queue areas, 5 airports
- **Theme:** Dark/light toggle, enterprise design

---

## To work on Queue Management
```bash
cd ~/Projects/dxc-airport-queue-mgmt
# Read CLAUDE.md + CHECKPOINT.md for context
```

## To start a new module (e.g., Flight Ops)
```bash
cd ~/Projects/airport-poc
# 1. Write requirements in requirements/flight-ops.md
# 2. Run researcher agent → research/flight-ops-briefing.md
# 3. Run solution-architect → decisions/flight-ops-decisions.md
# 4. Build backend in app repo: services/flight-ops/ or extend backend/
# 5. Build frontend pages in app repo: frontend/src/app/flight-ops/
# 6. Update this handoff
```

---

## Key facts
- Streamlit has been removed — Next.js is the only frontend
- The app repo has its own CLAUDE.md + CHECKPOINT.md for AI context
- Queue management has: Command Center, Passenger Journey, Queue Intelligence, Forecast, Anomalies, Staffing, Simulator, Analytics
- Demo clock in sidebar — shared across all pages via React context
- CORS enabled on FastAPI for cross-origin requests from Next.js
