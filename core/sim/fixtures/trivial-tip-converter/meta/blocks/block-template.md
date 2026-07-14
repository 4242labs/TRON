# Block <ID>: <Title>

**Phase:** <Phase number and name>
**Status:** 📋 To do
**Depends on:** <Block IDs this requires, or "none">
**Blocks:** <Block IDs that depend on this, or "none">
**Reviewer class:** <code | none>  ← which reviewer the Orchestrator dispatches on its review cadence; pinned at scoping
**Merge approval:** <auto | needs-user>  ← default `auto`; stamp `needs-user` only for a genuinely risky block that needs explicit human sign-off before merge (none in the trivial tier)
**Deploy:** <none | check>  ← default inherits the project deploy check (`context.md → Deploy`, which is `none` for this tier); `check` would override with a block-specific success check (unused in this tier)
**Created:** <YYYY-MM-DD>

---

## Context

<Why this block exists. What problem it solves. What came before it. 2-4 sentences.>

---

## Tasks

### T1: <Task title>

<What to do. Be precise enough that the engineer doesn't need to ask questions.>

### T2: <Task title>

<...>

---

## Acceptance Criteria

Each criterion is a contract. The verification method is fixed at scoping time.

| # | Criterion | Verification method | Owner |
|:--|:--|:--|:--|
| AC-1 | <what must be true> | `test:<name>` \| `cmd:<exact command>` \| `manual_by:<role>` | engineer |
| AC-2 | ... | ... | ... |

---

## Out of Scope

<Explicit exclusions. Any mid-flow scope change requires user approval and a note here.>

---

## Block Completion Gate

Do not mark this block done until:
- [ ] All acceptance criteria PASS in the Completion Report (no UNVERIFIED entries)
- [ ] Post-merge re-validation clean on `main`
- [ ] User explicitly acknowledged the Completion Report and triggered session-end

Review is not a block-completion gate: the reviewer (per `Reviewer class:` above) is dispatched by
the Orchestrator on its own review cadence, not pulled in here.
