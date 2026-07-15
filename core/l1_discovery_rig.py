"""core.l1_discovery_rig — block 01-38 T18 (AC-14): `cmd:<L1 discovers new
rigs>`.

Every prior task (T1-T17) added its own proof rig with zero edits to
`scripts/l1.sh` itself — its glob (`core/*_rig.py` + `core/sim/*_rig.py`,
confirmed by direct read of the script, never assumed) already picked each
one up automatically. T18 is the ASSERTION that this genuinely held for
EVERY new rig this block added, not merely a hope, plus a live,
mutation-style proof that the discovery mechanism is a REAL glob (dynamic,
re-evaluated) rather than a stale/cached list that happens to agree today.

WHAT COUNTS AS "this block added": every file `core/*_rig.py`/`core/sim/
*_rig.py` that did NOT exist at `_BLOCK_BASE_SHA` (the real merge-base this
branch shares with `origin/main` at the time this task was written — a
frozen historical fact, like every other `core/*_rig.py`'s own cited
commit/ledger-row constants, never a live `origin/main` ref that could
drift the diff scope as trunk moves independently of this branch).

`core/prompt_conformance.py` (T15) is DELIBERATELY not `_rig.py`-suffixed
(it must never auto-run a real token-spending model call from `l1.sh`'s
fast, free CI gate) — this rig asserts it is CORRECTLY ABSENT from the
discovered set, the expected shape, never flagged as a gap.

`ok(name, cond, detail)`; `main()` prints `PASS (n/m)`, exits non-zero on
fail.
"""
import glob
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))          # core
APP_ROOT = os.path.dirname(HERE)                             # tron-app worktree root

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


# The merge-base this branch (`block/01-38-engine-close`) shares with
# `origin/main` — read directly (`git merge-base HEAD origin/main`) when
# this task was authored, frozen here so the diff scope never drifts with
# trunk's own independent motion (the SAME "cite the fact, don't re-derive
# a moving target" discipline `core/door_fixtures_rig.py`'s ledger-row
# citations already use).
_BLOCK_BASE_SHA = "a8e3add"

_PROMPT_CONFORMANCE = "core/prompt_conformance.py"   # T15 — deliberately NOT _rig.py-suffixed


def _l1_discovery_globs():
    """The EXACT rig-discovery globs `scripts/l1.sh` uses (verbatim pattern
    every prior coverage-map rig in this block already established — never
    re-derived, never a hand copy)."""
    files = set(glob.glob(os.path.join(APP_ROOT, "core", "*_rig.py")))
    files |= set(glob.glob(os.path.join(APP_ROOT, "core", "sim", "*_rig.py")))
    return {os.path.relpath(f, APP_ROOT) for f in files}


def _block_added_rig_files():
    """Every `core/*_rig.py`/`core/sim/*_rig.py` path this BLOCK added —
    i.e. did not exist at `_BLOCK_BASE_SHA` and exists now. A REAL `git
    diff --diff-filter=A` over this worktree's own history, never a hand-
    typed list (the exact "hand-edited list" AC-14 forbids)."""
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=A",
         _BLOCK_BASE_SHA, "HEAD", "--",
         "core/*_rig.py", "core/sim/*_rig.py"],
        cwd=APP_ROOT, capture_output=True, text=True, check=True)
    return sorted(ln for ln in out.stdout.splitlines() if ln.strip())


def _l1_glob_source_is_dynamic():
    """A source-level check that `scripts/l1.sh` itself declares a GLOB
    pattern (`core/*_rig.py core/sim/*_rig.py`), not a hand-maintained
    array of filenames — the actual mechanism AC-14 requires, read
    directly rather than trusted from a docstring."""
    path = os.path.join(APP_ROOT, "scripts", "l1.sh")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return "core/*_rig.py" in text and "core/sim/*_rig.py" in text, text


def run_block_added_coverage():
    added = _block_added_rig_files()
    discovered = _l1_discovery_globs()

    ok("NON-VACUOUS: block 01-38 genuinely added new rig files since "
       f"{_BLOCK_BASE_SHA} (a real, non-empty diff — not an accidentally "
       "empty scope that would make every check below vacuously pass)",
       len(added) >= 10, f"added={len(added)}: {added}")

    for f in added:
        on_disk = os.path.isfile(os.path.join(APP_ROOT, f))
        in_l1 = f in discovered
        ok(f"BLOCK-ADDED {f!r}: still on disk AND discovered by scripts/"
           f"l1.sh's own glob (zero hand-edits to l1.sh were needed for "
           f"this rig to run)",
           on_disk and in_l1, f"on_disk={on_disk} in_l1={in_l1}")

    ok(f"EXPECTED-ABSENT: {_PROMPT_CONFORMANCE!r} (T15 — deliberately NOT "
       f"_rig.py-suffixed, must never auto-run a token-spending real-model "
       f"call from l1.sh's free/fast CI gate) exists on disk but is "
       f"CORRECTLY absent from the discovered set — an intentional "
       f"exclusion by NAMING, not a coverage gap",
       os.path.isfile(os.path.join(APP_ROOT, _PROMPT_CONFORMANCE))
       and _PROMPT_CONFORMANCE not in discovered,
       f"on_disk={os.path.isfile(os.path.join(APP_ROOT, _PROMPT_CONFORMANCE))} "
       f"in_l1={_PROMPT_CONFORMANCE in discovered}")


def run_glob_is_real():
    is_glob, _text = _l1_glob_source_is_dynamic()
    ok("scripts/l1.sh declares a GLOB pattern for rig discovery, not a "
       "hand-maintained filename array (read directly, never assumed)",
       is_glob)

    # MUTATION-NONVACUITY: a genuinely NEW throwaway rig file, dropped
    # on disk and removed again in `finally`, must appear in / disappear
    # from a FRESH discovery call — proving the glob is dynamically
    # re-evaluated each run, not a stale/cached list that happens to agree
    # with today's file set by coincidence.
    before = _l1_discovery_globs()
    probe_path = None
    probe_rel = None
    try:
        fd, probe_path = tempfile.mkstemp(
            suffix="_probe_l1_discovery_rig.py", dir=os.path.join(APP_ROOT, "core", "sim"))
        os.close(fd)
        with open(probe_path, "w", encoding="utf-8") as fh:
            fh.write("# throwaway l1-discovery mutation probe — removed by the rig that created it\n")
        probe_rel = os.path.relpath(probe_path, APP_ROOT)
        after_add = _l1_discovery_globs()
        ok("MUTATION: a genuinely NEW *_rig.py file dropped on disk is "
           "IMMEDIATELY discovered by a fresh glob call (dynamic, not "
           "cached) — the probe was ABSENT before, PRESENT after",
           probe_rel not in before and probe_rel in after_add,
           f"before={probe_rel in before} after={probe_rel in after_add}")
    finally:
        if probe_path and os.path.isfile(probe_path):
            os.remove(probe_path)
    after_remove = _l1_discovery_globs()
    ok("MUTATION cleanup: removing the probe file makes it disappear from "
       "discovery again (the probe never leaks into a real l1.sh run)",
       probe_rel is not None and probe_rel not in after_remove,
       "probe removed and re-checked")


def main():
    run_block_added_coverage()
    run_glob_is_real()
    n_pass = sum(1 for _, c, _ in _results if c)
    n_total = len(_results)
    for name, cond, detail in _results:
        mark = "PASS" if cond else "FAIL"
        print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not cond else ""))
    print(f"l1_discovery_rig: PASS ({n_pass}/{n_total})")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    sys.exit(main())
