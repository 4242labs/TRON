> ⛔ **ARCHIVED — 2026-06-05.** Historical session handoff. Current state: [`tron-backlog.md`](../tron-backlog.md).

# TRON GOES LIVE — Session 02 Handoff

**Date:** 2026-06-03
**Driver:** Architecture rewrite, same product. In-place rewrite; keep repo/remote/site/history.
**This session:** rethought TRON's structural model from first principles, then built the seeder through the scaffolding/mapping phase.

> Predecessors: `tron-goes-live-01.md` (session 01 distill + decisions), `tron-distilled.md`, `tron-rebuild-decisions.md`.

---

## THE BIG SHIFT THIS SESSION — structural model

Session 01 left the seeder facing a collision: the "scaffold vs map" decision (mirror SUPER-M's SCAFFOLD-fresh vs UPGRADE-existing) vs canon Premise 17 ("operator owns agent files; seeder must never create them"). Walking it back to first principles dissolved the collision.

### What TRON actually needs from the host

**Outside TRON's own folder, exactly two things — both recorded as pointers:**
1. **A specs path** — local MD files describing the work.
2. **An agents path** — wherever the worker definitions live (NOT necessarily `<meta>/agents/`).

Everything else is one of:
- **TRON brings it** (inside its folder): crew is dispatched from the agents path, but workflow, skills, state, logs, templates are all TRON's.
- **TRON detects it**: main branch, remote, org, conventions.
- **TRON defaults/creates it inside its own folder**: worktrees dir, logs, pipeline ledger (when host has none).

**Git is NOT a TRON requirement** — it's the *default workflow's* dependency (worktrees/PRs). Swap the workflow and git may not apply. So git checks are warnings, not hard gates.

### No host scaffolding — ever

The seeder **collects and documents; it never scaffolds the host.** It writes only inside `<meta>/agents/tron/`. It never creates spec files or agent files in the host — it points at them. This kills the Premise-17 collision entirely: there's nothing structural to "create" or "map" in the host.

### Specs model

- A spec = a **pure declaration of intent**: ID, goal, acceptance criteria, scope bounds, dependencies, owner role (default `engineer`).
- **No status field** in specs. Specs are host-owned; TRON reads, never rewrites.
- Format flexible; TRON maps what it finds and asks the operator to fill gaps rather than refusing on cosmetic mismatch.

### Pipeline ledger — the status + sequence record

- Single source of running status, joined to specs by ID. Fields: ID, order, owner, status (`todo`/`in-progress`/`blocked`/`review`/`done`), notes (optional).
- **Host already keeps a pipeline doc** → TRON validates required fields and **uses it directly** as the live ledger (`pipeline: host`). Consequence accepted: TRON then writes to a host-tracked file each turn.
- **Host has none** → TRON **interviews the operator** about blocks/statuses, then **creates the ledger inside its folder** (`<meta>/agents/tron/pipeline.md`, `pipeline: internal`).
- During a session, **TRON's ledger is authoritative**. Spec **dependencies = hard gates**; pipeline **order = preference**.
- This handles mid-project injection: initial statuses come from the host doc or the interview, so injecting TRON into work-already-underway doesn't lose track of what's done.

### Workflow handling at seed

- TRON ships an **embedded default workflow** (works out of the box).
- At seed, TRON **explains it conflict-driven** — names specific assumptions ("default has a reviewer rule but no reviewer.md found — drop or add?", "default commits via worktrees+PRs — does this project use git?") rather than a vague "does this fit?".
- Operator changes anything in natural language; TRON **applies edits live via `skill-edit-self`** (the seeder IS the same runtime TRON uses, so it can use the real skill, iterating with the operator). The hardening of `skill-edit-self` is the right fix for any fragility — not deferring edits.
- **Workflow is settled first** because it's the reference that defines which roles + knobs everything else is validated against.

### project.md = TRON's own config file

Lives inside TRON's folder (`<meta>/agents/tron/project.md`); host never owns it. Records the two pointers + pipeline mode + agents map + detected facts + conventions.

### Canon hygiene

Clone canon **outside** the project; run the seeder *from* it, seed *into* the project. Never clone canon in-tree (nested `.git`, canon-purity leak, stale update source, tree pollution).

### `<meta>` placeholder

Never hardcode `meta/` — the meta-repo dir is project-specific (`zovv-meta`, `hiresling-meta`…). Applied throughout the rewritten files.

---

## WHAT WAS BUILT (branch `rewrite/tron-v2`)

Repo `~/42labs/tron` is a **plain git repo** (no `.repo-class`, no `hooksPath` — the worktree mandate is 42hq-only). Recovery tag **`archive/v1`** set at `c9a90bc`. Working on branch **`rewrite/tron-v2`**. **Nothing committed or pushed** — `main` untouched.

### New files
- `spec.example.md` — spec contract + example (required fields; no status).
- `pipeline.example.md` — pipeline ledger contract + example (host-doc vs internal).
- `templates/pipeline.md` — seed template for the internal ledger.

### Rewritten
- `tron-seed.md` — full new seeding flow (see below). ~230 lines reworked.
- `project.example.md` — two-pointer model; dropped the Premise-17 "agents must live in `<meta>/agents`" framing; git facts framed as workflow-only.
- `workflow.example.md` — framed as embedded default; **dropped `session_end_idle_min`**; `max_concurrent_engineers` note (= min(threshold, dispatchable blocks)); R6 tied to pipeline order + spec deps.
- `templates/workflow-state.md` — removed `session_end_idle_min` knob.

### New seeder flow (`tron-seed.md`)
1. **Lay down TRON's folder** — copy crew/templates/skills/scripts; init gitignored runtime state; write `.gitignore`. No host files touched.
2. **Workflow** — explain conflict-driven; edit live via `skill-edit-self`; record required roles.
3. **Agents** — ask path; enumerate; validate vs workflow roles; never create.
4. **Specs** — ask path; explain contract; check compliance; never rewrite.
5. **Pipeline** — host doc (validate + use) or interview + create internal ledger.
6. **Write `project.md`** — consolidate pointers, agents map, detected facts, conventions.
7. **Optional** Telegram `.env` + cron heartbeat.
8. **Verify, fail fast** — pointers resolve, workflow↔agents consistent, specs comply, ledger valid, instance files present. (Live-loop dry-run deferred.)
9. **Seed-trace + sign-off** (project-relative paths only).

### Deferred to the orchestration phase (carried from v1 UNTOUCHED)
- `skills/` (dispatch, sweep, recover, escalate, checkpoint, validate, doctor, update, edit-self, session-end)
- `scripts/` (`sweep.sh`, `tg-poll.sh`, `tg-send.sh`, `cron-install.sh`)
- `templates/handover-*.md`, `templates/tron.md` (live agent file), `templates/state.md`
- `tron-scripts.md`, `README.md`, `landing-page.md`, `www/`

---

## NEXT

### Immediate — operator validation
Operator tests the seed end-to-end: open a fresh session pointed at `tron-seed.md`, give a throwaway target project, walk to instance creation. Report breakage / wrong feel. Iterate on `rewrite/tron-v2`. **Only then** commit + PR (no push until validated).

### Orchestration phase (after seed is validated)
Build the live loop. Carries the session-01 cross-cutting tasks:
1. **Rewrite every `state.json` reference to real CLI 2.1.160 fields** — liveness `state` (not `status`); activity `updatedAt` + `timeline.jsonl` (not `lastActivityAt`); job dir = 8-char short id (full ids in `sessionId`/`resumeSessionId`); `name`/`nameSource` present. Affects sweep/recover/checkpoint/escalate + `scripts/sweep.sh`, `tg-poll.sh`.
2. **Name-primary / ID-fallback addressing** (E12) across handovers, scripts, recover. `claude --resume <name> -p` confirmed working; `current-id` kept as fallback for the ambiguous-name picker edge case.
3. **Harden `skill-edit-self`** (E14) — clear Mode A/B, atomic batch write, explicit rollback. Critical: the seeder now depends on it live.
4. **Revamp standing-instruction handover/spawn scripts** (E5, top revamp target).
5. **`skill-validate` reshaped to Mode B only** (drift-guard E11 dropped); drop session-start K2; drop post-write re-validate.
6. Wire `tron.md` live agent file + workflow-state to the pipeline ledger (current_block ← pipeline order/deps).
7. Apply `<meta>` across the still-deferred files.

### Distill walk still open (one-at-a-time method, surface only unresolved)
G3 (fixed-config values), G5/G6 (peer-consult mechanics), H (roles/worker model), I (file layout — reflect dropped drift-guard + pipeline), J (config vs runtime split), K (session start — drop K2), L (callbacks), M (skills detail), N (DONE/SV-01 gate), O (sweep/reliability — real fields), P (escalation), Q (scripts), R (seeder steps — now largely realized this session; reconcile), S (canon update path), T (standing rules/voice).

---

## TASKS
- **#1 (still open)** — Move TRON site `tron.build` → `tron.42labs.io` (DNS/domain, `www/CNAME`, README links). Flagged session 01; not yet done.

---

## STATE SNAPSHOT
- `~/42labs/tron`: branch `rewrite/tron-v2`, uncommitted changes (4 rewritten + 3 new files). Tag `archive/v1` = recovery. `main` clean/untouched. Pre-existing untracked: `TO-DO-WIKI.md`, `_TRON-GOES-LIVE-01.md` (note: session-01 handoff canonical copy is `super-m/plans/tron-goes-live-01.md`; a root copy may linger).
- `~/42labs/42hq` (canon, hook-protected): planning docs live in `super-m/plans/`. Commit this handoff via worktree branch per SUPER-M discipline when ready.

## TEST FEEDBACK — round 1 (live seed of `ganttflow`)

First seeder run surfaced three issues; all fixed on `rewrite/tron-v2`:

1. **Self-narration.** Seeder recited its own guardrails ("I collect and document only… never scaffold… never touch canon"). Those are *instructions to the seeder*, not operator-facing. Fix: added a **"do not recite your constraints"** rule; moved guardrails under an explicit "for the seeder — do not recite" heading.
2. **Verbosity.** Added a **Voice** section to `tron-seed.md`: terse, no preamble/recap, one question at a time, state-default-and-confirm rather than explain-the-model.
3. **`<meta>` framing leak.** Seeder asked for a "meta-repo directory name" — not the agreed model. **Dropped `<meta>` entirely.** New model: TRON installs **next to the crew** — operator gives the **agents directory `<agents>`**, TRON installs at `<agents>/tron.md` + `<agents>/tron/`. First interaction is now **Step 0 — Locate**: detect + confirm the two locations (`<agents>`, `<specs>`), no jargon. Replaced all `<meta>/agents/…` paths with `<agents>/…` across `tron-seed.md`, `project.example.md`, `pipeline.example.md`.

Files touched this round: `tron-seed.md` (added Voice + Step 0, reframed install), `project.example.md` (`<agents>` model), `pipeline.example.md` (path fix), `templates/workflow-state.md` (already had `session_end_idle_min` dropped).

> Carry-forward: the live agent file `templates/tron.md` and the deferred skills/scripts still use the old `<meta>` paths — sweep them to `<agents>` during the orchestration phase.

## TEST FEEDBACK — round 2 (applied)

- **TG ⇒ cron, config-driven.** Step 7 no longer asks about Telegram/cron. Two variables in `project.md` (`telegram: off|on`, `cron: auto|on|off`) the operator edits; the seeder follows them silently. Coupling: `telegram on` implies heartbeat on (cron polls TG); effective heartbeat = `telegram==on OR cron==on`. Variables documented in `project.example.md`, written by seeder Step 6, consumed by Step 7.

## RESUME POINTER
Next session: get operator's seed-test result → fix on `rewrite/tron-v2` → commit/PR the seeder → start the orchestration phase (begin with cross-cutting task #1, the `state.json` field rewrite). Remember the `<meta>`→`<agents>` sweep across deferred files.
