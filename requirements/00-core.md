# Core POC scope (seed)

> This is a seed file capturing what we've established so far. Expand or
> override it by adding more files or editing this one.

## What the POC must demonstrate
- Predict passenger queue length / wait time at airport checkpoints
  (e.g. security, check-in) over time.
- Show the forecast in a live dashboard a non-technical viewer can read.

## Confirmed so far
- Python-centric stack.
- Any open-source license acceptable (internal POC).
- Running local demo is the target deliverable.
- **Data: real historical (TSA FOIA throughput + Kaggle Airport Operations).**
  No free live queue API exists. See decision #4 in decisions/decision-log.md.

## Open questions for the user (fill in when known)
- [x] Real data vs synthetic → RESOLVED: real historical data.
- [ ] How many checkpoints should the demo model? (default: 1–3)
- [ ] Forecast horizon? (default: next periods at dataset granularity)
- [ ] Who is the demo audience? (default: internal technical)

## Add more below as you think of them
-
