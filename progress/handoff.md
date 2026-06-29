# Handoff — read this first, read ONLY what it tells you

> Last updated: 2026-06-29
> Active project: DXC Airport Queue Management POC

---

## Repo split (2026-06-29)

The app code now lives in a **separate deployable repo**:

| Repo | Purpose | URL |
|------|---------|-----|
| `airport-poc` | Agentic delivery skeleton (agent definitions, process, continuity) | https://github.com/arunprabhugit93/airport-poc |
| `dxc-airport-queue-mgmt` | Application code (deploy this) | https://github.com/arunprabhugit93/dxc-airport-queue-mgmt |

**For deployment:** give only `dxc-airport-queue-mgmt`. It's self-contained.
**For AI workflow:** clone both. Skeleton has the agents + process. App has the code.

### Local paths
- Skeleton: `~/Projects/airport-poc/`
- App: `~/Projects/dxc-airport-queue-mgmt/`

### Context protocol
The app repo has its own `CLAUDE.md` + `CHECKPOINT.md`. A new session reads only
those two files (~60 lines total). No need to read this skeleton's files when
working on the app code.

---

## What to do next
- Work on the app? `cd ~/Projects/dxc-airport-queue-mgmt` and follow its CHECKPOINT.md
- Start a new project? Write requirements in this skeleton's `requirements/`, run the agents
