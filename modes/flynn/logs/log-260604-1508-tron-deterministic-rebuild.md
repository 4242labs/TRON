# log — 260604-1508 — TRON deterministic rebuild (partial)

**Agent:** SUPER-M · **Operator:** Ânderson · **Status:** session ongoing (partial log)

## What happened

Continued the TRON recreation. Two threads: (1) finished + reviewed the v2 **seeder**; (2) pivoted the whole design to a **deterministic, script-driven** architecture and wrote an ADR for it.

### Seeder (v2) — shipped to `tron` main
- Rewrote `tron-seed.md` from scratch (no patching). Model: **collect + document, never scaffold the host.**
- Host needs only **two pointers** — a specs path and an agents path. TRON installs **next to the crew** (`<agents>/tron.md` + `<agents>/tron/`).
- Flow: greet → workflow-first walk (conflict-driven, edits via `skill-edit-self`) → locate agents/specs → install → validate agents+specs → pipeline (host doc or interview→internal ledger) → write `project.md` → telegram/cron (config-driven, not asked) → verify/fail-fast → trace + sign-off.
- New contracts: `spec.example.md` (ID/goal/AC/scope/deps/owner; no status), `pipeline.example.md` + `templates/pipeline.md` (status+sequence ledger). Reshaped `workflow.example.md` (dropped `session_end_idle_min`), `project.example.md` (two-pointer model).
- Test feedback applied: killed self-narration, added terse Voice, dropped `<meta>` jargon (→ `<agents>`), TG⇒cron made config-driven.

### Architecture pivot — deterministic FSM
- Decision: make TRON **as robotic as possible** — minimal LLM. Researched 2026 practice; grounded in **"Blueprint First, Model Second"** (arxiv 2508.02721) + the deterministic-orchestration consensus.
- **Two layers:** workflow *definition* (per-project composition + knobs) vs operational *layer* (canon prose + judgment).
- **Composition model (C-A):** canon ships fixed **step primitives** (`dispatch`/`review`/`gate`/`escalate`/`findings-triage`); projects **compose** them (order + roles/checks + knobs) in `workflow.yaml`. CI / security-review / data-architect = naming roles/checks into existing primitives, no canon change. Only a new *kind* of step (fan-out/join, loop-until, wait-for-event) is a canon change.
- **Single entry (C-B):** cron → `run.sh` (executor) → `claude -p` per typed tool → back to `run.sh`. `tron.md` = prompt context, not an executor.
- LLM confined to: classify-message, the judgment calls (triage / wall-vs-solvable / stall / scope-fix), and slot-filling. Every LLM touch is **schema-in/schema-out**.
- **All comms = canned templates** in one registry (`messages.yaml`), rendered via `render(tag,slots)`. Tone is **SET** by the landing-page voice; candidates extracted to `tron-messages-candidates.yaml` (names parameterized to slots).

### ADR + review
- Wrote `plans/tron-adr-001-deterministic-rebuild.md`; a second agent reviewed it (appended). Reconciled all findings: C-A + C-B resolved in the body, four Phase-0 gaps folded in (closed tag enum + `unclassified`→escalate; invalid-output retry→escalate; tick atomicity/idempotency; copy-scope), file tree relabeled. ADR now final/consistent.

## Commits (all pushed)
- `42agents` main `93af595` — ADR-001 (reconciled) + `tron-goes-live-02.md` + `tron-messages-candidates.yaml` (via worktree flow).
- `tron` main `771174e` — v2 seeder + spec/pipeline contracts + wiki to-do; `rewrite/tron-v2` merged + deleted; `archive/v1` tag stands.

## Open / next
- **Phase 0** (schemas, step-primitive library + composition schema, closed tag vocabulary, judgment-tool contracts, blueprint-lint) — the gated next step; needs no operator input.
- Phases 1–5 per ADR. Tone is set; `messages.yaml` unblocked.
- Pending task: move site `tron.build` → `tron.42labs.io`.

## Note
This log is uncommitted (canon — needs worktree flow to commit).
