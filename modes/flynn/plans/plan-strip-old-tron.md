# Plan: Strip Old TRON From All Projects

**Date opened:** 2026-05-15
**Owner:** operator (super-m provides plan; execution is operator-driven, project-by-project, per [Super-m scope ends at canon])
**Status:** OPEN — parallel workstream (cross-repo cleanup), NOT superseded by the engine rebuild.
> ⚠️ **2026-06-05 — specifics partly stale.** Premise references the old v0.3.0 markdown canon; the *goal* (strip the predecessor SQLite/iTerm TRON from Jubiscreu/Hiresling/Nordgrid + delete `tron-42`) still stands. The `tron.build → tron/www/` fold is **outdated** — the site move is now `tron.42labs.io` (see backlog §5). Re-validate paths before executing. Tracked in [`tron-backlog.md`](tron-backlog.md) §5.

---

## Why now

`github.com/42piratas/tron` v0.3.0 just shipped — the first public canon on Claude Code Agent View. The predecessor TRON (SQLite-bus + iTerm-spawn era) is still present in three projects. Before seeding the new canon anywhere, strip the predecessor entirely so the seeder lands on a clean foundation.

---

## In scope

Three projects with a predecessor TRON installation:

| Project | Path | TRON agent path |
|:--|:--|:--|
| Jubiscreu | `~/42labs/jubiscreu/` | `meta/agents/tron.md` (30K) |
| Hiresling | `~/42labs/hiresling.ai/` | `hiresling-meta/agents/tron.md` (33K) |
| Nordgrid | `~/42labs/nordgrid/` | `nordgrid-meta/agents/tron.md` (15K) |

Plus two standalone repos to consolidate:

| Asset | Path | Action |
|:--|:--|:--|
| `tron-42/` working dir | `~/42labs/tron-42/` | delete entirely (local) |
| `tron-42/` remote | `github.com/42piratas/tron-42` | delete entirely (remote) |
| `tron.build/` working dir | `~/42labs/tron.build/` | fold into canon as `tron/www/`, then delete |
| `tron.build/` remote | `github.com/42piratas/tron.build` | delete entirely (remote, after canon absorbs content) |

**Out of scope** (operator decisions to make separately):

- `tron/www/` content rewrite for v0.3.0 messaging (the move is in scope; rewrite isn't)
- Re-seeding any project with the new canon
- Audit of `principles.md` for merge-policy refinements (separate effort)

---

## Stripping decision: skills

Predecessor TRON tightly coupled with `skill-session-end-*`, `skill-review-cycle`, `skill-validate`, `skill-tg-comms` — these were authored for the old dispatch + bus protocol.

**Recommended approach: delete TRON-coupled skills entirely** in each project. Reasoning:

- The new canon ships its own handover-based standing instructions (RELEASE → read `skill-session-end-{role}.md` → execute every step).
- Skills authored for the bus protocol won't fit the new RELEASE pattern; partial-strip risks subtle mismatch.
- Projects that haven't yet re-seeded the new canon temporarily lose session-end skills — that's acceptable; engineers can still wrap up cleanly without them, and the new canon will re-introduce role-appropriate skills when seeded.

Per-project skill purge list captured in each strip section below.

---

## Per-project strip detail

### Jubiscreu (`~/42labs/jubiscreu/`)

**Branch:** `chore/strip-tron-260515` (worktree)

**Files to delete:**
- `meta/agents/tron.md`
- `meta/skills/skill-tg-comms.md`
- `meta/skills/skill-session-end-engineer.md`
- `meta/skills/skill-session-end-architect.md`
- `meta/skills/skill-session-end-reviewer-code.md`
- `meta/skills/skill-review-cycle.md`
- `meta/skills/skill-review-code.md`
- `meta/skills/skill-validate.md`
- `meta/logs/tron/` (directory, including bus state)

**Files to inspect + edit:**
- `meta/agents/super-m-local.md` — strip TRON-tracking sections; leave the super-m wrapper intact.
- `principles.md` (if present) — search/strip any TRON-specific clauses.
- `context.md` (if present) — search/strip any TRON-specific clauses.
- `CLAUDE.md` (top-level) — strip TRON references in agent table or invocation rules.
- `.env` — delete `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` lines. (When the new canon is seeded into a project, the seeder asks about TG configuration fresh; old keys are not needed.)

**Logs to leave alone:**
- `meta/logs/super-m/log-260320-1000-bootstrap-full-audit.md` — historical, mentions TRON in past tense; do not edit.
- `meta/logs/architecture/*` — historical.

**Commit + merge:**
- Commit on `chore/strip-tron-260515`.
- PR + merge per Jubiscreu's conventions.

---

### Hiresling (`~/42labs/hiresling.ai/`)

**Branch:** `chore/strip-tron-260515` (worktree)

**Files to delete:**
- `hiresling-meta/agents/tron.md`
- `hiresling-meta/skills/skill-tg-comms.md`
- `hiresling-meta/skills/skill-session-end-engineer.md`
- `hiresling-meta/skills/skill-session-end-architect.md`
- `hiresling-meta/skills/skill-session-end-data-architect.md`
- `hiresling-meta/skills/skill-session-end-reviewer-code.md`
- `hiresling-meta/skills/skill-session-end-reviewer-security.md`
- `hiresling-meta/skills/skill-session-end-reviewer-branding-design.md`
- `hiresling-meta/skills/skill-review-cycle.md`
- `hiresling-meta/skills/skill-validate.md`
- `hiresling-meta/logs/tron/` (directory, including any TG inbox files)

**Files to inspect + edit:**
- `hiresling-meta/principles.md` — keep authoritative; strip TRON-specific clauses if any.
- `hiresling-meta/context.md` — strip TRON-specific clauses if any.
- `CLAUDE.md` (top-level) — strip TRON references in agent table (audit found tron.md was undocumented anyway).
- `hiresling-meta/logs/architecture/log-260427-0100-cycle-review.md:5` quotes *"tron.md agent undocumented in project CLAUDE.md"* — leave historical, do not edit.
- `.env` — same as Jubiscreu: delete TG keys.

**Commit + merge:**
- Commit on `chore/strip-tron-260515`.
- PR + merge per Hiresling's conventions.

---

### Nordgrid (`~/42labs/nordgrid/`)

**Branch:** `chore/strip-tron-260515` (worktree)

**Files to delete:**
- `nordgrid-meta/agents/tron.md`
- `nordgrid-meta/skills/skill-tron-first-run.md`
- `nordgrid-meta/skills/skill-session-end-engineer.md`
- `nordgrid-meta/skills/skill-session-end-architect.md`
- `nordgrid-meta/skills/skill-session-end-data-architect.md`
- `nordgrid-meta/skills/skill-session-end-analyst-quant.md`
- `nordgrid-meta/skills/skill-session-end-reviewer-code.md`
- `nordgrid-meta/skills/skill-session-end-reviewer-security.md`
- `nordgrid-meta/skills/skill-review-cycle.md`
- `nordgrid-meta/skills/skill-validate.md`
- `nordgrid-meta/logs/tron/` (directory)
- `nordgrid-meta/logs/nordgrid-archive/tron/` (legacy bus state, 48K bus.db)
- `nordgrid-meta/logs/nordgrid-archive/logs/tron/` (duplicate archive)

**Files to inspect + edit:**
- `nordgrid-meta/principles.md` (if present) — strip TRON-specific clauses if any.
- `nordgrid-meta/context.md` (if present) — strip TRON-specific clauses if any.
- `CLAUDE.md` — strip TRON references.
- Block archive docs that reference TRON as a deliverable — leave historical, do not edit.

**Note:** Nordgrid never used Telegram bridge (notifications only, no inbox). No `.env` TG keys to flag.

**Commit + merge:**
- Commit on `chore/strip-tron-260515`.
- PR + merge per Nordgrid's conventions.

---

### `tron-42/` repo

After all three projects merge their strip PRs:

1. Confirm no remaining references to `tron-42/` anywhere on the local machine (grep ~/.zshrc, ~/.bash_profile, scripts/, etc.).
2. Delete local working dir: `rm -rf ~/42labs/tron-42/`.
3. Delete remote: `gh repo delete 42piratas/tron-42 --yes` (irreversible — operator confirms).

### `tron.build/` → fold into canon

The website becomes part of the canon repo, served from `tron/www/`:

1. **Audit current content** in `~/42labs/tron.build/` — identify what carries forward (assets, brand, structure) vs what gets rewritten for v0.3.0 messaging.
2. **Branch in canon:** `chore/fold-website-260515` in `~/42labs/tron/`.
3. **Move content:** copy meaningful files from `tron.build/` into `tron/www/`, preserving git history if reasonable (otherwise plain copy + reattribute in commit message).
4. **Update canon `README.md`** to reference the website location (`tron/www/`) and the domain (`tron.build`).
5. **Vercel / domain config:** point `tron.build` domain at the canon repo's `www/` subpath. Operator handles DNS + Vercel project settings (T1/T5).
6. **Delete `tron.build` local dir:** `rm -rf ~/42labs/tron.build/`.
7. **Delete `tron.build` remote:** `gh repo delete 42piratas/tron.build --yes` (after Vercel project re-pointed).

**Content rewrite for v0.3.0 messaging:** separate operator decision; the move itself does not require the rewrite to be finished.

---

## Execution order

Sequential, one project at a time. Reasons:

- Pattern emerging during the first strip (which files to keep vs delete, edge cases in `principles.md`) informs the next two.
- Lets operator verify each merge works cleanly before opening the next PR.
- Surfaces any cross-project skill divergence early.

Recommended order:

1. **Nordgrid first** — no Telegram bridge, smallest TRON footprint (15K agent), simplest test case.
2. **Jubiscreu** — medium footprint, Telegram active.
3. **Hiresling** — largest TRON footprint (33K), most coupled skills, most cross-doc references.
4. **`tron-42/`** — delete (local + remote) after all three projects validated.
5. **`tron.build/` → `tron/www/`** — fold the website into canon; delete the standalone repo. Can run in parallel with steps 1–4 since it touches the canon repo, not the consumer projects.

---

## Validation gates

After each project's strip PR merges:

- No file under `<project>/` (or `<project-meta>/`) references `tron-42`, `tron.md` (as an agent), `skill-tg-comms`, or `meta/logs/tron/`.
- Running a fresh agent session (`claude` in the project root) does not surface any "missing skill" warnings.
- Existing principles.md still parses cleanly as the project's authoritative ops doc.
- super-m-local.md still operates without the TRON-tracking sections.

If any gate fails: open a follow-up issue; do not block the next project's strip.

---

## After strip is complete

Operator-driven choices (out of super-m scope per locked feedback):

- `tron/www/` content rewrite for v0.3.0 messaging (separate effort from the move itself).
- Decide which (if any) project gets the new TRON canon seeded first via `tron-seed.md`. The seeder will ask about TG keys fresh per project.
- Operator owns scheduling and execution; super-m does not coordinate these.

---

## Branches in flight

- This plan: `chore/strip-old-tron-260515` (42hq worktree)
- Per project: `chore/strip-tron-260515` (each project's own worktree, opened by operator when ready)

---

## Open questions

- `super-m-local.md` TRON-tracking sections: are they self-contained enough to surgically remove, or does the file need a full rewrite per project? (Inspect during execution.)
- `tron.build` → `tron/www/`: preserve git history (cherry-pick-style) or plain copy + attribute in commit message? (Decide at execution time; plain copy is simpler.)
