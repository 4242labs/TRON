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

  test:<event_emission_completeness>  (T7 FINAL sub-commit, AC-12) — the
      completeness lint itself (`core/r3_lint.py::run_completeness`, scoped
      to `production_files()`, never `harness_files()`'s rig surface):
      EVERY production `core/*.py` module (never `core/emit.py` itself, the
      one legal writer) is genuinely clean of raw manifest-rooted writes —
      neither a literal `manifest[...] = ...` NOR a raw write onto a
      by-reference sub-object (`gate_state`/a worker record/a job dict) that
      bypasses this module. Proven honest (never vacuous) by two companion
      mutation probes run against SYNTHETIC fixture source (never the real
      tree) at C1/C2 below: a literal `manifest[...] = ...` is caught, and a
      by-reference `gate_state[...] = ...` is caught too — so a PASS on the
      real tree is the lint genuinely finding nothing, not a lint that can't
      find anything.

`ok(name, cond, detail)`; `main()` prints `PASS (n/m)`, exits non-zero on fail.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_APP_ROOT, "engine"))
sys.path.insert(0, _HERE)

import emit      # noqa: E402 — core/emit.py, the unit under test
import r3_lint    # noqa: E402 — core/r3_lint.py, T7's completeness-lint machinery

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

    # ── C1/C2: the completeness lint is honest, not vacuous (SYNTHETIC
    #     fixture source only — never the real tree) ──
    c1_src = ('def foo(manifest, block):\n'
              '    manifest["gates"][block]["stage"] = "closed"\n')
    c1_violations = r3_lint.lint_source_completeness(c1_src, path="<c1-fixture>")
    ok("C1 (MUTATION PROBE — must be GREEN): a literal `manifest[...] = ...` "
       "raw write in synthetic fixture source IS caught by the completeness "
       "lint — proves the lint's `manifest`-name seed still fires",
       len(c1_violations) == 1 and c1_violations[0].rule == "MANIFEST_DIRECT_WRITE",
       f"violations={[str(v) for v in c1_violations]}")

    c2_src = ('def advance(eng, block, gate_state):\n'
              '    gate_state["stage"] = "closed"\n')
    c2_violations = r3_lint.lint_source_completeness(c2_src, path="<c2-fixture>")
    ok("C2 (MUTATION PROBE — must be GREEN): a raw write onto a BY-REFERENCE "
       "sub-object parameter (`gate_state`, PRODUCTION_BYREF_PARAMS) in "
       "synthetic fixture source IS caught — proves the by-reference seeding "
       "genuinely extends coverage, not just the base `manifest`-name seed",
       len(c2_violations) == 1 and c2_violations[0].rule == "MANIFEST_DIRECT_WRITE",
       f"violations={[str(v) for v in c2_violations]}")

    c3_src = ('import emit\n'
              'def advance(eng, block, gate_state):\n'
              '    emit.patch_obj(eng, "gate_escalated", gate_state, {"stage": "closed"})\n')
    c3_violations = r3_lint.lint_source_completeness(c3_src, path="<c3-fixture>")
    ok("C3 (NON-VACUITY CONTROL — must be GREEN): the IDENTICAL scenario, "
       "routed genuinely through emit.patch_obj instead of a raw write, "
       "stays CLEAN — C1/C2's RED is the lint finding a real violation, "
       "never a lint that flags every by-reference parameter unconditionally",
       len(c3_violations) == 0, f"violations={[str(v) for v in c3_violations]}")

    c4_src = ('def helper():\n'
              '    gate_state = {"local": 1}\n'
              '    gate_state["local"] = 2\n')
    c4_violations = r3_lint.lint_source_completeness(c4_src, path="<c4-fixture>")
    ok("C4 (SCOPE-ISOLATION CONTROL — must be GREEN): a purely LOCAL variable "
       "that happens to share a by-reference name but is never bound as a "
       "function PARAMETER is NOT flagged — the by-reference seed is scoped "
       "to the parameter binding, never a bare/global name match",
       len(c4_violations) == 0, f"violations={[str(v) for v in c4_violations]}")

    # ── test:<event_emission_completeness> (T7 FINAL sub-commit, AC-12) ──
    completeness = r3_lint.run_completeness()
    ok("test:<event_emission_completeness>: every production core/*.py module "
       "(core/emit.py excluded — the one legal writer) is genuinely clean of "
       "raw manifest-rooted writes, by-reference sub-object writes included — "
       "0 files red, 0 stale KNOWN_RED, 0 unlisted offenders",
       completeness.ok,
       f"violations_by_file={ {k: [str(v) for v in vs] for k, vs in completeness.violations_by_file.items()} } "
       f"stale={completeness.stale_known_red} unlisted={completeness.unlisted_offenders}")

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.emit_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail and not c else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
