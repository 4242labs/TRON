# Block 03 — Raft Part 3C: persistence (MIT 6.5840 Lab 3)

test: bash run-oracle.sh 3C
test-timeout: 1200

depends on: block-02 (3B)

## Task

Implement **persistence**: save Raft's persistent Figure 2 state (current term,
vote, log) via `persister.Save()` whenever it changes, and restore it in
`readPersist()` on restart so a crashed-and-rebooted peer rejoins correctly.
Complete `persist()`/`readPersist()` with `labgob` encoding. Passing 3C also
requires the fast log-backup optimisation so `TestFigure8Unreliable3C` and the
churn tests finish in time.

The authoritative specification is **`LAB.md`** → "Part 3C: persistence". The
gate is cumulative: 3A and 3B must stay green.

## What to edit

- Implement in `src/raft1/raft.go` (new files under `src/raft1/` allowed).
- **Do not** modify the oracle/harness or the provided packages (see
  `principles.md` §2–4).

## Definition of done (third-party oracle)

`bash run-oracle.sh 3C` is green — MIT's `raft_test.go` `-run '3A|3B|3C'` passes
all 3A/3B/3C tests (basic/more persistence, partitioned-leader restart, Figure 8
reliable + unreliable, reliable/unreliable churn) on a fresh trunk checkout,
within the course's per-test 120s and overall 600s limits. The course's tests
are the sole judge.
