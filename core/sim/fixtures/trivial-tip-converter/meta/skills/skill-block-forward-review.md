---
name: skill-block-forward-review
description: Architect folds a finished block's learnings into upcoming blocks; Orchestrator-dispatched, flips no status.
source: project
---

# Skill: Block Forward Review

**The Orchestrator dispatches this skill when a block lands done (✅) on `main`.** It is not user-initiated and
it is not session-end — it flips no status and closes no block. Its job is to carry forward what
the just-done block taught us, so upcoming blocks stay correct. Read this file **now** — do not
rely on memory.

Performed by the **Architect**.

**Purpose:** A block rarely lands exactly as scoped. Left unreconciled, drift silently invalidates
downstream blocks. This pass reads the finished block's record and adjusts the **upcoming** blocks
(and their pipeline rows) before they are dispatched.

---

## 1. Determine Forward Scope

The done block is named by the dispatch. Build the set of blocks to reconcile:

- [ ] The **done block** itself (read-only here — it is already ✅, never edit it)
- [ ] Every **not-done** block that lists the done block in its `Depends on:` (direct downstream)
- [ ] Remaining **not-done** blocks in the same phase (candidates for drift)

```bash
grep -l "{DONE_BLOCK_ID}" blocks/*.md      # find blocks that reference the done one
```

Only **not-done** blocks (`📋 / 🔄 / 📌 / 🔧`) are in scope for editing.

---

## 2. Harvest Learnings

Read the done block's record:

- [ ] The block file `blocks/archive/{DONE_BLOCK_ID}.md` — final scope vs. original
- [ ] The engineer's session log for the block (`logs/engineering/log-*-{DONE_BLOCK_ID}-*.md`) —
  the `## Completion Report` and `## Completion Report (post-merge)` sections
- [ ] Any reviewer `## Critic Verdict` log for the block, if a reviewer fired on it

Extract, as a short list, only what changes future work: interface changes, new constraints,
dependencies that proved unnecessary or newly required, tech debt logged for a later block to
absorb, scope that moved into or out of the block.

If nothing in the record changes future work, record "no forward impact" and stop at §5.

---

## 3. Assess Each Upcoming Block

For each in-scope not-done block, decide whether a learning forces a change: scope, `Depends on`,
approach, or acceptance criteria. No change needed is the common case — say so and move on.

---

## 4. Apply Adjustments

Edit the in-scope block files and their `pipeline.md` rows directly:

- [ ] Update block `Depends on:` / `Blocks:` headers, tasks, acceptance criteria, or `Out of Scope`
- [ ] Update the matching `pipeline.md` rows; **never change a block's `Status` emoji here**
- [ ] Add a one-line note in each edited block's `Notes`: `adjusted per learnings from {DONE_BLOCK_ID}`

**Escalate to the user, do not silently rewrite, when** a learning invalidates a block wholesale or
would cut/split a block.

---

## 5. Persist

Carve your own worktree + branch (`arch/{DONE_BLOCK_ID}-forward`) into your own scratch dir, commit,
then land it yourself via grant + `land.sh` (`principles.md §Git & Branching` — this repo has no
remote, so no PR).

- [ ] Write a forward-review log to `logs/architecture/log-YYMMDD-HHMM-{DONE_BLOCK_ID}-forward.md`
  using the session-log format (`ref-session-log-format.md`): the learnings harvested (§2), the
  blocks assessed (§3), the adjustments applied or escalated (§4). If there was no forward impact,
  the log says so in one line.

---

## Guardrails

- This skill **never flips block status** and **never archives** — that is session-end
  (`skill-session-end-engineer.md §6`) only.
- It edits **only not-done blocks**. The done block and all terminal-status blocks are read-only.
- It does not review code — that is the reviewer's cadence (`skill-review-code.md`), dispatched
  separately by the Orchestrator.
