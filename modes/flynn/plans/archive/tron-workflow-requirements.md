> ⛔ **SUPERSEDED — 2026-06-05.** All requirements here were applied to [`tron-workflow-v2-skills.csv`](../tron-workflow-v2-skills.csv). Source of truth: [`tron-backlog.md`](../tron-backlog.md). Retained for history.

# TRON workflow — open requirements (from external review + operator rulings)

Decisions to apply to `tron-workflow-v2-skills.csv` before it's frozen. The workflow is the
source of truth; all other artifacts conform to it afterward. Status: ⬜ pending · ✅ applied

## From the review + operator rulings (this round)

- ⬜ **R1 — Build emits multiple outcomes.** `Build` must emit `done | wall | stalled`, not only
  `done`. This gives `wall` a producer (else the escalate row is unreachable).
- ⬜ **R2 — Liveness is the ENGINE, not the workflow.** Heartbeat/stall/dead-worker detection
  lives in the engine (sweep/tick + jobs). The workflow does NOT poll. It only needs an
  **inbound trigger** for an engine-detected stall (e.g. `worker:stalled`) → escalate/recover.
- ⬜ **R3 — Split Row 4 (two different milestones).**
  - Post-build review: input = the delivered log; the block is already built.
  - Architect **forward review / clear-ahead**: the block is unbuilt → there is NO log; input is
    the block spec. Different inputs and outputs → separate rows.
- ⬜ **R4 — Architect forward review consults prior done work, cross-session** (so it clears
  without drift). Exception: the **first run** has nothing prior to consult. Only state needed =
  "is this the first run?". The *how* is the skill's job (R6).
- ⬜ **R5 — Reviewer review method/scope = the reviewer's SKILL**, not the table. Strip Row 6's
  `scope = …` cell. (Kills the "untracked last-review clock" concern entirely.)
- ⬜ **R6 — Architect review gets skills.** `skill:forward-review` (clear-ahead) and
  `skill:log-review` (findings → adhoc). The review method lives in the skill, like reviewers.
- ⬜ **R6b — Every architect review is FORWARD-LOOKING.** A log review reads a log only to shape
  **upcoming** work (adhoc/next blocks). The architect never reopens or re-reviews a done block;
  findings on built work become future fix blocks, not retroactive edits. Applies to both
  architect skills.
- ⬜ **R7 — WHAT-NEXT silent-stall gap.** Case: blocks remain, none cleared, no architect idle →
  matches no IF and isn't session:end. Add a **WAIT / escalate** branch so a free slot with
  remaining work always has a defined action.
- ⬜ **R8 — Declare fan-out.** `block:next:done` fires Rows 3 & 4; `review:<type>:done` fires
  Rows 8 & 9. State explicitly that **both** fire (parallel), not a pick.
- ⬜ **R9 — Spawn modeling.** Either add explicit engineer/architect spawn rows, or declare
  spawning implicit in dispatch. Architect (persistent) currently has no creator row that
  Rows 4/9 depend on.
- ⬜ **R10 — Define terminals + reconcile grammar.** `end` and `-` are used as ON-COMPLETE but
  undefined as terminals. Triggers `tron:start`, `session:end`, `directive:0`, `build:block:next`
  don't fit the stated grammar — either widen the grammar enum or rename the triggers.

## Standing guardrails (already settled — keep enforcing)

- Skill-internals NEVER in the table (release, validate/deploy, reviewer scope, review method,
  session-end internals). The table names the skill + its outcome only.
- A block is dispatchable iff **cleared**; clearing only informs TRON (no direct dispatch).
- Every "informs TRON" outcome returns via `directive:0`; the dispatcher decides.
- Closed, lintable vocabulary — not a scripting language.

## Confirmed clean

- Separation of concerns in the table (skills hold all multi-step protocols).
