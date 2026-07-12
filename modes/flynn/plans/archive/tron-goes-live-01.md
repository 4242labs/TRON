> ⛔ **ARCHIVED — 2026-06-05.** Historical session handoff. Current state: [`tron-backlog.md`](../tron-backlog.md).

# TRON GOES LIVE — Session 01 Handoff

**Date:** 2026-06-02
**Driver:** Architecture rewrite, same product. Recreate TRON one piece at a time, no preset requirements.
**Method:** In-place rewrite (NOT a detached folder). Keep repo/remote/site/history.

> Source artifacts (read these to resume):
> - Full current-version distill: `~/42labs/42hq/super-m/plans/tron-distilled.md` (groups A–U, ~115 atomic items)
> - Live decisions log: `~/42labs/42hq/super-m/plans/tron-rebuild-decisions.md`
> - This handoff consolidates both + lists what's still open.

---

## Build mandate for the NEXT phase

Build a working TRON **up to the scaffolding/mapping phase only** — i.e. the seeder/profiler that either **maps an existing repo** to TRON's requirements or **creates a new structure**, mirroring how `~/42labs/42hq/super-m/` does SCAFFOLD (fresh) vs UPGRADE (map existing). Stop there. Goal: validate the requirements in parts, before building the live orchestration loop.

### Rebuild mechanics (agreed approach)
1. `git tag archive/v1` (+push) — immutable recovery point for the current canon.
2. Branch `rewrite/tron-v2` in a worktree off `main`.
3. `git rm` what's replaced; re-author; `main` stays shippable.
4. One PR to merge when ready. Site + history + remote intact.

---

## DECISIONS LOCKED (session 01)

### Copy / positioning
- **A1 (standing rule):** Strip "markdown" / "markdown-defined" from ALL copy — irrelevant, even depreciative. Identity line → e.g. "a thin supervisor agent for Agent View." (Memory updated.)
- **A2, A3, A5, A7:** keep.
- **A4:** reword — TRON **talks and coordinates** the fleet.
- **A6:** TRON ships with an **embedded default workflow** (pre-set out of the box); operator edits later. (Mechanism implication, see Seeder.)
- **B1–B5, C1–C4:** keep.
- **C5:** keep — "single-operator" = one human per TRON instance, not a shared team orchestrator.
- **U1, U3:** keep.
- **U2:** site moves `tron.build` → **`tron.42labs.io`** (Task #1, this session).
- **U4:** correction — TRON has NO special relation to zovv or any project; it may serve such projects but that doesn't change TRON. Drop the "downstream consumers pull canon" framing as a TRON property.
- **U5:** drop the TRON/MCP persona note from the mechanism distill (cosmetic only).

### Architecture shape
- **D1–D7:** keep.
- **D2 (standing rule):** never hardcode `meta/` — use the `<meta>` placeholder everywhere (meta dir is project-specific: `hiresling-meta`, `zovv-meta`…).

### Premises
- **E1–E9:** keep. (E2 = encapsulation; E3 = single public canon repo, nothing personal in canon; E4 = Agent View wire; E7 = maintainer discipline only, not imposed on users.)
- **E5:** keep concept (TRON owns the standing-instructions layer). ⚠️ **TOP REVAMP TARGET:** the actual spawn/handover scripts (`scripts.md` spawn entries + `templates/handover-*.md`) most need rework.
- **E10:** keep `skill-update` + canon-update path — the surgical per-file diff/accept/reject path (coexists with re-seed). *(Dropped then reversed by operator.)*
- **E11:** **DROP the drift-guard.** Redundant given atomic `skill-edit-self`. Cascade: `skill-validate` loses Mode A (doc-drift), keeps only Mode B (worker-AC diagnosis); drop session-start step K2; drop post-write re-validate.
- **E12:** **CHANGE** — address TRON by **name primary, ID fallback**. Confirmed `claude --resume <name> -p "..."` works (CLI 2.1.160). TRON is a singleton → name resolves non-interactively; `current-id` kept as fallback for the ambiguous-name edge case (picker would hang `-p`). Simplifies restart re-broadcast.
- **E13:** keep (= D6 cron heartbeat).
- **E14:** keep. **Quality target:** harden `skill-edit-self` (clear Mode A/B, atomic batch write, explicit rollback) so TRON can't corrupt its own docs.
- **E15:** keep lightweight 2-file recovery. ⚠️ **CORRECTION (verified CLI 2.1.160):** canon's `state.json` fields are STALE and silently fail today:
  - liveness = `state` (NOT `status`)
  - activity = `updatedAt` + `timeline.jsonl` (NOT `lastActivityAt`)
  - job dir = 8-char short id (NOT full UUID); full ids in `sessionId`/`resumeSessionId`
  - `name`/`nameSource` present (supports E12)
  - → rewrite ALL sweep/recover/checkpoint references to real fields + short-id→sessionId mapping.
- **E16:** keep (re-runnable seed + doctor; doctor only audits/reports, never fixes/updates).
- **E17–E23:** keep. (E22 stall override + E23 self-validate also need the E15 field rewrite. E21 TG poller stays a separate process.)

### Workflow rules & knobs
- **F1–F8:** keep all 8 rules (R1–R8) as the embedded default workflow.
- **G1:** keep `max_concurrent_engineers` — **always ask at session start, no default.** Actual concurrency = **min(operator threshold, available blocks)**.
- **G2:** **DROP `session_end_idle_min`.** TRON is turn-based, idle costs nothing; workers released on command. Session ends on explicit operator command or when all work is complete.

### Seeder (the next-phase deliverable)
- **DECIDED:** the seeder still engages the operator about the workflow, and offers to **map the project's existing structure** to TRON's requirements **OR create a new one** — mirroring `~/42labs/42hq/super-m/` SCAFFOLD (fresh) vs UPGRADE (infer/map). It profiles the repo first, then maps or scaffolds. (Supersedes any "ask nothing" reading of A6.)

---

## OPEN — not yet discussed (resume here next session)

Walk these against `tron-distilled.md`, same one-at-a-time method (surface only the unresolved):

- **G3** — fixed-config values: `reviewer_threshold` (3), `silence_ping_min` (6), `silence_escalate_min` (8). Keep values? Tie to cron cadence.
- **G5/G6** — peer-consult pairs mechanics (premise E18 kept; confirm the table format + per-project setup).
- **H1–H7** — roles & worker model (3 canonical roles + extensibility; worker IDs; report verbs; scope discipline).
- **I1–I13** — local instance file layout (apply `<meta>`; reflect dropped drift-guard artifacts).
- **J1–J4** — config vs runtime-state split (tracked/PR'd vs gitignored/in-place).
- **K1–K7** — session-start sequence (drop K2 drift-validate; fold in name-addressing).
- **L1–L3** — per-message + callback handling.
- **M1–M9** — skills, in detail. `skill-validate` reshaped (Mode B only); `skill-update` kept; **handovers + spawn scripts = revamp (E5)**.
- **N1–N8** — DONE path / SV-01 validation gate.
- **O1–O7** — reliability + stall sweep (REWRITE against real `state.json` fields).
- **P1–P6** — escalation (Telegram) flow.
- **Q1–Q4** — shell scripts (`sweep.sh`, `tg-poll.sh`, `tg-send.sh`, `cron-install.sh`) — rewrite sweep/poll against real fields.
- **R1–R13** — seeder steps end-to-end (apply the scaffold/map decision; A6 embedded workflow; drop forced per-rule interview but keep workflow engagement).
- **S1–S4** — canon update path (kept via E10 reversal) — confirm mechanics.
- **T1–T7** — standing rules & voice (concise-only; owns-its-docs; append-only logs; worktree for config; never outside project root; supervisor-not-coder).

### Cross-cutting build tasks (apply throughout the rewrite)
1. Rewrite every `state.json` reference to real fields (`state`, `updatedAt`, `timeline.jsonl`, short-id→sessionId). — affects E15, E22, E23, O, Q, recover/checkpoint.
2. Implement **name-primary / ID-fallback** addressing (E12) across handovers, scripts, recover.
3. Harden `skill-edit-self` (E14).
4. Revamp standing-instruction handover/spawn scripts (E5).
5. Apply `<meta>` placeholder everywhere (D2).

---

## TASKS
- **#1** — Move TRON site `tron.build` → `tron.42labs.io` (this session; flagged by operator).

---

## RESUME POINTER
Next session: continue the distill walk at **G3**, then build TRON through the **scaffolding/mapping phase** per the build mandate above.
