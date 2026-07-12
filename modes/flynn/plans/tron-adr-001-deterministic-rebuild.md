# ADR-001 — TRON deterministic rebuild (FSM + scripted I/O)

**Status:** Accepted — **partially superseded (2026-06-05)** by the converged workflow ([`tron-workflow-v2-skills.csv`](tron-workflow-v2-skills.csv); see [`tron-backlog.md`](tron-backlog.md) §1). The FSM + scripted-I/O foundation holds; the review-as-verdict model, status set, and dispatch shape are replaced — conform to the backlog.
**Date:** 2026-06-04
**Authors:** operator + SUPER-M
**Supersedes:** the v1 LLM-improvised architecture (`tron-goes-live-01.md`, `tron-goes-live-02.md` capture the prior rewrite path; the seeder built there is kept and reviewed, not discarded).

---

## Context

TRON v1 is an LLM-heavy supervisor: behavior is improvised by the model at runtime from prose markdown. Costs: output drift, verbosity, unpredictable terminal text, hard to audit, many LLM calls.

Goal: make TRON **as robotic as possible** — strict scripts and flows, minimal LLM. The LLM enters only for (a) classifying messages, (b) a small set of genuine judgment calls, (c) filling slots in pre-set sentences. It never decides what happens next.

2026 practice supports this (researched 2026-06-04):
- **"Blueprint First, Model Second"** — deterministic workflow with the LLM as a constrained component ([arxiv 2508.02721](https://arxiv.org/abs/2508.02721)).
- Separate **deterministic orchestration** (FSM / graph / durable workflow) from **non-deterministic reasoning**; offload everything solvable to a non-LLM layer. Reported ~80% fewer tool/LLM calls.
- Production standard is two-layer (durability à la Temporal + reasoning à la LangGraph). TRON is the **lightweight, turn-based, no-daemon** version of this: shell scripts + state files + a cron tick stand in for the durable engine.

---

## Decision

Rebuild TRON **from scratch** as a **script-driven finite state machine**. No reuse of v1 files. Exception: pure mechanical connectors with no behavior (e.g. the Telegram send/poll shell) may be carried **after review**.

### The two layers

1. **Workflow definition** — *what this project's orchestration is*. A per-project **composition** of standard steps + knobs (set at seed). Not the mechanics — just the choice of steps, order, roles, and checks.
2. **Operational layer** — *how TRON reasons*. Prose in `tron.md` + worker agent files. Canon, judgment-only, doesn't vary per project.

### Workflow = composed steps (C-A resolution)

The orchestration flow is **composed**, not hardcoded and not free-form per project.

- **Canon-invariant — the step primitives.** A small, fixed menu of generic step types, each verified once and shipped with TRON: `dispatch(role)`, `review(role)`, `gate(kind)`, `escalate`, `findings-triage`. Each primitive has defined enter/exit edges and which judgment tool it calls.
- **Per-project — the composition.** An ordered list of those steps with the roles/checks filled in, plus knobs (threshold, git on/off, peer-consult pairs). Lives in `workflow.yaml`, set at seed.

So a project adds CI / security review / data-architect by *naming* them into existing primitives (`gate(ci)`, `review(security)`, `dispatch(data-architect)`) — **no change to TRON**. Only a genuinely new *kind* of step (e.g. fan-out/join, loop-until, wait-for-external-event) is a canon change: a new primitive shipped to all installs. The seeder writes the **composition** (in `workflow.yaml`); it never authors primitives or routing.

### Single entry point (C-B resolution)

The wake path is: **cron heartbeat → `run.sh` → shells out to `claude -p` per typed tool → control returns to `run.sh`.** `run.sh` is the executor; `tron.md` is **not** an executor — it is the prompt context the bounded judgment tools run under. There is one spine, and it is the runner.

### Deterministic vs LLM

**Deterministic (scripts + state files — no LLM):**
- read/write state, ledger, counters
- choose next block (pipeline order + spec deps)
- spawn / resume / release / kill workers
- sweep: liveness + stall detection
- reviewer fires every N blocks
- routing: reviewer-done → resume architect; block-done → architect review; threshold → reviewer
- select which canned sentence to emit

**LLM (only here):**
- classify operator/worker message → situation tag
- judgment: architect agrees with a finding? scope of a fix block? wall-vs-solvable? stalled-vs-slow?
- fill template slots; supply a judgment payload when the content *is* a judgment

**Hard rule:** at every LLM touch the model returns a **tag + structured slots**, never free prose to the flow.

### Blueprint executes; the model never reads the path (from Blueprint-First, arxiv 2508.02721)

The paper's domain — "user–tool–rule" scenarios — is exactly TRON's (operator–worker–workflow). Three sharpenings adopted from it:

1. **Runner executes the FSM; the LLM never interprets routing.** A deterministic **runner** (`scripts/run.sh`) reads the primitives (`routing.yaml`) + the project's composition (`workflow.yaml`) and drives the flow. The model is *called out to* only for a bounded subtask, then control returns to the runner. The LLM is removed from flow control entirely — not even reading the path. (Stronger than "the LLM reads the tag and decides.")
2. **Each judgment call is a typed, bounded tool — schema in, schema out.** Not "the LLM judges," but e.g. `triage(findings) → {agree: bool, fix_blocks: [...]}`, `classify_message(text) → {tag, slots}`, `assess_stall(activity) → {stalled: bool}`. The blueprint *invokes* these like functions. Every LLM touch is contract-bound, verifiable, and model-swappable.
3. **Blueprint verification as a build gate.** Procedural fidelity is checkable: lint the FSM for reachability, total tag coverage, and no dead/missing transitions. Runs in `doctor`/`validate` so a malformed flow fails at seed, not at runtime.

**Bonus enabled — tiered models.** Because each call is bounded, use a cheap model for `classify`/slot-fill and a strong one only for `triage`/judgment. Cost + latency win.

### Communication

Every message — operator, terminal, worker, Telegram — is a **canned template** in one registry. `render(tag, slots)` produces the text. The LLM only fills slots, or writes free text when the payload is a fresh judgment it just made.

- **Tone:** already set by the established TRON voice in `~/42labs/tron/landing-page.md` (dark, dry, sardonic sci-fi). All copy authored in that tone. No host-runtime names anywhere (canon rule).
- **Between-task feedback:** a set of short progress/heartbeat sentences shown *between* tasks so TRON is informative, not silent. Seeded from the landing-page terminal messages (see `super-m/plans/tron-messages-candidates.yaml`); operator may extend.
- **Terminal discipline:** no backend/behavior narration ever reaches the terminal — only rendered, pre-set sentences.

---

## Architecture — file tree

```
<agents>/
├── tron.md                      # judgment-tool prompt context (NOT the executor — run.sh is the spine)
└── tron/
    │   ── per-project config (structured, tracked, PR'd; written by seeder) ──
    ├── project.yaml             # pointers (specs/agents), detected facts, notifications (telegram/cron)
    ├── workflow.yaml            # the COMPOSITION: ordered steps + roles/checks + knobs (threshold, git, peer-consults)
    │   ── canon (ships with TRON; copied at seed; not edited per project) ──
    ├── routing.yaml             # step-primitive library + edges (dispatch/review/gate/escalate/findings-triage)
    ├── messages.yaml            # all canned copy: operator/worker/terminal/tg (tag→template+slots); landing-page voice
    │   ── procedures (skills = multi-step actions only) ──
    ├── skills/
    │   ├── dispatch.md  sweep.md  recover.md  checkpoint.md
    │   ├── escalate.md  edit-self.md  update.md  doctor.md  session-end.md
    │   ── shell (pure determinism) ──
    ├── scripts/
    │   ├── run.sh               # the deterministic engine: executes routing.yaml, calls LLM only for bounded tools
    │   ├── render.sh            # render(tag, slots) → string, reads messages.yaml
    │   ├── sweep.sh             # reads ~/.claude/jobs (real fields)
    │   ├── tg-poll.sh  tg-send.sh  cron-install.sh
    │   ── runtime state (gitignored, edited in place) ──
    ├── workflow-state.yaml      # live FSM state + counters
    ├── pipeline.md              # ledger (if internal; else host owns it)
    ├── state.md  current-id  dispatched.log  tg-inbox.jsonl  .tg-offset  .env  logs/
    ├── seed-trace.md
    └── .gitignore
```

Three clean layers: **data the rails read** (config + routing + messages) · **the rails** (skills + scripts) · **runtime state** (FSM memory). The spine is `run.sh`; `tron.md` shrinks to the judgment-tool prompt context.

---

## Consequences

**Positive:** predictable, auditable, low-drift, cheap (few LLM calls), testable (the FSM + registry can be unit-checked); all copy in one place → tone + the no-verbose / no-runtime-name rules enforced at a glance; the seeder already follows config rather than asking ad-hoc.

**Negative / accepted:** more upfront structure; the routing table must cover *every* transition or TRON stalls; intentional loss of improvisational flexibility; YAML authoring discipline required.

---

## Implementation plan (phased, build fresh)

**Phase 0 — Foundations**
- This ADR.
- Define the **step-primitive library** (`dispatch`/`review`/`gate`/`escalate`/`findings-triage`: each one's edges + which judgment tool it calls) and the **composition schema** (`workflow.yaml`).
- Define the schemas: `project.yaml`, `workflow.yaml`, `routing.yaml`, `messages.yaml`. Lock the situation-tag vocabulary as a **closed enum** (every message + every transition has a tag), including a reserved **`unclassified`** tag with a mandatory **escalate-to-operator** edge *(G-1)*.
- Define the **judgment-tool contracts** (input/output schema per LLM call: `classify_message`, `triage`, `assess_wall`, `assess_stall`, `scope_fix`).
- Define the **invalid-output policy** *(G-2)*: bounded retry budget → escalate via the `unclassified` edge.
- Define the **tick model** *(G-3)*: each wake = one bounded sweep → advance → persist → exit; **atomic state writes + idempotent ticks** so a crashed wake is safely retried (this is the durability claim).
- Scope **copy systems** *(G-4)*: `messages.yaml` = runtime copy only; the seeder's voice is separate (it does not draw from `messages.yaml`).
- Define the **blueprint-lint** rules — over the canon primitives (reachability, total tag-enum coverage, no dead transitions) **and over each project's composition** (every step's exit edge lands on a real next step, no orphan steps, a terminal is reachable). The composition is the seed-time author-error surface — this is what the build gate most needs to catch.

**Phase 1 — Seeder review/adjust** *(kept from prior work, not rebuilt)*
- Align the finished seeder to the new file tree + structured config outputs (it currently writes md-style instances).
- Add the deterministic install/render scripts it must drop.
- Confirm seed → produces a valid FSM-ready instance.

**Phase 2 — Composition + canon content (fresh)**
- **Per-project:** `workflow.yaml` — the composition schema + the embedded default composition (steps, roles/checks, knobs).
- **Canon (ships with TRON, not per-project):** finalize `routing.yaml` (step-primitive edges, from the Phase-0 library) and author `messages.yaml` from the candidate pool — tone is already set, so nothing blocks it.

**Phase 3 — Rails (fresh)**
- `run.sh` — the deterministic engine that executes `routing.yaml` and calls the LLM only for the typed judgment tools.
- Judgment tools implemented to their Phase-0 contracts (schema-validated I/O); wire tiered models (cheap classify, strong triage).
- Skills rewritten from scratch as procedures only.
- Scripts: `render.sh`; `sweep.sh` + `recover` against the **real `~/.claude/jobs` fields** (`state`, `updatedAt`, `timeline.jsonl`, short-id→`sessionId`); name-primary / id-fallback addressing.
- TG connector: review the v1 shell, carry if clean.
- `blueprint-lint` wired into `doctor`/`validate`.

**Phase 4 — `tron.md` judgment context (fresh)**
- `tron.md` = the prompt context the judgment tools run under: the judgment calls + TRON's identity/standing rules. **Not** an executor and **not** a duplicate of the flow — the spine is `run.sh`.

**Phase 5 — End-to-end streamline review** *(operator-flagged)*
- Walk the whole path: seeding → session start → dispatch → block-done → review → findings → escalation → session end.
- Verify: every transition has a `routing.yaml` entry; every emitted line has a `messages.yaml` entry; **zero backend narration** reaches the terminal.

**Phase 6 — Packaging (later)**
- CLI installer: deterministic install / update / version-pin, then hand off to the seeder session for interactive config.

---

## Open inputs (from operator)
- **Tone:** SET — the landing-page voice (`~/42labs/tron/landing-page.md`); candidates extracted to `super-m/plans/tron-messages-candidates.yaml`.
- **Between-task feedback:** seeded from the same source; operator may extend/adjust.
- (Nothing now blocks `messages.yaml` authoring.)

## Cross-cutting rules
- Real `~/.claude/jobs` fields everywhere; name-primary / id-fallback addressing.
- Structured output at every LLM touch.
- No host-runtime names in any copy; concise by default.
- Templates → `messages.yaml`; procedures → skills; never merge the two.

---

## Review — SUPER-M (2026-06-04)

Reviewer: SUPER-M, advisory/agent-evaluation pass. Scope read: this ADR, `tron-goes-live-02.md`, and the built seeder set (`tron-seed.md`, `project/workflow/pipeline.example.md`). Not re-read: `tron-goes-live-01.md` and the v1 `skills/`/`scripts/` — Phase 3 replaces them wholesale, so they don't constrain the design.

### Verdict

Architecture is sound and well-grounded — the two-layer split, bounded typed tools, single message registry, and lint-as-build-gate are the right calls, and Phase 0 is the correct starting point. Two contradictions sit **upstream** of Phase 0's deliverables (the routing schema and tool contracts can't be defined cleanly until they're settled), plus four gaps that belong inside Phase 0 and four watch-items.

### 🔴 Contradictions — resolve before Phase 0 locks

| # | Finding | Recommendation |
|:--|:--|:--|
| C-A | **FSM authorship is doubly-defined.** The built seeder produces prose `workflow.md` with conflict-driven R1–R8 edits; this ADR wants `workflow.yaml` (knobs) + `routing.yaml` (FSM table). And `routing.yaml` is filed under "config — per-project, tracked, PR'd" yet Phase 2 builds it "fresh" as canon orchestration logic. Is the FSM **canon-invariant** (ships once) or **per-project** (seeded)? | Make the FSM **canon-invariant**: one routing table ships with TRON; all per-project variation lives in `workflow.yaml` knobs (reviewer_threshold, roles present, peer-consult pairs, git on/off). The seeder produces `project.yaml` + `workflow.yaml` **only — never `routing.yaml`.** This also right-sizes Phase 1: "align seeder" becomes "rewrite Step 1's R1–R8 walk to set knobs." |
| C-B | **Two spines.** The ADR calls `run.sh` "the deterministic engine" *and* `tron.md` "the SPINE." On cron wake, which is the entry point? If `run.sh` drives and shells out to `claude -p` per tool, `tron.md` is **not** a spine — it's the prompt fragment the judgment tools run under. If a Claude session reads `tron.md` and *then* calls `run.sh`, the LLM is back adjacent to flow control and there are two spines. | Name the **single wake entry point** (likely: cron → `run.sh` → shells out to `claude -p` with a schema per judgment tool). Restate `tron.md`'s runtime role as the prompt context the bounded tools run under, not the executor. |

### 🟡 Gaps — fold into Phase 0

| # | Finding | Fix |
|:--|:--|:--|
| G-1 | **Unknown-tag deadlock.** `classify_message → {tag}` drives the FSM, and blueprint-lint demands *total tag coverage* — but an LLM can emit an out-of-enum tag, so "no dead transitions" is unprovable. | Closed tag **enum** in the tool schema + a reserved `unclassified` tag with a **mandatory escalate-to-operator edge**. Lint checks the enum, not an open set. |
| G-2 | **No LLM-output-invalid policy.** "Schema in, schema out" doesn't say what `run.sh` does when output is malformed or re-fails validation. | One policy, defined once: bounded retry budget → escalate via G-1's edge. |
| G-3 | **Tick model + atomicity unspecified.** "Turn-based, no daemon" implies each wake = one bounded sweep+advance+persist+exit, and a tick crashing mid-LLM-call must leave consistent state. | State the tick model explicitly; require **atomic state writes + idempotent ticks** so a crashed wake is safely retried. This is what backs the "Temporal-lite durability" claim. |
| G-4 | **Two copy systems.** The seeder already commits to a "Voice" persona; this ADR says runtime tone is operator-pending and governs all of `messages.yaml`. Unscoped overlap. | Scope it: `messages.yaml` = **runtime** copy only; the seeder's voice is separate. Decide explicitly whether operator-supplied tone overrides or coexists with the built-in TRON persona. |

### 🟢 Risks — watch

- **R-1 — `run.sh` is a YAML-FSM interpreter in bash.** Parsing `routing.yaml`, validating LLM JSON, rendering templates, looping — bash+yq+jq does it but gets fragile fast. Keep the FSM small; if parsing/validation grows, a tiny non-bash helper beats a 600-line shell script.
- **R-2 — `pipeline: host` mode is the determinism soft spot.** Parsing *and rewriting* a human-formatted host MD table every tick, mutating a host-tracked file each turn. Constrain the accepted format tightly, or keep a normalized internal mirror and write back less often.
- **R-3 — internal `pipeline.md` is gitignored.** The authoritative project-status ledger isn't version-controlled. If block-status history matters, reconsider tracking it (or accept the loss explicitly).
- **R-4 — `messages.yaml` blocks e2e testing.** Phases 3–4 rails can't be tested end-to-end while copy is operator-pending. Stub **placeholder copy keyed to the Phase-0 tag vocabulary** so rails build/test now; swap real copy when tone + sentences arrive.

### The one decision to make first

**Resolve C-A (FSM ownership).** It determines the `routing.yaml` schema, whether the seeder touches it at all, and the true size of Phase 1 — and every Phase-0 deliverable (schemas, tag vocabulary, tool contracts) sits downstream of it. Recommended: **FSM = canon-invariant, knobs = per-project, seeder never writes `routing.yaml`.**

### Resolution (2026-06-04) — all folded into the body

- **C-A — RESOLVED:** composition model. Canon ships the **step-primitive library** (`routing.yaml`); per-project = the **composition + knobs** (`workflow.yaml`); the seeder writes the composition, never the primitives. New step *kinds* (fan-out/join, loop-until, wait-for-event) are the only canon FSM changes. See *Workflow = composed steps* + file tree.
- **C-B — RESOLVED:** single entry — cron → `run.sh` → `claude -p` per tool; `tron.md` is prompt context, not an executor. See *Single entry point*.
- **G-1..G-4 — RESOLVED:** closed tag enum + `unclassified`→escalate; invalid-output retry→escalate; explicit tick model (atomic, idempotent); `messages.yaml` scoped to runtime copy (seeder voice separate). All in Phase 0.
- **R-1..R-4 — accepted as watch-items** (keep the FSM small; constrain `pipeline: host`; gitignored-ledger trade-off acknowledged; stub placeholder copy keyed to the tag enum so rails test before final copy).
