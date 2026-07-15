"""core.sim.trunk_blame_rig — the T10 door fixture (block 01-38, R7/AC-6):
`test:<budgeted_waits_correct_blame>`.

Paper-test ledger row 3 (D3 — HANDOVER-260712): a historical, NEVER-MERGED
bug (the frozen ADR-0011 S-4 branch) had an unbudgeted trunk-red redrive that
re-ordered the WRONG worker — "block B blamed for block A's red commit."
That code never landed; `core/gate.py::_advance_trunk` on a real fail simply
HOLDS (`return "trunk_failed", detail`) — no auto-redrive, no re-order, no
second worker touched. Row 23 (R7's own summary) confirms budget+addressee
is closed across every OTHER surface, but flags the **blame-assignment
proof itself** as the one thing "not independently found as a distinct
proof artifact" — this file is that artifact.

It also closes a real, narrower gap `core/sim/sim_l2_rig.py`'s own
`run_failing_test_variant` (F1-F6) left open: that fixture stops the instant
`core.sentry` escalates the idle gate into a PARKED case (owner="architect",
never triaged, run halts at its tick cap) — it never exercises the case
actually reaching the ARCHITECT'S verdict and the real FIRST PAGE. This
fixture drives that far.

THE SCENARIO
------------
Two independent blocks, `worker_count=2` (both dispatch concurrently), over
the mockup's SHARED, aggregate declared test command (`app/tests/test_lib.
py` checks every `app/lib/*.py` module's own `check()` in one run — a real,
common shape: one broken module reds the WHOLE suite, not just its own):
  - FAIL_BLOCK (02-01) — deliberately broken function; never fixed.
  - OK_BLOCK (02-02) — a small, CORRECT function that MERGES onto trunk ON
    TOP of FAIL_BLOCK's still-open wait — a genuine "another worker landed
    on top" moment. Because the suite is SHARED, OK_BLOCK's own trunk
    re-validation *also* reds (the aggregate exit code is non-zero) even
    though its OWN code independently passes (the declared command's own
    detail text says so: `"...FAIL 02-01...PASS 02-02..."`) — so OK_BLOCK's
    gate ALSO ends up escalated+paged, on its OWN, separate case. This is
    NOT the D3 bug (a project-level shared-suite property, out of engine
    scope to fix) — it is the PERFECT adversarial fixture for blame: the
    two blocks' trunk-verdict text is now genuinely SHARED/AMBIGUOUS
    (both block ids appear in it), so a heuristic that derived blame by
    scanning that text would be dangerously ambiguous. The engine's real
    blame is never derived from that text — it is the block's OWN
    `gate_state["wid"]`, structural, never confused between the two
    concurrently-red gates. See B6/M1 below.

A custom `ScriptedDriver` (`_OperatorVerdictDriver`) answers the architect's
triage turn with a real routed `architect.triage_verdict` verdict=`"operator"`
(never `"answer"`, `self_retract_rig`'s own choice — the opposite proof: HERE
the case must genuinely reach the operator) the instant the architect orders
a `triage` job — carrying the wait through its FULL bounded ladder: idle-cap
escalate -> architect-first triage -> the FIRST real page.

THE TERMINAL LEG (documented, not re-proven here)
---------------------------------------------------
A proven-dead TRANSPORT (repeated delivery failure -> `PAGE_PERMANENT_FAIL_
AFTER` -> `case_page_permfailed`, SAFE-PARK-AND-HALT) is the SAME generic,
case-kind-agnostic backstop `core/operator_channel_rig.py` (block 01-38 T5,
`test:<operator_channel_outbound>`) already proves. This wait rides that
SAME mechanism, not a new one — B7 below confirms the paging bookkeeping
that backstop reads (`consecutive_fail`/`attempts`/`permanently_failed`) is
genuinely initialized on THIS case kind too (never special-cased out of it),
rather than re-driving a whole second broken-transport scenario.

Asserted off the events-as-single-ground-truth stream (`eng.events.log`,
T7) — never the advisory flow-log:
  B1  BOUNDED — FAIL_BLOCK's gate observes a REAL trunk fail (the real
      declared test command, genuinely red) and HOLDS — never advances into
      record/close.
  B2  SWAP GUARD (the D3 regression, both directions) — NEITHER case's
      `worker_id` ever equals the OTHER block's worker: FAIL_BLOCK's case
      is never blamed on `engineer-02-02`, OK_BLOCK's case is never blamed
      on `engineer-02-01` — even though both blocks are concurrently red
      and their trunk-verdict TEXT is shared/interleaved.
  B3  SENTRY BOUNDS THE SILENT WAIT — idle-cap escalates FAIL_BLOCK's gate
      (never core.gate self-escalating its own real red).
  B4  ARCHITECT-FIRST — the escalation opens a parked case `owner=
      "architect"` (never an immediate page) — the root invariant holding
      for this wall kind too.
  B5  PAGE — the architect's own `"operator"` verdict fires the FIRST real
      page (`case_escalated_to_operator` + `operator_page`) — the leg
      `sim_l2_rig`'s own fixture never reaches.
  B6  CORRECT BLAME (the adversarial check) — OK_BLOCK's own code genuinely
      MERGED onto trunk (`gate_merged`) causally BEFORE FAIL_BLOCK's page
      fires — a real "another worker landed on top" moment inside the run
      — and still, FAIL_BLOCK's paged case's `worker_id` is unambiguously
      `engineer-02-01`, never `engineer-02-02`.
  B7  THE TERMINAL BACKSTOP IS WIRED (not re-driven) — the page's own paging
      bookkeeping (`attempts`/`consecutive_fail`/`permanently_failed`) is
      genuinely present on this case kind, the SAME shape T5's terminal
      proof reads — never special-cased out.
  M1  MUTATION PROOF (non-vacuity, a concrete WRONG heuristic) — OK_BLOCK's
      OWN case's `trunk_verdict_detail` literally contains the substring
      `"FAIL 02-01"` (the shared-suite text — its OWN code independently
      PASSED, per the SAME detail's `"PASS 02-02"`). A heuristic that
      derived blame by scanning that text for the reported failure would
      misattribute OK_BLOCK's case to `engineer-02-01`. The REAL,
      engine-assigned `worker_id` for that case is `engineer-02-02` —
      DIFFERS from the naive heuristic's guess, proving blame is sourced
      structurally (`gate_state["wid"]`), never parsed from shared/
      ambiguous test output.

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)` and every
line, exits non-zero on any fail.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # core/sim
CORE_DIR = os.path.dirname(HERE)                             # core
APP_ROOT = os.path.dirname(CORE_DIR)                         # worktree root
ENGINE_DIR = os.path.join(APP_ROOT, "engine")
sys.path.insert(0, ENGINE_DIR)
sys.path.insert(0, CORE_DIR)
sys.path.insert(0, HERE)

import jobs                              # noqa: E402 — engine/jobs.py, the ONE process-spawn seam this driver stubs
import state                             # noqa: E402 — core/state.py
import gate                             # noqa: E402 — core/gate.py, stage constants
import intake                           # noqa: E402 — core/intake.py, the private per-agent door (rig-side write)
from engine import Engine               # noqa: E402 — core/engine.py, the module under drive

import architect as core_architect       # noqa: E402 — core/architect.py, ARCHITECT_WID
import scaffold as sim_scaffold          # noqa: E402 — core/sim/scaffold.py
import worker as sim_worker              # noqa: E402 — core/sim/worker.py, ScriptedDriver + Transcript

FAIL_BLOCK = "02-01"
OK_BLOCK = "02-02"
BLOCKS = [
    {"id": FAIL_BLOCK, "depends_on": [], "reviewer_class": "none",
     "title": "double(x): DELIBERATELY BROKEN (never fixed)"},
    {"id": OK_BLOCK, "depends_on": [], "reviewer_class": "none",
     "title": "triple(x): a small real, CORRECT function — lands cleanly "
              "ON TOP of FAIL_BLOCK's still-open wait"},
]
MAX_TICKS = 80

_BROKEN_DOUBLE_BODY = (
    '"""app/lib/02-01.py — double(x), DELIBERATELY BROKEN for '
    'core.sim.trunk_blame_rig (identity instead of *2, never fixed/'
    're-merged) — genuinely fails the mockup\'s real declared test command '
    'on trunk."""\n\n'
    "def double(x):\n"
    "    return x   # BUG: should be x * 2 — deliberately never fixed\n\n\n"
    "def check():\n"
    "    return double(21) == 42\n"
)
_TRIPLE_BODY = (
    '"""app/lib/02-02.py — triple(x), a small real, CORRECT function — '
    'the INNOCENT block that lands cleanly ON TOP of FAIL_BLOCK\'s still-'
    'open wait (core.sim.trunk_blame_rig)."""\n\n'
    "def triple(x):\n"
    "    return x * 3\n\n\n"
    "def check():\n"
    "    return triple(7) == 21 and triple(0) == 0 and triple(-2) == -6\n"
)


def _transcript():
    return sim_worker.default_transcript(overrides={
        FAIL_BLOCK: ("app/lib/02-01.py", _BROKEN_DOUBLE_BODY),
        OK_BLOCK: ("app/lib/02-02.py", _TRIPLE_BODY),
    })


_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


class _OperatorVerdictDriver(sim_worker.ScriptedDriver):
    """The happy-path `ScriptedDriver`, plus: the instant the architect
    ORDERS a `triage` job, answer it with a real routed
    `architect.triage_verdict` verdict=`"operator"` — forcing a GENUINE
    escalation + page (`self_retract_rig`'s own driver deliberately answers
    `"answer"`, the opposite proof: resolved without ever paging). Every
    block's own engineer/reviewer play is super's, unchanged."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._triage_answered = set()
        self.triage_ordered_tick = {}

    def react(self, i, manifest):
        super().react(i, manifest)
        self.react_architect_triage_operator(i, manifest)

    def react_architect_triage_operator(self, i, manifest):
        arch = manifest.get("architect") or {}
        cur = arch.get("current_job") or {}
        if cur.get("kind") != "triage" or not cur.get("ordered"):
            return
        tid = cur.get("triage_id")
        if not tid:
            return
        self.triage_ordered_tick.setdefault(tid, i)
        if tid in self._triage_answered:
            return
        intake.write(self.tron_ctx, core_architect.ARCHITECT_WID,
                     {"tag": "architect.triage_verdict", "agent_id": core_architect.ARCHITECT_WID,
                      "slots": {"triage_id": tid, "verdict": "operator"}})
        self._triage_answered.add(tid)


def _drive(max_ticks=MAX_TICKS):
    """Mirrors `core/sim/self_retract_rig.py::_drive`'s own manual boot/
    tick/observe/spawn-stub shape (no real worker process, real trunk
    observation throughout) — used here (rather than `core/sim/run.py::
    run_sim`) because this scenario needs a CUSTOM driver
    (`_OperatorVerdictDriver`), which `run_sim` has no seam to accept."""
    ctx, root = sim_scaffold.build(BLOCKS)
    driver = _OperatorVerdictDriver(root, ctx.grants_dir, ctx, _transcript())

    spawn_calls = []

    def _fake_spawn_runner(worker_id, worker_dir, session_id, cwd=None,
                           runtime=None, adapter=None, model=None, settle_s=2.0):
        spawn_calls.append(worker_id)
        return {}

    real_spawn_runner = jobs.spawn_runner
    jobs.spawn_runner = _fake_spawn_runner
    try:
        eng = Engine(ctx)
        eng.dry = False   # real trunk observation throughout
        eng.start(scope="all", worker_count=2, models={})

        session_ended_tick = None
        i = -1
        for i in range(max_ticks):
            res = eng.tick()
            manifest = state.load(ctx)
            driver.record_done_ticks(i, res.get("outcomes") or {})
            driver.react(i, manifest)
            if res.get("session_end") is not None:
                session_ended_tick = i
                break

        final_manifest = state.load(ctx)
        return {
            "root": root, "ctx": ctx, "eng": eng, "driver": driver,
            "events": list(eng.events.log),
            "session_ended_tick": session_ended_tick,
            "session_end": final_manifest.get("session"),
            "final_manifest": final_manifest,
            "gates": final_manifest.get("gates") or {},
            "cases": final_manifest.get("cases") or {},
            "ticks_used": i + 1,
        }
    finally:
        jobs.spawn_runner = real_spawn_runner


_PAGE_EVENT_TYPES = {"operator_page", "engine_operator_page_recorded",
                     "case_escalated_to_operator"}


def main():
    r = _drive()
    events = r["events"]
    fail_wid = f"engineer-{FAIL_BLOCK}"
    ok_wid = f"engineer-{OK_BLOCK}"

    def _of(type_):
        return [e for e in events if e["type"] == type_]

    types_seq = [e["type"] for e in events]

    # ── B1 — BOUNDED: FAIL_BLOCK genuinely observes a real trunk fail, holds ──
    trunk_fail_events = [e for e in _of("gate_trunk_verdict")
                         if e["payload"].get("block") == FAIL_BLOCK
                         and e["payload"].get("status") == "fail"]
    g_fail = r["gates"].get(FAIL_BLOCK) or {}
    ok("B1 (BOUNDED — must be GREEN): FAIL_BLOCK's gate.trunk ran the REAL "
       "declared test command and observed a genuine FAIL, and NEVER "
       "advanced into record/close",
       len(trunk_fail_events) >= 1
       and g_fail.get("stage") not in (gate.STAGE_RECORD, gate.STAGE_CLOSE, gate.STAGE_CLOSED),
       f"trunk_fail_events={len(trunk_fail_events)} stage={g_fail.get('stage')!r}")

    # ── B2 — SWAP GUARD (the D3 regression, both directions): neither case's
    #     worker_id ever equals the OTHER block's worker, even though both
    #     blocks are concurrently red and their trunk-verdict TEXT is shared/
    #     interleaved (see module docstring) ──
    fail_case_b2 = next((c for c in r["cases"].values()
                         if c.get("block") == FAIL_BLOCK and c.get("source") == "sentry.cap"), None)
    ok_case_b2 = next((c for c in r["cases"].values()
                       if c.get("block") == OK_BLOCK and c.get("source") == "sentry.cap"), None)
    ok("B2 (D3 REGRESSION GUARD, SWAP-PROOF — must be GREEN): neither "
       "block's parked case is ever blamed on the OTHER block's worker — "
       "FAIL_BLOCK's case is never engineer-02-02, OK_BLOCK's case is never "
       "engineer-02-01 — the historical wrong-worker cross-attribution (D3) "
       "stays dead even under a shared/ambiguous trunk-verdict text",
       fail_case_b2 is not None and ok_case_b2 is not None
       and fail_case_b2.get("worker_id") == fail_wid
       and fail_case_b2.get("worker_id") != ok_wid
       and ok_case_b2.get("worker_id") == ok_wid
       and ok_case_b2.get("worker_id") != fail_wid,
       f"fail_case_worker={ (fail_case_b2 or {}).get('worker_id') } "
       f"ok_case_worker={ (ok_case_b2 or {}).get('worker_id') }")

    # ── B3 — SENTRY bounds the silent wait ──
    sentry_escalations = [e for e in _of("sentry_escalated")
                          if e["payload"].get("block") == FAIL_BLOCK]
    ok("B3 (SENTRY BOUNDS THE WAIT — must be GREEN): the gate, held idle at "
       "gate.trunk past the idle cap, was escalated by core.sentry (never "
       "by core.gate itself)",
       len(sentry_escalations) >= 1
       and any(e["payload"].get("block") == FAIL_BLOCK for e in _of("case_opened")
              if e["payload"].get("source") == "sentry.cap"),
       f"sentry_escalations={len(sentry_escalations)}")

    # ── B4 — ARCHITECT-FIRST: the parked case opens owner="architect" ──
    cap_case = next((c for c in r["cases"].values()
                     if c.get("block") == FAIL_BLOCK and c.get("source") == "sentry.cap"), None)
    architect_first_opens = [e for e in _of("case_opened")
                             if e["payload"].get("source") == "sentry.cap"
                             and e["payload"].get("block") == FAIL_BLOCK]
    ok("B4 (ARCHITECT-FIRST — must be GREEN): the cap escalation opened a "
       "parked case, NEVER an immediate page — case_opened precedes any "
       "case_escalated_to_operator/operator_page for it",
       len(architect_first_opens) == 1
       and ("case_opened" in types_seq and "case_escalated_to_operator" in types_seq
            and types_seq.index("case_opened") < types_seq.index("case_escalated_to_operator")),
       f"architect_first_opens={len(architect_first_opens)} "
       f"case_opened@{types_seq.index('case_opened') if 'case_opened' in types_seq else None} "
       f"escalated@{types_seq.index('case_escalated_to_operator') if 'case_escalated_to_operator' in types_seq else None}")

    # ── B5 — PAGE: the architect's own "operator" verdict fires the FIRST real page ──
    escalated = _of("case_escalated_to_operator")
    fail_escalated = [e for e in escalated if e["payload"].get("block") == FAIL_BLOCK]
    real_pages = [e for e in _of("operator_page")]
    ok("B5 (PAGE — must be GREEN, the leg sim_l2_rig's own fixture never "
       "reaches): the architect's real triage verdict 'operator' fired the "
       "FIRST page for FAIL_BLOCK's case — case_escalated_to_operator AND a "
       "real operator_page event both present",
       len(fail_escalated) >= 1 and len(real_pages) >= 1
       and cap_case is not None and cap_case.get("owner") == "operator",
       f"fail_escalated={len(fail_escalated)} real_pages={len(real_pages)} "
       f"cap_case_owner={(cap_case or {}).get('owner')}")

    # ── B6 — CORRECT BLAME (the adversarial check) ──
    # Causal order: OK_BLOCK's own MERGE (its code genuinely landing on
    # trunk) precedes FAIL_BLOCK's page — a real "another worker landed on
    # top" moment genuinely inside the run (full CLOSE is impossible here —
    # the shared-suite exit code stays nonzero until 02-01 is fixed, a
    # project-test-design property, not an engine one — see docstring).
    ok_merged_idx = next((idx for idx, e in enumerate(events)
                         if e["type"] == "gate_merged" and e["payload"].get("block") == OK_BLOCK), None)
    page_idx = next((idx for idx, e in enumerate(events)
                     if e["type"] == "case_escalated_to_operator"
                     and e["payload"].get("block") == FAIL_BLOCK), None)
    blamed_worker = (fail_case_b2 or {}).get("worker_id")
    ok("B6 (CORRECT BLAME, THE ADVERSARIAL CHECK — must be GREEN): OK_BLOCK's "
       "own code genuinely MERGED onto trunk CAUSALLY BEFORE FAIL_BLOCK's "
       "page (a real innocent worker landed ON TOP while FAIL_BLOCK was "
       "still stuck) — and FAIL_BLOCK's paged case's worker_id is "
       "unambiguously its OWN worker, never OK_BLOCK's",
       ok_merged_idx is not None and page_idx is not None
       and ok_merged_idx < page_idx and blamed_worker == fail_wid,
       f"ok_merged_idx={ok_merged_idx} page_idx={page_idx} "
       f"blamed_worker={blamed_worker!r} fail_wid={fail_wid!r} ok_wid={ok_wid!r}")

    # ── B7 — the terminal backstop's own bookkeeping is genuinely wired here ──
    paging = (fail_case_b2 or {}).get("paging") or {}
    ok("B7 (TERMINAL BACKSTOP WIRED, not re-driven — must be GREEN): the "
       "SAME paging bookkeeping T5's proven-dead-transport terminal proof "
       "reads (attempts/consecutive_fail/permanently_failed) is genuinely "
       "present on THIS case kind — never special-cased out of the generic "
       "R8 machinery",
       {"attempts", "consecutive_fail", "permanently_failed"} <= set(paging)
       and paging.get("attempts", 0) >= 1,
       f"paging={paging}")

    # ── M1 — MUTATION PROOF (non-vacuity): a concrete WRONG heuristic ──
    # OK_BLOCK's OWN case's trunk_verdict_detail is the SHARED/ambiguous
    # text (both block ids appear in it — see module docstring: its own
    # code independently PASSED, per that SAME text's "PASS 02-02", yet the
    # aggregate suite still reds because of 02-01). A heuristic that derived
    # blame by scanning "FAIL <block>" out of a case's OWN trunk-verdict
    # text would misattribute OK_BLOCK's case to engineer-02-01. The REAL
    # blame must DIFFER from that wrong heuristic.
    ok_detail = r["gates"].get(OK_BLOCK, {}).get("trunk_verdict_detail") or ""
    naive_wrong_blame = f"engineer-{FAIL_BLOCK}" if f"FAIL {FAIL_BLOCK}" in ok_detail else None
    ok_case_blamed = (ok_case_b2 or {}).get("worker_id")
    ok("M1 (MUTATION PROOF — a concrete wrong heuristic, non-vacuity): "
       "OK_BLOCK's own trunk-verdict text contains 'FAIL 02-01' (the "
       "shared-suite text) — a text-scanning heuristic would misattribute "
       "OK_BLOCK's case to engineer-02-01 — the REAL blamed worker for "
       "OK_BLOCK's case DIFFERS from that wrong heuristic and is its OWN "
       "(engineer-02-02), sourced structurally from gate_state['wid'], "
       "never parsed from the shared text",
       naive_wrong_blame == fail_wid and ok_case_blamed != naive_wrong_blame
       and ok_case_blamed == ok_wid,
       f"ok_trunk_verdict_detail={ok_detail!r} naive_wrong_blame={naive_wrong_blame!r} "
       f"ok_case_blamed={ok_case_blamed!r}")

    ok("test:<budgeted_waits_correct_blame> (AC-6): the trunk-red wait is "
       "budgeted (bounded -> architect-first parked case -> real page) and "
       "the blame is correct even with a genuinely concurrently-landing "
       "innocent worker present in the same run",
       all(c for _, c, _ in _results))

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.sim.trunk_blame_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
