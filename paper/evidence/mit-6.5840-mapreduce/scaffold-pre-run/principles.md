# Principles — conduct for every agent

1. Work only inside your own working copy; the trunk is read-only to you.
2. The tests are MIT's, not yours. **Never** edit, delete, or "adjust"
   `src/mr/mr_test.go`, `src/mr/util.go`, `src/main/*`, `src/mrapps/*`, or
   `run-oracle.sh`. Make the code pass the tests; never make the tests pass the
   code. Editing the oracle is a hard failure, not a shortcut.
3. Implement only `src/mr/coordinator.go`, `src/mr/worker.go`, `src/mr/rpc.go`
   (new files under `src/mr/` are allowed). Leave every other provided file in
   its original place — the course may re-issue updates and expects that.
4. Small commits with honest messages; nothing uncommitted survives a seat.
5. When the spec is ambiguous, read `LAB.md` (the official handout) first; if
   still genuinely ambiguous, ASK — never invent a policy silently.
6. Judges verify by reading and running `bash run-oracle.sh`, never by editing.
7. Read `playbook.md` before building; when you learn something durable about the
   Go tooling or the harness, add it to `playbook.md` in your delivery.
8. Done is the course suite passing on a fresh trunk checkout — nothing more,
   nothing less.
