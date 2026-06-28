# Architecture Decision Log (FROZEN CONTRACT)

> This is the frozen architecture. Agents and sessions **build against it and
> do not re-decide it.** To change a decision, append a new dated entry at the
> bottom under "Change history" — never silently overwrite a row above.
>
> **STATUS: APPROVED & FROZEN (2026-06-28).** Build against this. To change any
> row, append a dated entry under "Change history" — never overwrite above.

## Decision sheet v1 (frozen 2026-06-28)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Core approach | Time-series forecast of queue length / wait time, served via API to a live dashboard | Matches use-case; proven open-source pattern transfers directly |
| 2 | Base/reference | LSTM/Prophet passenger-flow pattern (ferry/metro repos as reference); SimPy optionally to generate synthetic queue data | No turnkey airport repo exists; lowest-effort proven combination |
| 3 | Model | Start with **Prophet** (fallback: simple LSTM) | Handles daily/weekly seasonality out of the box; fastest to a working demo |
| 4 | Data source | **Real historical data** — TSA FOIA passenger-throughput dataset (5 US airports, 2020–2022) + Kaggle "Airport Operations Multi-Table" simulated security/journey tables. **No live API** (none exists free/open as of 2026). Optional synthetic minute-level layer only if sub-daily queue granularity is needed | Research confirmed no free live queue API; official TSA endpoint deprecated 2023. Real free data gives best credibility-per-effort, no paid dependency |
| 5 | Backend/API | **FastAPI** (Python) | Lightest Python API, auto-docs |
| 6 | Database | **SQLite** (file-based) | POC needs no Postgres; removes an ops surface. Swappable later |
| 7 | UI | **Streamlit** dashboard | Fastest Python-native UI; no JS stack to maintain |
| 8 | QA | pytest on model + API; smoke test dashboard loads | Proportional to a POC |
| 9 | Docs | README + architecture note + run guide | Enough for internal technical audience |
| 10 | Agent setup | Native Claude Code Markdown agents, `isolation: worktree`, no orchestration code | User constraint: nothing to babysit |

### Data sources (decision #4 detail)
- **TSA FOIA throughput** — real daily passenger counts, ATL/DEN/ORD/LAX/DFW,
  2020-02-15 → 2022-10-15. Source: https://www.tsa.gov/foia/readingroom
- **Kaggle Airport Operations Multi-Table** — simulated end-to-end ops incl.
  security processing & passenger journeys (realistic structure).
  https://www.kaggle.com/datasets/sinanshereef/airport-operations-multi-table-dataset
- Live APIs evaluated and rejected: TSA GetTSOWaitTimes (dead 2023),
  TSAWaitTimes.com (paid, estimates-on-estimates), SITA/FlightQueue (enterprise).

---

## Change history
_Append dated entries here when a frozen decision changes. Format:_
_`### YYYY-MM-DD — <what changed and why>`_

### 2026-06-28 — Initial proposal recorded (not yet approved)

### 2026-06-28 — Decision #4 resolved & sheet frozen
Research confirmed no free/open live airport queue API exists (official TSA
endpoint deprecated 2023; others paid/enterprise). Changed #4 from synthetic to
**real historical data** (TSA FOIA + Kaggle Operations). Sheet approved by user
and frozen. All other rows unchanged.
