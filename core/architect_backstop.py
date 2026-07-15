"""core.architect_backstop — block 01-38 T12 (behavior-preserving split of
`core/architect.py`): the ONE `backstop` part (T12's own binding rule —
"every backstop lives in the ONE backstop part"). Houses `ADR-0006 R1d`,
`_backstop_refused_authoring`: a STARTED-then-REFUSED forward/log job — the
architect's order was genuinely DELIVERED and it settled idle, yet
`land_via_grant` still reports `"fail-closed"` (its patch-id is
unresolvable == it authored NO branch, prose instead of a file). (R1a — the
architect can never be the SOURCE of a triage — and R1b — a settled triage
turn with no routed verdict is bounded-re-ordered, then paged — are the
OTHER two named backstops this module's docstring cross-references; both
stay inline in `core/architect_triage.py`'s own `enqueue_triage`/
`_advance_triage`, exactly where they lived pre-split, since each is a
handful of lines woven into that job-kind's own order-then-observe control
flow, not a standalone callable — extracting them would be a redesign, not
a relocation.)

T12 BINDING: every backstop routes through the counter partition
(`core/counters.py`, T9). `architect_refused_authoring_backstop_fired` is
the first REAL production `may_fire`-class member (T9 shipped the
mechanism, mutation-proven, with zero live members — this is the
"one-entry addition" its own forward-notes predicted): a started-then-
refused authoring event is a designed-rare defensive backstop — the
architect ordering work and then genuinely failing to author a branch
should almost never happen, but is not structurally impossible, so it is
COUNTED (not just paged) and given a real per-run ceiling acceptance can
grade against, rather than being invisible to the event-stream-as-ground-
truth read."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import casestate  # noqa: E402 — core/casestate.py, open_operator_case
import emit       # noqa: E402 — core/emit.py, block 01-38 T7's single emit API
import architect  # noqa: E402 — core/architect.py, the facade (ARCHITECT_WID)


def _backstop_refused_authoring(eng, manifest, cur):
    """ADR-0006 R1d (ADR-0009: re-keyed onto `_turn_settled`/R-D): a
    STARTED-then-REFUSED forward/log job — the architect's order was
    genuinely DELIVERED (`_turn_settled`) and it settled idle, yet
    `land_via_grant` still reports `"fail-closed"` (its patch-id is
    unresolvable == it authored NO branch, prose instead of a file).
    Resolve LOUD: page the operator once and free the architect. Never poll
    a never-authored branch to budget (the log/forward wedge A3), and — for
    a log-review — never silently DROP the reviewer's findings by
    benign-clearing. Clearing `current_job` at the call site is the
    once-guard (the job is gone next tick, so `open_operator_case`'s
    non-idempotency can't storm). A cold/dead architect whose order was
    NEVER delivered at all is not here — R-G's no-progress budget
    (`_advance_delivery`) owns that window."""
    kind = cur.get("kind")
    # T12 (counter partition, R4/T9): a designed-rare backstop is COUNTED,
    # not just paged — the first real `may_fire`-class production member
    # (see module docstring). Forensic-only (no state of its own); the
    # state changes this backstop drives live in `casestate.open_operator_case`.
    emit.record(eng, "architect_refused_authoring_backstop_fired",
               block=cur.get("block"), job_kind=kind)
    detail = (f"architect ordered a {kind!r} job for {cur.get('block')!r} and "
              f"settled idle having authored NO branch (land grant fail-closed) "
              f"— started-then-refused authoring; routed to operator (ADR-0006 "
              f"R1d), never a silent wedge or a dropped log-review finding")
    casestate.open_operator_case(eng, manifest, cur.get("block"),
                                 f"architect.{kind}_refused", detail,
                                 worker_id=architect.ARCHITECT_WID, kind="stall")
    eng.log("flow", f"architect[{kind}:{cur.get('block')}]: refused authoring "
                    f"(fail-closed + settled idle) -> operator (R1d)")
