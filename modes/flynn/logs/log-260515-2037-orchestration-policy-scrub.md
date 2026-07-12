# SUPER-M Session: 2026-05-15

**Mode:** AUDIT (canon-wide drift) + FIX (multi-repo scrub)
**Project:** canon + 8 consumer projects (zovv, ai-aggregator, jubiscreu, lens, nordgrid, semdigitar, nordlens, vault) + memos for 2 deferred (alfred, hiresling.ai)

## Workflow Health Summary

Canon-wide orchestration-policy leakage caught and scrubbed. Every project that inherited from `new-project-template` carried concurrency caps + reviewer cadence + dead skill refs baked into core docs — orchestration policy belongs to the orchestrator (operator at runtime, OR TRON's `workflow.md` in TRON mode), not project core docs. 14 PRs merged + 3 workspace direct edits + 2 high-severity warnings filed for the deferred projects.

## Pulse Check

| Item | Status | Detail |
|:--|:--|:--|
| Session log quality | ✅ OK | All PRs have full descriptions + precedent links |
| Pipeline staleness | n/a | Cross-project sweep, no single-project pipeline touched |
| Code review freshness | n/a | Drift-fix sweep, no domain code touched |
| SUPER-M gap | 0 days | Last super-m session 2026-05-15 (`log-260515-1100-strip-old-tron.md`) |

## Deep-Dive: Orchestration-policy leakage (Findings A + B + C)

### Finding A — Orchestration policy embedded in core docs

| Where | Pattern | Why wrong |
|:--|:--|:--|
| `principles.md` | `## TRON (if enabled)` Max-N concurrent line | Operator decides at runtime; TRON's `workflow.md` decides in TRON mode. Two-source contradiction. |
| `principles.md` Skills Registry | `Review Cycle` cadence trigger ("Post-phase or post-block-set") | Same — cadence is orchestrator's call, not a project rule. |
| `agents/reviewer-security.md` | `## Review Cadence` section ("at least once per pipeline phase") | Same. |
| `skills/skill-session-end-engineer.md` | `(post-phase or post-block-set)` cadence parenthetical | Same. |
| Workspace-root `CLAUDE.md` | Skills table Review Cycle cadence trigger | Same. |

### Finding B — Spurious `architect-local.md`

Zovv-only drift: every project ships `architect.md` as a full agent doc; `*-local.md` is reserved for project wrappers over canon agents with no project specialization (e.g. `super-m-local.md`). Zovv's first-architect-run authored `architect-local.md` instead. Precedent: `42labs.io` caught + fixed the same drift earlier (PR #8).

### Finding C — Dead `skill-tg-comms.md` references

Skill file was removed from canon; references remained in `engineer.md` / `reviewer-code.md` / `reviewer-security.md` prereq checklists, `services-setup.md` TRON section, plus stragglers in handover docs + super-m-local TODOs.

### Findings caught only post-merge (case-insensitive sweep)

| Project | Missed by initial audit | Reason |
|:--|:--|:--|
| alfred | `agents/super-m-local.md:35` second `## TRON (if enabled)` section | Initial audit only checked `principles.md` for the TRON section pattern |
| hiresling.ai | `hiresling-meta/principles.md:120` lowercase `(post-phase or post-block-set)` | Initial audit was case-sensitive (`Post-phase` only) |

Amended in PR #58 (42agents).

## Execution table

| # | Repo | PR | Scope | Status |
|:-:|:--|:-:|:--|:-:|
| 1 | zovv-meta | #5 | Finding A scrub (pilot) | ✅ |
| 2 | 42agents | #55 | Canon: Finding A scrub on `new-project-template` + `principles-base.md` | ✅ |
| 3 | zovv-meta | #6 | Findings B + C (architect-local + tg-comms) | ✅ |
| 4 | 42agents | #56 | Canon: Finding C scrub on `new-project-template` agent files + services-setup | ✅ |
| 5 | 42agents | #57 | Warnings filed for alfred + hiresling.ai | ✅ |
| 6 | nordgrid-meta | #30 | Finding A (reviewer-security Review Cadence) | ✅ |
| 7 | nordlens-meta | #30 | Finding A (cadence trigger) | ✅ |
| 8 | jubiscreu-meta | #12 | Finding C (block doc handover line) | ✅ |
| 9 | semdigitar-meta | #69 | Finding A (Skills trigger + session-end-engineer) | ✅ |
| 10 | lens-meta | #72 | Findings A + C | ✅ |
| 11 | vault-meta | #6 | Finding A | ✅ |
| 12 | aggregator-meta | #1 | Findings A + C | ✅ |
| 13 | aggregator-app | #3 | Finding C (services-setup) + Finding A leak (Max-2 step) | ✅ |
| 14 | 42agents | #58 | Warnings amend (missed case-insensitive hits) | ✅ |

Workspace-root `CLAUDE.md` direct edits (untracked): `zovv/`, `lens/`, `vault/`, `ai-aggregator/`.

## Recommendations

1. **(severity: high) Alfred + hiresling.ai warnings are live.** Their next agent session (any role) will surface the warning at session-start (per `principles-base.md §9`) and block feature work until the scrub PR lands. Watch the warnings/ dir for archival.
2. **(severity: medium) `services-setup.md` TRON section is structurally leakage.** Per `super-m/skills/skill-project-profile.md:11`, TRON seeds itself when activated; scaffold/audit/upgrade flows should not pre-create `tron.md` / `skill-tg-comms.md`. Today's PRs removed dead step 5 + step 6, but step 4 ("Add `tron.md` to `meta/agents/` — copy from `42agents/new-project-template/templates/meta/agents/tron.md`") references a file that does NOT exist in canon either. Worth a follow-up canon PR to either delete the whole section or replace it with a pointer to TRON's own seed flow.
3. **(severity: low) Case-sensitive audits are a known footgun.** This session's residual hits were both case-variants. SUPER-M's audit skills should default to case-insensitive for prose patterns. Worth a small `skill-audit.md` note.
4. **(severity: low) Jubiscreu's `meta/blocks/handover-reviewer-code.md` is residual TRON v0.2 dispatch infrastructure.** Today's PR removed the dead skill-tg-comms reference but kept the file. The whole `## IF YOU'RE TRON:` branch is stale under TRON v0.3 (session-resume, not block-doc handovers). Retire-or-keep is the project owner's call, not super-m's — flagged in PR #12 body.

## Self-Improvements Applied

| # | Target | Change | Rationale |
|:--|:--|:--|:--|
| 1 | `skill-audit.md` (not yet applied — recommendation only) | Default audit greps to case-insensitive for prose patterns | Today's residual hits were both case-variants of patterns the initial sweep matched only one form of |

## Next Run

- **Recommended:** when next consumer-project session starts (any of: alfred, hiresling.ai, jubiscreu, lens, nordgrid, semdigitar, nordlens, vault) — surface this session log's recommendations + close out warnings if alfred/hiresling have shipped their scrub.
- **Next deep-dive category:** C3 (Pipeline & Block Plan Health) on the next pivotal project session — orchestration is now sterilized, so C2/C3 are the natural next targets.

---

## Linked artifacts

- Plan file: `~/42labs/SCRUB_ORCHESTRATION_FROM_PROJECTS_PLAN.md` (workspace-root, not tracked)
- Warning files (active): `shared-knowledge/notifications/warnings/warning-260515-super-m-{alfred,hiresling}-orchestration-scrub.md`
- PR thread: zovv-meta #5 + #6, 42agents #55-#58, nordgrid-meta #30, nordlens-meta #30, jubiscreu-meta #12, semdigitar-meta #69, lens-meta #72, vault-meta #6, aggregator-meta #1, aggregator-app #3
