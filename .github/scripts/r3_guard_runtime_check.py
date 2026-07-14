#!/usr/bin/env python3
"""r3_guard_runtime_check.py — runtime write-guard CI proof (block 01-40 T1,
Opus-pivot item 2, ruling-independent).

`core/r3_lint.py` proves no rig AST *shape* fabricates a sender or bypasses
the drain. `core/r3_guard.py` is the runtime backstop: an
`sys.addaudithook` that makes a genuinely protected ingress path physically
UNWRITABLE from Python code in that process, independent of mechanism. This
script spawns REAL `python3` child processes with the guard wired exactly
the way `scripts/l1.sh` wires it (via `materialize_site_dir` +
`R3_GUARD_PROTECT`/`PYTHONPATH`) and proves, live:

  DIES     builtin `open()` write, `os.open`+write-flags, `pathlib
           Path.write_text`, a tmp-file-then-`os.replace` onto the
           protected path, and `csv.writer` over an `open()` of the
           protected path (caught AT THE OPEN, before csv ever gets a
           handle) — every one of these against the protected file.
  DIES     (block 01-40 T1, second pass — hostile-review closures) —
           `os.open(basename, flags, dir_fd=dfd)` (the dir_fd/openat
           bypass: the audit event hands the hook ONLY the bare relative
           filename, no dir_fd, which the OLD code resolved against the
           wrong base — CWD — and missed; now denied by RELATIVE-basename
           match, never resolved against CWD at all), `os.remove` /
           `os.unlink` of the protected file, `os.rename`/`os.replace`
           MOVING the protected file AWAY to an unprotected path (not just
           writes ONTO it), and `shutil.move` of the protected file (same-
           filesystem rename, or cross-device copy2+unlink — either way,
           the protected file's bytes are gone or aliased away, denied).
           Each of these asserts BOTH the protected file's CONTENT and its
           EXISTENCE are unchanged after the child dies.
  SURVIVES a read-mode `open()` of the protected file, and a write to an
           UNPROTECTED sibling path.
  SURVIVES (documented, not a bug) — `del sys.addaudithook` from rig code
           does not remove the already-installed hook; a further protected
           write still dies.
  SUCCEEDS (documented hole, asserted EXPLICITLY) — a subprocess CHILD the
           guarded process spawns, without the guard's own PYTHONPATH/env
           wired into it, writes the protected file successfully: audit
           hooks do not propagate through exec. CORRECTED CLAIM: a prior
           version of this comment said this surface was owned by
           `core/r3_lint.py`'s static subprocess-shell-REDIRECT check —
           WRONG, that check required a `>`/`>>` redirect and missed a
           plain argv-only `subprocess.run([sys.executable, "-c", code,
           protected_path, payload])`. `core/r3_lint.py` now denies-by-
           default on ANY subprocess/os.exec*/os.spawn* call carrying a
           WORKER/OPERATOR-tainted argument, no redirect syntax required
           (see both docstrings, and `.github/scripts/
           r3_honesty_lint_check.py` fixture 36). The TRUE residual is a
           child invocation built from NO tainted argument at all — see
           both docstrings' honest-limits sections.

Exit 0 only if every one of the above holds.
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CORE = os.path.join(ROOT, "core")
sys.path.insert(0, CORE)

import r3_guard  # noqa: E402


def _guarded_env(protect_specs, site_dir, rig="proof-rig"):
    r3_guard.materialize_site_dir(site_dir)
    env = dict(os.environ)
    env["PYTHONPATH"] = site_dir + os.pathsep + env.get("PYTHONPATH", "")
    env["R3_GUARD_PROTECT"] = os.pathsep.join(protect_specs)
    env["R3_GUARD_RIG"] = rig
    return env


def _run(code, env, timeout=20):
    return subprocess.run([sys.executable, "-c", code], env=env,
                           capture_output=True, text=True, timeout=timeout,
                           cwd=ROOT)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _snapshot(path):
    """(exists, content-or-None) — never raises on a missing file (several
    of the block 01-40 T1 second-pass DIES cases are DESTRUCTION attempts;
    if the guard ever regressed and let one through, the file could be
    genuinely GONE afterward — this must observe that, not crash)."""
    exists = os.path.exists(path)
    return exists, (_read(path) if exists else None)


def main():
    failed = False
    work = tempfile.mkdtemp(prefix="r3-guard-proof-")
    site_dir = os.path.join(work, "site")
    protected = os.path.join(work, "instance", "operator-inbox.jsonl")
    unprotected = os.path.join(work, "instance", "worker-inbox.jsonl")
    os.makedirs(os.path.dirname(protected), exist_ok=True)
    with open(protected, "w", encoding="utf-8") as fh:
        fh.write("seed\n")

    env = _guarded_env([protected], site_dir, rig="r3_guard_runtime_check")

    def expect_dies(name, code):
        """DIES: the child must exit non-zero via the guard's own
        PermissionError, AND the protected file's EXISTENCE and CONTENT
        must both be exactly unchanged afterward — covers write-mode
        opens (content-only concern, existence trivially unchanged) and
        destruction/move-away attempts (existence is the real assertion)
        with the SAME check."""
        nonlocal failed
        before_exists, before = _snapshot(protected)
        r = _run(code, env)
        after_exists, after = _snapshot(protected)
        if r.returncode == 0:
            print(f"REGRESSION [{name}]: expected the guard to kill this write "
                  f"(protected file unchanged), but the child exited 0. "
                  f"stdout={r.stdout!r} stderr={r.stderr!r}", file=sys.stderr)
            failed = True
        elif not after_exists:
            print(f"REGRESSION [{name}]: child died (rc={r.returncode}) but the "
                  f"protected file is GONE afterward (existed before={before_exists}) "
                  "— a destructive op landed before the guard fired.", file=sys.stderr)
            failed = True
        elif after != before:
            print(f"REGRESSION [{name}]: child died (rc={r.returncode}) but the "
                  f"protected file's content CHANGED anyway (before={before!r} "
                  f"after={after!r}) — the write landed before the guard fired.",
                  file=sys.stderr)
            failed = True
        elif "r3_guard" not in r.stderr and "PermissionError" not in r.stderr:
            print(f"REGRESSION [{name}]: child died (rc={r.returncode}) but not "
                  f"via the guard's PermissionError — stderr={r.stderr!r}",
                  file=sys.stderr)
            failed = True
        else:
            print(f"DIES confirmed [{name}]: rc={r.returncode}, existence+content "
                  "unchanged, guard's PermissionError raised.")

    def expect_survives(name, code, check=None):
        nonlocal failed
        r = _run(code, env)
        if r.returncode != 0:
            print(f"REGRESSION [{name}]: expected this to survive the guard, but "
                  f"the child died (rc={r.returncode}) stderr={r.stderr!r}",
                  file=sys.stderr)
            failed = True
        elif check is not None and not check(r):
            print(f"REGRESSION [{name}]: child exited 0 but the expected effect "
                  f"did not happen — stdout={r.stdout!r}", file=sys.stderr)
            failed = True
        else:
            print(f"SURVIVES confirmed [{name}]: rc=0.")

    # ── DIES: builtin open() write ──
    expect_dies("builtin_open_write", f"""
open({protected!r}, "w").write("pwned")
""")

    # ── DIES: os.open + os.write (denied at the os.open itself, mode=None
    #     path — the raw O_* flags int, per the module docstring) ──
    expect_dies("os_open_os_write", f"""
import os
fd = os.open({protected!r}, os.O_WRONLY | os.O_TRUNC)
os.write(fd, b"pwned")
os.close(fd)
""")

    # ── DIES: pathlib write_text ──
    expect_dies("pathlib_write_text", f"""
import pathlib
pathlib.Path({protected!r}).write_text("pwned")
""")

    # ── DIES: tmp-file-then-os.replace onto the protected path (the write
    #     itself, into the TMP file, must legitimately succeed — only the
    #     replace onto the protected dst is denied) ──
    expect_dies("tmp_then_os_replace", f"""
import os
tmp = {protected!r} + ".tmp"
with open(tmp, "w") as fh:
    fh.write("pwned")
os.replace(tmp, {protected!r})
""")

    # ── DIES: csv.writer over an open() of the protected path — caught AT
    #     THE OPEN, csv.writer never gets a handle at all ──
    expect_dies("csv_writer_over_open", f"""
import csv
with open({protected!r}, "a", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["pwned"])
""")

    # ── DIES: `del sys.addaudithook` does not remove the installed hook ──
    expect_dies("del_addaudithook_does_not_bypass", f"""
import sys
del sys.addaudithook
open({protected!r}, "w").write("pwned")
""")

    # ── DIES (block 01-40 T1, second pass — hostile-review closure #1):
    #     `os.open(basename, flags, dir_fd=dfd)` — the audit 'open' event
    #     hands the hook ONLY the bare relative filename, no dir_fd. The
    #     OLD code realpath-resolved that against the WRONG base (this
    #     child's CWD, not dfd's directory), found nothing, and let the
    #     write through. Now denied by the RELATIVE-basename fail-closed
    #     rule, never resolved against CWD at all. ──
    expect_dies("dir_fd_openat_bypass", f"""
import os
protected = {protected!r}
dfd = os.open(os.path.dirname(protected), os.O_RDONLY)
fd = os.open(os.path.basename(protected), os.O_WRONLY | os.O_TRUNC, dir_fd=dfd)
os.write(fd, b"pwned-dirfd")
os.close(fd)
os.close(dfd)
""")

    # ── DIES (hostile-review closure #2a): os.remove of the protected
    #     file itself — pure destruction, no open()/rename() involved,
    #     the OLD hook had no 'os.remove' branch at all. ──
    expect_dies("os_remove_destroys_protected", f"""
import os
os.remove({protected!r})
""")

    # ── DIES (hostile-review closure #2b): os.rename MOVING the protected
    #     file AWAY to an unprotected path — the OLD hook only guarded
    #     args[1] (dst onto the protected path), never args[0] (src moved
    #     off of it); the bytes under the protected name are gone either
    #     way. ──
    expect_dies("os_rename_move_away_destroys_protected", f"""
import os
protected = {protected!r}
os.rename(protected, protected + ".moved-away")
""")

    # ── DIES (hostile-review closure #2c): shutil.move of the protected
    #     file — same-filesystem uses os.rename internally (caught by the
    #     src-check above); a cross-device move falls back to copy2 +
    #     os.unlink(src) (caught by the os.remove branch instead). Either
    #     way the protected file must survive untouched. ──
    expect_dies("shutil_move_destroys_protected", f"""
import shutil
protected = {protected!r}
shutil.move(protected, protected + ".moved-by-shutil")
""")

    # ── SURVIVES: read-mode open of the protected path ──
    expect_survives("read_mode_open_survives", f"""
data = open({protected!r}, "r").read()
assert data == "seed\\n", data
print("read ok")
""", check=lambda r: "read ok" in r.stdout)

    # ── SURVIVES: write to an unprotected sibling path ──
    expect_survives("unprotected_write_survives", f"""
open({unprotected!r}, "w").write("fine")
print("unprotected ok")
""", check=lambda r: "unprotected ok" in r.stdout)

    # ── SUCCEEDS (documented hole): a subprocess child, spawned by a
    #     GUARDED parent, without the guard's env wired into it, writes the
    #     protected path successfully — audit hooks do not propagate
    #     through exec. Asserted here explicitly, never silently assumed. ──
    before = _read(protected)
    r = _run(f"""
import os
import subprocess
import sys

clean_env = dict(os.environ)
clean_env.pop("PYTHONPATH", None)
clean_env.pop("R3_GUARD_PROTECT", None)
clean_env.pop("R3_GUARD_RIG", None)
grandchild = subprocess.run(
    [sys.executable, "-c", "open({protected!r}, 'w').write('pwned-by-child')"],
    env=clean_env, capture_output=True, text=True,
)
print("GRANDCHILD_RC", grandchild.returncode)
print("GRANDCHILD_STDERR", grandchild.stderr)
""", env)
    after = _read(protected)
    if r.returncode != 0:
        print(f"REGRESSION [documented_hole_subprocess_child]: the guarded "
              f"PARENT unexpectedly died — rc={r.returncode} stderr={r.stderr!r}",
              file=sys.stderr)
        failed = True
    elif "GRANDCHILD_RC 0" not in r.stdout:
        print(f"REGRESSION [documented_hole_subprocess_child]: expected the "
              f"unguarded grandchild to SUCCEED (documenting the known hole), "
              f"but it did not — stdout={r.stdout!r}", file=sys.stderr)
        failed = True
    elif after != "pwned-by-child":
        print(f"REGRESSION [documented_hole_subprocess_child]: grandchild "
              f"reported rc=0 but the protected file's content is {after!r}, "
              "not 'pwned-by-child' — the write did not actually land.",
              file=sys.stderr)
        failed = True
    else:
        print("DOCUMENTED HOLE confirmed [documented_hole_subprocess_child]: "
              "a subprocess child NOT wired with the guard's env wrote the "
              "protected file successfully (before={!r}, after={!r}) — audit "
              "hooks do not propagate through exec, a CPython/OS fact this "
              "module cannot fix. core/r3_lint.py denies-by-default on ANY "
              "subprocess/os.exec/os.spawn call carrying a WORKER/OPERATOR- "
              "tainted argument (no redirect-syntax requirement — a PRIOR "
              "version required one and was WRONG, see both docstrings); the "
              "TRUE residual is a child invocation built from NO tainted "
              "argument at all, undetectable by either module.".format(before, after))
        with open(protected, "w", encoding="utf-8") as fh:
            fh.write("seed\n")   # reset for any later case in this run

    print(f"\nr3_guard_runtime_check: {'PASS' if not failed else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
