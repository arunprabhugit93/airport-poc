# Project status

> Update this at the END of every session. It's how the next session knows
> where to pick up. Keep it short and current.

## Current state
- Repo scaffolded with continuity protocol (CLAUDE.md, requirements/,
  decisions/, progress/, .claude/agents/).
- Architecture decision sheet drafted in `decisions/decision-log.md` —
  **PROPOSED, awaiting user approval.**
- Specialist agents defined in `.claude/agents/`.
- No application code written yet.

## Next actions
1. **User to approve or tweak** the decision sheet in `decisions/decision-log.md`.
2. **User to answer:** real data or synthetic? (the one open architectural call)
3. Once frozen → data-engineer agent builds the synthetic data generator + SQLite layer.
4. Then in parallel: api-engineer (FastAPI), ui-engineer (Streamlit).
5. Then qa-engineer + docs-writer.

## Open questions
- Real passenger data available, or synthetic? (blocks freezing decision #4)
- Number of checkpoints, forecast horizon (defaults noted in requirements/00-core.md)

## Session log
| Date | What happened |
|------|---------------|
| 2026-06-28 | Repo scaffolded, decision sheet proposed, agents defined. Git initialized. |
