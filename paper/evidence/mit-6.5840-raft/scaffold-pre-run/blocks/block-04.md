# Block 04 — Raft Part 3D: log compaction / snapshots (MIT 6.5840 Lab 3)

test: bash run-oracle.sh 3D
test-timeout: 1200

depends on: block-03 (3C)

## Task

Implement **log compaction via snapshots**. Implement `Snapshot(index,
snapshot)` so the service can tell Raft to discard log entries up to `index`;
persist the snapshot alongside the Raft state; send an `InstallSnapshot` RPC from
leader to a follower whose log is too far behind; and hand installed snapshots to
the service on `applyCh`. Your log indexing must keep working once the log's
front has been trimmed away.

The authoritative specification is **`LAB.md`** → "Part 3D: log compaction". The
gate is cumulative and runs MIT's **complete** Raft suite: 3A, 3B, and 3C must
stay green.

## What to edit

- Implement in `src/raft1/raft.go` (new files under `src/raft1/` allowed).
- **Do not** modify the oracle/harness or the provided packages (see
  `principles.md` §2–4).

## Definition of done (third-party oracle)

`bash run-oracle.sh 3D` is green — MIT's `raft_test.go` `-run '3A|3B|3C|3D'` (the
whole Raft suite, all 28 tests including the snapshot install/crash scenarios)
passes on a fresh trunk checkout, within the course's per-test 120s and overall
600s limits. This block's green means the entire third-party Raft oracle passes.
The course's tests are the sole judge.
