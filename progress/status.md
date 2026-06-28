# Project status

> Update this at the END of every session. It's how the next session knows
> where to pick up. Keep it short and current.

## Current state
- This is the **generic agentic delivery skeleton** — domain-agnostic.
- Seven agents defined in `agents/`: researcher, solution-architect,
  data-engineer, backend-engineer, ui-engineer, test-engineer, doc-writer.
- Continuity protocol in place (CLAUDE.md, requirements/, decisions/, progress/).
- **No active project loaded.** `requirements/` and `decisions/` are empty
  templates awaiting a domain.

## Next actions
1. Add project requirements to `requirements/`.
2. Run the **researcher** agent → produces a domain briefing in `research/`.
3. Run the **solution-architect** → freezes the architecture in
   `decisions/decision-log.md`.
4. Run specialists in order: data-engineer → (backend-engineer + ui-engineer in
   parallel) → test-engineer → doc-writer.

## Open questions
- (none — skeleton is at rest, awaiting a project)

## Session log
| Date | What happened |
|------|---------------|
| 2026-06-28 | Built as airport queue POC, then generalised to a domain-agnostic skeleton. Airport content stripped. 7 generic agents. Pushed to GitHub. |
