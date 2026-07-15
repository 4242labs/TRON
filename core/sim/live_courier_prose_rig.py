"""core.sim.live_courier_prose_rig — block 01-38 T19: non-vacuous lock for
`core/sim/live.py::_courier`'s new `prose` knob (`run_live(courier_prose=...)`
/ the live CLI's `--courier-prose`), the fix for the T19 live-run killer:
the courier used to scrape a real agent's raw turn-narration into that
agent's own intake as an UNTAGGED report every loop. `core.classify` is
structured-only (`worker-contract.md` §2, block 01-37/ADR-0012) — an
untagged, unbranched line has no verb to resolve, so `core.door.refuse`
records it and opens an architect-first `door_refusal` case EVERY time. A
real LLM turn always produces turn-text, so that scrape manufactured an
endless refuse -> architect-triage -> re-dispatch churn out of ordinary
narration ("FYI — online, standing by") — `gate.local` never opened. This
rig proves, against the REAL engine (real `casestate.open_case`/`core.door`/
`core.classify`, nothing about that pipeline re-mocked):

  PROSE-ON  (`prose=True`, the historical default every scripted `core/sim/
            *_rig.py` drive still relies on): the exact same turn-narration
            text, harvested by `_courier`, DOES open a `door_refusal` case —
            the failure mode this knob exists to suspend, reproduced here as
            the mutation baseline (not asserted as desirable, asserted as
            the PRIOR behavior a straight read of `_courier`'s old docstring
            promised, so PROSE-OFF's contrast is meaningful).
  PROSE-OFF (`prose=False`, the live host-cli run's own new default): the
            IDENTICAL turn-narration text, sitting in the SAME worker's
            `timeline.jsonl`, produces ZERO intake delivery and ZERO case —
            genuine silence, not a suppressed refusal. Then, in the SAME
            fixture, a REAL `scripts/report.sh --tag wall` subprocess
            invocation (the INDEPENDENT structured path `core/sim/
            report_channel_rig.py` already locks end to end, never routed
            through `_courier`) still lands and still drives the gate — a
            genuine `wall` case opens, proving report.sh is untouched by the
            suspension and remains the ONLY way an agent moves engine state.

Non-vacuous by construction: PROSE-ON and PROSE-OFF run the SAME scripted
turn-narration text through the SAME courier call, differing only in the
one boolean under test — flipping it flips the outcome (INJ-style mutation
proof, mirroring `core/sim/live_fleet_outage_injection_rig.py`'s own ON/OFF
shape for H2b).

Reuses `core/outage_rig.py`'s proven real-git fixture builders (scaffold +
pipeline + roles + project.yaml + knobs.yaml) as a LIBRARY — nothing about
that scaffold machinery is re-derived here — plus `core/sim/seed_canon.
install_canon` (this rig is the first to need a REAL `scripts/report.sh` on
top of an `outage_rig` fixture) and drives the REAL `core.engine.Engine`
directly (no `run_live` wall-clock loop needed — this proves the courier
knob + the pipeline it feeds, not the live driver's pacing, which `core/sim/
live_fleet_outage_injection_rig.py` and `core/sim/verdict_sealed_rig.py`
already cover their own ground on).

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)`, exits
non-zero on any fail.
"""
import json
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))            # core/sim
_CORE_DIR = os.path.dirname(_HERE)                              # core
_APP_ROOT = os.path.dirname(_CORE_DIR)                            # tron-app worktree root
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
sys.path.insert(0, _ENGINE_DIR)
sys.path.insert(0, _CORE_DIR)
sys.path.insert(0, _HERE)

from ctx import Ctx                     # noqa: E402 — engine/ctx.py
from engine import Engine                # noqa: E402 — core/engine.py, real bootup/tick, unedited
import jobs                                # noqa: E402 — engine/jobs.py, the ONE process-spawn seam stubbed
import state                                # noqa: E402 — core/state.py
import intake                                # noqa: E402 — core/intake.py, intake_path for the report.sh call
import outage_rig                              # noqa: E402 — core/outage_rig.py, REUSED as a library:
                                               # scaffold builders (real git fixture) — never re-derived here.
from seed_canon import install_canon             # noqa: E402 — core/sim/seed_canon.py, real report.sh + schema
import live                                        # noqa: E402 — core/sim/live.py, unit under test (_courier)

_results = []

_TEXT = ("FYI — online, standing by, everything looks good so far. "
         "This is ordinary turn-narration, never a --tag report.")


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


def _fake_spawn_stub():
    """The ONE process-spawn seam this rig stubs — writes a genuinely-ALIVE
    `runner.json` (`pid=os.getpid()` — always alive for the rig's own
    lifetime, so `jobs.is_alive` never flags a fleet death and this rig's
    ticks stay confined to proving the courier/classify/door pipeline, never
    confounded by unrelated liveness churn) instead of spawning a real
    process — the SAME no-real-process idiom `core/outage_rig.py`'s own
    `make_spawn_stub`/`core/sim/live_fleet_outage_injection_rig.py`'s
    `_noop_spawn_stub` use, specialized to report itself alive rather than
    silent (no OTHER rig needs a self-reporting-alive stub, so it lives
    here, not lifted into `outage_rig` itself)."""
    def _fake(worker_id, worker_dir, session_id, cwd=None, runtime=None,
             adapter=None, model=None, settle_s=2.0):
        os.makedirs(worker_dir, exist_ok=True)
        with open(os.path.join(worker_dir, jobs.RUNNER_STATE), "w") as fh:
            json.dump({"session_id": session_id, "state": "idle",
                      "pid": os.getpid(), "turns": 1,
                      "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, fh)
    return _fake


def _build_fixture(tag):
    """One block, one worker, a REAL `scripts/report.sh` installed on top of
    `outage_rig`'s proven real-git scaffold (this rig is the first `core/
    sim/live_*_rig.py` to need the real script, not just the engine-side
    intake/classify/door pipeline it feeds)."""
    BLOCKS = ["cr-1"]
    root = outage_rig.build_root(tag)
    outage_rig.seed_pipeline(root, BLOCKS)
    outage_rig.seed_roles(root)
    inst = os.path.join(root, "meta", "agents", "tron")
    outage_rig.write_project_yaml(inst, root)
    outage_rig.write_knobs(inst, worker_count=1)   # huge silence thresholds by default —
                                                    # no liveness ping/escalate noise in a
                                                    # handful of ticks
    install_canon(inst)   # scripts/report.sh + vocab.schema.json — the structured path's
                          # own real subprocess target
    return root, inst, BLOCKS


def _boot(inst, blocks):
    """Boot a real `Engine`, dispatch the single worker (process-spawn
    stubbed alive, never really launched). Returns `(ctx, eng, wid)`."""
    real_spawn_runner = jobs.spawn_runner
    jobs.spawn_runner = _fake_spawn_stub()
    try:
        ctx = Ctx(inst)
        eng = Engine(ctx)
        eng.dry = False   # HARD RULE: real trunk observation throughout
        eng.start(scope="all", worker_count=len(blocks), models={})
    finally:
        jobs.spawn_runner = real_spawn_runner
    manifest = state.load(ctx)
    wid = next(iter(manifest.get("workers") or {}))
    return ctx, eng, wid


def _write_prose_turn(ctx, wid, text, seq=1):
    """Simulate a real `worker_runner.py`'s OWN `turn_done` timeline write —
    the EXACT shape `engine/worker_runner.py:412` produces after a real
    `claude` turn, never a synthetic courier-only shape — for a worker whose
    process was stubbed (never really spawned, so no real runner ever wrote
    this itself)."""
    wdir = ctx.worker_dir(wid)
    os.makedirs(wdir, exist_ok=True)
    tl = os.path.join(wdir, jobs.TIMELINE)
    with open(tl, "a") as fh:
        fh.write(json.dumps({"event": "turn_done", "seq": seq, "text": text}) + "\n")


def _door_refusal_case(manifest):
    for c in (manifest.get("cases") or {}).values():
        if c.get("kind") == "door_refusal":
            return c
    return None


def _wall_case(manifest):
    for c in (manifest.get("cases") or {}).values():
        if c.get("kind") == "wall":
            return c
    return None


def main():
    # ══ PROSE-ON — the mutation BASELINE: the historical scrape, prose=True ══
    root_on, inst_on, blocks_on = _build_fixture("courierprose-on")
    ctx_on, eng_on, wid_on = _boot(inst_on, blocks_on)
    _write_prose_turn(ctx_on, wid_on, _TEXT)

    delivered_on = set()
    n_on = live._courier(eng_on, state.load(ctx_on), delivered_on, prose=True)
    ok("ON1: _courier(prose=True) DELIVERED the turn-narration to the worker's "
       "own intake (the historical scrape, unchanged for every direct caller "
       "that omits the new argument)",
       n_on == 1, f"delivered={n_on}")

    for _ in range(5):
        eng_on.tick()
    manifest_on = state.load(ctx_on)
    refusal_on = _door_refusal_case(manifest_on)
    ok("ON2 (THE MUTATION BASELINE — must be GREEN): with prose scraping ON, "
       "ordinary turn-narration ('FYI — online, standing by') genuinely opens "
       "a real `door_refusal` case via the REAL classify/door pipeline — this "
       "IS the endless refuse->triage->re-dispatch churn the knob exists to "
       "suspend, reproduced here as the baseline PROSE-OFF must contrast "
       "against",
       refusal_on is not None,
       f"cases={manifest_on.get('cases')}")

    # ══ PROSE-OFF — the live host-cli run's own new default, prose=False ══
    root_off, inst_off, blocks_off = _build_fixture("courierprose-off")
    ctx_off, eng_off, wid_off = _boot(inst_off, blocks_off)
    _write_prose_turn(ctx_off, wid_off, _TEXT)   # THE IDENTICAL text ON used

    delivered_off = set()
    n_off = live._courier(eng_off, state.load(ctx_off), delivered_off, prose=False)
    ok("OFF1: _courier(prose=False) delivered NOTHING — genuine silence, not "
       "a suppressed/queued delivery",
       n_off == 0, f"delivered={n_off}")

    for _ in range(5):
        eng_off.tick()
    manifest_off = state.load(ctx_off)
    refusal_off = _door_refusal_case(manifest_off)
    ok("OFF2 (THE NON-VACUITY KILLER — must be GREEN): the SAME turn-"
       "narration text that opened a door_refusal case under ON opens NO "
       "case at all under OFF — proves ON2's case-open is provably the "
       "courier's OWN doing (flip the switch, the prose WOULD create a case "
       "again — ON2/OFF2 differ in nothing but the one boolean under test)",
       refusal_off is None,
       f"cases={manifest_off.get('cases')}")
    ok("OFF3: zero cases of ANY kind exist yet — the suspension is total "
       "silence, not merely 'no door_refusal specifically'",
       not (manifest_off.get("cases") or {}),
       f"cases={manifest_off.get('cases')}")

    # Still fixture OFF: the SAME worker now files a REAL structured report —
    # the independent path, never routed through _courier at all.
    ipath = intake.intake_path(ctx_off, wid_off)
    script = os.path.join(inst_off, "scripts", "report.sh")
    r = subprocess.run(["bash", script, "--intake", ipath, wid_off,
                        "--tag", "wall", "a genuine blocker, filed correctly"],
                       capture_output=True, text=True)
    ok("REP1: the real `report.sh --tag wall` subprocess exited 0 (accepted "
       "at the script's own door, independent of the courier's prose knob "
       "entirely)",
       r.returncode == 0, f"rc={r.returncode} stderr={r.stderr!r}")

    for _ in range(5):
        eng_off.tick()
    manifest_after_report = state.load(ctx_off)
    wall_case = _wall_case(manifest_after_report)
    ok("REP2 (THE STRUCTURED PATH SURVIVES — must be GREEN): a real "
       "`report.sh --tag wall` STILL lands and STILL drives the gate — a "
       "genuine `wall` case opens on the worker's real durable block binding "
       "— with prose suspension ACTIVE the whole time. report.sh was never "
       "routed through `_courier`; suspending the scrape does not touch it",
       wall_case is not None and wall_case.get("block") == blocks_off[0],
       f"cases={manifest_after_report.get('cases')}")

    ok("test:<courier_prose_suspension> (T19): flipping `_courier`'s `prose` "
       "argument on the IDENTICAL turn-narration flips the outcome (ON opens "
       "a door_refusal case, OFF opens none), while a real `report.sh --tag` "
       "call lands and opens a real case regardless — the live host-cli "
       "run's new default makes an agent's turn output genuinely invisible "
       "to the engine without touching the structured intake path at all",
       n_on == 1 and refusal_on is not None
       and n_off == 0 and refusal_off is None
       and not (manifest_off.get("cases") or {})
       and r.returncode == 0 and wall_case is not None)

    n_pass = sum(1 for _, c, _ in _results if c)
    n_total = len(_results)
    for name, cond, detail in _results:
        mark = "PASS" if cond else "FAIL"
        print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not cond else ""))
    print(f"live_courier_prose_rig: PASS ({n_pass}/{n_total})")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    sys.exit(main())
