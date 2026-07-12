# SUPER-M Session: 2026-06-04

**Mode:** BUILD (executing block B2 as engineer)
**Project:** TRON deterministic rebuild (`~/42labs/tron/`)
**Block:** B2 — Composition + canon content · Wave 2 (∥ B1)

## Summary
Authored the three canon data files the rails read. Merged to `tron` main (FF). Lint L1–L13 self-checked clean.

## Delivered (in `tron/`)
| File | Encodes |
|:--|:--|
| `routing.yaml` | Primitive library (fixed edges), closed 19-tag→action map, invalid-output policy, judgment-tool refs. Clean runnable YAML (placeholders stripped). |
| `workflow.yaml` | Embedded default composition: R1 persistent architect, R5 `review(architect)` no cadence, R4 `review(reviewer)` cadence `every_n_blocks: reviewer_threshold`, `findings-triage`→fix blocks, R3 wall→`escalate`. |
| `messages.yaml` | 17 emit-point templates, landing-page voice, zero host-runtime names. |

## Decisions
1. **`on:`→`edges:`** — surfaced the YAML 1.1 boolean-coercion footgun on the bare `on` key. Operator escalated to B0; canon fixed in `bbd798a` (key renamed `edges:`). Rebased B2 onto it. Routing's `edges:` is a list *value*, not a key — unaffected.
2. **`max_concurrent_engineers: ~`** — required per-session input, no baked default (per `workflow.example.md`). Encoded absence explicitly; runner refuses to start until set.
3. **No `gate` step in the default** — not in B2's required-default list; `gate(ci)` primitive still ships in `routing.yaml` for projects to compose.
4. **`next` = block-complete/next-block only** — all intra-block forward moves use explicit step ids, so bindings are unambiguous regardless of how B3 treats positional `next`.

## Git
- Branch `feat/b2-composition-canon-content` → FF-merged to `tron` main (`6756891`), pushed, branch + worktree removed. Clean.
- B1 (seeder) ran in parallel; no collision (B2 fenced to the three new files).

## Next
- **B3** (rails/engine) unblocked — needs B0 + B2. It will consume these files; the `edges:` key and `~` sentinel are the two parser-contract items B3 must honor.
