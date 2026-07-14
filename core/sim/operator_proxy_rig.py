"""core.sim.operator_proxy_rig — unit + honest-path lock for the MODERATE-tier
LLM operator-proxy (`core.sim.operator_proxy`, ADR-0007).

The proxy stands an LLM in for the operator on a moderate SIM: it finds every
case the engine escalated to the operator and injects a decision. The single
most important property — the one that keeps it from reintroducing the false-
green disease — is that it can ONLY settle a genuinely-escalated operator case,
by the SAME classify->router->settle path a real operator reply travels, and it
fabricates NOTHING else. So this rig's flagship proofs are the HONEST-PATH ones
(E1/E2): a decision the proxy injects is routed by the REAL `core.classify` +
`core.router` + `core.casestate.settle` and actually settles the case — no
faked trunk, no direct case-dict mutation.

Block 01-38 T6 (R3 MODEL A — the honest rebuild): `_inject_decision` no longer
writes a hand-built dict straight into an intake file (`core.intake.write`) —
it now shells out to a REAL `scripts/report.sh --intake <path>` subprocess,
exactly the door a genuine operator reply uses. Every proof that exercises
injection now runs over a REAL canon-installed instance (`_fresh_ctxroot`
below calls `core.sim.seed_canon.install_canon`, so `scripts/report.sh` +
`vocab.schema.json` genuinely exist on disk) — no more bare scratch dir a
Python-level `intake.write` call alone could satisfy. `G1`-`G3` (bottom) are
the block's own named proof, `test:<rigs_honest_by_construction>`: the
runtime write-guard (`core/r3_guard.py`) genuinely trips on a direct
fabricated-sender write to this proxy's own intake file, a genuine unprotected
write is unaffected (non-vacuity), and the REBUILT `_inject_decision` still
lands its line under the SAME guard — because it never performs an in-process
write at all, only a real `report.sh` child-process call the guard's own
documented per-interpreter boundary does not (and structurally cannot) reach.

Token-free throughout via the `decide_fn` seam: every proof injects a stub
decision, so the rig asserts the WIRING (predicate -> inject -> settle; gating;
idempotency; architect-refusal; malformed-drop), never a model's judgment.

Proofs:
  P1  _needs_operator: operator-owned + OPEN                 -> True
  P2  _needs_operator: architect-owned + open               -> False (never bypass architect-first)
  P3  _needs_operator: operator-owned + already-settled      -> False
  P4  _parse_decision: clean / fenced / prose / bad-verb / empty (tolerance lock)
  P5  _inject_decision runs a REAL report.sh call — plain text, no fabricated tag/sender
  T1  tick on an operator-owned open case (stub resume)     -> injects 1, marks decided
  T2  tick again, case already decided this run             -> no-op (idempotent)
  T3  tick on an ARCHITECT-owned case                       -> no inject, decide_fn NEVER called
  T4  tick, decide_fn returns None (malformed)              -> no inject, attempt counted, no crash
  T5  tick, decide_fn keeps failing                          -> capped at _MAX_ATTEMPTS calls
  T6  tick over a mixed manifest (op-open / arch-open / settled) -> only the op-open injects
  E1  HONEST PATH: injected {resume} -> real classify+router+settle -> case SETTLED (no dangling)
  E2  HONEST PATH: injected {abandon} -> case settled AND block in abandoned_blocks
  E3  HONEST negative: a bad-verb decision never settles -> case stays OPEN (honest REJECT surface)
  E4  DEFENSE LAYER 2: a bad-verb report routed through the REAL router is refused by
      `casestate.settle` ITSELF (independent of the proxy's own layer-1 filter) -> case stays OPEN
  G1-G3 test:<rigs_honest_by_construction> — the block's AC-4 proof (see below)

`ok(name, cond, detail)`; `main()` prints `PASS (n/m)`, exits non-zero on fail.
"""
import json
import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE_DIR = os.path.dirname(_HERE)
_APP_ROOT = os.path.dirname(_CORE_DIR)
sys.path.insert(0, os.path.join(_APP_ROOT, "engine"))
sys.path.insert(0, _CORE_DIR)
sys.path.insert(0, _HERE)

import casestate                       # noqa: E402 — core/casestate.py, the real settle
import classify                        # noqa: E402 — core/classify.py, the real structured bypass
import router                          # noqa: E402 — core/router.py, the real operator.decision route
import operator_proxy as op            # noqa: E402 — core/sim/operator_proxy.py, unit under test
import intake                          # noqa: E402 — core/intake.py, block 01-38 T1's private per-agent intake
import vocab                           # noqa: E402 — core/vocab.py, OPERATOR kind (block 01-38 T2's typed Origin)
import r3_guard                        # noqa: E402 — core/r3_guard.py, the runtime write-guard under proof (G1-G3)
from seed_canon import install_canon   # noqa: E402 — core/sim/seed_canon.py, installs a REAL scripts/report.sh

_results = []


def ok(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    return bool(cond)


class _DuckCtx:
    """Real-shaped enough for `core.intake` (block 01-38 T1): just `.p()`,
    resolving under a fresh scratch root — no other `Ctx` surface is
    touched by `_inject_decision`/`core.intake.write`."""
    def __init__(self, root):
        self.dir = root

    def p(self, *parts):
        return os.path.join(self.dir, *parts)


class _RigEvents:
    """Minimal `.event(type, **payload)` sink (block 01-38 T7): casestate's
    settle path now routes its state changes through the emit API, so the
    duck eng needs an events sink exactly as the real Engine has."""
    def __init__(self):
        self.log = []

    def event(self, type_, **payload):
        self.log.append({"type": type_, "payload": payload})


class _DuckEng:
    """The minimum `eng` surface `_inject_decision` + `settle` (resume/abandon)
    touch: a real-shaped ctx (ONLY for `core.intake`'s own `.p()` — no other
    `Ctx` surface), `.dry`, a `.log` sink, and (block 01-38 T7) an `.events`
    sink casestate's emit-routed settle path writes to."""
    def __init__(self, root):
        self.dry = True
        self.ctx = _DuckCtx(root)
        self.logs = []
        self.events = _RigEvents()

    def log(self, channel, msg):
        self.logs.append((channel, msg))


def _op_case(cid, block="01-02", owner="operator", decision=None):
    """A case dict in `open_operator_case`'s shape — only the keys the proxy /
    settle actually read need be present."""
    return {
        "case_id": cid, "block": block, "kind": "wall", "source": "worker.wall",
        "worker_id": f"engineer-{block}", "detail": f"planted wall on {block}",
        "decision": decision, "owner": owner,
    }


def _fresh_ctxroot():
    """A fresh scratch dir with the REAL canon installed (`scripts/report.sh`
    + `vocab.schema.json`, `core.sim.seed_canon.install_canon`) — block 01-38
    T6's honest rebuild routes every injection through a genuine `report.sh`
    subprocess, so every proof that exercises `_inject_decision`/`tick()`
    needs the real door PRESENT on disk, not just a bare directory `core.
    intake` can mint a private intake file under. `core.intake` still mints
    `_OPERATOR_PROXY_WID`'s own private intake underneath it lazily, on
    first write — never a bare pre-created inbox FILE (there is no shared
    one any more)."""
    root = tempfile.mkdtemp(prefix="opproxy_ctxroot_")
    install_canon(root)
    return root


def _last_line(ctx):
    path = intake.intake_path(ctx, op._OPERATOR_PROXY_WID)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    return json.loads(lines[-1]) if lines else None


def _count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path) as f:
        return len([ln for ln in f.read().splitlines() if ln.strip()])


# ═══════════════════════════════════════════════════════════════════════
# test:<rigs_honest_by_construction> (block 01-38 T6, the AC-4 proof) —
# G1-G3, below. Each leg spawns a FRESH child interpreter: `core/r3_guard.py`
# `install()` is a per-process singleton (a second call in an already-
# guarded process — e.g. this rig running under `scripts/l1.sh`'s OWN guard,
# which protects a DIFFERENT path — is a silent no-op), so only a fresh
# child can install a hook over OUR OWN chosen protected-path spec, exactly
# the `.github/scripts/r3_guard_runtime_check.py` pattern.
# ═══════════════════════════════════════════════════════════════════════
def _guarded_env(protect_spec):
    site_dir = tempfile.mkdtemp(prefix="rhbc_site_")
    r3_guard.materialize_site_dir(site_dir, core_dir=_CORE_DIR)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([site_dir, env.get("PYTHONPATH", "")])
    env["R3_GUARD_PROTECT"] = protect_spec
    env["R3_GUARD_RIG"] = "rigs_honest_by_construction-proof"
    return env


def _run_child(code, protect_spec, timeout=25):
    env = _guarded_env(protect_spec)
    return subprocess.run([sys.executable, "-c", code], env=env,
                          capture_output=True, text=True, timeout=timeout)


def _direct_write_code(root, wid):
    """The OLD, dishonest mechanism T6 removed: a raw in-process
    `core.intake.write` call carrying a fabricated `sender.kind="operator"`
    payload — never through `scripts/report.sh`. G1 proves the runtime
    guard denies exactly this shape."""
    return f"""
import sys
sys.path.insert(0, {_CORE_DIR!r})
import intake

class _C:
    def __init__(self, d):
        self.dir = d
    def p(self, *parts):
        import os
        return os.path.join(self.dir, *parts)

ctx = _C({root!r})
intake.write(ctx, {wid!r}, {{"tag": "operator.decision",
                             "slots": {{"case_id": "X", "verb": "resume"}},
                             "sender": {{"kind": "operator", "id": {wid!r}}}}})
print("WROTE-OK")
"""


def _inject_code(root, wid):
    """The REBUILT, honest mechanism: calls `operator_proxy._inject_decision`
    itself — which only ever shells out to a real `scripts/report.sh`
    subprocess, never an in-process write. G3 proves this still lands its
    line even while the SAME file is guard-protected."""
    return f"""
import sys
sys.path.insert(0, {_CORE_DIR!r})
sys.path.insert(0, {_HERE!r})
import operator_proxy as op

class _C:
    def __init__(self, d):
        self.dir = d
    def p(self, *parts):
        import os
        return os.path.join(self.dir, *parts)

class _E:
    def __init__(self, d):
        self.ctx = _C(d)
    def log(self, ch, msg):
        pass

eng = _E({root!r})
ok = op._inject_decision(eng, "CASE-G3", {{"verb": "resume", "note": "door-proof"}})
print("INJECT-OK" if ok else "INJECT-FAIL")
"""


def run_rigs_honest_by_construction():
    # G1 — THE TRIP: a direct, in-process, fabricated-sender write (the
    # mechanism this module used BEFORE T6) dies under the guard.
    g1_root = tempfile.mkdtemp(prefix="rhbc_direct_")
    protected_path = intake.intake_path(_DuckCtx(g1_root), op._OPERATOR_PROXY_WID)
    r_g1 = _run_child(_direct_write_code(g1_root, op._OPERATOR_PROXY_WID), protected_path)
    g1_landed = os.path.exists(protected_path) and os.path.getsize(protected_path) > 0
    ok("test:<rigs_honest_by_construction> G1 (THE GUARD TRIPS): a direct "
       "in-process fabricated-sender write to this proxy's own intake file "
       "— the SAME mechanism T6 removed — is DENIED by core/r3_guard.py's "
       "runtime write-guard: the child dies, 'WROTE-OK' never prints, and "
       "the protected file is never created/written",
       r_g1.returncode != 0 and "WROTE-OK" not in (r_g1.stdout or "") and not g1_landed,
       f"rc={r_g1.returncode} stdout={r_g1.stdout!r} "
       f"stderr_tail={(r_g1.stderr or '')[-300:]!r} landed={g1_landed}")

    # G2 — NON-VACUITY: the IDENTICAL direct-write code, run under an
    # ACTIVE guard whose spec names a genuinely UNRELATED path, succeeds
    # normally — proves G1's failure is the real guard tripping on a real
    # match, never an incidental bug (missing module, bad code, wrong
    # interpreter, ...).
    g2_root = tempfile.mkdtemp(prefix="rhbc_unprotected_")
    g2_target = intake.intake_path(_DuckCtx(g2_root), op._OPERATOR_PROXY_WID)
    unrelated_spec = os.path.join(g2_root, "__nothing_writes_here__.jsonl")
    r_g2 = _run_child(_direct_write_code(g2_root, op._OPERATOR_PROXY_WID), unrelated_spec)
    g2_landed = os.path.exists(g2_target) and os.path.getsize(g2_target) > 0
    ok("test:<rigs_honest_by_construction> G2 (NON-VACUITY): the IDENTICAL "
       "direct-write code, run under an ACTIVE guard whose spec names a "
       "genuinely UNRELATED path, succeeds normally ('WROTE-OK' prints, "
       "the line lands) — G1's failure is the guard matching a real "
       "protected path, not a broken proof",
       r_g2.returncode == 0 and "WROTE-OK" in (r_g2.stdout or "") and g2_landed,
       f"rc={r_g2.returncode} stdout={r_g2.stdout!r} landed={g2_landed}")

    # G3 — THE REBUILT RIG PASSES THROUGH THE DOOR: under the EXACT SAME
    # guard protecting the SAME file G1 just proved unwritable in-process,
    # the REBUILT `_inject_decision` still lands its line — because it
    # never performs a protected write itself, only a real `report.sh`
    # CHILD-PROCESS call (a fresh OS process, outside this guarded
    # interpreter's own per-process audit hook — `core/r3_guard.py`'s own
    # module docstring names this as a real, structural limit of an
    # in-process mechanism, not a loophole this rig exploits: shelling out
    # to the real door IS the honest mechanism, not a bypass of it).
    g3_root = _fresh_ctxroot()
    protected_path2 = intake.intake_path(_DuckCtx(g3_root), op._OPERATOR_PROXY_WID)
    r_g3 = _run_child(_inject_code(g3_root, op._OPERATOR_PROXY_WID), protected_path2)
    g3_line = None
    if os.path.exists(protected_path2):
        with open(protected_path2) as fh:
            g3_lines = [json.loads(ln) for ln in fh if ln.strip()]
        g3_line = g3_lines[-1] if g3_lines else None
    ok("test:<rigs_honest_by_construction> G3 (REBUILT RIG PASSES THROUGH "
       "THE DOOR): under the SAME guard protecting the SAME file G1 proved "
       "unwritable in-process, the REBUILT operator_proxy._inject_decision "
       "still lands a REAL report.sh-produced line (sender.kind='worker', "
       "genuinely produced by report.sh's own jq — never JSON this rig "
       "built by hand) — it never performs an in-process write, only a "
       "real subprocess call through the door",
       r_g3.returncode == 0 and "INJECT-OK" in (r_g3.stdout or "")
       and g3_line is not None and g3_line.get("sender", {}).get("kind") == "worker"
       and "CASE-G3" in g3_line.get("text", ""),
       f"rc={r_g3.returncode} stdout={r_g3.stdout!r} g3_line={g3_line}")


def main():
    # ── P1-P3: the predicate is exactly casestate.reping's (never architect) ──
    ok("P1: _needs_operator TRUE for an operator-owned OPEN case",
       op._needs_operator(_op_case("c1")) is True)
    ok("P2: _needs_operator FALSE for an ARCHITECT-owned case (never bypass architect-first)",
       op._needs_operator(_op_case("c2", owner="architect")) is False)
    ok("P3: _needs_operator FALSE for an already-SETTLED operator case",
       op._needs_operator(_op_case("c3", decision="resume")) is False)

    # ── P4: parse tolerance ──
    ok("P4a: clean JSON parses",
       op._parse_decision('{"verb": "resume", "note": "ok"}') == {"verb": "resume", "note": "ok"})
    ok("P4b: a ```json-fenced object inside prose parses",
       (op._parse_decision('Sure.\n```json\n{"verb": "amend", "note": "fix"}\n```') or {}).get("verb") == "amend")
    ok("P4c: prose with no JSON object -> None (never a guessed verb)",
       op._parse_decision("I think we should resume actually") is None)
    ok("P4d: a JSON object with a non-VERB verb -> None",
       op._parse_decision('{"verb": "nuke"}') is None)
    ok("P4e: empty text -> None",
       op._parse_decision("") is None)

    # ── P5: injection shape (block 01-38 T6 — a REAL report.sh call, plain
    # text, NO fabricated tag/slots/sender payload; report.sh itself always
    # stamps sender.kind="worker" — the honest rebuild's whole point is that
    # the OPERATOR classification comes from the intake CHANNEL, never this
    # payload) ──
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    injected_p5 = op._inject_decision(eng, "CASE-9", {"verb": "resume", "note": "unblock it"})
    line = _last_line(eng.ctx)
    ok("P5: _inject_decision runs a REAL report.sh call — the raw written "
       "line is PLAIN TEXT naming the verb+case id, report.sh's own "
       "hardcoded sender.kind='worker' (never a fabricated 'operator' "
       "sender, never a tag/slots payload this module built by hand)",
       injected_p5 is True and line
       and line.get("sender", {}).get("kind") == "worker"
       and line.get("sender", {}).get("id") == op._OPERATOR_PROXY_WID
       and "resume" in line.get("text", "") and "CASE-9" in line.get("text", ""),
       f"line={line}")

    # ── T1/T2: inject once, then idempotent ──
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    manifest = {"cases": {"CASE-1": _op_case("CASE-1")}}
    decided, attempts = set(), {}
    calls = {"n": 0}

    def stub_resume(case):
        calls["n"] += 1
        return {"verb": "resume", "note": "proxy: unblock"}

    n1 = op.tick(eng, manifest, decided, attempts, decide_fn=stub_resume)
    ok("T1: tick injects exactly one decision for one operator-owned open case, marks it decided",
       n1 == 1 and "CASE-1" in decided and _count_lines(intake.intake_path(eng.ctx, op._OPERATOR_PROXY_WID)) == 1, f"n1={n1} decided={decided}")
    n2 = op.tick(eng, manifest, decided, attempts, decide_fn=stub_resume)
    ok("T2: tick is idempotent — a case already decided this run is a no-op (no second line)",
       n2 == 0 and _count_lines(intake.intake_path(eng.ctx, op._OPERATOR_PROXY_WID)) == 1 and calls["n"] == 1, f"n2={n2} calls={calls['n']}")

    # ── T3: an ARCHITECT-owned case is never touched, decide_fn never called ──
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    manifest = {"cases": {"CASE-A": _op_case("CASE-A", owner="architect")}}
    ac = {"n": 0}

    def stub_counted(case):
        ac["n"] += 1
        return {"verb": "resume"}

    n3 = op.tick(eng, manifest, set(), {}, decide_fn=stub_counted)
    ok("T3: tick never acts on an ARCHITECT-owned case (no inject, decide_fn NEVER called)",
       n3 == 0 and _count_lines(intake.intake_path(eng.ctx, op._OPERATOR_PROXY_WID)) == 0 and ac["n"] == 0, f"n3={n3} decide_calls={ac['n']}")

    # ── T4: a malformed decision (None) never injects, counts an attempt, no crash ──
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    manifest = {"cases": {"CASE-M": _op_case("CASE-M")}}
    decided, attempts = set(), {}
    n4 = op.tick(eng, manifest, decided, attempts, decide_fn=lambda c: None)
    ok("T4: a malformed (None) decision -> no inject, case NOT marked decided, attempt counted",
       n4 == 0 and _count_lines(intake.intake_path(eng.ctx, op._OPERATOR_PROXY_WID)) == 0 and "CASE-M" not in decided
       and attempts.get("CASE-M") == 1, f"n4={n4} attempts={attempts}")

    # ── T5: repeated failure is capped at _MAX_ATTEMPTS decide_fn calls ──
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    manifest = {"cases": {"CASE-C": _op_case("CASE-C")}}
    decided, attempts = set(), {}
    fc = {"n": 0}

    def stub_fail(case):
        fc["n"] += 1
        return None

    for _ in range(op._MAX_ATTEMPTS + 3):
        op.tick(eng, manifest, decided, attempts, decide_fn=stub_fail)
    ok("T5: a persistently-failing decide_fn is capped at _MAX_ATTEMPTS calls (no infinite retry, no inject)",
       fc["n"] == op._MAX_ATTEMPTS and _count_lines(intake.intake_path(eng.ctx, op._OPERATOR_PROXY_WID)) == 0,
       f"decide_calls={fc['n']} cap={op._MAX_ATTEMPTS}")

    # ── T6: mixed manifest — only the operator-owned OPEN case is injected ──
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    manifest = {"cases": {
        "OP-OPEN": _op_case("OP-OPEN", block="01-02"),
        "ARCH": _op_case("ARCH", block="01-03", owner="architect"),
        "SETTLED": _op_case("SETTLED", block="01-04", decision="resume"),
    }}
    n6 = op.tick(eng, manifest, set(), {}, decide_fn=stub_resume)
    injected = _last_line(eng.ctx)
    ok("T6: over a mixed manifest, ONLY the operator-owned open case is injected",
       n6 == 1 and _count_lines(intake.intake_path(eng.ctx, op._OPERATOR_PROXY_WID)) == 1
       and injected and "OP-OPEN" in injected.get("text", ""),
       f"n6={n6} injected_text={injected and injected.get('text')}")

    # ══ E1: THE HONEST PATH — injected {resume} routed by REAL classify+router+settle ══
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    manifest = {"cases": {"CASE-E1": _op_case("CASE-E1")}}
    op.tick(eng, manifest, set(), {}, decide_fn=lambda c: {"verb": "resume", "note": "unblock"})
    msg = _last_line(eng.ctx)
    tag, slots = classify.classify(
        eng, intake.Origin(vocab.OPERATOR, op._OPERATOR_PROXY_WID), msg, manifest)
    ok("E1a: the injected line classifies as operator.decision via the real structured bypass",
       tag == "operator.decision" and slots.get("case_id") == "CASE-E1" and slots.get("verb") == "resume",
       f"tag={tag} slots={slots}")
    router._route_decision(eng, manifest, {"tag": tag, "slots": slots})
    ok("E1b: the REAL settle path removed the case (no dangling open case — the gate's conjunct)",
       "CASE-E1" not in manifest.get("cases", {}), f"cases={list(manifest.get('cases', {}))}")

    # ══ E2: injected {abandon} — settled AND block abandoned, via the real path ══
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    manifest = {"cases": {"CASE-E2": _op_case("CASE-E2", block="01-07")}}
    op.tick(eng, manifest, set(), {}, decide_fn=lambda c: {"verb": "abandon", "note": "out of scope"})
    msg = _last_line(eng.ctx)
    tag, slots = classify.classify(
        eng, intake.Origin(vocab.OPERATOR, op._OPERATOR_PROXY_WID), msg, manifest)
    router._route_decision(eng, manifest, {"tag": tag, "slots": slots})
    ok("E2: injected abandon settles via the real path — case cleared AND block in abandoned_blocks",
       "CASE-E2" not in manifest.get("cases", {})
       and "01-07" in (manifest.get("abandoned_blocks") or []),
       f"cases={list(manifest.get('cases', {}))} abandoned={manifest.get('abandoned_blocks')}")

    # ══ E3: HONEST negative — a bad-verb decision never settles; the case stays OPEN ══
    ctxroot = _fresh_ctxroot()
    eng = _DuckEng(ctxroot)
    manifest = {"cases": {"CASE-E3": _op_case("CASE-E3")}}
    n = op.tick(eng, manifest, set(), {}, decide_fn=lambda c: {"verb": "nuke"})
    ok("E3: a bad-verb decision injects nothing and leaves the case OPEN (a malformed op reply never greens)",
       n == 0 and manifest["cases"]["CASE-E3"].get("decision") is None,
       f"n={n} decision={manifest['cases']['CASE-E3'].get('decision')}")

    # ══ E4: DEFENSE LAYER 2 — settle's OWN verb-guard. Bypass the proxy's layer-1
    # filter and hand the REAL router a bad-verb operator.decision directly: the
    # case must stay OPEN because `casestate.settle` itself refuses a non-VERB verb
    # (proves the two layers are independent — a mutation deleting settle's own
    # check would be caught here, not masked by the proxy's filter always firing first).
    eng = _DuckEng(_fresh_ctxroot())
    manifest = {"cases": {"CASE-E4": _op_case("CASE-E4")}}
    router._route_decision(eng, manifest, {"tag": "operator.decision",
                                           "slots": {"case_id": "CASE-E4", "verb": "nuke"}})
    ok("E4: settle's OWN verb-guard refuses a bad verb via the real router (defense layer 2) — case stays OPEN",
       "CASE-E4" in manifest.get("cases", {})
       and manifest["cases"]["CASE-E4"].get("decision") is None,
       f"case={manifest.get('cases', {}).get('CASE-E4')}")

    run_rigs_honest_by_construction()

    passed = sum(1 for _, c, _ in _results if c)
    print(f"\ncore.sim.operator_proxy_rig: {'PASS' if passed == len(_results) else 'FAIL'} "
          f"({passed}/{len(_results)})")
    for name, c, detail in _results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {detail}" if detail and not c else ""))
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
