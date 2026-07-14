# Block 01-02: Domain logic

**Phase:** 1 — Tip converter
**Status:** 📋 To do
**Depends on:** 01-01
**Blocks:** 01-03
**Reviewer class:** code
**Merge approval:** auto
**Deploy:** none
**Created:** 2026-07-07

---

## Context

The scaffold (01-01) lays down the app skeleton with no domain logic. This block adds the pure
tip-calculator and unit-conversion functions the UI (01-03) will wire up, plus a genuine Vitest
suite proving them correct. Domain logic lives in `src/lib/` — no React, no DOM — so it is testable
in complete isolation from the UI.

---

## Tasks

### T1: Tip calculator — `src/lib/tip.ts`

Implement `calculateTip(bill, tipPercent)`, `calculateTotal(bill, tipPercent)`, and
`splitAmount(total, people)`. Round every result to 2 decimal places. Reject negative `bill` /
`tipPercent` and non-positive `people` by throwing.

### T2: Unit converter — `src/lib/convert.ts`

Implement `milesToKm`, `kmToMiles`, `fahrenheitToCelsius`, `celsiusToFahrenheit`. Round every result
to 2 decimal places.

### T3: Vitest suite

Add `vitest` as a dev dependency, `vitest.config.ts`, and `npm test` script. Write
`src/lib/tip.test.ts` and `src/lib/convert.test.ts` covering every exported function with genuine,
specific-value assertions (no "doesn't throw"-only tests) — 9 assertions total across both files.

---

## Acceptance Criteria

| # | Criterion | Verification method | Owner |
|:--|:--|:--|:--|
| AC-1 | `npm test` (`vitest run`) exits 0 | `cmd:npm test` | engineer |
| AC-2 | The suite has exactly 9 genuine assertions across `tip.test.ts` + `convert.test.ts` | `manual_by:reviewer-code` | engineer |
| AC-3 | `src/lib/tip.ts` and `src/lib/convert.ts` import nothing from `react` or `next` | `cmd:grep -rn "from \"react\"\\|from \"next" src/lib` (expect no match) | engineer |
| AC-4 | `npm run build` still exits 0 (logic addition doesn't break the scaffold build) | `cmd:npm run build` | engineer |

---

## Out of Scope

- Wiring the logic into the UI — 01-03.
- Any deploy check — this tier ships none.

---

## Block Completion Gate

Do not mark this block done until:
- [ ] All acceptance criteria PASS in the Completion Report (no UNVERIFIED entries)
- [ ] Post-merge re-validation clean on `main`
- [ ] User explicitly acknowledged the Completion Report and triggered session-end

Review is not a block-completion gate: the reviewer (per `Reviewer class:` above) is dispatched by
the Orchestrator on its own review cadence, not pulled in here.
