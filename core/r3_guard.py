"""r3_guard — runtime write-guard (block 01-40 T1, ADR-0012 Opus-pivot item 1).

`core/r3_lint.py` proves, STATICALLY, that no rig-authored AST *shape*
fabricates a sender or bypasses the drain. It cannot see a byte actually
land on disk — a runtime mechanism the static prover misses, or simply
never enumerated (its own docstring's "REMAINING LIMITS"), still writes.
This module is the runtime backstop: an `sys.addaudithook` installed once
per process, in every rig `scripts/l1.sh` spawns, that makes a genuinely
protected ingress path physically UNWRITABLE from Python code in that
process — independent of AST shape, mechanism, or how many rewrites the
lint itself needs.

WIRING (this module never wires itself): `scripts/l1.sh` calls
`materialize_site_dir()` to drop a `sitecustomize.py` into a directory it
prepends to `PYTHONPATH` for every rig it spawns. `sitecustomize.py` (never
`PYTHONSTARTUP` — that hook fires only for *interactive* sessions, never
for `python3 script.py`) is imported automatically by the stdlib `site`
module at interpreter startup whenever its directory is importable — which
is exactly what a `PYTHONPATH`-prepended directory gives us, with zero
change to any of the ~30 rig scripts themselves.

PROTECTED SET IS 100% DATA, NEVER CODE (this is deliberate, not just
tidy): every path this module actually blocks comes from the
`R3_GUARD_PROTECT` environment variable — an `os.pathsep`-joined list of
specs, each one of:

  - an absolute FILE path                    → protects exactly that file
  - an absolute DIRECTORY path (trailing
    `os.sep`)                                → protects everything under it
  - a pattern containing `*`/`?`/`[`          → `fnmatch` glob (note:
                                                 `fnmatch`'s `*` matches
                                                 ACROSS path separators too,
                                                 so one glob covers every
                                                 depth a rig's own
                                                 `tempfile.mkdtemp()`-
                                                 randomized instance dir
                                                 might land at — the
                                                 "protected-DIRECTORY prefix
                                                 match" unit-style rigs need
                                                 without this module ever
                                                 having to know a single
                                                 rig's directory naming
                                                 scheme)

This module hardcodes NOTHING about which paths are "the" ingress files —
not `worker-inbox.jsonl`, not `operator-inbox.jsonl`. `scripts/l1.sh` is
the ONE place that policy lives today (operator_inbox only — see its own
comment for why worker_inbox is deliberately NOT yet in that list: it is
the one piece of the R3 pivot still awaiting an operator ruling on MODEL
A/B). Flipping that policy later is a ONE-LINE CHANGE to what `l1.sh`
exports into `R3_GUARD_PROTECT` — never a code change here.

GUARDED EVENTS (audit hook, not monkeypatching — every documented way
CPython raises 'a write is about to happen', including ones a
future stdlib idiom this module's author never enumerated will likely
still raise, since these are the SAME finite set of low-level events every
higher-level write (`open().write`, `Path.write_text`, `csv.writer`,
`json.dump`, ...) ultimately funnels through):

  'open'         write-intent from EITHER the mode string containing any
                 of w/a/x/+ (builtin `open`/`io.open`/`Path.open`, which
                 `Path.write_text`/`write_bytes`/`csv.writer(open(...))`
                 all fall through to) OR — when mode is None, as with
                 `os.open` — the raw flags int carrying any of
                 O_WRONLY|O_RDWR|O_APPEND|O_CREAT|O_TRUNC. DENY BY DEFAULT
                 on an unresolvable flags value.
  'os.rename'    covers `os.replace` too (verified empirically — CPython
                 raises the SAME 'os.rename' audit event for `os.replace`,
                 there is no separate 'os.replace' event); guards BOTH
                 args[0] (src) AND args[1] (dst) — dst catches the
                 write-tmp-then-atomic-rename-onto-the-real-path evasion
                 (at the rename, not the legal tmp-file open); src catches
                 a rig renaming the PROTECTED file itself away to an
                 unprotected path (destruction-by-move-away — the bytes
                 under the protected name are gone either way).
  'os.truncate'  guards args[0] (path).
  'os.link'      guards args[1] (dst) — a hardlink is a second directory
                 entry for the SAME inode; blocking it stops a rig from
                 aliasing a fresh path onto the protected file's bytes.
  'os.symlink'   guards args[1] (dst) — same reasoning, one level of
                 indirection.
  'os.remove'    guards args[0] (path). CPython raises the SAME
                 'os.remove' audit event for `os.unlink` (verified
                 empirically — `os.unlink` is a bare alias for
                 `os.remove`, no separate event exists), so this one
                 branch covers both spellings, plus `shutil.move`'s
                 cross-device fallback (`copy2` then `os.unlink(src)`
                 when rename can't cross filesystems) — the unlink half of
                 that fallback dies here even though the copy2 half writes
                 an UNPROTECTED destination.
  'os.rmdir'     guards args[0] (path) — a protected DIRECTORY spec's own
                 root, or an ancestor a glob/dir spec still matches.

DIR_FD / OPENAT FAIL-CLOSED RULE: `os.open(basename, flags,
dir_fd=some_open_dir_fd)` hands the 'open' audit event ONLY the bare
RELATIVE filename — no dir_fd, no absolute base, nothing this module could
resolve against. Blindly `realpath`-ing that relative candidate resolves
it against the process's CWD instead — the WRONG base — very likely
matching nothing, and the write sails through even though it landed on
the protected file via the dir_fd's real directory. This applies to
`os.remove`/`os.rmdir`/`os.rename` too (all accept a `dir_fd=` kwarg the
same way). FAIL-CLOSED fix, applied uniformly to every guarded path slot
via `_protected()`: any RELATIVE candidate whose BASENAME matches a
protected basename is denied UNCONDITIONALLY — never resolved against
CWD, never given the benefit of the doubt, regardless of whether it
happens to also resolve to an existing file. This trades a small
false-RED risk (a same-named but genuinely unrelated relative write, e.g.
a rig's own relative temp file that happens to end in the exact protected
basename) for closing a real, demonstrated bypass; every legitimate
relative write in this tree uses a temp filename that does not collide
with a protected basename — verified by `scripts/l1.sh` staying 30/30
green with this rule active.

NON-BYPASSABLE FROM RIG CODE: install() is idempotent (a module-level
sentinel — `sys.modules` caches this module, so a second `import
r3_guard; r3_guard.install()` from rig code is a no-op, never a second
hook). `del sys.addaudithook` from rig code does NOT remove hooks already
installed — CPython's own audit-hook list has no corresponding
`removeaudithook`; deleting the attribute only prevents ADDING new ones
from that point forward. Verified live by `.github/scripts/
r3_guard_runtime_check.py` (a case explicitly does `del sys.addaudithook`
then attempts a protected write, and the write still dies).

THE KNOWN, DOCUMENTED HOLE — child processes: `sys.addaudithook` is
per-interpreter. `subprocess`/`os.exec*`/`os.system` start a NEW process
image; nothing about this module's hook travels with it (this is a
CPython/OS fact, not a bug to fix here). A rig that shells out to write a
protected path bypasses this guard entirely. CORRECTED CLAIM (a prior
version of this paragraph said this surface was OWNED by
`core/r3_lint.py`'s static `_check_subprocess_redirect` — WRONG, that
check gated on a textual `>`/`>>` shell-redirect and let a plain
`subprocess.run([sys.executable, "-c", code, protected_path, payload])`
through clean, no redirect syntax required to hand a child a tainted
path): `core/r3_lint.py` now denies-by-default on ANY subprocess/
os.exec*/os.spawn* call carrying a TAINTED argument, no redirect-syntax
requirement (see its module docstring and required-RED fixture 36). The
TRUE residual — never closeable statically, by construction — is a child
invocation built from NO tainted argument at all (every argument a bare
literal, the protected path reconstructed or hardcoded independently
rather than derived from a traced marker): there is no taint to see, so
no static prover can catch it; only a runtime, per-process mechanism like
this module could, and this module's own hook does not propagate through
`exec` either (below). `.github/scripts/r3_guard_runtime_check.py` proves
the runtime half of this hole EXPLICITLY (a guarded parent spawns an
unguarded child that writes the protected path, and the proof asserts
that SUCCEEDS) — an acknowledged gap, never a silently-assumed one.
"""
import fnmatch
import os
import sys

_ENV_PROTECT = "R3_GUARD_PROTECT"
_ENV_RIG = "R3_GUARD_RIG"

_installed = False

_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_WRITE_MODE_CHARS = "wax+"


def _parse_specs(raw):
    """`R3_GUARD_PROTECT` -> `[(kind, value), ...]`, `kind` in
    `{"exact", "dir", "glob"}`. Every non-empty `os.pathsep`-joined entry is
    classified by its own SHAPE alone — never by guessing what it names."""
    specs = []
    for entry in (raw or "").split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        if any(c in entry for c in "*?["):
            specs.append(("glob", entry))
        elif entry.endswith(os.sep):
            specs.append(("dir", os.path.realpath(entry.rstrip(os.sep)) or os.sep))
        else:
            specs.append(("exact", entry))
    return specs


def _resolve_path(raw):
    """Any of the shapes CPython's audit events hand us for a "path" slot —
    `str`/`bytes`/`os.PathLike`/an open file descriptor (`int`, as
    `os.truncate(fd, n)` legally accepts) — to a `realpath` string, or
    `None` if it cannot be resolved at all (never treated as a match in
    that case; the SPECIFIC candidate is simply not checkable, this is not
    a deny-by-default position on unresolvable candidates — genuinely
    unresolvable targets are extremely rare here and not this module's
    threat model, which is enumerated FS write mechanisms, not fd
    provenance obfuscation)."""
    if raw is None:
        return None
    if isinstance(raw, int):
        try:
            raw = os.readlink(f"/proc/self/fd/{raw}")
        except OSError:
            return None
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = os.fsdecode(bytes(raw))
        except Exception:
            return None
    try:
        raw = os.fspath(raw)
    except TypeError:
        return None
    try:
        return os.path.realpath(raw)
    except Exception:
        return None


def _same_file(candidate_real, exact_spec):
    """`os.path.realpath` string equality FIRST, then — only when both
    sides actually exist — `(st_dev, st_ino)` identity as a second,
    independent proof (never the only proof: the protected ingress file
    frequently does NOT exist yet, e.g. an inbox before its first write —
    `realpath` alone still resolves deterministically in that case since it
    only needs to resolve symlinks in the EXISTING ancestor directories)."""
    spec_real = os.path.realpath(exact_spec)
    if candidate_real == spec_real:
        return True
    try:
        if os.path.exists(candidate_real) and os.path.exists(spec_real):
            a, b = os.stat(candidate_real), os.stat(spec_real)
            return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)
    except OSError:
        pass
    return False


def _matches(specs, candidate_real):
    if candidate_real is None:
        return False
    for kind, val in specs:
        if kind == "exact":
            if _same_file(candidate_real, val):
                return True
        elif kind == "dir":
            if candidate_real == val or candidate_real.startswith(val + os.sep):
                return True
        elif kind == "glob":
            if fnmatch.fnmatchcase(candidate_real, val):
                return True
    return False


def _raw_str(raw):
    """Best-effort `str()` of a "path" audit-event slot WITHOUT resolving
    it against CWD — used only to inspect the RAW shape (is it relative?
    what is its basename?) ahead of, or instead of, `_resolve_path`'s
    realpath resolution. `None` for anything not already string/bytes/
    PathLike-shaped (an fd int, or unresolvable bytes) — never guessed;
    an fd int is never "relative" in the sense this helper cares about."""
    if raw is None or isinstance(raw, int):
        return None
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = os.fsdecode(bytes(raw))
        except Exception:
            return None
    try:
        return os.fspath(raw)
    except TypeError:
        return None


def _protected_basename_match(specs, raw):
    """FAIL-CLOSED dir_fd/openat bypass close (see module docstring): a
    RELATIVE candidate is never realpath-resolved against CWD here — it is
    tested by BASENAME alone against every "exact"/"glob" protected spec's
    own basename. An ABSOLUTE candidate always returns False (it has a
    real base already; `_resolve_path`+`_matches` is the correct, more
    precise check for it). "dir" specs are skipped deliberately — a
    protected-DIRECTORY prefix rule has no single meaningful basename to
    compare a bare relative filename against."""
    s = _raw_str(raw)
    if s is None or os.path.isabs(s):
        return False
    base = os.path.basename(s)
    if not base:
        return False
    for kind, val in specs:
        if kind == "exact" and os.path.basename(val) == base:
            return True
        if kind == "glob" and fnmatch.fnmatchcase(base, os.path.basename(val)):
            return True
    return False


def _protected(specs, raw):
    """The ONE decision point for "does this raw path slot denote a
    protected path" — shared by every guarded event, so the dir_fd/openat
    fail-closed basename rule is never a per-event special case a hostile
    review can find missing from the NEXT event this module adds. Checks
    the fail-closed relative-basename rule FIRST (cheap, and correct even
    when the candidate does not exist / cannot be realpath-resolved at
    all), then falls back to full realpath resolution. Returns
    `(matched, display)` — `display` is whichever form was actually
    matched against, for the denial message."""
    if _protected_basename_match(specs, raw):
        return True, _raw_str(raw)
    cand = _resolve_path(raw)
    return _matches(specs, cand), cand


def _is_write_open(mode, flags):
    """DENY BY DEFAULT: an unresolvable flags value (shouldn't happen —
    CPython always hands a real int here — but if it ever doesn't, treat
    it as a possible write rather than silently waving it through)."""
    if mode is not None:
        return any(c in mode for c in _WRITE_MODE_CHARS)
    try:
        return bool(int(flags) & _WRITE_FLAGS)
    except (TypeError, ValueError):
        return True


def install():
    """Install the audit hook once per process. A no-op on every call after
    the first (idempotent by design — see module docstring's
    non-bypassable claim) and a no-op entirely if `R3_GUARD_PROTECT` is
    empty/unset (an explicit opt-in per process, never ambient)."""
    global _installed
    if _installed:
        return
    _installed = True
    specs = _parse_specs(os.environ.get(_ENV_PROTECT, ""))
    if not specs:
        return
    rig = os.environ.get(_ENV_RIG, "<unknown-rig>")

    def _deny(event, path):
        raise PermissionError(
            f"r3_guard: rig '{rig}' attempted {event} on protected ingress "
            f"path {path!r}. Writes to an ingress file must go through the "
            "real door (scripts/report.sh), never rig-internal I/O — see "
            "core/r3_lint.py / core/r3_guard.py."
        )

    def hook(event, args):
        if event == "open":
            path, mode, flags = args
            if not _is_write_open(mode, flags):
                return
            matched, display = _protected(specs, path)
            if matched:
                _deny("open() for write", display)
        elif event == "os.rename":
            # guard BOTH slots: dst (write-tmp-then-atomic-rename-onto-the-
            # real-path evasion) AND src (rig renames the protected file
            # itself AWAY — destruction by move-away).
            matched, display = _protected(specs, args[1])
            if matched:
                _deny("os.rename/os.replace onto", display)
            matched, display = _protected(specs, args[0])
            if matched:
                _deny("os.rename/os.replace (move-away) of", display)
        elif event == "os.truncate":
            matched, display = _protected(specs, args[0])
            if matched:
                _deny("os.truncate", display)
        elif event == "os.link":
            matched, display = _protected(specs, args[1])
            if matched:
                _deny("os.link (hardlink) onto", display)
        elif event == "os.symlink":
            matched, display = _protected(specs, args[1])
            if matched:
                _deny("os.symlink onto", display)
        elif event == "os.remove":
            # covers os.unlink too (same audit event — see module
            # docstring) — also the unlink half of shutil.move's
            # cross-device copy2+unlink fallback.
            matched, display = _protected(specs, args[0])
            if matched:
                _deny("os.remove/os.unlink of", display)
        elif event == "os.rmdir":
            matched, display = _protected(specs, args[0])
            if matched:
                _deny("os.rmdir of", display)

    sys.addaudithook(hook)


_SITECUSTOMIZE_TEMPLATE = '''\
# AUTO-GENERATED by core/r3_guard.materialize_site_dir — block 01-40 T1.
# Installs the R3 runtime write-guard for every rig process that inherits
# this directory on PYTHONPATH. sitecustomize.py (never PYTHONSTARTUP —
# that one only fires for interactive sessions, not `python3 script.py`)
# is imported automatically by the stdlib `site` module at interpreter
# startup whenever its own directory is importable.
import sys
sys.path.insert(0, {core_dir!r})
import r3_guard
r3_guard.install()
'''


def materialize_site_dir(site_dir, core_dir=None):
    """Write `sitecustomize.py` into `site_dir` (created if needed).
    Prepending `site_dir` to a child process's `PYTHONPATH` is then the
    ENTIRE wiring needed to install the guard in that process — no rig
    code changes, ever. `core_dir` (defaults to this module's own
    directory) is the one path baked in at generation time; it only says
    WHERE `r3_guard.py` itself lives, never WHAT it protects — that is
    still 100% `R3_GUARD_PROTECT`, read fresh by `install()` in the child's
    own environment."""
    core_dir = os.path.abspath(core_dir or os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(site_dir, exist_ok=True)
    path = os.path.join(site_dir, "sitecustomize.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_SITECUSTOMIZE_TEMPLATE.format(core_dir=core_dir))
    return path


def _cli():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--write-site-dir", required=True,
                    help="directory to materialize sitecustomize.py into")
    ns = p.parse_args()
    print(materialize_site_dir(ns.write_site_dir))


if __name__ == "__main__":
    _cli()
