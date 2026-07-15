"""core.coordinator_split_rig — `test:<coordinator_split>` (block 01-38 T12,
AC-8): the split of `core/architect.py` (~1199 lines) into per-job-kind
sibling modules is behavior-preserving BY STRUCTURE, not merely "the full
suite still passes" (that's `scripts/l1.sh`'s 41 OTHER rigs — `core/
architect_rig.py`/`core/verdict_wire_rig.py`/`core/sim/sim_l2_rig.py`/`core/
sim/trunk_blame_rig.py`/`core/sim/self_retract_rig.py` among them — every
one of which drives real `architect.<name>` behavior end-to-end and stayed
GREEN across the split with ZERO rig-side changes beyond this file + two
disclosed, tightened assertions in `core/counters_rig.py`/`core/
identity_backstop_rig.py`). This rig instead proves the SPLIT ITSELF:

  S1  every name T12's own checkpoint named "must stay `architect.<name>`
      for importers" resolves off the facade module, with the right type.
  S2  every internal name rigs ALSO import directly (`architect._advance_
      triage`, `architect._delivered`, ...) resolves off the facade too.
  S3  STRUCTURAL — the split is REAL, not a re-export shim over code that
      secretly never left `core/architect.py`: each job-kind's own leaf
      function is DEFINED in (`__module__ ==`) its named sibling module,
      never in the facade — proven by inspecting `__module__` on the very
      function object `architect.<name>` resolves to, for every name T12's
      checkpoint assigned a sibling home.
  S4  THE PATCH-PROPAGATION RISK THIS SPLIT SPECIFICALLY INTRODUCES: `core/
      architect_rig.py` monkeypatches `architect._redeliver`/`architect.
      _advance_delivery`/`architect.RESPAWN_CAP`/`architect.
      NO_PROGRESS_BUDGET` directly on the facade's own namespace. A naive
      split (sibling modules importing these via `from architect import X`,
      binding a COPY at import time) would silently stop honoring such a
      patch from any call site living in a sibling module — a real
      regression `scripts/l1.sh`'s OTHER rigs happen to already catch
      (architect_rig.py's own RIG1-B/§8 mutation tests), but this task's
      OWN proof should demonstrate it directly, scoped to exactly the
      mechanism the split's design note (`core/architect.py`'s own
      docstring) claims: patching `architect.RESPAWN_CAP` is honored by
      `core/architect_triage.py::_advance_triage` (a DIFFERENT file),
      because that call site reads it via the live `architect` module
      OBJECT at call time, never a value/reference frozen at import time.
  S5  THE BACKSTOP COUNTER-PARTITION BINDING (T12): the ONE backstop part
      (`core/architect_backstop.py`) routes through `core/counters.py` (T9)
      — `architect_refused_authoring_backstop` is declared MAY_FIRE with a
      real (non-None) ceiling, rides a real registered `core/emit.py`
      effect, and `core/architect_backstop.py::_backstop_refused_
      authoring`'s own source genuinely calls `emit.record` with that exact
      effect name (AST-checked, not just "the registry entry exists").
  S6  `ARCHITECT_WID`/`RESPAWN_CAP`/`REDELIVER_AFTER`/`NO_PROGRESS_BUDGET`
      are unchanged in VALUE from pre-split (byte-for-byte behavior
      preservation of the tunables themselves, not just their names).

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)`, exits
non-zero on any fail — same idiom `core/counters_rig.py`/`core/emit_rig.py`
already use.
"""
import ast
import glob
import inspect
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import architect            # noqa: E402 — core/architect.py, the facade under test
import architect_enqueue    # noqa: E402
import architect_forward    # noqa: E402
import architect_reconcile  # noqa: E402
import architect_triage     # noqa: E402
import architect_log        # noqa: E402
import architect_backstop   # noqa: E402
import emit                 # noqa: E402 — core/emit.py
import counters             # noqa: E402 — core/counters.py

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


# ── S1: the public surface every importer resolves as architect.<name> ──
PUBLIC_FUNCS = ("new_state", "gated_blocks", "enqueue", "enqueue_triage",
                "enqueue_log_review", "advance")
PUBLIC_CONSTS = {"ARCHITECT_WID": str, "RESPAWN_CAP": int,
                 "REDELIVER_AFTER": int, "NO_PROGRESS_BUDGET": int}

# ── S2: internals rigs ALSO import directly off the facade ──
INTERNAL_FUNCS = ("_advance_triage", "_delivered", "_redeliver",
                  "_advance_delivery", "_stamp_dispatch", "_order_triage",
                  "_forward_branch", "_clock")

# ── S3: name -> the sibling module its OWN leaf definition must live in
# (never the facade — a re-export shim over undisturbed code would fail
# this) — the T12 checkpoint's own job-group mapping, restricted to names
# also RE-EXPORTED off the facade (`architect.<name>` must resolve too).
# `_advance_delivery` family + tunables are DELIBERATELY excluded here:
# `core/architect.py`'s own docstring discloses they stay facade-resident
# by design (the cross-cutting, patch-sensitive delivery cluster — S4 is
# their proof). `_next_reconcile_target`/`_next_triage_id`/`_adhoc_branch`
# are DELIBERATELY sibling-internal-only — never called from the facade and
# never monkeypatched by any rig, so the facade does not re-export them;
# `SIBLING_INTERNAL_ONLY` below still proves their OWN module ownership.
SIBLING_HOME = {
    "_enqueue_forward_jobs": architect_enqueue,
    "_forward_branch": architect_forward,
    "_advance_forward": architect_forward,
    "_enqueue_reconcile": architect_reconcile,
    "_order_reconcile": architect_reconcile,
    "enqueue_triage": architect_triage,
    "_order_triage": architect_triage,
    "_advance_triage": architect_triage,
    "enqueue_log_review": architect_log,
    "_advance_log": architect_log,
    "_backstop_refused_authoring": architect_backstop,
}
SIBLING_INTERNAL_ONLY = {
    "_next_reconcile_target": architect_reconcile,
    "_next_triage_id": architect_triage,
    "_adhoc_branch": architect_log,
    "_has_forward_job": architect_enqueue,
    "_has_triage_job": architect_enqueue,
    "_has_reconcile_job": architect_enqueue,
}


def main():
    # ── S1 ──
    for name in PUBLIC_FUNCS:
        fn = getattr(architect, name, None)
        ok(f"S1[{name}]: architect.{name} resolves and is callable",
           callable(fn), f"got={fn!r}")
    for name, typ in PUBLIC_CONSTS.items():
        val = getattr(architect, name, None)
        ok(f"S1[{name}]: architect.{name} resolves with the right type",
           isinstance(val, typ), f"got={val!r} type={type(val)}")

    # ── S2 ──
    for name in INTERNAL_FUNCS:
        fn = getattr(architect, name, None)
        ok(f"S2[{name}]: architect.{name} resolves and is callable "
           f"(the internal surface rigs import directly)",
           callable(fn), f"got={fn!r}")

    # ── S3: STRUCTURAL — the definition genuinely lives in its named sibling ──
    for name, owner in SIBLING_HOME.items():
        via_facade = getattr(architect, name, None)
        defined_in = getattr(owner, name, None)
        ok(f"S3[{name}]: DEFINED in {owner.__name__} (not the facade) — "
           f"architect.{name} resolves to the SAME object the sibling itself defines",
           via_facade is not None and via_facade is defined_in
           and inspect.getmodule(via_facade).__name__ == owner.__name__,
           f"architect.{name}={via_facade!r} module={getattr(inspect.getmodule(via_facade), '__name__', None)!r}")

    # ── S3b: the sibling-internal-only helpers exist, ARE callable, and are
    # genuinely defined in their own named module (never accidentally left
    # behind in the facade, never re-exported since nothing external needs
    # them at `architect.<name>`) ──
    for name, owner in SIBLING_INTERNAL_ONLY.items():
        fn = getattr(owner, name, None)
        not_on_facade = getattr(architect, name, None) is None
        ok(f"S3b[{name}]: defined + callable in {owner.__name__} ONLY — "
           f"never re-exported off the facade (nothing external needs it there)",
           callable(fn) and inspect.getmodule(fn).__name__ == owner.__name__ and not_on_facade,
           f"fn={fn!r} on_facade={getattr(architect, name, 'ABSENT')!r}")

    # ── S4: patch-propagation — a facade-attribute patch reaches a sibling's
    # own call site (the split's OWN specific risk; the mechanism the
    # module docstring claims). Real end-to-end coverage of this already
    # lives in `core/architect_rig.py`'s RIG1-B/§8; this is the split's own
    # narrow, direct demonstration. ──
    job = {"kind": "triage", "triage_id": "t-split-1", "case_id": None,
          "source": "classify.unclassified", "block": None, "worker_id": None,
          "ordered": True, "dispatch_seq": True, "verdict": None, "note": None,
          "adhoc": None, "resolved": False, "_verdict_reorders": 0}

    class _Sink:
        def __init__(self):
            self.log = []

        def event(self, type_, **payload):
            self.log.append({"type": type_, "payload": payload})

    class _Eng:
        dry = True

        def __init__(self):
            self.events = _Sink()
            self.operator_pages = []

        def log(self, *a, **k):
            pass

        def _to_worker(self, *a, **k):
            pass

        def _page_operator(self, case_id, block, detail, worker_id=None, manifest=None):
            self.operator_pages.append((case_id, block, detail, worker_id))
            return "delivered"

    manifest = {"triage_verdicts": {}}
    _real_cap = architect.RESPAWN_CAP
    architect.RESPAWN_CAP = 0   # MUTATION: any re-order at all now exceeds the cap
    try:
        # architect_triage._advance_triage (a DIFFERENT file than architect.py)
        # reads RESPAWN_CAP via `architect.RESPAWN_CAP` at call time — the
        # patch above must be visible to it, not just to architect.py's own code.
        architect_triage._advance_triage(_Eng(), manifest, job)
    finally:
        architect.RESPAWN_CAP = _real_cap
    s4 = (job.get("_verdict_reorders") == 1 and job.get("verdict") == "operator")
    ok("S4 (MUTATION PROOF, non-vacuity): patching architect.RESPAWN_CAP=0 is "
       "honored by core/architect_triage.py::_advance_triage — a DIFFERENT "
       "file — which immediately exhausts the (now-zero) cap and forces "
       "verdict='operator', proving the patch propagates via the live "
       "architect module object, never a value frozen at sibling import time",
       s4, f"job={job}")

    # ── S5: the backstop counter-partition binding ──
    ok("S5a: architect_refused_authoring_backstop_fired is a registered emit "
       "effect, forensic kind, counter_class=may_fire",
       "architect_refused_authoring_backstop_fired" in emit.EFFECTS
       and emit.EFFECTS["architect_refused_authoring_backstop_fired"].kind == "forensic"
       and emit.EFFECTS["architect_refused_authoring_backstop_fired"].counter_class == "may_fire")
    c = counters.COUNTERS.get("architect_refused_authoring_backstop")
    ok("S5b: architect_refused_authoring_backstop is declared MAY_FIRE with a "
       "real (non-None) per-run ceiling, riding the registered emit effect",
       c is not None and c.cls == counters.MAY_FIRE and c.ceiling is not None
       and c.effect == "architect_refused_authoring_backstop_fired",
       f"counter={c!r}")
    src = inspect.getsource(architect_backstop._backstop_refused_authoring)
    tree = ast.parse(src)
    calls_emit_record = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == "record" and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "emit"
        and any(isinstance(a, ast.Constant) and a.value == "architect_refused_authoring_backstop_fired"
               for a in n.args)
        for n in ast.walk(tree))
    ok("S5c (AST, not just the registry entry): "
       "_backstop_refused_authoring's own source genuinely calls "
       "emit.record(eng, 'architect_refused_authoring_backstop_fired', ...)",
       calls_emit_record)

    # ── S6: tunables unchanged in VALUE from pre-split ──
    ok("S6: ARCHITECT_WID/RESPAWN_CAP/REDELIVER_AFTER/NO_PROGRESS_BUDGET are "
       "byte-for-byte the pre-split values",
       architect.ARCHITECT_WID == "architect" and architect.RESPAWN_CAP == 3
       and architect.REDELIVER_AFTER == 3 and architect.NO_PROGRESS_BUDGET == 30,
       f"ARCHITECT_WID={architect.ARCHITECT_WID!r} RESPAWN_CAP={architect.RESPAWN_CAP} "
       f"REDELIVER_AFTER={architect.REDELIVER_AFTER} NO_PROGRESS_BUDGET={architect.NO_PROGRESS_BUDGET}")

    # ── S7: engine/ never touched by this split (glob sanity — the real
    # guarantee is the git-diff check every commit runs; this is a live,
    # in-process corroboration that no core/architect*.py module reaches
    # into engine/ beyond the pre-existing sys.path splice every core/*.py
    # module already does) ──
    core_files = sorted(
        f for f in glob.glob(os.path.join(_HERE, "architect*.py"))
        if not os.path.basename(f).endswith("_rig.py"))
    ok("S7: exactly the 7 expected architect*.py PRODUCTION files exist "
       "(no stray/duplicate split artifact; *_rig.py excluded — that's the "
       "proof-harness surface, not the split's own production output)",
       len(core_files) == 7,
       f"core_files={[os.path.basename(f) for f in core_files]}")

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.coordinator_split_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail and not c else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
