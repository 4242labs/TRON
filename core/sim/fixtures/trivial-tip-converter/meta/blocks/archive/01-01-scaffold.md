# Block 01-01: Scaffold

**Phase:** 1 — Tip converter
**Status:** ✅ Done
**Apps:** trivial-tip-converter (this repo)
**Depends on:** none
**Blocks:** 01-02
**Reviewer class:** code
**Merge approval:** auto
**Deploy:** none
**Created:** 2026-07-07
**Completed:** 2026-07-07

---

## Context

The trivial tier needs a real, buildable, Vercel-deployable Next.js baseline before any domain logic
lands. This block lays down the app skeleton only — no tip/convert logic, no interactive UI — so later
blocks build forward on a known-clean foundation. `next build` must be offline-green (no remote font
fetch), a genuine constraint for any CI/sandbox runner with no network egress.

---

## Tasks

### T1: Scaffold the app

`create-next-app` baseline — App Router, TypeScript, Tailwind CSS. Strip the `next/font/google` import
from `layout.tsx` and use a system font stack instead, so `next build` never needs network access.

### T2: Ship deploy + dev-server config

Add `vercel.json` (Vercel-deployable). Wire the dev/start scripts to read the port from `$PORT`
(`next dev -p ${PORT:-3100}`) — never a hardcoded `3000` — so concurrent replicas never collide.

---

## Acceptance Criteria

| # | Criterion | Verification method | Owner |
|:--|:--|:--|:--|
| AC-1 | `npm run build` (`next build`) exits 0 with no network access | `cmd:npm run build` | engineer |
| AC-2 | `vercel.json` present at repo root | `cmd:test -f vercel.json` | engineer |
| AC-3 | Dev/start scripts read the port from `$PORT`, no literal `3000` | `cmd:grep -n 3000 package.json` (expect no match) | engineer |

---

## Out of Scope

- Domain logic (`src/lib/tip.ts`, `src/lib/convert.ts`) — 01-02.
- Interactive UI wiring the logic into the page — 01-03.

---

## Block Completion Gate

Do not mark this block done until:
- [x] All acceptance criteria PASS in the Completion Report (no UNVERIFIED entries)
- [x] Post-merge re-validation clean on trunk (no deploy check declared for this block)
- [x] User explicitly acknowledged the Completion Report and triggered session-end

Review is not a block-completion gate: the reviewer (per `Reviewer class:` above) is dispatched by the
supervising process on its own review cadence, not pulled in here.
