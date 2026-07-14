# Principles — Trivial Tip Converter

Agent behavior rules for this project. All agents must read and internalize this file before any
session.

---

## Configuration

This project has **no shared knowledge base** — every rule it needs is written directly in this
file, `context.md`, and the `skills/` directory below. Self-contained; no external lookup, no
runtime path variable to resolve.

---

## Core Rules

1. **Tests are mandatory.** Never defer tests or offer them as optional. Include in the same commit
   as the code they cover.
2. **Branch before touching any file.** No exceptions, including `meta/`, logs, or `pipeline.md`.
   Always a feature branch, never a direct commit on `main`.
3. **Merge only when authorized.** A block's branch merges into `main` once its acceptance criteria
   pass — per this project's `Merge approval:` field (every block in this tier is `auto`; there are
   no `needs-user` blocks in the trivial tier).
4. **Fix what you find.** Engineer: fix immediately. Reviewer: report only (no code changes).
5. **No shortcuts.** Lead with root-cause, highest-standard, long-term fix. No band-aids.
6. **Never defer issues.** Every finding gets fixed. Never ask whether to defer.
7. **Be terse.** One sentence per finding. Lead with conclusion. No headers for simple answers.
8. **Update docs continuously.** Update `pipeline.md`, `context.md`, and session logs throughout the
   session. Never defer to session end.

---

## Git & Branching (single-repo, no remote)

This repo has **no git remote** (`repo.remote: none`) — a local shakeout. There is no GitHub, no PR,
no CI run to watch. The root checkout stays **detached** at seat (never on `main`) so the trunk ref
can advance by ref alone, race-free — never edit files there. The full procedure (ADR-0002 D1/D2 —
grant → land-script → observe; the worker's hands, never the Orchestrator's):

1. **Carve your own worktree.** Your spawn cwd is your own scratch dir
   (`meta/agents/tron/scratch/<your-worker-id>/`, gitignored) — your first act is carving your own
   worktree + branch there, off the current trunk tip: `git worktree add <scratch-dir>/<slug> -b
   {type}/{block-id}-{slug} main` (`type` in `feat|fix|chore`). Never carve on the shared root
   checkout — it is not yours to touch.
2. **Build + commit.** Work happens in your own worktree, on your own branch, only. Commit
   subjects: lowercase, present tense.
3. **Close: rebase, re-validate, land.** Once the block's acceptance criteria pass
   (`skill-validate.md`), rebase your branch onto current trunk in your own worktree and
   re-validate — do this before every close, never skip it. Report; once your merge is authorized
   (`Merge approval:` is `auto` for every block in this tier — no `needs-user` blocks here), the
   Orchestrator mints a one-time, block-scoped grant. Run `meta/scripts/land.sh <case-id>` yourself
   — the **only** sanctioned way to advance trunk locally. It validates your grant, fast-forwards
   trunk to your tip, and consumes the grant. The Orchestrator never merges, rebases, or lands
   anything itself — code or paperwork — it only mints the grant and observes the landed result.
   If `land.sh` refuses your land as **non-fast-forward** (trunk moved after your grant was
   approved), rebase your branch again onto current trunk and re-land. A **pure** rebase (same
   diff) keeps your existing grant; a **content-changing** rebase re-asks the gate.
4. **Clean up.** Remove your own worktree and delete your own branch once landed
   (`git worktree remove` + `git branch -d {branch}`) — your close ritual, never the
   Orchestrator's.

One branch per block, one worktree per worker. Even at this project's single-agent scale, the
worktree carve is mechanical, not optional: it is what keeps the root checkout detached and the
trunk ref safe to advance by compare-and-swap.

---

## Workflow — canonical flow (trivial tier)

Every block: build → validate → merge → session-end. PR/CI/staging steps are inapplicable (no
remote, no deploy check) — status flips only under explicit user trigger, never automatically.

1. **Build** — tasks coded, tested locally, committed on the block's branch.
2. **Local validation** — run `skill-validate.md`. Every acceptance criterion verified. Completion
   Report produced in the engineer's session log.
3. **User-test gate** — hand off the Completion Report; mandatory for any visible/behavioral change.
   Engineer does not proceed past this step without explicit user go-ahead.
4. **User approves → engineer lands** `{branch} → main` via the grant + `land.sh` ritual (see Git &
   Branching above). No PR, no CI to watch (no remote); the Orchestrator mints the grant, the
   engineer runs the script.
5. **Post-merge re-validation** — re-run `skill-validate.md` against `main`; engineer self-attests.
   Reviewers are dispatched by the Orchestrator on its own review cadence — never here.
6. **User triggers session-end** — only then `skill-session-end-engineer.md §6` flips
   `**Status:** ✅ Done`, archives the block file, updates `pipeline.md`.

| Step | Skill | Section |
|:-----|:------|:--------|
| 1 Build | (engineer's normal coding loop) | — |
| 2 Local validation + 3 User-test gate | `skill-validate.md` | §1–§5 |
| 4 Merge | (this file, §Git & Branching) | — |
| 5 Post-merge re-validation | `skill-validate.md` | §1–§4, §6 |
| 6 Status flip | `skill-session-end-engineer.md` | §6 |

---

## Skills Registry

| Skill | File | Trigger |
|-------|------|---------|
| Validate | `skills/skill-validate.md` | Pre-merge local validation and post-merge re-validation |
| Code Review | `skills/skill-review-code.md` | Code quality audits — dispatched on the review cadence (`cadence.code` in `meta/tron/knobs.yaml`) |
| Block Forward Review | `skills/skill-block-forward-review.md` | Architect — dispatched by the Orchestrator when a block lands done; reconcile upcoming blocks against learnings/drift |
| Session End | `skills/skill-session-end-{role}.md` | End of every session |

---

## Branching Convention

- Default branch: `main`
- Feature flow: `feat|fix|chore/<block-id>-<slug>` — carved into its own worktree, landed via
  grant + `land.sh` by the engineer once authorized (no PR, no remote)
- Commit subjects: fully lowercase

---

## Core Docs

Every agent reads these at session start:

- `pipeline.md` — always
- `context.md` — always
- `README.md` — project commands (`npm run build` / `npm test` / `npm run dev`)

**Rules:**

- [ ] **Same-session update.** If your work changes what a Core Doc describes — update it in the
  same session. A code change without a doc update is incomplete delivery.
- [ ] **One-line `Last Updated`.** Replace the existing line — never append `Previous:` chains or
  essay paragraphs. Format: `**Last Updated:** YYYY-MM-DD — short reason.`
- [ ] **Block titles are short.** Pipeline `Task` column = single short sentence. Detail belongs in
  the block file.
