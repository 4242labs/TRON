# SUPER-META Session: 2026-02-28 — Shared Skill Creation

**Mode:** Implementation (user-directed — create shared branching skill and update shared-knowledge references)
**Triggered during project:** 42Bros
**Session:** #8 (shared-knowledge portion)
**Executed by Model:** Claude Opus 4.6
**Related log (42Bros):** `42bros/meta/logs/super-meta/log-260228-1629-branching-strategy-implementation.md`

## Summary

Created a new shared skill `skill-branching-strategy.md` in `shared-knowledge/agentic-ai/skills/` and updated `shared-knowledge/meta/agent.md` to register it in the repository structure listing. This skill was extracted from the 42Bros branching strategy block plan (`block-XX-XX-branching-strategy.md`) and generalized for cross-project reuse. All 42Bros agent docs were refactored to reference this shared skill rather than containing generic branching logic inline — those changes are documented in the related 42Bros log.

## Context & Rationale

The 42Bros project needed a branch-per-task workflow (branch → PR → CI → auto-merge → deploy) to eliminate direct-to-main pushes. A block plan existed (`block-XX-XX-branching-strategy.md`) with detailed task breakdowns. During implementation, the user flagged that reusable/generic content must live as a shared skill in `shared-knowledge/agentic-ai/skills/`, with project-specific docs cross-referencing it — matching the established pattern used by `skill-change-tracking.md`, `skill-code-review.md`, and other existing shared skills.

This required splitting the block plan's content into:

- **Shared skill** (this log) — generic branch-per-task workflow pattern applicable to any project
- **Project-specific extensions** (42Bros log) — exact repo names, CI workflow names, git-tag release mechanism, deploy validation procedure

## New File Created

### `shared-knowledge/agentic-ai/skills/skill-branching-strategy.md` (201 lines)

Structured to match existing skill conventions (`skill-change-tracking.md`, `skill-code-review.md` — "When to Use" → procedure → project-specific extensions pattern).

#### Section Inventory

| Section | Lines | Content |
|:--|:--|:--|
| When to Use | 4 | Scope definition: any project with CI/CD and deploy risk on `main` |
| Principles | 7 | 5 principles: main always deployable, ephemeral branches, CI is the gate, agents stay autonomous, incremental adoption |
| Branch Naming Convention | 12 | `feat/`, `fix/`, `chore/` prefixes; lowercase hyphens only; cross-repo identical branch names |
| Repo Classification | 9 | 3-category table (deploy-tracked, IaC, docs/meta) with workflow, protection, and auto-merge columns. Each project defines which repos belong where. |
| Engineer Workflow | 30 | Session Start (determine name, create/checkout branch, resume from handover), During Session (push to branch not main), Session End (PR + auto-merge + CI wait + deploy validation + handover with branch name) |
| Cross-Repo Ordering | 14 | Generic 5-step sequence: merge shared lib → release → update pins → open consumer PRs. Project defines release mechanism (tags, registry, etc.). Hard enforcement: agent MUST NOT open consumer PRs before shared lib is merged AND released. |
| Branch Timeout Policy | 6 | >2 sessions without merge → escalate to user; flaky CI → max 3 retries then escalate; CI timeout → check status page, retry once; abandoned branches → re-escalate each session |
| TRON Integration | 14 | Branch name in session plan, pass to engineer spawn, track PR status in returns, verify all PRs merged at session end |
| Reviewer Integration | 5 | PR diff scope when branch exists (`gh pr diff`), timestamp-based fallback when no branch |
| IaC-Specific Notes | 7 | Structural validation CI only (no state-changing ops); plan/apply manual; user reviews plan before merge; emergency admin bypass for hotfixes |
| Branch Protection Configuration | 14 | Status checks required (for auto-merge to function), no required reviewers, no force push, no deletions, admin bypass enabled (self-lock mitigation for solo devs), auto-delete heads, emergency rollback command |
| Project-Specific Extensions | 8 | 5 extension points: repo classification table, CI workflow names, cross-repo release mechanism, cross-repo ordering details, deploy validation procedure |
| Changelog | 3 | Initial creation entry |

#### Design Decisions

| Decision | Rationale |
|:--|:--|
| No project-specific repo names, org names, or CI file names in shared skill | Must be reusable across any project — 42Bros specifics live in `meta/agents/engineer.md` §42Bros Branching Extensions |
| Cross-repo ordering is generic ("release" not "git tag") | Different projects may use git tags, npm publish, PyPI, etc. — the shared skill describes the pattern, the project defines the mechanism |
| Branch timeout thresholds hardcoded (2 sessions, 3 CI retries) | These are reasonable defaults. A project can override in its own agent docs if needed. |
| Emergency rollback command uses `gh api -X DELETE` | This is the GitHub CLI approach — platform-agnostic projects would need their own equivalent, but GitHub is dominant enough to include directly |
| Admin bypass is the default self-lock mitigation | Documented as essential for solo developers/small teams without a second person to approve overrides |
| Squash merge is the default in Engineer Workflow | `gh pr merge --auto --squash` — keeps `main` history clean. Projects can override if they prefer merge commits. |

## Files Modified in shared-knowledge

### `shared-knowledge/meta/agent.md`

| Area | Change |
|:--|:--|
| §2 Repository Structure — ASCII tree | Added `│   │   ├── skill-branching-strategy.md` to the skills listing, maintaining alphabetical order between `skill-architect-modes.md` and `skill-change-tracking.md` |

This ensures any agent consulting the repository structure map knows the skill exists and where to find it.

## Cross-References Established

The shared skill is now referenced from the following 42Bros files (changes documented in the related 42Bros log):

| File | Reference Type |
|:--|:--|
| `42bros/meta/agents/engineer.md` | Prerequisites (required reading) + §42Bros Branching Extensions (project-specific extensions) |
| `42bros/meta/agents/tron.md` | Prerequisites (§TRON Integration) + session plan + spawn + return tracking + session end |
| `42bros/meta/agents/reviewer-code.md` | Prerequisites (§Reviewer Integration) + PR diff scope |
| `42bros/meta/agents/skills/skill-iac-change.md` | Flow section (§IaC-Specific Notes) + references |
| `42bros/meta/principles.md` | Git — Project Override section |
| `42bros/meta/context.md` | §Branching Convention + agent architecture layering diagram |
| `42bros/42bros-iac/docs/playbook-infra.md` | §4.1 branch naming reference |

## Validation

| Check | Result |
|:--|:--|
| Shared skill follows existing conventions (When to Use → procedure → extensions) | ✅ |
| No 42Bros-specific content leaked into shared skill | ✅ Verified — no `42piratas`, no service names, no repo names |
| All 5 extension points in §Project-Specific Extensions are covered by 42Bros engineer.md | ✅ |
| `agent.md` repository structure listing is alphabetically correct | ✅ |
| Shared skill is self-contained — readable without any project context | ✅ |
| No duplicated content between shared skill and 42Bros agent docs | ✅ — 42Bros docs reference skill sections, don't repeat them |

## Notes

- This is the 6th shared skill in `shared-knowledge/agentic-ai/skills/`. The existing 5 are: architect-guardrails, architect-modes, change-tracking, code-review, decision-records. The branching skill follows the same structural conventions.
- The skill was extracted from a single project (42Bros) but written to be project-agnostic. True cross-project validation will occur when a second project adopts it.
- No self-improvements to SUPER-META's own agent doc were identified this session.
