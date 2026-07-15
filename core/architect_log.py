"""core.architect_log — block 01-38 T12 (behavior-preserving split of
`core/architect.py`): the `log` job-kind (wave 10) — a `<type>` review's
DONE-REVIEW gate just attested; queue the architect's forward-looking
`log-review` job, turning the review's findings into UPCOMING adhoc block
files (or none, a clean review).

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

import gitobs     # noqa: E402 — core/gitobs.py, the ONE git-observation seam
import landing    # noqa: E402 — core/landing.py, Wave-1's ONE landing primitive
import emit       # noqa: E402 — core/emit.py, block 01-38 T7's single emit API
import architect  # noqa: E402 — core/architect.py, the facade (ARCHITECT_WID + delivery infra)


def _adhoc_branch(adhoc_id):
    return f"arch/{adhoc_id}-logreview"


def enqueue_log_review(eng, manifest, typ, findings):
    """Wave 10 (`core/reviewers.py`): a `<type>` review's DONE-REVIEW gate
    just attested (`reviewers.on_review_done`'s second hand-back) — queue
    the architect's forward-looking `log-review` job: turn the review's
    findings into UPCOMING adhoc block files, or none (a clean review).
    Idempotent bookkeeping only (`manifest["architect"]`/`architect_queue`
    may not exist yet — the very FIRST architect_queue write of the whole
    run, if this project has no missing block files and no reconcile ever
    fired); one `log` job per attested review cycle, never deduped against
    a prior one (each cycle's findings are independent, unlike `forward`/
    `reconcile`'s block-keyed dedupe)."""
    architect._ensure_installed(eng, manifest)
    job = {"kind": "log", "type": typ, "findings": list(findings or []),
          "ordered": False, "adhoc": [], "landed_all": False}
    emit.append(eng, manifest, "architect_log_job_enqueued", ("architect_queue",), job,
               type=typ, findings=len(findings or []))
    eng.log("flow", f"architect: log-review queued for the {typ} review "
                    f"({len(findings or [])} finding(s))")


def _advance_log(eng, manifest, job):
    """One `log`-job step: order ONCE (mints the adhoc block ids + branch
    names for every finding, up front, off a manifest-persisted per-type
    sequence — `manifest["adhoc_seq"]`, mirroring `core/casestate.py::
    next_case_id`'s own "deterministic, monotonic, never uuid/random"
    idiom), then every subsequent call re-checks each still-unlanded entry's
    branch and attempts its content-bound land via the Wave-1 primitive,
    reused verbatim — exactly `_advance_forward`'s own "order once, then
    poll+land every entry" shape, generalized over a LIST instead of one
    block. Zero findings (a clean review) needs no order at all — the job
    completes on this SAME call, nothing ever queued or landed. `job[
    "landed_all"]` is set ONLY once EVERY entry's `land_via_grant` has
    itself reported `"landed"` (real ancestry observed) — never on a
    message alone, and never for a job still holding un-authored entries."""
    if not job.get("ordered"):
        findings = job.get("findings") or []
        entries = []
        if findings:
            typ = job.get("type") or "adhoc"
            seq = manifest.get("adhoc_seq") or {}
            n = int(seq.get(typ, 0))
            for finding in findings:
                n += 1
                adhoc_id = f"adhoc-{typ}-{n}"
                entries.append({"block": adhoc_id, "branch": _adhoc_branch(adhoc_id),
                                "finding": finding, "case_id": None, "landed": False})
            emit.put(eng, manifest, "architect_adhoc_seq_advanced", ("adhoc_seq",), typ, n)
        if not entries:
            emit.patch_obj(eng, "architect_log_ordered", job,
                           {"adhoc": entries, "ordered": True, "landed_all": True},
                           type=job.get("type"))
            eng.log("flow", f"architect[log:{job.get('type')}]: clean review — "
                            f"no findings, nothing queued")
            return
        emit.patch_obj(eng, "architect_log_ordered", job,
                       {"adhoc": entries, "ordered": True}, type=job.get("type"))
        text = (f"[TRON]  architect — log-review for the {job.get('type')} "
               f"review: author + land {len(entries)} upcoming adhoc block "
               f"file(s), one per finding ({', '.join(e['block'] for e in entries)}), "
               f"each on its OWN branch (meta/blocks/<id>.md, Status: 📋 To do, "
               f"plus its pipeline.md row) — I land each once it resolves.")
        if not eng.dry:
            eng._to_worker(architect.ARCHITECT_WID, text, "arch.log-review")
        architect._stamp_dispatch(eng, job, text, "arch.log-review")   # ADR-0009 R-B
        eng.log("flow", f"architect[log:{job.get('type')}]: ordered "
                        f"{len(entries)} adhoc block(s): "
                        f"{[e['block'] for e in entries]} (dispatch_seq="
                        f"{job.get('dispatch_seq')!r})")
        return

    entries = job.get("adhoc") or []
    if not entries:
        emit.patch_obj(eng, "architect_log_poll_recorded", job,
                       {"landed_all": True, "last_outcome": "landed"}, type=job.get("type"))
        return

    truth_ref = eng._truth_ref()
    tick_outcomes = []
    for e in entries:
        if e.get("landed"):
            continue
        block, branch = e["block"], e["branch"]
        patch_id = gitobs.patch_id(eng.paths["root"], branch, truth_ref, eng.dry)
        # Content-bound to the CURRENT patch-id, never a stale cached id (T2-17
        # fix; single-source in landing.stage_case_id).
        case_id = landing.stage_case_id(e.get("case_id"), "logreview", branch, patch_id)
        emit.patch_obj(eng, "architect_log_entry_case_bound", e, {"case_id": case_id},
                       block=block)
        outcome = landing.land_via_grant(eng, case_id, block, branch, architect.ARCHITECT_WID,
                                         "arch.log-review", "architect-logreview")
        tick_outcomes.append(outcome)
        if outcome == "landed":
            emit.patch_obj(eng, "architect_log_entry_landed", e, {"landed": True}, block=block)
            eng.log("flow", f"architect[log:{job.get('type')}]: adhoc block "
                            f"{block!r} landed via {branch} -> dispatchable")
        elif outcome == "pending":
            eng.log("flow", f"architect[log:{job.get('type')}]: grant live for "
                            f"{case_id}, awaiting land.sh")
        else:
            eng.log("flow", f"architect[log:{job.get('type')}]: {outcome} (case "
                            f"{case_id}, branch not authored yet?)")

    landed_all = all(e.get("landed") for e in entries)
    # ADR-0006 R1d: aggregate the tick's poll verdict for `advance`'s backstop.
    # All landed -> done; ANY entry still authoring/landing ("pending") holds the
    # poll (never backstop mid-land); otherwise every un-landed entry is
    # "fail-closed" (nothing authored) -> the architect refused to author its
    # ordered adhoc block(s) — a started-then-refused log-review that must NOT
    # silently drop the reviewer's findings.
    if landed_all:
        last_outcome = "landed"
    elif "pending" in tick_outcomes:
        last_outcome = "pending"
    else:
        last_outcome = "fail-closed"
    emit.patch_obj(eng, "architect_log_poll_recorded", job,
                   {"landed_all": landed_all, "last_outcome": last_outcome},
                   type=job.get("type"))
