---
name: skill-validate
description: Local + post-merge validation gate for trivial-tip-converter — concrete commands, evidence, and the Completion Report format.
source: project
---

# Skill: Validate

Read this file at every invocation — do not rely on memory from session start.

---

## When to Use

Two checkpoints, same procedure: pre-merge local validation, and post-merge re-validation on `main`
(`principles.md §Workflow`).

---

## 1. Build Hygiene — Concrete Commands

Run from the repo root:

```bash
npm install     # first run only, or after a package.json change
npm run build   # next build — must be offline-green (no remote font, no network calls)
npm test        # vitest run — every acceptance criterion with a `test:` verification method
```

If any check fails → STOP. Fix it before continuing. No silent-PASS-with-caveats.

---

## 2. Visual / Behavioral Check

This project ships no browser-automation MCP config — visual checks are manual:

```bash
npm run dev   # dev server; port from $PORT (see .env.example), no hardcoded literal port
```

Open the page, exercise the tip calculator and unit converter forms, confirm the displayed values
match a hand-computed expectation. Required for any block that touches `src/app/` (UI).

---

## 3. Project-Specific Audits

| Audit | Trigger | Procedure | Severity gate |
|:--|:--|:--|:--|
| Input validation | Form fields accept user input | Confirm non-numeric / negative input degrades gracefully (no thrown error reaching the UI) | HIGH unresolved → STOP |

No other project-specific audits apply — this project has no auth, no database, no external
integrations, and no deploy check.

---

## 4. Completion Report — Where It Lives

The Completion Report **is** the session-end log — there is no separate completion-report file. It
is the `## Completion Report` section of the engineer's session log
(`logs/engineering/log-YYMMDD-HHMM-{block-id}-{slug}.md`). The pre-merge invocation writes that
section; the post-merge invocation appends a `## Completion Report (post-merge)` section to the
same log.

Format:

```
## Completion Report

| AC | Criterion | Verification method | Result |
|:--|:--|:--|:--|
| AC-1 | ... | cmd:npm run build | PASS |
| AC-2 | ... | test:tip.test.ts | PASS |

**Evidence:** {command output / test summary}
```

---

## 5. Post-Local-Validation Hand-off

After local validation completes clean:

- Produce a **User Verification List** as a section at the bottom of the block doc:

```
## User Verification Required

1. {what to check} — {URL / page} — evidence: {command output / manual check description}

No items require user verification: [ ] (check only if truly nothing needs visual/manual testing)
```

Hand off to the user. Do not merge until the user signs off.

---

## 6. Post-Merge Hand-off

After post-merge re-validation completes clean on `main`:

- Engineer self-attests against the Completion Report
- Hand off to the user acknowledgment gate (`skill-session-end-engineer.md §1`)
- If a regression is found → do not flip status; open a new feature branch and re-enter the flow
  from step 1

---

## Constraints

These bind every validate invocation:

- **No silent scope downgrade / legal moves.** "Cannot verify → I'll explain why and substitute
  alternative evidence" is forbidden. `UNVERIFIED` is a hard stop. When a contracted Verification
  method cannot run, the only legal moves are: (a) complete as specified, (b) negotiate the spec
  with the user, or (c) escalate and STOP.
- **No capitulation on a verified PASS.** If the user pushes back on a criterion that passed
  without producing new evidence, do not flip it or soften the report — re-state the evidence.
  Re-open a criterion only when the user supplies new evidence.
