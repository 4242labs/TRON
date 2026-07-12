> ⚠️ **Status section is STALE — 2026-06-05.** Live block status lives in [`tron-backlog.md`](tron-backlog.md) §3 (B0/B2/B4 re-open against the converged workflow; B3 rebuild). Deps/waves below remain valid.

# TRON build — blocks index (from ADR-001)

**Source:** `tron-adr-001-deterministic-rebuild.md` + `tron-adr-002-interaction-model.md` (Proposed)
**Author:** SUPER-M (architect pass) · **Date:** 2026-06-04
**Block files:** `tron-blocks/` — one self-contained spec per block (ID · goal · acceptance criteria · scope · dependencies · owner), each with an ADR pointer so a fresh agent can be dispatched against it directly.

> These build **TRON itself**, not specs TRON dispatches into a host. Targets the `tron` canon repo (`~/42labs/tron/`).

---

## Blocks

| Block | File | Phase | Owner | Deps |
|:--|:--|:--|:--|:--|
| **B0** Blueprint contracts | `tron-blocks/B0-blueprint-contracts.md` | 0 | architect | — |
| **B1** Seeder alignment | `tron-blocks/B1-seeder-alignment.md` | 1 | engineer | B0 |
| **B2** Composition + canon content | `tron-blocks/B2-composition-canon-content.md` | 2 | engineer | B0 |
| **B3** Rails / engine | `tron-blocks/B3-rails-engine.md` | 3 | engineer | B0, B2 |
| **B4** `tron.md` judgment context | `tron-blocks/B4-tron-md-judgment-context.md` | 4 | engineer | B0, B3 |
| **B7** Interactive console | `tron-blocks/B7-interactive-console.md` | interaction (ADR-002) | engineer | B2, B3, B4 |
| **B5** E2E streamline review | `tron-blocks/B5-e2e-streamline-review.md` | 5 | reviewer | B1–B4, B7 |
| **B6** Packaging CLI *(deferred)* | `tron-blocks/B6-packaging-cli.md` | 6 | engineer | B5 |

## Dependency graph

```
B0 ──┬── B1 ───────────────────────┐
     └── B2 ──┬── B3 ── B4 ─────────┤
              └── B7 (B2,B3,B4) ────┤
                                    ├── B5 ── (B6, deferred)
B3, B4 ─────────────────────────────┘
```
(B7 = interactive console, ADR-002; needs B2+B3+B4. B5 now also joins B7.)

## Status

| Block | State | Note |
|:--|:--|:--|
| B0 | ✅ done | contracts canon (`bbd798a`); `edges:` key fix landed |
| B1 | ✅ done | seeder alignment merged to `tron` main (`ee327ea`); new tree + `project.yaml`/`workflow.yaml` outputs, Step 8 runs blueprint-lint. `on:`→`edges:` drift checked clean (seeder copies canon `workflow.yaml`, never authors the key); `max_concurrent_engineers` left `null` (no baked default) |
| B2 | ✅ done | `workflow.yaml` + `routing.yaml` + `messages.yaml` merged to `tron` main (`6756891`); lint L1–L13 clean — see `super-m/logs/log-260604-1620-tron-b2-composition-canon.md` |
| B3 | 🔄 in flight | the engine (`run.sh`, judgment tools, skills, scripts) — SUPER-M executing in parallel |
| B4 | ✅ done | `tron.md` judgment context merged to `tron` main (`9d961b0`); identity + standing rules (R1/R2/R3/R7/R8) + per-tool guidance for all 5 tools. Landed ahead of stated dep B3 (prose matched to B3's tool-invocation contract, no code import) — see `super-m/logs/log-260604-2100-tron-b4-tron-md.md` |
| B7 | ⬜ pending | interactive console (ADR-002) — bounded conversational front + fleet view; UX validated via `tron/prototype/tron-proto6.py` |
| B5–B6 | ⬜ pending | B5 joins B1–B4 + B7; B6 deferred |

## Parallel-dispatch waves

- **Wave 1:** B0 alone (gates everything; locks the contracts).
- **Wave 2:** B1 ∥ B2 (both unblocked once B0 lands).
- **Wave 3:** B3 (needs B2).
- **Wave 4:** B4 (needs B3) · B7 console (needs B2+B3+B4).
- **Wave 5:** B5 (join — needs B1+B2+B3+B4+B7).
- **Deferred:** B6 (after B5, on operator greenlight).

Only one block (B0) runs in true parallel-of-one first; real fan-out begins at Wave 2.
