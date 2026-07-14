---
name: skill-session-end-reviewer-code
description: Code reviewer close-out — Core Docs staleness flags, persist review report.
source: project
---

# Skill: Code Reviewer Session End

**This skill runs only when the user explicitly triggers session-end.** Do not run automatically
after the review report is produced. See `principles.md §Workflow`.

Read this file **now** — do not rely on memory from session start.

---

## 1. Core Docs Staleness Check

**Answer each explicitly in the review report. Do not skip any row.** Reviewers do not fix code —
flag staleness in findings and escalate.

| Doc | Staleness found? | If yes, flagged in findings? |
|:----|:-----------------|:------------------------------|
| `context.md` | YES / NO | ✅ / N/A |
| `pipeline.md` | YES / NO | ✅ / N/A |
| `principles.md` | YES / NO | ✅ / N/A |
| `README.md` | YES / NO | ✅ / N/A |

## 2. Persist Review Report

- [ ] Save review report to `logs/review-code/YYMMDD-HHMM-review-{scope}.md` using the
  **review report format** in `ref-review-report-format.md`
- [ ] Persist via your own worktree + branch, landed via grant + `land.sh` (per `principles.md
  §Git & Branching` — no PR, no remote): commit on your branch, obtain the grant, run
  `meta/scripts/land.sh <case-id>` yourself, then clean up your own worktree and branch
- [ ] Report any unresolved items to user
