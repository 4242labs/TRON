# Plan: Hiresling.ai — Git Flow Update

**Created:** 2026-04-19
**Execution order:** independent — can run before or after repo split. A second pass on worktree paths is required after the repo split lands (see Out of scope).

---

## Why

`skill-worktree-and-branching.md` points to two deprecated shared skills and is missing rules now required by `skill-git-multi-agent.md`: rebase-before-push, CI monitoring, `--force-with-lease`, stale branch detection, PR-merged guard before cleanup, and rebase conflict resolution. Branch naming examples also use uppercase block IDs throughout, which fails commitlint.

---

## Files to change

### 1. `meta/skills/skill-worktree-and-branching.md`

- [ ] Replace canonical references (top section) — point to `skill-git-multi-agent.md` instead of the two deprecated files
- [ ] Fix all branch naming examples: `B{phase}` → `b{phase}` (lowercase throughout)
- [ ] Add rebase-before-push as an explicit rule
- [ ] Add CI monitoring step after push: `gh pr checks {PR} --watch` — do not proceed until green
- [ ] Add `--force-with-lease` to re-push recipe; add rebase conflict resolution one-liner
- [ ] Add stale branch detection: after `git fetch --prune`, run `git branch -vv` — `[gone]` = stale
- [ ] Add PR-merged guard before `git branch -D`: `gh pr view {PR} --json state --jq '.state'` must return `MERGED`
- [ ] Add note: worktree path convention will be updated after repo split lands

### 2. `meta/principles.md`

- [ ] Line 47: `feat/B06-13-github-actions-ci` → `feat/b06-13-github-actions-ci`
- [ ] Line 48: `chore/B06-adhoc-worktree-foundation` → `chore/b06-adhoc-worktree-foundation`

---

## Out of scope

- Worktree base path update (`~/Spaceship/Hiresling.ai--{branch}` → new parent-dir path) — blocked on repo split; a second pass on `skill-worktree-and-branching.md` is required after `plan-hiresling-repo-split.md` executes
- Agent doc updates — each agent doc references `skill-worktree-and-branching.md` as the single entry point; no individual agent docs need changes

---

## Execution notes

- Branch: `chore/adhoc-git-flow-update`
- Worktree: per convention
- No app code changes — meta-only; still requires PR → staging per principles
