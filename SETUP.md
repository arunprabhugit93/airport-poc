# Setup & Workflow

How to work on this project across multiple devices and how to run the
specialist agents. Read this once per device.

**Repo:** https://github.com/arunprabhugit93/airport-poc
**Source of truth:** GitHub. The repo (committed files) is the project's memory —
not any single machine and not OneDrive.

---

## 1. One-time setup per device

Each device needs git installed and authenticated to GitHub once.

```bash
# Clone into a folder that is NOT cloud-synced (avoid OneDrive/iCloud paths).
# ~/Projects is a safe default.
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/arunprabhugit93/airport-poc.git
cd airport-poc
```

**Authentication:** the first `git push` prompts for credentials.
- Username: `arunprabhugit93`
- Password: a **Personal Access Token** (NOT your GitHub password).
  Create one at: GitHub → Settings → Developer settings →
  Personal access tokens → Tokens (classic) → Generate → tick `repo` scope.

> **Why not OneDrive?** Git stores a live database in `.git/`. OneDrive (and
> iCloud) try to sync those files mid-write, causing `index.lock` / `HEAD.lock`
> errors and, on multiple devices, possible repo corruption. GitHub is the
> correct sync layer for git. Keep the working copy outside any cloud-sync
> folder.

---

## 2. Daily workflow (every device, every session)

```bash
git pull                              # get the latest before you start
# ... dump requirements, run agents, edit files ...
git add -A
git commit -m "what you changed"
git push                              # share it back so other devices see it
```

The single rule that keeps you sane: **always pull before working, always push
after.** Never edit the same project from two devices without pushing in
between.

---

## 3. Continuity protocol (how a fresh session catches up)

Any new session — human or agent — gets full context by reading, in order:

1. `CLAUDE.md` — project rules + the continuity protocol
2. `progress/status.md` — current state, next actions, open questions
3. `decisions/decision-log.md` — the FROZEN architecture (build against it)
4. `requirements/` — what to build (dump new requirements here freely)

At the **end** of every session, update `progress/status.md` and commit. That
single habit is what lets the next session pick up cleanly with zero
re-explaining.

---

## 4. Running the specialist agents (in Claude Code)

The agents in `agents/` are declarative Markdown — there is **no orchestration
code to run or maintain**. They execute inside **Claude Code** (the CLI), which
auto-discovers agent definitions.

### First time in a clone
Claude Code looks for agents under `.claude/agents/`. This repo keeps them in
`agents/` (a portable location). Link them once per clone:

```bash
cd ~/Projects/airport-poc
mkdir -p .claude
ln -s ../agents .claude/agents      # symlink; or copy if you prefer: cp -r agents .claude/agents
```

### Launch
```bash
cd ~/Projects/airport-poc
claude                               # opens Claude Code in this folder
```

Then ask it to run a specialist, e.g.:
- "Use the solution-architect agent to review the frozen decisions and plan the build."
- "Run the data-engineer agent to ingest the TSA FOIA + Kaggle data and build the SQLite layer."

### The agents
| Agent | Role |
|-------|------|
| `solution-architect` | Governs the build; freezes/maintains decisions; reviews other agents' output |
| `data-engineer` | Ingests real data (TSA FOIA + Kaggle), builds SQLite schema + load layer, publishes the data contract |
| `api-engineer` | FastAPI forecast endpoints (Prophet) over the data |
| `ui-engineer` | Streamlit dashboard of current vs predicted queue/wait-times |
| `qa-engineer` | pytest on model + API; dashboard smoke test |
| `docs-writer` | README, architecture note, run guide |

Build order: **data-engineer first** (defines the contract), then
**api-engineer + ui-engineer in parallel**, then **qa-engineer + docs-writer**.
Each agent uses `isolation: worktree`, so parallel work doesn't collide.

---

## 5. Cleanup note (one-time)

A leftover test git repo may exist at `~/Documents/Airport POC/.git` from
earlier setup. It's unused — remove it:

```bash
rm -rf "$HOME/Documents/Airport POC/.git"
```
