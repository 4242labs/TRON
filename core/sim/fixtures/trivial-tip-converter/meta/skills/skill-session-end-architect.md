---
name: skill-session-end-architect
description: Architect close-out — record decisions/ADRs, Core Docs staleness, git sync, session log.
source: project
---

# Skill: Architect Session End

**This skill runs only when the user explicitly triggers session-end.** Do not run automatically
after any check passes or because the conversation feels "done." See `principles.md §Workflow`.

Read this file **now** — do not rely on memory from session start.

---

## 1. Validation

- [ ] Verify all outputs are complete and actionable
- [ ] Verify the user approved any significant decisions

## 2. Record Decisions

- [ ] Lightweight decisions → note in session log
- [ ] Significant decisions → full ADR in `logs/architecture/adr-YYMMDD-{title}.md`
- [ ] Check: do any prior ADRs in `logs/architecture/` need to be marked superseded?

## 3. Core Docs Staleness Check

**Answer each explicitly in the session log. Do not skip any row.**

| Doc | Affected? | Updated? |
|:----|:----------|:---------|
| `context.md` | YES / NO | ✅ / N/A |
| `pipeline.md` | YES / NO | ✅ / N/A |
| `principles.md` | YES / NO | ✅ / N/A |
| `README.md` | YES / NO | ✅ / N/A |

## 4. Git Sync

Follow `principles.md §Git & Branching` — your own worktree + branch, landed via grant + `land.sh`;
never commit or check out `main` directly (the root checkout stays detached); this repo has no
remote, so no PR.

## 5. Logging

- [ ] Create session log at `logs/architecture/log-YYMMDD-HHMM-{description}.md` using the
  **session-log format** in `ref-session-log-format.md`
- [ ] Final checklist for user — numbered list of remaining decisions or actions
