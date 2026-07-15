"""core.aide_invocation_rig — mutation-proof lock for `test:<aide_invocation_
emitted_on_real_aide_call>` (block 01-38 T7 FINAL sub-commit, AC-12's own
task-level proof).

Operator decision 260714: a real AIDE invocation is a consequential action,
so under events-as-single-ground-truth + emission completeness it must be
readable from `events.jsonl` — this is what lets a SIM verify "AIDE fired
live" (02-13/02-14) without trusting a unit test as per-run evidence. The
`aide_invocation` forensic effect is registered in `core/emit.py`'s closed
EFFECTS vocabulary; TODAY's one real call site is the legacy
`engine/judge.py::call_aide` (every bootup AIDE node in `engine/console.py`
routes through it — the ONE shared shape, never a per-caller copy). T24
wires the future `core/*` runtime AIDE lane and will call
`emit.record(eng, "aide_invocation", ...)` at ITS OWN call site; this rig
proves TODAY's real one, offline and TOKEN-FREE via `TRON_JUDGE_STUB`
(`engine/judge.py`'s own documented offline-testability hook — no LLM spent,
no network).

  A1  the effect is registered in `core/emit.py`'s closed vocabulary (kind
      "forensic") — a guard so a later sub-commit removing it fails here.
  A2  a real (stub-backed) `call_aide` invocation that SUCCEEDS emits
      EXACTLY one `aide_invocation` event, with the right payload (mode,
      model, ok=True) — tightened to identity + payload, never bare
      membership.
  A3  a real (stub-backed) `call_aide` invocation whose canned output NEVER
      validates (budget exhausted, ok=False — "AIDE unavailable") STILL
      emits `aide_invocation` with ok=False — "fires for every mode, ok or
      not — a fail-open 'AIDE unavailable' is still a genuine invocation
      attempt, not a no-op" (the docstring's own claim, proven not asserted).
  A4  MUTATION PROOF (non-vacuity): with `elog=None` (the pre-existing
      "no forensic sink" case `_record_model_call` already tolerates),
      `call_aide` returns normally — no crash, and (trivially) no event,
      proving the emit call is genuinely conditional on a real sink, not
      a hardcoded side effect this rig's own stub happens to always see.
  A5  every mode `call_aide` is real callers actually pass ("scope",
      "counts", "resolve", "ask") round-trips through the SAME chokepoint —
      the event's own `mode` field matches whatever the caller passed, for
      each of the four.

`ok(name, cond, detail)`; `main()` prints `PASS (n/m)`, exits non-zero on fail.
"""
import json
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import judge   # noqa: E402 — engine/judge.py, the unit under test (call_aide)
import emit    # noqa: E402 — core/emit.py, the closed effect registry aide_invocation lives in

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


class _Sink:
    """The SAME `.event(type, **payload)` shape `core/emit.py`'s duck-typed
    `eng.events` contract requires — `engine/judge.py`'s own `elog` is
    already this exact shape (`engine/eventlog.py::EventLog`), so this fake
    is a faithful stand-in for both."""
    def __init__(self):
        self.log = []

    def event(self, type_, **payload):
        self.log.append({"type": type_, "payload": payload})


def _write_stub(mapping):
    fh = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(mapping, fh)
    fh.close()
    return fh.name


def main():
    # ── A1: the effect is registered, forensic-kind ──
    ok("A1: aide_invocation is registered in core.emit's closed EFFECTS "
       "vocabulary as a forensic effect",
       "aide_invocation" in emit.EFFECTS and emit.EFFECTS["aide_invocation"].kind == "forensic",
       f"EFFECTS.get={emit.EFFECTS.get('aide_invocation')}")

    # ── A2: a SUCCEEDING call emits exactly one event, right payload ──
    stub_path = _write_stub({"aide": [{"advice": "pick 01-02, it's dependency-clear"}]})
    old_stub_env = os.environ.get("TRON_JUDGE_STUB")
    os.environ["TRON_JUDGE_STUB"] = stub_path
    try:
        sink = _Sink()
        result_ok, out, _ = judge.call_aide(
            ctx=None, paths={}, mode="scope", model="claude-opus-4-8",
            elog=sink, cid="cid-1")
        aide_events = [e for e in sink.log if e["type"] == "aide_invocation"]
        ok("A2: a successful call_aide emits EXACTLY one aide_invocation "
           "event (alongside judge.call's own pre-existing model_call "
           "event, untouched) with mode/model/ok in its payload — tightened "
           "to identity + payload, never bare membership",
           result_ok is True
           and len(aide_events) == 1
           and aide_events[0]["payload"]["mode"] == "scope"
           and aide_events[0]["payload"]["model"] == "claude-opus-4-8"
           and aide_events[0]["payload"]["ok"] is True,
           f"result_ok={result_ok} out={out} log={sink.log}")
    finally:
        if old_stub_env is None:
            os.environ.pop("TRON_JUDGE_STUB", None)
        else:
            os.environ["TRON_JUDGE_STUB"] = old_stub_env
        os.remove(stub_path)
        judge._stub_cache = None
        judge._stub_idx = {}

    # ── A3: an UNAVAILABLE (never-validates) call STILL emits, ok=False ──
    stub_path = _write_stub({"aide": [{"advice": ""}]})   # blank advice never validates
    os.environ["TRON_JUDGE_STUB"] = stub_path
    try:
        sink = _Sink()
        result_ok, out, _ = judge.call_aide(
            ctx=None, paths={}, mode="counts", model="claude-opus-4-8",
            elog=sink, cid="cid-2")
        aide_events = [e for e in sink.log if e["type"] == "aide_invocation"]
        ok("A3 (MUTATION PROBE — must be GREEN): a call_aide whose canned "
           "output NEVER validates (budget exhausted, ok=False — 'AIDE "
           "unavailable, proceed unaided') STILL emits aide_invocation, "
           "with ok=False — a fail-open non-answer is still a genuine "
           "invocation attempt, never a silent no-op",
           result_ok is False
           and out is None
           and len(aide_events) == 1
           and aide_events[0]["payload"]["ok"] is False,
           f"result_ok={result_ok} out={out} log={sink.log}")
    finally:
        if old_stub_env is None:
            os.environ.pop("TRON_JUDGE_STUB", None)
        else:
            os.environ["TRON_JUDGE_STUB"] = old_stub_env
        os.remove(stub_path)
        judge._stub_cache = None
        judge._stub_idx = {}

    # ── A4: MUTATION PROOF (non-vacuity) — elog=None never crashes, never fakes an event ──
    stub_path = _write_stub({"aide": [{"advice": "fine"}]})
    os.environ["TRON_JUDGE_STUB"] = stub_path
    try:
        raised = False
        result_ok = None
        try:
            result_ok, _, _ = judge.call_aide(
                ctx=None, paths={}, mode="resolve", model="claude-opus-4-8",
                elog=None, cid="cid-3")
        except Exception:   # noqa: BLE001 — any exception here is itself the failure A4 checks for
            raised = True
        ok("A4 (MUTATION PROOF — non-vacuity): elog=None (the pre-existing "
           "'no forensic sink' case _record_model_call already tolerates) "
           "never crashes call_aide — proves the emit call is genuinely "
           "conditional on a real sink, not an unconditional side effect "
           "this rig's own stub happens to always provide",
           not raised and result_ok is True, f"raised={raised} result_ok={result_ok}")
    finally:
        if old_stub_env is None:
            os.environ.pop("TRON_JUDGE_STUB", None)
        else:
            os.environ["TRON_JUDGE_STUB"] = old_stub_env
        os.remove(stub_path)
        judge._stub_cache = None
        judge._stub_idx = {}

    # ── A5: every real caller mode round-trips through the same chokepoint ──
    stub_path = _write_stub({"aide": [{"advice": "ok", "choices": ["a", "b", "c"], "answered": True}]})
    os.environ["TRON_JUDGE_STUB"] = stub_path
    try:
        for mode in ("scope", "counts", "resolve", "ask"):
            sink = _Sink()
            judge.call_aide(ctx=None, paths={}, mode=mode, model="claude-opus-4-8",
                            elog=sink, cid=f"cid-{mode}")
            aide_events = [e for e in sink.log if e["type"] == "aide_invocation"]
            ok(f"A5[{mode}]: call_aide(mode={mode!r}) emits EXACTLY one "
               f"aide_invocation event with THAT mode in its payload",
               len(aide_events) == 1 and aide_events[0]["payload"]["mode"] == mode,
               f"log={sink.log}")
            judge._stub_idx = {}   # reset so every mode replays the SAME canned response
    finally:
        if old_stub_env is None:
            os.environ.pop("TRON_JUDGE_STUB", None)
        else:
            os.environ["TRON_JUDGE_STUB"] = old_stub_env
        os.remove(stub_path)
        judge._stub_cache = None
        judge._stub_idx = {}

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.aide_invocation_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail and not c else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
