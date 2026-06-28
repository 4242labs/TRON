"""git_test — the 01-05 merge + git hygiene acceptance suite (AC-1 … AC-3).

Deterministic, token-free (TRON_DRY): no git, no spawn, no LLM. Reuses sentry_test's
fixture builders (a throwaway TRON dir + a fixture canon repo) and drives the engine's
deterministic merge-gate units directly. Exit 0 only if every case passes.

Covers:
  AC-1  two-gate merge sequencing (staging APPROVED -> promote ASK) vs single-gate merge_main
  AC-2  agent-owned branch: TRON resolves the PR by the worker-REPORTED name, never feat/<block>
  AC-3  git-hygiene contract surfaced to the worker (pull/rebase-before-push in the brief)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

os.environ["TRON_DRY"] = "1"

from fsm import Engine                       # noqa: E402
from sentry_test import build, started, events  # noqa: E402

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))


def _eng(staging="none", block="A-01"):
    """An engine with one engineer on `block`, optionally two-gate (staging set)."""
    ctx, _ = build(blocks=[(block, "📋", "none")])
    eng = Engine(ctx); started(eng)
    eng.paths["staging"] = staging
    eng.st.workers.append({"id": "ENG-" + block, "role": "engineer", "block": block,
                           "session_id": "dry", "status": "working"})
    return eng


# ── AC-2: the agent owns + names its branch; TRON resolves the PR by that name ──
def t_branch_ownership():
    eng = _eng()
    named = "fix/widget-overflow-260628"        # NOT the feat/<block> convention
    eng._ingest("worker.branch", {"block": "A-01", "branch": named}, {"id": "ENG-A-01"})
    ok("AC-2 worker.branch records the worker-named branch",
       eng.st.branches.get("A-01") == named)
    ok("AC-2 branch is NOT a guessed feat/<block>", named != eng._branch("A-01"))

    # A PR exists ONLY under the reported name. The gate must find it there (not feat/A-01).
    eng.st.data["open_prs"] = {named: {"number": 11, "checks": "passing"}}
    g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
    eng._drive_gate("A-01", g)
    ok("AC-2 gate resolves the PR via the reported branch -> merge",
       g["stage"] == "merge" and g.get("pr") == 11)

    # Control: a PR under the GUESSED name with NO report is ignored (TRON never guesses).
    eng2 = _eng(block="A-02")
    eng2.st.data["open_prs"] = {"feat/A-02-wrongguess": {"number": 9, "checks": "passing"}}
    g2 = eng2.st.gate.setdefault("A-02", {"stage": None, "pr": None})
    eng2._drive_gate("A-02", g2)
    ok("AC-2 unreported branch -> no guess, stays validate-local",
       g2["stage"] == "validate-local")


# ── AC-1: single-gate repo uses one merge step (merge_main), not the two-gate path ──
def t_single_gate():
    eng = _eng(staging="none")
    eng.st.branches["A-01"] = "feat/A-01"
    eng.st.data["open_prs"] = {"feat/A-01": {"number": 7, "checks": "passing"}}
    g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
    eng._drive_gate("A-01", g)
    ok("AC-1 single-gate: CI green -> one merge step (merge_main)", g["stage"] == "merge")
    ok("AC-1 single-gate raised no merge-gate case", not eng.st.pending_cases)


# ── AC-1: two-gate sequencing — staging APPROVED -> promote ASK ──
def t_two_gate():
    eng = _eng(staging="staging")
    eng.st.branches["A-01"] = "feat/A-01"

    # Gate 1: feature PR CI green. merge_staging defaults APPROVED -> TRON instructs the merge.
    eng.st.data["open_prs"] = {"feat/A-01": {"number": 7, "checks": "passing"}}
    g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
    eng._drive_gate("A-01", g)
    last = events(eng.ctx)[-1]
    ok("AC-1 gate1 = merge-staging (APPROVED, auto-instructed)", g["stage"] == "merge-staging")
    ok("AC-1 gate1 instruction targets staging", "-> staging" in last)
    ok("AC-1 gate1 (APPROVED) opens no operator case", not eng.st.pending_cases)

    # Gate 2: feature PR merged to staging (gone). promote_main defaults ASK -> hold + escalate.
    eng.st.data["open_prs"] = {}
    n_before = len(events(eng.ctx))
    eng._drive_gate("A-01", g)
    ok("AC-1 gate2 = promote-main", g["stage"] == "promote-main")
    promote_cases = [c for c in eng.st.pending_cases.values() if c.get("kind") == "promote_main"]
    ok("AC-1 gate2 (ASK) parks an operator case", len(promote_cases) == 1)
    ok("AC-1 gate2 escalates to the operator (escalate.gate)",
       any("Merge gate" in t for t in events(eng.ctx)))
    ok("AC-1 gate2 does NOT promote before the operator says so",
       not any("-> main" in t for t in events(eng.ctx)[n_before:]))

    # Operator go-ahead (resume the case) -> TRON now instructs the promotion.
    case_id = next(cid for cid, c in eng.st.pending_cases.items()
                   if c.get("kind") == "promote_main")
    eng._h_apply_decision({"case": case_id, "decision": "resume", "block": "A-01"})
    ok("AC-1 resume grants the gate", eng.st.gate["A-01"].get("approved_promote_main") is True)
    ok("AC-1 resume closes the case", case_id not in eng.st.pending_cases)
    ok("AC-1 after go-ahead, TRON instructs promote staging -> main",
       any("-> main" in t for t in events(eng.ctx)))


# ── AC-1: an ASK staging gate also holds (the knob is honoured both ways) ──
def t_staging_ask_holds():
    eng = _eng(staging="staging")
    eng.st.branches["A-01"] = "feat/A-01"
    eng.st.approvals["merge_staging"] = "ASK"     # operator wants to gate even the staging merge
    eng.st.data["open_prs"] = {"feat/A-01": {"number": 7, "checks": "passing"}}
    g = eng.st.gate.setdefault("A-01", {"stage": None, "pr": None})
    eng._drive_gate("A-01", g)
    ok("AC-1 ASK staging gate holds (no merge instruction)",
       not any("-> staging" in t for t in events(eng.ctx)))
    ok("AC-1 ASK staging gate parks a case",
       any(c.get("kind") == "merge_staging" for c in eng.st.pending_cases.values()))


# ── AC-3: the git-hygiene contract reaches the worker (pull/rebase + branch ownership) ──
def t_hygiene_surface():
    eng = _eng()
    brief = eng._handover("engineer", "A-01")
    ok("AC-3 brief tells the agent to name + report its own branch",
       "report" in brief.lower() and "branch" in brief.lower()
       and "feat/A-01" not in brief)             # no dictated name
    pmt = open(os.path.join(ROOT, "prompts", "PMT-ENG-BRIEF.md")).read().lower()
    ok("AC-3 PMT-ENG-BRIEF mandates pull/rebase before push",
       "rebase" in pmt and "push" in pmt)


def main():
    for t in (t_branch_ownership, t_single_gate, t_two_gate,
              t_staging_ask_holds, t_hygiene_surface):
        t()
    bad = [r for r in _results if not r[1]]
    for name, good, detail in _results:
        print(f"  [{'PASS' if good else 'FAIL'}] {name}" + (f" — {detail}" if detail and not good else ""))
    print(f"git_test: {'PASS' if not bad else 'FAIL'} ({len(_results)-len(bad)}/{len(_results)})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
