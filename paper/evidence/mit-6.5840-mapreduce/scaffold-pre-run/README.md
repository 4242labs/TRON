# mit-6.5840-tron

A **third-party-specified** Orchestrator run: implement **MIT 6.5840 Lab 1
(MapReduce)** and drive it to done. Unlike an in-house project, the specification
(`LAB.md`, mirrored from MIT's public handout) and the pass/fail oracle
(`src/mr/mr_test.go`, MIT's own Go test suite) were authored by an independent
third party. That independence is the point — see `context.md`.

This directory is a **project instance** for an orchestrator to run: the plan
(`context.md`, `pipeline.md`, `principles.md`, `policy.md`, `playbook.md`,
`blocks/`) wrapped around MIT's provided starter code under `src/`. The
orchestrator dispatches the block, a worker implements it in an isolated arena,
and the gate runs MIT's tests to decide done. Start at `pipeline.md`; build to
`context.md`; the spec is `LAB.md`.

## The integrity invariant

Workers edit **only** `src/mr/coordinator.go`, `src/mr/worker.go`,
`src/mr/rpc.go`. The oracle and harness (`src/mr/mr_test.go`, `src/mr/util.go`,
`src/main/*`, `src/mrapps/*`, `run-oracle.sh`) are **never** edited — touching
them voids the probe.

## Running the tests directly

```sh
bash run-oracle.sh      # builds course plugins + binaries, runs MIT's go test
```

Requires **Go 1.22+** on `PATH` (the gate builds Go plugins). Built artifacts are
gitignored, so the command is self-contained on a fresh checkout.

Not affiliated with MIT. Course starter code © its authors, used here to run and
evaluate an orchestration; see https://pdos.csail.mit.edu/6.824/ .
