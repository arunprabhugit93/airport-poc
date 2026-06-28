# Architecture Decision Log (FROZEN CONTRACT)

> This is the frozen architecture. Agents and sessions **build against it and
> do not re-decide it.** To change a decision, append a new dated entry at the
> bottom under "Change history" — never silently overwrite a row above.
>
> **STATUS: PROPOSED — awaiting user approval.** Until the user says "approve",
> treat these as the architect's recommendation, not yet frozen.

## Decision sheet v1 (proposed 2026-06-28)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Core approach | Time-series forecast of queue length / wait time, served via API to a live dashboard | Matches use-case; proven open-source pattern transfers directly |
| 2 | Base/reference | LSTM/Prophet passenger-flow pattern (ferry/metro repos as reference); SimPy optionally to generate synthetic queue data | No turnkey airport repo exists; lowest-effort proven combination |
| 3 | Model | Start with **Prophet** (fallback: simple LSTM) | Handles daily/weekly seasonality out of the box; fastest to a working demo |
| 4 | Data source | **Synthetic generator** modeling realistic daily/weekly patterns | No live airport feed for a POC; standard approach. CHANGE if real data exists |
| 5 | Backend/API | **FastAPI** (Python) | Lightest Python API, auto-docs |
| 6 | Database | **SQLite** (file-based) | POC needs no Postgres; removes an ops surface. Swappable later |
| 7 | UI | **Streamlit** dashboard | Fastest Python-native UI; no JS stack to maintain |
| 8 | QA | pytest on model + API; smoke test dashboard loads | Proportional to a POC |
| 9 | Docs | README + architecture note + run guide | Enough for internal technical audience |
| 10 | Agent setup | Native Claude Code Markdown agents, `isolation: worktree`, no orchestration code | User constraint: nothing to babysit |

### The one open call
Decision #4 (synthetic data) flips the model/data design if real historical
data exists. Resolve before freezing.

---

## Change history
_Append dated entries here when a frozen decision changes. Format:_
_`### YYYY-MM-DD — <what changed and why>`_

### 2026-06-28 — Initial proposal recorded (not yet approved)
