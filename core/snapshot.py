"""core.snapshot — the immutable per-tick view `core.tick`'s decide step reads.

`build(eng) -> Snapshot` performs the WHOLE observe phase in one call
(contracts/blueprint-contracts.md §5's "load MANIFEST → ... → build
snapshot"): `core.state.load` (fresh manifest off disk), drain
`ctx.worker_inbox` (structured `tag`+`slots` JSON lines — NO LLM/classify in
this brick; a `worker.done` line IS a local-pass report, read structurally),
then one `core.gitobs` trunk-tip read. Nothing here is retained between
ticks — `core.tick.tick` discards the `Snapshot` at tick end; this module
keeps no module-level state of its own.

The inbox drain follows the SAME at-least-once idiom `engine/fsm.py::
_claim_inboxes` uses (learned by reading, re-expressed fresh here for the
structured shape this brick reads — never copied, never the raw-text+
classify path that module also carries): rotate the live inbox to a `.proc`
sidecar (atomic rename — a fresh append landing after the rename starts a
new inbox, never lost to a full-file rewrite); if a `.proc` already exists
(the crash residue of a prior tick that drained but never got to persist),
read THAT again instead of rotating a new one, so a report a crashed tick
already consumed from the live file is never silently dropped. The sidecar
is NOT deleted here — `release` (below) is the caller's job, invoked only
AFTER `core.state.save` succeeds, so a crash before persist leaves the
sidecar for the next tick to re-drain. This is the ONE non-git-observable
input `core/gate.py`'s own docstring calls out (`local_report`, `gate.local`
's predicate — "the ONE piece of the DONE ladder that isn't purely
git-observable"); everything else a gate stage needs is re-derived from real
git/grants state on every call, so only THIS input needs the persist-gated
release discipline.

`gates` is a direct alias onto `manifest.setdefault("gates", {})` — mutating
a `gate_state` dict inside it (exactly what `core.gate.advance` does)
mutates the SAME object `core.tick`'s act phase later hands to
`core.state.save`; no separate merge-back step, no copy skew.

No git/subprocess of any kind here beyond `core.gitobs`'s one delegated
call; the `.proc` rotate/read/remove is plain (non-git) file IO.
"""
import collections
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# `state` is imported BEFORE `gitobs` (below) deliberately: `gitobs`'s own
# import transitively puts `engine/` onto `sys.path` (it ships its OWN
# `state.py`, the pre-ADR-0004 `State` class) — Python caches an import by
# bare name in `sys.modules` the FIRST time it resolves, so binding the name
# "state" to `core/state.py` here, before `engine/` is ever on the path,
# keeps it bound to THIS module for the rest of the process regardless of
# what any later import does to `sys.path`. See `core/tick.py`'s matching
# note (it re-imports "state" too — same cached module, no re-resolution).
import state    # noqa: E402 — core/state.py
import gitobs   # noqa: E402 — core/gitobs.py, the ONE git-observation seam


Snapshot = collections.namedtuple(
    "Snapshot", ["manifest", "gates", "trunk_tip", "worker_reports", "local_reports",
                "inbox_sidecar"])


def _drain_inbox(ctx, log):
    """Rotate `ctx.worker_inbox` to a `.proc` sidecar (or re-read a `.proc`
    a crashed prior tick already rotated — at-least-once). Returns
    `(reports, sidecar_path_or_None)`. A malformed/structurally-invalid line
    is logged and skipped — one poison line must never sink the whole tick."""
    path = ctx.worker_inbox
    proc = path + ".proc"
    if not os.path.exists(proc):
        if not os.path.exists(path):
            return [], None
        try:
            os.rename(path, proc)
        except OSError as e:
            log("flow", f"snapshot: inbox rotate failed ({e}); draining nothing this tick")
            return [], None

    reports = []
    with open(proc, "r") as fh:
        lines = fh.readlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            log("flow", f"snapshot: dropped a malformed worker-inbox line: {e}")
            continue
        if not isinstance(rec, dict) or "tag" not in rec:
            log("flow", f"snapshot: dropped a structurally invalid worker-inbox line: {line!r}")
            continue
        reports.append(rec)
    return reports, proc


def build(eng):
    """Assemble this tick's immutable view — the whole observe phase, in one
    call: fresh manifest (`core.state.load`), the structured reports this
    tick's inbox drain surfaced, and one real trunk-tip read
    (`core.gitobs.tip_sha`, never a raw git call)."""
    ctx = eng.ctx
    manifest = state.load(ctx)
    worker_reports, sidecar = _drain_inbox(ctx, eng.log)

    root = eng.paths["root"]
    main_branch = eng.paths.get("main_branch", "main")
    trunk_tip = gitobs.tip_sha(root, main_branch, eng.dry)

    gates = manifest.setdefault("gates", {})

    # A worker.done/local-pass report is the ONE structural shape this brick
    # reads (core/gate.py's own `local_report` kwarg contract: a well-formed
    # `{"verdict": "pass", "evidence": <str>}` dict). Last-one-wins per block
    # if more than one arrived this tick — the same "only what THIS call is
    # handed" discipline `core/gate.py::_advance_local`'s own docstring
    # documents for `local_report` (nothing from a prior tick's report is
    # ever implicitly re-supplied).
    local_reports = {}
    for rep in worker_reports:
        if rep.get("tag") == "worker.done" and rep.get("block"):
            local_reports[rep["block"]] = rep.get("slots") or {}

    return Snapshot(manifest=manifest, gates=gates, trunk_tip=trunk_tip,
                    worker_reports=worker_reports, local_reports=local_reports,
                    inbox_sidecar=sidecar)


def release(snap):
    """Drop the drained inbox sidecar — ONLY ever called by `core.tick.tick`
    AFTER `core.state.save` has succeeded (at-least-once: a crash before
    this leaves the sidecar for the next tick to re-drain, same discipline
    as `engine/fsm.py::_release_claimed`)."""
    sidecar = snap.inbox_sidecar
    if not sidecar:
        return
    try:
        os.remove(sidecar)
    except OSError:
        pass
