# SUPER-M Session: Emily agent merge · KB folder cleanup · fleet sync

**Date:** 2026-07-06
**Branch discipline:** `chore/super-m-20260706-*`
**Model:** Claude Opus 4.8

## Summary

Merged the two demand-side consultants (Analyst-Marketing + Analyst-SEO-GEO) into a single lean agent — **Emily** — and propagated the rename fleet-wide. Separately, cleaned up a stray top-level `kb/` folder that had been re-created against the pre-rename path, traced its root cause, and added a guard. Captured three new backlog items and consolidated the operator TODO into the backlog. 7 PRs, all merged.

## Work Performed

| # | Task | Result |
|:--|:-----|:-------|
| 1 | Backlog capture — TRON modes (SCAFFOLD/NEW/ADVISOR), persona→memory, stronger conciseness enforcement | 3 open items in `agents/super-m/backlog.md` |
| 2 | Name selection for merged agent → **Emily** (Emily Cooper — digital-marketing strategist; name only, Cooper as a one-line note) | user decision |
| 3 | **Merge Analyst-Marketing + Analyst-SEO-GEO → Emily** (`agents/emily/`) | 42hq #138 |
| 4 | Polish Emily doc — de-bloat pass | 343 → **307 lines** |
| 5 | Deal with stray `kb/` folder + trace root cause + guard | in #138 |
| 6 | Fleet-wide Emily sync across downstream repos | #970 / #106 / #110 / #63 / #60 |
| 7 | Consolidate operator TODO into backlog (single findable list) | 42hq #139 |

## Emily — the merge

**Lean consolidation.** Two ~440-line mirror-image docs → one **307-line** agent. 8 modes: `POSITIONING · FUNNEL · CONTENT · PRICING · LAUNCH · CHANNEL · SEO · GEO`. Deduped the 13+10 thinking principles → 13; merged both guardrail sets; merged Cross-Project Design + Owned Artifacts into one Layout block; removed the PESSOA boundary stated three times down to one.

**Boundaries set fleet-wide:**
- Emily = **punctual consultant** (analyzes, specs, drafts on request).
- PESSOA = **deployed operator** (runs content around the clock against Emily's strategy). Neither overrides the other's standing decision without the user.
- Analyst-Finance sets price points; Emily frames/presents them.

**Files:**
- New: `agents/emily/{emily.md, skills/, logs/}` — carried over `skill-viral-artifact` + `skill-free-tool-ideation` (git-mv, history preserved), unified `skill-session-start`/`skill-session-end`, historical log.
- Removed: `agents/analyst-marketing/`, `agents/analyst-seo-geo/`.
- Repointed in 42hq: `README.md`, `principles-base.md` role list, `analyst-finance`, `art-director`, `coo`, `i18n` (two boundaries merged into one), `product-designer`, all `pessoa` files (template + skills + guide + brief).
- `docs-reports/` inventories left as historical record.

## KB folder cleanup + root-cause trace

**Problem:** a stray top-level `42hq/kb/frameworks/css-inline-flex-dom-order-line-break.md` existed alongside the canonical tree at `knowledge-base/kb/`.

**Trace:** added by **PR #136** (`11d8be3`, 2026-07-05, a 42labs.io session) — written to the top-level `kb/` path that PR #133 had *just* consolidated away that same day. The canonical write protocol (`knowledge-base/meta/agent.md §4.2`) was correct (`knowledge-base/kb/{category}/{topic}.md`); the offending agent resolved `kb/` relative to the repo root instead of from `knowledge-base/` — a pre-rename muscle-memory path.

**Fix:**
- Moved the note to `knowledge-base/kb/frameworks/` (git-mv); removed the stray `kb/`.
- **Guard added** to `agent.md §4.2`: explicit anti-pattern — "the topic tree lives **only** at `knowledge-base/kb/`, never a top-level `kb/` at repo root; if the KB is a separate workspace root, `cd` in first and resolve from `knowledge-base/`."

## Fleet-wide sync — PRs

| Repo | PR | Change |
|:-----|:---|:-------|
| 42hq | #138 | Emily merge + polish + KB fix + guard |
| hiresling-meta | #970 | `analyst-marketing-local.md`→`emily-local.md`; `logs/analyst-marketing/`→`logs/emily/`; `principles.md` two session-end rows→one Emily row; all pessoa files repointed |
| semdigitar-meta | #106 | local→`emily-local.md`; `logs/` rename; `context.md` registry row + scope mentions; `emily-local.md` scope rule (SEO/GEO now in-scope, Modes 7–8) |
| tron (public) | #110 | scaffold `AGENTS.md` org-agent row relabel → Emily (path stays placeholder per TD-10) |
| ganttflow-meta | #63 | 2 passing mentions |
| semdigitar-app | #60 | 1 passing mention (base `staging`, branch-protected — merged after checks) |
| 42hq | #139 | consolidate operator TODO into backlog |

**Sync + clean:** all 6 local checkouts fast-forwarded to origin; every temp worktree removed; merged 42hq branches deleted. 42hq main at `377bf21`.

**Verification:** fleet-wide grep confirms zero canonical (load-bearing) references to the old agent names remain — every residual mention is history (`logs/`, `blocks/archive/`, `reports/`, ADRs, `docs-reports/` inventories, tron-meta TD-10 tracking).

## Backlog state (`agents/super-m/backlog.md`)

**Open:**
1. TRON operating modes — SCAFFOLD · NEW · ADVISOR (ADVISOR absorbs SUPER-M). Design the mode boundary before building.
2. Agents persist persona into memory (compaction survival) — codify in canon bootstrap.
3. Stronger concise-speech enforcement — harder than the ANSWER/ACT/FLAG/FYI reminder.

**Operator Actions (user-only):**
- Set `CANON_READ_TOKEN` secret in `ganttflow-meta` + `zovv-meta` (fine-grained PAT, `contents: read` on `42piratas/42hq`). Unblocks canon-drift CI there.

**Closed this session:** Emily merge (+ fleet sync).

## Parked / deferred (carryover)

- P-06 — move the scaffold *procedure* (`skill-project-scaffold`) into TRON vs keep SUPER-M-owned; hiresling's lefthook bridge as sanctioned SoT override.
- `canon_version` re-pin for skills whose canonical moved 42hq→TRON; setup-repo/hooks reconcile on next touch; backfill the 8 off-disk registry projects.

---
Executed by Model: Claude Opus 4.8
