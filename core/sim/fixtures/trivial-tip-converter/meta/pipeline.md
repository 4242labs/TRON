# Trivial Tip Converter Pipeline

**Status:** Living Document
**Purpose:** Single source of truth for all product scope — what's being built, what's envisioned, and what needs fixing.

**Last Updated:** 2026-07-07

> This is the `trivial` tier of the Orchestrator's sim target set (`tron-meta/sims/README.md`) — a
> pure happy-path shakeout. It plants no walls and no `await_confirm`.

---

## How to Read This Document

**This is the ONLY status tracker for active work.** No other document tracks what's in progress, planned, or needs fixing.

**Status indicators:**

- **✅** — Done (implemented, tested, validated)
- **📋** — To do (scoped, not yet started)
- **🔄** — In progress
- **📌** — Deferred (reason noted)
- **🔧** — Open debt
- **❌** — Cut / Superseded
- **📦** — Folded into another block
- **✂️** — Split into multiple blocks

**Format contract.** This document follows a fixed shape so it stays parseable at a glance (and by tooling):

- Phases are `### Phase N: <Title>` headers; each owns one table.
- Every table has the columns `ID | Task | Status | Notes`, in that order.
- The **Status** cell holds exactly one emoji from the set above — no prose, no second glyph.
- When a row has a block file, its **Notes** cell names it as `` Block `blocks/<id>.md` ``.

---

## Roadmap

### Phase 1: Tip converter

📋 **Status:** To do

A single-page tip calculator and unit (distance / temperature) converter. Linear dependency chain,
depth 1, no fan-in — the trivial tier's grading shape.

| ID | Task | Status | Notes |
|:---|:-----|:-------|:------|
| 01-01 | Scaffold the Next.js + TS + Tailwind app, offline-green build, `vercel.json` | ✅ | Block `blocks/archive/01-01-scaffold.md` |
| 01-02 | Domain logic — `src/lib/tip.ts` + `src/lib/convert.ts`, genuine Vitest suite | 📋 | Block `blocks/01-02-logic.md` |
| 01-03 | UI — wire the domain logic into the single-page converter form | 📋 | Block `blocks/01-03-ui.md` |

---

## Technical Debt

Items that exist but are not yet scoped into a block.

| ID | Issue | Status | Notes |
|:---|:------|:-------|:------|
| TD-01 | none yet | — | — |

---

## Ad-hoc Blocks

Blocks not tied to a roadmap phase (cross-cutting fixes, hardening, hygiene).

| ID | Task | Status | Notes |
|:---|:-----|:-------|:------|
| ADHOC-01 | none yet | — | — |

---

## Backlog

Pipeline-adjacent items waiting to be promoted into a phase.

| ID | Task | Status | Notes |
|:---|:-----|:-------|:------|
| BL-01 | none yet | — | — |
