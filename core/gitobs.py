"""core.gitobs — the new `core/` stack's SINGLE git-observation seam.

This is the ONLY place in `core/` that touches `engine/trunk.py`. Every other
`core/` module (`core/gate.py`, `core/landing.py`, ...) reads git state
exclusively through the functions exposed here — never `import trunk`
directly, never a raw `git`/`subprocess` call of its own. One seam, one
documented boundary, so the fresh stack's substrate coupling stays in one
place instead of scattered import-and-shell-out per module.

Two kinds of reads live here:
  - Reads `engine/trunk.py` already implements correctly: delegated straight
    through (import trunk HERE, in this one module, and call it) — never
    forked, never re-derived. `trunk.py` is a respected, unmodified contract;
    this module's job is to be its one gateway into `core/`, not to replace
    it.
  - `last_touching_sha`: the record-baseline read `core/gate.py` needs
    (last commit touching a path on a ref) that `trunk.py` doesn't expose as
    a standalone public function — implemented directly here (plain
    read-only `git log`), so it lives in the seam instead of inline in
    control-plane logic.

A later wave may fully vendor these reads into `core/` (dropping the
`engine/trunk.py` dependency entirely) — until then, this is the single,
intentional bridge to the ported substrate. Never scattered.
"""
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
_ENGINE_DIR = os.path.join(_APP_ROOT, "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

import trunk    # noqa: E402 — respected contract, imported as-is (never forked); ONLY here


def tip_sha(root, branch, dry=False):
    """Delegates to `trunk.tip_sha` — the branch's current tip sha, or ''."""
    return trunk.tip_sha(root, branch, dry)


def patch_id(root, branch, truth_ref, dry=False):
    """Delegates to `trunk.patch_id` — the branch's content-identity hash
    against `truth_ref`, or '' (unresolvable/dry, fail-closed downstream)."""
    return trunk.patch_id(root, branch, truth_ref, dry)


def is_ancestor(root, sha, ref, dry=False):
    """Delegates to `trunk.is_ancestor` — True iff `sha` is an ancestor of
    `ref`'s tip."""
    return trunk.is_ancestor(root, sha, ref, dry)


def record_commit_ok(root, block_file, dry=False, truth_ref="main"):
    """Delegates to `trunk.record_commit_ok` — the record-diff content check
    (exactly one file, exactly the `**Status:**` field). Returns (ok, detail)."""
    return trunk.record_commit_ok(root, block_file, dry, truth_ref=truth_ref)


def replica_clean(root, branch, main_branch="main", dry=False):
    """Delegates to `trunk.replica_clean` — the close-time cleanliness check
    (branch gone, no worktree checked out on it). Returns (clean, detail)."""
    return trunk.replica_clean(root, branch, main_branch, dry)


def validate_trunk(root, merged_sha, test_command, test_env=None, ci_check_name=None,
                    dry=False, scratch_root=None):
    """Delegates to `trunk.validate_trunk` — the DONE-ladder wave-3 addition: the
    trunk-stage TRUSTED-VERDICT read `core.gate`'s `gate.trunk` stage needs (re-run the
    project's declared test command once, in a clean detached `git worktree` at
    `merged_sha`, never the worker's own checkout/say-so; or read a named CI check's
    verdict when `ci_check_name` is given). Returns `(status, detail)` with status one
    of `"pass"` / `"fail"` / `"unconfirmed"` — see `trunk.validate_trunk`'s own
    docstring for the full contract (T3: a real failure is never the same thing as
    "can't confirm"; neither is ever a silent free pass).

    `scratch_root` is forwarded as-is — `trunk.py`'s own sealed git-subcommand
    allowlist refuses a `worktree add`/`remove` outside it (fail-closed on a missing
    scratch_root in production; a caller here that needs a real validation run must
    supply one, exactly like `engine/fsm.py`'s own `ctx.scratch_dir` call site)."""
    return trunk.validate_trunk(root, merged_sha, test_command, test_env=test_env,
                                ci_check_name=ci_check_name, dry=dry,
                                scratch_root=scratch_root)


def last_touching_sha(root, ref, path):
    """Last commit sha touching `path` on `ref`, or '' if none/unresolvable.
    A tiny read-only read (mirrors the first half of `trunk.record_commit_ok`'s
    own walk) used to tell 'nothing new since the record baseline' apart from
    'something new landed, check it'. `trunk.py` doesn't expose this specific
    read as a standalone public function, so it's implemented directly here
    (plain `git log`) rather than reaching into `trunk.py`'s private
    internals — the seam's job, not a control-plane module's."""
    r = subprocess.run(["git", "-C", root, "log", "-n", "1", "--format=%H",
                        ref, "--", path], capture_output=True, text=True)
    if r.returncode != 0:
        return ""
    return r.stdout.strip()
