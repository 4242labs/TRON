# ADR-002 — TRON interaction model (bounded conversational console)

**Status:** Proposed
**Date:** 2026-06-04
**Authors:** operator + SUPER-M
**Amends:** ADR-001's interaction stance (which had TRON **headless, no session**). This ADR revises that to a **bounded conversational front over the deterministic engine**, validated by prototype (`tron/prototype/tron-proto6.py`).

---

## Context

ADR-001 made TRON a deterministic FSM woken by cron — headless, with the operator reaching it only via Telegram or `run.sh msg`. In review, the operator established a hard product requirement: TRON must be **the one agent you talk to** and the place you **see the fleet**, inside a **regular terminal** — like an agent session today — and **all operator↔worker communication must route through TRON** (no talking to spawned agents directly).

This reintroduces a live session, which appears to conflict with the deterministic design. The resolution (below) keeps determinism by bounding what TRON can *do*, not what it can *say*. Prototyped end-to-end (`proto6`): real restricted-LLM TRON + real concurrent worker agents + a HOME/WATCH console. The operator confirmed the model.

---

## Decision

**TRON = a bounded conversational front + the deterministic engine behind it.**

### The determinism line
Bound TRON's **actions**, not its **language**. TRON converses freely (a restricted LLM, not a dummy field), but:
- **Flow decisions stay in `run.sh`/FSM** — next block, review cadence, escalate gating, dispatch. The front's only flow-action is *"call the engine."*
- TRON may **report, acknowledge, relay**. It may **not** decide/reorder flow, invent work, or claim work done. Asked to change flow → it routes the request to the engine, never fabricates an outcome.
- Enforced structurally: the front emits only defined intents/tool-calls; the engine validates and executes. `tron.md` + the tool schemas are the fence.

### All through TRON
Operators never address a worker directly. Worker problems surface to TRON; TRON relays to the operator and relays the answer back into the worker's session. `watch <id>` is **read-only** observation; interaction is TRON-only.

### The console (any terminal, stdlib curses — no separate app)
- **HOME** — pinned status box (one line per agent + live status/spinner) + the TRON conversation + **only high-signal events** (status changes, milestones, walls). No routine worker chatter.
- **WATCH** — `watch ENG-N` enters that agent's session: boxed header + that agent's action stream only; `home`/Esc returns to HOME.
- UX: contrasting colors (black-bg safe), spinners on active agents, boxed input (`TRON>`), Tab autocomplete (commands + agent names).
- **Idle filler:** after an interval of silence in HOME, TRON prints a random between-task line from `messages.yaml` (the landing-page "funny sentences" pool) — informative-not-silent, never backend narration.

### Lifecycle
- **`start`** — a dumb form (plain input, no LLM): prompts the **composition-declared** required inputs (default: just `max_concurrent_engineers`), spawns the persistent architect + first block, installs the cron heartbeat.
- **`tick`** — cron-driven; runs the engine headless when you're away.
- **`stop`** — guards unfinished work (active workers / in-progress ledger) before releasing.
- **Two parallel channels:** terminal + Telegram, both funneled through `classify_message → tag → handler`.

### LLM touches (unchanged budget shape)
Per operator message: one `classify_message` (cheap model) → tag → handler; replies **rendered from `messages.yaml`** (`{detail}` the only free-text slot). Plus the existing judgment tools. The supervisor stays cheap; spend is in the workers.

---

## Failure handling (the console is disposable)

The console is a face; the workers and the engine are the truth. No single exit cascades:

- **Console closed (mistake / terminal closed):** workers survive (detached background sessions in `~/.claude/jobs`, **not** children of the console TTY — a B3 requirement: spawn detached so SIGHUP can't cascade); `workflow-state.yaml` is on disk (atomic per tick); the cron heartbeat keeps ticking `run.sh` headless. **Reconnect by re-running `tron`** — it runs `recover` (rebuild live workers from `~/.claude/jobs` + `dispatched.log`, rebroadcast callback id) and drops you back into HOME at current state. Not a chat-resume — a reattach. Persist the HOME event log so the relaunched console **replays recent history** (B7).
- **Worker exits/crashes mid-block:** sweep tags `worker.dead` → purge + re-dispatch that block; other agents unaffected.
- **TRON crashes mid-tick:** atomic + idempotent ticks → consistent state, safe retry next heartbeat/restart.

Caveat: if cron is on, the engine advanced while the console was closed (reconnect to live progress); if off, nothing advanced — relaunch resumes supervision.

## Consequences

**Positive:** TRON is the single coordinator the operator wanted, in any terminal; determinism intact (flow in the engine); the fleet is visible; communication is centralized (auditable).

**Negative / accepted:** deliberately re-adds a live session → tokens while open + context to manage (mitigated: classify is cheap, replies are canned). New build surface — the **console is its own block (B7)**; the **engine (B3) must be exposed as a callable** the console/conversation drives.

**Deferred:** console visuals polish and workflow fine-tuning.

---

## Reference
- Prototype: `tron/prototype/tron-proto6.py` (throwaway; not canon).
- Builds on ADR-001 (deterministic FSM) and B0 contracts (`tron/contracts/`).
