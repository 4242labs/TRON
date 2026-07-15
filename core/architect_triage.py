"""core.architect_triage — block 01-38 T12 (behavior-preserving split of
`core/architect.py`): the `triage` job-kind (wave 18, GAP-E, architect-first
routing for ALL wall kinds). A raised wall/escalation (`worker.wall`, a
`sentry.cap` escalation, a liveness `worker.stalled` recovery — every
`core/casestate.py::open_case` caller — PLUS `core/classify.py`'s own
`unclassified` result) lands FIRST, never an immediate operator page.

THE ROOT INVARIANT THIS MODULE CARRIES — THE VERDICT WIRE (T12 binding: do
not alter its logic, only relocate it verbatim): `_advance_triage` orders
ONCE (`arch.triage`, a structured ask for a verdict ∈ `{scope_forward,
answer, operator}`), then waits for a routed `architect.triage_verdict`
report (`core/router.py`, recorded into `manifest["triage_verdicts"]`)
before applying it. This closed-vocabulary verdict handling is THE root of
every phantom-wall failure in this system's history — `core/
verdict_wire_rig.py` + `core/architect_rig.py` are the regression guards
that must stay green across this relocation. `_advance_triage`'s BODY below
is byte-for-byte the pre-split function; the only mechanical change is
routing facade-owned shared/patch-sensitive names (`_delivered`,
`_turn_settled`, `_advance_delivery`, `_reset_delivery_state`,
`_stamp_dispatch`, `RESPAWN_CAP`, `ARCHITECT_WID`, `_ensure_installed`)
through the live `architect` module OBJECT (`architect.<name>`, resolved at
CALL time) instead of a bare same-file name — required because `core/
architect_rig.py` monkeypatches several of those names directly on the
facade's own namespace (`architect._redeliver`, `architect.
_advance_delivery`, `architect.RESPAWN_CAP`, `architect.NO_PROGRESS_BUDGET`)
and the patch must still be honored from every call site, not just the
facade's own.

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
import vocab      # noqa: E402 — core/vocab.py, emit template-id constants
import landing    # noqa: E402 — core/landing.py, Wave-1's ONE landing primitive
import pipeline   # noqa: E402 — core/pipeline.py, stale_landing_wall (ADR-0008)
import casestate  # noqa: E402 — core/casestate.py, architect_resolve/open_operator_case
import emit       # noqa: E402 — core/emit.py, block 01-38 T7's single emit API
import architect  # noqa: E402 — core/architect.py, the facade (ARCHITECT_WID + delivery infra)
from architect_enqueue import _has_triage_job   # noqa: E402 — core/architect_enqueue.py
from architect_log import _adhoc_branch          # noqa: E402 — core/architect_log.py


def _next_triage_id(eng, manifest):
    """A deterministic, monotonically-numbered triage-job id — a manifest-
    persisted counter (`manifest["triage_seq"]`), never `uuid`/`random`
    (mirrors `core/casestate.py::next_case_id`'s own idiom). This is the
    correlation handle `manifest["triage_verdicts"]` is keyed by — NEVER
    `case_id`, which is legitimately `None` for a case-less triage job
    (`core/classify.py`'s unclassified path) and would otherwise collide
    across two independent case-less jobs raised over the life of one run."""
    n = int(manifest.get("triage_seq", 0)) + 1
    emit.put(eng, manifest, "architect_triage_seq_advanced", (), "triage_seq", n)
    return f"triage-{n}"


def enqueue_triage(eng, manifest, case_id, source, block, detail, worker_id=None,
                   wall_landing=False):
    """Wave 18 (GAP-E): a raised wall/escalation becomes a PMT-TRIAGE job
    FIRST — NEVER an immediate operator page. Called from `core/
    casestate.py::open_case` (case-bearing, `case_id` set — worker.wall/
    sentry.cap/liveness-stall) and `core/classify.py::_triage_unclassified`
    (case-less, `case_id=None`, `block=None` — raw free text). Idempotent
    for a case-bearing job only — see `_has_triage_job`'s own docstring.

    `wall_landing` (block 01-38 T19 W1, H1 structural fix): the ENGINE-
    OBSERVED flag `open_case` snapshots from the raising worker's own block
    gate stage at case-creation time (never a worker-declared label) —
    threaded onto the job here so `_advance_triage`'s stale-wall downgrade
    (below) can read it without a second manifest lookup. Defaults False —
    the block-less/case-less caller (`core/router.py::_route_wall`'s
    no-durable-block arm) has no gate to snapshot at all, so a block-less
    wall is NEVER treated as a landing wall (fail-safe: absent ⇒ not
    landing ⇒ pages)."""
    architect._ensure_installed(eng, manifest)
    # R1a (ADR-0005) final backstop: the architect can never be the SOURCE of a
    # triage — its own narration creates nothing. The call-site guards (classify /
    # router, ahead of open_case) are primary; this is defense-in-depth so no
    # future creation path can queue an architect-sourced triage. Its OWN in-flight
    # triage resolves via the R1b idle backstop, never by self-enqueue.
    if worker_id == architect.ARCHITECT_WID:
        eng.log("flow", "architect: enqueue_triage refused — sender is the architect "
                        "itself (R1a self-source backstop); created nothing")
        return
    if _has_triage_job(manifest, case_id):
        return
    triage_id = _next_triage_id(eng, manifest)
    job = {"kind": "triage", "triage_id": triage_id, "case_id": case_id,
          "source": source, "block": block, "detail": detail,
          "worker_id": worker_id, "wall_landing": wall_landing, "ordered": False,
          "verdict": None, "note": None, "adhoc": None, "resolved": False}
    emit.append(eng, manifest, "architect_triage_job_enqueued", ("architect_queue",),
               job, triage_id=triage_id, case_id=case_id, source=source, block=block)
    eng.log("flow", f"architect: PMT-TRIAGE queued (triage_id={triage_id!r}, "
                    f"case_id={case_id!r}, source={source!r}, "
                    f"block={block!r}) — architect-first, never an immediate "
                    f"operator page")


def _order_triage(eng, job):
    text = (f"[TRON]  architect — TRIAGE (triage_id={job['triage_id']!r}, "
           f"case_id={job.get('case_id')!r}, source={job.get('source')!r}, "
           f"block={job.get('block')!r}): {job.get('detail')}\nReply with a "
           f"structured architect.triage_verdict (triage_id="
           f"{job['triage_id']!r}, verdict in "
           f"scope_forward|answer|operator[, note]).")
    if not eng.dry:
        eng.emit(
            vocab.TPL_ARCH_TRIAGE, text,
            slots={"detail": job.get("detail"), "sender": job.get("source"),
                  "triage_id": job["triage_id"]},
            worker_id=architect.ARCHITECT_WID,
            kind="arch.triage")
    architect._stamp_dispatch(eng, job, text, "arch.triage", extra={"ordered": True})   # ADR-0009 R-B
    eng.log("flow", f"architect[triage:{job['triage_id']}]: ordered triage "
                    f"(source={job.get('source')!r}, dispatch_seq="
                    f"{job.get('dispatch_seq')!r})")


def _advance_triage(eng, manifest, job):
    """One triage-job step (GAP-E, wave 18) — see module docstring for the
    full order-then-observe-then-apply shape. Sets `job["resolved"] = True`
    (the ONE thing `advance`, below, reads to free the architect back to
    idle) only once the verdict's own effect has genuinely landed — a
    `scope_forward` verdict never resolves until its adhoc block is
    genuinely observed `"landed"` (real ancestry), never on a message
    alone."""
    import casestate   # lazy — casestate.py itself lazily imports this
                       # module (see its own module docstring); both are
                       # always fully loaded by the time either is CALLED

    if job.get("resolved"):
        # Idempotent: `advance` clears current_job the tick after resolved is set,
        # so the live engine never re-enters — but never re-apply a verdict (e.g.
        # re-page an operator case) if a caller ticks a resolved job again.
        return

    if not job.get("ordered"):
        _order_triage(eng, job)
        return

    if job.get("verdict") is None:
        verdicts = manifest.get("triage_verdicts") or {}
        v = verdicts.get(job["triage_id"])
        if v is None:
            # No structured verdict yet (R1b, ADR-0009 re-keyed onto R-D).
            # Arm only once the architect's order is genuinely DELIVERED
            # (`_turn_settled`: read_hwm >= dispatch_seq, held while
            # provably mid-turn) — never a wall-clock/idle-tick debounce.
            # While NOT yet delivered, drive the R-C/R-E/R-G recovery loop
            # (respawn/re-deliver/no-progress-budget) instead of just idling.
            if not architect._turn_settled(eng, job):
                if job.get("dispatch_seq") is not None and not architect._delivered(eng, job):
                    architect._advance_delivery(eng, manifest, job)
                return
            architect._reset_delivery_state(eng, job)   # R-G: genuine delivery flip — reset the budget
            # T10 (ADR-0012 §6(b), the guess-from-silence backstop DELETED):
            # under structured-only + the closed verdict wire (T9), a
            # genuinely completed architect turn always carries a real
            # `report.sh --tag verdict ...` reply — R1b's old idle-GUESS
            # (fabricating "operator"/"answer" from `job.get("source")`
            # alone) is now dead code by the design's own premise, and
            # worse, a content guess. A settled turn with NO structured
            # verdict is instead a genuine delivery gap: bounded RE-ORDER
            # (the SAME `RESPAWN_CAP` idiom R-C already uses for a stuck
            # DELIVERY, reused rather than a second cap), never a guess;
            # past the cap, the operator is paged LOUD (never fabricated
            # content) — "a truly-dead architect surfaces via the liveness
            # budget as a page" (supersedes the HANDOVER "R1b byte-for-byte"
            # note per ADR §6(b)).
            reorders = job.get("_verdict_reorders", 0) + 1
            emit.patch_obj(eng, "architect_triage_reorder_bumped", job,
                           {"_verdict_reorders": reorders}, triage_id=job["triage_id"])
            if reorders > architect.RESPAWN_CAP:
                note = (
                    f"architect's triage order (triage_id={job['triage_id']!r}) was "
                    f"DELIVERED and re-ordered {reorders} time(s) with NO structured "
                    f"architect.triage_verdict ever routed — never guessed; paged "
                    f"LOUD instead (T10)")
                emit.patch_obj(eng, "architect_triage_reorder_exhausted", job,
                               {"verdict": "operator", "note": note}, triage_id=job["triage_id"])
                eng.log("flow", f"architect[triage:{job['triage_id']}]: {job['note']}")
            else:
                eng.log("flow", f"architect[triage:{job['triage_id']}]: order "
                                f"DELIVERED with no structured verdict yet (re-order "
                                f"{reorders}/{architect.RESPAWN_CAP}) — re-ordering, never guessing")
                emit.patch_obj(eng, "architect_triage_reorder_retried", job,
                               {"ordered": False}, triage_id=job["triage_id"])
                _order_triage(eng, job)
                return
        else:
            architect._reset_delivery_state(eng, job)   # R-G: a routed report proves delivery too
            verdict = v.get("verdict")
            if verdict not in ("scope_forward", "answer", "operator"):
                eng.log("flow", f"architect[triage:{job['triage_id']}]: "
                                f"unrecognized verdict {verdict!r} — falling back "
                                f"to 'operator' (never silently dropped — the one "
                                f"safe default, still reaches a human)")
                verdict = "operator"
            emit.patch_obj(eng, "architect_triage_verdict_recorded", job,
                           {"verdict": verdict, "note": v.get("note")}, triage_id=job["triage_id"])

    # ADR-0008 — stale-wall revalidation (covers BOTH the R1b idle-backstop
    # operator verdict AND a structured `triage_verdict="operator"`: both set
    # verdict="operator" and converge here). A genuine LANDING worker.wall whose
    # block has already closed out on trunk is moot — revalidate against durable
    # trunk truth (the gate stage, which survives branch teardown) and retire it
    # benignly rather than paging the operator about a wall that no longer holds.
    # block 01-38 T19 W1 (H1 structural fix): "genuine LANDING" is read off
    # `job["wall_landing"]` — the engine-observed flag `open_case` snapshotted
    # at case-creation time — NEVER a substring sniff over `job["detail"]`'s
    # free text (a worker cannot mislabel a structural fact it never sets).
    if job["verdict"] == "operator" and pipeline.stale_landing_wall(
            manifest, job.get("source"), job.get("worker_id"), job.get("wall_landing")):
        stale_note = ("stale landing worker.wall — block closed on trunk; "
                      "operator NOT paged (ADR-0008)")
        emit.patch_obj(eng, "architect_triage_verdict_downgraded_stale", job,
                       {"verdict": "answer", "note": stale_note}, triage_id=job["triage_id"])
        eng.log("flow", f"architect[triage:{job['triage_id']}]: STALE landing worker.wall "
                        f"revalidated (worker={job.get('worker_id')!r} block CLOSED on "
                        f"trunk) — downgraded operator->answer, operator NOT paged (ADR-0008)")

    if job["verdict"] in ("answer", "operator"):
        if job.get("case_id") is not None:
            casestate.architect_resolve(eng, manifest, job["case_id"], job["verdict"],
                                        note=job.get("note"))
        elif job["verdict"] == "operator":
            casestate.open_operator_case(eng, manifest, job.get("block"),
                                         job.get("source"), job.get("detail"),
                                         worker_id=job.get("worker_id"))
        elif job.get("worker_id") and not eng.dry:
            eng._to_worker(
                job["worker_id"],
                job.get("note") or f"[TRON]  architect answer on triage "
                                   f"({job.get('source')}): see guidance.",
                "architect.answer")
        emit.patch_obj(eng, "architect_triage_resolved", job, {"resolved": True},
                       triage_id=job["triage_id"])
        eng.log("flow", f"architect[triage:{job['triage_id']}]: verdict "
                        f"{job['verdict']!r} applied — job done")
        return

    # scope_forward — author + land ONE real adhoc block, THEN resolve the
    # original case (if any) — never before the adhoc genuinely lands.
    entry = job.get("adhoc")
    if entry is None:
        seq = manifest.get("adhoc_seq") or {}
        n = int(seq.get("triage", 0)) + 1
        emit.put(eng, manifest, "architect_adhoc_seq_advanced", ("adhoc_seq",), "triage", n)
        adhoc_id = f"adhoc-triage-{n}"
        entry = {"block": adhoc_id, "branch": _adhoc_branch(adhoc_id),
                 "finding": job.get("detail"), "case_id": None, "landed": False,
                 "ordered": False}
        emit.patch_obj(eng, "architect_triage_adhoc_created", job, {"adhoc": entry},
                       triage_id=job["triage_id"])

    if not entry["ordered"]:
        text = (f"[TRON]  architect — scope_forward on triage "
               f"(triage_id={job['triage_id']!r}): author + land ONE "
               f"upcoming adhoc block ({entry['block']}, meta/blocks/"
               f"{entry['block']}.md, Status: 📋 To do, plus its "
               f"pipeline.md row) — I land it once it resolves, then "
               f"resolve the original wall/escalation.")
        if not eng.dry:
            eng._to_worker(architect.ARCHITECT_WID, text, "arch.log-review")
        # R-B: `entry` is its OWN order-requiring sub-state, a fresh dict
        # separate from `job`'s own `dispatch_seq` namespace — stamping it
        # here satisfies "NULLED on every transition" by construction (a
        # freshly-created dict already starts `dispatch_seq=None`).
        architect._stamp_dispatch(eng, entry, text, "arch.log-review", extra={"ordered": True})
        eng.log("flow", f"architect[triage:{job['triage_id']}]: ordered "
                        f"adhoc {entry['block']!r} (dispatch_seq="
                        f"{entry.get('dispatch_seq')!r})")
        return

    truth_ref = eng._truth_ref()
    patch_id = gitobs.patch_id(eng.paths["root"], entry["branch"], truth_ref, eng.dry)
    # Content-bound to the CURRENT patch-id, never a stale cached id (T2-17 fix;
    # single-source in landing.stage_case_id, shared with core/gate.py).
    land_case_id = landing.stage_case_id(entry.get("case_id"), "triage-forward",
                                         entry["branch"], patch_id)
    emit.patch_obj(eng, "architect_triage_adhoc_case_bound", entry,
                   {"case_id": land_case_id}, triage_id=job["triage_id"])

    outcome = landing.land_via_grant(eng, land_case_id, entry["block"], entry["branch"],
                                     architect.ARCHITECT_WID, "arch.log-review",
                                     "architect-triage-forward")
    if outcome == "landed":
        emit.patch_obj(eng, "architect_triage_adhoc_landed", entry, {"landed": True},
                       triage_id=job["triage_id"])
        eng.log("flow", f"architect[triage:{job['triage_id']}]: adhoc "
                        f"{entry['block']!r} landed — resolving the original "
                        f"wall/escalation (never paging the operator)")
        if job.get("case_id") is not None:
            casestate.architect_resolve(eng, manifest, job["case_id"],
                                        "scope_forward", note=job.get("note"))
        emit.patch_obj(eng, "architect_triage_resolved", job, {"resolved": True},
                       triage_id=job["triage_id"])
    elif outcome == "pending":
        eng.log("flow", f"architect[triage:{job['triage_id']}]: grant live "
                        f"for {land_case_id}, awaiting land.sh")
    else:
        eng.log("flow", f"architect[triage:{job['triage_id']}]: {outcome} "
                        f"(case {land_case_id}, branch not authored yet?)")
