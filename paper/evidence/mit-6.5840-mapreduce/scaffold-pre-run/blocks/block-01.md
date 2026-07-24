# Block 01 — MapReduce (MIT 6.5840 Lab 1)

test: bash run-oracle.sh

## Task

Implement MIT 6.5840 Lab 1: a distributed **MapReduce** system. Build a
**coordinator** that hands out map and reduce tasks and re-issues tasks from
workers that fail or stall, and a **worker** that repeatedly asks the coordinator
for a task, runs the application `Map`/`Reduce` (loaded as a plugin), reads its
input files, and writes its output files — all over RPC.

The authoritative specification is **`LAB.md`** (MIT's handout, mirrored
verbatim), including the "Your Job", "Rules", and "Hints" sections. Build to it.

## What to edit

- Implement in `src/mr/coordinator.go`, `src/mr/worker.go`, `src/mr/rpc.go`
  (new files under `src/mr/` are allowed if needed).
- **Do not** modify any other provided file — in particular the oracle and
  harness: `src/mr/mr_test.go`, `src/mr/util.go`, `src/main/*`, `src/mrapps/*`,
  `run-oracle.sh`. See `principles.md` §2–3.

## Definition of done (third-party oracle)

`bash run-oracle.sh` is green — i.e. MIT's `src/mr/mr_test.go` passes all eight
scenarios (word-count and indexer correctness, map parallelism, reduce
parallelism, job count, early exit, crash recovery) on a fresh trunk checkout.
No acceptance criteria are authored here; the course's tests are the sole judge.
