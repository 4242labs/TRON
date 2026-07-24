# Evidence — MIT 6.5840 Lab 3 (Raft) run through TRON

Third-party-specified-and-tested probe for paper objection #4 (Linear 42L-1121).
The specification and the pass/fail oracle were authored by MIT, not by us. This is
the *hard* probe: a full Raft implementation (leader election, log replication,
persistence, snapshots) graded by the course's own test suite.

## Benchmark (cite, do not redistribute)
- **MIT 6.5840 (Spring 2026), Lab 3: Raft** — https://pdos.csail.mit.edu/6.824/labs/lab-raft.html
- Starter code: `git://g.csail.mit.edu/6.5840-golabs-2026` (used verbatim as the trunk).
- **Oracle:** MIT's own `src/raft1/raft_test.go` — **28 tests**: 3A leader election (3),
  3B log replication (10), 3C persistence (8), 3D snapshots (7). Gate is cumulative:
  each block re-runs every part up to and including it, so block 04 runs the **complete**
  suite. Run via `run-oracle.sh`, which also builds `src/main/raft1d` before `go test`
  (mirroring MIT's own Makefile: the 2026 tester runs each Raft peer as a separate OS
  process exec'ing that daemon). MIT grades **without** `-race`; the gate matches.

The working solution is **not** published: 6.5840 forbids posting lab solutions, and the
starter is MIT's copyright. This archive holds only our authored scaffold + the engine's
decision log. To reproduce: fetch MIT's starter, apply `scaffold-pre-run/`, run TRON; the
gate is MIT's unmodified `raft_test.go`.

## Run
- Engine run id: `run-260723-153412` (2026-07-23). Flow `build-review-merge`.
- Config: headless defaults — worker/reviewer `claude-sonnet-5`, architect/AIDE `claude-opus-4-8`, scope=all.
- Outcome: **4/4 delivered, clean.** 0 operator pages, 0 walls, 0 turn-overruns.
  Every build-gate + review + merge-gate GREEN; **8/8 on-trunk `trunk_check` GREEN**.
- Wall clock: **169.7 min**. Per-block (dispatch→block_done): 3A **11.6 min**, 3B **29.0**,
  3C **42.2**, 3D **86.4** (3D re-runs the full 28-test suite each self-test, hence longest).

## Commit SHAs (private repo `mit-6.5840-raft-tron`)
- `804ba11` — pristine pre-run trunk (= `scaffold-pre-run/` + MIT starter; `raft.go` = MIT's 216-line stub).
- `fc00cfd` — `main` tip at run end (delivered state).
- Worker edited **only** `src/raft1/raft.go`; MIT's `raft_test.go` / `test.go` / `util.go` /
  `server.go` / `proxy.go` and the `raftapi` / `labrpc` / `labgob` / `tester1` packages —
  and `run-oracle.sh` — byte-for-byte untouched (integrity: the green is earned, not gamed).
  No acceptance criteria authored; the course's tests are the sole judge.

## Independent verification (outside the engine's own claim)
Fresh clone of `main`, no arena, no cached build artifacts, MIT's canonical steps by hand
(`go build -o main/raft1d main/raft1d.go` then `go test -run '3A|3B|3C|3D'`):
```
PASS
ok  	6.5840/raft1	413.538s   (exit 0)
```
All 28 tests, including the 3D install-snapshot / crash-and-restart / unreliable-network
scenarios. Matches the engine's on-trunk `trunk_check: ok` events in `events.jsonl`.

`-race` dev-bar pass (MIT grades without it), fresh clone, full suite:
```
PASS
ok  	6.5840/raft1	429.768s   (exit 0)
```
Zero data races across all 28 tests — the implementation is correct **and** race-free.

## Files here
- `events.jsonl` — the engine's typed decision log (path/user-scrubbed). Ground truth.
- `report.md`, `manifest.md` — run summary + seat roster (scrubbed).
- `scaffold-pre-run/` — our orchestrator-agnostic scaffold as it stood before dispatch
  (blocks + `run-oracle.sh` + context/principles/policy/playbook/README + pipeline). MIT
  copyright material (`LAB.md`, `Makefile`, `src/`) and post-run outputs (session logs) are
  deliberately excluded.

## Note on setup
Making MIT's suite *runnable* under the engine (the daemon-build step; per-block test and
turn budgets sized for a suite that legitimately runs minutes) was pre-experiment harness
work — setup, not part of the measured run. It is not a TRON result and is out of scope for
the paper's claims.
