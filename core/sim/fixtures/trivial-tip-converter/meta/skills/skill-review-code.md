---
name: skill-review-code
description: Code reviewer's full audit procedure for trivial-tip-converter — correctness, tests, doc drift.
source: project
---

# Skill: Code Review — Trivial Tip Converter

Read this file **now** — do not rely on memory.

---

## Mindset

You are a **critical technical reviewer** operating in a separate session from the code author.
Your purpose is to find issues, not to validate work. Assume nothing is correct until proven
otherwise.

- **Skeptical:** Question every decision.
- **Independent:** Do not defer to the author's logic.
- **Thorough:** Incomplete reviews are worse than no reviews.

You are NOT a rubber stamp.

---

## Phase 1 — Load Context

Before reviewing, read:

- [ ] `principles.md` — project rules
- [ ] `context.md` — project scope, stack, constraints
- [ ] Active block plan(s) in `blocks/` relevant to the reviewed scope

---

## Phase 2 — Scope Materialization

1. Define the scope (files changed since last review, or user-specified scope)
2. Build a file manifest — every file in scope must be read in full
3. Record findings OR explicit `no issues` per file — no file may be silently absent

```
## Manifest

{N} files in scope:
1. {file_path} — {brief description of change}
2. ...
```

---

## Phase 3 — Audit Checklist

### 3.1 — Security surface

This project has **no auth, no database, and no external integrations** — the security checklist
is narrow:

| Check | Severity | Reference |
|:------|:---------|:----------|
| **Secrets:** No hardcoded tokens/keys anywhere in the tree | BLOCKER | `principles.md` |
| **Input validation:** Form inputs (bill amount, tip %, party size, miles, °C) degrade gracefully on non-numeric / negative input — no thrown error reaching the rendered page | HIGH | `src/app/converter-form.tsx` |
| **Dependency pinning:** New npm packages pinned to specific versions in `package.json` | HIGH | — |

### 3.2 — Domain Logic

| Check | Severity | Reference |
|:------|:---------|:----------|
| **Pure functions:** `src/lib/*.ts` stays free of React/DOM imports — testable in isolation | BLOCKER | `context.md` |
| **Rounding:** Currency and unit-conversion results round to 2 decimal places consistently | MEDIUM | `src/lib/tip.ts`, `src/lib/convert.ts` |

### 3.3 — Frontend

| Check | Severity | Reference |
|:------|:---------|:----------|
| **No business logic in components** — `src/app/*.tsx` imports from `src/lib/`, never reimplements the math | BLOCKER | `context.md` |
| **Offline build** — no `next/font/google` or other remote-fetching import anywhere in `src/app/` | BLOCKER | `context.md §Constraints` |

### 3.4 — Testing

| Check | Severity | Reference |
|:------|:---------|:----------|
| **Test coverage** — every exported function in `src/lib/` has at least one Vitest assertion | BLOCKER | `principles.md` |
| **Test quality** — tests verify behavior (specific expected values), not just "doesn't throw" | HIGH | — |
| **Edge cases** — zero/negative inputs tested where the function's contract defines behavior for them | MEDIUM | — |

### 3.5 — Documentation Drift

| Check | Severity | Reference |
|:------|:---------|:----------|
| **`README.md`** matches actual build/test/dev commands | HIGH | — |
| **Block plans** accurately describe what was implemented | MEDIUM | — |

---

## Phase 4 — Output

**The Completeness section is a GATE. If `matches manifest` is `NO`, the review is incomplete —
cover the missing files before finalizing.**

```
## Completeness

- Manifest: {N} files
- Reviewed with findings: {X} files
- Reviewed — no issues: {Y} files
- **Total reviewed: {X+Y} — matches manifest: YES/NO**

## Review Summary

**Files Reviewed:** X
**Issues Found:** Y (Z blockers)

### Blockers (must fix)
- Issue 1 brief description

### High Priority
- Issue 2 brief description

### Medium / Low
- Issue 3 brief description

### Verdict
[ ] APPROVE — No blockers, code meets standards
[ ] APPROVE WITH COMMENTS — Minor issues, acceptable to merge
[ ] REQUEST CHANGES — Blockers found, must address before merge
```

**Output log:** `logs/review-code/YYMMDD-HHMM-review-{scope}.md`

---

## Severity Levels

| Level | Meaning | Action |
|:------|:--------|:-------|
| **BLOCKER** | Active bug or hard architecture-rule violation | Fix immediately |
| **HIGH** | Significant quality or correctness issue | Fix in this session |
| **MEDIUM** | Code quality gap, missing validation | Fix if quick, defer with user approval only |
| **LOW** | Style, naming, minor improvement | Defer unless trivial |

**All findings must be fixed.** The reviewer does not defer findings to `pipeline.md`. If a finding
would pose significant risk or cost to fix, the reviewer flags to the user. Only with explicit user
approval does any item go to `pipeline.md` as `[REVIEW-DEBT]`.

---

## Files Quick Reference

```
Standards (read before every review):
  principles.md
  context.md

Agent docs:
  agents/reviewer-code.md

Output:
  logs/review-code/
```
