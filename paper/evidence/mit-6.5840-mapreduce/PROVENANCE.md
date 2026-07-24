# Evidence — MIT 6.5840 Lab 1 (MapReduce) run through TRON

Third-party-specified-and-tested probe for paper objection #4 (Linear 42L-1121).
The specification and the pass/fail oracle were authored by MIT, not by us.

## Benchmark (cite, do not redistribute)
- **MIT 6.5840 (Spring 2026), Lab 1: MapReduce** — https://pdos.csail.mit.edu/6.824/labs/lab-mr.html
- Starter code: `git://g.csail.mit.edu/6.5840-golabs-2026` (used verbatim as the trunk).
- **Oracle:** MIT's own `src/mr/mr_test.go` (8 scenarios: wc + indexer correctness,
  map/reduce parallelism, job count, early exit, crash recovery), run via `run-oracle.sh`.

The working solution is **not** published: 6.5840 forbids posting lab solutions, and
the starter is MIT's copyright. This archive holds only our authored scaffold + the
engine's decision log. To reproduce: fetch MIT's starter, apply `scaffold-pre-run/`,
run TRON; the gate is MIT's unmodified test.

## Run
- Engine run id: `run-260723-094148` (2026-07-23). Flow `build-review-merge`.
- Config: headless defaults — worker/reviewer `claude-sonnet-5`, architect/AIDE `claude-opus-4-8`, scope=all.
- Outcome: **1/1 delivered, clean.** No walls, no operator pages. Review APPROVED cycle 1.

## Commit SHAs (private repo `mit-6.5840-tron`)
- `424cadc` — initial scaffold + MIT starter (pre-run trunk; = `scaffold-pre-run/`).
- `a8527aa` — delivered block-01 landed on `main`.
- `0ec5ca9` — `main` tip at run end (delivered state).
- Worker edited **only** `src/mr/coordinator.go`, `src/mr/worker.go`, `src/mr/rpc.go`;
  oracle + harness (`mr_test.go`, `util.go`, `main/*`, `mrapps/*`, `run-oracle.sh`)
  byte-for-byte untouched (integrity: the green is earned, not gamed).

## Independent verification (outside the engine's own claim)
Fresh clone of `main`, no arena, no cached build artifacts, MIT oracle run by hand:
```
PASS
ok  	6.5840/mr	88.663s   (exit 0)
```
Matches the engine's two on-trunk `trunk_check: ok` events in `events.jsonl`.

## Files here
- `events.jsonl` — the engine's typed decision log (path/user-scrubbed). Ground truth.
- `report.md`, `manifest.md` — run summary + seat roster (scrubbed).
- `scaffold-pre-run/` — our orchestrator-agnostic scaffold as it stood before dispatch
  (clean; the post-run `playbook.md` in the live repo contains solution hints and is
  deliberately excluded).
