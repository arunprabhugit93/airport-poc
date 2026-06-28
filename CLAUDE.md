# Agentic Delivery Skeleton

> **READ THIS FIRST, EVERY SESSION.** This file is the project's memory.
> A fresh session knows nothing until it reads this. Start every session by
> reading this file, then `progress/status.md`, then `decisions/decision-log.md`,
> then anything under `research/` and `requirements/` relevant to the task.

---

## What this is

A **generic, domain-agnostic skeleton** for delivering a project with a team of
specialist AI agents. It carries **no domain knowledge of its own.** You point
it at a domain by writing requirements; the agents then research that domain,
become expert in it, and build the solution — research → architecture → data →
backend → UI → test → docs.

Today it might build an airport tool; tomorrow, anything. The skeleton stays the
same. Only `requirements/`, `research/`, `decisions/`, and the produced code
change per project.

---

## The agents (in `agents/`)

| Agent | Role |
|-------|------|
| `researcher` | Studies the domain, gathers prior art/data/standards, produces a briefing that makes the team expert |
| `solution-architect` | Turns research + requirements into a frozen architecture; governs the build |
| `data-engineer` | Builds the data layer + a stable data contract |
| `backend-engineer` | Builds the backend/API + core logic/models + a stable API contract |
| `ui-engineer` | Builds the interface against the API contract |
| `test-engineer` | Verifies logic, contracts, and that the system runs |
| `doc-writer` | Writes README, architecture note, run guide from the committed artifacts |

There is **no orchestration code** — agents are declarative Markdown. Nothing to
run or maintain beyond the agent files themselves.

---

## How a project flows

1. **You** write requirements into `requirements/` (freely, over many sessions).
2. **researcher** reads them, studies the domain, writes a briefing to `research/`.
3. **solution-architect** freezes the architecture in `decisions/decision-log.md`.
   You approve/tweak the decision sheet once — that's your main input gate.
4. **data-engineer** → then **backend-engineer + ui-engineer** (parallel) →
   **test-engineer** → **doc-writer**. Each works against the frozen contracts.
5. **End of session:** update `progress/status.md`, commit. The repo is the
   memory, not the conversation.

---

## Continuity protocol (why this survives sessions and devices)

A new session catches up by reading, in order: `CLAUDE.md` → `progress/status.md`
→ `decisions/decision-log.md` → `research/` + `requirements/`. Context lives in
committed files, so no session ever re-explains the project and no tokens are
wasted re-deriving it. See `SETUP.md` for the multi-device git workflow.

---

## Working rules

- **Expensive-to-reverse decisions** (schema, contracts, core approach) are
  frozen in `decisions/`. Build against them; append-only changes.
- **Cheap/local decisions** — agents just make them.
- **One source of truth:** if chat and a committed file disagree, the file wins.
- **Each agent learns the domain from research + requirements** — it never
  assumes a previous project's domain or stack.

---

## Repo map

```
.
├── CLAUDE.md                 ← you are here; read first
├── SETUP.md                  ← per-device git workflow + how to run the agents
├── requirements/             ← dump requirements here, freely, over time
│   ├── README.md
│   └── 00-core.md            ← start-here / how to begin a project
├── research/                 ← researcher writes the domain briefing here (created on use)
├── decisions/
│   └── decision-log.md       ← architecture, frozen per project (starts empty)
├── progress/
│   └── status.md             ← updated end of every session
└── agents/                   ← the 7 specialist agent definitions (Markdown)
    ├── researcher.md
    ├── solution-architect.md
    ├── data-engineer.md
    ├── backend-engineer.md   (file: api-engineer.md)
    ├── ui-engineer.md
    ├── test-engineer.md      (file: qa-engineer.md)
    └── doc-writer.md         (file: docs-writer.md)
```
