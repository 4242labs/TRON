"""core.scaffold_src — the ONE resolver for the real trivial-tip-converter
scaffold source directory that every `core/*_rig.py`, `core/sim/*.py`, and
`engine/land_paperwork_rig.py` copies FROM before seeding a throwaway git
repo (never mutates the source itself — see each rig's own docstring).

Before this module existed, the same absolute path
(`/home/anderson/42labs/tron/tron-meta/sims/_sources/trivial-tip-converter`)
was copy-pasted as a literal `SCAFFOLD_SRC = "..."` into 18 separate rig
files. That path only ever existed on one dev machine — a CI runner (or
anyone else's checkout) has no `/home/anderson` at all, so every one of
those 18 rigs died with `FileNotFoundError` in CI, and the block's own
AC-1/AC-2 proof steps (which run AFTER the L1 rig sweep in engine-ci.yml)
never executed. Fixing that by hand-editing 18 literals would have left the
same failure mode for rig #19 — this is the single source of truth instead:
one resolver, every rig imports it.

The FIRST fix attempted here was checking `tron-meta` (the scaffold's real
upstream repo) out in CI. That does not work and never can: `tron-meta`'s
own `.gitignore` deliberately excludes `sims/*` wholesale ("sim target
projects are their own (nested) git repos — disposable, not tracked here")
— `sims/_sources/trivial-tip-converter` is git-invisible in that repo on
EVERY machine, not just CI's. No token/checkout fixes a path nothing ever
committed.

The actual fix: this scaffold is small (~1.8MB WITH its full git history —
excludes its own `node_modules`/`.next`/`coverage`, which are gitignored in
its own history and no `core/` rig ever needs) and this app is its one real
consumer. It is vendored straight into THIS repo —
`core/sim/fixtures/trivial-tip-converter/` — as a real `git clone` of the
upstream scaffold repo, HISTORY AND TAGS INCLUDED: `core/sim/
boot_real_scaffold_rig.py` (and `core/sim/report_channel_rig.py`, which
reuses its seeding) does not just copy this scaffold's WORKING TREE — it
reads `meta/tron/scaffold.yaml`'s `scaffold_ref` (a real git TAG,
`block-01-01-scaffold`, marking the pre-block-01-02 commit) and `git
archive`s TWO separate refs out of `SCAFFOLD_SRC`'s own history (the
unbuilt `scaffold_ref` tree overlaid with `HEAD`'s `meta/`) to build an
honest, un-hollow SIM seed. A flat file snapshot (no `.git`, no tags) breaks
that — a real clone is the only vendoring shape that preserves it.

A directory literally named `.git` inside this repo's own working tree
would make git treat it as an embedded submodule (a gitlink) instead of
ordinary tracked content, and `actions/checkout` (this workflow disables
`submodules`) would then check out NOTHING there — so the fixture's `.git`
is committed here under the name `_git_history/` (ordinary tracked files,
byte-identical to a real `.git` dir). `resolve()` never renames that in
place inside the TRACKED tree (a rename-in-place was tried first and
rejected: it left `.git` materialized in the working tree between runs,
one `git add -A` away from being accidentally committed back as a gitlink
— exactly the failure mode this vendoring exists to avoid). Instead it
materializes a COPY into a process-wide temp cache
(`$TMPDIR/tron-scaffold-src-trivial-tip-converter/`, rebuilt whenever the
vendored tree's own recorded HEAD sha changes) and renames `_git_history`
-> `.git` ONLY inside that disposable copy — the tracked fixture itself is
never mutated, so there is nothing to forget to rename back before a commit.

Resolution order:
  1. `TRON_REAL_SCAFFOLD_SRC` env var, if set — an explicit override for a
     developer/CI run that wants to point at a DIFFERENT real scaffold
     checkout instead of the vendored fixture.
  2. The vendored fixture (`core/sim/fixtures/trivial-tip-converter/`,
     relative to this file), materialized into the temp cache described
     above — the default everywhere: dev machine, CI, or any other
     checkout of this repo, since the fixture ships IN this repo.

`resolve()` raises immediately with a clear message if neither location
exists as a real directory — one obvious failure at the one place this is
resolved, instead of 18 different confusing `FileNotFoundError`s deep inside
unrelated `shutil.copytree` calls.

DRIFT RISK (honestly disclosed, block 01-40 T1): this vendored copy is a
point-in-time `git clone` of tron-meta's real `trivial-tip-converter`
source — nothing here re-syncs it if the upstream fixture changes later, so
it CAN silently drift from tron-meta's original over time. There is no
automated check for that drift; re-vendoring (a fresh clone + commit here)
is a manual step if/when the upstream fixture is intentionally updated.
"""
import os
import shutil
import tempfile

ENV_VAR = "TRON_REAL_SCAFFOLD_SRC"
_VENDORED = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "sim", "fixtures", "trivial-tip-converter")
_CACHE_DIR = os.path.join(tempfile.gettempdir(), "tron-scaffold-src-trivial-tip-converter")


def _vendored_head_sha():
    """The vendored fixture's own recorded HEAD sha (read directly out of
    `_git_history/refs/heads/<branch>` — no `git` subprocess needed just to
    key a cache), used to invalidate a stale materialized copy when the
    fixture is ever updated."""
    history_dir = os.path.join(_VENDORED, "_git_history")
    head_path = os.path.join(history_dir, "HEAD")
    try:
        with open(head_path, encoding="utf-8") as fh:
            head = fh.read().strip()
    except OSError:
        return None
    if not head.startswith("ref:"):
        return head   # a detached HEAD already holds the sha directly
    ref = head.split(None, 1)[1].strip()
    ref_path = os.path.join(history_dir, ref)
    try:
        with open(ref_path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return None


def _materialize_vendored_copy():
    """A disposable COPY of the vendored fixture, with `_git_history/` ->
    `.git/`, in a temp cache — never mutates the tracked fixture itself
    (see module docstring). Rebuilt whenever missing or stale (keyed off
    the vendored tree's own HEAD sha); reused across every rig subprocess
    in the same run/host otherwise."""
    sha = _vendored_head_sha()
    sha_marker = os.path.join(_CACHE_DIR, ".vendored_head_sha")
    cached_sha = None
    if os.path.isfile(sha_marker):
        with open(sha_marker, encoding="utf-8") as fh:
            cached_sha = fh.read().strip()
    if os.path.isdir(_CACHE_DIR) and cached_sha == sha and sha is not None:
        return _CACHE_DIR
    if os.path.isdir(_CACHE_DIR):
        shutil.rmtree(_CACHE_DIR)
    shutil.copytree(_VENDORED, _CACHE_DIR)
    history_dir = os.path.join(_CACHE_DIR, "_git_history")
    git_dir = os.path.join(_CACHE_DIR, ".git")
    if os.path.isdir(history_dir):
        os.rename(history_dir, git_dir)
    if sha is not None:
        with open(sha_marker, "w", encoding="utf-8") as fh:
            fh.write(sha)
    return _CACHE_DIR


def resolve():
    if os.environ.get(ENV_VAR):
        path = os.environ[ENV_VAR]
        if not os.path.isdir(path):
            raise FileNotFoundError(
                f"core.scaffold_src.resolve(): {ENV_VAR}={path!r} does not exist.")
        return path
    if not os.path.isdir(_VENDORED):
        raise FileNotFoundError(
            f"core.scaffold_src.resolve(): the vendored fixture {_VENDORED!r} is "
            f"missing. Restore core/sim/fixtures/trivial-tip-converter/ (tracked in "
            f"this repo), or set {ENV_VAR} to a real scaffold checkout instead."
        )
    return _materialize_vendored_copy()
