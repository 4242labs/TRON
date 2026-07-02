"""tron13_test — regressions for the tron-13 pre-sim implementation set (the co-signed
design of record: tron-meta logs/engineer/260702-tron-13-design.md).

  D3/A-5  full ladder ratchet — trunk AND record are a monotonic hold zone; the held
          rung re-verifies its OWN predicate (merged sha ancestry / merged PR staying
          closed) and a contradicted predicate is a NAMED gate-contradiction escalation,
          never a silent recompute and never a "worker stall" misread.

Run: python3 engine/tron13_test.py   (exit 0 = pass). No tokens, no network.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

os.environ["TRON_DRY"] = "1"

import trunk            # noqa: E402
import jobs             # noqa: E402
import util             # noqa: E402
from fsm import Engine  # noqa: E402
from sentry_test import build, started  # noqa: E402


def _events(eng):
    return util.read_jsonl(eng.ctx.event_log)

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))


def _eng(blocks=None, block="A-01"):
    ctx, repo = build(blocks=blocks)
    eng = Engine(ctx)
    started(eng)
    eng.st.workers.append({"id": "ENG-" + block, "role": "engineer", "block": block,
                           "session_id": "dry", "status": "working"})
    return eng


def _capture(eng):
    sent = []
    orig = eng.emit
    eng.emit = (lambda tid, slots=None, worker_id=None:
                sent.append((tid, dict(slots or {}))) or orig(tid, slots, worker_id))
    return sent


# ── D3/A-5: the ladder ratchet ──
def t_ratchet_floor_paperwork_commits():
    # The W1 floor case, now with the anchored predicate: paperwork commits move the
    # branch tip (branch_merged goes false) but the MERGED sha stays an ancestor —
    # the gate holds quietly, no contradiction, no regression, no duplicate orders.
    eng = _eng()
    g = eng.st.gate.setdefault("A-01", {"stage": "trunk", "pr": None,
                                        "merged_sha": "abc1234"})
    sent = _capture(eng)
    orig_bm, orig_be, orig_ia = trunk.branch_merged, trunk.branch_exists, trunk.is_ancestor
    trunk.branch_merged = lambda *a, **k: False          # tip moved (paperwork commits)
    trunk.branch_exists = lambda *a, **k: True
    trunk.is_ancestor = lambda *a, **k: True             # merged sha still in history
    try:
        eng._drive_gate("A-01", g)
        ok("A-5 paperwork commits: trunk holds on merged-sha ancestry",
           g.get("stage") == "trunk", f"stage={g.get('stage')}")
        ok("A-5 paperwork commits: no gate-contradiction raised",
           not any(t.startswith("wall:raised") or t == "escalate.gate" for t, _ in sent)
           and "A-01" in eng.st.gate, f"sent={sent}")
        ok("A-5 paperwork commits: no duplicate DONE-LOCAL",
           not any(t == "gate.local" for t, _ in sent), f"sent={sent}")
    finally:
        trunk.branch_merged, trunk.branch_exists, trunk.is_ancestor = (
            orig_bm, orig_be, orig_ia)


def t_ratchet_record_holds():
    # record is inside the hold zone too: a plain tick never recomputes it downward.
    eng = _eng()
    g = eng.st.gate.setdefault("A-01", {"stage": "record", "pr": None,
                                        "merged_sha": "abc1234"})
    sent = _capture(eng)
    orig_bm, orig_ia = trunk.branch_merged, trunk.is_ancestor
    trunk.branch_merged = lambda *a, **k: False
    trunk.is_ancestor = lambda *a, **k: True
    try:
        eng._drive_gate("A-01", g)
        ok("A-5 record holds on a plain tick", g.get("stage") == "record",
           f"stage={g.get('stage')}")
        ok("A-5 record hold sends no stage order",
           not any(t.startswith("gate.") for t, _ in sent), f"sent={sent}")
    finally:
        trunk.branch_merged, trunk.is_ancestor = orig_bm, orig_ia


def t_ratchet_ancestry_contradiction():
    # History surgery (force-push / reset): the merged sha vanishes from trunk history —
    # a NAMED gate-contradiction escalation, never a quiet hold, never a stall misread.
    eng = _eng()
    g = eng.st.gate.setdefault("A-01", {"stage": "trunk", "pr": None,
                                        "merged_sha": "abc1234"})
    sent = _capture(eng)
    orig_ia = trunk.is_ancestor
    trunk.is_ancestor = lambda *a, **k: False
    try:
        eng._drive_gate("A-01", g)
        ok("A-5 broken ancestry drops the gate", "A-01" not in eng.st.gate,
           f"gate={eng.st.gate}")
        fails = [e for e in _events(eng) if e.get("kind") == "failure"]
        ok("A-5 broken ancestry raises a named contradiction",
           any(e.get("code") == "gate-contradiction"
               and "no longer in trunk history" in (e.get("cause") or "")
               for e in fails),
           f"fails={fails}")
        ok("A-5 contradiction failure is code gate-contradiction",
           any(e.get("code") == "gate-contradiction" for e in fails),
           f"fails={fails}")
    finally:
        trunk.is_ancestor = orig_ia


def t_ratchet_pr_reopened_contradiction():
    # Remote mode: the merged PR shows OPEN again (revert + reopen) while the gate holds
    # at trunk — affirmative regression evidence, escalates as gate-contradiction.
    eng = _eng()
    eng.st.workers[0]["branch"] = "feat/a-01"
    eng.st.branches["A-01"] = "feat/a-01"
    eng.st.open_prs["feat/a-01"] = {"number": 7, "checks": "passing"}
    g = eng.st.gate.setdefault("A-01", {"stage": "trunk", "pr": 7,
                                        "merged_sha": "abc1234"})
    sent = _capture(eng)
    orig_ia = trunk.is_ancestor
    trunk.is_ancestor = lambda *a, **k: True             # revert keeps ancestry; the PR is the tell
    try:
        eng._drive_gate("A-01", g)
        ok("A-5 reopened PR drops the gate", "A-01" not in eng.st.gate,
           f"gate={eng.st.gate}")
        fails = [e for e in _events(eng) if e.get("kind") == "failure"]
        ok("A-5 reopened PR raises a named contradiction naming the PR",
           any(e.get("code") == "gate-contradiction" and "#7" in (e.get("cause") or "")
               for e in fails),
           f"fails={fails}")
    finally:
        trunk.is_ancestor = orig_ia


def t_ratchet_no_sha_holds_quietly():
    # No anchored sha (e.g. remote-merged branch unresolvable locally): the predicate is
    # unknowable — hold quietly (R-3's giveup detail covers diagnosis at the idle cap).
    eng = _eng()
    g = eng.st.gate.setdefault("A-01", {"stage": "trunk", "pr": None})
    orig_ia = trunk.is_ancestor
    trunk.is_ancestor = lambda *a, **k: False            # would contradict IF consulted
    try:
        eng._drive_gate("A-01", g)
        ok("A-5 missing merged sha never fabricates a contradiction",
           g.get("stage") == "trunk" and "A-01" in eng.st.gate,
           f"stage={g.get('stage')}")
    finally:
        trunk.is_ancestor = orig_ia


def t_merge_anchors_sha():
    # The executed local ff-merge anchors the predicate to the EXACT merged tip (A-3's
    # pinned sha), so later paperwork commits can never dislodge it.
    eng = _eng()
    g = eng.st.gate.setdefault("A-01", {"stage": "local", "pr": None,
                                        "approved_merge": True})
    orig_be, orig_ff, orig_ts = trunk.branch_exists, trunk.merge_ff_only, trunk.tip_sha
    trunk.branch_exists = lambda *a, **k: True
    trunk.merge_ff_only = lambda *a, **k: (True, "")
    trunk.tip_sha = lambda *a, **k: "feedbee1"
    try:
        eng._drive_gate("A-01", g)
        ok("A-5 executed merge anchors merged_sha",
           g.get("stage") == "trunk" and g.get("merged_sha") == "feedbee1",
           f"g={g}")
    finally:
        trunk.branch_exists, trunk.merge_ff_only, trunk.tip_sha = (
            orig_be, orig_ff, orig_ts)


TESTS = [
    t_ratchet_floor_paperwork_commits,
    t_ratchet_record_holds,
    t_ratchet_ancestry_contradiction,
    t_ratchet_pr_reopened_contradiction,
    t_ratchet_no_sha_holds_quietly,
    t_merge_anchors_sha,
]


def main():
    for t in TESTS:
        t()
    failed = [(n, d) for n, c, d in _results if not c]
    for n, c, d in _results:
        print(("PASS " if c else "FAIL ") + n + (f"  [{d}]" if (d and not c) else ""))
    print(f"{len(_results) - len(failed)}/{len(_results)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
