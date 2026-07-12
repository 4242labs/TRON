> ⛔ **SUPERSEDED — 2026-06-05.** Closed in scope consolidation. The model is now frozen in [`tron-workflow-v2-skills.csv`](../tron-workflow-v2-skills.csv); source of truth is [`tron-backlog.md`](../tron-backlog.md). Retained for the decision rationale (C1–C9) only.

# TRON journey review — required changes

Running log of changes surfaced while walking a full TRON journey (operator + SUPER-M).
Amends ADR-001/002, blocks B3/B7, and canon. Each item: what's wrong today → required
change → affected → status.

Status legend: ⬜ pending decision · 🔄 doing · ✅ done

---

## C1 — Review is a milestone, not a verdict-branch
**Today:** the `review` primitive branches on a reviewer verdict (`clean` / `findings`),
and the closed message vocabulary has no signal for "clean" — so a clean review can't advance.
**Correct model:** a reviewer (code / security / brand / … — a distinct agent, **never** the
architect) just delivers a **log** and signals **"review done."** One outcome. What happens to
the log is the **next workflow step** (milestone → script), e.g. triage. The judgment moves
downstream; the review step doesn't decide.
**Required:**
- Canon: `review` exposes one completion outcome ("done" → next step), not `clean`/`findings`.
- routing.yaml + B0 §1 (primitive edges) + tron.md review guidance updated.
- Engine: remove the `EDGE_ALIAS {(review,done):clean}` stopgap.
**Affected:** B0, B2 (routing.yaml), B3 (fsm), B4 (tron.md).
**Status:** ⬜ (operator sets the canon shape)

## C2 — No internal jargon: "ledger" → "pipeline"
**Today:** "ledger" was a second name for the pipeline (block list: order/owner/status/spec).
**Required:** one clean name — **pipeline** — everywhere; no coined/duplicate terms anywhere
operator- or canon-facing.
**Affected:** contracts, schemas, templates, engine, seed docs.
**Status:** ✅ done (all docs + code; state key is now `pipeline:`)

## C3 — Start is console-gated; nothing dispatches pre-confirmation
**Today:** `start --max N` spawns the architect + first engineer **immediately**, before the
operator is even in the console. Work begins behind their back.
**Correct flow:**
1. `tron start` → **console opens first** (nothing spawned).
2. TRON checks the pipeline and proposes the start point — *"Next up looks like block N.
   Confirm?"* (in tone) → operator confirms or adjusts.
3. TRON asks max concurrent engineers.
4. **Only then** → spawn architect + dispatch first block.
**Required:**
- B3: split `start` into *prepare* (load pipeline, compute proposed next block, expose required
  inputs) and *begin* (dispatch). `start` must not auto-dispatch.
- B7: console runs the pre-flight Q&A (confirm start point → ask agent count) → calls *begin*.
**Affected:** B3 (engine.start), B7 (console), ADR-002 lifecycle.
**Status:** ⬜

## C4 — Where-to-start persistence
**Today:** start point = first not-done block in the pipeline. Internal-mode pipeline is
gitignored at the instance (contracts §8), so statuses can vanish on a fresh clone / wiped
folder — even though every block's PR is durably in git (engineer session-end commits/PRs).
**Open:** trust the pipeline file, or **reconcile** done/not-done from real evidence (merged
PRs / branches / spec presence) at start so git is the source of truth.
**Affected:** B3 (start/recover), seeder, ADR.
**Status:** ⬜ decision pending

## C5 — Unified `tron` CLI verb (one command on PATH)
**Today:** commands are `bash <agents>/tron/scripts/run.sh <cmd>`. Awkward.
**Required:** a single `tron` executable on PATH dispatching verbs:
`tron start | seed | tick | stop | recover | update | doctor | validate | msg`.
`run.sh` becomes the internal shim. (Pulls B6 packaging forward.)
**Affected:** B3 (engine entry), B6 (packaging — now partly in scope).
**Status:** ⬜

## C6 — `tron seed`
**Today:** seeding = manually point the runtime at `tron-seed.md` in an interactive session.
**Required:** `tron seed` launches the interactive seeder walk directly.
**Affected:** B3/B6 CLI, tron-seed.md (invocation note).
**Status:** ⬜

## C7 — `tron update` (build it) + `doctor` reconciles & mutates settings
**Today:** `update` doesn't exist; `doctor` only diagnoses (env + blueprint-lint).
**Required:**
- `tron update` — refresh canon in a seeded instance (carry v1 `skill-update` intent).
- `tron doctor` — beyond diagnostics, **detect drift and adjust config**: agents added/removed
  at the agents pointer → update `project.yaml agents:`; composition/knob changes → update
  `workflow.yaml`; confirm changes in tone before writing. A re-sync, not just a check.
- Define the boundary: **doctor = reconcile per-project config** · **update = refresh canon**.
**Affected:** B3 (engine), seeder overlap (re-seed / edit-self), ADR.
**Status:** ⬜

## C8 — Flow rules + worked example
See `tron-flow-rules-and-example.md`. New canon-affecting rules it introduces beyond C1–C7:
- **Blocking architect drift-guard** (R10/R11): architect reviews the delivered log **and** the
  next not-started block; that block can't dispatch until cleared.
- **Block-done script** (R7–R9): validated-locally? → deploy (if engineers may) → done → kill.
- **Multiple reviewer cadences** (R12): code/security/data on independent block-count knobs.
- **Fix sub-numbering** (R14): fixes are sub-blocks of what they fix (`01-06-02`), slotted before
  the next un-started block.
**Affected:** B0 (primitive/pipeline shapes), B2 (workflow + knobs), B3 (engine), B4 (tron.md).
**Status:** ⬜

---

## C9 — Converged workflow model (Jun 05) — supersedes the framing in C1/C8

The journey review landed a concrete two-layer model. This is now the reference; earlier
items fold into it.

### Two layers
- **Standing — `Directive #0`** (the Dispatcher): keep every worker slot busy; pick work via
  **Next-Block**; any unexpected input → **SCRIPTS**. Conditionals:
  - *Clear Ahead* — blocks ahead, none cleared, architect idle → trigger `REVIEW:NEXT`.
  - *Stand Down* — all idle, nothing left → trigger `SESSION END` protocol.
- **Reactive — the event table:** `trigger → step → on-complete (== a trigger)`. Steps are
  **multi-outcome** (stacked output/on-complete pairs); the milestone's **script** resolves which.

### Next-Block selection (priority)
1. open **adhoc** && cleared (oldest first) → 2. **cadence** due → 3. next by sequential ID
(`01-01-01` before `01-02`). Source of truth = the **pipeline**.

### Settled rules
- **Review = milestone, not verdict** (confirms C1). Reviewer delivers a log + "review done";
  the architect's **Log Review** turns findings into work.
- **`cleared` is a pipeline status:** `todo → cleared → in-progress → done`. The architect
  **Forward Review** clears the *next* block (as-is or amended — always clears). Clearing only
  **informs TRON**; it triggers nothing (dispatch is the Dispatcher's job).
- **Reviewers ≠ architect**, are **distinct agents**, and **count as workers** (share the slot
  pool). The **architect is the clearance bottleneck** → **architect-count is a knob** (test, scale).
- **Two fix types:** `adhoc` (review-driven) vs injected `NN-NN-NN` (operator/architect-decided).
- **Protocols** (Bootup, Session End) = TRON lifecycle; **Scripts** = milestone handlers + the
  catch-all. Both **bounded/lintable** — rich workflow, not a scripting language (the guardrail).
- **`SESSION END` is a protocol** (confirm-with-operator → end or continue), not a hard stop.
- **Block naming by role:** `block:next / block:done / block:adhoc`, `log:done`, `log:review:<type>`.
- **`release-engineer` is a TRON skill** invoked by the block-done script (validate → deploy →
  release). The Dispatcher depends on slots actually freeing.
- **Directive #0 = the standing dispatch LOOP (engine spine), NOT a skill.** It is run at bootup
  and after every "informs TRON" event; it iterates free slots and emits `Build` / `review:next`,
  draining to `Session End`. It lives **beside** the reactive table, not as a row in it.
  **Next-Block IS a skill** (pure deterministic selection) that the loop calls per free slot.
  Both must stay deterministic code — never an LLM call.

### Status of earlier items under this model
- C1 ✅ folded (review-as-milestone).  C3 (console-gated start) → now the **Bootup protocol**.
- C8's blocking-forward-review → reframed as **`cleared` status + Forward Review**, not engine rule.
- The Dispatcher replaces ad-hoc "what fires the next build" (was the keystone hole).

### Open frontier (not started)
1. **Scripts + protocols layer** — define them (bounded), incl. block-done (validate/deploy/
   release), wall→operator escalation, Bootup, Session End.
2. **Generalized structured-workflow format** — closed vocabulary (triggers/steps/actors/
   outcomes) + lint; this example is one instance of it.
3. **Reconcile B3 engine + canon (B0/B2/B4)** to this model (engine still encodes the old one).
4. **B7 console** + start-gating on top of the above.

---

## Carried open decisions (pre-journey)
- **Skills form** in the deterministic model: one `procedures.md` index vs per-file stubs vs none.
- **Start scoping:** walk the whole pipeline vs let the operator pick a spec / subset / start point
  (overlaps C3 step 2 "adjust").
