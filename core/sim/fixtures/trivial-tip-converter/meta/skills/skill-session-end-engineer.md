---
name: skill-session-end-engineer
description: Paperwork-only close-out — status flip, archive, log, doc sync. Validation is a precondition.
source: project
---

# Skill: Engineer Session End

**This skill runs only when the user explicitly triggers session-end.** Do not run automatically
after merge, after validation passes, or because the conversation feels "done." See
`principles.md §Workflow`.

Read this file **now** — do not rely on memory from session start.

---

## Precondition: validation must already have run

This skill is **paperwork only**. It does not validate. Validation lives in
`skills/skill-validate.md` and must already have produced a clean Completion Report at:

- **Local validation** (pre-merge), all ACs `PASS`.
- **Post-merge re-validation** (on `main`), all ACs `PASS`, no regressions.

If either is missing or has any `UNVERIFIED` row → STOP. Run validation first, then return here.
Do not substitute alternative evidence — see `skill-validate.md §Constraints`.

Reviewers (code) do **not** dispatch from this skill — they are dispatched by the Orchestrator on
its own review cadence.

---

## 1. User Acknowledgment Gate

Before any status flip, surface in chat:

```
Completion Report: meta/logs/engineering/log-…-{block-id}-…md (## Completion Report) — N/N PASS (local)
Post-merge re-validation: N/N PASS
Trigger session-end? (explicit yes required)
```

Ambiguous responses ("looks good", "sounds fine", "ok") are **not** authorization — re-prompt for
an explicit go-ahead. If the user pushes back on a verified PASS without producing new evidence, do
not capitulate — re-state the evidence.

---

## 2. Pre-Close Checks

- [ ] All tasks completed this session are tested and committed
- [ ] No undisclosed hard blocks this session — any hard block must have been escalated when
  detected, not deferred to this gate

---

## 3. Core Docs Staleness Check

**Answer each explicitly in the session log. Do not skip any row.**

| Doc | Affected? | Updated? |
|:----|:----------|:---------|
| `context.md` | YES / NO | ✅ / N/A |
| `pipeline.md` | YES / NO | ✅ / N/A |
| `principles.md` | YES / NO | ✅ / N/A |
| `README.md` | YES / NO | ✅ / N/A |

Also sweep the project structure: any new files created this session (routes, lib modules,
components) must be reflected in `README.md §Layout` if they change the described structure.

---

## 4. Git Sync

Follow `principles.md §Git & Branching` — your own worktree + branch, landed via grant + `land.sh`;
no PR, no remote.

## 5. Logging

- [ ] Create session log at `meta/logs/engineering/log-YYMMDD-HHMM-{description}.md` using the
  **session-log format** in `ref-session-log-format.md`
- [ ] Final checklist for user — numbered list of remaining manual actions

---

## 6. Block Status Update *(the only status flip in this project)*

**Runs only after** §1 user acknowledgment is explicit and §2–§5 are clean, and
`skill-validate.md` has produced clean local and post-merge Completion Reports.

For each block completed this session:

- [ ] Update block doc status: `**Status:** ✅ Done`
- [ ] Add `**Completed:** YYYY-MM-DD`
- [ ] Move the block file from `blocks/` to `blocks/archive/`
  (`git mv blocks/{id}.md blocks/archive/{id}.md`); the Completion Report lives in the engineer's
  session log under `meta/logs/engineering/` and stays there
- [ ] In `pipeline.md`, edit **only your block's own row(s)**: flip the Status cell and
  repoint the Notes `` Block `blocks/…` `` link to the archived path. Change **nothing else** —
  not the `**Last Updated:**` header, not phase headers, not any other block's row. The
  pipeline's document shape is the Orchestrator's/architect's to change, not yours; every
  line you touch in `pipeline.md` must name your own block id, or the landing is refused as
  an out-of-lane edit (a close-time wall).
- [ ] Commit the status-flip + archival on your own branch (keep your worktree). Signal the
  Orchestrator you're ready to land — open the reply `clean {id}:`; that signal is what mints
  your land grant (never wait on a pre-existing one, never page for one). Once it's minted,
  land it yourself via `land.sh` (§Git Sync above) — paperwork lands the same way as code —
  then remove your worktree + branch and confirm `clean {id}:` once more
- [ ] Report to user: block completion summary, Completion Report path
