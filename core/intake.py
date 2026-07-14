"""core.intake — the private per-agent intake (block 01-38 T1, ADR-0012
root invariant / R6). Replaces the single shared `ctx.worker_inbox` drop-
box every agent used to write into: each agent gets its OWN file,
`<instance>/intake/<agent_id>.jsonl`, minted the moment the agent is
spawned (`core/switchboard.py::fill`, `core/reviewers.py::dispatch`,
`core/engine.py::Engine.start`'s architect boot) — never lazily
materialized on first write, so a spawned-but-silent agent's intake still
drains cleanly as empty, never as "no such file". The shared drop-box
itself is DELETED from this stack's live path (`core/snapshot.py` no
longer reads `ctx.worker_inbox` at all) — removed, not sanitized.

`scripts/report.sh` is handed its own intake via a NEW `--intake <path>`
flag — never a `--worker-id`-style claim it could point anywhere else.
The real invocation a worker is ever taught (`prompts/PMT-SPAWN.md`'s
`bash {report} {worker_id} "online"`) never changes: `core/engine.py::
Engine.emit` computes `{report}`'s VALUE per call, baking THIS worker's
own `--intake <path>` into the command line handed to it — the worker
never types, chooses, or even sees an alternative intake to name (the
`{worker_id}` token that follows is now cosmetic only — unchanged canon,
zero prompt/messages.yaml edits needed).

`core/snapshot.py::build` drains EVERY known intake each tick (never a
single shared file) and pairs each drained report with a fresh `Origin`
(below) computed from WHICH intake it was drained from — the concrete,
channel-derived agent id, independent of anything the message body
claims. `Origin` is a distinct typed value (a `namedtuple`, never a bare
string). `core/vocab.py::resolve_origin`'s payload-trusting fallback is
UNTOUCHED here (its deletion is block 01-38 T2) — this module adds a
SECOND, stronger signal alongside it: the one T2/T3 migrate every reader
onto, threaded out-of-band (never a vocab-slot-settable field — no
`--origin` flag exists anywhere, and this module is the sole writer of
the pairing) through `core/tick.py`'s route -> act pass.

Same at-least-once discipline `core/snapshot.py::_drain_inbox` used to
give the single shared inbox (learned by reading, re-expressed per-file
here — never copied): rotate a live intake to a `.proc` sidecar; a
`.proc` already on disk (a crashed prior tick's undrained residue) is
re-read instead of re-rotated, so a report a crashed tick already
consumed is never silently dropped. Sidecars are released by the caller
(`core/snapshot.py::release`) only AFTER `core.state.save` succeeds —
unchanged discipline, just plural now (one sidecar per intake drained
this tick).
"""
import collections
import glob
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import vocab       # noqa: E402 — core/vocab.py, WORKER/ARCHITECT kind constants
import architect    # noqa: E402 — core/architect.py, ARCHITECT_WID

INTAKE_DIRNAME = "intake"

# Origin — the distinct typed value the door produces (the root invariant,
# T1): `kind` is one of `core/vocab.py`'s WORKER/ARCHITECT/OPERATOR
# constants, `id` is the CONCRETE channel-derived agent id (the intake's
# own filename) — never a coarse class alone: downstream needs the
# specific id (liveness touch, per-worker block attribution, reviewer
# id). The real operator TRANSPORT (T5's scope) is not built yet; today's
# `operator.decision` settle still lands as a structured line through
# this SAME per-channel mechanism, filed under the one well-known
# `vocab.OPERATOR` pseudo-agent-id (see `drain_all`, below) — never the
# deleted shared drop-box.
Origin = collections.namedtuple("Origin", ["kind", "id"])


def intake_dir(ctx):
    return ctx.p(INTAKE_DIRNAME)


def intake_path(ctx, agent_id):
    """The ONE deterministic path for `agent_id`'s own private intake —
    the same path `create` mints at spawn, `report.sh --intake` is handed,
    and `drain_all` reads back. Never a second derivation of this shape
    anywhere else."""
    return os.path.join(intake_dir(ctx), f"{agent_id}.jsonl")


def create(ctx, agent_id):
    """Mint `agent_id`'s private intake — idempotent (a re-tick replaying
    spawn, or a deterministic re-spawn of the SAME id, never truncates an
    already-written intake). Called at spawn, before any process/order —
    the intake exists the instant the agent does, so a spawned-but-silent
    agent still drains cleanly as empty, never as a missing file."""
    os.makedirs(intake_dir(ctx), exist_ok=True)
    path = intake_path(ctx, agent_id)
    if not os.path.exists(path):
        with open(path, "a"):
            pass
    return path


def known_agent_ids(ctx):
    """Every agent id with a minted intake on disk right now — the
    drain's own enumeration (never a second, driftable roster of its
    own). An agent with no intake yet was never spawned and has nothing
    to drain."""
    d = intake_dir(ctx)
    if not os.path.isdir(d):
        return []
    ids = []
    for path in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
        base = os.path.basename(path)
        if base.endswith(".jsonl"):
            ids.append(base[: -len(".jsonl")])
    return ids


def write(ctx, agent_id, obj):
    """Append one line directly to `agent_id`'s own intake — the RIG-side
    stand-in for a real `scripts/report.sh --intake <path>` subprocess
    write (a scripted fixture playing a worker; see each rig's own
    docstring — R3 MODEL A's honest-rig rebuild is block 01-38 T6, not
    this task). Creates the intake first (idempotent) so a rig that
    injects before any `create()` call of its own still lands correctly."""
    path = create(ctx, agent_id)
    with open(path, "a") as fh:
        fh.write(json.dumps(obj) + "\n")


def _drain_one(path, log):
    """Rotate ONE intake file to a `.proc` sidecar (or re-read a `.proc` a
    crashed prior tick already rotated — at-least-once; mirrors the
    single shared-inbox drain this module replaces, generalized to one
    call per file). Returns `(raw_lines, sidecar_path_or_None)` — un-
    parsed strings; the caller parses (one poison line must never sink
    the whole drain)."""
    proc = path + ".proc"
    if not os.path.exists(proc):
        if not os.path.exists(path):
            return [], None
        try:
            os.rename(path, proc)
        except OSError as e:
            log("flow", f"intake: rotate failed for {path!r} ({e}); "
                        f"draining nothing from it this tick")
            return [], None
    with open(proc, "r") as fh:
        return fh.readlines(), proc


def drain_all(ctx, log):
    """Drain EVERY known agent's intake this tick — replaces the single
    shared `ctx.worker_inbox` read entirely (block 01-38 T1: "delete the
    legacy single shared drop-box from the core/ path"). Returns
    `(paired, sidecars)`: `paired` is a list of `(Origin, dict)` — each
    drained JSON object PAIRED with the `Origin` the door resolved for it
    purely from WHICH intake it was drained from (never from anything the
    line itself claims — the root invariant's own words, T1's own proof:
    `test:<origin_from_channel_only>`); `sidecars` is every `.proc` path
    this pass rotated, for the caller to release only after a successful
    persist (unchanged at-least-once discipline, now plural — one per
    intake actually drained this tick).

    A malformed/structurally-invalid line is logged and skipped — one
    poison line in one agent's intake must never sink the whole tick's
    drain, exactly like the single-inbox drain it replaces."""
    paired = []
    sidecars = []
    for agent_id in known_agent_ids(ctx):
        if agent_id == architect.ARCHITECT_WID:
            kind = vocab.ARCHITECT
        elif agent_id == vocab.OPERATOR or agent_id.startswith(vocab.OPERATOR + "-"):
            # The not-yet-built real operator channel (T5's scope) still
            # has no dedicated transport in this stack — an
            # `operator.decision` settle is, today, injected as a
            # structured line the SAME way any other report is (see
            # `core/door.py::admit`'s own documented "no impersonation
            # surface to close for a verb-less tag" note: minters is not
            # enforced for it). Every simulated operator actor's pseudo-
            # agent-id is `vocab.OPERATOR` itself or `vocab.OPERATOR +
            # "-<detail>"` (e.g. `core/sim/operator_proxy.py`'s own
            # `"operator-proxy"`) — never confused with a real worker/
            # architect id (neither is ever `"operator"`-prefixed).
            kind = vocab.OPERATOR
        else:
            kind = vocab.WORKER
        origin = Origin(kind, agent_id)
        lines, sidecar = _drain_one(intake_path(ctx, agent_id), log)
        if sidecar:
            sidecars.append(sidecar)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                log("flow", f"intake: dropped a malformed line from "
                            f"{agent_id!r}'s intake: {e}")
                continue
            if not isinstance(rec, dict) or ("tag" not in rec and "text" not in rec):
                log("flow", f"intake: dropped a structurally invalid line "
                            f"from {agent_id!r}'s intake: {line!r}")
                continue
            paired.append((origin, rec))
    return paired, sidecars
