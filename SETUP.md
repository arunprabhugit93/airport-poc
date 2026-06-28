# Setup & Workflow

How to work on this skeleton across multiple devices and how to run the
specialist agents. Read this once per device.

**Repo:** https://github.com/arunprabhugit93/airport-poc
**Source of truth:** GitHub. The repo (committed files) is the memory — not any
single machine and not OneDrive.

> The GitHub repo is still named `airport-poc` for now (that was the first
> project). The contents are a **generic, domain-agnostic agentic delivery
> skeleton**. You can rename the repo on GitHub later if you want; if you do,
> update the URLs here and your remote (`git remote set-url origin <new-url>`).

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

> **Why not work inside OneDrive/iCloud?** Git stores a live database in
> `.git/`. Cloud sync tries to copy those files mid-write, causing
> `index.lock` / `HEAD.lock` errors and possible repo corruption across
> devices. GitHub is the correct sync layer for git. Keep the working copy
> outside any cloud-sync folder.

---

## 2. Daily workflow (every device, every session)

```bash
git pull                              # get the latest before you start
# ... add requirements, run agents, edit files ...
git add -A
git commit -m "what you changed"
git push                              # share it back so other devices see it
```

The single rule: **always pull before working, always push after.** Never edit
from two devices without pushing in between.

---

## 3. Continuity protocol (how a fresh session catches up)

Any new session — human or agent — gets full context by reading, in order:

1. `CLAUDE.md` — what the skeleton is + the continuity protocol
2. `progress/status.md` — current state, next actions, open questions
3. `decisions/decision-log.md` — the frozen architecture for the active project
4. `research/` + `requirements/` — the domain briefing and what to build

At the **end** of every session, update `progress/status.md` and commit. That
habit is what lets the next session pick up cleanly with zero re-explaining.

---

## 4. Starting a new project (point the skeleton at a domain)

1. Write requirements into `requirements/` — what to build, for whom, to what end.
2. Run **researcher** → it studies the domain and writes a briefing to `research/`.
3. Run **solution-architect** → it freezes the architecture in
   `decisions/decision-log.md`. Approve or tweak the decision sheet once.
4. Run specialists: **data-engineer** → **backend-engineer + ui-engineer**
   (parallel) → **test-engineer** → **doc-writer**.

The agents carry no domain knowledge — they learn it from research and
requirements and become expert in whatever domain you load.

---

## 5. Running the agents (in Claude Code)

The agents in `agents/` are declarative Markdown — **no orchestration code to
run or maintain**. They execute inside **Claude Code** (the CLI), which
auto-discovers agent definitions under `.claude/agents/`.

### First time in a clone — link the agents
```bash
cd ~/Projects/airport-poc
mkdir -p .claude
ln -s ../agents .claude/agents      # symlink; or copy: cp -r agents .claude/agents
```

### Launch
```bash
cd ~/Projects/airport-poc
claude                               # opens Claude Code in this folder
```

Then ask it to run an agent, e.g.:
- "Run the researcher agent on the requirements and produce a domain briefing."
- "Run the solution-architect to freeze the architecture."

### The agents
| Agent | File | Role |
|-------|------|------|
| researcher | `agents/researcher.md` | Studies the domain; produces the briefing that makes the team expert |
| solution-architect | `agents/solution-architect.md` | Freezes the architecture; governs the build; reviews output |
| data-engineer | `agents/data-engineer.md` | Data ingestion, storage, and the data contract |
| backend-engineer | `agents/api-engineer.md` | Backend/API + core logic/models + the API contract |
| ui-engineer | `agents/ui-engineer.md` | The interface, built against the API contract |
| test-engineer | `agents/qa-engineer.md` | Tests logic, contracts, and that the system runs |
| doc-writer | `agents/docs-writer.md` | README, architecture note, run guide |

Build order: **researcher → solution-architect → data-engineer →
(backend-engineer + ui-engineer in parallel) → test-engineer → doc-writer.**
The build specialists use `isolation: worktree`, so parallel work doesn't
collide.

> Note: a few filenames still reflect old role names (`api-engineer.md` holds
> the backend-engineer, `qa-engineer.md` holds the test-engineer,
> `docs-writer.md` holds the doc-writer). The `name:` field inside each file is
> authoritative. Rename the files later if you want them to match.
