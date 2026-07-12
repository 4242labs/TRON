# SUPER-M Session: Relocate project-scaffold kit (canon → tron)

**Date:** 2026-06-16
**Mode:** USER-DIRECTED — template relocation + rename (precursor to scaffold fix/enhance work)
**Executed by Model:** Opus 4.8
**Worktrees:**
- canon: `42hq/.worktrees/chore-super-m-20260616-template-edit` (branch `chore/super-m-20260616-template-edit`)
- tron-app: `tron/tron-app/.worktrees/chore-add-project-scaffold` (branch `chore/add-project-scaffold`)

---

## Purpose

Relocate the 42Labs project-scaffold template kit out of canon into the `tron` repo, and rename it. Precursor to the canon-reproduction/extension work specified in hiresling-meta PR #760 log (`log-260610-1040-agent-process-fixes.md` §Canon Reproduction & Extension Plan) — that fix/enhance work will now target the kit in its new home, not `42hq/new-project-template/`.

**User decisions (this session):**
- Destination: `tron/tron-app/templates/project-scaffold/`
- Rename: `new-project-template` → `project-scaffold`
- 42hq side: repoint operational refs (kit relocates; SUPER-M still owns scaffolding)
- Path reconciliation confirmed by user: `42agents`→`42hq`, `shared-knowledge`→`knowledge-base`

---

## What was done

### tron-app (receives kit) — PR https://github.com/42piratas/tron/pull/45
- Worktree off `origin/main` (isolates the 9 unrelated WIP files already in the tron-app checkout — not touched).
- Exported the 62 git-tracked kit files via `git archive` (exact tracked content) into `templates/project-scaffold/`.
- Kit-internal rename fixes: `CHANGELOG.md` title; `templates/app/services-setup.md` canon-path refs (`42hq/new-project-template/` → `tron/tron-app/templates/project-scaffold/`).
- Scoped `.gitignore` negation: tron-app ignores `.claude/` globally, which swallowed the kit's `templates/.claude/settings.json` payload template. Added `!templates/project-scaffold/templates/.claude/` + the file, so the kit ships complete.
- 62 kit files + `.gitignore` committed.

### 42hq (canon, removes kit) — PR https://github.com/42piratas/42hq/pull/99
- `git rm` `new-project-template/` (62 files).
- Repointed live operational refs to the new tron location:
  - `agents/super-m/super-m.md` (L174 templates source-of-truth)
  - `agents/super-m/skills/skill-project-scaffold.md` (L9, L28)
  - `agents/super-m/skills/skill-project-upgrade.md` (L7, L21)
  - `agents/product-designer/skills/skill-backlog-entry.md` (L26 canonical backlog-row source)
  - `README.md` — `## new-project-template/` section → pointer to tron location
- Historical records intentionally left with the old name (document past sessions): super-m.md changelog (L347), `agents/super-m/plans/*`, `knowledge-base/rollouts/2026-05-05-*`, `docs-reports/SCRUB_ORCHESTRATION_FROM_PROJECTS_PLAN.md`, `logs/*`.

---

## Sequencing

tron PR #45 must merge **before** 42hq PR #99 — the repointed canon refs depend on the new location existing. Both left unmerged per user rule (open PR, then STOP).

---

## Flagged / deferred decisions

1. **drift-check CANON_SKILL_DIRS** — `project-scaffold/templates/meta/scripts/canon-drift-check.sh` L31 still lists `new-project-template/templates/meta/skills` as a canonical search root. Updating it requires deciding what "canon repo" means now that the canonical skills live in the `tron` repo, not `42hq` (the script takes a single `<canon-repo-path>` arg). Left for the scaffold fix/enhance pass. The other canonical root (`knowledge-base/skills`) is unaffected.
2. **Claude attribution in the `tron` repo** — tron PR #45 commit + PR body carry the harness-mandated `Co-Authored-By: Claude Opus 4.8` trailer and "Generated with Claude Code" footer. This sits in tension with the standing TRON rule (never name Claude/host-runtime in TRON-facing material). Treated the trailer as engineering provenance (not product copy) and kept it; flagged for user to scrub if they want tron history runtime-agnostic.

---

## Next (the actual fix/enhance work — NOT started)

Per the hiresling work order, now retargeted to `tron/tron-app/templates/project-scaffold/`:
- **Part A** — reproduce FIX-01 (collapse engineer.md DoD/session-end narration → pointer; single-home rules in skill-validate §Constraints + skill-session-end 6-stage map) + FIX-02 (extract code standards → `app/docs/guidelines-coding.md`; add to always-read).
- **Part B** — extend cleaning: pull engineer.md inline §Branching/§Testing/§Security/§Code-Standards extras into owning skills/docs; sweep architect.md, data-architect.md, reviewer-code.md, reviewer-security.md.
- **Part C** — encode upstream in `knowledge-base/principles-base.md` ("agent docs reference skills/docs; never restate"); log initiative in super-m backlog + plans.
- **Carry-back** — HS super-m-local.md persistent state; confirm Part B fold targets.
