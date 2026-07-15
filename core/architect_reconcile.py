"""core.architect_reconcile — block 01-38 T12 (behavior-preserving split of
`core/architect.py`): the `reconcile` job-kind (M-05) — a block landing
`✅` enqueues a reconcile for the NEXT in-scope, not-yet-dispatched block (by
pipeline order); that block's dispatch is GATED until the reconcile
completes. This module never re-checks real content (no LLM here) — it
ORDERS the reconcile (a structured `arch.reconcile` message) and waits for
a structured `architect.reconciled` report to come back through `core/
router.py` (recorded into `manifest["reconciled"]`); the reconcile-COMPLETE
step itself (observing that report, or the R1b-style no-op backstop) stays
in `core/architect.py::advance` (the dispatcher) — this module never had
its OWN `_advance_reconcile` function even before the split (see `core/
architect.py::advance`'s own `cur.get("kind") == "reconcile"` branch).

See `core/architect.py`'s own module docstring for the full design context
this split preserves verbatim — this module is a RELOCATION, not a
redesign."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import vocab      # noqa: E402 — core/vocab.py, emit template-id constants
import pipeline   # noqa: E402 — core/pipeline.py, in_flight_blocks (dedupe read)
import casestate  # noqa: E402 — core/casestate.py, parked_blocks (dedupe read)
import emit       # noqa: E402 — core/emit.py, block 01-38 T7's single emit API
import architect  # noqa: E402 — core/architect.py, the facade (ARCHITECT_WID + IN_SCOPE_STATUSES + delivery infra)
from architect_enqueue import _has_reconcile_job   # noqa: E402 — core/architect_enqueue.py


def _next_reconcile_target(view, manifest, done_block):
    """The next in-scope, not-done, has-a-file, not-yet-in-flight block AFTER
    `done_block` by living-doc order — the one a just-landed block's drift
    could invalidate (M-05). Skips (never targets, keeps looking forward):
    an abandoned block (`core/casestate.py`'s permanent drop), a currently
    PARKED block (an open case), and anything already in-flight (a live
    worker or open gate — `core/pipeline.py::in_flight_blocks`, the SAME
    definition dispatch eligibility itself uses) — only a clean, untouched
    block is ever reconcile-targeted."""
    abandoned = set(manifest.get("abandoned_blocks") or [])
    parked = casestate.parked_blocks(manifest)
    inflight = pipeline.in_flight_blocks(manifest)
    rows = sorted(view, key=lambda r: r.get("order") or 1e9)
    seen = False
    for r in rows:
        if r["id"] == done_block:
            seen = True
            continue
        if not seen:
            continue
        bid = r["id"]
        if bid in abandoned or bid in parked or bid in inflight:
            continue
        if r.get("status") in architect.IN_SCOPE_STATUSES and r.get("has_block_file"):
            return bid
    return None


def _enqueue_reconcile(eng, manifest, view, done_block):
    reconciled = set(manifest.get("reconciled") or [])
    nxt = _next_reconcile_target(view, manifest, done_block)
    if not nxt or nxt in reconciled or _has_reconcile_job(manifest, nxt):
        return
    job = {"kind": "reconcile", "block": nxt, "after": done_block, "ordered": False}
    emit.append(eng, manifest, "architect_reconcile_job_enqueued", ("architect_queue",),
               job, block=nxt, after=done_block)
    eng.log("flow", f"architect: {done_block!r} landed ✅ -> enqueued reconcile "
                    f"for {nxt!r} (M-05) — its dispatch is gated until reconciled")


def _order_reconcile(eng, job):
    """One reconcile-job order: a structured `arch.reconcile` message, sent
    once. No content-check of this module's own (no LLM in this brick — see
    module docstring) — completion is observed exclusively via a LATER
    `architect.reconciled` report `core/router.py` routes into `manifest
    ["reconciled"]`; this function never mutates that itself."""
    text = (f"[TRON]  architect — reconcile {job['block']!r} against "
           f"{job.get('after')!r}'s just-landed drift and report "
           f"architect.reconciled once clear.")
    if not eng.dry:
        eng.emit(vocab.TPL_ARCH_RECONCILE, text,
                slots={"block": job["block"], "after": job.get("after")},
                worker_id=architect.ARCHITECT_WID, kind=vocab.TPL_ARCH_RECONCILE)
    architect._stamp_dispatch(eng, job, text, "arch.reconcile", extra={"ordered": True})   # ADR-0009 R-B
