# Principles — conduct for every agent

1. Work only inside your own working copy; the trunk is read-only to you.
2. The tests are MIT's, not yours. **Never** edit, delete, or "adjust"
   `src/raft1/raft_test.go`, `test.go`, `util.go`, `server.go`, `proxy.go`, or
   anything under `raftapi/`, `labrpc/`, `labgob/`, `tester1/`, or
   `run-oracle.sh`. Make the code pass the tests; never make the tests pass the
   code. Editing the oracle or the harness is a hard failure, not a shortcut.
   Your Raft must work against the **original** `labrpc` — that is what grades it.
3. Implement only `src/raft1/raft.go` (new files under `src/raft1/` are allowed).
   Leave every other provided file in its original place — the course re-issues
   updates and expects that.
4. Raft peers may interact **only through RPC** — never through shared Go
   variables or files. This is a rule of the lab, not a style preference.
5. Small commits with honest messages; nothing uncommitted survives a seat.
6. Each part builds on the last and must not regress it. Follow Figure 2 of the
   extended Raft paper precisely; most "my Raft almost works" bugs are a
   departure from Figure 2.
7. When the spec is ambiguous, read `LAB.md` (the official handout) and the
   paper first; if still genuinely ambiguous, ASK — never invent a policy
   silently.
8. Judges verify by reading and running `bash run-oracle.sh <part>`, never by
   editing. Timing tests can be flaky under load; a judge re-runs before ruling.
9. Read `playbook.md` before building; when you learn something durable about the
   Go tooling, the harness, or a Raft pitfall, add it to `playbook.md` in your
   delivery.
10. Done is the course suite (up to and including this part) passing on a fresh
    trunk checkout — nothing more, nothing less.
