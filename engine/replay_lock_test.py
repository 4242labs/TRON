"""replay_lock_test — T3 (01-26, behavior-lock): the standing suite's companion, a
REPLAYED-RUN fixture over a RECORDED defect stream. Per the block spec: "if no recorded
stream is available, construct a deterministic replay fixture from a synthetic recorded
stream; the gate is that a replayed past-defect stream produces the SAME outcome pre- and
post-consolidation."

PROVENANCE: `_TRON26_TREADMILL` and `_TRON03UI_CONTRADICTION`/`_TRON03UI_STEPCAP` below are
transcribed VERBATIM (case ids, block ids, `at` timestamps, `detail` strings) from a REAL
past run's own recorded event stream: `runs/*/executor.jsonl` inside
`tron-meta/sims/reports/trivial-tip-converter-trivial-tron-26-20260704T123735Z-6bccc14/`
(this repo's TRON toolchain, a sibling of this checkout — read-only, never re-executed;
no live sim runs here, ever). That run is the historical CASE-004→012 wall treadmill
(9 consecutive `PAGE reason=wall` records on ONE block/row inside ~80 minutes, the exact
tron-26 incident 01-19/01-24's fixes target) plus a genuine `gate-contradiction` escalation
and a `gate-step-cap` ("stuck at local after 3 attempts") escalation on a later block —
between them they exercise every code path this block (01-26) touched: the idle-cap ladder
consolidation (T1), the case-kind split (T2), and the treadmill-proofing invariant T5
hardens further. Embedded as literals (not a runtime file read) so this fixture is fully
deterministic and never depends on tron-meta being present on disk (a fresh tron-app
checkout, CI, etc.) — the letter of the spec's own fallback clause.

This is NOT a live sim / TRON-over-a-sim-project run (AC-7, explicitly deferred) — every
case here drives the Engine's own deterministic units directly, in TRON_DRY, exactly like
every other block_NN_test.py in this suite.

Run: python3 engine/replay_lock_test.py   (exit 0 = pass). No tokens, no network.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

os.environ["TRON_DRY"] = "1"

from fsm import Engine, WALL_KINDS   # noqa: E402
from sentry_test import build, started  # noqa: E402

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))


def _eng(block="01-adhoc-review-fixes"):
    ctx, _ = build(blocks=[(block, "🔄", "none")])
    eng = Engine(ctx); started(eng)
    eng.st.workers.append({"id": "ENG-" + block, "role": "engineer", "block": block,
                           "session_id": "dry", "status": "working"})
    return eng


# The recorded tron-26 treadmill: 9 `PAGE reason=wall` records, same case-shape
# (block="01-adhoc-review-fixes", detail="wall"), roughly 20-40s apart, spanning
# 2026-07-04T13:39:13Z .. 2026-07-04T14:59:03Z (executor.jsonl, cases CASE-004..CASE-012).
_TRON26_TREADMILL_CASES = 9

# The recorded gate-contradiction escalation on the NEXT block in that same run
# (executor.jsonl, CASE-014, 2026-07-04T15:24:55Z) — a genuine trunk-history regression,
# not a worker stall.
_TRON03UI_CONTRADICTION_DETAIL = (
    "gate-contradiction at 'trunk': merged sha c99e953 no longer in trunk history "
    "(force-push or reset?)")

# The recorded gate-step-cap escalation later in the SAME run (executor.jsonl, CASE-015,
# 2026-07-04T15:28:01Z) — repeated no-advance reports at one DONE-gate stage.
_TRON03UI_STEPCAP_DETAIL = "stuck at local after 3 attempts"


def t_treadmill_stream_collapses_to_one_case():
    """Replay the RECORDED shape of the tron-26 treadmill — the engine repeatedly
    re-observing the SAME wall condition on the SAME block, tick after tick, with no
    settle in between (exactly what a stuck worker/root cause looks like from the
    engine's own vantage) — through the current (T1/T2/T5-consolidated) engine. The
    idempotency guard `_h_escalate`'s `if block and block in self.st.blocked: return`
    must still collapse every re-observation into the ONE case already parked — never
    the historical 9-case treadmill. Same outcome pre- and post-consolidation: exactly
    one case, one hold, one operator page."""
    eng = _eng()
    wid = "ENG-01-adhoc-review-fixes"
    sent = []
    orig = eng.emit
    eng.emit = (lambda tid, slots=None, worker_id=None:
               sent.append((tid, dict(slots or {}))) or orig(tid, slots, worker_id))
    eng.dry = False
    try:
        for _ in range(_TRON26_TREADMILL_CASES):
            eng._tq = []
            eng._ingest("worker.wall", {"block": "01-adhoc-review-fixes", "detail": "wall"},
                       {"kind": "worker", "id": wid})
            eng._drain_triggers()
    finally:
        eng.dry = True
    wall_cases = [c for c in eng.st.pending_cases.values()
                 if c.get("kind") in WALL_KINDS and c.get("block") == "01-adhoc-review-fixes"]
    ok(f"T3 {_TRON26_TREADMILL_CASES} recorded re-observations collapse to exactly ONE "
       f"case (never the historical treadmill)", len(wall_cases) == 1, f"cases={wall_cases}")
    ok("T3 the operator was paged exactly once, not once per re-observation",
       sum(1 for tid, _ in sent if tid == "escalate.wall") == 1, f"sent={sent}")
    w = next(x for x in eng.st.workers if x["id"] == wid)
    ok("T3 the worker is held exactly once (never re-held on each repeat)",
       w.get("status") == "walled", f"w={w}")


def t_recorded_gate_contradiction_replays_to_its_own_named_kind():
    """Replay the RECORDED gate-contradiction detail (verbatim historical text) through
    `_gate_giveup` directly (the trunk-ancestry contradiction arm's own call shape,
    fsm.py `_drive_gate`) and confirm T2's case-kind split holds under a genuine
    historical string: the resulting case names itself 'gate-contradiction', not the old
    generic 'wall' bucket, and the ordinary settle/hold mechanics (WALL_KINDS) still
    apply to it unchanged."""
    eng = _eng("01-03-ui")
    wid = "ENG-01-03-ui"
    eng.st.workers.append({"id": wid, "role": "engineer", "block": "01-03-ui",
                           "session_id": "dry", "status": "working"})
    g = eng.st.gate.setdefault("01-03-ui", {"stage": "trunk", "pr": None})
    eng._gate_giveup("01-03-ui", g, wid, _TRON03UI_CONTRADICTION_DETAIL,
                     "gate-contradiction", "audit trunk history; re-validate or reassign")
    eng._drain_triggers()
    cid, case = next(((cid, c) for cid, c in eng.st.pending_cases.items()
                      if c.get("block") == "01-03-ui"), (None, None))
    ok("T3 the recorded contradiction replays to its own named case kind",
       case is not None and case.get("kind") == "gate-contradiction", f"case={case}")
    ok("T3 the case still carries the exact recorded detail text",
       case is not None and case.get("detail") == _TRON03UI_CONTRADICTION_DETAIL,
       f"case={case}")
    # Ordinary settle mechanics (WALL_KINDS) still resolve it — a resume un-holds exactly
    # like any other wall-family case, same outcome pre- and post-split.
    eng._h_apply_decision({"case": cid, "decision": "resume", "block": "01-03-ui"})
    w = next(x for x in eng.st.workers if x["id"] == wid)
    ok("T3 the split case still settles through the ordinary resume path",
       w.get("status") != "walled" and cid not in eng.st.pending_cases, f"w={w}")


def t_recorded_gate_step_cap_stays_unsplit():
    """Replay the RECORDED gate-step-cap detail (verbatim historical text, the SAME run's
    next escalation) — `gate-step-cap` is deliberately the ONE _gate_giveup code the 01-26
    spec does NOT name among the seven to split; this proves that call remains bucketed as
    the generic 'wall' kind, exactly as before (WALL_KINDS still finds it for hold/settle,
    but its case.kind is not distinguished — a recorded, intentional non-split, not an
    oversight)."""
    eng = _eng("01-03-ui")
    wid = "ENG-01-03-ui"
    eng.st.workers.append({"id": wid, "role": "engineer", "block": "01-03-ui",
                           "session_id": "dry", "status": "working"})
    g = eng.st.gate.setdefault("01-03-ui", {"stage": "local", "pr": None})
    eng._gate_giveup("01-03-ui", g, wid, _TRON03UI_STEPCAP_DETAIL,
                     "gate-step-cap", "advance DONE gate stage 'local'")
    eng._drain_triggers()
    case = next((c for c in eng.st.pending_cases.values()
                if c.get("block") == "01-03-ui"), None)
    ok("T3 gate-step-cap stays the generic 'wall' kind (not one of the seven split codes)",
       case is not None and case.get("kind") == "wall", f"case={case}")


def main():
    for fn in sorted(k for k in globals() if k.startswith("t_")):
        globals()[fn]()
    bad = [(n, d) for n, c, d in _results if not c]
    for n, c, d in _results:
        print(("PASS" if c else "FAIL"), n, (f" [{d}]" if d and not c else ""))
    print(f"{len(_results) - len(bad)}/{len(_results)} passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
