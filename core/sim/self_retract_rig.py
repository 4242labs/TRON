"""core.sim.self_retract_rig — the T8 door fixture (block 01-38, AC-13):
`test:<self_retract_own_block_clean_end>`.

Historically the SINGLE biggest clean-run killer (2 of 6 runs, paper-test
ledger row 15): a worker raised its OWN block over a transient snag, cleared
the snag itself, and then had NO word/handler/ledger row to say so — the case
sat open and the run never reached a clean end.

This is a FULL-FLOW door fixture (not a unit call): a real block is driven
through the REAL door end to end — the worker raises its OWN `worker.wall`
(via its private intake, the same channel `scripts/report.sh --intake` writes,
the SAME mechanism `core/sim/sim_l2_rig.py`'s own workers use), then withdraws
it with a real `worker.wall_retract`, and the run is driven to a genuine clean
session-end. The bar (AC-13, operator-set) is NOT "the retract was accepted":
it is that the OWN block **closes on trunk with ZERO operator pages across its
whole lifecycle** and the run completes clean.

The retract is NEVER trusted at face value (block 01-38's root invariant): it
routes the block back to a re-drivable gate stage and the ordinary gate ladder
RE-PROVES it on trunk (`casestate.self_retract` -> `_drop_gate_and_worker` ->
fresh spawn -> gate.local..close). The TRUNK VERDICT, not the retract, is what
closes the block — so this proof genuinely exercises the whole re-drive-to-
close path, never a face-value dismissal.

Asserted off the events-as-single-ground-truth stream (`eng.events.log`, T7)
— never the advisory flow-log:
  R1  the worker's OWN wall opened a real parked case (`case_opened`,
      source="worker.wall", the worker's own id) — the scenario genuinely
      raised its own block, not a no-op.
  R2  a real `worker.wall_retract` drained through the door and SELF-RETRACTED
      that exact case (`case_self_retracted`, decision "self_retracted", the
      worker's own id) — exactly one, for the worker's own case.
  R3  ZERO operator pages / escalations for the WHOLE run — no
      `operator_page`, no `engine_operator_page_recorded`, no
      `case_escalated_to_operator`, no `case_page_permfailed` anywhere in the
      event stream (the retract cleared the wall before any human was ever
      paged — the zero-pages guarantee, structural via the owner=="architect"
      no-take-back guard).
  R4  the OWN block RE-DRIVED and CLOSED on trunk (gate CLOSED, ✅ Done as read
      FROM main) — the retract returned it to normal dispatch and the gate
      ladder re-proved it, never a face-value close.
  R5  a genuine clean session-end fired (durable, re-read off disk) — the run
      completed clean, the historical killer genuinely gone.
  M1  MUTATION PROOF (non-vacuity): a SECOND drive of the IDENTICAL scenario
      with the retract SUPPRESSED (the worker walls but never withdraws it)
      does NOT reach a clean session-end within the same tick budget and the
      block never closes — proving R3/R4/R5 above are the retract's own doing,
      not a scenario that would have closed regardless.

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)` and every
line, exits non-zero on any fail.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # core/sim
CORE_DIR = os.path.dirname(HERE)                             # core
APP_ROOT = os.path.dirname(CORE_DIR)                         # worktree root
ENGINE_DIR = os.path.join(APP_ROOT, "engine")
# engine dir first, then core dir — core must win the bare name "engine"
# (shadowing engine/engine.py's CLI) so `from engine import Engine` below
# resolves to core/engine.py. Same ordering core/sim/run.py establishes.
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

MAIN = "main"
TARGET_BLOCK = "01-01"
BLOCKS = [{"id": TARGET_BLOCK, "depends_on": [], "reviewer_class": "none",
           "title": "double(x): a small real function"}]

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


def _git_out(args, cwd):
    r = subprocess.run(["git", "-C", cwd] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} (cwd={cwd}) rc={r.returncode}\n{r.stderr}")
    return r.stdout.strip()


class _WallRetractDriver(sim_worker.ScriptedDriver):
    """The happy-path `ScriptedDriver`, but for `target_block` it injects,
    through the REAL private-intake door, a self-raised `worker.wall` the
    first tick the block sits at `gate.local`, then a `worker.wall_retract`
    the tick that wall's own case is open — after which the block re-drives
    and super's own ladder carries the FRESH spawn to a clean close.

    `retract` (ctor flag): when False, the wall is raised but NEVER withdrawn
    — the M1 non-vacuity drive, proving the clean close is the retract's doing.

    Mechanism: while the wall is unresolved, `local_reported[target]` is held
    True so super never sends the target's `worker.done` (it is walling, not
    passing); the moment the retract is sent that suppression is lifted and
    the per-block tracking reset, so super drives the re-dispatched fresh
    worker through the ordinary gate.local..close ladder unchanged. Every
    OTHER block (none here, but the shape stays general) is driven by super
    verbatim."""

    def __init__(self, *a, target_block, retract=True, **k):
        super().__init__(*a, **k)
        self.target_block = target_block
        self.retract_enabled = retract
        self.wall_sent_tick = None
        self.retract_sent_tick = None
        self._wall_sent = False
        self._retract_sent = False
        self._triage_answered = set()   # triage_ids already answered

    def react(self, i, manifest):
        super().react(i, manifest)
        self.react_architect_triage(i, manifest)

    def react_architect_triage(self, i, manifest):
        """Play the architect's triage turn, exactly as
        `react_architect_reconcile`/`react_architect_log` play its reconcile/
        log turns: once the architect has ORDERED a `triage` job, reply with a
        real routed `architect.triage_verdict` so the job completes via the
        report (never left to stall on the stubbed architect's undelivered
        mailbox and trip the no-progress budget — a pure SIM artifact of not
        running a real architect process; a live architect consumes its own
        order, so this models that consumption faithfully).

        Deliberately answered ONLY AFTER the worker's retract has been sent
        (`_retract_sent`): the retract clears the case FIRST, so this benign
        `answer` verdict then no-ops on the already-cleared case
        (`architect_resolve`'s own unknown/settled-case guard) — the RETRACT
        is unambiguously what resolved the wall, never the architect. `answer`
        is chosen because it never pages even in the (here impossible) event
        the case were still open."""
        if not self._retract_sent:
            return
        arch = manifest.get("architect") or {}
        cur = arch.get("current_job") or {}
        if cur.get("kind") != "triage" or not cur.get("ordered"):
            return
        tid = cur.get("triage_id")
        if not tid or tid in self._triage_answered:
            return
        intake.write(self.tron_ctx, core_architect.ARCHITECT_WID,
                     {"tag": "architect.triage_verdict", "agent_id": core_architect.ARCHITECT_WID,
                      "slots": {"triage_id": tid, "verdict": "answer"}})
        self._triage_answered.add(tid)

    def react_engineers(self, i, manifest):
        b = self.target_block
        workers = manifest.get("workers") or {}
        gates = manifest.get("gates") or {}
        cases = manifest.get("cases") or {}
        wid = next((aid for aid, w in workers.items()
                    if aid.startswith("engineer-") and w.get("block") == b), None)

        # While our own wall is unresolved, suppress super's target-block
        # `worker.done` (the block is WALLING, not passing) by pre-marking it
        # reported. Lifted the instant the retract is sent (below), so the
        # re-driven fresh worker sends a genuine `worker.done` normally.
        if not self._retract_sent:
            self.local_reported[b] = True

        super().react_engineers(i, manifest)

        g = gates.get(b)
        stage = g.get("stage") if g else None

        # PHASE 1 — raise our OWN wall exactly once, the first tick the block
        # sits at gate.local with its branch authored (super's spawning arm
        # created the branch + sent worker.online already).
        if (not self._wall_sent and wid and stage == gate.STAGE_LOCAL
                and self.branch_created.get(b)):
            intake.write(self.tron_ctx, wid,
                         {"tag": "worker.wall", "block": b,
                          "slots": {"detail": "transient local snag — clearing it "
                                              "myself, will self-retract"}})
            self._wall_sent = True
            self.wall_sent_tick = i
            return

        # PHASE 2 — withdraw it once, the tick our own wall's case is open
        # (unless retract is disabled — the M1 non-vacuity drive).
        if self.retract_enabled and self._wall_sent and not self._retract_sent:
            own_open = any(c.get("worker_id") == wid
                           and c.get("source") == "worker.wall"
                           and c.get("decision") is None
                           for c in cases.values())
            if own_open and wid:
                intake.write(self.tron_ctx, wid, {"tag": "worker.wall_retract"})
                self._retract_sent = True
                self.retract_sent_tick = i
                # Lift the done-suppression and reset per-block tracking so
                # super re-drives the FRESH spawn through the full ladder.
                self.local_reported[b] = False
                self.branch_created[b] = False
                self.spawn_tick.pop(b, None)


def _drive(retract, max_ticks=80):
    """Seed a fresh real-git mockup for the single target block, boot
    core.engine.Engine, and drive it with `_WallRetractDriver` to a clean
    session-end (or `max_ticks`). Mirrors core/sim/run.py's own boot/tick/
    observe/spawn-stub shape (no real worker process, real trunk observation
    throughout). Returns a structured result dict."""
    ctx, root = sim_scaffold.build(BLOCKS)
    driver = _WallRetractDriver(root, ctx.grants_dir, ctx,
                                sim_worker.default_transcript(),
                                target_block=TARGET_BLOCK, retract=retract)

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
        eng.start(scope="all", worker_count=1, models={})

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
                     "case_escalated_to_operator", "case_page_permfailed"}


def main():
    # ══════════════════════════════════════════════════════════════════════
    # Primary drive — wall then RETRACT, must reach a clean close, zero pages.
    # ══════════════════════════════════════════════════════════════════════
    r = _drive(retract=True)
    events = r["events"]
    driver = r["driver"]

    def _of(type_):
        return [e for e in events if e["type"] == type_]

    # R1 — the worker genuinely raised its OWN wall (a real parked case).
    own_walls = [e for e in _of("case_opened")
                 if e["payload"].get("source") == "worker.wall"]
    ok("R1: the worker raised its OWN block — exactly one worker.wall case was "
       "opened (the scenario genuinely walled its own block, not a no-op)",
       len(own_walls) == 1 and own_walls[0]["payload"].get("block") == TARGET_BLOCK,
       f"case_opened(worker.wall)={[e['payload'] for e in own_walls]} "
       f"wall_sent_tick={driver.wall_sent_tick}")

    # R2 — a real wall_retract self-retracted exactly that case.
    retracts = _of("case_self_retracted")
    ok("R2: a real worker.wall_retract drained through the door and "
       "SELF-RETRACTED exactly one case for the worker's OWN block "
       "(decision 'self_retracted') — tightened to identity + payload",
       len(retracts) == 1
       and retracts[0]["payload"].get("block") == TARGET_BLOCK
       and retracts[0]["payload"].get("worker_id") == f"engineer-{TARGET_BLOCK}",
       f"case_self_retracted={[e['payload'] for e in retracts]} "
       f"retract_sent_tick={driver.retract_sent_tick}")

    # R2b — causal order: the retract event comes AFTER the wall's own case_opened.
    types_seq = [e["type"] for e in events]
    ok("R2b: causal order — case_self_retracted appears AFTER the "
       "case_opened it withdraws (a retract can only follow a raised wall)",
       "case_opened" in types_seq and "case_self_retracted" in types_seq
       and types_seq.index("case_self_retracted") > types_seq.index("case_opened"),
       f"first case_opened@{types_seq.index('case_opened') if 'case_opened' in types_seq else None} "
       f"self_retracted@{types_seq.index('case_self_retracted') if 'case_self_retracted' in types_seq else None}")

    # R3 — ZERO operator pages / escalations across the WHOLE run.
    page_events = [e for e in events if e["type"] in _PAGE_EVENT_TYPES]
    ok("R3 (THE ZERO-PAGES KILLER — must be GREEN): NOT ONE operator page / "
       "escalation event fired across the whole run (no operator_page / "
       "engine_operator_page_recorded / case_escalated_to_operator / "
       "case_page_permfailed) — the retract cleared the wall before any human "
       "was ever paged, the zero-pages guarantee holding structurally",
       len(page_events) == 0,
       f"page_events={[e['type'] for e in page_events]}")

    # R4 — the OWN block re-drived and CLOSED on trunk (the retract re-proved it).
    g = r["gates"].get(TARGET_BLOCK) or {}
    doc_head = []
    try:
        doc_head = _git_out(["show", f"{MAIN}:meta/blocks/{TARGET_BLOCK}.md"],
                            r["root"]).splitlines()[:4]
    except Exception:   # noqa: BLE001 — a missing/unreadable doc is itself the failure
        doc_head = []
    ok("R4 (RE-PROVED, NOT FACE-VALUE CLOSED — must be GREEN): the OWN block "
       "re-drived after the retract and CLOSED on trunk (gate CLOSED, ✅ Done "
       "as read FROM main) — the trunk verdict closed it, never the retract",
       g.get("stage") == gate.STAGE_CLOSED
       and any("✅ Done" in ln for ln in doc_head),
       f"stage={g.get('stage')!r} doc_head={doc_head}")

    # R5 — a genuine clean session-end (durable).
    se = r["session_end"] or {}
    ok("R5 (CLEAN SESSION-END — must be GREEN): the run reached a genuine "
       "clean session-end (durable, re-read off disk) — the historical "
       "biggest clean-run killer is gone",
       r["session_ended_tick"] is not None and se.get("ended_at") is not None
       and "reason" in se,
       f"session_ended_tick={r['session_ended_tick']} session_end={se} "
       f"ticks_used={r['ticks_used']}")

    # ══════════════════════════════════════════════════════════════════════
    # M1 — MUTATION PROOF: the IDENTICAL scenario with the retract SUPPRESSED
    # does NOT reach a clean close — proving R3/R4/R5 are the retract's doing.
    # ══════════════════════════════════════════════════════════════════════
    r2 = _drive(retract=False)
    g2 = r2["gates"].get(TARGET_BLOCK) or {}
    ok("M1 (MUTATION PROOF — non-vacuity): the IDENTICAL scenario with the "
       "retract SUPPRESSED (the worker walls but never withdraws) does NOT "
       "reach a clean session-end and the block does NOT close — proving "
       "R3/R4/R5 are the retract's OWN doing, not a run that would have "
       "closed regardless",
       r2["session_ended_tick"] is None and g2.get("stage") != gate.STAGE_CLOSED,
       f"session_ended_tick={r2['session_ended_tick']} "
       f"target_stage={g2.get('stage')!r} ticks_used={r2['ticks_used']}")

    # M1b — and that suppressed drive genuinely walled (so M1 isn't vacuous
    # for the OPPOSITE reason — a scenario that never walled at all).
    walled2 = [e for e in r2["events"] if e["type"] == "case_opened"
               and e["payload"].get("source") == "worker.wall"]
    ok("M1b: the suppressed drive genuinely DID raise the wall (so M1's "
       "no-clean-close is the UNwithdrawn wall holding the run open, never a "
       "scenario that failed to wall in the first place)",
       len(walled2) >= 1
       and not any(e["type"] == "case_self_retracted" for e in r2["events"]),
       f"walls={len(walled2)} retracts={sum(1 for e in r2['events'] if e['type']=='case_self_retracted')}")

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.sim.self_retract_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
