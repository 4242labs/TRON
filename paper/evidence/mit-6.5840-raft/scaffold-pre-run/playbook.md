# Playbook — shared infra memory

Durable, project-specific how-to knowledge. Agents UPDATE this file (on their
branch, like any file) when they learn something lasting; judges hold deliveries
to it.

- **Run the oracle:** `bash run-oracle.sh <part>` where `<part>` is `3A`, `3B`,
  `3C`, or `3D`. It `cd`s into `src/raft1/` and runs `go test -timeout 900s -run
  <part>` — MIT's `raft_test.go`. That `go test` **is** the grade. Selection is
  cumulative (3B re-runs 3A too, etc.), so keep earlier parts green.
- **Go 1.22+ must be on `PATH`.** `run-oracle.sh` also adds `~/.local/go/bin` and
  `/usr/local/go/bin` to `PATH`.
- **The file you implement:** `src/raft1/raft.go`. New files under `src/raft1/`
  are allowed. Everything else under `src/` is course-provided and off-limits to
  edits (see `principles.md` §2–3) — including the whole test/harness set and the
  `labrpc`/`labgob`/`tester1` packages.
- **The interface you satisfy** is `src/raftapi/raftapi.go` (`Start`, `GetState`,
  `Snapshot`, `PersistBytes`) plus `Make(...)`. The tester talks to your Raft
  only through these and through the `applyCh` you are handed in `Make`.
- **Read `LAB.md`** (MIT's handout, mirrored verbatim) and Figure 2 of the
  extended Raft paper before building. The handout's per-part sections list the
  exact behaviours each part's tests check.
- **Grading is without `-race`; develop with `-race`.** Timing-sensitive tests
  (elections, agreement deadlines) can flake under machine load; if a test fails,
  re-run it a few times before concluding the code is wrong, and prefer fixing a
  real timing/correctness bug over widening a timeout you don't control.
- **The daemon binary gap (read this before you touch `run-oracle.sh` or
  panic at a nil-pointer from `DaemonClnt.Call`).** This course version's
  tester runs each simulated Raft peer as a separate OS process, exec'ing a
  prebuilt binary at `src/main/raft1d` (see `src/tester1/daemonclnt.go`). That
  binary is a `go build` artifact, is gitignored, and **nothing in
  `run-oracle.sh` builds it** — so `go test -run 3A` on a truly fresh checkout
  fails immediately (nil pointer in `DaemonClnt.Call`), no matter how correct
  `raft.go` is. Fixing `run-oracle.sh` itself is off-limits (principles §2).
  The fix lives in `src/raft1/daemon_build_test.go` (+ `race_on_test.go` /
  `race_off_test.go`): a `TestMain` that `go build`s `src/main/raft1d.go` to
  `src/main/raft1d` before any test runs, mirroring `-race` onto that build so
  `go test -race` still catches races in the actual Raft logic (which executes
  in that separate daemon process, not in the `go test` binary). These are new
  files under `src/raft1/`, permitted by principles §3 — they don't touch or
  weaken the oracle, they just make the harness's own build step happen. If a
  later part adds another daemon (unlikely for Raft-only parts 3A-3D), extend
  `buildRaftDaemon()` rather than re-deriving this from scratch.
