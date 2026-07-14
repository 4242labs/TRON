"""r3_lint — R3 honesty lint (ADR-0012 §2 R3 / block 01-40 T1).

The only legal ingress into the engine, in tests too, is the real reporting
door: `scripts/report.sh` writes a JSON line to `ctx.worker_inbox`, hardcoding
`sender.kind: "worker"` — that is the ONLY sender kind the real door can ever
produce. A harness that writes a report claiming any OTHER sender kind into
that same file asserts an identity nothing real produced (R6: "identity is
ambient, not asserted") and proves a channel that does not exist (R8: "the
current harness injects into the worker channel and lies exactly the way the
old rigs lied"). There is also no real OPERATOR transport yet at all (R8) — a
rig that writes `ctx.operator_inbox` fabricates a channel wholesale. Likewise,
a harness that mutates persisted engine state (`manifest[...]`) directly,
instead of letting the real drain (tick -> classify -> router) apply the
effect, skips the door entirely.

DESIGN (block 01-40 T1, REBUILT a second time after a hostile review): the
FIRST rebuild inverted "deny by default" correctly for the PAYLOAD (a
sender's kind must be a statically-provable dict literal, or it is denied),
but still recognized the WRITE MECHANISM ITSELF (what counts as "a write to
the inbox" at all) via a small ENUMERATED set of shapes: `open()`/`.write()`,
`json.dump()`, `append_jsonl()`, a shelled `>>` redirect. A second hostile
review proved 9/10 plain rewrites of the exact same violation defeat
mechanism-enumeration: `print(obj, file=handle)` (a real idiom already used
elsewhere in this very tree — `core/sim/launch.py`, `core/sim/live.py`),
`pathlib.Path(...).open()`, `.write_text()`/`.write_bytes()`, `io.open`,
`getattr()`-obscured attribute access, a target-path helper indirection
(mirroring the ALREADY-CLOSED payload-helper-indirection case, but on the
TARGET side, which had no equivalent tracing), a manifest handle wrapped in a
throwaway `dict`/`list` container, and an `os.replace()` tmp-file swap onto
the real inbox path.

THIS rebuild inverts the MECHANISM the same way the first rebuild inverted the
payload: DENY BY DEFAULT, allow a small, explicit, statically-provable legal
surface — never enumerate illegal shapes and chase the next rewrite.
Concretely, one whole-file, bounded-depth alias/call-graph trace
(`_resolve_channel` / `_resolve_manifest`, sharing the same substrate:
`_nearest_assign_value`, `_resolve_param_inbound`, `_resolve_call_return`)
answers ONE question for any expression: does it denote (directly, via an
aliased Name, via a `dict`/`list` container wrapping it, via a bounded
same-file call-site trace of an inbound function parameter, or via a bounded
trace of a same-file function's `return` value) the real `ctx.worker_inbox`,
`ctx.operator_inbox`, or `manifest`?

Given that resolver, the DETECTION step is structural, not shape-based:

  1. `_check_channel_writes` walks EVERY call in the file. A call is
     considered "write-capable, in scope" the instant its RECEIVER, or ANY
     positional/keyword argument, resolves to a traced channel — this is
     what covers `print(..., file=ib)`, `.write_text()`/`.write_bytes()`,
     `io.open`, and the next unknown stdlib idiom "by construction": no
     method-name enumeration decides whether a call is in scope, only
     whether one of its arguments IS the channel. Two small, EXPLICIT
     allow-lists (never enumerated illegal shapes — the DENY-by-default
     inversion's whole point) keep this from flagging ordinary reads: a call
     is a reference-producer (`open`/`io.open`/`pathlib.Path`/`getattr` —
     these build a path/handle reference, they do not themselves write) or a
     provably-read-only method/`os.path` introspection call
     (`exists`/`read_text`/`.stat()`/...). A call whose target is a
     FUNCTION DEFINED IN THIS SAME FILE is never itself flagged (forwarding
     a path to a helper is not a write) — the helper's OWN body is walked
     independently, and the SAME resolver traces the parameter back to
     every real call site, so the actual write, wherever it structurally
     lives, is still caught. Where none of the above applies and the call
     still touches a traced channel, the operation is DENIED outright
     unless its payload is a statically-provable safe dict literal — an
     unresolvable touch is treated as illegal, never a silent pass-through.
  2. Within scope, `ctx.operator_inbox` is ALWAYS illegal
     (`OPERATOR_INBOX_WRITE`) — there is no real operator transport a rig or
     driver may legitimately use yet (R8), so no payload shape makes this
     legal.
  3. Within scope, `ctx.worker_inbox` is legal ONLY if the write's JSON
     payload is a statically-resolvable dict literal that either carries NO
     `sender` key at all (ambient — the shape `scripts/report.sh`'s own
     free-text/structured lines and `core.sim.live`'s courier fallback both
     use) or carries `sender.kind` as the string literal `"worker"`. ANY
     other outcome is DENIED (`INBOX_FABRICATED_SENDER`).
  4. `manifest[...]` direct-write is unchanged in kind (any subscript
     assignment/`AugAssign`/`.update()` at ANY depth >= 1) but now shares
     the SAME resolver as the channel side, so a manifest reference wrapped
     in a throwaway `dict`/`list` container (`bag = {"m": eng.manifest};
     bag["m"][...] = ...`) or obtained via a same-file helper's `return` is
     traced exactly like an aliased Name is — no separate, narrower
     mechanism for the manifest side.

Two illegal-ingress classes remain the visible violation vocabulary
(`INBOX_FABRICATED_SENDER` + `OPERATOR_INBOX_WRITE` for the reporting door;
`MANIFEST_DIRECT_WRITE` for direct state mutation) — only the DETECTION
underneath them was rebuilt, twice now.

NOT flagged: calling an internal function directly with a constructed
argument (e.g. `classify.classify(eng, {...}, manifest)` to unit-test
`classify` itself, or seeding a scenario's initial `manifest = {...}`
whole-dict fixture, or reading `manifest[...]`/`ctx.worker_inbox` anywhere —
a provably read-only method/function call, or a call whose only touch is a
value NOT further used to write, is not in scope). Only a WRITE-capable
operation whose target resolves to ingress state is in scope — ordinary
whitebox unit tests and fixture setup never claim to drive the real inbox ->
drain path, so they cannot lie about one.

REAL, HONESTLY-DISCLOSED REMAINING LIMITS (not closed by this rebuild — this
list names EXACTLY what is still open, not an aspirational "mostly done"):

  - The alias/call-graph trace (`_nearest_assign_value`,
    `_resolve_param_inbound`, `_resolve_call_return`) is a flat, whole-file,
    NAME-based walk with a bounded hop count (`_MAX_TRACE_DEPTH`) — not real
    scope-aware/interprocedural dataflow. Two functions in the same file
    that happen to share a name are treated as the same call target
    (matches call sites by bare name / bare attribute name only, never by
    class or module qualification); a chain of aliasing/forwarding deeper
    than the bound is treated as unresolved (and therefore denied if it
    touches a channel op, but silently unresolved — i.e. invisible — if it
    does not reach a channel-shaped operation at all within the bound).
  - `_resolve_channel`/`_resolve_manifest` do NOT descend into arbitrary
    compound expressions looking for a buried taint — an f-string
    (`JoinedStr`) or a `BinOp` (e.g. `path + ".suffix"`) is not traced
    through. This is deliberate (an f-string log message quoting
    `ctx.worker_inbox` for a human to read is not a write, and flagging it
    would defeat real diagnostic logging), but it also means a derived path
    built via string concatenation or an f-string (`open(f"{inbox}.tmp")`)
    is invisible to this lint even where it legitimately should be traced
    further (e.g. a tmp-file swap where the SWAP call itself, not the tmp
    write, is what gets caught — proven by the adversarial fixture, but the
    general case of an arbitrarily-derived path is not covered).
  - The recognized ingress-state markers are exactly `worker_inbox`,
    `operator_inbox`, and `manifest` — the concrete real doors/state this
    ADR names. Other `ctx` fields the engine also owns and appends to
    (`event_log`, `home_log`, `message_log`, ...) are NOT covered.
  - The two allow-lists (`_SAFE_READ_METHODS`, `_SAFE_READ_OSPATH_FUNCS`)
    that keep ordinary reads/introspection from being flagged are
    necessarily enumerated too — but they enumerate PROVABLY SAFE, side-
    effect-free operations (existence/stat/read checks), which is the
    designed-for kind of small allow-list ("deny by default, allow a small
    explicit legal surface"), not a deny-list of known offenders chasing
    the next rewrite. A genuinely new READ-only idiom not on this list would
    be denied (a false positive, fixed by widening the allow-list) rather
    than silently passed — the fail-closed direction the whole rebuild
    exists to guarantee.
  - The subprocess/shell-redirect check (`_check_subprocess_redirect`) is
    still a textual/AST pattern match for a `>`/`>>` operator plus an
    ingress-marker reference inside a `subprocess.*`/`os.system`/`os.popen`
    call — it is not a shell parser (e.g. a redirect hidden behind further
    indirection, like a `.sh` script file the rig writes and then executes,
    is out of scope). This is a fundamentally different mechanism (shell
    text, not a Python call graph) from the structural rebuild above and is
    unchanged by it.
  - When a rig's `manifest` alias/call-site trace resolves a case with a
    MIX of distinct call sites (e.g. a helper whose parameter receives
    `ctx.worker_inbox` at one call site and something unrelated at
    another), channel-KIND resolution (`_resolve_param_inbound`) returns
    the FIRST match found, not the union of every call site's kind — an
    all-real-call-sites-agree assumption, true of every current harness
    (re-verified against the whole `core/` proof surface + all 20
    adversarial fixtures below when this rebuild landed) but not a
    completeness guarantee if a future helper is ever called with BOTH a
    worker- and an operator-inbox target.
  - This is a static AST lint, not a dynamic/runtime enforcement layer — a
    sufficiently obfuscated adversarial rewrite (e.g. `exec`/`eval`-based
    indirection, or reflection through a data structure this trace does not
    unwrap) can still defeat static analysis in principle. The design goal
    is to catch the ILLEGAL CLASS as it is actually written by a developer
    trying to pass CI, not to be a covert-channel-proof sandbox.
  - `core/scaffold_src.py` vendors a COPY of tron-meta's real
    `trivial-tip-converter` fixture project (see that module's own
    docstring) — this lint has no way to notice if the vendored copy
    silently drifts from tron-meta's original over time; that is a
    fixture-freshness risk, not something a static write-mechanism lint can
    detect.
"""
import ast
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The explicit, visible known-red list (T1 spec: "an EXPLICIT, visible
# known-red manifest that lists each offender with its owning block"). This
# is never a silent whitelist — `run()` re-verifies every entry every call:
# a listed file that comes back CLEAN is a stale entry (FAIL, remove it or
# it regressed silently); a red file NOT listed here is an unlisted offender
# (FAIL, add it with its owning block or fix it).
KNOWN_RED = {
    "core/sim/operator_proxy.py": {
        "owning_block": "01-38",
        "reason": ('_inject_decision fabricates sender.kind="operator" and appends '
                   "it straight to eng.ctx.worker_inbox (the WORKER channel) — "
                   "report.sh, the one real door, can only ever emit "
                   'sender.kind="worker"; there is no real operator transport yet '
                   "(that is R8/R6, later blocks). ADR-0012 §2 R8 names this exact "
                   'harness: "the current harness injects into the worker channel '
                   'and lies exactly the way the old rigs lied." Rebuilt honestly '
                   "in 01-38 T4 once the real operator channel exists."),
    },
}


class Violation:
    def __init__(self, path, lineno, rule, detail):
        self.path = path
        self.lineno = lineno
        self.rule = rule
        self.detail = detail

    def __str__(self):
        return f"{self.path}:{self.lineno}: [{self.rule}] {self.detail}"


def harness_files():
    """`core/*_rig.py` + every module under `core/sim/` (the whole proof-
    harness surface: the L1 mutation-proof rigs, plus the SIM apparatus they
    and the live runner share) — glob-discovered, never hand-maintained."""
    files = sorted(glob.glob(os.path.join(ROOT, "core", "*_rig.py")))
    files += sorted(
        p for p in glob.glob(os.path.join(ROOT, "core", "sim", "*.py"))
        if os.path.basename(p) != "__init__.py"
    )
    return files


# ───────────────────── shared alias / call-graph trace ─────────────────────
# EVERY resolver below shares this one substrate: a flat, whole-file,
# line-ordered "nearest prior binding" walk (`_nearest_assign_value`), plus
# two bounded call-graph hops — INBOUND (a function parameter, traced back
# to what its real call sites actually pass: `_resolve_param_inbound`) and
# OUTBOUND (a call's result, traced forward into the callee's own `return`
# statements: `_resolve_call_return`). This is deliberately NOT real
# scope-aware/interprocedural dataflow (see module docstring's honestly-
# disclosed limits) — it is exactly powerful enough to defeat renaming,
# container-wrapping, and one level of same-file helper indirection in
# either direction, which is what the adversarial review actually produced.

_MAX_TRACE_DEPTH = 5


def _collect_all_bindings(tree):
    """Flat `(lineno, name, value_expr)` list — EVERY simple `name = <expr>`
    assignment AND `with <expr> as name:` binding, sorted by line. The
    single shared substrate every trace in this module walks."""
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.optional_vars, ast.Name):
                    out.append((node.lineno, item.optional_vars.id, item.context_expr))
    out.sort(key=lambda t: t[0])
    return out


def _nearest_assign_value(bindings, name, before_lineno):
    best = None
    for lineno, nm, val in bindings:
        if nm == name and lineno <= before_lineno:
            best = val
    return best


def _build_parent_function_map(tree):
    """AST node -> its nearest enclosing `FunctionDef`/`AsyncFunctionDef`
    (or `None` at module level)."""
    parent_func = {}

    def visit(node, current_func):
        parent_func[node] = current_func
        nxt = node if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else current_func
        for child in ast.iter_child_nodes(node):
            visit(child, nxt)

    visit(tree, None)
    return parent_func


def _collect_funcs_by_name(tree):
    """`name -> [FunctionDef, ...]` for every function/method DEFINED in
    this file (module-level defs AND methods, matched by bare name only —
    the same whole-file simplification documented throughout)."""
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.setdefault(node.name, []).append(node)
    return out


class _Ctx:
    __slots__ = ("tree", "parent_func", "assigns", "funcs")

    def __init__(self, tree):
        self.tree = tree
        self.parent_func = _build_parent_function_map(tree)
        self.assigns = _collect_all_bindings(tree)
        self.funcs = _collect_funcs_by_name(tree)


def _call_matches_name(call, name):
    return ((isinstance(call.func, ast.Name) and call.func.id == name)
             or (isinstance(call.func, ast.Attribute) and call.func.attr == name))


def _param_index(funcdef, name):
    for i, a in enumerate(funcdef.args.args):
        if a.arg == name:
            return i
    return None


def _call_arg_for_param(call, funcdef, idx, name):
    """The actual argument `call` sends for parameter index `idx` (named
    `name`) of `funcdef` — positional or keyword. A METHOD call site
    (`x.method(...)`) never passes `self`/`cls` explicitly, so the
    positional index is shifted by one relative to `funcdef.args.args`
    (which DOES include `self`/`cls`) whenever the call is an attribute
    call on a function whose first parameter is conventionally bound —
    closes the off-by-one that would otherwise make every bound-method
    call site (`rs.react(i, manifest, ctx.worker_inbox)`) unresolvable."""
    is_attr_call = isinstance(call.func, ast.Attribute)
    has_self = bool(funcdef.args.args) and funcdef.args.args[0].arg in ("self", "cls")
    eff_idx = idx - 1 if (is_attr_call and has_self and idx > 0) else idx
    if 0 <= eff_idx < len(call.args):
        return call.args[eff_idx]
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _resolve_param_inbound(name_node, before_lineno, ctx, resolver, depth):
    """`name_node` is an unbound Name (no local binding found) — is it a
    parameter of its enclosing function? If so, trace EVERY same-file call
    site of that function (by bare name) and resolve what was ACTUALLY
    passed there, via `resolver` (bounded depth). Returns the first truthy
    result found. This is the INBOUND half of the shared call-graph trace —
    closes "helper takes the channel/manifest as a parameter, forwards it
    to the real operation under an innocuous name"."""
    if depth >= _MAX_TRACE_DEPTH:
        return None
    enclosing = ctx.parent_func.get(name_node)
    if enclosing is None:
        return None
    idx = _param_index(enclosing, name_node.id)
    if idx is None:
        return None
    sites = [n for n in ast.walk(ctx.tree)
             if isinstance(n, ast.Call) and _call_matches_name(n, enclosing.name)]
    for call in sites:
        arg = _call_arg_for_param(call, enclosing, idx, name_node.id)
        if arg is None:
            continue
        result = resolver(arg, call.lineno, ctx, depth + 1)
        if result:
            return result
    return None


def _direct_returns(fn):
    """Every `Return` node directly inside `fn`'s own body — never
    descending into a nested `def`/`lambda` (those are a different
    function's returns)."""
    out = []

    def walk(node, top):
        if node is not top and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return
        if isinstance(node, ast.Return):
            out.append(node)
            return
        for child in ast.iter_child_nodes(node):
            walk(child, top)

    walk(fn, fn)
    return out


def _resolve_call_return(call, before_lineno, ctx, resolver, depth):
    """`call` invokes a same-file function (by bare name/attr) — resolve
    every `return <expr>` in ITS body via `resolver` (bounded depth), and
    return the first truthy result. This is the OUTBOUND half of the shared
    call-graph trace — closes "helper RETURNS the channel/manifest,
    assigned to an innocuously-named local" (`dest = _channel(eng)`)."""
    if depth >= _MAX_TRACE_DEPTH:
        return None
    if isinstance(call.func, ast.Name):
        name = call.func.id
    elif isinstance(call.func, ast.Attribute):
        name = call.func.attr
    else:
        return None
    for fn in ctx.funcs.get(name, []):
        for ret in _direct_returns(fn):
            if ret.value is None:
                continue
            result = resolver(ret.value, ret.lineno, ctx, depth + 1)
            if result:
                return result
    return None


# ───────────────────────── channel (inbox) resolution ─────────────────────────

_INBOX_ATTRS = {"worker_inbox": "worker", "operator_inbox": "operator"}
_REFERENCE_CALL_NAMES = {"open", "getattr", "Path"}
_REFERENCE_CALL_ATTRS = {"open", "Path"}


def _resolve_str_literal(expr, before_lineno, ctx, depth=0):
    """Resolve `expr` to a literal string if statically provable (a
    Constant, or a traced Name alias to one) — powers the `getattr(ctx,
    <name>)` close (the attr name may itself be a module constant)."""
    if expr is None or depth > _MAX_TRACE_DEPTH:
        return None
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.Name):
        val = _nearest_assign_value(ctx.assigns, expr.id, before_lineno)
        if val is not None:
            return _resolve_str_literal(val, before_lineno, ctx, depth + 1)
    return None


def _open_call_path_mode(call):
    """`open(<path>, <mode>)` / `io.open(<path>, <mode>)` — the 2-ARGUMENT
    convention: path/mode resolved from EITHER positional args OR
    `file=`/`mode=` kwargs."""
    path_arg = call.args[0] if len(call.args) >= 1 else None
    mode_arg = call.args[1] if len(call.args) >= 2 else None
    for kw in call.keywords:
        if kw.arg == "file" and path_arg is None:
            path_arg = kw.value
        if kw.arg == "mode" and mode_arg is None:
            mode_arg = kw.value
    if mode_arg is None:
        mode = "r"          # open()'s own default
    elif isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str):
        mode = mode_arg.value
    else:
        mode = "<non-literal>"
    return path_arg, mode


def _method_open_mode(call):
    """`<receiver>.open(<mode>)` — the 1-ARGUMENT convention (no separate
    path argument at all; the receiver itself IS the path/handle)."""
    mode_arg = call.args[0] if call.args else next(
        (kw.value for kw in call.keywords if kw.arg == "mode"), None)
    if mode_arg is None:
        return "r"
    if isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str):
        return mode_arg.value
    return "<non-literal>"


def _is_write_mode(mode):
    return isinstance(mode, str) and any(c in mode for c in "wax+")


def _is_open_call(node):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"


def _is_io_open_call(node):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "open" and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "io")


def _resolve_channel(expr, before_lineno, ctx, depth=0):
    """Does `expr` resolve — directly, via a traced alias, via a
    dict/list-wrapped container, via a bounded inbound-parameter trace, or
    via a bounded outbound-return trace — to `ctx.worker_inbox` /
    `ctx.operator_inbox` (as a path string, a `pathlib.Path` object, or an
    open file handle)? Returns `"worker"` / `"operator"` / `None`. This is
    the ONE place that knows what the two real channels look like; every
    other function in this module treats its answer as ground truth."""
    if expr is None or depth > _MAX_TRACE_DEPTH:
        return None
    if isinstance(expr, ast.Attribute) and expr.attr in _INBOX_ATTRS:
        return _INBOX_ATTRS[expr.attr]
    if isinstance(expr, ast.Call):
        func = expr.func
        # getattr(<obj>, "worker_inbox"/"operator_inbox"[, default]) — the
        # LITERAL attr name is the proof, whatever <obj> is.
        if isinstance(func, ast.Name) and func.id == "getattr" and len(expr.args) >= 2:
            lit = _resolve_str_literal(expr.args[1], before_lineno, ctx, depth)
            return _INBOX_ATTRS.get(lit)
        # bare open(path, mode?) / io.open(path, mode?) — 2-arg convention.
        if _is_open_call(expr) or _is_io_open_call(expr):
            path_arg, mode = _open_call_path_mode(expr)
            if _is_write_mode(mode):
                return _resolve_channel(path_arg, before_lineno, ctx, depth + 1)
            return None
        # pathlib.Path(X) / Path(X) — TRANSPARENT: a Path object over X is
        # the same channel as X (closes `.open()`/`.write_text()`/
        # `.write_bytes()` chained straight off a `Path(...)` constructor).
        if ((isinstance(func, ast.Attribute) and func.attr == "Path")
                or (isinstance(func, ast.Name) and func.id == "Path")):
            return _resolve_channel(expr.args[0], before_lineno, ctx, depth + 1) if expr.args else None
        # <receiver>.open(mode?) — 1-arg convention: the RECEIVER carries
        # the path (a Path object, or anything else this trace resolves).
        if isinstance(func, ast.Attribute) and func.attr == "open":
            recv_kind = _resolve_channel(func.value, before_lineno, ctx, depth + 1)
            if recv_kind and _is_write_mode(_method_open_mode(expr)):
                return recv_kind
            return None
        # anything else: bounded call-RETURN-value trace (closes "helper
        # returns the channel") — the OUTBOUND mirror of the inbound
        # parameter trace already used for a function's own arguments.
        return _resolve_call_return(expr, before_lineno, ctx, _resolve_channel, depth)
    if isinstance(expr, ast.Name):
        val = _nearest_assign_value(ctx.assigns, expr.id, before_lineno)
        if val is not None:
            return _resolve_channel(val, before_lineno, ctx, depth + 1)
        return _resolve_param_inbound(expr, before_lineno, ctx, _resolve_channel, depth)
    if isinstance(expr, (ast.Dict, ast.List)):
        vals = expr.values if isinstance(expr, ast.Dict) else expr.elts
        for v in vals:
            k = _resolve_channel(v, before_lineno, ctx, depth + 1)
            if k:
                return k
        return None
    return None


# ───────────────────── payload (sender-kind) resolution ─────────────────────

def _dict_literal_str_value(dict_node, key):
    """`{key: "literal"}` -> `"literal"`; `None` if absent, `"<non-literal>"`
    if present but not a string constant."""
    if not isinstance(dict_node, ast.Dict):
        return None
    for k, v in zip(dict_node.keys, dict_node.values):
        if isinstance(k, ast.Constant) and k.value == key:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                return v.value
            return "<non-literal>"
    return None


def _unwrap_json_dumps(arg):
    """`json.dumps(X) + "\\n"` or `json.dumps(X)` -> `X`; else `arg` as-is."""
    if arg is None:
        return None
    target = arg.left if isinstance(arg, ast.BinOp) else arg
    if (isinstance(target, ast.Call) and isinstance(target.func, ast.Attribute)
            and target.func.attr == "dumps" and target.args):
        return target.args[0]
    return target


def _resolve_payload_dicts(expr, before_lineno, ctx, depth=0):
    """Resolve a payload expression to `[(dict_node_or_None, effective_lineno), ...]`
    — normally one candidate. Closes the "helper-function indirection"
    evasion: a same-file helper whose payload argument is a bare pass-
    through parameter is judged by what EVERY one of its real call sites
    actually sends (bounded depth), never by its own signature alone."""
    if isinstance(expr, ast.Dict):
        return [(expr, before_lineno)]
    if isinstance(expr, ast.Name):
        val = _nearest_assign_value(ctx.assigns, expr.id, before_lineno)
        if val is not None:
            if isinstance(val, ast.Dict):
                return [(val, before_lineno)]
            if depth < _MAX_TRACE_DEPTH:
                return _resolve_payload_dicts(val, before_lineno, ctx, depth + 1)
            return [(None, before_lineno)]
        if depth < _MAX_TRACE_DEPTH:
            enclosing = ctx.parent_func.get(expr)
            if enclosing is not None:
                idx = _param_index(enclosing, expr.id)
                if idx is not None:
                    sites = [n for n in ast.walk(ctx.tree)
                             if isinstance(n, ast.Call) and _call_matches_name(n, enclosing.name)]
                    if sites:
                        out = []
                        for call in sites:
                            arg = _call_arg_for_param(call, enclosing, idx, expr.id)
                            if arg is None:
                                out.append((None, call.lineno))
                            else:
                                out.extend(_resolve_payload_dicts(arg, call.lineno, ctx, depth + 1))
                        return out
        return [(None, before_lineno)]
    return [(None, before_lineno)]


def _emit_channel_violation(kind, payload_expr, path, lineno, violations, mechanism, ctx):
    if kind == "operator":
        violations.append(Violation(
            path, lineno, "OPERATOR_INBOX_WRITE",
            f"writes to ctx.operator_inbox via {mechanism} — there is no real operator "
            "transport a rig or driver may use yet (ADR-0012 R8); this channel is illegal "
            "to write at all, regardless of payload"))
        return
    # kind == "worker"
    candidates = (_resolve_payload_dicts(payload_expr, lineno, ctx)
                  if payload_expr is not None else [(None, lineno)])
    for dict_node, at_lineno in candidates:
        if not isinstance(dict_node, ast.Dict):
            violations.append(Violation(
                path, at_lineno, "INBOX_FABRICATED_SENDER",
                f"writes to ctx.worker_inbox via {mechanism} with a payload that is not a "
                "statically-resolvable dict literal — cannot verify sender.kind, denied by "
                "default (see module docstring: this is the deliberate deny-unless-provable "
                "inversion, not a false positive on an unrelated write)"))
            continue
        sender = None
        for k, v in zip(dict_node.keys, dict_node.values):
            if isinstance(k, ast.Constant) and k.value == "sender":
                sender = v
                break
        if sender is None:
            continue  # no sender asserted — ambient/implicit, matches report.sh's own shape
        sender_dict = sender
        if isinstance(sender_dict, ast.Name):
            val = _nearest_assign_value(ctx.assigns, sender_dict.id, at_lineno)
            sender_dict = val if isinstance(val, ast.Dict) else sender_dict
        kind_val = (_dict_literal_str_value(sender_dict, "kind")
                    if isinstance(sender_dict, ast.Dict) else "<non-literal>")
        if kind_val == "worker":
            continue
        violations.append(Violation(
            path, at_lineno, "INBOX_FABRICATED_SENDER",
            f'writes to ctx.worker_inbox via {mechanism} asserting sender.kind={kind_val!r} — '
            f'report.sh (the one real door) can only ever emit sender.kind="worker"'))


# ───────────────────── structural write-mechanism scan ─────────────────────
# DENY BY DEFAULT: any call touching a traced channel is in scope UNLESS it
# is one of a small, EXPLICIT, provably-safe allow-list — never the reverse
# (an enumerated list of illegal shapes, which is exactly what the hostile
# review defeated 9/10 times).

_SAFE_READ_METHODS = {
    "close", "flush", "read", "readline", "readlines", "fileno", "tell",
    "seek", "__enter__", "__exit__",
    "exists", "is_file", "is_dir", "stat", "lstat", "read_text", "read_bytes",
    "resolve", "absolute", "samefile", "iterdir",
}
_SAFE_READ_OSPATH_FUNCS = {
    "exists", "isfile", "isdir", "getsize", "getmtime", "getctime",
    "dirname", "basename", "abspath", "realpath", "relpath", "normpath",
    "join", "split", "splitext",
}


def _is_os_path_call(call):
    f = call.func
    return (isinstance(f, ast.Attribute) and f.attr in _SAFE_READ_OSPATH_FUNCS
            and isinstance(f.value, ast.Attribute) and f.value.attr == "path"
            and isinstance(f.value.value, ast.Name) and f.value.value.id == "os")


def _is_reference_producing_call(call):
    """A call whose only role is to PRODUCE a path/attr/handle reference
    (`open`/`io.open`/`pathlib.Path`/`getattr`) — traced INTO by
    `_resolve_channel` (so a downstream use of the reference IS checked),
    but never a violation standing alone: opening/referencing is not
    writing."""
    if isinstance(call.func, ast.Name) and call.func.id in _REFERENCE_CALL_NAMES:
        return True
    if isinstance(call.func, ast.Attribute) and call.func.attr in _REFERENCE_CALL_ATTRS:
        return True
    return False


def _is_local_call(call, ctx):
    """A call whose target is a function/method DEFINED IN THIS FILE — this
    lint can (and does) look inside it: `_resolve_channel`'s inbound-
    parameter trace reaches every real call site from wherever the
    function's OWN body actually performs a write, so the outer call
    (merely forwarding a path/handle to a helper) is never itself flagged —
    only the real underlying operation is, wherever it structurally lives."""
    if isinstance(call.func, ast.Name):
        return call.func.id in ctx.funcs
    if isinstance(call.func, ast.Attribute):
        return call.func.attr in ctx.funcs
    return False


def _call_touches(call):
    """Every position that could carry the channel: the receiver (a method
    call's target) plus every positional arg and keyword value — the whole
    call surface, never one hand-picked slot per enumerated shape."""
    touches = []
    if isinstance(call.func, ast.Attribute):
        touches.append(("receiver", call.func.value))
    for a in call.args:
        touches.append(("arg", a))
    for kw in call.keywords:
        touches.append((f"kw:{kw.arg}", kw.value))
    return touches


def _describe_call(call):
    try:
        return f"`{ast.unparse(call.func)}(...)`"
    except Exception:   # noqa: BLE001 — unparse is best-effort for the message only
        return "a call"


def _check_channel_writes(tree, ctx, path):
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _is_local_call(node, ctx):
            continue
        if _is_reference_producing_call(node):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr in _SAFE_READ_METHODS:
            continue
        if _is_os_path_call(node):
            continue
        touches = _call_touches(node)
        channel_hit = None
        for role, e in touches:
            k = _resolve_channel(e, node.lineno, ctx)
            if k:
                channel_hit = (role, e, k)
                break
        if channel_hit is None:
            continue
        channel_role, channel_expr, kind = channel_hit
        # payload = the first OTHER (non-receiver, non-channel) touch — the
        # generic mirror of "whatever this write-shaped call's other slot
        # is" (`.write(content)`'s arg, `print(content, file=ib)`'s arg,
        # `append_jsonl(path, obj)`'s obj, ...).
        payload_candidates = [e for role, e in touches
                               if role != "receiver" and not (role == channel_role and e is channel_expr)]
        payload_expr = _unwrap_json_dumps(payload_candidates[0]) if payload_candidates else None
        _emit_channel_violation(kind, payload_expr, path, node.lineno, violations,
                                 _describe_call(node), ctx)
    violations.extend(_check_subprocess_redirect(tree, ctx, path))
    return violations


_SUBPROC_ATTRS = {"run", "call", "check_call", "check_output", "Popen", "system", "popen"}


def _is_subprocess_like_call(call):
    func = call.func
    return (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
            and func.value.id in ("subprocess", "os") and func.attr in _SUBPROC_ATTRS)


_REDIRECT_RE = re.compile(r">>|(?<!-)>(?!=)")


def _find_dumps_payload(node):
    """The first `json.dumps(X)` call anywhere inside `node`'s subtree ->
    `X`; used to recover a payload embedded in a shelled-out command
    string."""
    for sub in ast.walk(node):
        if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                and sub.func.attr == "dumps" and isinstance(sub.func.value, ast.Name)
                and sub.func.value.id == "json" and sub.args):
            return sub.args[0]
    return None


def _check_subprocess_redirect(tree, ctx, path):
    """A shelled-out `subprocess`/`os.system` command containing a `>`/`>>`
    redirect into an inbox-shaped target — never a real production shape
    (report.sh is always invoked via argv, never shell-redirected into). A
    fundamentally different, textual mechanism (shell command TEXT, not a
    Python call graph) from the structural scan above — kept separate, and
    still not a shell parser (see module docstring's honest limits)."""
    violations = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _is_subprocess_like_call(node)):
            continue
        try:
            text = ast.unparse(node)
        except Exception:
            continue
        if not _REDIRECT_RE.search(text):
            continue
        low = text.lower()
        if "operator_inbox" in low or "operator-inbox" in low:
            kind = "operator"
        elif "worker_inbox" in low or "worker-inbox" in low or "inbox" in low:
            kind = "worker"
        else:
            kind = None
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name):
                    k = _resolve_channel(sub, node.lineno, ctx)
                    if k:
                        kind = k
                        break
            if kind is None:
                continue
        payload = _find_dumps_payload(node)
        _emit_channel_violation(kind, payload, path, node.lineno, violations,
                                 "a shelled-out subprocess redirect (>>/>)", ctx)
    return violations


# ─────────────────────────── manifest direct-write ───────────────────────────

def _is_direct_manifest_ref(node):
    if isinstance(node, ast.Name):
        return "manifest" in node.id.lower()
    if isinstance(node, ast.Attribute):
        return "manifest" in node.attr.lower()
    return False


def _resolve_manifest(expr, before_lineno, ctx, depth=0):
    """Is `expr` — an assignment/`.update()` target, OR a bound alias'
    value — rooted at a manifest reference? Subscripts are unwound first
    (any depth >= 1 counts); the root is then checked directly, via a
    traced Name alias, via a `dict`/`list` container WRAPPING a manifest
    reference (unwound recursively — closes `bag = {"m": eng.manifest}`),
    or via the same bounded inbound/outbound call-graph trace the channel
    side uses (closes a same-file helper that RETURNS `eng.manifest`)."""
    if expr is None or depth > _MAX_TRACE_DEPTH:
        return False
    cur = expr
    while isinstance(cur, ast.Subscript):
        cur = cur.value
    if _is_direct_manifest_ref(cur):
        return True
    if isinstance(cur, ast.Name):
        val = _nearest_assign_value(ctx.assigns, cur.id, before_lineno)
        if val is not None:
            return _resolve_manifest(val, before_lineno, ctx, depth + 1)
        return bool(_resolve_param_inbound(cur, before_lineno, ctx, _resolve_manifest, depth))
    if isinstance(cur, (ast.Dict, ast.List)):
        vals = cur.values if isinstance(cur, ast.Dict) else cur.elts
        return any(_resolve_manifest(v, before_lineno, ctx, depth + 1) for v in vals)
    if isinstance(cur, ast.Call):
        return bool(_resolve_call_return(cur, before_lineno, ctx, _resolve_manifest, depth))
    return False


def _check_manifest_direct_write(tree, ctx, path):
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        else:
            targets = None
        if targets:
            for tgt in targets:
                if isinstance(tgt, ast.Subscript) and _resolve_manifest(tgt, node.lineno, ctx):
                    try:
                        shape = ast.unparse(tgt)
                    except Exception:
                        shape = "<subscript>"
                    violations.append(Violation(
                        path, node.lineno, "MANIFEST_DIRECT_WRITE",
                        f"assigns into manifest-rooted `{shape}` directly — bypasses the "
                        "real drain (tick -> classify -> router)"))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "update" and _resolve_manifest(node.func.value, node.lineno, ctx)):
            try:
                shape = ast.unparse(node.func.value)
            except Exception:
                shape = "<expr>"
            violations.append(Violation(
                path, node.lineno, "MANIFEST_DIRECT_WRITE",
                f"calls `.update()` on manifest-rooted `{shape}` directly — bypasses the "
                "real drain (tick -> classify -> router)"))
    return violations


# ─────────────────────────────── driver ───────────────────────────────

def lint_file(path):
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    return lint_source(source, path=path)


def lint_source(source, path="<fixture>"):
    tree = ast.parse(source, filename=path)
    ctx = _Ctx(tree)
    return _check_channel_writes(tree, ctx, path) + _check_manifest_direct_write(tree, ctx, path)


class LintResult:
    def __init__(self):
        self.violations_by_file = {}   # rel_path -> [Violation]
        self.stale_known_red = []      # KNOWN_RED entries that came back clean
        self.unlisted_offenders = []   # red rel_paths not in KNOWN_RED

    @property
    def ok(self):
        return not self.stale_known_red and not self.unlisted_offenders


def run(files=None):
    files = files if files is not None else harness_files()
    result = LintResult()
    for path in files:
        rel = os.path.relpath(path, ROOT)
        violations = lint_file(path)
        if violations:
            result.violations_by_file[rel] = violations
    for rel in KNOWN_RED:
        if rel not in result.violations_by_file:
            result.stale_known_red.append(rel)
    for rel in result.violations_by_file:
        if rel not in KNOWN_RED:
            result.unlisted_offenders.append(rel)
    return result


def main():
    result = run()
    for rel, entry in KNOWN_RED.items():
        red = rel in result.violations_by_file
        status = "RED (tracked)" if red else "STALE — now clean, remove from KNOWN_RED"
        print(f"[known-red] {rel}: {status} — owning block {entry['owning_block']}")
        for v in result.violations_by_file.get(rel, []):
            print(f"    {v}")
    for rel in result.unlisted_offenders:
        print(f"[UNLISTED OFFENDER] {rel}:")
        for v in result.violations_by_file[rel]:
            print(f"    {v}")
    ok = result.ok
    print(f"\nr3_lint: {'PASS' if ok else 'FAIL'} "
          f"({len(result.violations_by_file)} file(s) red, "
          f"{len(result.stale_known_red)} stale, {len(result.unlisted_offenders)} unlisted)")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
