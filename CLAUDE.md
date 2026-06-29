# Agentic Delivery Skeleton

> **Cold-start rule:** Read ONLY `progress/handoff.md`. It tells you exactly
> what to do and which files to read. Do NOT read the full decision log,
> research, or requirements unless the handoff says to.

---

## Quick context (skim, don't study)

7 specialist AI agents (researcher → solution-architect → data-engineer →
backend-engineer + ui-engineer → test-engineer → doc-writer) deliver a project.
Agents are declarative Markdown in `agents/`. No orchestration code.

**Active project:** DXC Airport Queue Management POC in `projects/dxc-poc/`.

---

## Continuity protocol (token-efficient)

### Starting a session (any account, any device)
1. Read `progress/handoff.md` — it has your task, relevant files, and state.
2. Read ONLY the files the handoff tells you to read.
3. Start working. Do not re-derive context that's already in the handoff.

### Ending a session
1. Update `progress/handoff.md` with exactly where you stopped:
   - Files created/modified (paths)
   - What works, what doesn't
   - Exact next step (not a menu — one clear action)
   - Which contract files the next session needs
2. Commit and push.

### Rules
- `progress/handoff.md` is the **only** file every session reads. Keep it under
  100 lines. It replaces the old "read 5 files in order" chain.
- `progress/status.md` is the **session log** (append-only history). Not read
  at cold start unless you need history.
- Frozen contracts in `decisions/` and `projects/dxc-poc/architecture/` are
  read **only when building against them** — not for orientation.
- If chat and a committed file disagree, the file wins.

---

## Repo map

```
.
├── CLAUDE.md                 ← you are here (skim only)
├── SETUP.md                  ← per-device git workflow
├── progress/
│   ├── handoff.md            ← ** READ THIS FIRST ** (cold-start briefing)
│   └── status.md             ← session log (append-only, not read at start)
├── decisions/
│   └── decision-log.md       ← frozen architecture (read only when building)
├── projects/dxc-poc/         ← all project code + contracts
│   ├── architecture/         ← data-contract.md, api-contract.md, ui-spec.md
│   ├── data/                 ← ETL + DuckDB
│   ├── backend/              ← FastAPI + models
│   ├── ui/                   ← Streamlit dashboard
│   ├── tests/                ← pytest
│   └── docs/                 ← demo script, README
├── requirements/             ← project requirements
├── research/                 ← domain briefing
└── agents/                   ← 7 specialist agent definitions
```
