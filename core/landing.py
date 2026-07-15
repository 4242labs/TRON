"""core.landing — ADR-0004 rewrite, brick 1: the ONE landing primitive, re-cut
with CONTENT-BOUND case-id identity.

CONFIRMED ROOT (engine/land_paperwork_rig.py, real-git, committed on
feat/l1-harness-landing-fix): the old primitive (`engine/land.py::land_via_grant`)
keys a paperwork case-id PURELY off role + branch name
(`paperwork-<role>-<branch>`, fsm.py's `_drain_landings`). When the SAME branch
is re-enqueued with NEW content (a later reconcile/forward re-authors it — a
different patch-id), the deterministic case-id collides with the ALREADY-
CONSUMED grant from the FIRST landing:

  - `land.py` (land.py:121-122) checks `grants.read_consumed(case_id)` FIRST,
    before anything else, and short-circuits `"landed"` on a hit — never
    re-deriving the branch's CURRENT patch-id, never even looking at content.
  - `land.sh` (~line 86) has the identical shape: `consumed/<case_id>.grant`
    exists -> "already consumed ... exit 0", checked BEFORE the live grant
    file or the branch's patch-id are read at all.

Net effect: the Nth re-authoring of a same-named branch is reported LANDED —
a false `docs_landed` fires — while its content never reaches trunk. Silent
loss, not a wedge; the worst shape a landing primitive can take.

THE FIX (this module): landing identity is CONTENT-BOUND — ONE invariant,
constructed at one place and enforced at one place:

  - CONSTRUCTED by `paperwork_case_id` below: the case-id embeds the branch's
    patch-id, so new content -> new case-id -> a receipt from stale content
    can never even be LOOKED UP under the new case-id in the first place.
    This also means `land.sh` (UNCHANGED, a respected contract) never sees a
    stale consumed receipt for genuinely new content, because the case-id
    it's invoked with is itself new.

  - ENFORCED at the single landing seam, `land_via_grant` below, regardless
    of what case-id scheme a caller uses: before trusting a consumed receipt
    found under `case_id`, re-derive the branch's CURRENT patch-id and
    compare it to the receipt's own `patch_id` field. A receipt only
    short-circuits `"landed"` when its content still matches what's on the
    branch RIGHT NOW (or when the branch's current content is unresolvable —
    e.g. a since-deleted branch post-land, the one case a live ancestry read
    can no longer see at all, where the receipt is the ONLY surviving proof
    and must still be trusted). A receipt whose patch-id has diverged is
    STALE for this content: never short-circuit on it — fall through to
    observe/mint/order exactly as if no receipt existed, so the new content
    gets a real grant and a real land.

  This is one invariant, not a hedge: construction makes the stale-receipt
  path structurally unreachable for a well-behaved caller (this module's own
  `gate.py` caller included); enforcement is the SAME invariant's single
  checkpoint, so even a caller that (mis)reuses a colliding case-id can never
  have unlanded content masked by an old receipt. There is exactly one
  content-bound-identity mechanism here, expressed twice — construct, then
  enforce — never two independent mechanisms.

Otherwise this ports `engine/land.py::land_via_grant`'s sequence faithfully:
observe-first (real ancestry), patch-id fail-closed (`grants.mint`'s own
contract), mint-or-reuse (reuse only when the live grant's patch-id matches
current content), order the worker only on a fresh mint (never re-spam an
unchanged live grant), observe-and-consume.

Duck-types the engine context exactly like `land.py` does: `eng.paths`,
`eng.dry`, `eng.ctx.grants_dir`, `eng.events`, `eng.log`, `eng._truth_ref()`,
`eng._to_worker`, `eng._grant_ttl()`. Trunk reads (`tip_sha`, `patch_id`,
`is_ancestor`) go through `core.gitobs` — the new stack's single
git-observation seam — never a direct `import trunk` here. Reuses `grants.py`
as-is (imported, never forked; a clean library, not git observation — may be
vendored into `core/` in a later pass) — a respected contract this module
does not and must not modify.
"""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import grants   # noqa: E402  — respected contract, imported as-is (never forked)
import gitobs   # noqa: E402  — core/gitobs.py, the ONE git-observation seam
import emit      # noqa: E402  — core/emit.py, block 01-38 T7's single emit API (the forensic event)

# Mirrors grants.CASE_ID_TOKEN's safe-token alphabet (land.sh's own
# pre-interpolation guard) — used here only to SANITIZE a branch name into a
# case-id component, never to relax the contract grants.py/land.sh already
# enforce on the case-id as a whole.
_UNSAFE_TOKEN_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def paperwork_case_id(role, branch, patch_id):
    """The content-binding fix, in one function: a paperwork case-id that
    embeds the branch's CURRENT patch-id, so a same-named branch re-authored
    with new content derives a DIFFERENT case-id — a stale receipt from the
    old content can never even be looked up under the new one.

    `"paperwork-{role}-{sanitized_branch}-{patch_id[:12]}"` — branch is
    sanitized to the safe-token alphabet `[A-Za-z0-9._-]+` (grants.py's
    `CASE_ID_TOKEN` / land.sh's own guard), 12 hex chars of patch-id is ample
    collision resistance for a single project's paperwork lane while keeping
    the case-id readable. `patch_id` unresolvable (`""`) still produces a
    (fail-closed-downstream) case-id — `grants.mint` itself refuses to mint
    against an empty patch-id, so this never becomes a false pass; it just
    means the caller gets a stable "no content yet" case-id rather than this
    helper raising."""
    safe_branch = _UNSAFE_TOKEN_CHARS.sub("-", branch or "")
    return f"paperwork-{role}-{safe_branch}-{(patch_id or '')[:12]}"


def stage_case_id(prev, role, branch, patch_id):
    """The ONE place a landing caller resolves its per-stage grant case-id
    (T2-17 fix, single-source for all six `land_via_grant` callers — gate.py's
    merge/record/close arms and architect.py's triage-forward/forward/logreview
    lanes). Content-binds to the branch's CURRENT patch-id whenever it resolves
    (a genuine re-authoring -> a FRESH case-id; a pure rebase preserves the
    patch-id -> the SAME case-id, stable across churn). ONLY when the patch-id
    is momentarily UNRESOLVABLE (`""` — the branch already fully landed so its
    diff is empty, or a mid-churn read) does it keep the caller's last-good
    `prev` id rather than overwrite it with a malformed empty-suffix id.

    Why this exists: callers used to compute `prev or paperwork_case_id(...)`,
    which CACHED the id UNCONDITIONALLY — pinning it to the FIRST landing's
    patch-id. A re-authored branch (a follow-up commit) then reused that stale,
    already-consumed case-id, and the worker's `land.sh` already-consumed check
    (keyed on case-id alone) no-op'd the new commit -> trunk stuck -> wall ->
    stall -> operator escalation (the T2-17 REJECT). Binding to the current
    patch-id restores the content-bound invariant `land_via_grant` documents as
    "the invariant's one enforcement point". `prev` may be `None` (first call).
    """
    if patch_id:
        return paperwork_case_id(role, branch, patch_id)
    return prev or paperwork_case_id(role, branch, patch_id)


def _mint_or_reuse_grant(eng, case_id, block, branch, patch_id):
    """Ported verbatim from `land.py::_mint_or_reuse_grant` (private to this
    module, same contract): a LIVE grant whose patch-id already matches this
    branch's CURRENT content is reused untouched; anything else (missing,
    expired, or content-changed) gets a fresh grant. Fail-closed on
    `patch_id == ""` or an off-alphabet case-id — `grants.mint`'s own
    contract. Returns `(grant_or_None, freshly_minted)`."""
    if not case_id or not patch_id:
        return None, False
    live = grants.read_live(eng.ctx.grants_dir, case_id)
    if live and live.get("patch_id") == patch_id:
        return live, False
    g = grants.mint(eng.ctx.grants_dir, case_id, block, branch, patch_id,
                    ttl_min=eng._grant_ttl())
    if g:
        emit.record(eng, "grant_minted", block=block, case=case_id,
                    branch=branch, patch_id=patch_id)
        eng.log("flow", f"grant[{case_id}] minted for {block} ({branch} "
                        f"@ patch-id {patch_id[:12]})")
    return g, bool(g)


def _order_land(eng, wid, block, case_id, branch, kind="gate.land"):
    """Ported verbatim from `land.py::_order_land`: order the responsible
    agent to run the scaffold's `land.sh` — the ONLY sanctioned way trunk
    advances (ADR-0002 D2). Engine-composed, dry-safe."""
    if not wid or eng.dry:
        return
    eng._to_worker(wid, f"[TRON]  {wid} — grant approved (case {case_id}): run "
                        f"`meta/scripts/land.sh {case_id}` to land {branch} onto "
                        f"trunk yourself. I observe trunk and pick it up the "
                        f"moment it lands — no separate report needed.", kind)


def _observe_landed(eng, branch, truth_ref):
    """Ported verbatim from `land.py::_observe_landed`: has `branch`'s tip
    already reached trunk? Committed-ref read only, never working-tree/say-so.
    T19 live-finding fix: in live (non-dry) mode, an unresolvable tip (branch
    never authored / already gone with no receipt) is NEVER treated as
    landed — `is_ancestor("")`'s `True` is a dry-mode vacuous-truth
    convenience, not a real observation; see the guard below."""
    tip = gitobs.tip_sha(eng.paths["root"], branch, eng.dry)
    if not eng.dry and not tip:
        return False   # unresolvable branch tip (never authored / gone with no
                       # receipt): is_ancestor("") is a DRY-mode vacuous truth,
                       # NEVER a real landing. A since-deleted-post-land branch
                       # is caught upstream by the consumed-receipt arm (land_via_grant).
    return gitobs.is_ancestor(eng.paths["root"], tip, truth_ref, eng.dry)


def _consume_grant_administratively(eng, case_id, result="engine-observed"):
    """Ported verbatim from `land.py::_consume_grant_administratively`: the
    crash-window arm — a live grant whose landing the ENGINE observed is
    consumed here, idempotent, a write strictly inside TRON's own grants dir."""
    if eng.dry or not case_id:
        return
    grants.consume(eng.ctx.grants_dir, case_id, result=result)


def land_via_grant(eng, case_id, block, branch, wid, kind, scope):
    """The ONE landing sequence — CORRECTED per the confirmed root above.
    `eng` is the live Engine (duck-typed, see module docstring).

    Returns one of:
      "landed"      observed landed — freshly consumed this call, or an
                    already-consumed receipt was on file WHOSE PATCH-ID
                    STILL MATCHES the branch's current content (or whose
                    content is unresolvable, e.g. a since-deleted branch —
                    the receipt is the only surviving proof there).
      "pending"     a grant is live (freshly minted or reused unchanged) and
                    the worker has been ordered (once, on the mint); not yet
                    observed landed. The caller re-evaluates on a later tick.
      "fail-closed" the branch's patch-id is unresolvable ("") or the
                    case-id falls outside land.sh's safe-token alphabet — no
                    grant minted (`grants.mint`'s own fail-closed rider).

    Never decides WHETHER content is safe to land — that precondition is the
    caller's, exactly as in `land.py`."""
    if not case_id or not branch:
        return "fail-closed"
    truth_ref = eng._truth_ref()

    # THE FIX, enforced (the same content-bound-identity invariant
    # `paperwork_case_id` CONSTRUCTS — see module docstring — makes this arm
    # structurally unreachable for a caller that content-binds its own
    # case-ids, but this is the invariant's one enforcement point, so the
    # primitive stays honest even if a caller doesn't): a consumed receipt is
    # trusted ONLY when its patch_id still matches the branch's CURRENT
    # content, or when current content is unresolvable (a since-deleted
    # branch — the receipt is the only proof left, same rationale land.py's
    # original short-circuit relied on). A receipt whose patch-id has
    # DIVERGED is stale for this content and must never mask it — fall
    # through to observe/mint/order for the real thing.
    consumed = grants.read_consumed(eng.ctx.grants_dir, case_id)
    if consumed:
        cur_pid_for_receipt = gitobs.patch_id(eng.paths["root"], branch, truth_ref, eng.dry)
        if not cur_pid_for_receipt or consumed.get("patch_id") == cur_pid_for_receipt:
            return "landed"
        eng.log("flow", f"land[{case_id}] {scope}: consumed receipt is STALE for "
                        f"current content (receipt patch_id="
                        f"{(consumed.get('patch_id') or '')[:12]} != branch's current "
                        f"{cur_pid_for_receipt[:12]}) — NOT short-circuiting; falling "
                        f"through as if unlanded (confirmed root: land.py:121-122 / "
                        f"land.sh's identical consumed-receipt arm)")

    if _observe_landed(eng, branch, truth_ref):
        if not consumed and not grants.read_live(eng.ctx.grants_dir, case_id):
            _report_grantless_land(eng, case_id, block, branch, scope)
        _consume_grant_administratively(eng, case_id)
        eng.log("flow", f"land[{case_id}] {scope}: observed landed -> consumed")
        return "landed"

    pid = gitobs.patch_id(eng.paths["root"], branch, truth_ref, eng.dry)
    grant, fresh = _mint_or_reuse_grant(eng, case_id, block, branch, pid)
    if not grant:
        if not eng.dry:
            eng.log("flow", f"land[{case_id}] {scope}: unresolvable patch-id — "
                            f"no grant minted (fail-closed)")
        return "fail-closed"
    if fresh:
        _order_land(eng, wid, block, case_id, branch, kind=kind or "gate.land")
    if _observe_landed(eng, branch, truth_ref):
        _consume_grant_administratively(eng, case_id)
        eng.log("flow", f"land[{case_id}] {scope}: landed same-tick -> consumed")
        return "landed"
    return "pending"


def _report_grantless_land(eng, case_id, block, branch, scope):
    """T22 (block 01-38, AC-18) — grantless-land detection, confirmed ABSENT
    from `core/*` (fsm.py's own elaborate `_drive_gate` bypass-check arm was
    never ported) and re-expressed here MINIMAL, at the ONE seam every
    landing already goes through: this exact content-bound `case_id`'s
    FIRST-EVER observation already reads "landed" on trunk with NEITHER a
    consumed receipt NOR a live grant EVER on file for it. Since
    `paperwork_case_id`/`stage_case_id` bind identity to the branch's OWN
    CURRENT patch-id (this module's own root fix), a genuine prior/later
    landing of DIFFERENT content for the same role/branch would carry a
    DIFFERENT case-id — this is the structural signature of an out-of-band
    bypass (a worker running raw git instead of `meta/scripts/land.sh`,
    ADR-0002 D2), never a legitimate route this primitive itself took.

    Counted unconditionally (must-be-zero, R4 — `core/counters.py`'s
    `grantless_land_detected`, the SAME surfacing mechanism every other
    must-be-zero backstop uses: acceptance REJECTS the run by this exact
    name, never a silent absorb into an ordinary "landed" outcome).
    Deliberately does NOT ALSO open an architect-first case here: this
    function runs from deep inside `gate.advance`'s own merge/record/close
    stage functions, mid-transition — mutating `gate_state["stage"]` from
    here would race the stage function's OWN imminent write to that exact
    field (e.g. `_advance_merge`'s `"stage": STAGE_TRUNK` a few lines after
    this returns), clobbering whichever write lands second. The counter is
    the safe, non-mutating surfacing path; a future task that wants this to
    ALSO park the block architect-first should thread the signal back
    THROUGH the calling stage function's own `emit.patch_obj`, never mutate
    `gate_state` from two places in the same call."""
    eng.log("flow", f"land[{case_id}] {scope}: GRANTLESS LAND — {block!r} on "
                    f"{branch!r} is already on trunk with NO consumed receipt "
                    f"and NO live grant ever on file for this content-bound "
                    f"case-id — an out-of-band bypass (ADR-0002 D2 violation), "
                    f"counted (must-be-zero, R4); acceptance rejects the run by "
                    f"this exact counter name")
    emit.record(eng, "must_be_zero", counter="grantless_land_detected",
               case_id=case_id, block=block, branch=branch, scope=scope)


def _find_open_pseudo_case(manifest, block):
    """The `(case_id, case)` of the OPEN (still-undecided) case parked
    against a block-less/synthetic pseudo-block id, or `(None, None)` when
    none is open — the same "at most one open case per block id" premise
    `casestate.open_case`'s own idempotent guard already establishes,
    just read here rather than re-derived."""
    for cid, c in (manifest.get("cases") or {}).items():
        if c.get("block") == block and c.get("decision") is None:
            return cid, c
    return None, None


def check_root_detached(eng, manifest):
    """T22 (block 01-38, AC-18) — 01-32's ADR-0002 D1 detection arm,
    confirmed ABSENT from `core/*` (fsm.py-only: `_check_root_detached`) and
    ported here MINIMAL, never copied: a local no-remote-mode root must stay
    DETACHED (never re-attached to a branch) so the trunk ref can advance by
    `update-ref` CAS with no working-tree race — `land.sh`'s own
    `require_detached` refusal is the structural write-time backstop; this
    is the ACTIVE per-tick READ (`core/tick.py` calls this once per tick,
    early — before `route`/`act`, so a re-attach is caught even on a tick
    that attempts no landing at all) that catches a re-attach and routes it
    the SAME way any other violation is routed. Remote-mode roots are never
    required to detach (the cost scopes to local no-remote mode only,
    mirrors `core/gitobs.py::refresh`'s own remote-mode no-op); `eng.dry`
    is a genuine no-op too (nothing to violate).

    Reuses the EXISTING architect-first case machinery
    (`casestate.open_case`, lazily imported — `core/gate.py` imports THIS
    module, so a module-level `import casestate` here would cycle back
    through `casestate -> gate -> landing`; deferred exactly like
    `casestate.py`'s own documented `import architect`), never a new
    escalation mechanism: a block-less, worker-less pseudo-case
    (`block="root-reattach"`, `source="root.reattached"` — the SAME
    `open_case` idempotent-per-block guard means a second call while still
    attached is a genuine no-op, never a duplicate case). Self-heals in the
    F-1 spirit: once detachment is restored, an OPEN case still
    architect-owned (never yet delivered to the operator — T21's own
    no-take-back rule extends here too, deliberately) is resolved via
    `casestate.architect_resolve`'s existing `"answer"` verdict — no bespoke
    close path of this module's own."""
    remote = eng.paths.get("remote") or "none"
    if eng.dry or remote not in ("none", ""):
        return
    import casestate   # lazy — see docstring above for the cycle this avoids

    pseudo_block = "root-reattach"
    existing_id, existing = _find_open_pseudo_case(manifest, pseudo_block)
    attached = not gitobs.root_head_detached(eng.paths["root"], eng.dry)

    if attached:
        if existing_id is not None:
            return   # idempotent — already an open case, never a duplicate
        casestate.open_case(
            eng, manifest, pseudo_block, "root.reattached",
            "the project root is checked out on a branch again — ADR-0002 "
            "D1 violation: the local-mode root must stay detached so the "
            "trunk ref can advance by update-ref CAS with no working-tree "
            "race; landing holds until detachment is restored",
            worker_id=None)
        return

    if existing_id is not None and existing.get("owner") == "architect":
        casestate.architect_resolve(
            eng, manifest, existing_id, "answer",
            note="root-reattach self-healed — detachment restored")
