# Plan: 42agents → 42hq rename + internal restructure

> **⚠ Superseded (2026-07-05):** the `new-project-template/` dir referenced below no longer exists — scaffold templates moved to `tron/tron-app/templates/project-scaffold/`. Retained as a historical record — current state in `agents/super-m/plans/plan-tron-sot-cleanup.md`.

**Status:** ✅ DONE (2026-06-16) — A+B+C complete; 26 sibling PRs merged. Sole holdout: `semdigitar-app` #49 (pre-existing unrelated CI fail). See `agents/super-m/logs/log-260616-1149-42hq-rename-restructure.md`. **Owner:** SUPER-M · **Opened:** 2026-06-16
**Branch:** `chore/super-m-20260616-agent-system`

---

## Goal

Rename canon repo `42agents` → `42hq`, group all agents under `agents/`, consolidate
`shared-knowledge` → `knowledge-base`. Sibling-repo references rewritten in a single later sweep.

## Final tree (canon root, agent internals omitted)

```
42hq/
├── README.md
├── agents/            ← all 14 agent dirs (advisor-legal … sysadmin, incl. i18n)
├── commons/
├── docs-reports/
├── new-project-template/
└── knowledge-base/              ← was shared-knowledge/
    ├── principles-base.md
    ├── meta/  skills/  templates/  reference/  rollouts/  notifications/
    └── kb/                      ← was shared-knowledge/knowledge-base/
        ├── databases/   (+ two-gate-prod-migration-apply-and-drift.md)
        ├── infra/       (+ github-api-unreachable.md)
        ├── frameworks/  (+ nextjs-server-only-in-standalone-script.md)
        └── data-science/  languages/  messaging/  tooling/
```

---

## Locked requirements

**R1 — Rename `42agents` → `42hq`** — local folder + GitHub repo `42piratas/42agents`→`42piratas/42hq`, `origin` URL, migrate Claude memory dir `…-42labs-42agents`→`…-42hq`.
**R2 — Create `agents/`** — move the 14 agent dirs in; commons, docs-reports, new-project-template, README.md, knowledge-base stay at root.
**R3 — `shared-knowledge` → `knowledge-base`** — rename bundle; inner `knowledge-base/`→`kb/`; merge 3 stray root articles into `kb/{databases,infra,frameworks}/`; delete stray root.

---

## Execution

**Pre-step (done):** main checkout had uncommitted in-flight work (alfred inbox + TRON consolidation) in dirs being relocated. Preserved as-is (old paths) before restructure, per user decision — nothing lost. Rebased onto latest `origin/main` after it advanced 3 KB commits mid-session.

**Phase A — canon-internal (this branch):** moves + live-doc reference rewrite (session logs excluded as point-in-time records). Regenerated atop the preserved WIP + latest origin so newly-added KB files and in-flight files relocate too.

**Phase A.1 — ignored-orphan relocate (main checkout):** tracked files move via git; untracked/ignored siblings do not. After landing, physically relocate `super-m/oss/`, `super-m/.claude/`, `alfred/artifacts/`, `shared-knowledge/.worktrees/` (and any other ignored content) to their new `agents/<agent>/` / `knowledge-base/` homes.

**Phase B — rename repo + folder (HELD):** GitHub rename, `origin` URL, local dir rename, worktree repair, `.claude` memory migration.

**Phase C — sibling fan-out (HELD):** rewrite references in ~30 sibling repos in one staged sweep, per each repo's conventions + active-agent safety. Includes `canon_version` drift-resync (canonical skill files' last-change SHA changed → all `source: canon` skills read stale). Reconcile pre-existing root checklists (`RENAME_CHECKLIST.md`, `META_RENAME_CHECKLIST.md`, `CANON_META_PLACEHOLDER_PLAN.md`, `SCRUB_ORCHESTRATION_FROM_PROJECTS_PLAN.md`).

## Risks / notes
- Renaming canon folder breaks absolute paths in existing worktree `.git` files — repair after Phase B.
- `.claude` slug is path-derived; migrate memory before working from the new path.
- Siblings touched exactly once (R1+R2+R3 together) — never split across the external boundary.
