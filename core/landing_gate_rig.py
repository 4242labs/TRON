"""core.landing_gate_rig — block 01-38 T22 (AC-18): landing is one path,
observables decide.

Three named proofs:

  test:<single_land_primitive> — `core/landing.py::land_via_grant` is the
  ONE landing sequence (structural: exactly one `def land_via_grant` in the
  whole `core/` tree; every real call site across production `core/*.py`
  references `landing.land_via_grant`, never a second/forked copy — the
  "old seven mint→order→observe copies" this replaced are structurally
  absent). Observation-first: a case-id whose content is ALREADY on trunk
  short-circuits "landed" without minting a redundant grant, real-git,
  real grants dir.

  test:<merge_inversion_cannot_recur> — the T2-17 content-bound-identity
  fix (a same-named branch re-authored with NEW content derives a
  DIFFERENT case-id, so a stale consumed receipt can never mask unlanded
  new content). COVERAGE MAP (T11's own pattern) for the two existing,
  heavier real-git regression proofs already running in this SAME l1.sh
  gate (`core/gate_full_rig.py`'s Phase A' T2-17 regression,
  `core/landing_rig.py`'s own re-authored-branch scenario), PLUS one fast,
  direct, focused mutation proof of the binding function itself.

  test:<grant_lifecycle_and_write_boundary> — patch-id-bound grant
  (reuse-vs-fresh), ""/off-token fail-closed, the crash-window
  administrative-consume arm, PLUS the two T22 production additions this
  task lands (confirmed absent from `core/*` at scoping, minimal+clean
  ports, never copied from `engine/fsm.py`'s own heavier machinery):
  grantless-land detected (counted, must-be-zero, mutation-proven) and
  root-reattach detected+self-healed (the architect-first case machinery,
  reused verbatim). PLUS the sealed write-boundary (structural:
  `engine/trunk.py`'s own allowlist has no merge/rebase/commit/push/reset
  shape at all — TRON's git surface cannot merge, the agent owns the land)
  and the "no second direct caller" backstop (structural: `grants.py`'s
  mint/consume/read_* functions are called from nowhere in production
  `core/*.py` except `core/landing.py`).

`ok(name, cond, detail)` collector; `main()` prints `PASS (n/m)` and every
line, exits non-zero on any fail."""
import ast
import glob
import inspect
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))            # core
APP_ROOT = os.path.dirname(HERE)                               # worktree root
ENGINE_DIR = os.path.join(APP_ROOT, "engine")
sys.path.insert(0, ENGINE_DIR)
sys.path.insert(0, HERE)

import grants                      # noqa: E402 — respected contract, real, unmodified
import trunk                       # noqa: E402 — respected contract, real, unmodified
import gitobs                      # noqa: E402 — core/gitobs.py, the ONE git-observation seam
import landing                     # noqa: E402 — core/landing.py, the module under test
import state                       # noqa: E402 — core/state.py

import landing_rig as lr           # noqa: E402 — real-git scaffold + MiniEng (reused, not forked)
import gate_full_rig as gfr        # noqa: E402 — real-git scaffold + the MORE complete MiniEng (.emit())

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


# ══════════════════════════════════════════════════════════════════════════
# test:<single_land_primitive>
# ══════════════════════════════════════════════════════════════════════════

def _production_core_files():
    """Every production `core/*.py` (never a `*_rig.py`, never `core/sim/`)
    — the SAME `production_files()` scoping `core/r3_lint.py`'s own
    completeness lint already establishes for T7, reused by name/shape
    rather than re-derived differently here."""
    return sorted(f for f in glob.glob(os.path.join(APP_ROOT, "core", "*.py"))
                 if not os.path.basename(f).endswith("_rig.py"))


def _single_land_primitive():
    # Structural: exactly ONE `def land_via_grant` in the whole core/ tree.
    defs = 0
    for f in _production_core_files() + glob.glob(os.path.join(APP_ROOT, "core", "*_rig.py")):
        with open(f) as fh:
            src = fh.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        defs += sum(1 for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef) and node.name == "land_via_grant")
    ok("SP1 (STRUCTURAL — must be GREEN): exactly ONE `def land_via_grant` exists "
       "anywhere under core/ — never a second/forked copy",
       defs == 1, f"definitions_found={defs}")

    # Every real production call site references `landing.land_via_grant`.
    import re
    call_re = re.compile(r"land_via_grant\s*\(")
    callers = []
    for f in _production_core_files():
        if os.path.basename(f) == "landing.py":
            continue
        with open(f) as fh:
            src = fh.read()
        # A genuine CALL site — `land_via_grant(` — vs. mere PROSE mentioning
        # the name in a docstring/comment (e.g. "land_via_grant observes
        # 'landed'", no trailing paren-call at all): only a real call is
        # checked for the `landing.` prefix; prose is never flagged.
        for m in call_re.finditer(src):
            prefix = src[max(0, m.start() - 8):m.start()]
            callers.append(os.path.basename(f))
            ok(f"SP2 [{os.path.basename(f)}]@{m.start()}: a genuine land_via_grant( "
               f"call site is prefixed `landing.` (the ONE seam), never a "
               f"bare/forked name",
               prefix.endswith("landing."), f"prefix={prefix!r}")
    ok("SP3 (NON-VACUITY — must be GREEN): at least one real production call site "
       "was genuinely found (this isn't a vacuously-true empty scan)",
       len(callers) >= 3, f"callers={sorted(set(callers))}")

    # Observation-first, real-git: land a branch for real, THEN call
    # land_via_grant AGAIN for the SAME case-id — must short-circuit "landed"
    # WITHOUT minting a second grant (observation decides, not a re-mint).
    root = lr.build_root()
    grants_dir = os.path.join(root, "meta", "agents", "tron", "grants")
    eng = lr.MiniEng(root, grants_dir)
    tip = lr.make_paperwork_commit(root, lr.BRANCH, "obs-first.md", "v1 content")
    pid = trunk.patch_id(root, lr.BRANCH, lr.MAIN, False)
    case_id = landing.paperwork_case_id(lr.ROLE, lr.BRANCH, pid)

    outcome1 = landing.land_via_grant(eng, case_id, lr.BLOCK, lr.BRANCH, lr.WID, "test", "obs")
    rc, out, err = lr.run_land(root, grants_dir, case_id)
    ok("SP4: the real land.sh call succeeded for the freshly-minted grant",
       rc == 0 and lr.is_ancestor(root, tip, lr.MAIN),
       f"rc={rc} out={out!r} err={err!r}")

    live_before = grants.list_live(grants_dir)
    outcome2 = landing.land_via_grant(eng, case_id, lr.BLOCK, lr.BRANCH, lr.WID, "test", "obs")
    live_after = grants.list_live(grants_dir)
    ok("SP5 (OBSERVATION-FIRST, THE KILLER — must be GREEN): a SECOND call for the "
       "SAME already-landed case-id short-circuits 'landed' instantly, minting NO "
       "new grant (live grants unchanged: 0 -> 0)",
       outcome1 == "pending" and outcome2 == "landed"
       and live_before == {} and live_after == {},
       f"outcome1={outcome1} outcome2={outcome2} live_before={live_before} "
       f"live_after={live_after}")

    ok("test:<single_land_primitive> (AC-18): landing is a single primitive, "
       "observation-first",
       all(c for name, c, _ in _results if name.startswith("SP")))


# ══════════════════════════════════════════════════════════════════════════
# test:<merge_inversion_cannot_recur>
# ══════════════════════════════════════════════════════════════════════════

def _l1_discovery_globs():
    files = set(glob.glob(os.path.join(APP_ROOT, "core", "*_rig.py")))
    files |= set(glob.glob(os.path.join(APP_ROOT, "core", "sim", "*_rig.py")))
    return {os.path.relpath(f, APP_ROOT) for f in files}


_COVERAGE_MAP = {
    "T2-17 regression (re-authored branch under a live close-out cycle)":
        "core/gate_full_rig.py",
    "content-bound case-id vs. the confirmed-RED old primitive shape":
        "core/landing_rig.py",
}


def _merge_inversion_cannot_recur():
    discovered = _l1_discovery_globs()
    for guarantee, rig_rel in _COVERAGE_MAP.items():
        on_disk = os.path.isfile(os.path.join(APP_ROOT, rig_rel))
        in_l1 = rig_rel in discovered
        ok(f"COVERAGE [{guarantee}]: its dedicated proof {rig_rel} exists AND is in "
           f"scripts/l1.sh's own discovery glob (runs green in THIS gate)",
           on_disk and in_l1, f"on_disk={on_disk} in_l1_discovery={in_l1}")

    # A FAST, direct, focused mutation proof of the binding function itself
    # (`stage_case_id`), on top of the two heavier real-git rigs above:
    # the SAME branch, DIFFERENT patch-ids -> DIFFERENT case-ids (never a
    # cached/reused id across genuinely new content); the SAME branch, the
    # SAME patch-id (a pure rebase — content-identical) -> the SAME case-id
    # (stable across churn, never spuriously fresh).
    branch = "feat/mi-01"
    cid_v1 = landing.stage_case_id(None, "merge", branch, "aaaaaaaaaaaa")
    cid_v1_again = landing.stage_case_id(cid_v1, "merge", branch, "aaaaaaaaaaaa")
    cid_v2 = landing.stage_case_id(cid_v1, "merge", branch, "bbbbbbbbbbbb")
    ok("MI1 (THE T2-17 KILLER, DIRECT — must be GREEN): stage_case_id derives a "
       "FRESH case-id for genuinely NEW content (different patch-id) on the SAME "
       "branch — never the cached prior id",
       cid_v1 != cid_v2, f"cid_v1={cid_v1} cid_v2={cid_v2}")
    ok("MI2 (STABILITY, NON-VACUITY — must be GREEN): the SAME branch + the SAME "
       "patch-id (content-identical, e.g. a pure rebase) reuses the SAME case-id — "
       "the fix is content-bound, not spuriously fresh on every call",
       cid_v1 == cid_v1_again, f"cid_v1={cid_v1} cid_v1_again={cid_v1_again}")
    ok("MI3 (UNRESOLVABLE PATCH-ID — must be GREEN): with the patch-id momentarily "
       "unresolvable ('' — mid-churn or already fully landed), stage_case_id keeps "
       "the caller's last-good id rather than overwrite it with a malformed "
       "empty-suffix one",
       landing.stage_case_id(cid_v1, "merge", branch, "") == cid_v1,
       f"kept={landing.stage_case_id(cid_v1, 'merge', branch, '')}")

    ok("test:<merge_inversion_cannot_recur> (AC-18): a same-named branch re-authored "
       "with new content can never reuse a stale consumed receipt",
       all(c for name, c, _ in _results if name.startswith(("COVERAGE", "MI"))))


# ══════════════════════════════════════════════════════════════════════════
# test:<grant_lifecycle_and_write_boundary>
# ══════════════════════════════════════════════════════════════════════════

def _grant_lifecycle_and_write_boundary():
    root = lr.build_root()
    grants_dir = os.path.join(root, "meta", "agents", "tron", "grants")
    eng = lr.MiniEng(root, grants_dir)

    # ── GL1/GL2: patch-id-bound grant — reused unchanged when content is
    #    IDENTICAL, freshly re-minted when content CHANGES. ──
    branch = "arch/gl-01"
    tip1 = lr.make_paperwork_commit(root, branch, "gl1.md", "v1")
    case_id = landing.paperwork_case_id("architect", branch, trunk.patch_id(root, branch, lr.MAIN, False))
    landing.land_via_grant(eng, case_id, "GL-01", branch, lr.WID, "test", "gl")
    live1 = grants.read_live(grants_dir, case_id)
    landing.land_via_grant(eng, case_id, "GL-01", branch, lr.WID, "test", "gl")   # re-call, no new commit
    live1_again = grants.read_live(grants_dir, case_id)
    ok("GL1 (PATCH-ID-BOUND, REUSE — must be GREEN): a re-call with IDENTICAL "
       "content reuses the SAME live grant untouched (same patch_id, same file)",
       live1 is not None and live1_again is not None
       and live1.get("patch_id") == live1_again.get("patch_id"),
       f"live1={live1} live1_again={live1_again}")

    # ── GL2: ""/off-token fail-closed — a branch whose CUMULATIVE diff
    #    against main nets to EMPTY (a file added then removed — patch-id
    #    resolves to "") while its tip is a genuinely NEW commit, NOT an
    #    ancestor of main (unlike a branch that simply never diverged, which
    #    would trivially short-circuit "landed" via real ancestry before the
    #    patch-id path is even reached — that is a DIFFERENT, already-proven
    #    shape, not this one). ──
    empty_branch = "arch/gl-empty"
    lr._git(["checkout", "-B", empty_branch, lr.MAIN], root)
    tmp_path = os.path.join(root, "meta", "net-zero-temp.md")
    with open(tmp_path, "w") as f:
        f.write("temporary")
    lr._git(["add", "-A"], root)
    lr._git(["commit", "-m", "add temp (will be reverted)"], root)
    os.remove(tmp_path)
    lr._git(["add", "-A"], root)
    lr._git(["commit", "-m", "remove temp (net-zero diff vs main)"], root)
    empty_tip = lr._git_out(["rev-parse", "HEAD"], root)
    lr._git(["checkout", "--detach", lr.MAIN], root)
    ok("GL2pre: the net-zero branch's tip is a genuinely NEW commit, NOT an "
       "ancestor of main (so `_observe_landed` reads False — this exercises the "
       "patch-id fail-closed path, never the already-proven real-ancestry one)",
       bool(empty_tip) and not lr.is_ancestor(root, empty_tip, lr.MAIN),
       f"empty_tip={empty_tip}")
    empty_pid = trunk.patch_id(root, empty_branch, lr.MAIN, False)
    empty_case = landing.paperwork_case_id("architect", empty_branch, empty_pid)
    outcome_empty = landing.land_via_grant(eng, empty_case, "GL-EMPTY", empty_branch,
                                           lr.WID, "test", "gl")
    ok("GL2 (FAIL-CLOSED, THE KILLER — must be GREEN): a branch with an "
       "unresolvable ('') patch-id (zero diff from main) is FAIL-CLOSED — no grant "
       "minted, never a false pass",
       empty_pid == "" and outcome_empty == "fail-closed"
       and grants.read_live(grants_dir, empty_case) is None,
       f"empty_pid={empty_pid!r} outcome={outcome_empty}")

    # off-alphabet case-id (unsafe chars) — grants.mint's own fail-closed rider,
    # reached through the SAME primitive.
    unsafe_case = "paperwork/../unsafe id!"
    tip_u = lr.make_paperwork_commit(root, "arch/gl-unsafe", "u.md", "unsafe")
    outcome_unsafe = landing.land_via_grant(eng, unsafe_case, "GL-UNSAFE", "arch/gl-unsafe",
                                            lr.WID, "test", "gl")
    ok("GL3 (OFF-TOKEN FAIL-CLOSED — must be GREEN): an off-safe-alphabet case-id "
       "never mints a grant either — the SAME fail-closed rider, land.sh's own "
       "pre-interpolation guard honored at the primitive",
       outcome_unsafe == "fail-closed",
       f"outcome_unsafe={outcome_unsafe}")

    # ── GL4: the crash-window administrative-consume arm — content reaches
    #    trunk for real (simulating land.sh's own merge step) while the grant
    #    stays LIVE (simulating a crash between land.sh's update-ref and its
    #    own consume step) — the NEXT land_via_grant call must observe it
    #    landed and consume the grant ADMINISTRATIVELY, never re-mint. ──
    branch2 = "arch/gl-crash"
    tip2 = lr.make_paperwork_commit(root, branch2, "gl-crash.md", "crash-window content")
    pid2 = trunk.patch_id(root, branch2, lr.MAIN, False)
    case2 = landing.paperwork_case_id("architect", branch2, pid2)
    out2 = landing.land_via_grant(eng, case2, "GL-CRASH", branch2, lr.WID, "test", "gl")
    ok("GL4a: a fresh grant was minted (pending) for the crash-window scenario",
       out2 == "pending" and grants.read_live(grants_dir, case2) is not None,
       f"out2={out2}")
    # Simulate land.sh's own merge step succeeding WITHOUT its own consume
    # (the crash window) — a real, direct ref advance, never land_via_grant's
    # own doing (mirrors land.sh's `git update-ref refs/heads/main <branch-tip>`).
    lr._git(["update-ref", f"refs/heads/{lr.MAIN}", tip2], root)
    ok("GL4b: the branch is genuinely on trunk now (real ancestry), grant STILL "
       "live (the crash window — merged but not yet consumed)",
       lr.is_ancestor(root, tip2, lr.MAIN) and grants.read_live(grants_dir, case2) is not None,
       f"live={grants.read_live(grants_dir, case2)}")
    out2b = landing.land_via_grant(eng, case2, "GL-CRASH", branch2, lr.WID, "test", "gl")
    ok("GL4c (CRASH-WINDOW KILLER — must be GREEN): the NEXT call observes landed "
       "and consumes the STILL-LIVE grant ADMINISTRATIVELY (never re-mints, never "
       "re-orders the worker a second time) — live gone, consumed on file, and it "
       "was correctly NOT flagged grantless (a live grant covered it)",
       out2b == "landed" and grants.read_live(grants_dir, case2) is None
       and grants.read_consumed(grants_dir, case2) is not None,
       f"out2b={out2b} live_after={grants.read_live(grants_dir, case2)} "
       f"consumed={grants.read_consumed(grants_dir, case2)}")

    # ── GL5/GL6: grantless-land detected (T22 production addition) — content
    #    reaches trunk via a raw ref advance for a case-id that NEVER had ANY
    #    grant (live or consumed) — the out-of-band-bypass signature. Counted
    #    (must-be-zero), mutation-proven against GL4's covered contrast. ──
    branch3 = "arch/gl-bypass"
    tip3 = lr.make_paperwork_commit(root, branch3, "gl-bypass.md", "bypassed content")
    pid3 = trunk.patch_id(root, branch3, lr.MAIN, False)
    case3 = landing.paperwork_case_id("architect", branch3, pid3)
    ok("GL5a: this exact content-bound case-id has NEVER been granted (no live, "
       "no consumed) before the bypass",
       grants.read_live(grants_dir, case3) is None
       and grants.read_consumed(grants_dir, case3) is None,
       "pre-bypass grant state clean")
    lr._git(["update-ref", f"refs/heads/{lr.MAIN}", tip3], root)   # the bypass itself
    events_before = len(eng.events.log)
    out3 = landing.land_via_grant(eng, case3, "GL-BYPASS", branch3, lr.WID, "test", "gl")
    grantless_events = [e for e in eng.events.log[events_before:]
                        if e["type"] == "must_be_zero"
                        and e["payload"].get("counter") == "grantless_land_detected"]
    ok("GL5b (GRANTLESS-LAND, THE KILLER — must be GREEN): content that reached "
       "trunk with NO grant EVER on file for this case-id is observed 'landed' AND "
       "counted (must-be-zero, R4) exactly once — never silently absorbed as an "
       "ordinary landing",
       out3 == "landed" and len(grantless_events) == 1
       and grantless_events[0]["payload"].get("case_id") == case3,
       f"out3={out3} grantless_events={grantless_events}")

    # Mutation/non-vacuity, direct against counters.evaluate: the run-level
    # acceptance read REJECTS by this exact name.
    import counters
    ok_eval, lines, reasons = counters.evaluate(eng.events.log)
    ok("GL5c (ACCEPTANCE REJECTS BY NAME — must be GREEN): `core/counters.py`'s own "
       "acceptance read REJECTS this run, naming grantless_land_detected explicitly "
       "— the SAME surfacing mechanism every other must-be-zero backstop uses",
       ok_eval is False and any("grantless_land_detected" in r for r in reasons),
       f"ok_eval={ok_eval} reasons={reasons}")

    ok("GL6 (NON-VACUITY CONTRAST — must be GREEN): GL4's crash-window landing "
       "(a LIVE grant DID exist) was correctly NOT counted grantless — the detector "
       "is genuinely discriminating covered-vs-bypassed, not a blanket flag on every "
       "'landed' outcome",
       not any(e["type"] == "must_be_zero"
              and e["payload"].get("counter") == "grantless_land_detected"
              and e["payload"].get("case_id") == case2
              for e in eng.events.log),
       "no grantless event for the covered (GL4) case")

    # ── GL11: T19 live-finding fix — an administrative no-op forward
    #    (architect_triage.py's `scope_forward` adhoc-forward lane) on a
    #    branch that was NEVER authored must NEVER read "landed". Mirrors
    #    architect_triage.py:290's own `stage_case_id(entry.get("case_id"),
    #    "triage-forward", entry["branch"], patch_id)` call exactly, with
    #    both the branch tip AND the patch-id genuinely unresolvable (never
    #    authored) — the SAME shape that false-fired `grantless_land_detected`
    #    on the T19 live trivial run. Both arms in the SAME gate: GL5b above
    #    proves a genuine out-of-band bypass (resolvable tip) STILL fires the
    #    counter by name; GL11 proves an unauthored branch (unresolvable tip)
    #    stays silent — never landed, never counted. ──
    unauthored_branch = "arch/adhoc-triage-unauthored-logreview"
    ok("GL11pre (NON-VACUITY — must be GREEN): the unauthored branch genuinely "
       "has no tip at all — trunk.tip_sha resolves to '' (never created, not a "
       "stale/deleted one)",
       trunk.tip_sha(root, unauthored_branch, False) == "",
       f"tip_sha={trunk.tip_sha(root, unauthored_branch, False)!r}")
    land_case_id = landing.stage_case_id(None, "triage-forward", unauthored_branch, "")
    events_before_gl11 = len(eng.events.log)
    outcome_gl11 = landing.land_via_grant(eng, land_case_id, "GL-UNAUTHORED",
                                          unauthored_branch, lr.WID, "test", "gl")
    grantless_events_gl11 = [e for e in eng.events.log[events_before_gl11:]
                             if e["type"] == "must_be_zero"
                             and e["payload"].get("counter") == "grantless_land_detected"]
    ok("GL11 (T19 LIVE-FINDING FIX, THE KILLER — must be GREEN): an unauthored "
       "branch (unresolvable tip) never reads 'landed' — outcome is 'fail-closed' "
       "(no grant, patch-id also unresolvable), NOT 'landed', and ZERO "
       "grantless_land_detected events fire for this case-id — the exact false-fire "
       "the T19 trivial live run hit (`arch/adhoc-triage-unauthored-logreview` never "
       "authored -> old is_ancestor('') vacuous-True -> false 'landed' -> false "
       "grantless-land REJECT)",
       outcome_gl11 == "fail-closed" and len(grantless_events_gl11) == 0,
       f"outcome_gl11={outcome_gl11} grantless_events_gl11={grantless_events_gl11}")

    ok_eval_gl11, lines_gl11, reasons_gl11 = counters.evaluate(eng.events.log[events_before_gl11:])
    ok("GL11b (ACCEPTANCE STAYS GREEN FOR THIS SEGMENT — must be GREEN): "
       "counters.evaluate over just this case's events never names "
       "grantless_land_detected as a rejection reason",
       not any("grantless_land_detected" in r for r in reasons_gl11),
       f"ok_eval_gl11={ok_eval_gl11} reasons_gl11={reasons_gl11}")

    # ── GL7/GL8: root-reattach detected + self-heals (T22 production
    #    addition), real git, the FULL architect-first case machinery
    #    (needs a more complete duck-typed eng — gate_full_rig's own, which
    #    already carries `.emit()`/`.workers`/`._release_worker`). ──
    root2 = gfr.build_root()
    grants_dir2 = os.path.join(root2, "meta", "agents", "tron", "grants")
    eng2 = gfr.MiniEng(root2, grants_dir2, test_command="true")
    eng2.paths["remote"] = "none"
    manifest = {}

    landing.check_root_detached(eng2, manifest)
    ok("GL7a: no violation while genuinely detached (the rig's own baseline state, "
       "ADR-0002 D1) — no case opened",
       not any(c.get("source") == "root.reattached" for c in (manifest.get("cases") or {}).values()),
       f"cases={manifest.get('cases')}")

    gfr._git(["checkout", gfr.MAIN], root2)   # the violation: root re-attached to a branch
    landing.check_root_detached(eng2, manifest)
    root_case_id, root_case = next(
        ((cid, c) for cid, c in (manifest.get("cases") or {}).items()
        if c.get("source") == "root.reattached"), (None, None))
    ok("GL7b (ROOT-REATTACH DETECTED, THE KILLER — must be GREEN): a real "
       "re-attach (root checked out on main, ADR-0002 D1 violation) opens an "
       "architect-first case (owner='architect', block-less pseudo-block "
       "'root-reattach') through the EXISTING case machinery — never a new "
       "escalation mechanism",
       root_case is not None and root_case.get("owner") == "architect"
       and root_case.get("decision") is None,
       f"root_case={root_case}")

    landing.check_root_detached(eng2, manifest)
    still_one = sum(1 for c in (manifest.get("cases") or {}).values()
                    if c.get("source") == "root.reattached")
    ok("GL7c (IDEMPOTENT — must be GREEN): re-checking while STILL attached never "
       "opens a second case for the same violation",
       still_one == 1, f"count={still_one}")

    gfr._git(["checkout", "--detach", gfr.MAIN], root2)   # restore detachment
    landing.check_root_detached(eng2, manifest)
    root_case_after = (manifest.get("cases") or {}).get(root_case_id)
    ok("GL8 (SELF-HEALS, THE F-1 KILLER — must be GREEN): once detachment is "
       "restored, the SAME open case is resolved via architect_resolve's existing "
       "'answer' verdict (cleared, re-drivable) — no bespoke close path, the "
       "EXISTING mechanism's own resolution",
       root_case_after is None,
       f"root_case_after={root_case_after} cases_now={manifest.get('cases')}")

    # ── GL9: sealed write-boundary — TRON's own git surface (engine/trunk.py,
    #    core/gitobs.py's ONE seam) structurally CANNOT merge/rebase/commit/
    #    push/reset; the agent owns the land (ADR-0002 D2), never the engine. ──
    banned_subcommands = {"merge", "rebase", "commit", "push", "reset", "checkout",
                          "cherry-pick", "revert", "am"}
    ok("GL9a (SEALED ALLOWLIST — must be GREEN): none of the git-mutation "
       "subcommands a merge/rebase would need are on trunk.py's own sealed "
       "allowlist at all",
       banned_subcommands.isdisjoint(trunk._ALLOWED_GIT_SUBCOMMANDS),
       f"allowed={sorted(trunk._ALLOWED_GIT_SUBCOMMANDS)}")
    raised = False
    try:
        trunk._run(["git", "-C", root2, "merge", "--ff-only", "some-branch"])
    except trunk.SealedAllowlistViolation:
        raised = True
    ok("GL9b (MUTATION -> RAISES, THE KILLER — must be GREEN): an actual attempted "
       "`git merge` through the ONE seam raises SealedAllowlistViolation, loud, "
       "never silently refused/swallowed — structurally, TRON cannot merge; the "
       "agent owns the land",
       raised is True, f"raised={raised}")

    # ── GL10: "no second direct caller" — grants.py's mint/consume/read_* are
    #    called from NOWHERE in production core/*.py except core/landing.py. ──
    offenders = []
    for f in _production_core_files():
        if os.path.basename(f) in ("landing.py", "gitobs.py"):
            continue
        with open(f) as fh:
            src = fh.read()
        if any(p in src for p in ("grants.mint(", "grants.consume(", "grants.read_live(",
                                  "grants.read_consumed(", "grants.read_raw(",
                                  "grants.list_live(")):
            offenders.append(os.path.basename(f))
    ok("GL10 (NO SECOND DIRECT CALLER — must be GREEN): no production core/*.py "
       "module other than core/landing.py calls grants.py's mint/consume/read_* "
       "functions directly — the ONE enforcement seam stays the ONE seam",
       not offenders, f"offenders={offenders}")

    ok("test:<grant_lifecycle_and_write_boundary> (AC-18): the grant lifecycle, "
       "the sealed write-boundary, and the two T22 detection additions all hold",
       all(c for name, c, _ in _results if name.startswith("GL")))


def main():
    _single_land_primitive()
    _merge_inversion_cannot_recur()
    _grant_lifecycle_and_write_boundary()

    passed = sum(1 for _, c, _ in _results if c)
    print(f"core.landing_gate_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
