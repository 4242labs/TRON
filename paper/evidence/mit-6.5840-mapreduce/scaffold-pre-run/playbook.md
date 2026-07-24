# Playbook — shared infra memory

Durable, project-specific how-to knowledge. Agents UPDATE this file (on their
branch, like any file) when they learn something lasting; judges hold deliveries
to it.

- **Run the oracle from anywhere:** `bash run-oracle.sh`. It `cd`s into `src/`,
  builds the course-provided plugins (`mrapps/*.so`) and the `mrcoordinator`/
  `mrworker`/`mrsequential` binaries, then runs `go test -timeout 300s` in
  `src/mr/`. That `go test` **is** the grade (MIT's `mr_test.go`).
- **Go 1.22+ must be on `PATH`.** The gate builds `-buildmode=plugin`, which
  needs a real Go toolchain. `run-oracle.sh` also adds `~/.local/go/bin` and
  `/usr/local/go/bin` to `PATH`. Built artifacts are gitignored, so a fresh trunk
  checkout rebuilds them — the command is self-contained.
- **Files you implement:** `src/mr/coordinator.go`, `src/mr/worker.go`,
  `src/mr/rpc.go`. Everything else under `src/` is course-provided and off-limits
  to edits (see `principles.md` §2–3).
- **Borrow from `src/main/mrsequential.go`** — it shows the Map/Reduce plugin
  loading, the `KeyValue` shape, and the expected `mr-out-*` output format. The
  distributed output, sorted and unioned, must match the sequential output.
- **The coordinator is invoked as** `mrcoordinator <sockname> <inputfiles...>`
  and the worker as `mrworker <app.so> <sockname>` (see `src/main/*.go`). Workers
  talk to the coordinator over a Unix-domain socket named by `coordinatorSock()`
  in `rpc.go`. The coordinator must exit (`Done() == true`) when all work is
  finished, or the harness hangs and the gate times out red.
- **Determinism traps in the test:** a task not reassigned within ~10s of a
  worker stalling fails the crash test; a worker or coordinator exiting *before*
  the job is done fails the early-exit test. Design for both.
- Use `LC_COLLATE=C` semantics if you sort — the reference output is byte-sorted.
