# Block 02 — Raft Part 3B: log replication (MIT 6.5840 Lab 3)

test: bash run-oracle.sh 3B
test-timeout: 1200

depends on: block-01 (3A)

## Task

Implement the leader and follower code to **append new log entries**. Implement
`Start()`, send/receive entries via `AppendEntries` following Figure 2, commit
entries once replicated on a majority, and deliver each newly committed entry on
`applyCh`. Implement the election restriction (paper §5.4.1) so only up-to-date
candidates can win.

The authoritative specification is **`LAB.md`** → "Part 3B: log". The gate is
cumulative: 3A must stay green.

## What to edit

- Implement in `src/raft1/raft.go` (new files under `src/raft1/` allowed).
- **Do not** modify the oracle/harness or the provided packages (see
  `principles.md` §2–4). Raft peers interact **only** through RPC.

## Definition of done (third-party oracle)

`bash run-oracle.sh 3B` is green — MIT's `raft_test.go` `-run '3A|3B'` passes all
3A and 3B tests (basic/failed/concurrent agreement, RPC byte + count limits,
rejoin, fast backup, follower/leader failure) on a fresh trunk checkout, within
the course's per-test 120s and overall 600s limits. The course's tests are the
sole judge.
