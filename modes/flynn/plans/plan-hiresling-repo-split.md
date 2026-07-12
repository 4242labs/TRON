# Plan: Hiresling.ai Repo Split

**Decided:** 2026-04-19
**Executed from:** `~/Spaceship/` (NOT from inside `hiresling.ai/` — see step 6 note)

---

## Why

Meta commits pollute app git history. CI fires on pipeline/log changes. PR history mixes code with workflow housekeeping. Separating gives each concern a clean, independent history.

---

## Target layout

```
~/Spaceship/hiresling.ai/     ← parent dir (not a repo)
  hiresling-app/              ← git repo (GitHub: hiresling-app)
  hiresling-meta/             ← git repo (GitHub: hiresling-meta)
```

## hiresling-meta/ internal structure: Option A

Files land at repo root — no `meta/` prefix:
`hiresling-meta/pipeline.md`, `agents/`, `blocks/`, `logs/`…

---

## Pre-flight

- ✅ No open PRs
- Full worktree + branch audit: `git worktree list` and `git branch -vv` — remove ALL stale worktrees and local branches (not just the known one)
- Remove stale worktree: `~/Spaceship/worktrees/hiresling-b42-02`
- `cd ~/Spaceship/` before proceeding — the shell must NOT be inside `hiresling.ai/` during Phase 2 (directory rename kills the CWD)
- Close all Claude sessions

---

## Phase 1 — Extract & rewrite history

1. Clone current repo to scratch: `git clone ~/Spaceship/hiresling.ai/ ~/Spaceship/hiresling-meta-scratch/`
2. Run `git filter-repo --path meta/ --path-rename meta/:` inside `hiresling-meta-scratch/` — this rewrites history so only meta commits survive and files land at repo root (no `meta/` prefix). Rename the directory: `mv hiresling-meta-scratch hiresling-meta/`
3. Run `git filter-repo --path meta/ --invert-paths` inside `hiresling.ai/` — removes `meta/` from app history entirely
4. Verify tag `live-260408` is preserved in the **app repo only** (`git tag -l` inside `hiresling.ai/`); re-tag if missing. No expectation this tag exists in `hiresling-meta/` — it's a release tag on an app commit.
5. Force-push rewritten `main` + `staging` with `--force` (not `--force-with-lease` — filter-repo rewrites all commits, making histories fully divergent; `--force-with-lease` will fail)
6. Verify on GitHub: confirm `main` and `staging` show rewritten history before proceeding

## Phase 2 — Restructure directories

7. From `~/Spaceship/`: rename `hiresling.ai/` → `hiresling-app/`
8. Create parent: `mkdir ~/Spaceship/hiresling.ai/`
9. Move app repo inside: `mv ~/Spaceship/hiresling-app/ ~/Spaceship/hiresling.ai/hiresling-app/`
10. Move meta repo inside: `mv ~/Spaceship/hiresling-meta/ ~/Spaceship/hiresling.ai/hiresling-meta/`
11. Rename GitHub repo `42piratas/Hiresling.ai` → `hiresling-app` (GitHub Settings → General → Repository name). Update remote in local repo: `git remote set-url origin git@github.com:42piratas/hiresling-app.git`
12. Create GitHub repo `hiresling-meta`; add remote and push: `git remote add origin git@github.com:42piratas/hiresling-meta.git && git push -u origin main staging`

## Phase 3 — Update references

13. **CLAUDE.md decision:** move to parent root (`~/Spaceship/hiresling.ai/CLAUDE.md`) for Claude Code discovery, AND keep a copy in `hiresling-app/` for version control. Parent copy is unversioned but Claude-readable; app copy is tracked. Keep both in sync.
14. Update all paths in CLAUDE.md to reflect new structure
15. Update meta cross-refs — two passes:
    - Relative: `app/...` → `../hiresling-app/app/...`
    - Absolute: grep for `/Spaceship/hiresling.ai/` or `/Spaceship/Hiresling.ai/` → update to `/Spaceship/hiresling.ai/hiresling-app/` or `/Spaceship/hiresling.ai/hiresling-meta/` as appropriate
16. `.vercel/`, `.github/`, `infra/`, `scripts/` stay in `hiresling-app/`
17. `vercel link` from inside `hiresling-app/`; verify env vars

## Phase 4 — Tooling

18. Enforce Claude invocation from `~/Spaceship/hiresling.ai/` in `CLAUDE.md` — invoking from sub-repos creates a silent new memory context
19. **TRON path update — bulk replace in `hiresling-meta/agents/tron.md`:**
    Replace all occurrences of `/Users/42piratas/Spaceship/Hiresling.ai/meta/` → `/Users/42piratas/Spaceship/hiresling.ai/hiresling-meta/`
    This covers: bus.db paths, tron-state.md, pipeline.md, blocks/, agents/, skills/, .env, and all log paths hardcoded throughout tron.md
20. Reopen Claude from `~/Spaceship/hiresling.ai/`; verify memory loads
