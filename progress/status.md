# Project status

> Update this at the END of every session. It's how the next session knows
> where to pick up. Keep it short and current.

## Current state
- Repo scaffolded with continuity protocol (CLAUDE.md, requirements/,
  decisions/, progress/, agents/).
- Architecture decision sheet in `decisions/decision-log.md` —
  **APPROVED & FROZEN (2026-06-28).**
- Decision #4 resolved: **real historical data** (TSA FOIA throughput +
  Kaggle Airport Operations). No free live queue API exists.
- Specialist agents defined in `agents/`.
- No application code written yet.

## Next actions
1. **data-engineer**: download/ingest TSA FOIA + Kaggle Operations data,
   define SQLite schema + load layer, publish the data contract.
2. Then in parallel: api-engineer (FastAPI forecast endpoints, Prophet),
   ui-engineer (Streamlit dashboard).
3. Then qa-engineer (pytest + smoke test) + docs-writer (README, run guide).

## Open questions (non-blocking — defaults stand until told otherwise)
- Number of checkpoints to model (default 1–3) and forecast horizon
  (default: next periods, granularity per dataset).
- FOIA data is daily-granular; if the demo needs sub-daily queue depth,
  add the optional synthetic minute-level layer (noted in decision #4).

## Session log
| Date | What happened |
|------|---------------|
| 2026-06-28 | Repo scaffolded, decision sheet proposed, agents defined. Git initialized. |
| 2026-06-28 | Researched live queue APIs — none free/open. Decision #4 set to real historical data. Sheet frozen. |
