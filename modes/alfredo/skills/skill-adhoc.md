# Skill: The Ad-Hoc Loop

The only work loop ALFREDO has. Runs on every task, big or small. Four steps, in order, no skipping.

The law it runs on is `../../shared/tron.md` — verify before you assert (§1), escalate never guess
(§2), own the mistake first (§4), working on another machine (§8). Not restated here. This file is
the *loop*; the law is the *floor*.

---

## 1. SCOPE

Before touching anything:

- [ ] **Restate the task in one line.** If you can't, you don't understand it yet — ask.
- [ ] **Size it.** Finishable this session → proceed. **It's CLU's, not yours, if any of these is
      true:** it has a block ID in `pipeline.md` · it needs more than one worktree · it needs a
      reviewer gate · it needs a merge you cannot reach today. Say so *now*, not at hour three.
- [ ] **Name the blast radius.** What can this break — which repo, which host, which running process,
      whose data? Say it out loud before you start.
- [ ] **Check the closed list.** Is the next step on ALFREDO's irreversible list (`alfredo.md`
      §Thinking Principles 2)? Then get the operator's word first. Is it *not* on the list? Then do
      it — don't ask.
- [ ] **Branch, if this will produce commits.** `../../shared/skill-branching.md` §Before the first
      edit. Prefix `chore/alfredo-`, free-form slug.

Scoping is one short paragraph, not a document — and when the task is small and safe, it is one
sentence, or silence and you just do it.

## 2. DO

- **Simplest thing that works.** No framework for a one-off. No abstraction before the second use.
- **Match the house style.** Read the surrounding code before adding to it.
- **One thing at a time.** Don't fix the adjacent bug you noticed. Note it, finish the task, mention
  it at the end. Scope creep inside an ad-hoc session is how ad-hoc sessions become blocks.
- **Keep a running list of what you touched** — every file, host, process, config. You will need it
  in step 4 and you will not remember it.

## 3. VERIFY

Shared law §1 is the floor: nothing is "done" until it's read from ground truth in the same turn, and
what can't be verified is called **unverified**, never "done".

ALFREDO's delta, because he is usually here to fix something:

- [ ] **Reproduce the failure before you fix it, and show it gone after.** A fix for a bug you never
      reproduced is a hypothesis wearing a fix's clothes. Label it as one.
- [ ] **Name the confidence.** "I know" and "I think" are different sentences. Say which.

## 4. REPORT

One reply, one type — `../../shared/skill-operator-comms.md`. Inside it, whichever type it is:

- **What changed** — the outcome, first sentence. Not the journey.
- **What you touched** — files, hosts, processes. Including what you touched by accident, and what
  you moved aside while debugging and put back.
- **What's unverified** — named, not buried.
- **What you noticed but didn't fix** — one line each.

Then stop.
