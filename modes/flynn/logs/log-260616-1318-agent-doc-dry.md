# SUPER-M Session: Agent-Doc DRY Pass (scaffold + canon)

**Date:** 2026-06-16
**Mode:** USER-DIRECTED — apply the "agent docs reference, never restate" cleanup to the project-scaffold kit + encode the rule in canon
**Worktrees:** `tron/tron-app/.worktrees/scaffold-dry-agent-docs` (Parts A/B), `42hq/.worktrees/super-m-20260616-agent-doc-dry` (Parts C)
**Executed by Model:** Opus 4.8

---

## Origin

Continues the cross-project agent/process cleanup begun in Hiresling.ai (FIX-01/FIX-02, source-of-truth notes: `hiresling-meta/logs/super-m/log-260610-1040-agent-process-fixes.md`). The scaffold kit was relocated into `tron/tron-app/templates/project-scaffold/` earlier the same day (log `log-260616-1159-relocate-project-scaffold.md`); this session applies the fixes to the kit in its new home and promotes the meta-rule into canon.

Governing principle confirmed against current best practice (progressive disclosure + single-responsibility per file; Anthropic Agent Skills, open standard Dec 2025): **procedures/gates → skills; durable standards → docs; identity/routing → agent doc. One home each.**

---

## Precursor — drift-check fix (tron #46, merged)

`canon-drift-check.sh` assumed a single canon checkout and still pointed at the dead `new-project-template/...` path. Made repo-aware: variadic `REPO_PATH::SKILL_SUBDIR` roots; per-file git history runs in the repo that owns the matched counterpart; `canon-drift.yml` checks out both `42hq` and `tron`. Resolves the deferred drift-check item — Part C no longer carries it.

---

## Part A — reproduce FIX-01 + FIX-02 (tron #47)

- `meta/agents/engineer.md` — collapsed §Block Completion + §Session End narration into pointers (stages 2/5 → `skill-validate`, stage 6 → `skill-session-end`). **89 → 59 lines.**
- **New** `app/docs/guidelines-coding.md` — single home for durable code standards + secure-coding baseline. Wired into engineer always-read, `principles.md §Core Docs`, session-end staleness table, root `CLAUDE.md` Key Files.
- `meta/skills/skill-validate.md` — added §Constraints: single-homes the no-substitute/legal-moves rule + the anti-sycophancy rule (anchored to `principles-base.md §11/§13`).
- `meta/skills/skill-session-end-engineer.md` — added the 6-stage DoD flow map + reading discipline; §Precondition and §1 now reference `skill-validate §Constraints` instead of restating.

## Part B — extend the sweep (tron #47)

- `engineer.md` — §Branching/§Testing/§Security folded into the Standards & procedures pointer block (owning skill/doc each: branching → `skill-worktree-and-branching`; testing gate → `skill-validate`; secure-coding standard → `guidelines-coding`; security scan gate → `skill-security-scan`).
- **Stale-reference fix** in `data-architect.md`, `reviewer-code.md`, `reviewer-security.md`: all three said the critic gate is "Dispatched by `skill-session-end-engineer.md §0.5`" — but §0.5 was removed when session-end became paperwork-only. Corrected to "dispatched by the supervising process on its review cadence (canon Reviewer-trigger map, `principles-base.md §12`)".
- `architect.md` — audited, already clean (pure pointers). No change.

## Part C — encode upstream (42hq, this worktree)

- `knowledge-base/principles-base.md §10 Skill References` — added **Agent docs reference; they never restate**: agent docs carry identity/scope/routing only; procedures live in skills, durable standards in docs, one home each; restating is drift. Framed as the root-cause rule behind progressive disclosure. Changelog + Last Updated bumped.

---

## Part D — reviewer session-start DRY + data-architect (tron #48)

Follow-on de-bloat surfaced while auditing session-start blocks for consistency:

- `reviewer-code.md` / `reviewer-security.md` — the inline notifications/warnings mechanics (list dir, exclude `warnings/`+`archive/`, archive >3 days) restated what the other three agents get via a one-line pointer to `agent.md §3.1+§3.2`. Collapsed to that pointer; kept only the reviewer-specific **delta** (active warning → reproduced as an audit finding).
- `data-architect.md` — added `read pipeline.md` to session start (needs to know what schema/migration work is in flight; engineer + architect already did).
- **Deliberately not done:** worktree-hygiene scan was *not* added to architect/data-architect — the stale-worktree cleanup is engineer/reviewer plumbing and risks confusion with other agents' WIP; design agents only need *branch-before-writing*, already covered by principles rule 2 + the worktree skill.

## Part E — session-start read-only + orphan worktree GC (42hq #102, tron #49)

Root finding: canon itself (`skill-git-multi-agent.md`) prescribed stale-worktree removal at **every** session start — a workaround for unreliable teardown, and the one shared-state mutation in an otherwise read-only bootup (every agent deleting worktrees it didn't create). Split the conflated responsibilities:

- **Session start** = read-only (inspect + conflict check). No removal.
- **Session end** = tear down your *own* worktree (unchanged).
- **Orphan GC** of truly-abandoned worktrees (remote `[gone]` + no open PR + not active) = **single owner: SUPER-M health check (C1)**.

Canon (42hq #102): `skill-git-multi-agent.md` §Setup made read-only; §"Stale cleanup (every session, start and end)" → §"Worktree teardown & orphan GC"; `super-m.md` C1 gained the orphan-GC ownership + prune action. Scaffold (tron #49): mirrored in `skill-worktree-and-branching.md` (step 3 → "Note orphans (read-only)") + `engineer.md` ("Worktree pre-flight (read-only)", removal bullet dropped); reviewers inherit via the §Session-Start Hygiene pointer.

---

## Outcome

| Part | Change | Repo | PR | Status |
|:--|:--|:--|:--|:--|
| precursor | Drift-check repo-aware | tron | #46 | merged |
| A + B | Scaffold agent-doc DRY (engineer collapse, guidelines-coding, validate §Constraints, 6-stage map, §0.5 fix) | tron | #47 | merged |
| C | Canon rule `principles-base.md §10` | 42hq | #100 | merged |
| C (scope) | Dropped cross-project carry-back | 42hq | #101 | merged |
| D | Reviewer session-start DRY + data-architect pipeline read | tron | #48 | merged |
| E | Canon session-start read-only + orphan-GC owner | 42hq | #102 | merged |
| E (scaffold) | Scaffold mirror of read-only session-start | tron | #49 | merged |

No behavioral content lost — every moved item verified to have a single home. Cross-reference sweep clean **against `origin/main`** (no `new-project-template` leftovers, no live `§0.5` dispatch refs, no residual stale-worktree-removal wording; all referenced skill sections exist). Note: local main checkouts were behind origin and showed stale hits — origin/main is the verified truth.

---

## Scope note

Canon rule (`principles-base.md §10`) + the project-scaffold kit are updated, so every newly scaffolded project inherits the DRY shape. Retrofitting existing live projects is **out of scope** and intentionally not tracked here.
