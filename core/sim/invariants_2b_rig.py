"""core.sim.invariants_2b_rig — the T11 consolidated §2b proof (block 01-38,
AC-7): `test:<invariants_2b_1..6>`.

The ADR's six §2b resilience invariants, each holding under one honest proof
through the real door, gathered under ONE named artifact:

  2b-1  fleet-wide outage self-recovery
  2b-2  two-workers-landing-at-once truth race
  2b-3  record integrity (records done only when the block's commit is on trunk)
  2b-4  spawn failure (counted, retried on a budget, then a case — no storm)
  2b-5  slow ≠ dead
  2b-6  post-close dispatch (an open operator case never halts independent blocks)

COVERAGE MODEL (why four map out, two are driven here)
-------------------------------------------------------
Four of the six ALREADY have a dedicated, green, real-door proof rig that
`scripts/l1.sh` discovers and runs in the SAME L1 gate as this file — so
re-driving their (heavy, real-git/real-Engine) scenarios here would be pure
duplication, not extra assurance. For those four this rig asserts a COVERAGE
MAP: the named rig file exists AND is in `scripts/l1.sh`'s own discovery glob
(`core/*_rig.py` / `core/sim/*_rig.py`), so it is GUARANTEED to run green in
this very gate. That is the honest "every invariant names its live proof",
never a re-run and never a weakened bar:

  2b-1 -> core/outage_rig.py          (drive_outage: bounded pause, architect-
                                        first fleet-outage case, self-release
                                        on recovery, counter reset)
  2b-2 -> core/trunkchurn_rig.py      (block B runs its whole ladder to a clean
                                        close while block A sits mid-gate.record
                                        with an unlanded grant — trunk genuinely
                                        moved under a mid-flight worker; the gate
                                        follows git truth, never a stale sha)
  2b-4 -> core/outage_rig.py          (a spawn that fails is COUNTED, retried,
                                        and — past the budget — becomes an
                                        architect-first case; spawn attempts stay
                                        BOUNDED while paused, never a retry storm)
  2b-5 -> core/liveness_working_rig.py (a worker driven silent up to — but not
                                        past — the ping/escalate threshold is
                                        pinged, never falsely stalled; the
                                        `_worker_working` gate shared with sentry)

DISCLOSED SCOPE NOTE for 2b-4 (surfaced, never hidden): `core/switchboard.py`'s
spawn-failure budget is the FLEET-WIDE `consecutive_deaths` counter (reset to 0
by ANY successful spawn anywhere). It fully satisfies the ADR's literal §2b-4
("a worker that fails to start is counted, retried on a budget, then a case —
never a silent retry storm") for the all-spawns-failing shape `outage_rig`
proves. A NARROWER refinement is NOT yet covered: one specific block whose spawn
ALWAYS fails while OTHER blocks keep succeeding would have its per-block failures
diluted by the shared counter and could retry indefinitely. That is a genuine,
documented open refinement (a per-block spawn-attempt budget) — flagged to the
coordinator/operator as a distinct item, deliberately NOT silently folded into a
"covered" claim here (operator rule: every issue surfaced, never hidden).

The two invariants with NO existing dedicated proof — 2b-3 and 2b-6 — are driven
HERE, each a real `core.engine.Engine` over a fresh real-git mockup (the SAME
boot/tick/observe/spawn-stub shape `core/sim/self_retract_rig.py` and
`core/sim/trunk_blame_rig.py` use), asserted off the events-as-single-ground-
truth stream (`eng.events.log`, T7).

  ── 2b-3 (record integrity) ──
  R1  a block whose ✅ record commit is genuinely authored on its BRANCH but
      WITHHELD from trunk (the commit exists OFF trunk) NEVER records done: no
      `gate_recorded` event, its doc on `main` stays not-✅, its gate never
      reaches CLOSED — the ✅ is earned by real trunk observation
      (`land_via_grant`=="landed"), never by the off-trunk commit's mere
      existence.
  R2  POSITIVE CONTROL (non-vacuity): an IDENTICAL sibling block whose record
      commit IS landed records done normally (gate CLOSED, ✅ Done on main) — so
      R1's no-record is the withheld land's doing, not a mechanism broken for all.
  R3  the withheld block's ✅ commit genuinely EXISTS off trunk (on its branch,
      NOT a `main` ancestor) — proving R1 is the real "commit exists outside the
      trunk" condition, not a block that simply never authored one.

  ── 2b-6 (post-close dispatch) ──
  P1  with an operator-owned case OPEN on block X (never settled), the
      INDEPENDENT block Y keeps advancing — Y's own code reaches a real trunk
      MERGE (`gate_merged`) AFTER X's case is escalated-to-operator; the open
      case did not halt Y's progress. (Y was itself dispatched WHILE X was
      already parked-and-excluded — worker_count=1, X's slot freed on park.)
  P2  that progress is REAL, not phantom: Y's merged sha is a genuine trunk
      ancestor — real code landed on trunk around the parked case.
  P3  the mechanism is exact: X (parked) IS in `casestate.dispatch_excluded_
      blocks`, Y is NOT — only the parked block is hidden from dispatch, never a
      bystander.

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)` and every line,
exits non-zero on any fail.
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
import gitobs                           # noqa: E402 — core/gitobs.py, the ONE git-observation seam
import intake                           # noqa: E402 — core/intake.py, the private per-agent door (rig-side write)
import casestate                        # noqa: E402 — core/casestate.py, dispatch_excluded_blocks (the 2b-6 mechanism)
from engine import Engine               # noqa: E402 — core/engine.py, the module under drive

import architect as core_architect       # noqa: E402 — core/architect.py, ARCHITECT_WID
import scaffold as sim_scaffold          # noqa: E402 — core/sim/scaffold.py
import worker as sim_worker              # noqa: E402 — core/sim/worker.py, ScriptedDriver + Transcript

MAIN = "main"

# The four invariants covered by an existing dedicated rig, mapped to the file
# `scripts/l1.sh` discovers and runs in THIS same gate (see module docstring).
_COVERAGE_MAP = {
    "2b-1 (fleet-outage self-recovery)": "core/outage_rig.py",
    "2b-2 (concurrent-landing truth race)": "core/trunkchurn_rig.py",
    "2b-4 (spawn failure counted/budgeted/cased)": "core/outage_rig.py",
    "2b-5 (slow != dead)": "core/liveness_working_rig.py",
}

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


def _l1_discovery_globs():
    """The EXACT rig-discovery globs `scripts/l1.sh` uses (`core/*_rig.py`
    and `core/sim/*_rig.py`) — read here so the coverage map asserts genuine
    membership in the live L1 gate, never a hand-copied file list that could
    drift from what l1.sh actually runs."""
    import glob
    files = set(glob.glob(os.path.join(APP_ROOT, "core", "*_rig.py")))
    files |= set(glob.glob(os.path.join(APP_ROOT, "core", "sim", "*_rig.py")))
    return {os.path.relpath(f, APP_ROOT) for f in files}


# ══════════════════════════════════════════════════════════════════════════
# 2b-3 — record integrity: a withheld (off-trunk) record commit never records
# done; a landed sibling does.
# ══════════════════════════════════════════════════════════════════════════
R3_CONTROL = "03-01"   # lands its record commit normally -> records done
R3_TARGET = "03-02"    # its record land is WITHHELD -> commit stays off trunk
R3_BLOCKS = [
    {"id": R3_CONTROL, "depends_on": [], "reviewer_class": "none",
     "title": "double(x): a small real function (record LANDS — positive control)"},
    {"id": R3_TARGET, "depends_on": [], "reviewer_class": "none",
     "title": "triple(x): a small real function (record commit WITHHELD from trunk)"},
]
R3_MAX_TICKS = 60


def _drive_record_integrity():
    """Drive a real Engine over two independent, both-CORRECT blocks. A
    `sim_worker.try_land` wrapper WITHHOLDS only R3_TARGET's RECORD land (its
    ✅ commit is authored on its branch but never lands on trunk); every other
    land — both merges, the control's record — proceeds normally. Mirrors
    `core/sim/trunk_blame_rig.py::_drive`'s own manual boot/tick/observe/
    spawn-stub shape."""
    ctx, root = sim_scaffold.build(R3_BLOCKS)
    driver = sim_worker.ScriptedDriver(root, ctx.grants_dir, ctx,
                                       sim_worker.default_transcript())

    real_try_land = sim_worker.try_land

    def _selective_try_land(r, grants_dir, case_id, branch):
        # A RECORD-stage land for the target's branch is refused — its ✅
        # commit stays off trunk. `landing.stage_case_id` stamps the stage
        # into the case id ("record"/"merge"), so this keys on the case id +
        # branch, never a fragile tick count.
        if branch == f"feat/{R3_TARGET}" and "record" in case_id:
            return False
        return real_try_land(r, grants_dir, case_id, branch)

    sim_worker.try_land = _selective_try_land
    real_spawn_runner = jobs.spawn_runner
    jobs.spawn_runner = lambda *a, **k: {}
    try:
        eng = Engine(ctx)
        eng.dry = False
        eng.start(scope="all", worker_count=2, models={})
        session_ended_tick = None
        i = -1
        for i in range(R3_MAX_TICKS):
            res = eng.tick()
            manifest = state.load(ctx)
            driver.record_done_ticks(i, res.get("outcomes") or {})
            driver.react(i, manifest)
            if res.get("session_end") is not None:
                session_ended_tick = i
                break
        final = state.load(ctx)
        return {
            "root": root, "ctx": ctx, "events": list(eng.events.log),
            "gates": final.get("gates") or {}, "session_ended_tick": session_ended_tick,
            "ticks_used": i + 1,
        }
    finally:
        sim_worker.try_land = real_try_land
        jobs.spawn_runner = real_spawn_runner


# ══════════════════════════════════════════════════════════════════════════
# 2b-6 — post-close dispatch: an open operator-owned case on X never halts
# dispatch of an independent block Y.
# ══════════════════════════════════════════════════════════════════════════
P6_X = "04-01"   # deliberately broken -> escalates -> parked operator case
P6_Y = "04-02"   # independent, correct -> must still dispatch + make progress
P6_BLOCKS = [
    {"id": P6_X, "depends_on": [], "reviewer_class": "none",
     "title": "double(x): DELIBERATELY BROKEN -> parked operator case"},
    {"id": P6_Y, "depends_on": [], "reviewer_class": "none",
     "title": "triple(x): independent, CORRECT -> dispatches around the parked case"},
]
P6_MAX_TICKS = 90

_P6_BROKEN = (
    '"""app/lib/04-01.py — double(x), DELIBERATELY BROKEN (identity, never '
    'fixed) — genuinely fails the mockup\'s real declared test on trunk."""\n\n'
    "def double(x):\n"
    "    return x   # BUG: should be x * 2\n\n\n"
    "def check():\n"
    "    return double(21) == 42\n"
)
_P6_OK = (
    '"""app/lib/04-02.py — triple(x), a small real, CORRECT function."""\n\n'
    "def triple(x):\n"
    "    return x * 3\n\n\n"
    "def check():\n"
    "    return triple(7) == 21 and triple(0) == 0\n"
)


class _OperatorVerdictDriver(sim_worker.ScriptedDriver):
    """The happy-path driver, plus: answer the architect's triage turn with a
    real routed verdict='operator' the instant a triage job is ordered —
    forcing X's case to genuinely reach + stay owned by the operator (the
    parked case 2b-6 needs standing open). Identical in spirit to
    `core/sim/trunk_blame_rig.py`'s own driver (kept local so this rig is
    self-contained — no cross-rig coupling)."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._triage_answered = set()

    def react(self, i, manifest):
        super().react(i, manifest)
        arch = manifest.get("architect") or {}
        cur = arch.get("current_job") or {}
        if cur.get("kind") != "triage" or not cur.get("ordered"):
            return
        tid = cur.get("triage_id")
        if not tid or tid in self._triage_answered:
            return
        intake.write(self.tron_ctx, core_architect.ARCHITECT_WID,
                     {"tag": "architect.triage_verdict",
                      "agent_id": core_architect.ARCHITECT_WID,
                      "slots": {"triage_id": tid, "verdict": "operator"}})
        self._triage_answered.add(tid)


def _drive_post_close_dispatch():
    """worker_count=1 (naturally sequential dispatch): X dispatches first,
    escalates to a parked operator case, frees the slot — and Y must then
    dispatch WHILE X's case is still open. `dispatch_excluded_blocks` sampled
    each tick so the hide/allow set is observed live, not just at the end."""
    ctx, root = sim_scaffold.build(P6_BLOCKS)
    transcript = sim_worker.default_transcript(overrides={
        P6_X: ("app/lib/04-01.py", _P6_BROKEN),
        P6_Y: ("app/lib/04-02.py", _P6_OK),
    })
    driver = _OperatorVerdictDriver(root, ctx.grants_dir, ctx, transcript)

    real_spawn_runner = jobs.spawn_runner
    jobs.spawn_runner = lambda *a, **k: {}
    excluded_history = []   # (tick, frozenset(dispatch_excluded_blocks))
    try:
        eng = Engine(ctx)
        eng.dry = False
        eng.start(scope="all", worker_count=1, models={})
        i = -1
        for i in range(P6_MAX_TICKS):
            res = eng.tick()
            manifest = state.load(ctx)
            excluded_history.append((i, frozenset(casestate.dispatch_excluded_blocks(manifest))))
            driver.record_done_ticks(i, res.get("outcomes") or {})
            driver.react(i, manifest)
            if res.get("session_end") is not None:
                break
        final = state.load(ctx)
        return {
            "root": root, "ctx": ctx, "events": list(eng.events.log),
            "gates": final.get("gates") or {}, "cases": final.get("cases") or {},
            "excluded_history": excluded_history, "ticks_used": i + 1,
        }
    finally:
        jobs.spawn_runner = real_spawn_runner


def main():
    # ══════════════════════════════════════════════════════════════════════
    # 2b-1 / 2b-2 / 2b-4 / 2b-5 — COVERAGE MAP (existing dedicated proofs,
    # guaranteed to run green in this SAME l1.sh gate).
    # ══════════════════════════════════════════════════════════════════════
    discovered = _l1_discovery_globs()
    for invariant, rig_rel in _COVERAGE_MAP.items():
        on_disk = os.path.isfile(os.path.join(APP_ROOT, rig_rel))
        in_l1 = rig_rel in discovered
        ok(f"COVERAGE {invariant}: its dedicated proof {rig_rel} exists AND is "
           f"in scripts/l1.sh's own discovery glob (runs green in THIS gate)",
           on_disk and in_l1,
           f"on_disk={on_disk} in_l1_discovery={in_l1}")

    # ══════════════════════════════════════════════════════════════════════
    # 2b-3 — record integrity (driven here)
    # ══════════════════════════════════════════════════════════════════════
    r3 = _drive_record_integrity()
    ev3 = r3["events"]

    def _recorded(block):
        return any(e["type"] == "gate_recorded" and e["payload"].get("block") == block
                   for e in ev3)

    control_status = _doc_on_main(r3["root"], R3_CONTROL)
    target_status = _doc_on_main(r3["root"], R3_TARGET)
    g_control = r3["gates"].get(R3_CONTROL) or {}
    g_target = r3["gates"].get(R3_TARGET) or {}

    ok("2b-3 R2 (POSITIVE CONTROL — must be GREEN): the sibling block whose "
       "record commit LANDED records done normally (gate_recorded fired, gate "
       "CLOSED, ✅ Done on main) — the mechanism is not broken for all",
       _recorded(R3_CONTROL) and g_control.get("stage") == gate.STAGE_CLOSED
       and "✅ Done" in control_status,
       f"recorded={_recorded(R3_CONTROL)} stage={g_control.get('stage')!r} "
       f"status_has_done={'✅ Done' in control_status}")

    ok("2b-3 R1 (RECORD INTEGRITY, THE KILLER — must be GREEN): the block whose "
       "✅ record commit was WITHHELD from trunk NEVER records done — no "
       "gate_recorded event, gate never CLOSED, doc on main not ✅ Done — the "
       "✅ is earned by real trunk observation, never the off-trunk commit's "
       "mere existence",
       not _recorded(R3_TARGET)
       and g_target.get("stage") != gate.STAGE_CLOSED
       and "✅ Done" not in target_status,
       f"recorded={_recorded(R3_TARGET)} stage={g_target.get('stage')!r} "
       f"status_has_done={'✅ Done' in target_status}")

    # R3 — the withheld ✅ commit genuinely EXISTS off trunk (on the branch,
    # NOT a main ancestor).
    target_branch = f"feat/{R3_TARGET}"
    branch_tip = gitobs.tip_sha(r3["root"], target_branch, False)
    branch_touch = gitobs.last_touching_sha(r3["root"], target_branch, f"meta/blocks/{R3_TARGET}.md")
    main_touch = gitobs.last_touching_sha(r3["root"], MAIN, f"meta/blocks/{R3_TARGET}.md")
    off_trunk = bool(branch_touch) and branch_touch != main_touch \
        and not gitobs.is_ancestor(r3["root"], branch_touch, MAIN, False)
    ok("2b-3 R3 (THE OFF-TRUNK COMMIT IS REAL — must be GREEN): the withheld "
       "block's ✅ record commit genuinely EXISTS on its branch and is NOT a "
       "trunk ancestor — proving R1 is the real 'a commit of that block exists "
       "outside the trunk' condition, not a block that never authored one",
       off_trunk,
       f"branch_touch={str(branch_touch)[:8]} main_touch={str(main_touch)[:8]} "
       f"branch_tip={str(branch_tip)[:8]} off_trunk={off_trunk}")

    # ══════════════════════════════════════════════════════════════════════
    # 2b-6 — post-close dispatch (driven here)
    # ══════════════════════════════════════════════════════════════════════
    r6 = _drive_post_close_dispatch()
    ev6 = r6["events"]

    def _first_idx(pred):
        return next((idx for idx, e in enumerate(ev6) if pred(e)), None)

    x_escalated_idx = _first_idx(lambda e: e["type"] == "case_escalated_to_operator"
                                 and e["payload"].get("block") == P6_X)
    y_merged_idx = _first_idx(lambda e: e["type"] == "gate_merged"
                              and e["payload"].get("block") == P6_Y)
    ok("2b-6 P1 (POST-CLOSE DISPATCH, THE KILLER — must be GREEN): with X's "
       "operator case OPEN, the INDEPENDENT block Y keeps advancing — Y's own "
       "code reaches a real trunk MERGE (gate_merged) AFTER X's case is "
       "escalated-to-operator; the open operator case did NOT halt Y's progress",
       x_escalated_idx is not None and y_merged_idx is not None
       and y_merged_idx > x_escalated_idx,
       f"x_escalated_idx={x_escalated_idx} y_merged_idx={y_merged_idx}")

    # P2 — Y's merge is a GENUINE trunk landing (its branch tip is a real main
    # ancestor), not a phantom "merged" event — the dispatch that continued
    # around the parked case produced real trunk state.
    y_gate = r6["gates"].get(P6_Y) or {}
    y_merged_sha = y_gate.get("merged_sha")
    y_on_trunk = bool(y_merged_sha) and gitobs.is_ancestor(r6["root"], y_merged_sha, MAIN, False)
    ok("2b-6 P2 (REAL PROGRESS, NOT PHANTOM — must be GREEN): Y's merged sha is "
       "a genuine trunk ancestor (real code landed on trunk) — the dispatch that "
       "continued around X's parked case produced real trunk state, never a "
       "hollow advance",
       y_on_trunk, f"y_merged_sha={str(y_merged_sha)[:8]} on_trunk={y_on_trunk}")

    # X's case is genuinely still open at end (never settled) — the "open case"
    # premise the whole invariant rests on.
    x_case_open = any(c.get("block") == P6_X and c.get("owner") == "operator"
                      and c.get("decision") is None for c in r6["cases"].values())
    # P3 — the exclusion is exact: at some tick X (parked) is excluded while Y
    # is NOT (only the parked block is hidden from dispatch, never a bystander).
    exact_exclusion = any(P6_X in excl and P6_Y not in excl
                          for _, excl in r6["excluded_history"])
    ok("2b-6 P3 (EXACT EXCLUSION — must be GREEN): X's case stayed genuinely "
       "OPEN (owner=operator, undecided) AND casestate.dispatch_excluded_blocks "
       "hid ONLY X (never Y) on at least one tick — only the parked block is "
       "held back, never an independent bystander",
       x_case_open and exact_exclusion,
       f"x_case_open={x_case_open} exact_exclusion={exact_exclusion}")

    ok("test:<invariants_2b_1..6> (AC-7): all six §2b resilience invariants "
       "each hold under one honest proof through the real door — four via their "
       "dedicated rig in this same l1.sh gate (coverage map), 2b-3 + 2b-6 driven "
       "here as real Engine scenarios",
       all(c for _, c, _ in _results))

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.sim.invariants_2b_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return 0 if passed == len(_results) else 1


def _doc_on_main(root, block):
    """`meta/blocks/<block>.md`'s content as read FROM `main` (the ✅-Done
    verdict source of truth). A missing file (a block never landed to trunk)
    yields '' — never a crash."""
    import subprocess
    r = subprocess.run(["git", "-C", root, "show", f"{MAIN}:meta/blocks/{block}.md"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


if __name__ == "__main__":
    sys.exit(main())
