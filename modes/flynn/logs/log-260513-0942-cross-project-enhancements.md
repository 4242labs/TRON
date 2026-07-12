# SUPER-M Session: 2026-05-13

**Mode:** Cross-project enhancements (user-directed implementation)
**Branch:** `chore/super-m-20260513-agent-system`
**Worktree:** `42agents/.worktrees/chore/super-m-20260513-agent-system/`

---

## Locked Decisions

| # | Decision |
|:--|:--|
| D1 | **Worktree path — multi-repo:** `{project}/worktrees/{repo}--{branch}/` (umbrella `worktrees/` dir at project root, validated across hiresling/alfred/semdigitar). One per branch. No numbering. |
| D2 | **Worktree path — single-repo / canon:** `{repo}/.worktrees/{branch}/` (gitignored). Applies to `42agents/`. |
| D3 | **Artifact path — block-scoped:** `{project}/{meta-repo}/blocks/{block-id}/screenshots/` (or other media dir). Pattern in Sem Digitar 01-05. |
| D3b | **Artifact path — ad-hoc / non-block:** `{project}/{meta-repo}/artifacts/{YYYYMMDD}/{session}/`. Replaces `~/Downloads/`, project-root dumps, and flat `meta/screenshots/`. |
| D4 | **Cross-project access:** stays ad-hoc / verbal per session. No tracked allowlist. §14 only acknowledges the category exists. |
| D5 | **Worktree enforcement:** hook fails commits from main checkout. Detection: `git rev-parse --git-dir` lacking `.git/worktrees/` substring. **Applies to all `.repo-class` values (canon, meta, app).** |
| D6 | **Meta repos:** no PR/staging required. Direct push to `main` from worktree allowed. Worktree rule still enforced. |
| D7 | **Completion Report location:** `## Completion Report` section inside the engineer's timestamped session log. Drop `blocks/<id>/completion-report.md`. |
| D8 | **Engineer log filename:** when a session targets a block, filename must include `{block-id}-{slug}` (per Nordgrid / Sem Digitar / Alfred convention; Hiresling drifts). Ad-hoc sessions keep freeform desc. |
| D9 | **No migration sweep:** existing `blocks/<id>/completion-report.md` files stay as historical. New blocks follow D7. |
| D10 | **Engineer log dir:** `{meta-repo}/logs/{role}/log-*.md`. Role = `super-m`, `engineering`, `architecture`, `analyst-marketing`, `art-director`, `advisor-legal`, … (de-facto across all projects). |

---

## Execution Plan

### Phase A — Canon edits

| # | File | Change |
|:--|:--|:--|
| A1 | `principles-base.md §14` | (a) Add "Worktree path" subsection → D1+D2. (b) Add "Artifact path" subsection → D3+D3b (block-scoped vs ad-hoc, both inside meta repo). (c) Add bullet: main checkout read-only for all repo classes; commits originate from added worktrees; enforced by `.githooks/pre-commit` → D5. |
| A2 | `principles-base.md §12` (line 172) | Replace the `blocks/<id>/completion-report.md` mandate with D7 wording. Drop the "or appended to block doc" ambiguity. |
| A3 | `principles-base.md` (logs section or new) | Codify D8 (filename) + D10 (dir `{meta}/logs/{role}/`). Engineer log filename `log-YYMMDD-HHMM-{block-id}-{slug}.md` when block-scoped. |
| A4 | `skill-git-multi-agent.md` | (a) Remove per-project override clause at L209. (b) Add "Meta repos" sub-section → D6. (c) Add single-repo `.worktrees/{branch}/` clause → D2. (d) Note hook enforcement → D5. |
| A5 | `skill-completion-verify.md` (L33) | Point to engineer session log per D7. |
| A6 | `skill-validate.md` (L88, L107) | Update example paths + chat-surface line per D7. |
| A7 | `guidelines-browser-testing.md §4` | Replace `~/Downloads/` fallback with `{project}/artifacts/{YYYYMMDD}/{session-or-block}/`. |

### Phase B — Kit edits

| # | File | Change |
|:--|:--|:--|
| B1 | `shared-knowledge/templates/hooks/pre-commit` | Insert worktree-identity check (snippet below). Apply for **all** `.repo-class` values, not just canon/meta. Header comment updated. |
| B2 | `shared-knowledge/templates/hooks/pre-push` | When `.repo-class=meta`, allow direct push to `main` from worktree. Keep PR-enforcement for canon/app. |
| B3 | `shared-knowledge/templates/setup-repo.sh` | On install, print one-line summary of what the hook enforces for current `.repo-class`. Ensure `.worktrees/` is gitignored for single-repo canon. |

### Phase C — Agent docs

| # | File | Change |
|:--|:--|:--|
| C1 | `super-m/super-m.md` C2 | Wording: reversal-log + completion-report live inside engineer's session log, not separate file. |
| C2 | `super-m/super-m.md` C3 | Re-anchor "Completion Report drift" audit to session-log section. Flag orphan `completion-report.md` files in active blocks as drift. |
| C3 | `super-m/super-m.md` C1 | Add: pre-commit hook applies to all repo classes; check filename pattern compliance for block-scoped logs. |

### Phase D — Rollout (per repo)

Per repo with `.repo-class` set:

| # | Action |
|:--|:--|
| D-1 | Copy updated `.githooks/pre-commit` and `pre-push`. |
| D-2 | Run `scripts/setup-repo.sh` to re-wire hooks. |
| D-3 | Add `.worktrees/` to `.gitignore` (single-repo / canon only). |
| D-4 | Commit + push per repo's flow (PR for canon/app, direct for meta). |

#### Phase D — Project-specific cleanups (discovered 2026-05-13)

| Project | Action |
|:--|:--|
| **Hiresling.ai** | Relocate 12 `b88-validate-*.png` from project root to `hiresling-meta/blocks/88-*/screenshots/`. |
| **Hiresling.ai** | Move `hiresling-meta/screenshots/console-*.log` to dated buckets under `hiresling-meta/artifacts/{YYYYMMDD}/{session}/` (or delete if stale). |
| **Hiresling.ai** | Delete empty `hiresling-meta-worktrees/`. Standardize on `worktrees/`. |
| **Hiresling.ai** | Filename audit: rename block-scoped engineer logs to include `{block-id}-{slug}` (D8). |
| **Alfred** | Move `alfred-meta/artifacts/dry-run-batches.md` into `artifacts/{YYYYMMDD}/{session}/` (or attach to its session log). |
| **Sem Digitar** | Leave `blocks/01-05-…/completion-report.md` as historical (D9). Future blocks follow D7. |

### Phase E — Validation

| # | Check |
|:--|:--|
| E1 | Commit from main checkout (canon) → hook blocks with worktree message. |
| E2 | Commit in `.worktrees/{branch}/` (canon) → hook passes. |
| E3 | Commit from main checkout (app repo) → hook blocks. (Q6 = enforce for app.) |
| E4 | Engineer dry-run on a sample block → Completion Report lands inside session log; no `blocks/<id>/completion-report.md` created; filename matches D8. |
| E5 | Browser-test dry-run → artifact lands in `{project}/artifacts/...`, referenced from completion-report section. |
| E6 | SUPER-M audit dry-run → flags orphan `completion-report.md` in active blocks; flags `~/Downloads/` references; flags engineer logs missing `{block-id}-{slug}` when block-scoped. |

---

## Hook detection snippet (Phase B1)

```sh
git_dir="$(git rev-parse --git-dir)"
case "$git_dir" in
  *.git/worktrees/*) ;;        # added worktree — OK
  *)
    echo "✘ pre-commit blocked — commit must run in an added worktree, not the main checkout." >&2
    echo "  Single-repo / canon:  git worktree add .worktrees/{branch} -b {branch} origin/main" >&2
    echo "  Multi-repo project:   git worktree add ../{repo}--{branch} -b {branch} origin/main" >&2
    exit 1
    ;;
esac
```

Match on `.git/worktrees/` (not bare `/worktrees/`) to avoid false-positive against the repo's own `.worktrees/` user-facing dir.

---

## Dependency Order

```
Phase A (canon)   ─┐
Phase B (kit)     ─┼─→ Phase C (agent docs) ─→ Phase D (per-repo rollout) ─→ Phase E (validation)
                  ─┘
```

A and B run in parallel (independent files). C waits on A. D waits on A+B merged. E covers ≥1 repo per class (canon, meta, app).

---

## Completion Report

**Status:** DONE — 2026-05-13

### Canon commits (origin/main)

| SHA | Scope |
|:--|:--|
| `152c403` | §14 path conventions (Worktree / Artifact / Engineer log) · §12 Completion Report relocated to session log |
| `0036260` | §14 `.integration-branch` tracked marker added; hooks parameterize protected branch |
| `f656a2b` | §14 hardened — apps integrate on `staging` (canonical, not optional) |
| `49692a6` | `setup-repo.sh` CI-safe (Vercel/GHA/Netlify/Railway/Render exit 0); git-version requirement warning-only |

### Retrofits landed (11 projects)

alfred (+ meta `staging`→`main` migration), ai-aggregator (+ meta migration), vault (+ meta migration), sem-digitar (app default aligned `main`→`staging`), tron-42, 42labs.io, jubiscreu (3 repos), lens (lens-app + lens-meta), nordlens. All have `.repo-class`, `.integration-branch`, refreshed `setup-repo.sh`, `.githooks/{pre-commit,pre-push}`, and `core.hooksPath=.githooks`. 16 stale `setup-repo.sh` copies re-synced.

### Bonus migration

**lens-meta `staging`→`main`** executed end-of-session. PR #68 merged on staging first; pre-flight commit landed; main backed up as tag `pre-migration-main-260513` (SHA `11446c95`); force-push `staging`→`main` under temporarily-relaxed protection; default switched; staging deleted. Live-fire test confirmed pre-commit hook blocks from main checkout. Full detail: `lens-meta/logs/engineering/log-260513-1829-lens-meta-staging-to-main-migration.md`.

### Held — URGENT memos written

| Project | Memo | Reason |
|:--|:--|:--|
| `outreach` | `URGENT-MEMO-TO-ARCHITECT.md` | `data-model-v2` branch deletes `scripts/setup-repo.sh` (1228 dirty files); retrofit after refactor lands |
| `nordgrid` (23 repos) | `URGENT-MEMO-TO-ARCHITECT.md` | Volume + per-repo `.repo-class` decisions needed |
| `hiresling.ai` | `URGENT-MEMO-TO-ARCHITECT.md` | Combined drift inventory (D1-D6: workspace-root PNGs, 188-file flat dump, dual umbrellas, 176 logs missing block-id prefix) split into 3 workstreams |

### Out of scope (explicit user decision)

- 7 standalone/marketing repos (42labs.io.ds, career-ops, conhecaseucandidato.ai, 42piratas.com, tron, tron.build, tutors) — peculiar cases, no retrofit
- Apps currently on `main` not migrated to `staging` (per "do not migrate wrong apps now")

### Validation (Phase E)

| # | Outcome |
|:--|:--|
| E1 | ✓ Canon pre-commit hook blocks from main checkout |
| E2 | ✓ Commits from added worktrees pass |
| E3 | ✓ App-class pre-commit hook blocks from main checkout (lens-app, sem-digitar-app verified) |
| E4-E6 | Carried forward to future engineer/audit sessions (no block-scoped engineer dry-run in this session) |

### Outstanding for future sessions

- Hiresling drift cleanup (3 workstreams per memo)
- Outreach retrofit after `data-model-v2` lands
- Nordgrid family retrofit decision (architect)

