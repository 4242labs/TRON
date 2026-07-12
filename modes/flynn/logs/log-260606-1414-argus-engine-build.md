# Session log — ARGUS: deterministic engine build (ENGINEER MODE)

**Date:** 2026-06-06 · **Author:** Ânderson (ENGINEER) · **Status:** complete · landed on `origin/main`

## What happened

Switched from SUPER-M to **ENGINEER MODE** and built the ARGUS engine from the spec
authored earlier this day (`argus/engine-spec.md` + `contracts/schema/`). Built in a
worktree off `origin/main` (primary checkout was dirty with in-flight TRON/Alfred
work — never touched it).

### Engine built — `argus/engine/` (19 modules, Python stdlib + PyYAML only)
Implements `engine-spec.md` end to end, in TRON's idiom (Python core, thin transports):
- **Spine:** `pulse` (the §1 tick loop), `collect` (direct HTTP / mcp / webhook + stub),
  `ingest` (drain + HMAC verify + dedupe), `sli` (predicate mini-grammar + rolling
  windows), `evaluate` (multiwindow multi-burn-rate + gauge hysteresis), `severity`
  (resolver — max urgency, never downgrade), `incident` (open/extend/close/dedupe/
  silence/inhibit + the `engine.blind` self-incident).
- **Judgment/action:** `judge` (the 3 schema-validated calls — correlate / propose /
  compose — with invalid-output retry→safe-default + tiering), `executor` (the gated
  remediation FSM + guardrails: kill-switch, rate-limit, circuit-breaker, dry-run,
  attempt-cap, rollback), `approve` (chat-native approve/deny/silence intake).
- **Output:** `route` (severity→channel, render from copy registry, dedupe, digest),
  `notify` (thin TG/Slack), `render`, `messages.yaml` (copy registry).
- **Plumbing/spine support:** `state` (atomic, crash-safe, idempotency ledgers),
  `config` (typed view), `lint` (L1–L10), `ctx`, `util` (atomic IO, injectable clock,
  duration + cron parsing), `engine.py` CLI, `argus` bash entrypoint,
  `scripts/cron-install.sh`, `templates/argus-state.yaml`, `engine/README.md`.

### Determinism by construction
The LLM is called out to only at the judge/compose steps — never decides firing,
severity, routing, or whether an action runs (§7.3). Every external effect and the
clock are stubbable via `ARGUS_*` env vars (`ARGUS_NOW`, `ARGUS_COLLECT_STUB`,
`ARGUS_JUDGE_STUB`, `ARGUS_EXEC_STUB`, `ARGUS_NOTIFY_STUB`), so a tick replays
identically with no token and no packet.

### Verified
- `argus/tests/test_engine.py` — **14 offline tests PASS:** burn-rate firing,
  gauge alarm + hysteresis, severity max-fold, incident open→extend→recover,
  await-approval→execute, off-allowlist→REJECTED, approval timeout→NO_OP, routing
  dedupe, ingest push+dedupe, blind-detector self-alarm, plus pure-fn units
  (durations, cron, predicates, sev_max, lint pass/fail).
- `argus validate` → **all 10 lint rules PASS** against `argus.targets.example.yaml`.
- Real `argus tick` against the example: live-probed placeholder hosts, fired 4
  conditions, opened 2 incidents, persisted state.

## Bug caught by the tests
The executor must keep stepping an **awaiting-approval** incident across *quiet* ticks
(an in-flight incident with unchanged conditions isn't "changed", so it was being
skipped). Fixed `pulse` to drive the executor over every open incident with a live
proposal or an in-flight FSM state, not just the changed set.

## Faithful behaviors the tests confirmed (not bugs)
- Multiwindow burn-rate keeps an incident firing until the **short** window clears the
  bad samples — the intended fast-reset. With two availability rules (5m + 30m short
  windows), recovery waits for the slower one. Correct, not a stall.

## Artifacts / commit
- Commit `6004082` `feat(argus): build the deterministic engine (PULSE spine + tests)`
  — 26 files, +2733. Clean FF to `origin/main` (`7455424..6004082`); worktree + branch
  removed; local `main` fast-forwarded; dirty TRON/Alfred work preserved.
- Memory `project_argus_created.md` updated: engine BUILT (was specified-only).

## Where it stands / next
- Engine is generic canon, on the shelf, fully tested. **Not wired into any project.**
- Next (operator-driven): install as `hiresling.ai/hiresling-argus` via
  `skill-bootstrap.md` (write `argus.targets.yaml` + secrets, wire a real connector +
  notify path, deploy as `.repo-class: app`); optionally finalize
  `contracts/schema/targets.schema.yaml` from the now-working config (watch-item A-2).
