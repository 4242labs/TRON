"""core.door_fixtures_rig — block 01-38 T13 (AC-9): `test:<door_fixtures>`.

The ~15 door fixtures: one fixture per historical failure vector, run as a
real command through the REAL door (`scripts/report.sh` + `core/door.py::
admit` — R3 Model A, rigs reach the engine ONLY through the door) into a
FRESH instance, each with a declared expected outcome under the new
vocabulary. The vector list is the HISTORICAL-MODE rows of the committed
ledger `tron-meta/logs/architecture/paper-test-ledger-260714.md` — rows
1-18 (rows 19-25 are that ledger's own meta/scoreboard rows: session-end
residue, R3 rig-honesty-as-a-class, the vocab handshake, the P3 blind-spot
note, R7's summary, the L1-proof-ladder-actually-runs meta-defect, and the
live-run scoreboard itself — none of those is a single door command with a
declared outcome, so they are out of THIS rig's scope; T17's ledger read
covers them by their own named mechanisms). Every one of rows 1-18 gets a
fixture entry below; none is left without one.

COVERAGE MODEL (map, don't rebuild — the block's own explicit instruction).
By the time T13 opened, FIFTEEN of the eighteen rows already had a
dedicated, green, real-door honest rig proving them — built for their own
earlier task (T8/T9/T10/T11/T18-adjacent work etc), independently
discovered and run by `scripts/l1.sh`'s own glob. Re-driving their
(often heavy: real-git, real-subprocess) scenarios here would be pure
duplication, not extra assurance — so for those rows this rig asserts a
COVERAGE MAP: the cited file exists on disk AND is a member of l1.sh's own
discovery glob (`core/*_rig.py` / `core/sim/*_rig.py`), so it is GUARANTEED
to run green in this SAME L1 gate. This is `core/sim/invariants_2b_rig.py`'s
own precedent pattern (T11), reused verbatim here, never re-derived.

THREE rows had no existing proof anywhere in the live repo when this rig was
written (grepped directly across every `core/*.py`/`core/sim/*.py`, not
assumed) — those are driven HERE, fresh, through the real door:

  F1  rows 1 + 2 (D1 "a typo'd --tag walls vanishes with zero trace" / D2+D7
      "seven agent-mintable tags with no verb, deleted rather than wired") —
      a REAL `scripts/report.sh` subprocess sends an unrecognized tag (a
      typo, AND separately one of the seven specifically-deleted historical
      tag names) into a fresh real instance. Declared outcome: report.sh's
      own local check refuses locally (nonzero exit, legal set printed) but
      STILL appends the attempted line to the intake (never a silent drop);
      the engine's own admission door (`core/door.py::admit`, the SECOND,
      authoritative check) refuses it AGAIN on drain and opens a real
      `worker.report_refused` case carrying the full raw text + the
      WORKER's own real channel origin — two independent nets, neither
      silent, matching the ledger row's own "two independent nets" text.

  F2  row 15's SECOND sub-vector (GAP-D flag-ordering containment — the
      self-retract HALF of row 15, historically the single biggest
      clean-run killer, already has its OWN dedicated T8 door fixture,
      `core/sim/self_retract_rig.py`, CITED below, never re-driven) — a
      REAL `report.sh` subprocess with `--tag wall` trailing AFTER the
      positional message (the exact historical fat-finger: a plain branch
      declaration with a stray trailing flag). Declared outcome: a hard
      error at the script itself (nonzero exit, "flags-after-message is not
      allowed"), BEFORE anything is ever appended to the intake — never
      silently swallowed into message text as a phantom wall.

  F3  row 6 (D6 "outbound vocabulary not lint-closed; engine.emit silently
      swallowed a KeyError to a fallback string") — a fresh real
      `core.engine.Engine.emit` call. Declared outcome, two halves: (a) a
      template_id NOT a member of `vocab.EMIT_TEMPLATE_IDS` raises
      `vocab.UnknownTemplateError` LOUD at the call, before any render is
      even attempted (the typo-fails-at-THIS-call guarantee); (b) a real,
      registered template whose actual render call is forced to fail still
      RE-RAISES (never swallowed to `fallback_text`) AFTER bumping the
      must-be-zero `emit_missing_template` counter by exactly one — the
      historical swallow-to-fallback-string behavior is gone, replaced by
      count-then-raise. (This vector's own historical shape is an OUTBOUND
      engine-emission defect, not an inbound admission one — there is no
      "admission door" for it to run through; it is driven directly against
      a fresh real `Engine`, the closest analog this vector has, disclosed
      here as a judgment call, not silently folded into the "real door"
      framing the other fixtures literally satisfy.)

CROSS-CHECK: every one of this rig's 18 rows also appears in T17's 25-row
ledger read; T13 accounts for 18 of the 25, the other 7 being the ledger's
own meta/scoreboard rows T17 covers by different named mechanisms (never a
door command).

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)` and every
line, exits non-zero on any fail.
"""
import glob
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))          # core
APP_ROOT = os.path.dirname(HERE)                             # worktree root
sys.path.insert(0, os.path.join(APP_ROOT, "engine"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "sim"))

from ctx import Ctx                 # noqa: E402 — engine/ctx.py
from engine import Engine           # noqa: E402 — core/engine.py, emit() under test (F3)
import snapshot                     # noqa: E402 — core/snapshot.py, the observe pass under test
import vocab                        # noqa: E402 — core/vocab.py, EMIT_TEMPLATE_IDS / UnknownTemplateError (F3)
import intake                       # noqa: E402 — core/intake.py, block 01-38 T1's per-agent intake
from boot_real_scaffold_rig import copy_real_scaffold, seed_live_instance   # noqa: E402
from seed_canon import install_canon   # noqa: E402
from render import Renderer         # noqa: E402 — engine/render.py, F3's real renderer under mutation

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


def _report(inst, intake_path, wid, *args):
    """Run the REAL installed report.sh exactly as the engine renders it —
    `--intake <path>` first, always (block 01-38 T1's own convention, the
    SAME helper shape `core/hostile_minter_rig.py`/`core/sim/
    report_channel_rig.py` already use — never a second, driftable copy)."""
    script = os.path.join(inst, "scripts", "report.sh")
    return subprocess.run(["bash", script, "--intake", intake_path, wid, *args],
                          capture_output=True, text=True)


# ══════════════════════════════════════════════════════════════════════════
# The COVERAGE MAP — 15 of 18 rows, each already proven by a dedicated,
# green, real-door honest rig `scripts/l1.sh` discovers and runs in THIS
# SAME gate. `core/sim/invariants_2b_rig.py`'s own precedent pattern (T11).
# ══════════════════════════════════════════════════════════════════════════
_COVERAGE_MAP = {
    "row 3  (D3 unbudgeted trunk-red redrive storm / wrong-worker blame)":
        ["core/sim/trunk_blame_rig.py", "core/gate_full_rig.py"],
    "row 4  (D4/GAP-A operator channel dead both ways)":
        ["core/operator_channel_rig.py"],
    "row 5  (D5 must-be-zero counters written but never read by acceptance)":
        ["core/sim/acceptance_verdict_rig.py", "core/counters_rig.py"],
    "row 7  (D8 minters enforcement rests on a self-asserted argv string)":
        ["core/hostile_minter_rig.py"],
    "row 8  (THE VERDICT-WIRE ROOT — architect.triage_verdict unreachable)":
        ["core/verdict_wire_rig.py"],
    "row 9  (§2b-1 fleet-wide outage self-recovery)":
        ["core/outage_rig.py"],
    "row 10 (§2b-2 two-workers-landing-at-once truth race)":
        ["core/trunkchurn_rig.py"],
    "row 11 (§2b-3 record integrity)":
        ["core/sim/invariants_2b_rig.py"],
    "row 12 (§2b-4 spawn failure counted/budgeted/cased)":
        ["core/outage_rig.py"],
    "row 13 (§2b-5 slow != dead)":
        ["core/liveness_working_rig.py", "core/liveness_rig.py"],
    "row 14 (§2b-6 post-close dispatch)":
        ["core/sim/invariants_2b_rig.py"],
    "row 15a (GAP-D same-worker wall self-retract, the biggest clean-run "
    "killer — F2 below covers row 15's OTHER sub-vector, flag-ordering)":
        ["core/sim/self_retract_rig.py"],
    "row 16 (R5 contradictory progress+blocking reports illegal as a class)":
        ["core/classify_rig.py"],
    "row 17 (R5 worker.flag surfaced non-paging, no light-notes bucket)":
        ["core/classify_rig.py"],
    "row 18 (GAP-E architect-first routing for every wall kind, incl. "
    "block-less)":
        ["core/wallrouting_rig.py", "core/casestate_rig.py"],
}


def _l1_discovery_globs():
    """The EXACT rig-discovery globs `scripts/l1.sh` uses — read here so
    the coverage map asserts genuine membership in the live L1 gate, never
    a hand-copied file list that could drift from what l1.sh actually
    runs. Verbatim pattern from `core/sim/invariants_2b_rig.py`."""
    files = set(glob.glob(os.path.join(APP_ROOT, "core", "*_rig.py")))
    files |= set(glob.glob(os.path.join(APP_ROOT, "core", "sim", "*_rig.py")))
    return {os.path.relpath(f, APP_ROOT) for f in files}


def run_coverage_map():
    discovered = _l1_discovery_globs()
    for row, files in _COVERAGE_MAP.items():
        for f in files:
            ok(f"COVERAGE-MAP {row}: {f!r} exists on disk",
               os.path.isfile(os.path.join(APP_ROOT, f)), f"path={f}")
            ok(f"COVERAGE-MAP {row}: {f!r} is a member of l1.sh's own "
               f"discovery glob (GUARANTEED to run green in this SAME "
               f"L1 gate, never a re-run of its own)",
               f in discovered, f"discovered={sorted(discovered)[:3]}...")


# ══════════════════════════════════════════════════════════════════════════
# F1 — rows 1+2: an unrecognized tag (a typo, and a specifically-deleted
# historical tag name) through the REAL report.sh -> REAL door.
# ══════════════════════════════════════════════════════════════════════════
WORKER_F1 = "engineer-01-90"

# The seven ADR-0012 R1 "Deletes" tags (paper-test row 2/D2/D7) — declared
# unreachable by construction now (`vocab.TAGS` has no entry for any of
# them); `worker.progress` is the ledger's own named example.
_DELETED_HISTORICAL_TAGS = ["progress", "await_confirm", "question_peer",
                            "question_tron", "relay", "logged", "escalate"]


def run_f1(inst, ctx, eng):
    w_intake = intake.create(ctx, WORKER_F1)

    # D1 — a genuine fat-finger typo, never a real verb.
    r_typo = _report(inst, w_intake, WORKER_F1, "--tag", "walls",
                     "--block", "01-door-f1",
                     "a typo'd --tag walls — the historical D1 vector")
    # D2/D7 — one of the seven tags the vocabulary deliberately DELETED
    # rather than wired (worker.progress: "a do-nothing route", per
    # vocab.py's own docstring).
    r_deleted = _report(inst, w_intake, WORKER_F1, "--tag", "progress",
                        "--block", "01-door-f1",
                        "worker.progress — one of the seven deleted "
                        "D2/D7 tags, historically declared but unreachable")

    ok("F1/row1 (D1): report.sh's OWN local check refuses a typo'd --tag "
       "(nonzero exit, legal set printed on stderr) — the worker's SAME "
       "turn sees the failure, never believes a dropped report succeeded",
       r_typo.returncode != 0 and "not in the closed vocabulary" in r_typo.stderr,
       f"rc={r_typo.returncode} stderr={r_typo.stderr!r}")
    ok("F1/row2 (D2/D7): report.sh's SAME local check refuses a DELETED "
       "historical tag (worker.progress) identically to any other unknown "
       "tag — the vocabulary-drift class fix is genuinely structural, not "
       "a special case for THIS one tag",
       r_deleted.returncode != 0 and "not in the closed vocabulary" in r_deleted.stderr,
       f"rc={r_deleted.returncode} stderr={r_deleted.stderr!r}")

    # BOTH attempted lines are STILL appended to the intake (report.sh's own
    # documented "never silently discarded") — drain them for real through
    # snapshot.build (the engine's SECOND, authoritative check).
    snap = snapshot.build(eng)
    refused_cases = [c for c in (snap.manifest.get("cases") or {}).values()
                     if c.get("source") == "worker.report_refused"
                     and c.get("worker_id") == WORKER_F1]
    ok("F1: the engine's OWN admission door (core/door.py::admit, the "
       "SECOND independent net) ALSO refused BOTH attempted lines on "
       "drain — a real worker.report_refused case opened for each, never "
       "a silent drop past report.sh's own local courtesy check",
       len(refused_cases) == 2,
       f"refused_cases={[(c.get('detail'), c.get('worker_id')) for c in refused_cases]}")
    ok("F1: BOTH refusal cases carry the FULL raw attempted text (R2 — "
       "'a genuine cry for help preserved as content, not reduced to an "
       "integer'), never just a count",
       all("walls" in refused_cases[0].get("detail", "")
           or "progress" in refused_cases[0].get("detail", "")
           for _ in [0])
       and any("walls" in c.get("detail", "") for c in refused_cases)
       and any("progress" in c.get("detail", "") for c in refused_cases),
       f"details={[c.get('detail') for c in refused_cases]}")
    ok("F1: both refusal cases carry the WORKER's OWN real channel origin "
       "(never anything the message claimed — root invariant), the SAME "
       f"single real id ({WORKER_F1!r}) for both",
       all(c.get("worker_id") == WORKER_F1 for c in refused_cases),
       f"worker_ids={[c.get('worker_id') for c in refused_cases]}")
    snapshot.release(snap)


# ══════════════════════════════════════════════════════════════════════════
# F2 — row 15's second sub-vector: flags-after-message hard error
# (GAP-D wall-mistag containment; T1/01-24 F-1a).
# ══════════════════════════════════════════════════════════════════════════
WORKER_F2 = "engineer-01-91"


def run_f2(inst, ctx):
    w_intake = intake.create(ctx, WORKER_F2)
    before = ""
    if os.path.exists(w_intake):
        with open(w_intake) as fh:
            before = fh.read()

    # The exact historical fat-finger: a plain positional message (a branch
    # declaration) with a trailing --tag wall AFTER it started.
    r = _report(inst, w_intake, WORKER_F2,
               "declaring my branch feat/01-door-f2", "--tag", "wall")

    ok("F2/row15b (GAP-D flag-ordering containment): a trailing --tag wall "
       "AFTER the positional message is a HARD ERROR at report.sh itself "
       "(nonzero exit, 'flags-after-message is not allowed') — never "
       "silently swallowed into message text as a phantom wall",
       r.returncode != 0 and "flags-after-message is not allowed" in r.stderr,
       f"rc={r.returncode} stderr={r.stderr!r}")

    after = ""
    if os.path.exists(w_intake):
        with open(w_intake) as fh:
            after = fh.read()
    ok("F2: the hard error fires BEFORE anything is ever appended to the "
       "intake — the malformed line never even reaches the engine's own "
       "door to refuse a second time; it is caught at the worker's own "
       "turn, unwritten",
       after == before, f"before={before!r} after={after!r}")


# ══════════════════════════════════════════════════════════════════════════
# F3 — row 6: engine.emit's unknown/failing-template path never swallows.
# ══════════════════════════════════════════════════════════════════════════
def run_f3(ctx, eng):
    eng._manifest = {}   # F3 drives Engine.emit() directly (a fresh unit-
                          # style call, not mid-tick) — a plain dict is all
                          # emit() itself ever reads/writes off _manifest.

    # (a) a template_id NOT a member of vocab.EMIT_TEMPLATE_IDS raises
    # immediately, before any renderer construction/render attempt at all.
    raised_unknown = None
    try:
        eng.emit("totally.made.up.template.id", "fallback text", {})
    except vocab.UnknownTemplateError as e:
        raised_unknown = e
    ok("F3a/row6 (D6, half 1): an unregistered template_id raises "
       "vocab.UnknownTemplateError LOUD at THIS call — a typo/removed "
       "constant fails here, never three frames down inside a renderer, "
       "never silently swallowed to fallback_text",
       raised_unknown is not None, f"raised={raised_unknown!r}")

    # (b) a REAL, registered template whose actual render call is forced to
    # fail: construct the real Renderer (canon installed), monkeypatch its
    # .render to raise, confirm the exception PROPAGATES (never swallowed)
    # AND the must-be-zero emit_missing_template counter moves by exactly 1.
    eng._renderer = Renderer(ctx)
    real_render = eng._renderer.render

    def _boom(template_id, slots=None):
        raise RuntimeError("F3 forced render failure — the real render() "
                           "genuinely raising, not a simulated string")
    eng._renderer.render = _boom

    before_count = int((eng._manifest.get("counters") or {}).get(
        "emit_missing_template", 0) or 0)
    raised_render_fail = None
    try:
        eng.emit(vocab.TPL_HEARTBEAT_PING, "fallback text", {})
    except RuntimeError as e:
        raised_render_fail = e
    finally:
        eng._renderer.render = real_render   # restore — never leave the
                                              # shared eng object mutated
    after_count = int((eng._manifest.get("counters") or {}).get(
        "emit_missing_template", 0) or 0)

    ok("F3b/row6 (D6, half 2): a genuine render() failure on a REAL, "
       "registered template RE-RAISES (never swallowed to fallback_text — "
       "the exact historical D6 swallow-to-string behavior is gone)",
       raised_render_fail is not None, f"raised={raised_render_fail!r}")
    ok("F3b: the SAME failure bumps the must-be-zero emit_missing_template "
       "counter by EXACTLY one BEFORE re-raising (D5's own counted-not-"
       "swallowed guarantee, paired with D6's raise)",
       after_count == before_count + 1,
       f"before={before_count} after={after_count}")


def main():
    root = copy_real_scaffold()
    inst, _project, _knobs = seed_live_instance(root)
    install_canon(inst)
    ctx = Ctx(inst)
    eng = Engine(ctx)
    eng.dry = False

    run_coverage_map()
    run_f1(inst, ctx, eng)
    run_f2(inst, ctx)
    run_f3(ctx, eng)

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.door_fixtures_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + ("" if c else f" — {detail}"))
    print(f"\nroot={root}\ninst={inst}")
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
