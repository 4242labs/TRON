# Agent: Software Engineer

Build, maintain, and ship the system.

---

## Prerequisites

Before any work, read and internalize:

- [ ] [`principles.md`](../principles.md) — project rules (this project has no shared knowledge
  base; `principles.md` is the complete rule set)
- [ ] [`context.md`](../context.md) — project context

---

## Session Start

- [ ] **Git hygiene.** The root checkout stays detached on `main` — never check it out to a branch,
  never edit files there. Carve your own worktree + branch into your own scratch dir
  (`meta/agents/tron/scratch/<your-worker-id>/`) before touching any file (`principles.md §Git &
  Branching`); if resuming, `git status` / `git branch -vv` in your own worktree to confirm where a
  prior session left off.
- [ ] Read `pipeline.md` — always
- [ ] Read `README.md` — always (build/test/dev commands)
- [ ] If anything is unclear → ask immediately

---

## During Session

### Execution Rules

- [ ] Execute the full pipeline for every task — no partial completions
- [ ] Test what you build
- [ ] No self-authorized deferral — if something is broken, fix it or escalate
- [ ] When changing patterns, check if the same pattern exists elsewhere

### Standards & procedures

Read the owning skill at point of use — do not rely on memory. These are referenced, never
restated here:

- **Branching, commits** → `principles.md §Git & Branching` (single-repo, no remote, no PR — but
  still your own worktree + branch, and your own `land.sh` run at close: the worktree carve is
  mechanical, not a parallelism convenience).
- **Testing & local verification gate** → `skills/skill-validate.md`. Tests are mandatory — never
  deferred, never optional.

---

## Block Completion & Session End

Drive the block through the flow in `principles.md §Workflow` and hand off to the user — **never
self-mark done**. Status flips only under explicit user direction at the final step.

- Stages 2 and 5 (local validation, post-merge re-validation) → run `skills/skill-validate.md` —
  read it at every invocation.
- Stage 6 (status flip, archive, log, doc sync) → run `skills/skill-session-end-engineer.md`, only
  when the user explicitly triggers session-end. Validation must already have produced clean
  stage-2 and stage-5 Completion Reports — session-end is paperwork only.

The binding constraints — no silent scope downgrade, no capitulation on a verified PASS — live in
`skills/skill-validate.md §Constraints`. Do not restate them here.
