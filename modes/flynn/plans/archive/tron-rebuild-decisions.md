> ⛔ **SUPERSEDED — 2026-06-05.** Consumed by the rebuild. Source of truth: [`tron-backlog.md`](../tron-backlog.md). Retained for history.

# TRON Rebuild — Decisions Log

Walking `tron-distilled.md` one item at a time. Each row = operator's instruction for the rebuild.

| Item | Decision |
|:--|:--|
| A1 | Drop "markdown-defined" / "markdown" descriptors from all copy — irrelevant, even depreciative. Identity line becomes e.g. "a thin supervisor agent for Agent View." (Standing rule, not just A1.) |
| A2 | Keep. |
| A3 | Keep. |
| A4 | Reword: TRON **talks and coordinates** the fleet. |
| A5 | Keep. |
| A6 | **Change:** TRON ships with an *embedded default workflow* — already in place out of the box. The operator may change it, but it is not authored-from-scratch. (Mechanism implication for the rebuild, not just copy.) |
| A7 | Keep. |
| B1–B5 | Keep. |
| C1–C4 | Keep. |
| C5 | Keep. (Means: one operator per TRON instance; not a shared team orchestrator.) |
| U1 | Keep. |
| U2 | **Change:** site moves from `tron.build` → `tron.42labs.io`. Tracked as Task #1, this session. |
| U3 | Keep. |
| U4 | **Correct:** TRON has no special relation to zovv or any project. It may serve such projects, but that does not change TRON itself. Drop the "downstream consumers pull canon" framing as if it were a TRON property. |
| U5 | Drop from mechanism distill (cosmetic persona note only: name/voice from the *Tron* films). |
| D1 | Keep. |
| D2 | Keep. **Standing rule:** never hardcode `meta/` — the meta dir name is project-specific (`hiresling-meta`, `zovv-meta`…). Use the `<meta>` placeholder in all paths/copy/templates. |
| D3 | Keep. |
| D4 | Keep. |
| D5 | Keep. |
| D6 | Keep. (External cron heartbeat wakes turn-based TRON to sweep workers + TG inbox.) |
| D7 | Keep. (Telegram optional, degrades gracefully.) |
| E1 | Keep. |
| E2 | Keep. (= D2/D3 encapsulation.) |
| E3 | Keep. Single public canon repo, no private/personal split — nothing personal lives in canon; it's all in the seeded instance. |
| E4 | Keep. (= D4.) |
| E5 | Keep concept (TRON owns the standing-instructions layer). **REVAMP TARGET:** the specific spawn/handover scripts (`scripts.md` spawn entries + `templates/handover-*.md`) most need rework. Revisit at groups M, R, and handovers. |
| E6 | Keep. |
| E7 | Keep as *maintainer* discipline (canon stays generic; our customization lives in our instance). Not a rule imposed on end users — they do whatever they want with their own copy. |
| E8 | Keep. |
| E9 | Keep. |
| E10 | ~~DROP~~ → **REVERSED (keep).** User wants `skill-update` (M8) + canon-update path (group S) retained as the surgical per-file diff/accept/reject path. Re-seed is the full path; skill-update is the surgical one — they coexist. (New evidence for reversal: user decision after clarifying that doctor only audits and nothing else updates instances.) |
| E11 | **DROP** the drift-guard. Redundant given `skill-edit-self` (E14) makes edits atomic — docs can't drift unless hand-edited. Cascade: `skill-validate` loses Mode A (doc-drift), keeps only Mode B (worker-AC diagnosis); drop session-start step K2; drop the post-write re-validate in skill-edit-self. |
| E12 | **CHANGE:** address TRON by **name primary, ID fallback**. Confirmed `claude --resume <name> -p "..."` works (docs). TRON is a singleton per project, so name `TRON` resolves cleanly non-interactively. `current-id` still written + passed as fallback for the ambiguous-name edge case (where resume-by-name would open an interactive picker and hang a `-p` call). Eliminates most of the restart re-broadcast pain. Cascade: simplify skill-recover CALLBACK_UPDATE step; handovers give both name + id. |
| E13 | Keep. (= D6.) |
| E14 | Keep. **Quality target:** `skill-edit-self` must be hardened/well-structured (clear Mode A/B, atomic batch write, explicit rollback on failure) so TRON cannot corrupt its own docs. |
| E21 | Keep. (TG poller separate process.) |
| E22 | Keep — ⚠️ rewrite against real `state.json`/`timeline.jsonl` fields (see E15). |
| E23 | Keep. (Self-validate read-only, attach to escalation, never auto-decide.) |
| F1–F8 | Keep all 8 rules as the embedded default workflow (ship pre-set; operator changes later via skill-edit-self). |
| Seeder scope | **DECIDED:** at seed time TRON still engages the operator about the workflow — and offers to **map the project's existing structure** to the requirements **OR create a new one**, mirroring how `~/42labs/42hq/super-m/` scaffolds (fresh) vs upgrades (map existing repo). So: not "ask nothing" — it profiles the repo and either maps or scaffolds. (Supersedes the "minimal/ask-nothing" reading of A6.) |
| G1 | Keep `max_concurrent_engineers` knob — **always ask at session start, no default.** Note: actual concurrency = min(operator threshold, available blocks) — TRON never spawns more engineers than there are dispatchable blocks, even if the threshold is higher. |
| G2 | **DROP `session_end_idle_min`** (operator-decided). TRON is turn-based; idle costs nothing; workers released on command. Session ends on explicit operator command or when all work is complete. Cascade: remove from workflow-state.md live config, session-start knob prompt, session-end trigger. |
| E16 | Keep. (Re-runnable seed + doctor. Doctor only audits/reports structure — does not fix or update.) |
| E15 | Keep (lightweight 2-file recovery is sound). **CORRECTION (verified CLI 2.1.160):** canon's `state.json` field names are stale and would silently fail today. Real schema: liveness = `state` (not `status`), activity = `updatedAt` + `timeline.jsonl` (not `lastActivityAt`). Job dir = 8-char short id, not full UUID; full ids are in `sessionId`/`resumeSessionId`. `name`/`nameSource` present (supports E12). Rebuild must rewrite all sweep/recover references to the real fields + handle short-id→sessionId mapping. |
