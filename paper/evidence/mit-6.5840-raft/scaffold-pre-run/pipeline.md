# Pipeline — permanent block register

Engine-owned: statuses are stamped by the engine's own verdict.

Raft is delivered in four parts, each gated by MIT's own tests. The blocks form
a dependency chain — every part builds on the one before and must not regress it
(the gate is cumulative), so they run in order, not in parallel.

| id | block | depends on | status | branch |
|:--|:--|:--|:--|:--|
| 01 | block-01 | —  | todo | feat/block-01 |
| 02 | block-02 | 01 | todo | feat/block-02 |
| 03 | block-03 | 02 | todo | feat/block-03 |
| 04 | block-04 | 03 | todo | feat/block-04 |
