"""core.architect_enqueue — block 01-38 T12 (behavior-preserving split of
`core/architect.py`): the clear-ahead `enqueue` step (the `forward`-job
discovery half of `core/architect.py::enqueue`, called BEFORE `core/
switchboard.py::fill` each tick) plus the three cross-job-kind dedupe reads
(`_has_forward_job`/`_has_triage_job`/`_has_reconcile_job`) every enqueue
site (this module's own `_enqueue_forward_jobs`, `architect_reconcile.py`'s
`_enqueue_reconcile`, `architect_triage.py`'s `enqueue_triage`) shares — one
dedupe implementation per job-kind, never re-derived at each call site.

See `core/architect.py`'s own module docstring for the full design context
this split preserves verbatim — this module is a RELOCATION, not a
redesign. `architect.IN_SCOPE_STATUSES` is read via the live `architect`
module OBJECT (never a name-bound copy) purely for import-cycle hygiene —
it is never itself monkeypatched, but every facade-owned name this split's
sibling modules read follows the SAME one rule for uniformity (see `core/
architect_forward.py`'s own note on why that rule exists for the genuinely
patch-sensitive names)."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import emit                              # noqa: E402 — core/emit.py, block 01-38 T7's single emit API
import architect                         # noqa: E402 — core/architect.py, the facade (IN_SCOPE_STATUSES)
from architect_forward import _forward_branch   # noqa: E402 — core/architect_forward.py


def _has_forward_job(manifest, block):
    queue = manifest.get("architect_queue") or []
    if any(j.get("kind") == "forward" and j.get("block") == block for j in queue):
        return True
    arch = manifest.get("architect") or {}
    cur = arch.get("current_job")
    return bool(cur and cur.get("kind") == "forward" and cur.get("block") == block)


def _has_triage_job(manifest, case_id):
    """Dedupe for a case-bearing triage job only (`case_id is not None`) —
    a case-less one (`core/classify.py`'s unclassified path) is NEVER
    deduped, same "no dedupe across independent occurrences" discipline
    `enqueue_log_review` already keeps for its own findings."""
    if case_id is None:
        return False
    queue = manifest.get("architect_queue") or []
    if any(j.get("kind") == "triage" and j.get("case_id") == case_id for j in queue):
        return True
    arch = manifest.get("architect") or {}
    cur = arch.get("current_job")
    return bool(cur and cur.get("kind") == "triage" and cur.get("case_id") == case_id)


def _has_reconcile_job(manifest, block):
    queue = manifest.get("architect_queue") or []
    if any(j.get("kind") == "reconcile" and j.get("block") == block for j in queue):
        return True
    arch = manifest.get("architect") or {}
    cur = arch.get("current_job")
    return bool(cur and cur.get("kind") == "reconcile" and cur.get("block") == block)


def _enqueue_forward_jobs(eng, manifest, view):
    """Clear-ahead (blueprint §1 SWITCHBOARD's own step, re-expressed here
    for the architect's OWN queue): every in-scope roadmap row with no block
    file yet gets a `forward` job — idempotent, never a second job for a
    block already queued/current."""
    for row in view:
        if row.get("has_block_file"):
            continue
        if row.get("status") not in architect.IN_SCOPE_STATUSES:
            continue
        block = row["id"]
        if not block or _has_forward_job(manifest, block):
            continue
        job = {"kind": "forward", "block": block, "branch": _forward_branch(block),
              "ordered": False, "case_id": None, "landed": False}
        emit.append(eng, manifest, "architect_forward_job_enqueued", ("architect_queue",),
                    job, block=block)
        eng.log("flow", f"architect: clear-ahead enqueued forward for missing "
                        f"block file {block!r}")
