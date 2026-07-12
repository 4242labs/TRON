# MEMO — Align to the TRON source-of-truth canon (action required)

**Date:** 2026-07-05 · **From:** SUPER-M (42hq canon) · **To:** every 42Labs project

The scaffold canon moved. The old `new-project-template` kit is **retired**. The git-hook + `setup-repo.sh`
templates and the project-scaffold payload now live in the **TRON** repo (`4242labs/tron`,
`templates/project-scaffold/`). `42hq/knowledge-base/` stays the **runtime canon** (principles + shared skills).

Bring this project into compliance. **Each item = its own branch + PR** per your Git rules — never commit
direct to a protected branch. Skip anything already done.

## Checklist

1. **Repoint canon citations.** Replace any reference to `42hq/new-project-template/…` or
   `42hq/knowledge-base/templates/{hooks,setup-repo.sh}` with the TRON path:
   - setup-repo → `tron/tron-app/templates/project-scaffold/templates/meta/scripts/setup-repo.sh`
   - hooks → `tron/tron-app/templates/project-scaffold/templates/meta/.githooks/{pre-commit,pre-push}`
   - scaffold/services templates → `tron/tron-app/templates/project-scaffold/templates/…`
   Leave dated `logs/` and `archive/` untouched (history).

2. **Agent-doc filename → `AGENTS.md`.** Rename `CLAUDE.md` → `AGENTS.md` at the workspace root, meta repo,
   and `app/` (model-agnostic, canon scaffold v1.3.0). Fix every internal reference to the renamed file.
   If an `AGENTS.md` stub already exists (Next.js), merge into it — don't clobber the managed block.

3. **Drift-check must be repo-aware.** `scripts/canon-drift-check.sh` + `.github/workflows/canon-drift.yml`
   must be TRON's repo-aware version that checks out **both** `42piratas/42hq` (private) and `4242labs/tron`
   (public) and calls the script with two roots:
   `canon-kb::knowledge-base/skills` and `canon-scaffold::templates/project-scaffold/templates/meta/skills`.
   **Set the `CANON_READ_TOKEN` repo secret** (read access to private 42hq) or the check can't run.
   If you have no drift-check at all, adopt it — silent skill drift is worse than none.

4. **Re-pin moved skills.** For any skill marked `source: canon` whose canonical counterpart moved
   42hq → TRON, re-base its `canon_version` to the owning TRON commit, so drift-check compares against the
   right repo (otherwise it reports false drift / errors).

5. **`setup-repo.sh` + hooks are copies.** They keep working as-is. When you next touch them, reconcile
   against the TRON SoT version — or document any deliberate override (e.g. a lefthook bridge) in the PR.

## Reference
Full change map, rationale, and per-project status: `42hq/agents/super-m/plans/plan-tron-sot-cleanup.md`.
Questions → run a SUPER-M `UPGRADE PROJECT` session, which executes this checklist for you.
