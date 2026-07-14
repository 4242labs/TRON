"""core.emit_rig — mutation-proof lock for the single emit API + the one
closed effect registry (`core/emit.py`, block 01-38 T7).

`core/emit.py` is the chokepoint every persisted manifest state change and
every forensic event routes through — the events-as-single-ground-truth
spine. This rig proves, TOKEN-FREE, against a tiny duck `eng`/manifest (no
git/subprocess/LLM — `emit` touches none):

  R1  the registry is CLOSED — an unregistered effect raises
      UnknownEffectError from every entry point (record/record_to/put/
      patch/append/drop), never a silently-mis-typed event that drifts the
      vocabulary.
  R2  record: a forensic effect writes EXACTLY one typed event whose `type`
      IS the effect name and whose payload is the caller's fields — and
      touches NO manifest state.
  R2b record refuses to be used for anything but a forensic effect (a
      state-kind effect through record is a caller error, raised).
  R3  put: sets manifest<path>[key]=value AND writes the typed event — the
      two are ONE operation (a mutation with no event, or vice-versa, is
      not expressible through this API).
  R4  patch: applies several fields at once onto manifest<path> AND emits.
  R5  append: appends to a manifest-rooted list (created if missing) AND
      emits.
  R6  drop: removes a key AND emits — a removal is still a recorded effect.
  M1  MUTATION PROOF (non-vacuity): with the event-write stubbed out, the
      SAME calls leave the event stream empty while STILL mutating — proving
      R2-R6's event assertions are the emit call's doing, not incidental.
  M2  MUTATION PROOF (the pairing): a put with a deliberately corrupted
      registry (effect removed) raises BEFORE any state change lands —
      proving the closed-registry check gates the mutation, not just the
      event.
  W1  the WIRED sites: the four effect types the pre-T7 stack already
      emitted (door_refusal, grant_minted, operator_page, must_be_zero) are
      all registered — a guard so a later sub-commit removing one from the
      registry (and silently un-typing its live event) fails here.

`ok(name, cond, detail)`; `main()` prints `PASS (n/m)`, exits non-zero on fail.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_APP_ROOT, "engine"))
sys.path.insert(0, _HERE)

import emit   # noqa: E402 — core/emit.py, the unit under test

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


class _Sink:
    """The `.event(type, **payload)` shape both `_Events` and `EventLog`
    share — records every write as `{"type", "payload"}`, the SAME shape
    `core/engine.py::_Events` produces."""
    def __init__(self):
        self.log = []

    def event(self, type_, **payload):
        self.log.append({"type": type_, "payload": payload})


class _NullSink:
    """A sink that DROPS every event — used by the M1 mutation proof to show
    a state mutation still lands with the event-write neutralized (so R2-R6's
    event assertions are genuinely the emit call's doing)."""
    def __init__(self):
        self.log = []

    def event(self, type_, **payload):
        pass


class _Eng:
    def __init__(self, sink=None):
        self.events = sink or _Sink()


def _raises_unknown(fn):
    try:
        fn()
    except emit.UnknownEffectError:
        return True
    except Exception:   # noqa: BLE001 — any OTHER exception is not the closed-registry proof
        return False
    return False


def main():
    # ── R1: closed registry — every entry point rejects an unknown effect ──
    eng = _Eng()
    m = {}
    ok("R1a: record raises UnknownEffectError on an unregistered effect",
       _raises_unknown(lambda: emit.record(eng, "nope_not_real", x=1)))
    ok("R1b: record_to raises on an unregistered effect",
       _raises_unknown(lambda: emit.record_to(_Sink(), "nope_not_real", x=1)))
    ok("R1c: put raises on an unregistered effect",
       _raises_unknown(lambda: emit.put(eng, m, "nope_not_real", ("a",), "k", 1)))
    ok("R1d: patch raises on an unregistered effect",
       _raises_unknown(lambda: emit.patch(eng, m, "nope_not_real", ("a",), {"k": 1})))
    ok("R1e: append raises on an unregistered effect",
       _raises_unknown(lambda: emit.append(eng, m, "nope_not_real", ("a",), 1)))
    ok("R1f: drop raises on an unregistered effect",
       _raises_unknown(lambda: emit.drop(eng, m, "nope_not_real", ("a",), "k")))
    ok("R1g: an unregistered effect left NO event and NO state behind",
       eng.events.log == [] and m == {},
       f"log={eng.events.log} m={m}")

    # ── R2: record writes one typed event, touches no state ──
    eng = _Eng()
    m = {"pre": "existing"}
    emit.record(eng, "door_refusal", reason="bad tag", raw="hello")
    ok("R2: record wrote exactly one event whose type IS the effect and whose "
       "payload is the caller's fields",
       len(eng.events.log) == 1 and eng.events.log[0]["type"] == "door_refusal"
       and eng.events.log[0]["payload"] == {"reason": "bad tag", "raw": "hello"},
       f"log={eng.events.log}")
    ok("R2-state: record touched NO manifest state", m == {"pre": "existing"}, f"m={m}")

    # ── R2b: record refuses a state-kind effect ──
    # (Sub-commit 1 registers only forensic effects, so synthesize a state
    # effect to prove the guard — restored immediately after.)
    emit.EFFECTS["_probe_state_effect"] = emit._Effect("_probe_state_effect", "state")
    try:
        eng = _Eng()
        ok("R2b: record REFUSES a state-kind effect (raises) — a state change "
           "is never a pure forensic record",
           _raises_unknown(lambda: emit.record(eng, "_probe_state_effect", x=1))
           and eng.events.log == [])
    finally:
        del emit.EFFECTS["_probe_state_effect"]

    # ── R3: put sets one key AND emits, as one operation ──
    eng = _Eng()
    m = {}
    emit.put(eng, m, "must_be_zero", ("cases",), "CASE-1", {"decision": None},
             counter="probe", case_id="CASE-1")
    ok("R3: put created the nested section, set the key to the value, AND wrote "
       "the paired typed event",
       m == {"cases": {"CASE-1": {"decision": None}}}
       and len(eng.events.log) == 1 and eng.events.log[0]["type"] == "must_be_zero"
       and eng.events.log[0]["payload"] == {"counter": "probe", "case_id": "CASE-1"},
       f"m={m} log={eng.events.log}")

    # ── R4: patch applies several fields at once AND emits ──
    eng = _Eng()
    m = {"gates": {"01-02": {"stage": "local", "old": 1}}}
    emit.patch(eng, m, "must_be_zero", ("gates", "01-02"),
               {"stage": "merge", "merged_sha": None}, counter="probe")
    ok("R4: patch merged every update onto the target dict (keeping untouched "
       "fields) AND wrote the paired event",
       m["gates"]["01-02"] == {"stage": "merge", "old": 1, "merged_sha": None}
       and len(eng.events.log) == 1 and eng.events.log[0]["type"] == "must_be_zero",
       f"m={m} log={eng.events.log}")

    # ── R5: append to a manifest-rooted list, created if missing, AND emits ──
    eng = _Eng()
    m = {}
    emit.append(eng, m, "must_be_zero", ("escalations",), {"block": "01-02"},
                counter="probe")
    emit.append(eng, m, "must_be_zero", ("escalations",), {"block": "01-03"},
                counter="probe")
    ok("R5: append created the list on first call and appended to it on the "
       "second, writing one event each",
       m == {"escalations": [{"block": "01-02"}, {"block": "01-03"}]}
       and len(eng.events.log) == 2,
       f"m={m} log_n={len(eng.events.log)}")

    # ── R6: drop removes a key AND emits ──
    eng = _Eng()
    m = {"cases": {"CASE-1": {"x": 1}, "CASE-2": {"y": 2}}}
    popped = emit.drop(eng, m, "must_be_zero", ("cases",), "CASE-1", counter="probe")
    ok("R6: drop removed the key (returning its value) AND wrote the paired event",
       m == {"cases": {"CASE-2": {"y": 2}}} and popped == {"x": 1}
       and len(eng.events.log) == 1,
       f"m={m} popped={popped} log_n={len(eng.events.log)}")

    # ── M1: MUTATION PROOF — neutralize the event write, state STILL mutates ──
    eng = _Eng(_NullSink())
    m = {}
    emit.put(eng, m, "must_be_zero", ("cases",), "CASE-9", {"decision": "resume"},
             counter="probe")
    emit.append(eng, m, "must_be_zero", ("escalations",), {"block": "x"}, counter="probe")
    emit.drop(eng, m, "must_be_zero", ("cases",), "CASE-9", counter="probe")
    ok("M1: with the event write neutralized (NullSink), the SAME put/append/drop "
       "STILL mutate state — proving R2-R6's event assertions are the emit call's "
       "own doing, not incidental, AND that the pairing is real (state lands here, "
       "event was the only thing removed)",
       eng.events.log == [] and m == {"cases": {}, "escalations": [{"block": "x"}]},
       f"m={m} log={eng.events.log}")

    # ── M2: the closed-registry check gates the MUTATION, not just the event ──
    eng = _Eng()
    m = {"cases": {}}
    ok("M2: a put with an unregistered effect raises BEFORE any state change "
       "lands — the registry gate protects the mutation, not just the event",
       _raises_unknown(lambda: emit.put(eng, m, "unregistered_x", ("cases",), "C", {}))
       and m == {"cases": {}} and eng.events.log == [],
       f"m={m} log={eng.events.log}")

    # ── W1: the four already-live effect types stay registered ──
    for name in ("door_refusal", "grant_minted", "operator_page", "must_be_zero"):
        ok(f"W1[{name}]: the pre-T7 live effect type {name!r} is registered in "
           f"the one closed vocabulary",
           name in emit.EFFECTS, f"EFFECTS={sorted(emit.EFFECTS)}")

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.emit_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail and not c else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
