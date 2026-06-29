# Agentic Delivery Skeleton

> **Cold-start rule:** Read ONLY `progress/handoff.md`. It tells you exactly
> what to do, which repos to clone, and which files to read.

---

## What this is

A reusable AI delivery framework. 7 specialist agents deliver projects:
researcher → solution-architect → data-engineer → backend-engineer +
ui-engineer → test-engineer → doc-writer. Agent definitions in `agents/`.

This skeleton provides the **process**. The **code** lives in separate repos.

---

## Active platform: DXC Airport Ops

| Repo | What | URL |
|------|------|-----|
| `airport-poc` (this) | Process, agents, continuity, requirements, research, decisions | https://github.com/arunprabhugit93/airport-poc |
| `dxc-airport-queue-mgmt` | Queue Management module (backend + Next.js frontend + data) | https://github.com/arunprabhugit93/dxc-airport-queue-mgmt |

### Platform modules (in `dxc-airport-queue-mgmt`)
- **Queue Management** — BUILT (19 API endpoints, 8 Next.js pages)
- **Flight Operations** — NOT STARTED (placeholder in nav)
- **Baggage Handling** — NOT STARTED (placeholder in nav)
- **Comms** — NOT STARTED (placeholder in nav)
- **Maintenance** — NOT STARTED (placeholder in nav)
- **Retail** — NOT STARTED (placeholder in nav)

---

## Starting a new module

1. Read `progress/handoff.md` for current state
2. Write requirements for the module in `requirements/`
3. Run the researcher agent → produces domain briefing
4. Run solution-architect → freezes architecture
5. Build in the app repo under the appropriate service/pages directory
6. Update `progress/handoff.md` when done

---

## Continuity protocol

### Starting a session
1. Read `progress/handoff.md` — it has your task and repo links
2. Clone/pull the app repo if working on code
3. The app repo has its own `CLAUDE.md` + `CHECKPOINT.md`

### Ending a session
1. Update `progress/handoff.md` in this repo
2. Update `CHECKPOINT.md` in the app repo
3. Commit and push both

### Rules
- `progress/handoff.md` is the only file read at cold start
- The app repo is self-contained — give it to any AI tool and it works
- Contracts in `decisions/` and `projects/dxc-poc/architecture/` are reference only
