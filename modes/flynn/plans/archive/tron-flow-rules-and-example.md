> ⛔ **SUPERSEDED — 2026-06-05.** Replaced by [`tron-workflow-v2-skills.csv`](../tron-workflow-v2-skills.csv) + [`tron-backlog.md`](../tron-backlog.md) §1. Retained for history.

# TRON flow — rules + worked example

Distilled from the operator's journey walk. Two parts: (A) the **rules** that govern
every session, (B) a **worked example** that shows them in motion. Amends the current canon
(see `tron-journey-review-changes.md`). Project-specific numbers (cadences, deploy-allowed)
are **knobs**, not canon — shown here as one project's settings.

---

## A. Rules

### Communication
- **R1 — One throat.** The operator talks only to TRON; TRON talks to the fleet. Workers are
  never addressed directly. `watch` is read-only.
- **R2 — Peer-consult.** A working engineer that hits a problem reaches the **architect**
  directly. TRON observes, does not relay, does not transition.
- **R3 — Escalation is the architect's ceiling.** If the architect can't resolve a problem
  within its rules/restrictions, **TRON escalates to the operator** — terminal, plus Telegram
  if enabled. Only genuine walls reach the operator.

### Milestones drive everything
- **R4 — Milestone → script.** A worker doesn't branch the flow. It hits a **milestone**
  ("block done", "review done"); TRON then runs the **script the workflow binds to that
  milestone** — an ordered sequence of steps. The milestone is only *complete* once every step
  in its script has run.
- **R5 — Review is a milestone, not a verdict.** A reviewer (code / security / data / … — a
  distinct agent, never the architect) delivers a **log** and signals "review done." TRON runs
  the review-done script; the *decision* about the log happens in that script, downstream.
- **R6 — Only TRON releases.** Workers never self-terminate. TRON kills a worker **after** its
  milestone script fully completes — never before.

### The block-done script (engineer reports done)
- **R7** TRON asks: *validated locally?* If no → the engineer must validate first.
- **R8** If yes, and **deploy is allowed to engineers** in this workflow → TRON directs the
  engineer to deploy.
- **R9** When every step of the script has run → block marked **done** → TRON kills the engineer.

### The architect drift-guard (per delivered block)
- **R10 — Architect reviews two things on every engineer block-done:**
  (a) the **delivered block's log**, and
  (b) the **next not-yet-started block**, re-checked against the latest delivered logs — because
  a finished block occasionally changes things and the plan can drift.
- **R11 — Blocking.** TRON **cannot dispatch the next block until the architect has cleared it.**
  The next block is held pending architect review.

### Reviewer cadences (project knobs)
- **R12 — Periodic reviewers fire by count of delivered blocks**, each its own agent:
  code every N, security every M, data every K (this project: 3 / 5 / 7). When a cadence hits,
  TRON dispatches that reviewer after the block is done. A reviewer may peer-consult the
  architect along the way.

### Fixes from reviews
- **R13 — Findings → architect → fix block.** On a reviewer's "review done", TRON kills the
  reviewer and hands its findings to the **architect**, who scopes the fix(es) into block(s).
- **R14 — Fix blocks are sub-blocks of what they fix, slotted ahead of un-started work.**
  A fix for delivered block `01-06` becomes `01-06-02`, inserted **before the next not-yet-started
  top-level block**, so it's picked up next without renumbering the plan.
  (e.g. block 5 running, 6 just delivered + reviewed, 7 not started → fix = `01-06-02`.)

### Concurrency + start
- **R15 — Parallelism.** Up to `max_concurrent_engineers` engineers run at once, plus one
  **persistent architect** (idle until summoned).
- **R16 — Start is confirmed in-console.** Nothing dispatches until the operator confirms, inside
  the console, the proposed start block and the agent count (see C3).

---

## B. Worked example

**This project's settings**
- `max_concurrent_engineers: 2` · persistent architect: on
- architect per-block review: **on, blocking the next block** (drift-guard)
- code review every **3** delivered blocks · security every **5** · data every **7**
- deploy allowed to engineers: **yes**
- pipeline already has blocks `01-01 … 01-10`, all `todo`

**Start.** Operator runs `tron start`. The console opens. TRON checks the pipeline:
*"Next up is `01-01`. Confirm?"* — operator confirms, sets 2 engineers. Only now does TRON spawn
**ARCH-PERSIST** (idle) and dispatch **ENG-1 → 01-01** and **ENG-2 → 01-02** (two concurrent).

**Work + peer-consult.** Both engineers build; the architect idles. ENG-1 hits a design problem
and reaches the architect directly (R2) — TRON just watches. The architect answers within its
rules and ENG-1 continues. *(Had the architect been unable to clear it within its restrictions,
TRON would have escalated to the operator on the terminal, and Telegram if set — R3.)*

**A block lands.** ENG-2 finishes `01-02` and reports done — a milestone. TRON runs the
block-done script (R4): *"Everything validated locally?"* ENG-2 confirms. Deploy is allowed to
engineers here, so TRON directs ENG-2 to deploy; it deploys. Every script step has run, so
`01-02` is marked **done** and TRON kills ENG-2 (R6/R9).

**Drift-guard review (blocking).** TRON summons the architect to review the **log of `01-02`**
and to re-check the **next not-started block** against the latest logs (R10). The next block is
`01-03` — TRON **will not dispatch it until the architect clears it** (R11). The architect
reviews, clears `01-03`; it becomes dispatchable, and TRON sends a freed engineer onto it.

**Code-review cadence.** `01-03` lands — the **3rd delivered block** — so the code-review
cadence fires (R12). TRON dispatches **REV-CODE** over the last 3 delivered blocks. REV-CODE
peer-consults the architect once, then signals "review done" with a log (R5). TRON runs the
review-done script; when it's truly complete, TRON kills REV-CODE and hands its findings to the
architect (R13).

**Fixes.** The architect turns the findings into a fix block. Say the findings were against
delivered block `01-06`, with `01-05` still running and `01-07` not yet started: the architect
creates **`01-06-02`** and slots it **before `01-07`** (R14), so the fix is the next thing picked
up — no renumbering of the plan.

The loop continues: every 5th delivered block adds a security reviewer, every 7th a data
reviewer, each firing the same milestone→script→findings→fix path.

---

*(Continues — more of the journey to be exemplified next.)*
