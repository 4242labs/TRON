"""block_01_32_test — merge inversion T1: worker close rituals (ADR-0002 D1+D2).

Per-AC coverage this session reaches (block doc `blocks/01-32-merge-inversion.md`);
T2/T3 (git wrapper, truth-ref rekeying, detached root, scratch bootstrap, grants,
land.sh, hook, verify_docs, mutation-arm deletion) are NOT covered here — see the PR
body / final report for exactly what remains out of scope this session.

  AC-2 test:clobber_dead — the wave-1b stale-branch pipeline clobber cannot land stale
       content: `trunk.merge_ff_only`'s 01-17 auto-rebase-and-retry arm is retired
       (a real-git proof: a first ff-refusal is NEVER silently rebased, conflict-free
       or not — trunk stays untouched); the FSM gate never blind-retries a held
       approval once a rebase has been ordered (only a FRESH `on_report` — the
       worker's rebase-then-re-validate ritual, reported — re-enters the merge
       attempt); a worker that genuinely cannot resolve it walls to the architect
       WITH content (not silently accepted, not corrupted, not a bare operator page).

Run: python3 engine/block_01_32_test.py   (exit 0 = pass). No tokens, no network for
the FSM cases; the real-git case shells out to a throwaway `git init` repo, same
convention as block_01_17_test.py/tron13_test.py.
"""
import os
import sys
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

os.environ["TRON_DRY"] = "1"

import trunk                                            # noqa: E402
from fsm import Engine                                   # noqa: E402
from sentry_test import build, started                   # noqa: E402

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))


# ── real-git fixture (block_01_17_test/tron13_test convention) ──
def _git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _mkrepo(prefix="tron-0132-"):
    d = tempfile.mkdtemp(prefix=prefix)
    _git(d, "init", "-q", "-b", "main")
    _git(d, "config", "user.email", "t@t")
    _git(d, "config", "user.name", "t")
    os.makedirs(os.path.join(d, "meta"))
    with open(os.path.join(d, "meta", "pipeline.md"), "w") as fh:
        fh.write("| A-01 | to-do |\n| A-02 | to-do |\n")
    _git(d, "add", "-A")
    _git(d, "commit", "-qm", "base")
    return d


# ── AC-2 (real git): the wave-1b shape itself — a stale close-out branch cut before
# another block's row landed would REVERT it if silently merged/rebased by the engine ──
def t_clobber_dead_real_git():
    d = _mkrepo()
    # The soon-to-close worker's branch, cut from base: touches ONLY its own row.
    _git(d, "checkout", "-qb", "feat/a-02")
    with open(os.path.join(d, "meta", "pipeline.md"), "w") as fh:
        fh.write("| A-01 | to-do |\n| A-02 | done |\n")
    _git(d, "commit", "-aqm", "A-02 done")
    _git(d, "checkout", "-q", "main")
    # Meanwhile A-01 landed on trunk FIRST — trunk's pipeline.md now differs from the
    # closer's pre-image on the SAME file (the exact wave-1b shape: a non-ff on a
    # shared, small paperwork file).
    with open(os.path.join(d, "meta", "pipeline.md"), "w") as fh:
        fh.write("| A-01 | done |\n| A-02 | to-do |\n")
    _git(d, "add", "-A")
    _git(d, "commit", "-qm", "A-01 done")
    okm, err = trunk.merge_ff_only(d, "feat/a-02", "main")
    ok("AC-2 clobber_dead: the stale close-out branch is REFUSED, never silently "
       "rebased-and-landed", okm is False, f"err={err}")
    trunk_content = open(os.path.join(d, "meta", "pipeline.md")).read()
    ok("AC-2 clobber_dead: trunk's A-01 row is untouched — no revert, ever",
       "A-01 | done" in trunk_content)
    ok("AC-2 clobber_dead: no rebase was ever attempted on trunk's behalf (no residue)",
       not os.path.exists(os.path.join(d, ".git", "rebase-merge"))
       and not os.path.exists(os.path.join(d, ".git", "rebase-apply")))
    shutil.rmtree(d, ignore_errors=True)


# ── FSM-level: the DONE ritual around a non-ff, real git under a dry engine ──
def _eng(block="A-01"):
    ctx, _ = build(blocks=[(block, "🔄", "none")])
    eng = Engine(ctx); started(eng)
    eng.st.workers.append({"id": "ENG-" + block, "role": "engineer", "block": block,
                           "session_id": "dry", "status": "working"})
    eng.st.branches[block] = f"feat/{block}"
    return eng


def _stub(exists=True, ff_sequence=None):
    """ff_sequence: a list of (ok, err) tuples, one consumed per merge_ff_only call
    (the last value repeats once exhausted) — models the worker's branch state
    changing (or not) across successive rebase attempts."""
    calls = {"n": 0}
    seq = list(ff_sequence or [(False, "not a fast-forward")])

    def _merge(*a, **k):
        i = min(calls["n"], len(seq) - 1)
        calls["n"] += 1
        return seq[i]

    trunk.branch_exists = lambda *a, **k: exists
    trunk.merge_ff_only = _merge
    return calls


def t_non_ff_orders_rebase_not_wall():
    orig = (trunk.branch_exists, trunk.merge_ff_only)
    _stub()
    try:
        eng = _eng()
        g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
        eng._drive_gate("A-01", g)                      # -> local (first pass)
        eng._drive_gate("A-01", g, on_report=True)       # ff refused
        ok("AC-2 non-ff: stays at local (worker's ritual, not an engine wall)",
           g.get("stage") == "local")
        ok("AC-2 non-ff: rebase_pending is set (the ordered ritual step)",
           g.get("rebase_pending") is True)
        ok("AC-2 non-ff: no case/wall raised — the worker gets first crack at it",
           not eng.st.pending_cases)
    finally:
        trunk.branch_exists, trunk.merge_ff_only = orig


def t_held_approval_never_retries_without_fresh_report():
    # ASK mode: an operator "approve" grant must never let a BARE idle tick retry the
    # merge once a rebase has been ordered — only a fresh on_report (the worker's
    # reported rebase + re-validate) may re-enter the merge attempt. This is the
    # concrete fsm.py fix (01-32 T1): `elif on_report or (approved_merge and not
    # rebase_pending):` — the direct behavioral proof that a held grant alone can't
    # silently re-drive git state nobody re-validated.
    orig = (trunk.branch_exists, trunk.merge_ff_only)
    calls = _stub()
    try:
        eng = _eng()
        eng.st.approvals["merge"] = "ASK"
        g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
        eng._drive_gate("A-01", g)                      # -> local
        eng._drive_gate("A-01", g, on_report=True)       # evidence -> ASK parks a case
        cid = next(c for c in eng.st.pending_cases)
        eng._h_apply_decision({"case": cid, "decision": "approve", "block": "A-01"})
        ok("setup: approve grants approved_merge", g.get("approved_merge") is True)
        n_before = calls["n"]
        ok("setup: the grant's own merge attempt hit the non-ff refusal, rebase ordered",
           g.get("rebase_pending") is True and n_before >= 1)
        # A bare tick — NOT a fresh report — must not call merge_ff_only again.
        eng._drive_gate("A-01", g)
        ok("AC-2 grant crash-safety: a bare idle tick never re-attempts the merge while "
           "a rebase is pending (no blind retry on stale/unreviewed git state)",
           calls["n"] == n_before, f"calls before={n_before} after={calls['n']}")
        ok("AC-2 grant crash-safety: the gate is still at local, not trunk — nothing "
           "landed behind the worker's back", g.get("stage") == "local")
    finally:
        trunk.branch_exists, trunk.merge_ff_only = orig


def t_fresh_report_after_rebase_lands():
    # The happy path this whole ritual exists for: the worker rebases + re-validates in
    # its OWN worktree (never TRON), then reports done again — THAT fresh on_report is
    # what re-drives the merge attempt, and only then.
    orig = (trunk.branch_exists, trunk.merge_ff_only)
    calls = _stub(ff_sequence=[(False, "not a fast-forward"), (True, "")])
    try:
        eng = _eng()
        g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
        eng._drive_gate("A-01", g)                      # -> local
        eng._drive_gate("A-01", g, on_report=True)       # ff refused -> rebase ordered
        ok("setup: rebase ordered after the first refusal", g.get("rebase_pending") is True)
        # A bare tick still must not retry (same invariant as above).
        eng._drive_gate("A-01", g)
        ok("AC-2: idle ticks between the order and the worker's fresh report never retry",
           calls["n"] == 1)
        # The worker's fresh report — rebase done, re-validated — re-enters the merge.
        eng._drive_gate("A-01", g, on_report=True)
        ok("AC-2: the fresh on_report re-attempts the merge (worker-owned resolution)",
           calls["n"] == 2)
        ok("AC-2: it lands -> re-validate on trunk (rebase_pending cleared)",
           g.get("stage") == "trunk" and not g.get("rebase_pending"))
    finally:
        trunk.branch_exists, trunk.merge_ff_only = orig


def t_unresolvable_rebase_walls_architect_with_content():
    # The worker keeps reporting done, but the branch never actually becomes
    # fast-forwardable (an unfinishable rebase, e.g. a conflict it can't resolve) —
    # this must NEVER hang forever and NEVER silently corrupt trunk. It walls, with
    # real content, and (per block 01-31, ADR-0002 D2) routes to the architect FIRST,
    # never straight to the operator.
    orig = (trunk.branch_exists, trunk.merge_ff_only)
    _stub()   # every attempt refuses — the worker can never land it
    try:
        eng = _eng()
        arch = {"id": "ARCH-PERSIST", "role": "architect", "session_id": "dry",
               "status": "idle", "current_job": None, "block": None, "mbox_seq": 0}
        eng.st.workers.append(arch)
        g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
        clock = {"t": 1000.0}
        eng._now_s = lambda: clock["t"]
        eng._drive_gate("A-01", g)                      # -> local
        eng._drive_gate("A-01", g, on_report=True)       # ff refused -> rebase ordered
        eng._tq = []
        eng._drive_gate("A-01", g)                       # anchor idle_since at 'local'
        clock["t"] += eng._pace("gate_idle_cap", 3) + 1  # past the idle cap
        eng._drive_gate("A-01", g)
        eng._drain_triggers()
        case = next((c for cid, c in eng.st.pending_cases.items()
                    if c.get("block") == "A-01"), None)
        ok("AC-2: an unresolvable rebase walls (never a silent hang, never a corrupt land)",
           case is not None and "A-01" not in eng.st.gate, f"case={case} gate={eng.st.gate}")
        ok("AC-2: the wall CARRIES content (never a contentless placeholder)",
           bool(case and case.get("detail")), f"case={case}")
        ok("AC-2: it dispatches the architect first — never a direct operator page "
           "(ADR-0002 D2, 01-31)",
           (arch.get("current_job") or {}).get("kind") == "triage"
           and (arch.get("current_job") or {}).get("case") is not None, f"arch={arch}")
    finally:
        trunk.branch_exists, trunk.merge_ff_only = orig


def main():
    for fn in (t_clobber_dead_real_git, t_non_ff_orders_rebase_not_wall,
              t_held_approval_never_retries_without_fresh_report,
              t_fresh_report_after_rebase_lands,
              t_unresolvable_rebase_walls_architect_with_content):
        fn()
    bad = [r for r in _results if not r[1]]
    for name, good, detail in _results:
        print(f"  [{'PASS' if good else 'FAIL'}] {name}" + (f" — {detail}" if detail and not good else ""))
    print(f"block_01_32_test: {'PASS' if not bad else 'FAIL'} ({len(_results)-len(bad)}/{len(_results)})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
