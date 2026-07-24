# mit-6.5840-raft-tron

A **third-party-specified** Orchestrator run: implement **MIT 6.5840 Lab 3
(Raft)** and drive it to done, part by part. Unlike an in-house project, the
specification (`LAB.md`, mirrored from MIT's public handout) and the pass/fail
oracle (`src/raft1/raft_test.go`, MIT's own Go test suite) were authored by an
independent third party. That independence is the point — see `context.md`.

This directory is a **project instance** for an orchestrator to run: the plan
(`context.md`, `pipeline.md`, `principles.md`, `policy.md`, `playbook.md`,
`blocks/`) wrapped around MIT's provided starter code under `src/`. The
orchestrator dispatches each block, a worker implements it in an isolated arena,
and the gate runs MIT's tests to decide done. Start at `pipeline.md`; build to
`context.md`; the spec is `LAB.md`.

## The integrity invariant

Workers implement **only** `src/raft1/raft.go` (new files under `src/raft1/`
allowed). The oracle and harness — `raft_test.go`, `test.go`, `util.go`,
`server.go`, `proxy.go`, and the `raftapi`/`labrpc`/`labgob`/`tester1` packages,
plus `run-oracle.sh` — are **never** edited. Touching them voids the probe.

## Running the tests directly

```sh
bash run-oracle.sh 3A     # leader election
bash run-oracle.sh 3B     # + log replication
bash run-oracle.sh 3C     # + persistence
bash run-oracle.sh 3D     # full suite (+ snapshots)
```

Requires **Go 1.22+** on `PATH`. Selection is cumulative (3D runs the whole
suite). MIT grades without `-race`; the gate matches that.

This tester runs each simulated Raft peer as a separate OS process, exec'ing a
prebuilt `src/main/raft1d` binary. `go test` builds that binary itself (via a
`TestMain` in `src/raft1/daemon_build_test.go`) before any test runs, so
`run-oracle.sh` works from a clean checkout with no separate build step; see
`playbook.md` for why that file exists.

Not affiliated with MIT. Course starter code © its authors, used here to run and
evaluate an orchestration; see https://pdos.csail.mit.edu/6.5840/ .
