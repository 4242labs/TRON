"""core.architect_forward — block 01-38 T12 (behavior-preserving split of
`core/architect.py`): the `forward` job-kind. Author a MISSING upcoming
block file (an in-scope roadmap row with no block file yet). The architect
writes the block doc on its OWN `arch/<block>-forward` branch and lands it
via `core.landing.land_via_grant` under a CONTENT-BOUND case-id
(`role="forward"`). See `core/architect.py`'s own module docstring for the
full design context this split preserves verbatim — this module is a
RELOCATION, not a redesign.

Cross-module note (T12): this module reads `architect.ARCHITECT_WID` and
`architect._stamp_dispatch` via the `architect` module OBJECT (never a
`from architect import ...` name-bound copy) — `core/architect_rig.py`
monkeypatches `architect._redeliver`/`architect._advance_delivery`/
`architect.RESPAWN_CAP`/`architect.NO_PROGRESS_BUDGET` directly on the
facade's own namespace (mutation-proof rigs); routing every facade-owned
name through the live `architect` module object (attribute lookup at CALL
TIME, never an import-time value/reference copy) is what keeps those
patches honored regardless of which physical file the caller lives in.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import gitobs     # noqa: E402 — core/gitobs.py, the ONE git-observation seam
import vocab      # noqa: E402 — core/vocab.py, emit template-id constants
import landing    # noqa: E402 — core/landing.py, Wave-1's ONE landing primitive
import emit       # noqa: E402 — core/emit.py, block 01-38 T7's single emit API
import architect  # noqa: E402 — core/architect.py, the facade (ARCHITECT_WID + delivery infra)


def _forward_branch(block):
    return f"arch/{block}-forward"


def _advance_forward(eng, manifest, job):
    """One forward-job step: order once (side effect, idempotent — mirrors
    `core/gate.py`'s own "order once, then poll" stages), then every
    subsequent call re-checks the branch and attempts the content-bound
    land via the Wave-1 primitive, reused verbatim. `job["landed"]` is set
    ONLY once `land_via_grant` itself reports `"landed"` (real ancestry
    observed) — never on a message alone."""
    block = job["block"]
    branch = job.get("branch") or _forward_branch(block)
    if job.get("branch") != branch:
        emit.patch_obj(eng, "architect_forward_branch_bound", job, {"branch": branch},
                       block=block)

    if not job.get("ordered"):
        text = (f"[TRON]  architect — block {block!r} is missing its block file. "
               f"Author it on {branch} (meta/blocks/{block}.md, Status: 📋 To do) "
               f"and push — I land it once it resolves.")
        if not eng.dry:
            eng.emit(vocab.TPL_ARCH_FORWARD, text, slots={"block": block},
                    worker_id=architect.ARCHITECT_WID, kind=vocab.TPL_ARCH_FORWARD)
        architect._stamp_dispatch(eng, job, text, "arch.forward", extra={"ordered": True})   # ADR-0009 R-B
        eng.log("flow", f"architect[forward:{block}]: ordered authoring on {branch} "
                        f"(dispatch_seq={job.get('dispatch_seq')!r})")
        return

    truth_ref = eng._truth_ref()
    patch_id = gitobs.patch_id(eng.paths["root"], branch, truth_ref, eng.dry)
    # Content-bound to the CURRENT patch-id, never a stale cached id (T2-17 fix;
    # single-source in landing.stage_case_id).
    case_id = landing.stage_case_id(job.get("case_id"), "forward", branch, patch_id)
    emit.patch_obj(eng, "architect_forward_case_bound", job, {"case_id": case_id}, block=block)

    outcome = landing.land_via_grant(eng, case_id, block, branch, architect.ARCHITECT_WID,
                                     "arch.forward", "architect-forward")
    # ADR-0006 R1d: record the grant poll's verdict for `advance`'s backstop.
    # "fail-closed" = the branch's patch-id is unresolvable / no grant minted =
    # the architect authored NOTHING (prose instead of a branch); "pending" =
    # authored & landing (must keep polling, never backstop mid-land).
    emit.patch_obj(eng, "architect_forward_outcome_recorded", job, {"last_outcome": outcome},
                   block=block)
    if outcome == "landed":
        emit.patch_obj(eng, "architect_forward_landed", job, {"landed": True}, block=block)
        eng.log("flow", f"architect[forward:{block}]: block file landed via "
                        f"{branch} -> dispatchable")
    elif outcome == "pending":
        eng.log("flow", f"architect[forward:{block}]: grant live for {case_id}, "
                        f"awaiting land.sh")
    else:
        eng.log("flow", f"architect[forward:{block}]: {outcome} (case {case_id}, "
                        f"branch not authored yet?)")
