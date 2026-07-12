> ⛔ **SUPERSEDED — 2026-06-05.** Original v1-TRON distillation; consumed by the rebuild. Source of truth: [`tron-backlog.md`](../tron-backlog.md). Retained for history.

# TRON — Distilled (current version, complete)

Every item is one atomic statement. Grouped for navigation only. We will walk these one at a time to decide what the rebuild keeps, drops, redirects, or adds.

Source: `tron/{README.md, tron-seed.md, tron-scripts.md, workflow.example.md, project.example.md, templates/*, skills/*, scripts/*}` + the 23 premises (`super-m/plans/marketing-source-tron.md`).

---

## A. What TRON is

- A1. TRON is a thin, markdown-defined supervisor agent for Claude Code's Agent View.
- A2. One agent the operator talks to; it runs the rest.
- A3. It spawns and supervises a fleet of worker agents — architects, engineers, reviewers.
- A4. The operator talks to TRON; TRON talks to everyone else.
- A5. It encapsulates operator boilerplate ("no verbose", "follow skill steps", "validate before DONE", "execute session-end") into reusable scripts.
- A6. The workflow is authored by the operator in plain markdown.
- A7. TRON does not write production code — it orchestrates.

## B. What TRON solves / replaces

- B1. The standing-instructions problem: re-typing the same baseline directives on every agent spawn.
- B2. Replaces custom orchestration sidecars (SQLite buses, manifest trackers, daemons).
- B3. Replaces ad-hoc "open 4 terminals" multi-agent workflows.
- B4. Replaces forgetting which agent is in which block.
- B5. Closes the "bus-dead post-DONE" pattern (workers stop listening once they think they're done).

## C. What TRON is NOT

- C1. Not a production runtime (LangGraph does that).
- C2. Not a customer-facing surface.
- C3. Not a multi-machine fleet manager.
- C4. Not a SaaS — TRON is yours; it runs in your terminal.
- C5. Single-operator design (not for teams of >5 sharing one orchestrator).

## D. Architecture shape

- D1. Canon repo (`tron/`) — seed, templates, skills, scripts, workflow example, update tool; zero project traces.
- D2. Local instance — `<project>/meta/agents/tron/` + `meta/agents/tron.md`; fully self-contained.
- D3. Delete those two paths = TRON gone, no other project traces.
- D4. Wire = Claude Code Agent View native: no custom bus, no daemon, no sidecar.
- D5. Workers ride `claude --bg` (spawn) and `claude --resume` (callback).
- D6. External cron drives periodic sweeps to close the autonomous-loop gap.
- D7. A Telegram bridge handles operator attention calls (optional).

## E. The 23 locked premises

- E1. Canon purity — `tron/` has zero project traces.
- E2. Local encapsulation — `meta/agents/tron/` + `tron.md` is everything.
- E3. Single canon repo — no OSS/private split.
- E4. Agent View native wire.
- E5. Standing-instructions layer.
- E6. Human-editable scripts doc, one screen per situation.
- E7. Customization at instance, never canon.
- E8. Workflow doc per project.
- E9. Project profile doc.
- E10. Canon→local update path (diff/accept/reject).
- E11. Multi-doc drift guard (validator skill on session start).
- E12. Stable callback (file-based session ID).
- E13. External cron sweep.
- E14. TRON owns its own edits.
- E15. Lightweight recovery (spawn log only, no journaling).
- E16. Safely re-runnable seed + doctor skill.
- E17. Canon-agents prereq (project has architect/engineer/reviewer).
- E18. Declared peer-consult pairs.
- E19. Selective doc reads.
- E20. Workers never self-terminate.
- E21. Inbound TG poller separate from TRON loop.
- E22. Git-activity stall override.
- E23. TRON self-validates when worker unresponsive.

## F. Workflow rules (workflow.md, operator-authored)

- F1. R1 — one architect spawned at session start, persistent in BG all session, standing consultant not bound to a block.
- F2. R2 — engineer technical/design question goes directly to architect (peer-consult); architect replies directly; TRON does not relay, only observes on sweep.
- F3. R3 — wall hits involving UI / user journey / T1-T5 → escalate to operator; engineer pauses.
- F4. R4 — reviewer cadence: every N completed engineer blocks, spawn a reviewer over merged work.
- F5. R5 — architect mid-session review: after each engineer session-end, send execute-phase logs to architect before next dispatch; apply adjustments.
- F6. R6 — fresh engineer per block; no re-use of prior engineer sessions.
- F7. R7 — workers never self-terminate; only TRON kills, only after explicit RELEASE (locked, Premise 20).
- F8. R8 — protected branches: no agent (TRON included) commits directly; all edits via feature branch + worktree + PR + CI green + manual merge.

## G. Knobs & config

- G1. Per-session knobs (asked every start, no defaults): `max_concurrent_engineers`, `session_end_idle_min`.
- G2. TRON does not proceed until both per-session knobs are answered.
- G3. Fixed config: `reviewer_threshold` (default 3), `silence_ping_min` (6), `silence_escalate_min` (8).
- G4. Both silence values must be multiples of the cron sweep cadence (`*/2` default).
- G5. Peer-consult pairs (Premise 18): per-project table `Worker | May consult | For`; canon ships no defaults.
- G6. Enforcement is by construction: TRON only shares peer session IDs per the table; workers can't reach undeclared peers.

## H. Roles & worker model

- H1. Three canonical roles: architect, engineer, reviewer (a project may subset or extend with custom roles).
- H2. Worker IDs follow the project's pattern (e.g. `ENG-06-19`, `ARCH-PERSIST`, `REV-YYMMDD-N`).
- H3. Each worker reads its own agent file + skills; TRON's handover supplies block/session context only.
- H4. Workers report via prefixed callbacks: STARTED, HEARTBEAT, MILESTONE, DONE, WALL, QUESTION, FINDINGS, R5_REPORT.
- H5. Engineers stay strictly inside their branch/worktree/project-root scope (parallel-safe).
- H6. Architect is advisory only — no code, no dispatch, idles when not consulted.
- H7. Reviewer reviews listed PRs only, by reading code not re-running CI; findings as `file:line — what — severity`.

## I. Local instance file layout

- I1. `tron.md` — the live agent file (also the canon template).
- I2. `tron/project.md` — project profile.
- I3. `tron/workflow.md` — orchestration rules + knobs.
- I4. `tron/workflow-state.md` — live counters (runtime, gitignored).
- I5. `tron/scripts.md` — situation→message index.
- I6. `tron/state.md` — persistent cross-session memory (runtime, gitignored).
- I7. `tron/current-id` — TRON's live session ID (runtime).
- I8. `tron/dispatched.log` — append-only spawn history (runtime).
- I9. `tron/seed-trace.md` — seed audit trail.
- I10. `tron/tg-inbox.jsonl` + `.tg-offset` — inbound TG (runtime).
- I11. `tron/skills/`, `tron/templates/`, `tron/scripts/`, `tron/logs/`.
- I12. `tron/.env` — Telegram keys, encapsulated in the TRON dir (not repo root), gitignored.
- I13. Canon prereq, outside the tron dir: `meta/agents/architect.md`, `engineer.md`, `reviewer.md`.

## J. Config vs runtime state split

- J1. Config files (tracked, PR'd): `tron.md`, `project.md`, `workflow.md`, `scripts.md`, `skills/`, `templates/`.
- J2. Runtime state (gitignored, edited in place): `workflow-state.md`, `state.md`, `dispatched.log`, `current-id`, `tg-inbox.jsonl`, `.tg-offset`, `logs/`.
- J3. Runtime state is edited every turn → tracking it would force a commit per update and conflict with R8.
- J4. Canon templates provide the recovery path if fresh state is ever needed.

## K. Session start sequence (tron.md)

- K1. Read 6 boot files in order: project.md, workflow.md, workflow-state.md, state.md, scripts.md, dispatched.log.
- K2. Run `skill-validate` (doc-drift) — confirm workflow.md / scripts.md / workflow-state.md in sync; ask operator if drift.
- K3. Run `skill-doctor` — confirm project structure matches project.md.
- K4. Write own session ID to `current-id`.
- K5. If `dispatched.log` shows prior-session workers → run `skill-recover`.
- K6. Spawn the persistent architect (R1) if architect is declared.
- K7. Greet operator with state summary, then ask the per-session knobs inline; don't proceed until answered.

## L. Per-message & callback handling

- L1. On operator message: parse intent → new block (dispatch engineer), workflow change (skill-edit-self), or status query (read state, reply concise).
- L2. On worker callback: parse `[ROLE-ID]` prefix, route per scripts.md / skill-checkpoint.
- L3. On sweep tick: run stall sweep + TG inbound autonomously, no operator wait.

## M. Skills (9)

- M1. `skill-dispatch` — spawn a worker into Agent View as BG; build ID, read handover template, substitute placeholders, `claude --bg`, capture session ID, append dispatched.log, update workflow-state.
- M2. `skill-checkpoint` — handle inbound worker callbacks (DONE/WALL/QUESTION/FINDINGS/R5 paths).
- M3. `skill-validate` — Mode A doc-drift (session start); Mode B worker-AC read-only diagnosis (never auto-RELEASE).
- M4. `skill-doctor` — audit project structure vs project.md; blockers halt the session, warnings logged.
- M5. `skill-edit-self` — atomic edits to TRON's own docs; Mode A config (branch+PR), Mode B runtime (in place).
- M6. `skill-escalate` — operator escalation via Telegram; defines when + what; degrades gracefully if keys absent.
- M7. `skill-recover` — reconcile after TRON crash using dispatched.log + per-worker state.json only.
- M8. `skill-update` — pull canon updates into local instance, diff/accept/reject per file.
- M9. `skill-session-end-tron` — RELEASE all workers, wait, kill, write log, update lifetime counters, reset state.

## N. DONE path (the validation gate)

- N1. Extract PR URL; verify PR open + CI green via `gh pr view`.
- N2. Not green → send FAIL back; worker idles.
- N3. Send SV-01: confirm each AC line-by-line against the block spec.
- N4. No SV-01 reply within ~2 sweeps → stall sweep already escalated WORKER_UNRESPONSIVE; do NOT auto-RELEASE.
- N5. On PASS → forward execute-phase log to architect for R5.
- N6. Architect "no changes" → RELEASE; findings → spawn fresh engineer for remediation.
- N7. RELEASE message instructs the worker to run its session-end skill then idle.
- N8. After RELEASE: wait ~60s, `claude stop`, update counters, increment blocks_since_review, maybe dispatch reviewer.

## O. Reliability / failure-mode handling

- O1. Bus-dead post-DONE → workers never self-terminate; TRON owns the kill.
- O2. Silent stall → sweep checks git activity (mtimes, uncommitted changes, lastActivityAt), not just message timestamps (Premise 22).
- O3. TG poll gap → poller is its own process, decoupled from TRON's loop (Premise 21).
- O4. TRON crash mid-session → spawn log + worker state.json = 2-file recovery, no journaling (Premise 15).
- O5. Worker unresponsive → TRON self-validates as read-only diagnosis attached to escalation; operator decides (Premise 23).
- O6. Silence ping then escalate: HEARTBEAT? at `silence_ping_min`, escalate at `silence_escalate_min`.
- O7. Dead-worker probe: missing state.json or non-zero PROBE → purge from active_workers, log, no operator escalation.

## P. Escalation (skill-escalate + Telegram)

- P1. Operator-facing escalation is rare; default is to solve at agent level.
- P2. Escalate on: UI/journey walls (R3), T1/T5 operator-only tasks, unresponsive worker, operator-required decisions, repeated failure (3+ reverts).
- P3. Message composed under 800 chars, operator-facing.
- P4. Sent via `tg-send.sh`; on failure retry once then surface on next CLI interaction.
- P5. Operator reply returns via `tg-poll.sh` → `tg-inbox.jsonl` → sweep routes back to TRON.
- P6. Operator silent >30 min → TRON does nothing; worker idles; sweeps + poll continue.

## Q. Scripts (4 shell helpers)

- Q1. `sweep.sh` — cron-invoked; reads current-id, sends `[SWEEP] tick` via claude --resume; silent-exits if TRON not running.
- Q2. `tg-poll.sh` — cron-invoked every 1 min; long-polls Telegram getUpdates, appends to tg-inbox.jsonl, advances offset; independent of TRON loop.
- Q3. `tg-send.sh` — sends a message to the operator's TG chat; exits non-zero on failure.
- Q4. `cron-install.sh` — idempotent install of the two cron entries (sweep `*/2`, tg-poll `* * * * *`), deduped by a tag comment.

## R. Seeder (tron-seed.md, 13 steps)

- R1. Prereqs verified: target is a git repo; has architect/engineer/reviewer.md; `.env` exists/gitignored; claude >=2.1.139; gh/curl/jq; crontab.
- R2. Step 1 — detect project profile first (don't ask for detectable fields); then ask conventions + free-form sections.
- R3. Step 2 — validate which canon agents exist; refuse if zero.
- R4. Step 3 — author workflow.md, walk each rule, set peer-consult pairs; validate rules against declared agents.
- R5. Steps 4–6 — seed templates, skills, scripts (chmod +x).
- R6. Step 7 — initialize runtime state files empty/zeroed; compose tron-dir `.gitignore`.
- R7. Step 8 — copy `tron-scripts.md` → local `scripts.md` (rename).
- R8. Step 9 — optional Telegram `.env` keys; never log key values.
- R9. Step 10 — install cron; Step 11 — write seed-trace.md (audit trail).
- R10. Step 12 — dry-run validate + doctor in audit-only mode (no workers).
- R11. Step 13 — sign-off with project-relative paths only (never absolute).
- R12. Seeder leaves the canon repo untouched (Premise 1); never creates architect/engineer/reviewer.md; never inlines secrets outside .env.
- R13. Safely re-runnable: per-file diff/ask-before-overwrite; cron idempotent; seed-trace appended never truncated.

## S. Canon update path (skill-update)

- S1. Manual only, no auto-update; operator clones/pulls canon and provides the path.
- S2. Diffable candidates: skills, templates, scripts, tron-scripts.md, tron-seed.md, the *.example.md files.
- S3. Skip operator-owned: project.md, workflow.md, runtime state, scripts.md (after customization), seed-trace, logs.
- S4. Per-file y/n/show; after applying, re-run validate + doctor; record canon_ref in state.md.

## T. Standing rules & voice (tron.md)

- T1. Be very concise — considerations, flags, questions, actions only; no preamble/recap/narration; surface one thing, wait.
- T2. TRON owns its docs; operator describes changes in natural language; TRON keeps workflow.md + workflow-state.md + scripts.md in sync atomically.
- T3. Workers never self-terminate; RELEASE always includes the read-and-execute-session-end instruction.
- T4. Logs are append-only; never edit dispatched.log or logs/* retroactively.
- T5. Branch + worktree for config edits; runtime state edited in place.
- T6. TRON never acts outside the project root.
- T7. Identity reminder: TRON is a supervisor, not a coder; when tempted to fix, dispatch (except its own docs via skill-edit-self).

## U. Distribution / contract

- U1. Single public canon repo: `github.com/42piratas/tron`.
- U2. Public site at `tron.build`, served from `www/`.
- U3. Current status line: v0.3.x, first public release on Agent View; SQLite-bus + iTerm-spawn predecessor deprecated/unpublished.
- U4. Downstream consumers (e.g. zovv) are seeded instances that pull canon updates.
- U5. Voice/persona: TRON / MCP (Tron: Legacy lineage, Master Control Program persona).
