# Pipeline — permanent block register

Engine-owned: statuses are stamped by the engine's own verdict.

| id | block | depends on | status | branch |
|:--|:--|:--|:--|:--|
| 01 | block-01 | — | todo | feat/block-01 |

One block by design. MapReduce (Lab 1) is a single cohesive deliverable gated by
one third-party test suite; splitting it into sub-blocks would mean authoring
sub-criteria here, which is exactly the independence this probe must not spend.
The natural multi-block follow-on is Lab 3 (Raft), whose own `go test -run`
targets (3A/3B/3C/3D) give honest, course-authored block boundaries.
