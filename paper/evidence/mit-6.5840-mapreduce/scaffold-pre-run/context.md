# mit-6.5840-tron — MIT 6.5840 Lab 1 (MapReduce) run through the Orchestrator

Implement the **MIT 6.5840 (Distributed Systems) Lab 1: MapReduce** distributed
system — a coordinator process that hands out map/reduce tasks and copes with
failed workers, plus a worker process that executes them over RPC — and drive it
to done through the Orchestrator's full flow.

**Why this project exists (read this first).** Every other project this
Orchestrator has run was *specified and tested by the same people who built the
Orchestrator*. This one is not. The specification is MIT's public course handout
(mirrored verbatim in `LAB.md`) and the pass/fail oracle is MIT's own Go test
suite (`src/mr/mr_test.go`). Neither was authored here. That independence is the
entire point — it is what makes a green run mean something an in-house benchmark
cannot. **Do not weaken it.**

## The integrity invariant (non-negotiable)

- The **only** files a worker may create or edit are the three the lab tells you
  to implement: `src/mr/coordinator.go`, `src/mr/worker.go`, `src/mr/rpc.go`.
  You may add **new** files under `src/mr/` if genuinely needed.
- **Never** edit, delete, or "fix" the oracle or the harness: `src/mr/mr_test.go`,
  `src/mr/util.go`, `src/main/mrcoordinator.go`, `src/main/mrworker.go`,
  `src/main/mrsequential.go`, `src/mrapps/*`, or `run-oracle.sh`. Touching any of
  them voids the probe — a passing test then proves nothing.
- Done is decided **only** by MIT's tests passing. No acceptance criterion is
  authored in this repo; the gate runs the course suite verbatim.

## Stack

- **Go 1.22+** (the course's language). No other runtime. The Orchestrator is
  stack-agnostic — the gate simply runs the declared command.
- **Go 1.22+ must already be on `PATH`** on the machine that runs this (the gate
  builds Go plugins). This is an environment prerequisite the scaffold assumes,
  like any provided asset; `run-oracle.sh` also probes the common install paths.

## The gate (the third-party oracle)

The declared test command is **`bash run-oracle.sh`**. It:

1. builds the course-provided MapReduce apps as Go plugins (`mrapps/*.so`) and the
   `mrcoordinator` / `mrworker` / `mrsequential` binaries (these compile the
   worker's `mr/` code), then
2. runs **`go test -timeout 300s`** inside `src/mr/` — i.e. MIT's `mr_test.go`,
   unmodified.

`mr_test.go` runs eight scenarios: word-count and indexer correctness, map and
reduce parallelism, job-count, early-exit, and crash recovery. The suite exits
non-zero on any failure (and the stub hangs → the `-timeout` forces a red), so
the gate cannot false-green. Built artifacts (`*.so`, the binaries, `mr-*`
scratch) are gitignored, so the command is self-contained on a fresh trunk
checkout — not only in the worker's arena.

## The task, in one line

Make MIT's MapReduce test suite pass by implementing the coordinator and worker.
The authoritative, verbatim specification — job description, rules, and hints — is
`LAB.md` (mirrored from https://pdos.csail.mit.edu/6.824/labs/lab-mr.html). Build
to that; the tests are the judge.
