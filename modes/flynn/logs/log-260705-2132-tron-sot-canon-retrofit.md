# SUPER-M session log — 2026-07-05 — TRON-as-SoT canon migration + fleet retrofit

**Mode:** CREATE AGENT (task 1) + canon migration/retrofit (task 2). **Branch:** `chore/super-m-20260705-retrofit` (this log) and earlier `chore/super-m-20260705-agent-edit` / `-doc-fix`.

---

## Task 1 — PESSOA template streamline (done, merged)

Applied the TRON lean-doc pattern to `agents/pessoa/pessoa.template.md` (agent file is a thin router; substance referenced not restated): collapsed the duplicate "What PESSOA Is"/Role split, merged the two overlap paragraphs, fixed checkbox discipline, trimmed KB RAG prose, dropped duplicated citations. Kept the 15 Principles. **PR #132 merged** (`f5b8ba7`).

---

## Task 2 — Retire the old canon scaffold template; make TRON the single source of truth

### The two canons (do not conflate)
1. **Scaffold-template payload** (`new-project-template` kit) — already **relocated** into TRON (`4242labs/tron`, `templates/project-scaffold/`) by commit `250645e`. No copy remains in 42hq.
2. **Runtime canon** (`42hq/knowledge-base/`) — principles-base, shared skills, reference — **stays** in 42hq.

### What was found
- The scaffold skill (`skill-project-scaffold.md`) already sourced most payload from TRON, but still pulled **git hooks + `setup-repo.sh` from `knowledge-base/templates/`** — a back-reference loop, and those files were **duplicated + diverged** between 42hq and TRON.
- TRON's copies were leaner but its **hooks were weaker** (branch-name guard only; missing the worktree-mandatory + `.repo-class`/`.integration-branch` enforcement that `principles-base §14` requires). TRON's `setup-repo.sh` also dropped the CI short-circuit + git≥2.48 guard.
- Fleet-wide: 5 on-disk projects (ganttflow, hiresling, lens, semdigitar, zovv) carried dead `new-project-template/…` refs, stale `knowledge-base/templates/setup-repo.sh` "canon source" citations, pre-v1.3.0 `CLAUDE.md`, and (3 of them) a broken `canon-drift-check.sh` (dead search-root). tron-flynn is decoupled tooling.

### Decisions (user-directed)
- **TRON = SoT** for all scaffold payload (hooks, setup-repo, templates). KB duplicates deleted; refs repointed to TRON.
- Preserve enforcement: **ported the two setup-repo guards** into TRON's lean version, and **adopted the full canon enforcement into TRON's hooks** (so SoT ≠ regression).
- **`CLAUDE.md` → `AGENTS.md`** fleet-wide (canon v1.3.0 convergence), cross-refs fixed, dated logs/archive left as history.
- **`canon-drift-check.sh`** → adopt TRON's repo-aware version (scans `42piratas/42hq` **and** `4242labs/tron`); added it to the 2 projects that lacked it.
- Off-disk projects: **not cloned/backfilled** — instead a **compliance memo** pasted in each on-disk project root + master in 42hq; off-disk self-align via `UPGRADE PROJECT`.
- Historical docs (resolved rollout, scrub report, superseded plans): **superseded banners**, internals not rewritten.

### Shipped — 13 PRs, all MERGED + cleaned + synced
| Repo | PR | Content |
|---|---|---|
| 42piratas/42hq | #133 (`2ca181c`) | KB hook/setup-repo dupes deleted (−245 lines); 6 canon refs → TRON; scaffold step 4b de-looped; stray `42hq/kb/` merged into `knowledge-base/kb/frameworks/`; `ref-*.md` count 4→3; scaffold-skill `CLAUDE.md`→`AGENTS.md`; §14 changelog row; 5 superseded banners; `plan-tron-sot-cleanup.md`; `memo-tron-canon-compliance.md` |
| 4242labs/tron | #108 | setup-repo CI+git-version guards; hooks adopt full worktree-mandatory enforcement; README/GETTING_STARTED/blueprint-contracts repointed off `new-project-template` |
| ganttflow-meta / -app | #62 / #41 | canon-source repoint; CLAUDE→AGENTS; **added** repo-aware drift-check; token memo |
| hiresling-meta / -app | #961 / #1101 | canon-source + drift-check repoint; CLAUDE→AGENTS (app; workspace-root renamed loose); #1101 had a conflict — rebased on staging, resolved, CI-passed |
| lens-meta / lens / lens-my | #126 / #20 / #89 | canon-source + drift-check repoint; CLAUDE→AGENTS (app AGENTS.md stubs merged, not clobbered) |
| semdigitar-meta / -app | #105 / #59 | canon-source + drift-check repoint; CLAUDE→AGENTS |
| zovv-meta / -app | #67 / #27 | canon-source repoint; **added** drift-check; CLAUDE→AGENTS; token memo |

State: 42hq main `2ca181c`; all project integration branches FF-synced; no leftover migration branches/worktrees.

---

## Operator TODO (only the user can do)
- **Set `CANON_READ_TOKEN` secret** in `ganttflow-meta` and `zovv-meta` (fine-grained PAT, `contents: read` on `42piratas/42hq`). Each repo has `ACTION-set-CANON_READ_TOKEN.md`. Until set, their new drift-check CI fails at the canon-checkout step. (The other 3 already have it.)

## Deferred / delegated (in the compliance memo, per project via UPGRADE PROJECT)
- **`canon_version` re-pin** for `source: canon` skills whose canonical moved 42hq→TRON — needs the skill re-sync too (judgment-heavy; not a blind script). Until done, drift-check may report noise on those skills.
- **`setup-repo.sh`/hooks reconcile** against the TRON SoT on next touch (or document a deliberate override, e.g. hiresling's lefthook bridge).
- **8 off-disk registry projects** (NordGrid, Jubs, NordLens, Outreach, 42labs.io, Alfred, Aggregator, tron-www) — same backfill when next checked out.

## Parked decisions (Part-5 of the change map — user to discuss)
- P-06: move the scaffold *procedure* (`skill-project-scaffold`) into TRON, or keep it SUPER-M-owned (payload in TRON, procedure in SUPER-M)?
- Is hiresling's lefthook bridge a sanctioned per-project override of the SoT?

## Notes / hygiene
- Backlog item #1 (merge Analyst-Marketing + Analyst-SEO-GEO) still open — logged in `agents/super-m/backlog.md`.
- The clean-sweep pruned 4 already-merged local branches in `hiresling-meta` (PRs #946/#947/#960/#962 — no work lost; user's active branch untouched). Lesson: scope branch-prune to the migration's own branches, not all `[gone]` branches.
- Local `42hq/.claude/settings.local.json` superseded by the now-tracked origin copy (old backed up in job tmp).

## Reference
Full change map: `agents/super-m/plans/plan-tron-sot-cleanup.md`. Compliance memo: `agents/super-m/plans/memo-tron-canon-compliance.md`.
