# Airport Passenger Flow / Queue Prediction POC

> **READ THIS FIRST, EVERY SESSION.** This file is the project's memory.
> A fresh Claude session knows nothing until it reads this. Start every
> session by reading this file, then `progress/status.md`, then anything
> under `requirements/` and `decisions/` that is relevant to the task.

---

## How to use this repo (continuity protocol)

This repo is designed so you can **dump requirements over many sessions and
never re-explain context**. The rules:

1. **Start of session:** read `CLAUDE.md` (this file) → `progress/status.md`
   → relevant files in `requirements/` and `decisions/`. You are now caught up.
2. **Adding requirements:** the user writes them into `requirements/` (any
   number of `.md` files, any time). Treat everything there as the source of
   truth for *what* to build.
3. **Architecture is frozen in `decisions/decision-log.md`.** Do NOT re-decide
   anything already recorded there. If a decision must change, append a new
   dated entry — never silently overwrite.
4. **End of session:** update `progress/status.md` with what was done, what's
   next, and any open questions. Commit. This is what makes the *next* session
   pick up cleanly.
5. **Commit often.** The git history is the audit trail. The repo is the memory,
   not the conversation.

---

## Project at a glance

- **Goal:** POC demonstrating passenger flow / queue (wait-time) prediction for
  an airport.
- **Audience:** internal / technical (until stated otherwise).
- **Stack:** Python-centric.
- **License posture:** any open-source acceptable (internal POC).
- **Deliverable:** a running local demo (forecast → API → dashboard).

The full, frozen architecture is in `decisions/decision-log.md`. Do not
duplicate it here.

---

## Working rules for agents and sessions

- **Expensive-to-reverse decisions** (DB schema, API contract, core model
  choice) are frozen in `decisions/`. Build against them; don't drift.
- **Cheap/local decisions** (component layout, query details, validation rules)
  — just make them, no need to ask.
- **One source of truth:** if the conversation and a committed file disagree,
  the committed file wins. Update the file rather than carrying state in chat.
- **No orchestration code.** Specialists are the Markdown agents in
  `agents/`. There is deliberately no `orchestra.py` to maintain.
  (If you run this through Claude Code's native agent system, copy or symlink
  `agents/` to `.claude/agents/` — Claude Code auto-discovers agents there.)

---

## Repo map

```
.
├── CLAUDE.md                 ← you are here; read first
├── SETUP.md                  ← per-device git workflow + how to run the agents
├── requirements/             ← dump requirements here, freely, over time
│   └── README.md             ← index of requirement files
├── decisions/
│   └── decision-log.md       ← FROZEN architecture contract (+ change history)
├── progress/
│   └── status.md             ← updated end of every session
└── agents/                   ← specialist agent definitions (Markdown)
    ├── solution-architect.md
    ├── data-engineer.md
    ├── api-engineer.md
    ├── ui-engineer.md
    ├── qa-engineer.md
    └── docs-writer.md
```
