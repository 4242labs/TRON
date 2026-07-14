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

DESIGN: DENY-BY-DEFAULT OVER EVERY AUDIT EVENT — THE TERMINAL FIX (block
01-40 T1, EIGHTH hostile review). Every one of the seven prior review
rounds added ANOTHER individually-named branch to this hook — 'open',
then 'os.rename', 'os.truncate', 'os.link', 'os.symlink', 'os.chmod',
'os.chown', 'os.remove', 'os.rmdir' — and every round after that found
the NEXT ordinary `os.*` mutating call this module had simply never
enumerated (THIS round: `os.utime`, `os.setxattr`, `os.removexattr` all
sailed straight through and mutated a protected file, unguarded, because
no branch named them). That is an ADDITIVE-BY-DISCOVERY coverage model —
structurally guaranteed to have a next gap, because CPython's own
audit-event surface is neither closed nor stable, and each round was
betting it could out-enumerate that surface one hostile review at a time.
It cannot. This round replaces the enumeration with the CLASS fix:

  hook(event, args):
    1. event == "open"                    → UNCHANGED special case (see
                                             `_is_write_open`, below): the
                                             ONE event that is
                                             legitimately BOTH a read AND
                                             a write depending on
                                             mode/flags — SURVIVES a
                                             read-mode open of a
                                             protected path, DENIES a
                                             write-mode one.
    2. event in `_SAFE_EVENTS`, or
       event starts with a
       `_SAFE_EVENT_PREFIXES` entry        → ALLOWED UNCONDITIONALLY —
                                             the allow-list below is now
                                             THE ONLY EXEMPTION SURFACE IN
                                             THE ENTIRE MODULE.
    3. every other event, WHATEVER ITS
       NAME                                → DENY BY DEFAULT the moment
                                             ANY of its raw arguments
                                             resolves to a protected
                                             candidate — string/bytes/
                                             `os.PathLike` checked as a
                                             path, `int` checked as an
                                             open fd via `/proc/self/fd`
                                             (the SAME `_resolve_path`
                                             this module already used for
                                             every hand-named branch) —
                                             through the exact same
                                             `_protected()` (fail-closed
                                             relative-basename rule, then
                                             realpath, then inode-identity
                                             alias match) every
                                             previously hand-named branch
                                             already called. A brand-new
                                             `os.*` mutating call this
                                             module's author has STILL
                                             never heard of — the NEXT
                                             hostile-review discovery — is
                                             denied the moment it touches
                                             a protected path, BY
                                             CONSTRUCTION, with ZERO code
                                             change here. The enumeration
                                             gap is closed structurally,
                                             never by listing one more op.

ALLOW-LIST IS THE ONLY EXEMPTION SURFACE (`_SAFE_EVENTS` /
`_SAFE_EVENT_PREFIXES`) — kept intentionally TIGHT, every entry verified
EMPIRICALLY on this interpreter (a throwaway `sys.addaudithook` probe
script, not guessed from documentation) to (a) actually fire as its own
distinct audit event at all, and (b) never itself write/mutate/alias a
path — only read or execute:

  os.listdir / os.scandir / os.walk / os.fwalk    directory LISTING /
                                                    TRAVERSAL — read-only.
  glob.glob / glob.glob/2 / pathlib.Path.glob /
  pathlib.Path.rglob / pathlib.Path.walk           pattern-matching
                                                    traversal, built on
                                                    the same read-only
                                                    scandir underneath.
  os.getxattr / os.listxattr                       extended-attribute
                                                    READS — contrast
                                                    `os.setxattr` /
                                                    `os.removexattr`,
                                                    which MUTATE and are
                                                    deliberately NOT
                                                    allow-listed (THIS
                                                    round's own finding —
                                                    see below).
  import / compile / exec                          code loading /
                                                    execution — never
                                                    itself a filesystem
                                                    write, whatever
                                                    filename LABEL is
                                                    attached to the code
                                                    object (`compile`'s
                                                    `filename` arg is an
                                                    inert label, not a
                                                    write target —
                                                    `compile()` cannot
                                                    write a file
                                                    regardless of its
                                                    content); the actual
                                                    bytecode-cache WRITE a
                                                    fresh `import`
                                                    performs goes through
                                                    a SEPARATE,
                                                    already-guarded 'open'
                                                    event.
  socket.*  (PREFIX, the one prefix rule
             in this list)                         network transport —
                                                    never a filesystem
                                                    write to a protected
                                                    path; enumerating
                                                    every `socket.*` event
                                                    name (`connect`,
                                                    `bind`, `__new__`,
                                                    `sendmsg`, ...) one at
                                                    a time would be
                                                    exactly the additive-
                                                    enumeration mistake
                                                    this rewrite exists to
                                                    stop — the CATEGORY,
                                                    not the individual
                                                    event name, is what
                                                    makes these safe.

  (`os.stat`/`os.lstat`/`os.access`/`os.mkfifo`/`os.mknod` do not appear
  above: empirically, THIS interpreter raises no audit event for them at
  all — they never reach `hook()` in the first place, allow-listed or
  not; noted here so a future reader does not go looking for a branch
  that was never needed.)

Anything NOT in this list — including an `os.*` mutating call invented in
a future CPython release, or one that simply existed all along and nobody
tried yet — is denied by default the instant it names a protected
candidate. `.github/scripts/r3_guard_runtime_check.py` proves this
CONSTRUCTIVELY, not just for the three named gaps THIS round found
(`os.utime`, `os.setxattr`, `os.removexattr`): one case drives `os.mkdir`
— an event this module has NEVER special-cased, in any of the eight
rounds, on either side of this rewrite — directly at a protected path and
asserts `PermissionError`, so a regression in the allow-list (or a return
to per-event enumeration) surfaces in CI the moment it reintroduces a
gap, without needing a NINTH hostile review to find the next named op
first.

WHAT THE OLD PER-EVENT BRANCHES USED TO SAY, now subsumed: 'os.rename'
(covers `os.replace` too — CPython raises the SAME event for both, no
separate `os.replace` event exists) guarded both `args[0]`/src (a rig
renaming the PROTECTED file itself away — destruction-by-move-away) and
`args[1]`/dst (write-tmp-then-atomic-rename-onto-the-real-path); 'os.link'
and 'os.symlink' guarded both slots the same way (source-side closure:
aliasing the protected file's bytes under a fresh, unprotected name has
no legitimate use); 'os.chmod'/'os.chown' guarded a channel-breaking DoS
that leaves CONTENT and EXISTENCE both unchanged (`os.chmod(protected,
0o000)` would otherwise permanently lock even the real door,
scripts/report.sh, out of the path, invisible to every content/existence
snapshot proof); 'os.remove' covered `os.unlink` too (a bare alias, no
separate event) plus the unlink half of `shutil.move`'s cross-device
`copy2`+unlink fallback; 'os.rmdir' guarded a protected DIRECTORY spec's
own root. Every one of these is now just a NAME that happens to fall into
branch 3 above — the specific per-event reasoning is preserved here for
context, not because any of it is special-cased in code anymore.

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

ALIAS-RESOLUTION ROOT FIX — inode identity for "glob" specs too (block
01-40 T1, second hostile review): `_same_file` already proved "exact"
specs by BOTH realpath-string equality AND, when both sides exist,
`(st_dev, st_ino)` identity — but `_matches`'s "glob" branch (the spec
KIND `scripts/l1.sh` actually exports in production,
`R3_GUARD_PROTECT="$SANDBOX/*operator-inbox.jsonl"`) was pure `fnmatch`
STRING compare with no inode fallback at all. A hardlink whose OWN path
does not textually match the glob pattern — `os.link(protected,
"unrelated")` then `open("unrelated", "w")` — shares the SAME inode as the
protected file yet sailed through: the `os.link` call's dst ("unrelated")
never matched the glob string, and the later `open`'s candidate
("unrelated") never matched it either. Worse, this defeats even a
hardlink this process's own hook never SAW get created at all (one
pre-existing before `install()` ran, or built by an unguarded child per
this module's own documented subprocess hole below) — no creation event
to deny in the first place, only the alias-identity check at the point of
use can catch it. `_glob_inode_match` closes this GENERICALLY, the same
way `_same_file` already does for "exact": whenever the candidate
physically exists, also match if its `(st_dev, st_ino)` equals that of any
CURRENTLY-EXISTING real file the glob pattern textually matches (`glob.
glob(spec)`, stat each hit, compare identity) — additive to the existing
fnmatch string check, never a replacement for it (a file that has not yet
been created still needs the string-based proof, exactly as before).

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

THE TRUE RESIDUAL, HONESTLY, AFTER THE DENY-BY-DEFAULT REWRITE — stated
plainly rather than left implicit, because deny-by-default over "every
audit event" is still bounded by what CPython's audit subsystem itself
sees:

  - `ctypes` / raw syscalls. `ctypes.CDLL("libc.so.6").open(...)` (or
    any direct FFI call into libc) calls into the kernel BELOW CPython's
    own `os`/`io` layer entirely — no audit event fires for it, ever, on
    any branch of this hook, allow-listed or not. This is a CPython
    architectural fact (audit hooks are woven into CPython's own C
    implementations of `os.*`/`io.*`, not into the syscall boundary
    itself), not something this module — or any pure-Python audit-hook
    mechanism — can close.
  - `fchmod`/similar fd-based ops on an fd whose OWN `open()` was itself
    unguarded. This sounds like a gap but is adversarial-only in
    practice: the fd has to come from SOMEWHERE, and the `open()` (or
    `os.open()`) call that MINTED that fd is itself always guarded in
    THIS process (branch 1 above) — the only way to hold an fd this
    hook never saw opened is to receive it from an unguarded process
    (the child-process hole immediately above, `os.pipe`/`socket.
    socketpair` fd-passing via `sendmsg`/`SCM_RIGHTS`, or an
    already-open fd inherited at process start, e.g. fd 3+ passed by a
    parent) — a deliberately adversarial setup, not an ordinary rig
    mistake.

Both are real, both are stated here rather than silently assumed —
consistent with every other honest-limits section in this module and in
`core/r3_lint.py`.
"""
import fnmatch
import glob as glob_mod
import os
import sys

_ENV_PROTECT = "R3_GUARD_PROTECT"
_ENV_RIG = "R3_GUARD_RIG"

_installed = False

_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_WRITE_MODE_CHARS = "wax+"

# THE ONLY EXEMPTION SURFACE in this module (module docstring's "DESIGN:
# DENY-BY-DEFAULT" section) — every entry verified EMPIRICALLY, on this
# interpreter, to (a) fire as its own real audit event and (b) never
# itself write/mutate/alias a filesystem path. Adding to this set is a
# real security decision (it is the ONE way to exempt an event from
# deny-by-default) — never add an event here without the same empirical
# verification (a throwaway `sys.addaudithook` probe), and never add one
# "to make a rig pass" without first confirming the event genuinely never
# writes.
_SAFE_EVENTS = frozenset({
    # directory listing / traversal — read-only.
    "os.listdir", "os.scandir", "os.walk", "os.fwalk",
    "glob.glob", "glob.glob/2",
    "pathlib.Path.glob", "pathlib.Path.rglob", "pathlib.Path.walk",
    # extended-attribute READS — contrast os.setxattr/os.removexattr
    # (MUTATE, deliberately NOT here; this round's own finding).
    "os.getxattr", "os.listxattr",
    # code loading/execution — never itself a filesystem write, whatever
    # filename LABEL is attached to the code object.
    "import", "compile", "exec",
})
# network transport — never a filesystem write to a protected path. A
# PREFIX rule (the only one in this module) because enumerating every
# `socket.*` event name one at a time would be exactly the
# additive-enumeration mistake this rewrite exists to stop.
_SAFE_EVENT_PREFIXES = ("socket.",)


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


def _glob_inode_match(candidate_real, glob_spec):
    """ALIAS-CLOSING fallback for "glob" specs — the ROOT fix for the
    hardlink-via-glob bypass (a second hostile review): `fnmatch` is a pure
    STRING compare, with NO `(st_dev, st_ino)` identity check, unlike the
    "exact" branch's `_same_file`. A hardlink whose OWN path does not
    textually match the glob pattern — created either by THIS process
    (`os.link` with a non-matching dst name) or entirely OUTSIDE this
    process's audit visibility (a pre-existing alias, or one built by an
    unguarded child per this module's own documented subprocess hole) — is
    otherwise invisible to the glob rule even though it shares the exact
    same inode as a real, currently-protected file. Whenever the candidate
    physically exists, ALSO treat it as matched if its `(st_dev, st_ino)`
    identity equals that of ANY currently-existing real file the glob
    pattern textually matches — generalizing `_same_file`'s proof from
    "exact" to "glob", since "glob" is the spec kind `scripts/l1.sh`
    actually exports in production
    (`R3_GUARD_PROTECT="$SANDBOX/*operator-inbox.jsonl"`)."""
    try:
        if not os.path.exists(candidate_real):
            return False
        cand_stat = os.stat(candidate_real)
    except OSError:
        return False
    for hit in glob_mod.glob(glob_spec):
        try:
            hit_real = os.path.realpath(hit)
            if hit_real == candidate_real:
                continue   # already caught by the direct fnmatch string compare
            hit_stat = os.stat(hit_real)
        except OSError:
            continue
        if (cand_stat.st_dev, cand_stat.st_ino) == (hit_stat.st_dev, hit_stat.st_ino):
            return True
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
            if _glob_inode_match(candidate_real, val):
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
        # 1. 'open' — the ONE event that is legitimately BOTH a read and a
        #    write depending on mode/flags; kept as its own special case
        #    (module docstring's DESIGN section, step 1) so a read-mode
        #    open of a protected path keeps surviving.
        if event == "open":
            path, mode, flags = args
            if not _is_write_open(mode, flags):
                return
            matched, display = _protected(specs, path)
            if matched:
                _deny("open() for write", display)
            return
        # 2. the ONLY exemption surface in this module — see
        #    `_SAFE_EVENTS`/`_SAFE_EVENT_PREFIXES` and the module
        #    docstring's ALLOW-LIST section for why each entry is safe.
        if event in _SAFE_EVENTS or event.startswith(_SAFE_EVENT_PREFIXES):
            return
        # 3. DENY BY DEFAULT — every other event, WHATEVER ITS NAME,
        #    including one this module has never seen or named before:
        #    scan every raw argument (never a per-event slot list — that
        #    enumeration is exactly what seven prior rounds kept losing
        #    to) through the SAME `_protected()` resolver every previously
        #    hand-named branch already used, and deny the instant ANY
        #    argument names a protected candidate. `bool` is excluded
        #    (True/False are technically `int` in Python but are never a
        #    meaningful fd number); every other `str`/`bytes`/`bytearray`/
        #    `os.PathLike`/`int` argument is a candidate — `_protected()`
        #    (via `_resolve_path`) already no-ops cleanly on an
        #    unresolvable one (a bare int that is not actually an open fd
        #    simply fails to resolve and is never treated as a match).
        for raw in args:
            if isinstance(raw, bool):
                continue
            if not isinstance(raw, (str, bytes, bytearray, int)) and not hasattr(raw, "__fspath__"):
                continue
            matched, display = _protected(specs, raw)
            if matched:
                _deny(event, display)

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
