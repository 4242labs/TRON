# B7 — Interactive console (bounded conversational front)

**Project:** TRON deterministic rebuild · **Phase:** interaction layer (new — ADR-002)
**Read first:** `../tron-adr-002-interaction-model.md` + `../tron-adr-001-deterministic-rebuild.md` + `B0-blueprint-contracts.md`.
**Reference prototype:** `tron/prototype/tron-proto6.py` (throwaway; the validated UX, not canon).
**Repo:** `tron` canon repo (`~/42labs/tron/`).

> Context: TRON is the one agent the operator talks to and watches the fleet through, in a regular terminal — a **bounded conversational front** over the deterministic engine (B3). It converses freely but acts only via defined handlers; **flow stays in `run.sh`**. All operator↔worker traffic routes through TRON; no direct worker talk.

---

- **Goal:** build the terminal console — the conversational TRON front + live fleet view — on top of the B3 engine.

- **Acceptance criteria:**
  - **HOME view:** pinned status box (one line per agent + live status + spinner while active) + the TRON conversation + **high-signal events only** (status changes, milestones, walls) — no routine worker chatter.
  - **WATCH view:** `watch <id>` enters a per-agent session (boxed header + that agent's action stream only, read-only); `home`/Esc returns to HOME.
  - **Bounded conversation:** operator input → `classify_message` (cheap model) → tag → defined handler; replies rendered from `messages.yaml`. TRON may report/acknowledge/relay; it **cannot** decide/reorder flow — flow requests route to the engine. No path to free-form flow control.
  - **All through TRON:** no mechanism to talk to a worker directly; `watch` is observation only.
  - **Lifecycle wired to B3:** `start` (dumb form — composition-declared required inputs, no LLM), `tick` (cron/headless), `stop` (guards unfinished work).
  - **Two channels:** terminal + Telegram, both funneled through the same `classify → handler` path.
  - **Idle filler:** after an interval of silence in HOME, print a random between-task line from `messages.yaml` (no backend narration).
  - **Reconnect:** re-running `tron` reattaches to the live engine via `recover`; **persist the HOME event log** so the relaunched console replays recent history.
  - UX: black-bg-safe colors (cyan/yellow/green/white — no blue/magenta), spinners, boxed input (`TRON>`), Tab autocomplete (commands + agent names), line wrapping.

- **Scope:** the console front + its wiring to the engine. No flow logic (that's B3).

- **Dependencies:** B2, B3, B4.

- **Owner:** engineer.

- **Deferred:** visuals polish and workflow fine-tuning (operator-flagged as later).
