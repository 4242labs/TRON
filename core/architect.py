"""core.architect — the persistent, POOL-EXCLUDED architect (blueprint-
contracts.md §1 "Architect"; rebuild-spec.md C6/D1 + T5's `architect.
reconciled` -> `block:<block>:reconciled`). Drains a FIFO `manifest[
"architect_queue"]` at most ONE job per tick, in two job-kinds:

  `forward`   — author a MISSING upcoming block file (an in-scope roadmap
              row with no block file yet). The architect writes the block
              doc on its OWN `arch/<block>-forward` branch and lands it via
              `core.landing.land_via_grant` under a CONTENT-BOUND case-id
              (`role="forward"` — distinct from gate.py's `merge`/`record`
              roles for the SAME branch-naming convention, so the three can
              never collide on each other's receipts). Once landed, the
              block file is on trunk and the block becomes dispatchable
              normally — no bookkeeping of this module's own is needed past
              that point.

  `reconcile` (M-05) — a block landing `✅` enqueues a reconcile for the
              NEXT in-scope, not-yet-dispatched block (by pipeline order);
              that block's dispatch is GATED until the reconcile completes.
              This module never re-checks real content in this brick (no
              LLM here — see the module's own read-first list, which skips
              log-review/triage) — it ORDERS the reconcile (a structured
              `arch.reconcile` message) and waits for a structured
              `architect.reconciled` report to come back through `core/
              router.py` (the SAME two-step "order then observe a report"
              discipline `core/gate.py`'s own stages already use — the
              report is drained+routed on a LATER tick, never trusted
              same-call). `core/router.py` records the completion into
              `manifest["reconciled"]`; THIS module only clears its own
              `current_job` (frees the architect to pop its next job) once
              it observes that.

Persistent + pool-excluded (blueprint's own words): modeled ENTIRELY in
`manifest["architect"]` (status/current_job) + `manifest["architect_queue"]`
(the FIFO) — NEVER a `manifest["workers"]` entry, so `core/switchboard.py`'s
`_active_worker_count`/`core/pipeline.py::in_flight_blocks` (both keyed off
`manifest["workers"]`/`manifest["gates"]`) never count it toward a worker
slot. `eng._spawn_architect()` — a NEW stubbed hook, called exactly ONCE,
lazily, the first tick this module actually needs to pop a job (never
called at all by a caller whose architect_queue stays empty its whole run —
see `core/architect_rig.py`'s docstring for why the other 8 rigs' `eng`
stand-ins never need to implement it).

Wire (`core/tick.py`, two calls straddling `core/switchboard.py::fill`):
  `enqueue(eng, manifest, view, landed_blocks)` — called BEFORE fill(),
  same tick as a block's `record_landed` outcome: creates a fresh gate (or a
  fresh forward job) the SAME tick it's warranted, so `gated_blocks` below
  (read by `core/tick.py` to build fill()'s excluded-block set) reflects it
  immediately — a fresh gate excludes same-tick, never a tick late.

  `advance(eng, manifest)` — called AFTER fill(): progresses whatever job
  is current by exactly one step, and is the ONE place a completed
  reconcile job's `current_job` gets cleared (freeing the block for
  dispatch). Running this AFTER fill() (not before) is deliberate, not
  incidental: `core/router.py` may have just recorded a block's
  `manifest["reconciled"]` entry THIS SAME tick's `route()` (which runs
  BEFORE fill()) — clearing `current_job` immediately would let fill(),
  later in this SAME tick, dispatch the block the INSTANT its report
  drains, collapsing `reconciled_tick == spawn_tick`. Positioning the clear
  AFTER fill() instead means a block stays gated (`gated_blocks` still
  reports it, since `current_job` hasn't been cleared yet) through the
  WHOLE tick its `architect.reconciled` report is routed, and only becomes
  dispatchable starting the NEXT tick — `core/architect_rig.py`'s own
  ordering proof (`spawn_tick > reconciled_tick > done_tick`, all STRICT)
  is exactly this.

`gated_blocks(manifest)` — read by `core/tick.py` right before calling
`switchboard.fill` (unioned with `core/casestate.py::dispatch_excluded_
blocks`, the SAME "hand fill() a filtered dispatch view" mechanism wave 8
already established): every block with an outstanding (queued OR current)
reconcile job. `forward` jobs need no such exclusion — their target block
has no block file yet, so `core/pipeline.py::dispatchable` (which requires
`has_block_file`) already excludes it structurally; nothing more to do here.

Dedupe throughout (`_enqueue_forward_jobs`/`_enqueue_reconcile`): never a
second job for a block already queued/current; a reconcile is never
re-enqueued for a block already in `manifest["reconciled"]`; forward-looking
only — `_next_reconcile_target` walks living-doc order STRICTLY AFTER the
just-landed block and skips anything abandoned (`core/casestate.py`),
parked (an open case), or already in-flight (`core/pipeline.py::
in_flight_blocks`) — never reopens a done block, never re-targets one
already mid-drive.

Wave 18 (GAP-E, architect-first routing for ALL wall kinds): a FOURTH job
kind, `triage` (PMT-TRIAGE) — the ONE place a raised wall/escalation
(`worker.wall`, a `sentry.cap` escalation, a liveness `worker.stalled`
recovery — every `core/casestate.py::open_case` caller — PLUS `core/
classify.py`'s own `unclassified` result) lands FIRST, never an immediate
operator page. `enqueue_triage` is called from TWO places: `core/
casestate.py::open_case` (a real casestate case behind it, `case_id` set)
and `core/classify.py::_triage_unclassified` (case-less — raw free text
with no block/gate to park, `case_id=None`). One job of triage throughput
per tick, same FIFO discipline as `forward`/`reconcile`/`log`.
`_advance_triage` orders ONCE (`arch.triage`, a structured ask for a
verdict ∈ `{scope_forward, answer, operator}`), then waits for a routed
`architect.triage_verdict` report (`core/router.py`, recorded into
`manifest["triage_verdicts"]` — the SAME two-step "order then observe a
report" discipline `reconcile`'s own `architect.reconciled` already uses,
drained on a LATER tick, never trusted same-call) before applying it:
`answer`/`operator` resolve in ONE step via `core.casestate.
architect_resolve` (case-bearing) or directly (case-less: `answer` relays a
note, `operator` mints via `core.casestate.open_operator_case`) —
`scope_forward` ADDITIONALLY authors + lands ONE real adhoc block first
(mirrors `_advance_log`'s own single-entry order-then-poll-and-land shape,
reusing the Wave-1 landing primitive verbatim) before resolving the
original case, if any — the wall/escalation only clears once the
forward-looking work has genuinely landed on trunk. An unrecognized verdict
falls back to `operator` — never silently dropped, the one safe default:
it still reaches a human, just via the loudest channel.

No raw git of any kind here — `core.gitobs` (the ONE seam) for the forward
job's patch-id read, `core.landing.land_via_grant`/`.paperwork_case_id`
(Wave-1's ONE landing primitive, imported and reused verbatim, never
forked) for the forward job's content-bound land. A plain manifest mutation
otherwise, the same "gates is a direct alias onto the manifest" idiom every
other `core/*.py` module already uses.

═══════════════════════════════════════════════════════════════════════
T12 SPLIT (block 01-38): this module is now a FACADE over per-job-kind
sibling modules — behavior-preserving, `test:<coordinator_split>`. It was
~1199 lines; the six job-kinds' own leaf logic moved out to:
  `core/architect_enqueue.py`   — the `forward`-job clear-ahead scan + the
                                   three cross-job-kind dedupe reads
                                   (`_has_forward_job`/`_has_triage_job`/
                                   `_has_reconcile_job`).
  `core/architect_forward.py`   — the `forward` job-kind (`_forward_branch`,
                                   `_advance_forward`).
  `core/architect_reconcile.py` — the `reconcile` job-kind's order half
                                   (`_next_reconcile_target`,
                                   `_enqueue_reconcile`, `_order_reconcile`
                                   — its COMPLETION half stays here, in
                                   `advance`, exactly where it already lived
                                   pre-split: reconcile never had its own
                                   `_advance_reconcile`).
  `core/architect_log.py`       — the `log` job-kind (`enqueue_log_review`,
                                   `_advance_log`, `_adhoc_branch`).
  `core/architect_triage.py`    — the `triage` job-kind (`enqueue_triage`,
                                   `_order_triage`, `_advance_triage`,
                                   `_next_triage_id`) — carries THE VERDICT
                                   WIRE (see that module's own docstring);
                                   its logic is RELOCATED VERBATIM, never
                                   altered.
  `core/architect_backstop.py`  — the ONE backstop part
                                   (`_backstop_refused_authoring`, ADR-0006
                                   R1d), now routed through the counter
                                   partition (T9) as the first real
                                   `may_fire`-class production member.

THIS FILE keeps: the public entrypoints every importer resolves as
`architect.<name>` (`ARCHITECT_WID`, `new_state`, `gated_blocks`, `enqueue`,
`enqueue_triage`, `enqueue_log_review`, `advance`, plus the tunable
constants `RESPAWN_CAP`/`REDELIVER_AFTER`/`NO_PROGRESS_BUDGET` — the last
two re-exported from their sibling modules only where genuinely leaf-owned;
see below) — PLUS the ADR-0009 delivery machinery (`_delivered`,
`_turn_settled`, `_stamp_dispatch`, `_clock`, `_redeliver`,
`_advance_delivery`, `_reset_delivery_state`) and the two tunables that
gate it (`RESPAWN_CAP`, `NO_PROGRESS_BUDGET`; `REDELIVER_AFTER` alongside
them for cohesion). This is a DELIBERATE deviation from a literal 7-way
split: the delivery machinery is cross-cutting (called from the dispatcher
itself AND from `architect_triage.py`), never itself one of the module's
named job-kinds, and — load-bearing for behavior-preservation —
`core/architect_rig.py`'s mutation-proof rigs monkeypatch
`architect._redeliver`, `architect._advance_delivery`, `architect.
RESPAWN_CAP`, `architect.NO_PROGRESS_BUDGET` DIRECTLY on this module's own
namespace (`architect.<name> = mock`, restored in `finally`). Python
resolves a bare-name call against the DEFINING module's own globals dict at
CALL time (never a value/reference frozen at another module's import time),
so a patch on `architect.<name>` is honored by every caller **in this same
file** for free; a sibling module reads these same names via the live
`architect` module OBJECT at call time (`architect.<name>`, never a
`from architect import <name>` copy) for the identical reason — see `core/
architect_triage.py`'s own docstring. Keeping the whole delivery cluster
physically here, rather than splitting it into an 8th sibling, removes the
ONLY place this split could have silently broken those mutation proofs.
Every other job-kind's leaf function is never itself monkeypatched (only
called) and was safe to relocate as a plain re-export.

`advance()` remains the ONE dispatcher tying every job-kind together —
exactly as it did pre-split ("architect-count... a single persistent
architect in this brick").
═══════════════════════════════════════════════════════════════════════
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

import vocab      # noqa: E402 — core/vocab.py, emit template-id constants (T7's own _send_flag_digest)
import landing    # noqa: E402 — core/landing.py — kept importable as `architect.landing` for
                  # `core/architect_rig.py`'s own `architect.landing.land_via_grant` monkeypatch,
                  # even though this file's own remaining code never calls it directly post-split
                  # (the forward/log/triage job-kinds own the real land_via_grant call sites now).
import casestate  # noqa: E402 — core/casestate.py, open_operator_case (R-G no-progress budget)
import liveness   # noqa: E402 — core/liveness.py, working_excluded_integrate (R-G) — kept importable
                  # as `architect.liveness` for the SAME monkeypatch-compatibility reason as `landing`.
import emit       # noqa: E402 — core/emit.py, block 01-38 T7's single emit API

ARCHITECT_WID = "architect"

# Mirrors core/session.py's own IN_SCOPE_STATUSES verbatim (never forked into
# a second constant this module could silently drift from).
IN_SCOPE_STATUSES = ("to-do", "in-progress")

# T12: the job-kind sibling modules (see the SPLIT section of this module's
# own docstring above). Imported AFTER the constants above so a sibling's own
# `import architect` + `architect.IN_SCOPE_STATUSES`/`architect.ARCHITECT_WID`
# read (deferred to CALL time, never at either module's IMPORT time) resolves
# even mid-circular-import.
from architect_enqueue import _enqueue_forward_jobs                    # noqa: E402,F401
from architect_forward import _forward_branch, _advance_forward        # noqa: E402,F401
from architect_reconcile import _enqueue_reconcile, _order_reconcile   # noqa: E402
from architect_triage import enqueue_triage, _order_triage, _advance_triage   # noqa: E402,F401
from architect_log import enqueue_log_review, _advance_log             # noqa: E402,F401
from architect_backstop import _backstop_refused_authoring             # noqa: E402

# Re-exported ONLY so `architect.<name>` keeps resolving for external callers
# (`core/architect_rig.py` calls `architect._order_triage`/`architect.
# _forward_branch` directly; T12's own checkpoint names both as part of the
# public-facing internal surface) — neither is called from this file's own
# code (see the owning sibling module for the real call site).


def new_state():
    """The initial `manifest["architect"]` shape — persistent, idle, never
    yet spawned (`eng._spawn_architect()` fires lazily, once, off this flag,
    the first tick a job is actually popped — see module docstring)."""
    return {"status": "idle", "current_job": None, "spawned": False}


def gated_blocks(manifest):
    """Every block with an outstanding (queued OR current) `reconcile` job —
    `core/tick.py`'s own exclusion-set read, called right before `core/
    switchboard.py::fill`. A `forward` job's target needs no entry here
    (see module docstring: `has_block_file` already excludes it)."""
    arch = manifest.get("architect") or {}
    queue = manifest.get("architect_queue") or []
    gated = {j["block"] for j in queue if j.get("kind") == "reconcile" and j.get("block")}
    cur = arch.get("current_job")
    if cur and cur.get("kind") == "reconcile" and cur.get("block"):
        gated.add(cur["block"])
    return gated


def _ensure_installed(eng, manifest):
    """Lazily install `manifest["architect"]` via emit the FIRST time any of
    this module's own entry points (`enqueue`/`enqueue_triage`/
    `enqueue_log_review`/`advance`) touches it before `core/engine.py`'s own
    explicit bootup install (`engine_architect_installed`) has run — e.g. a
    rig that drives this module directly. `architect_installed` is this
    module's OWN install effect, distinct from engine.py's: the two never
    collide because each only ever fires while the key is still absent.
    Returns the (possibly just-installed) `manifest["architect"]` dict."""
    arch = manifest.get("architect")
    if arch is None:
        arch = emit.put(eng, manifest, "architect_installed", (), "architect", new_state())
    return arch


def enqueue(eng, manifest, view, landed_blocks):
    """Called BEFORE `core/switchboard.py::fill` each tick (`core/tick.py`):
    (1) clear-ahead `forward` jobs for every in-scope row missing a block
    file; (2) a `reconcile` job for the next in-scope block after each block
    whose gate outcome THIS tick was `record_landed` (✅ genuinely observed
    on trunk). Idempotent throughout — see module docstring.

    Wave 19 (GAP-C): while a fleet-outage case sits open, (1) — NEW
    forward-looking work discovery — is skipped ("spawn NOTHING new while
    paused", the design's own words, extended to the architect's own queue,
    never just `core/switchboard.py`'s worker-pool spawn); (2) is left
    unguarded — it only ever fires for a block that landed THIS tick, which
    structurally never happens while dispatch is paused (nothing new lands
    with nothing new spawned), so no separate guard is needed there."""
    _ensure_installed(eng, manifest)
    if not casestate.fleet_paused(manifest):
        _enqueue_forward_jobs(eng, manifest, view)
    for block in landed_blocks:
        _enqueue_reconcile(eng, manifest, view, block)


# ADR-0009 — restore the deliver-until-consumed dispatch invariant and
# consolidate R1b/R1c/R1d onto it (§3, §6). R1c (the `arch_started`/
# `cold_ticks`/`stall_paged` ladder above, `_architect_liveness_ladder`) is
# DELETED — its scope (the delivery gap) dissolves into R-A..R-E below; its
# honest core (a genuinely dead/unrestartable architect must still reach a
# human) becomes ONE no-progress budget (R-G, `_advance_delivery`). R1b's
# `arch_started` latch + `idle_ticks` debounce are ALSO deleted
# (`_architect_settled_idle` -> `_turn_settled`, below, re-keyed onto the
# `read_hwm(ARCH) >= dispatch_seq` read, R-D) — see this module's own
# module-docstring cross-reference and `adr-0009-architect-turn-completion-
# invariant.md` §3/§6 for the full design.
#
# `_LOW_CONFIDENCE_TRIAGE_SOURCES` (the R1b idle-GUESS's own genuine/
# low-confidence source split) is DELETED here (block 01-37, T10,
# ADR-0012 §6(b)) along with the guess itself (`architect_triage.py::
# _advance_triage`) — structured-only reporting means a settled architect
# turn always carries a real verdict; the classify-layer `unclassified`
# source this constant named no longer exists either (T8 retired the
# free-text grader that produced it).

# R-C/R-E/R-G tunables (ordering constraint, R-G): RESPAWN_CAP * (respawn-
# settle + turn-latency) < NO_PROGRESS_BUDGET < the run's own wall-clock
# budget — recovery always gets its full budget before the honest page, and
# the honest page always beats a silent budget-REJECT. Units are "pace
# units" — the SAME opaque, pluggable clock `core/sentry.py`/`core/
# liveness.py` already use (`eng._now()` live, a persisted tick counter in
# a rig) — never a hardcoded wall-clock assumption baked in here.
RESPAWN_CAP = 3            # at most this many clean re-spawns per stuck order (R-C)
REDELIVER_AFTER = 3        # pace units the runner must sit IDLE before a re-send (R-E)
NO_PROGRESS_BUDGET = 30    # working-excluded pace units unconsumed before ONE page (R-G)


def _delivered(eng, job):
    """ADR-0009 R-D: `delivered(W) ≡ read_hwm(W) >= dispatch_seq`, read
    per-wid (here always `ARCHITECT_WID` — the active resend/respawn loop
    is architect-only; workers stay on `core/sentry.py`'s own re-send
    ladder). `eng._read_hwm` is an OPTIONAL duck-typed hook (mirrors
    `eng._worker_working`/`eng._now`) — real `core.engine.Engine` wires it
    to `engine/jobs.py::read_hwm`. ABSENT (every `core/*_rig.py` fixture
    that predates ADR-0009 and never backs a real runner mailbox for the
    architect) degrades to the job's own `ordered` flag — 'sent ==
    delivered', the documented PRE-ADR-0009 behavior — so no prior rig
    changes; `job["dispatch_seq"]` itself degrades the SAME way (see
    `_stamp_dispatch`), so the two stay consistent whether or not either is
    a real int."""
    if job.get("dispatch_seq") is None:
        return False
    fn = getattr(eng, "_read_hwm", None)
    if not callable(fn):
        return bool(job.get("ordered"))
    try:
        hwm = fn(ARCHITECT_WID)
    except Exception:   # noqa: BLE001 — a broken hook never wedges the job
        return False
    return hwm >= job["dispatch_seq"]


def _turn_settled(eng, job):
    """Whether it is safe to apply a completion BACKSTOP for `job` (R1b's
    directional triage resolve, R1d's refused-authoring escalation, the
    reconcile no-op backstop): the current order must be DELIVERED (R-D,
    `_delivered` above) AND the architect must not currently be mid-turn
    (`eng._worker_working`, optional — absent reads not-working, same
    fail-toward-arming discipline `core/sentry.py`/`core/liveness.py`
    already use for this hook). Replaces the deleted `_architect_settled_
    idle` (the `arch_started` latch + `idle_ticks` debounce, ADR-0009 §6):
    no separate debounce state — `_worker_working`, re-sampled every call
    (never latched), is what pauses a genuinely live turn; `_delivered`
    alone (hwm-anchored, for a live engine) is what proves a turn actually
    ran to completion. One invariant, read fresh every call, never two
    copies that could drift."""
    if not _delivered(eng, job):
        return False
    fn = getattr(eng, "_worker_working", None)
    if callable(fn):
        try:
            if fn(ARCHITECT_WID):
                return False
        except Exception:   # noqa: BLE001 — a broken hook never wedges the job
            pass
    return True


def _stamp_dispatch(eng, d, text, kind, extra=None):
    """ADR-0009 R-B: stamp `d["dispatch_seq"]` (a job OR one of its
    sub-dict entries — e.g. a `scope_forward` triage's own adhoc `entry`,
    a SEPARATE order-requiring sub-state with its own namespace, so a
    fresh dict already starts `dispatch_seq=None` the instant a NEW
    order-requiring sub-state begins — R-B's "NULLED on every transition"
    is satisfied by construction, never a second explicit reset) to the
    seq JUST used for this send — read back off `eng._mbox_seq` (OPTIONAL,
    mirrors R-A's persisted `manifest["mbox_seq"][ARCHITECT_WID]`; real
    `core.engine.Engine` wires it). ABSENT (every pre-ADR-0009 rig, none of
    which back a real runner mailbox for the architect) degrades to a
    truthy sentinel (`True`) — the exact pre-ADR-0009 `ordered=True`
    semantic `_delivered`'s own hookless fallback already expects. Also
    remembers the exact order text/kind (`_order_text`/`_order_kind`) so
    R-C/R-E can re-deliver the SAME content at the SAME seq — the runner
    dedups by seq (`engine/worker_runner.py::_pending`), so an
    at-least-once re-send is harmless. `extra` (optional dict) folds any
    SAME-transition sibling field (e.g. `ordered=True`) into this ONE emit,
    rather than a second separate write — `d` is mutated + the ONE typed
    event written together, atomically, via `emit.patch_obj`."""
    fn = getattr(eng, "_mbox_seq", None)
    if callable(fn):
        try:
            seq = fn(ARCHITECT_WID)
        except Exception:   # noqa: BLE001 — never wedge a send on a broken hook
            seq = True
    else:
        seq = True
    updates = {"dispatch_seq": seq, "_order_text": text, "_order_kind": kind}
    if extra:
        updates.update(extra)
    emit.patch_obj(eng, "architect_dispatch_stamped", d, updates, kind=kind)


def _clock(eng, manifest):
    """The SAME pluggable-clock idiom `core/sentry.py`/`core/liveness.py`
    already use — `eng._now()` when present, else an internal counter
    persisted at `manifest["architect_clock"]`, incremented once per
    call — a SEPARATE counter from either of those modules' own (all three
    track each other tick-for-tick whenever every one falls back, but none
    ever reads another's counter directly)."""
    now_fn = getattr(eng, "_now", None)
    if callable(now_fn):
        return now_fn()
    counters = manifest.get("architect_clock") or {}
    newclock = int(counters.get("clock", 0)) + 1
    emit.put(eng, manifest, "architect_clock_advanced", ("architect_clock",), "clock",
            newclock)
    return newclock


def _redeliver(eng, d, now):
    """Re-send `d`'s already-stamped order at its ALREADY-STAMPED seq
    (never a fresh mint — R-A/R-E: 'same monotonic seq; runner dedups') via
    the OPTIONAL `eng._resend` hook (real `core.engine.Engine` wires it to
    `engine/jobs.py::send` at a caller-supplied seq); absent, a no-op (a
    pre-ADR-0009 rig has no real mailbox to re-append to anyway — its own
    `_delivered` fallback already reads 'delivered' the instant `ordered`
    is set, so this is never reached for one). Re-anchors `last_sent_at` so
    R-E's idle-gated throttle measures from THIS send forward."""
    fn = getattr(eng, "_resend", None)
    seq = d.get("dispatch_seq")
    # `is not True` (never `!=`/`not in (None, True)`): Python's `1 == True`,
    # so an equality-based check would wrongly treat a REAL, legitimate seq
    # of 1 as the hookless `True` sentinel and skip the re-send entirely.
    if callable(fn) and seq is not None and seq is not True:
        try:
            fn(ARCHITECT_WID, d["dispatch_seq"], d.get("_order_text") or "",
              d.get("_order_kind") or "arch.redeliver")
        except Exception:   # noqa: BLE001 — a broken hook never wedges the job
            pass
    emit.patch_obj(eng, "architect_redelivered", d, {"last_sent_at": now})


def _advance_delivery(eng, manifest, d):
    """ADR-0009 R-C/R-E/R-G: the architect-ONLY deliver-until-consumed
    recovery loop for `d` (a job or one of its sub-dict entries) whose
    current order has been SENT (`dispatch_seq` set) but not yet DELIVERED
    (`_delivered` False). Workers stay on `core/sentry.py`'s own re-send
    ladder (R-D) — this is never called for anything but the architect's
    own `current_job`/adhoc entries.

    Live-only: `eng._read_hwm` gates the WHOLE function — absent (every
    pre-ADR-0009 rig `eng` stand-in), this is a genuine no-op, because
    `_delivered`'s own hookless fallback already reads 'delivered' the
    instant `ordered` is set (`dispatch_seq` is then `True`, never `None`),
    so the 'not yet consumed' branch this function handles is structurally
    unreachable for those rigs — zero behavior change, exactly the
    discipline every other optional hook in this stack already keeps.

    R-G's no-progress accumulator is a PERSISTED INTEGRATING accumulator
    (`d["unconsumed_work_excluded"]`), sampled once per call via the SAME
    shared helper `core/liveness.py::sweep` uses for its own silence ladder
    (`liveness.working_excluded_integrate` — "FACTOR the working-excluded
    integration step... into a shared helper both call, do not copy it") —
    `reset_on_active=False`: PAUSED while the architect is provably
    working, never reset to 0 merely because it worked (only a genuine
    `_delivered` flip resets it — see the job-kind advance functions below,
    which clear it the instant `_turn_settled`/`_delivered` observes
    completion). Anchored on the ORDER (`d["unconsumed_since"]`), never on
    the raw hwm integer (a respawn's hwm reset 3->0 must never read as
    'progress')."""
    read_hwm = getattr(eng, "_read_hwm", None)
    if not callable(read_hwm):
        return   # no live delivery signal — see docstring; nothing to recover

    now = _clock(eng, manifest)
    anchor = {}
    if d.get("unconsumed_since") is None:
        anchor["unconsumed_since"] = now
    if d.get("last_sample") is None:
        anchor["last_sample"] = now
    if d.get("last_sent_at") is None:
        # Anchor R-E's idle-gated redeliver timer to the FIRST tick this
        # gap was observed (effectively "right after sending" — `advance`
        # calls this the very next pass after `_stamp_dispatch`) — never
        # left unset until a redeliver has already happened once, else
        # `now - d.get("last_sent_at", now)` would trivially read 0 forever
        # and REDELIVER_AFTER could never trip.
        anchor["last_sent_at"] = now
    if anchor:
        emit.patch_obj(eng, "architect_delivery_anchored", d, anchor)
    last_sample = d.get("last_sample", now)

    working = False
    wfn = getattr(eng, "_worker_working", None)
    if callable(wfn):
        try:
            working = bool(wfn(ARCHITECT_WID))
        except Exception:   # noqa: BLE001 — a broken hook never wedges the job
            working = False

    new_last_sample, new_unconsumed = liveness.working_excluded_integrate(
        now, last_sample, d.get("unconsumed_work_excluded", 0),
        working, reset_on_active=False)
    emit.patch_obj(eng, "architect_delivery_integrated", d,
                   {"last_sample": new_last_sample, "unconsumed_work_excluded": new_unconsumed})

    alive = True
    afn = getattr(eng, "_is_alive", None)
    if callable(afn):
        try:
            alive = bool(afn(ARCHITECT_WID))
        except Exception:   # noqa: BLE001 — fail toward "alive" (never respawn-storm on a flaky hook)
            alive = True

    if not alive:
        respawns = d.get("respawns", 0)
        if respawns < RESPAWN_CAP:
            spawn_fn = getattr(eng, "_spawn_architect", None)
            if callable(spawn_fn):
                spawn_fn()   # R-C: clean-slate (retire_stale_dir, engine.py::_real_spawn)
            emit.patch_obj(eng, "architect_respawn_recorded", d, {"respawns": respawns + 1})
            _redeliver(eng, d, now)
            eng.log("flow", f"architect: DEAD — re-spawned (clean-slate, R-C) and "
                            f"re-delivered the outstanding order at dispatch_seq="
                            f"{d.get('dispatch_seq')!r} (respawn #{d['respawns']})")
    else:
        idle = False
        ifn = getattr(eng, "_runner_idle", None)
        if callable(ifn):
            try:
                idle = bool(ifn(ARCHITECT_WID))
            except Exception:   # noqa: BLE001 — fail toward "not idle" (never race a live turn)
                idle = False
        if idle and (now - d.get("last_sent_at", now)) >= REDELIVER_AFTER:
            _redeliver(eng, d, now)
            eng.log("flow", f"architect: re-delivered (R-E, idle-gated) the "
                            f"outstanding order at dispatch_seq="
                            f"{d.get('dispatch_seq')!r}")

    if (d["unconsumed_work_excluded"] >= NO_PROGRESS_BUDGET
            and not d.get("no_progress_paged")):
        detail = (f"architect ordered a job (dispatch_seq={d.get('dispatch_seq')!r}) "
                  f"that has stayed UNCONSUMED for {d['unconsumed_work_excluded']} "
                  f"working-excluded pace unit(s) (>= NO_PROGRESS_BUDGET="
                  f"{NO_PROGRESS_BUDGET}) — R-G no-progress budget, paged ONCE "
                  f"(THE FLOOR re-pings after)")
        casestate.open_operator_case(eng, manifest, d.get("block"),
                                     "architect.no_progress", detail,
                                     worker_id=ARCHITECT_WID, kind="stall")
        emit.patch_obj(eng, "architect_no_progress_paged", d, {"no_progress_paged": True})
        eng.log("flow", f"architect: NO-PROGRESS — {detail}")


def _reset_delivery_state(eng, d):
    """R-G: reset the no-progress accumulator + respawn count ONLY on the
    genuine `read_hwm >= dispatch_seq` flip (never on a mere respawn or a
    working-tick) — called by every job-kind's advance function the
    instant it observes `_delivered`/`_turn_settled` true, so a
    MULTI-order job (R-B) starts its NEXT order's budget fresh."""
    emit.patch_obj(eng, "architect_delivery_reset", d, {
        "unconsumed_since": None, "last_sample": None, "last_sent_at": None,
        "unconsumed_work_excluded": 0, "respawns": 0, "no_progress_paged": False})


def advance(eng, manifest):
    """Called AFTER `core/switchboard.py::fill` each tick (`core/tick.py`) —
    see module docstring for why this positioning (not before fill) is what
    makes the reconcile-gate ordering STRICT. Progresses the current job by
    exactly one step; clears it (architect back to idle) the tick a
    reconcile job's block is observed in `manifest["reconciled"]` or a
    forward job's `land_via_grant` observes `"landed"`. Then, if idle, pops
    + starts the next queued job (one job of NEW throughput per tick —
    `architect-count` in the real design is the knob that would parallelize
    this; a single persistent architect in this brick)."""
    arch = _ensure_installed(eng, manifest)
    reconciled = set(manifest.get("reconciled") or [])

    cur = arch.get("current_job")
    if cur:
        # ADR-0009 R-C/R-E/R-G: the architect-only deliver-until-consumed
        # recovery loop — runs BEFORE the kind-specific step below, on
        # WHATEVER order is currently outstanding (any job kind), so a
        # stuck delivery recovers regardless of which completion signal
        # that job kind ultimately waits on. Replaces ADR-0006 R1c
        # (`_architect_liveness_ladder`, DELETED — its scope dissolves into
        # R-A..R-E, its honest core becomes this ONE no-progress budget).
        if cur.get("dispatch_seq") is not None and not _delivered(eng, cur):
            _advance_delivery(eng, manifest, cur)
        if cur.get("kind") == "reconcile":
            if cur.get("block") in reconciled:
                eng.log("flow", f"architect[reconcile:{cur['block']}]: "
                                f"architect.reconciled observed -> gate "
                                f"cleared, architect idle")
                _reset_delivery_state(eng, cur)
                emit.patch_obj(eng, "architect_job_cleared", arch,
                               {"status": "idle", "current_job": None},
                               block=cur.get("block"), kind="reconcile")
            elif _turn_settled(eng, cur):
                # R1b-style backstop for reconcile (mirrors `architect_triage.py`'s
                # own `_advance_triage`, ADR-0009 re-keyed onto `_turn_settled`/R-D):
                # the architect's reconcile order was genuinely DELIVERED and it
                # settled idle with NO `architect.reconciled` routed — a real-LLM
                # NO-OP reconcile ("no forward impact") whose free-text classify
                # couldn't tag as a structured reconciled report. Tie
                # completion to ENGINE STATE (genuine delivery + settled),
                # never to parsed prose: mark the block reconciled so 01-xx's
                # dispatch is freed. A no-op is benign, and any REAL drift the
                # architect missed surfaces as an ordinary build wall on that
                # block (architect-first) — never a silent WEDGE of the whole
                # fleet (the T2-12 reconcile-gate hang).
                emit.append(eng, manifest, "architect_reconciled_recorded",
                           ("reconciled",), cur["block"], block=cur["block"])
                eng.log("flow", f"architect[reconcile:{cur['block']}]: order "
                                f"DELIVERED, settled idle, no architect.reconciled "
                                f"-> no-op reconcile backstop, gate cleared (R1b-style)")
                _reset_delivery_state(eng, cur)
                emit.patch_obj(eng, "architect_job_cleared", arch,
                               {"status": "idle", "current_job": None},
                               block=cur.get("block"), kind="reconcile")
        elif cur.get("kind") == "forward":
            _advance_forward(eng, manifest, cur)
            if cur.get("landed"):
                _reset_delivery_state(eng, cur)
                emit.patch_obj(eng, "architect_job_cleared", arch,
                               {"status": "idle", "current_job": None},
                               block=cur.get("block"), kind="forward")
            elif cur.get("last_outcome") == "fail-closed" and _turn_settled(eng, cur):
                _backstop_refused_authoring(eng, manifest, cur)
                emit.patch_obj(eng, "architect_job_cleared", arch,
                               {"status": "idle", "current_job": None},
                               block=cur.get("block"), kind="forward")
        elif cur.get("kind") == "log":
            _advance_log(eng, manifest, cur)
            if cur.get("landed_all"):
                _reset_delivery_state(eng, cur)
                emit.patch_obj(eng, "architect_job_cleared", arch,
                               {"status": "idle", "current_job": None},
                               block=cur.get("block"), kind="log")
            elif cur.get("last_outcome") == "fail-closed" and _turn_settled(eng, cur):
                _backstop_refused_authoring(eng, manifest, cur)
                emit.patch_obj(eng, "architect_job_cleared", arch,
                               {"status": "idle", "current_job": None},
                               block=cur.get("block"), kind="log")
        elif cur.get("kind") == "triage":
            _advance_triage(eng, manifest, cur)
            if cur.get("resolved"):
                emit.patch_obj(eng, "architect_job_cleared", arch,
                               {"status": "idle", "current_job": None},
                               block=cur.get("block"), kind="triage")
        else:
            eng.log("flow", f"architect: current_job has an unknown kind "
                            f"{cur.get('kind')!r} — held, never advanced")

    queue = manifest.get("architect_queue") or []
    if arch["status"] == "idle" and queue:
        if not arch.get("spawned"):
            eng._spawn_architect()
            emit.patch_obj(eng, "architect_spawned_marked", arch, {"spawned": True})
        job = emit.pop_index(eng, manifest, "architect_job_popped", ("architect_queue",), 0)
        emit.patch_obj(eng, "architect_job_dispatched", arch,
                       {"status": "busy", "current_job": job}, kind=job["kind"])
        if job["kind"] == "reconcile":
            _order_reconcile(eng, job)
        elif job["kind"] == "forward":
            _advance_forward(eng, manifest, job)
        elif job["kind"] == "log":
            _advance_log(eng, manifest, job)
        elif job["kind"] == "triage":
            _advance_triage(eng, manifest, job)
        eng.log("flow", f"architect: dispatch {job}")

    # T7 (block 01-37, R5) — the batched visibility-flag digest: sent the
    # next time the architect is IDLE (whether or not a new job was JUST
    # popped above — sending it here, unconditionally on idle, never makes
    # it wait a whole extra tick behind a fresh job). Purely informational:
    # never a job of its own, never blocks/consumes the architect's queue
    # throughput, never pages.
    if arch["status"] == "idle":
        _send_flag_digest(eng, manifest)

    return {"status": arch["status"], "current_job": arch.get("current_job")}


def _send_flag_digest(eng, manifest):
    """T7 — batch every `worker.flag` recorded since the last digest
    (`core/router.py::_route_flag` appends to `manifest["architect_flags"]`)
    into ONE `arch.flags` order, never one order per flag (R5: "a chatty
    worker cannot starve real triage"). A no-op when nothing is pending.
    Pages no one, opens no case, expects no reply — purely informational;
    the durable, operator-readable record is `manifest["flag_ledger"]`
    (`core/router.py`'s own append, untouched here)."""
    flags = manifest.get("architect_flags") or []
    if not flags:
        return
    emit.put(eng, manifest, "architect_flags_digest_sent", (), "architect_flags", [],
            count=len(flags))
    lines = "\n".join(
        f"  - block={f.get('block') or '(none)'} worker={f.get('worker_id')!r}: "
        f"{f.get('detail')}" for f in flags)
    text = (f"[TRON]  architect — VISIBILITY DIGEST ({len(flags)} flagged since "
           f"the last digest, surfaced non-paging, R5):\n{lines}")
    if not eng.dry:
        eng.emit(vocab.TPL_ARCH_FLAGS, text, slots={"detail": lines},
                 worker_id=ARCHITECT_WID, kind=vocab.TPL_ARCH_FLAGS)
    eng.log("flow", f"architect: sent visibility digest for {len(flags)} "
                    f"flag(s) — pages no one")
