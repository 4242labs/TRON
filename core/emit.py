"""core.emit — the SINGLE emit API + the one closed effect registry
(block 01-38 T7, ADR-0012 events-as-single-ground-truth spine).

THE INVARIANT THIS MODULE EXISTS TO MAKE UNREPRESENTABLE
--------------------------------------------------------
Every persisted state change in `core/` — every mutation of the durable
manifest (`core.state`'s payload) — routes through THIS module, and every
such change simultaneously writes ONE typed event naming the effect. The
two are inseparable by construction: you cannot apply a state change here
without the event, and you cannot (legally) apply one anywhere else at all.

Historically the manifest was a plain dict mutated raw (`manifest["cases"]
[cid]["decision"] = verb`, `gate_state["stage"] = ...`) all over `core/`,
and the forensic event stream was a SEPARATE, best-effort thing only five
call sites in the whole stack ever wrote to. The two could — and did —
drift: a state transition with no event, an event with no state behind it.
Under the operator's events-as-single-ground-truth rule (`events.jsonl` is
the sole truth source; the human flow-log is advisory) that drift is a
defect: acceptance and every proof read the event stream, so an un-emitted
transition is invisible to them (emission completeness — an un-emitted
effect is a must-be-zero-class defect).

T7 closes it by making the manifest mutation and its event ONE operation:

  - Call sites never write manifest-rooted state directly any more. They
    call `emit.put` / `emit.patch` / `emit.append` / `emit.drop` (state
    changes) or `emit.record` (a pure forensic event, no state) — each
    takes an `effect` naming a member of the closed `EFFECTS` registry, and
    each WRITES THE TYPED EVENT as part of applying the change.
  - The mutation is thus expressed as a FUNCTION CALL carrying an effect
    name, never a bare `manifest[...] = ...` subscript-store. A bypassing
    raw write is not the natural thing to type — and the completeness lint
    (block 01-38 T7's final sub-commit: a manifest-taint check over ALL of
    `core/`, whitelisting only THIS module) makes any that slip a hard
    failure. This module is the SOLE place a manifest-rooted subscript-store
    legally appears in `core/`.
  - `EFFECTS` is the ONE registry of the effect vocabulary. `emit` refuses
    an effect not in it (`UnknownEffectError`, raised — a typo fails loud at
    the call, never a silently-mis-typed event that drifts the vocabulary).

WHY A GENERIC MUTATOR, NOT ONE HAND-WRITTEN APPLIER PER EFFECT
-------------------------------------------------------------
The DECISION of what to change, and to what, stays in the domain modules
(`core/gate.py`, `core/casestate.py`, `core/architect.py`, ...) where it
belongs — this module never becomes a god-object re-implementing their
logic. It owns only the two things that must be central: (1) the single
point every manifest mutation physically happens, and (2) the paired typed
event. The verbs (`put`/`patch`/`append`/`drop`) are a small, generic,
mechanism-complete vocabulary of "what can physically change in a dict/list
manifest"; the `effect` argument carries the SEMANTICS (which is what the
event stream records and acceptance reads).

SINK-AGNOSTIC: the typed event is written to `eng.events` (the duck-typed
`.event(type, **payload)` sink `core.engine.Engine` supplies — an in-memory
`_Events` by default, a durable `engine/eventlog.py::EventLog` when a real
run passes one). Both share the `.event(type, **payload)` shape, so this
module never cares which it is. `record_to` takes a raw sink directly for
the ONE pre-engine caller that has an events sink but no `eng` yet
(`core/vocab.py::check_handshake`).

Duck-typed `eng` contract used here: `eng.events` (the `.event(...)` sink).
Nothing else — no git, no subprocess, no LLM, no file IO in this module.
"""

# ─────────────────────────── the one registry ───────────────────────────
#
# Each effect is one entry. `kind` is "state" (accompanies a manifest
# mutation) or "forensic" (a pure event, no state change). `counter_class`
# (R4, wired fully in T9) partitions the counter effects: "must_be_zero" (a
# primary path silently failing — acceptance reads these at zero) or
# "may_fire" (a designed rare backstop). A non-counter effect leaves it
# None. This registry GROWS one domain module's effects per T7 sub-commit;
# it is the single source of the effect vocabulary the completeness test
# (final sub-commit) reads.


class _Effect:
    __slots__ = ("name", "kind", "counter_class")

    def __init__(self, name, kind, counter_class=None):
        self.name = name
        self.kind = kind
        self.counter_class = counter_class


def _reg(name, kind, counter_class=None):
    return name, _Effect(name, kind, counter_class)


EFFECTS = dict([
    # ── forensic events (no manifest mutation of their own) ──
    # A patch-id-bound merge/close grant was minted (`core/landing.py`).
    _reg("grant_minted", "forensic"),
    # The admission door refused a report — full text + origin recorded
    # durably (`core/door.py`, R2 "a door refusal is recorded engine-side").
    _reg("door_refusal", "forensic"),
    # An operator page was attempted over the real transport, with its
    # delivered/failed receipt (`core/engine.py::_page_operator`, R8).
    _reg("operator_page", "forensic"),
    # A must-be-zero counter fired: a primary path silently failed where it
    # never should (`core/casestate.py` permanent page-fail, `core/vocab.py`
    # version-handshake fail). Acceptance reads the must-be-zero set at zero
    # (R4). The specific counter is named in the event's `counter` field.
    _reg("must_be_zero", "forensic", counter_class="must_be_zero"),
])


class UnknownEffectError(KeyError):
    """A caller named an effect not in the closed `EFFECTS` registry — a
    typo or an un-registered new effect. Raised at the call (never a
    silently-mis-typed event that drifts the vocabulary); the fix is to
    register the effect in `EFFECTS` above, deliberately, or correct the
    name."""


def _spec(effect):
    try:
        return EFFECTS[effect]
    except KeyError:
        raise UnknownEffectError(
            f"emit: {effect!r} is not a registered effect. Every effect must be "
            f"declared in core.emit.EFFECTS (the one closed effect vocabulary). "
            f"Legal effects: {sorted(EFFECTS)}") from None


def _write(sink, effect, fields):
    """The ONE event-write. `sink` is a `.event(type, **payload)` sink
    (`_Events` or `EventLog`). The typed event's `type` IS the effect name —
    the registry is the closed vocabulary of those types."""
    sink.event(effect, **fields)


# ─────────────────────────── navigation ───────────────────────────
def _nav(manifest, path, create):
    """Resolve `path` (a tuple of keys) to the container it names inside
    `manifest`. With `create=True`, every missing intermediate dict is
    `setdefault`-seeded (the SAME "seed the section you need" discipline
    every `core/` module already uses on the manifest) so a first write to a
    fresh section lands. `path=()` is the manifest root itself. This is the
    ONLY manifest navigation in the mutating verbs below — a single, audited
    place, never scattered."""
    node = manifest
    for key in path:
        if create:
            node = node.setdefault(key, {})
        else:
            node = node[key]
    return node


# ─────────────────────────── the emit API ───────────────────────────
def record(eng, effect, **fields):
    """A pure forensic event — NO manifest mutation. Writes the typed
    `effect` event to `eng.events`. `effect` must be a `kind == "forensic"`
    registry member (a state-kind effect used with no mutation is a caller
    error — use the mutating verbs). The single replacement for the raw
    `eng.events.event(<type>, ...)` calls the pre-T7 stack scattered."""
    spec = _spec(effect)
    if spec.kind != "forensic":
        raise UnknownEffectError(
            f"emit.record: {effect!r} is a {spec.kind!r}-kind effect — a state "
            f"change, not a pure forensic event; use emit.put/patch/append/drop.")
    _write(eng.events, effect, fields)


def record_to(sink, effect, **fields):
    """`record`, but for the ONE pre-engine caller that holds a raw events
    sink and no `eng` yet (`core/vocab.py::check_handshake`, which runs at
    the version handshake before any `Engine` is assembled). Same closed-
    registry check, same typed write."""
    spec = _spec(effect)
    if spec.kind != "forensic":
        raise UnknownEffectError(
            f"emit.record_to: {effect!r} is a {spec.kind!r}-kind effect, not a "
            f"pure forensic event.")
    _write(sink, effect, fields)


def put(eng, manifest, effect, path, key, value, **fields):
    """Set `manifest<path>[key] = value` (creating missing intermediate
    dicts) AND write the typed `effect` event. Returns `value`. The event's
    payload is `fields` (the caller names what the stream records); the
    verb + path + key/value are the physical change. Use for a single keyed
    assignment (`manifest["cases"][cid] = case`)."""
    _spec(effect)
    _nav(manifest, path, create=True)[key] = value
    _write(eng.events, effect, fields)
    return value


def patch(eng, manifest, effect, path, updates, **fields):
    """Apply every `updates` key onto the dict at `manifest<path>` (creating
    it if missing) AND write the typed `effect` event — the natural shape
    for a state TRANSITION that sets several related fields at once (a gate
    moving stage while clearing the next stage's fields). Returns the
    patched dict."""
    _spec(effect)
    target = _nav(manifest, path, create=True)
    target.update(updates)
    _write(eng.events, effect, fields)
    return target


def append(eng, manifest, effect, path, value, **fields):
    """Append `value` to the list at `manifest<path>` (created empty if
    missing) AND write the typed `effect` event. `path` names the list
    itself (e.g. `("escalations",)`). Returns `value`."""
    _spec(effect)
    parent = _nav(manifest, path[:-1], create=True)
    parent.setdefault(path[-1], []).append(value)
    _write(eng.events, effect, fields)
    return value


def drop(eng, manifest, effect, path, key, **fields):
    """Remove `key` from the dict at `manifest<path>` (a `pop`, absent-safe)
    AND write the typed `effect` event — a state change is still a state
    change when it REMOVES (a case cleared, a worker slot freed). Returns the
    popped value (or None). `path` must already exist (a drop from a missing
    section is a no-op that still records the intended effect)."""
    _spec(effect)
    try:
        target = _nav(manifest, path, create=False)
    except (KeyError, TypeError):
        target = None
    popped = target.pop(key, None) if isinstance(target, dict) else None
    _write(eng.events, effect, fields)
    return popped
