# Block 01 — Raft Part 3A: leader election (MIT 6.5840 Lab 3)

test: bash run-oracle.sh 3A
test-timeout: 1200

## Task

Implement Raft **leader election and heartbeats** (`AppendEntries` RPCs with no
log entries): a single leader is elected, stays leader with no failures, and a
new leader takes over when the old one fails or is partitioned. Add the Figure 2
election state to the `Raft` struct, fill in `RequestVoteArgs`/`RequestVoteReply`,
implement the `RequestVote` handler and the election ticker, define and send
periodic `AppendEntries` heartbeats, and implement `GetState()`.

The authoritative specification is **`LAB.md`** → "Part 3A: leader election"
(MIT's handout, mirrored verbatim) and Figure 2 of the extended Raft paper.
Heartbeats ≤10/sec; a new leader within 5s of a failure.

## What to edit

- Implement in `src/raft1/raft.go` (new files under `src/raft1/` allowed).
- **Do not** modify any other provided file — the oracle/harness (`raft_test.go`,
  `test.go`, `util.go`, `server.go`, `proxy.go`) or the `raftapi`/`labrpc`/
  `labgob`/`tester1` packages, or `run-oracle.sh`. See `principles.md` §2–4.

## Definition of done (third-party oracle)

`bash run-oracle.sh 3A` is green — MIT's `raft_test.go` `-run 3A` passes
(`TestInitialElection3A`, `TestReElection3A`, `TestManyElections3A`) on a fresh
trunk checkout. No individual test may exceed 120s and the part must finish well
under the course's 600s cap. No acceptance criteria are authored here; the
course's tests are the sole judge.
