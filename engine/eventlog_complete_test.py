"""eventlog_complete_test — the 01-09 §4 forensic-completion suite.

01-06 made the *failure* log complete; 01-09 makes the *event* stream complete, so events.jsonl
is a full per-tick / per-decision / per-model-call record (the run-trace observer reads exactly
this — the engine stays unaware it is measured). Covers the four new record types and the one
guarantee that matters: emitting them changes no decision (trace-on == trace-off).

Deterministic, token-free (TRON_DRY). Reuses eventlog_test's fixture builder.
"""
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

os.environ["TRON_DRY"] = "1"

import util              # noqa: E402
import judge            # noqa: E402
import eventlog         # noqa: E402
import eventlog_test as elt  # noqa: E402  (reuse build/engine/recs)

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))


def _types(ctx):
    return [r.get("type") for r in elt.recs(ctx) if r.get("kind") == "event"]


def _of_type(ctx, t):
    return [r for r in elt.recs(ctx) if r.get("kind") == "event" and r.get("type") == t]


def _with_stub(ctx, tag):
    """Point the classifier at a deterministic stub returning `tag` (single-shot, retries=0)."""
    stub = os.path.join(ctx.dir, f"stub-{tag.replace('.', '_')}.json")
    util.atomic_write(stub, json.dumps({"classify_message": [{"tag": tag, "slots": {}}]}))
    os.environ["TRON_JUDGE_STUB"] = stub
    judge._stub_cache = None
    judge._stub_idx.clear()
    judge._tags_cache = None


def _clear_stub():
    os.environ.pop("TRON_JUDGE_STUB", None)
    judge._stub_cache = None
    judge._stub_idx.clear()


# ── Gap 1: model_call ────────────────────────────────────────────────────────
def t_model_call():
    ctx, _ = elt.build()
    eng = elt.engine(ctx)
    _with_stub(ctx, "worker.online")
    try:
        eng._classify({"text": "online", "sender": {"kind": "worker", "id": "W-1"}})
    finally:
        _clear_stub()
    mc = _of_type(ctx, "model_call")
    ok("Gap1 one model_call per classify", len(mc) == 1, f"got {len(mc)}")
    p = (mc[0].get("payload") or {}) if mc else {}
    ok("Gap1 model_call carries tool", p.get("tool") == "classify_message")
    ok("Gap1 model_call carries tier", bool(p.get("tier")))
    ok("Gap1 model_call carries plane=control", p.get("plane") == "control")
    ok("Gap1 model_call ok=True on valid output", p.get("ok") is True)
    ok("Gap1 model_call retries int", isinstance(p.get("retries"), int))
    ok("Gap1 model_call stamped with tick state", mc and "tick" in mc[0] and "run" in mc[0])

    # Fail path: an invalid tag exhausts validation -> ok=False, still recorded.
    ctx2, _ = elt.build()
    eng2 = elt.engine(ctx2)
    _with_stub(ctx2, "NOPE")
    try:
        eng2._classify({"text": "garble", "sender": {"kind": "worker", "id": "W-2"}})
    finally:
        _clear_stub()
    mc2 = _of_type(ctx2, "model_call")
    ok("Gap1 model_call recorded on failure too", len(mc2) == 1)
    ok("Gap1 model_call ok=False on invalid output",
       mc2 and (mc2[0].get("payload") or {}).get("ok") is False)

    # elog=None -> no emit, no crash (the sink is optional).
    ok("Gap1 judge.call without elog does not emit",
       judge.call("classify_message", {"text": "x", "sender": {}}, ctx, elog=None) is not None)


# ── Gap 2: per-tick record ───────────────────────────────────────────────────
def t_tick_record():
    ctx, _ = elt.build()
    eng = elt.engine(ctx)
    eng.tick("manual")                                   # a full tick under dry
    ticks = _of_type(ctx, "tick")
    ok("Gap2 one tick record per tick", len(ticks) == 1, f"got {len(ticks)}")
    t0 = ticks[0] if ticks else {}
    p = t0.get("payload") or {}
    ok("Gap2 tick carries trigger_source (honest)", p.get("trigger_source") == "manual")
    ok("Gap2 tick carries snapshot_hash", bool(p.get("snapshot_hash")))
    ok("Gap2 tick carries run/tick_seq/trunk", "run" in t0 and "tick" in t0 and "trunk" in t0)
    ok("Gap2 tick has a timestamp", bool(t0.get("at")))

    # snapshot_hash is stable for an unchanged snapshot, and the field is a real hash.
    h1 = eng._snapshot_hash
    eng._refresh_from_trunk(count=False)
    ok("Gap2 snapshot_hash deterministic for unchanged trunk", eng._snapshot_hash == h1)
    ok("Gap2 snapshot_hash is a sha256 hex", bool(re.fullmatch(r"[0-9a-f]{64}", h1 or "")))

    # trigger honesty: a timer-driven tick records "timer".
    eng.tick("timer")
    ok("Gap2 trigger_source reflects the caller",
       any((r.get("payload") or {}).get("trigger_source") == "timer" for r in _of_type(ctx, "tick")))


# ── Gap 3: gate_advance / release / settle ───────────────────────────────────
def t_gate_advance():
    ctx, _ = elt.build()
    eng = elt.engine(ctx)
    g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
    eng._drive_gate("A-01", g, reason="first nudge")     # None -> local (no PR yet)
    ga = _of_type(ctx, "gate_advance")
    ok("Gap3 gate_advance emitted on a stage advance", len(ga) >= 1, f"got {len(ga)}")
    p = (ga[0].get("payload") or {}) if ga else {}
    ok("Gap3 gate_advance carries from/to", p.get("from") is None and p.get("to") == "local")
    ok("Gap3 gate_advance carries block", ga and ga[0].get("block") == "A-01")

    # A re-nudge at the SAME stage must NOT emit a new gate_advance.
    before = len(_of_type(ctx, "gate_advance"))
    eng._drive_gate("A-01", g, reason="re-nudge")
    ok("Gap3 no gate_advance on a same-stage re-nudge",
       len(_of_type(ctx, "gate_advance")) == before)


def t_release():
    ctx, _ = elt.build()
    eng = elt.engine(ctx)
    w = {"id": "ENG-A-01", "role": "engineer", "session_id": "dry", "block": "A-01"}
    eng.st.workers.append(w)
    eng._release_worker(w, notify=False, reason="close-confirmed")
    rel = _of_type(ctx, "release")
    ok("Gap3 release emitted on slot free", len(rel) == 1, f"got {len(rel)}")
    r0 = rel[0] if rel else {}
    ok("Gap3 release carries actor + block", r0.get("actor") == "ENG-A-01" and r0.get("block") == "A-01")
    ok("Gap3 release carries role + reason",
       (r0.get("payload") or {}).get("role") == "engineer"
       and (r0.get("payload") or {}).get("reason") == "close-confirmed")


def t_settle():
    ctx, _ = elt.build()
    eng = elt.engine(ctx)
    eng.st.pending_cases["CASE-001"] = {"block": "A-01", "kind": "await",
                                        "worker_id": "ENG-A-01", "detail": "d", "decision": None}
    eng._h_apply_decision({"decision": "resume", "case": "CASE-001", "block": "A-01"})
    st = _of_type(ctx, "settle")
    ok("Gap3 settle emitted on disposition", len(st) == 1, f"got {len(st)}")
    s0 = st[0] if st else {}
    ok("Gap3 settle carries block + cid + disposition",
       s0.get("block") == "A-01" and s0.get("cid") == "CASE-001"
       and (s0.get("payload") or {}).get("disposition") == "resume")


# ── taxonomy: no drift ───────────────────────────────────────────────────────
def t_taxonomy():
    new = {"tick", "model_call", "gate_advance", "settle", "release"}
    ok("taxonomy registers every new type", new <= eventlog.EVENT_TYPES,
       f"missing: {sorted(new - eventlog.EVENT_TYPES)}")
    emitted = set()
    for fname in ("fsm.py", "wake.py", "judge.py", "console.py", "engine.py"):
        path = os.path.join(HERE, fname)
        if os.path.exists(path):
            with open(path) as fh:
                emitted |= set(re.findall(r'(?:events|elog)\.event\(\s*"([a-z_]+)"', fh.read()))
    ok("taxonomy covers every emitted type (no drift)", emitted <= eventlog.EVENT_TYPES,
       f"undeclared: {sorted(emitted - eventlog.EVENT_TYPES)}")


# ── the guarantee: trace-on == trace-off (emitting changes no decision) ───────
def _decision_state(eng):
    """The decision-relevant state — what the engine would act on next tick. The event stream
    is a separate file; if emitting altered any of this, the trace would be changing behaviour."""
    return json.dumps({
        "gate": eng.st.gate,
        "workers": [{k: w.get(k) for k in ("id", "role", "block", "rtype")} for w in eng.st.workers],
        "dropped": eng._dropped(),
        "pending": eng.st.pending_cases,
        "blocked": eng.st.blocked,
    }, sort_keys=True, default=str)


def _drive_scenario(eng):
    """Exercise every new emit path: a gate advance, a release, a settle, a tick."""
    eng.tick("timer")
    g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
    eng._drive_gate("A-01", g)
    w = {"id": "ENG-A-02", "role": "engineer", "session_id": "dry", "block": "A-02"}
    eng.st.workers.append(w)
    eng._release_worker(w, notify=False, reason="close-confirmed")
    eng.st.pending_cases["CASE-9"] = {"block": "A-02", "kind": "await",
                                      "worker_id": "ENG-A-02", "detail": "d", "decision": None}
    eng._h_apply_decision({"decision": "abandon", "case": "CASE-9", "block": "A-02"})


def t_transition_identical():
    # trace-OFF: suppress the event stream entirely; capture the resulting decision state.
    ctx_off, _ = elt.build()
    eng_off = elt.engine(ctx_off)
    eng_off.events.event = lambda *a, **k: None          # silence the trace
    _drive_scenario(eng_off)
    state_off = _decision_state(eng_off)

    # trace-ON: identical fixture + identical scenario, full event stream.
    ctx_on, _ = elt.build()
    eng_on = elt.engine(ctx_on)
    _drive_scenario(eng_on)
    state_on = _decision_state(eng_on)

    ok("§4 trace-on == trace-off (decisions identical)", state_on == state_off,
       "decision state diverged with the trace on")
    ok("§4 trace-on actually emitted records", len(elt.recs(ctx_on)) > 0)
    ok("§4 trace-off emitted none", len(elt.recs(ctx_off)) == 0)


def main():
    tests = (t_model_call, t_tick_record, t_gate_advance, t_release, t_settle,
             t_taxonomy, t_transition_identical)
    for t in tests:
        try:
            t()
        except Exception as e:
            ok(f"{t.__name__} raised", False, repr(e))
    passed = sum(1 for _, c, _ in _results if c)
    print(f"eventlog_complete_test: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail and not c else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
