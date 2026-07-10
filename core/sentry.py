"""core.sentry — the ONE pacing ladder wrapping the DONE gate (contracts/
blueprint-contracts.md §5: "an idle worker at any stage is re-nudged
(`gate_nudge_after`) then escalated (`gate_idle_cap`) off the runner's own
idle state — a gate can never hang silently"). `core/gate.py`'s own
`advance` is a PURE predicate-driven state machine — it reports an honest
HOLDING outcome each tick (`local_waiting`, `merge_pending`, `trunk_failed`/
`trunk_unconfirmed`, `record_waiting`, `close_holding`, ...) and never caps
itself. The ladder's own internal cap (`CLOSE_ATTEMPT_CAP`, the one place
capping used to live, close-stage only) is GONE — see `core/gate.py`'s
`_advance_close`, which now holds forever on an unclean replica. Capping
lives in exactly ONE place, for EVERY stage: here.

`pace(eng, snapshot)` — called by `core/tick.py`, once per tick, AFTER that
tick's own `gate.advance` pass and STRICTLY BEFORE persist (so any
escalation this call produces is durable the same tick it fires) — walks
every in-flight gate in `snapshot.gates` and tracks how long it has HELD at
its CURRENT stage:

  - A stage a gate just ADVANCED into (or a gate this module has never seen
    before) starts a fresh pacing episode: `holding_stage` / `holding_since`
    / `nudged_at` (persisted directly on the `gate_state` dict — "in the
    manifest", `core/state.py`'s own durable store, no separate side table)
    are (re)anchored to the CURRENT clock reading; no holding time is
    counted on this call — progress clears the clock.
  - A stage that reads the SAME as last call's HOLDS: `holding = now -
    holding_since`.
      * At `holding >= GATE_NUDGE_AFTER` (once per holding episode —
        `nudged_at` guards a second nudge on a later call while still
        holding) the stage's order is RE-SENT via `eng._to_worker` — a
        distinct `sentry.nudge.<stage>` kind, never impersonating the
        stage's own order kind, so a re-nudge is always tellable apart from
        the stage's first order.
      * At `holding >= GATE_IDLE_CAP` (exactly once — the gate turns
        terminal the same call, so there is no "again") the gate is marked
        ESCALATED: `gate_state["stage"] = gate.STAGE_ESCALATED` and
        `gate_state["escalation"] = <detail>` — the SAME two fields
        `core/gate.py::_escalate` itself sets on a gate-driven escalation,
        so a caller can't tell a sentry-driven one apart by shape — plus a
        structured record appended to `manifest["escalations"]` (block,
        stage, holding, the cap it tripped, a human detail, the clock
        reading). Casestate/operator settle on this record is a later wave
        (T4-E6/H2) — this is the honest, durable trace for now.
  - A gate already terminal (`closed`/`escalated`, whether `core.gate`
    itself or a PRIOR `pace()` call put it there) is skipped outright, and
    its pacing fields are dropped — a stale episode never survives past the
    tick that closed it.

ONE parametrized mechanism for ALL stages: `GATE_NUDGE_AFTER`/
`GATE_IDLE_CAP` below are read the SAME way regardless of which stage a
gate is holding at (`gate.local` idle exactly like `gate.close` idle) —
there is no per-stage cap anywhere in this module, and none left in
`core/gate.py` either (the close stage's `CLOSE_ATTEMPT_CAP` consolidation
this module exists to complete).

The clock is intentionally pluggable, so a rig can be deterministic:
`eng._now()`, when the caller provides one (a plain callable), is read once
per `pace()` call and used as-is — a rig can hand it a fully self-controlled
counter (`core/sentry_rig.py` does exactly this, to pin the nudge/cap
boundaries exactly) or real wall-clock time. Absent that, `pace` falls back
to its OWN tick counter (`manifest["sentry"]["clock"]`, persisted like
everything else in the manifest, incremented exactly once per `pace()`
call) — still a deterministic "tick counter the rig controls", simply by
however many times it calls `core.tick.tick`/`pace` while a gate makes no
progress: `core/tick_rig.py` / `core/dispatch_rig.py` / `core/
multiblock_rig.py` all exercise this fallback path completely unmodified,
never wired to `eng._now()` themselves. Either way the unit is opaque to
this module: only relative deltas (`now - holding_since`) are ever compared
against the two knobs above.

Duck-typed `eng` contract: everything `core/gate.py` already needs
(`eng._to_worker`, `eng.dry`, `eng.log`) PLUS the OPTIONAL `eng._now()`
above — no new REQUIRED surface, so every existing `core/*_rig.py` eng
fixture keeps working completely unmodified (they all fall through to the
manifest-clock path).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import gate   # noqa: E402 — core/gate.py, the STAGE_CLOSED/STAGE_ESCALATED terminal vocabulary

# ── the ONE pacing ladder's two knobs — every stage, no exceptions ──
GATE_NUDGE_AFTER = 3   # ticks holding at one stage, no progress -> re-nudge (once per episode)
GATE_IDLE_CAP = 6      # ticks holding at one stage, no progress -> escalate (exactly once)

_TERMINAL_STAGES = (gate.STAGE_CLOSED, gate.STAGE_ESCALATED)


def _clock(eng, manifest):
    """The ONE clock this ladder reads — see module docstring. `eng._now()`
    when present (a plain callable, no required signature beyond
    zero-arg), else an internal counter persisted at
    `manifest["sentry"]["clock"]`, incremented exactly once per call."""
    now_fn = getattr(eng, "_now", None)
    if callable(now_fn):
        return now_fn()
    counters = manifest.setdefault("sentry", {})
    counters["clock"] = counters.get("clock", 0) + 1
    return counters["clock"]


def _drop_pacing(gate_state):
    gate_state.pop("holding_stage", None)
    gate_state.pop("holding_since", None)
    gate_state.pop("nudged_at", None)


def _nudge(eng, block, gate_state, stage, holding):
    wid = gate_state.get("wid")
    if wid and not eng.dry:
        eng._to_worker(
            wid,
            f"[TRON]  {wid} — still waiting at gate.{stage} ({holding} pace "
            f"unit(s) with no observed progress) — re-sending the order. A "
            f"gate idle past gate_idle_cap escalates; this is the one "
            f"re-nudge first.",
            f"sentry.nudge.{stage}")
    eng.log("flow", f"sentry: nudged {block} at gate.{stage} (holding={holding}, "
                    f"gate_nudge_after={GATE_NUDGE_AFTER})")


def _escalate(eng, manifest, block, gate_state, stage, holding, now):
    detail = (f"gate[{block}] idle at gate.{stage} for {holding} pace unit(s) "
             f"(>= gate_idle_cap={GATE_IDLE_CAP}) — sentry escalated (the gate "
             f"itself never self-caps; capping lives only in core.sentry)")
    gate_state["stage"] = gate.STAGE_ESCALATED
    gate_state["escalation"] = detail
    record = {"block": block, "stage": stage, "holding": holding,
             "gate_idle_cap": GATE_IDLE_CAP, "detail": detail, "at": now}
    manifest.setdefault("escalations", []).append(record)
    eng.log("flow", f"sentry: ESCALATED {block} — {detail}")
    return detail


def pace(eng, snapshot):
    """Walk every in-flight gate in `snapshot.gates`, nudge/cap exactly as
    described in the module docstring. Returns `{"nudged": [block, ...],
    "escalated": [(block, detail), ...]}` — a NON-durable convenience for
    the caller (`core/tick.py` folds `escalated` into its own tick result,
    same shape `core.gate.advance`'s own escalate outcomes already use);
    `manifest["escalations"]` is the durable record."""
    manifest = snapshot.manifest
    gates = snapshot.gates
    now = _clock(eng, manifest)

    nudged, escalated = [], []
    for block, gate_state in gates.items():
        stage = gate_state.get("stage")
        if stage in _TERMINAL_STAGES:
            # Already terminal (this tick's own gate.advance pass, a PRIOR
            # pace() call, or a gate seeded pre-closed) — never pace a
            # terminal gate; drop any stale episode so it can't leak.
            _drop_pacing(gate_state)
            continue

        if gate_state.get("holding_stage") != stage:
            # Just advanced into this stage (or first time pace() has ever
            # seen this gate) — progress clears the clock; no holding time
            # accrues on the tick a gate actually moved.
            gate_state["holding_stage"] = stage
            gate_state["holding_since"] = now
            gate_state.pop("nudged_at", None)
            continue

        holding = now - gate_state["holding_since"]

        if holding >= GATE_IDLE_CAP:
            detail = _escalate(eng, manifest, block, gate_state, stage, holding, now)
            _drop_pacing(gate_state)
            escalated.append((block, detail))
            continue

        if holding >= GATE_NUDGE_AFTER and gate_state.get("nudged_at") is None:
            _nudge(eng, block, gate_state, stage, holding)
            gate_state["nudged_at"] = now
            nudged.append(block)

    return {"nudged": nudged, "escalated": escalated}
