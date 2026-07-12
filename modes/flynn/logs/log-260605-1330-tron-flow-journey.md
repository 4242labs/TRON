# Session log — TRON: B3 engine build + workflow-model journey review (partial)

**Date:** 2026-06-05 · **Author:** SUPER-M + operator (Ânderson) · **Status:** session ongoing (partial log)

## What happened

### 1. B3 engine built (deterministic spine)
Built the engine fresh in the `tron` repo — **Python core + thin bash connectors** (chosen because `yq` is absent; `pyyaml`/`jq`/`claude` present; FSM/JSON/schema work is fragile in bash, watch-item R-1):
- `engine/`: `engine.py` (CLI: start/tick/msg/stop/recover/validate/doctor), `fsm.py` (interpreter), `judge.py` (5 judgment tools, tiered, schema-validate + retry→unclassified, stubbable offline), `lint.py` (blueprint-lint L1–L13), `state.py`, `render.py`, `jobs.py` (~/.claude/jobs, detached spawn, stall pre-filter), `hostpipe.py`, `ctx.py`, `util.py`.
- `scripts/`: `run.sh`, `sweep.sh` (cron→tick, no LLM-resume), `cron-install.sh`, `report.sh` (worker→inbox), `tg-poll.sh`/`tg-send.sh` (carried from v1).
- **Verified offline, no tokens:** `validate` → **13/13 lint PASS** over canon; dry FSM run advanced start→dispatch→worker.done→review→next→end.
- **Caveat:** the engine encodes the *pre-journey* model. The journey review below supersedes large parts of it — **not yet reconciled**.

### 2. Process correction (saved to memory)
- **Nothing outside the project** — a `/tmp` sandbox was created and rejected; rule saved. Sandboxes go in a gitignored in-repo path.
- **No internal jargon** — "ledger" was a second name for **pipeline**; ripped out of all docs + code (state key now `pipeline:`).
- Canon `.gitignore` had instance-runtime ignores wrongly; trimmed to `.sandbox/` + `prototype/` (instance gitignore is the seeder's job).

### 3. Workflow-model journey review (the substance)
Walked a full TRON journey with the operator, who drove the model to a **two-layer** shape:
- **Standing layer — Directive #0:** keep every worker slot busy; pick work via **Next-Block** (priority: open+cleared adhoc → cadence due → next by sequential ID, intermediates `01-01-01` before `01-02`); unexpected input → **SCRIPTS**. Conditionals: *Clear Ahead* (blocks ahead, none cleared, architect idle → `REVIEW:NEXT`) and *Stand Down* (all idle, nothing left → `SESSION END` protocol).
- **Reactive layer — the event table:** `trigger → step → on-complete (== a trigger)`. Steps are multi-outcome (stacked output/on-complete pairs); the milestone's **script** resolves which branch fires.

Key model decisions:
- **Review is a milestone, not a verdict.** A reviewer delivers a log + "review done"; the architect's **Log Review** turns findings into work. The `review` verdict-branch (clean/findings) is wrong.
- **Reviewers ≠ architect.** Distinct agents (code/security/data + any). Architect is the standing consultant (R1), does Forward Review (clears upcoming blocks) + Log Reviews. **Reviewers == workers** (share the slot pool); the **architect is the clearance bottleneck** → make architect-count a knob.
- **`cleared` is a pipeline status** (`todo → cleared → in-progress → done`); the architect clears the *next* block (as-is or amended) — always clears. Clearing only **informs TRON**; it triggers nothing (dispatch is the standing Dispatcher's job).
- **Two fix types:** `adhoc` (review-driven) vs injected `NN-NN-NN` (operator/architect-decided).
- **Protocols** (Bootup, Session End) = TRON lifecycle procedures; **Scripts** = milestone handlers + catch-all. Both bounded/lintable (the guardrail: rich workflow, *not* a scripting language).
- **Block-naming by role:** `block:next`, `block:done`, `block:adhoc`, `log:done`, `log:review:<type>`.
- **release-engineer is a TRON skill** invoked by the block-done script (validate → deploy → release); the dispatcher depends on slots actually freeing.

## Artifacts produced
- `super-m/plans/tron-flow-rules-and-example.md` — rules + worked example.
- `super-m/plans/tron-journey-review-changes.md` — running change log (updated this session).
- `super-m/plans/tron-workflow-bpmn.html` — the workflow in BPMN (HTML/SVG).
- `super-m/plans/tron-workflow-v1-lean.csv`, `tron-workflow-v2-skills.csv` — two alternative table cuts.

## Where it stands / next
- Flow **example** model: converged.
- **Open frontier:** (1) define the **scripts + protocols** layer (bounded); (2) write the **generalized structured-workflow format** (closed vocabulary + lint); (3) **reconcile B3 engine + canon (B0/B2/B4)** to this model; (4) B7 console + start-gating.
