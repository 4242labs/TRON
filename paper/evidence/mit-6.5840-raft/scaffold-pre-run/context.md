# mit-6.5840-raft-tron — MIT 6.5840 Lab 3 (Raft) run through the Orchestrator

Implement the **MIT 6.5840 (Distributed Systems) Lab 3: Raft** — a replicated
state-machine protocol (leader election, replicated log, persistence, and log
compaction/snapshots) as a Go module used by a larger service — and drive it to
done through the Orchestrator's full flow, part by part.

**Why this project exists (read this first).** Almost every project this
Orchestrator has run was *specified and tested by the same people who built the
Orchestrator*. This one is not. The specification is MIT's public course handout
(mirrored verbatim in `LAB.md`) and the pass/fail oracle is MIT's own Go test
suite (`src/raft1/raft_test.go`). Neither was authored here. That independence is
the entire point — it is what makes a green run mean something an in-house
benchmark cannot. **Do not weaken it.** Raft is materially harder than Lab 1:
the tests inject network loss, reordering, partitions, and crashes, and several
are timing-sensitive. That is expected; build to Figure 2 of the paper.

## The integrity invariant (non-negotiable)

- The **only** file a worker implements is the one the lab tells you to:
  `src/raft1/raft.go`. You may add **new** files under `src/raft1/` if genuinely
  needed, but everything must keep working with the provided harness unchanged.
- **Never** edit, delete, or "fix" the oracle or the harness: `raft_test.go`,
  `test.go`, `util.go`, `server.go`, `proxy.go`, anything under `raftapi/`,
  `labrpc/`, `labgob/`, `tester1/`, or `run-oracle.sh`. The handout says Raft
  must work against the *original* `labrpc` — that is what grades it. Touching
  any of these voids the probe: a passing test then proves nothing.
- Done is decided **only** by MIT's tests passing. No acceptance criterion is
  authored in this repo; the gate runs the course suite verbatim.

## Stack

- **Go 1.22+** (the course's language). No other runtime. The Orchestrator is
  stack-agnostic — the gate simply runs the declared command.
- **Go 1.22+ must already be on `PATH`** on the machine that runs this. This is
  an environment prerequisite the scaffold assumes, like any provided asset;
  `run-oracle.sh` also probes the common install paths.

## The gate (the third-party oracle)

The declared test command is **`bash run-oracle.sh <part>`**. It `cd`s into
`src/raft1/` and runs **`go test -timeout 900s -run <part>`** — i.e. MIT's
`raft_test.go`, unmodified. Selection is **cumulative**: block 3B re-runs
`3A|3B`, block 3C re-runs `3A|3B|3C`, block 3D runs `3A|3B|3C|3D` (the complete
suite). A later part may therefore never silently regress an earlier one, and
the final block validates MIT's whole Raft suite.

MIT grades Raft **without** `-race` (see `LAB.md`); the gate matches the grade.
`-race` is the recommended developer bar and is verified out of band after
delivery, not by the gate. The suite exits non-zero on any assertion failure,
and a non-terminating implementation trips the `-timeout` into red, so the gate
cannot false-green.

## The task, in one line

Make MIT's Raft test suite pass — part by part, 3A→3B→3C→3D — by implementing
`src/raft1/raft.go`. The authoritative, verbatim specification is `LAB.md`
(mirrored from https://pdos.csail.mit.edu/6.5840/labs/lab-raft1.html). Build to
it and to Figure 2 of the extended Raft paper; the tests are the judge.
