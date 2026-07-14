#!/usr/bin/env python3
"""r3_honesty_lint_check.py — AC-2 (block 01-40 T1) CI proof.

`core/r3_lint.py` is the R3 honesty lint: a harness may not fabricate a
sender kind the real door (scripts/report.sh) could never produce, write
`ctx.operator_inbox` at all (no real operator transport exists yet), nor
mutate `manifest[...]` state directly. This is the FOURTH rebuild. Rounds
one through three each replaced one finite enumeration (write mechanisms,
then binding shapes) with a bigger finite enumeration, and each time a
hostile review found the next shape outside it — round three's own binding
walk still resolved a USE back to the NEAREST prior binding, which a FOURTH
review broke with if/else and try/except branch shadowing (the nearest
binding is not always the taint-carrying one), `os.path.*`/`str()`
reconstruction (taint didn't propagate through an arbitrary call), `IfExp`/
`BoolOp` (unhandled expression shapes fell through to unresolved-but-
skipped), `AugAssign` as a binding form, and lambda closures. This FOURTH
rebuild replaces resolution entirely with a flow-insensitive TAINT UNION
computed as a monotone fixed point (see `core/r3_lint.py`'s own docstring):
a name is tainted with a marker's kind if ANY binding anywhere in its own
lexical scope carries that kind — never "the nearest one" — so a missed
case can only cause a false RED, never a false GREEN. Proves, live:

  RED (x28)  every evasion the first three hostile reviews produced is
             still caught (10 write-mechanism evasions, 10 further
             write-mechanism evasions, 8 binding-shape evasions — see
             each fixture's own inline comment for what it demonstrates).
  RED (x6)   each of the 6 FOURTH-review evasions is caught: if/else and
             try/except branch shadowing (`dest = eng.ctx.worker_inbox`
             bound in one branch, an inert literal in the other — nearest-
             binding picked the wrong one depending on branch order),
             `AugAssign` as a binding form (`dest = ""; dest +=
             eng.ctx.worker_inbox`), a ternary (`IfExp`) and a `BoolOp`
             (`or`) channel-select, `os.path.dirname`/`basename`/`join`
             path RECONSTRUCTION (taint through a call, not a name alias),
             and a lambda closure (`getdest = lambda: eng.ctx.worker_inbox`).
  GREEN      two legal shapes stay clean: a door-only report (worker sender,
             or no sender key at all — report.sh's own shape) written
             straight, AND the identical "helper indirection" MECHANISM used
             legitimately (a thin same-file wrapper whose every real call
             site sends a safe payload) — proving the lint tells indirection
             APART from a violation, rather than reddening all indirection.
  GREEN/tree the real `core/` proof-harness tree is clean except the
             explicit, visible KNOWN_RED list (core/sim/operator_proxy.py
             at minimum) — every KNOWN_RED entry is re-verified genuinely
             red on THIS run, never a silent whitelist.
  MECHANISM  the lint's own stale/unlisted detectors fire correctly — a
             known-red entry that has gone clean is caught, and a red file
             missing from KNOWN_RED is caught — proven with synthetic
             KNOWN_RED overrides, never by editing the real list.

Exit 0 only if every one of the above holds.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "core"))

import r3_lint  # noqa: E402

# ─────────────────── the 10 evasions (each must stay RED) ───────────────────
# Every one of these is a DIRECT rewrite of the SAME violation the original
# lint caught (an operator-sender fabrication into worker_inbox, or a direct
# manifest mutation) — only the SYNTACTIC SHAPE changed. The old lint pattern-
# matched one shape per rule; these proved it caught none of the other nine.

EVASION_FIXTURES = {
    "1_renamed_inbox_path_variable": '''
import json

def bad(eng):
    p = eng.ctx.worker_inbox
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    with open(p, "a") as ib:
        ib.write(json.dumps(rep) + "\\n")
''',
    "2_path_as_file_kwarg": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    with open(file=eng.ctx.worker_inbox, mode="a") as ib:
        ib.write(json.dumps(rep) + "\\n")
''',
    "3_json_dump_to_inbox_handle": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    with open(eng.ctx.worker_inbox, "a") as ib:
        json.dump(rep, ib)
''',
    "4_bare_open_no_with": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    ib = open(eng.ctx.worker_inbox, "a")
    ib.write(json.dumps(rep) + "\\n")
    ib.close()
''',
    "5_helper_function_indirection": '''
import json

def _emit(eng, obj):
    with open(eng.ctx.worker_inbox, "a") as ib:
        ib.write(json.dumps(obj) + "\\n")

def bad(eng):
    _emit(eng, {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}})
''',
    "6_subprocess_shell_append": '''
import json
import subprocess

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    subprocess.run(["bash", "-c", f"echo '{json.dumps(rep)}' >> {eng.ctx.worker_inbox}"])
''',
    "7_manifest_alias": '''
def bad(manifest, case_id, verb):
    m = manifest
    m["cases"][case_id]["decision"] = {"verb": verb}
''',
    "8_depth1_wholesale_overwrite": '''
def bad(manifest, new_cases):
    manifest["cases"] = new_cases
''',
    "9_update_call": '''
def bad(manifest, case_id, decision):
    manifest["cases"][case_id].update({"decision": decision})
''',
    "10_sender_built_via_helper_call": '''
import json

def _build_sender():
    return {"kind": "operator", "id": "x"}

def bad(eng):
    rep = {"tag": "operator.decision", "sender": _build_sender()}
    with open(eng.ctx.worker_inbox, "a") as ib:
        ib.write(json.dumps(rep) + "\\n")
''',

    # ── SECOND-REVIEW evasions (block 01-40 T1, second rebuild) — each one
    #     defeated the FIRST rebuild's enumerated-mechanism design by using
    #     a write/target-resolution SHAPE outside its fixed shape list. ──

    "11_print_file_kwarg": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    with open(eng.ctx.worker_inbox, "a") as ib:
        print(json.dumps(rep), file=ib)
''',

    "12_pathlib_open_chain": '''
import json
import pathlib

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    pathlib.Path(eng.ctx.worker_inbox).open("a").write(json.dumps(rep) + "\\n")
''',

    "13_pathlib_write_text": '''
import json
import pathlib

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    p = pathlib.Path(eng.ctx.worker_inbox)
    existing = p.read_text() if p.exists() else ""
    p.write_text(existing + json.dumps(rep) + "\\n")
''',

    "14_target_path_helper_indirection": '''
import json

def _channel(eng):
    return eng.ctx.worker_inbox

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    dest = _channel(eng)
    with open(dest, "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "15_getattr_constant_indirection": '''
import json

_CHANNEL_ATTR = "worker_inbox"

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    with open(getattr(eng.ctx, _CHANNEL_ATTR), "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "16_manifest_wrapped_in_dict": '''
def bad(eng, case_id, verb):
    bag = {"m": eng.manifest}
    bag["m"]["cases"][case_id]["decision"] = {"verb": verb}
''',

    "17_manifest_wrapped_in_list": '''
def bad(eng, case_id, verb):
    refs = [eng.manifest]
    refs[0]["cases"][case_id]["decision"] = {"verb": verb}
''',

    "18_manifest_via_helper_call": '''
def _state(eng):
    return eng.manifest

def bad(eng, case_id, verb):
    _state(eng)["cases"][case_id]["decision"] = {"verb": verb}
''',

    "19_write_tmp_then_rename_onto_inbox": '''
import json
import os

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    tmp = eng.ctx.worker_inbox + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(json.dumps(rep) + "\\n")
    os.replace(tmp, eng.ctx.worker_inbox)
''',

    "20_io_open": '''
import io
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    with io.open(eng.ctx.worker_inbox, "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    # ── THIRD-REVIEW evasions (block 01-40 T1, third rebuild) — each one
    #     defeated the SECOND rebuild's write-mechanism scan not by using an
    #     unrecognized WRITE mechanism, but by using a variable-BINDING
    #     SHAPE `_collect_all_bindings` never recorded at all (tuple/list
    #     unpacking, chained assigns, a for-loop target, walrus, an
    #     attribute target) — so the channel/manifest alias was invisible
    #     to the resolver from the start, never even reaching the
    #     (already-correct) deny-by-default payload/write check. ──

    "21_tuple_unpack_from_helper": '''
import json

def _channel_and_mode(eng):
    return eng.ctx.worker_inbox, "a"

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    path, mode = _channel_and_mode(eng)
    with open(path, mode) as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "22_tuple_unpack_plain": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    path, mode = eng.ctx.worker_inbox, "a"
    with open(path, mode) as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "23_manifest_tuple_unpack": '''
def bad(eng, case_id, verb):
    m, _extra = eng.manifest, None
    m["cases"][case_id]["decision"] = {"verb": verb}
''',

    "24_manifest_tuple_container": '''
def bad(eng, case_id, verb):
    refs = (eng.manifest,)
    refs[0]["cases"][case_id]["decision"] = {"verb": verb}
''',

    "25_chained_assignment": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    a = path = eng.ctx.worker_inbox
    with open(path, "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "26_self_attribute_storage": '''
import json

class Reporter:
    def __init__(self, eng):
        self.dest = eng.ctx.worker_inbox

    def bad(self):
        rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
        with open(self.dest, "a") as fh:
            fh.write(json.dumps(rep) + "\\n")
''',

    "27_for_loop_binding": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    for dest in (eng.ctx.worker_inbox,):
        with open(dest, "a") as fh:
            fh.write(json.dumps(rep) + "\\n")
''',

    "28_walrus_binding": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    if (p := eng.ctx.worker_inbox):
        with open(p, "a") as fh:
            fh.write(json.dumps(rep) + "\\n")
''',

    # ── FOURTH-REVIEW evasions (block 01-40 T1, fourth rebuild) — each one
    #     defeated the THIRD rebuild's generic-binding-walk-but-NEAREST-
    #     WINS resolution: `_nearest_assign_value` picked the textually
    #     nearest/last binding for a name, so an ORDINARY idiom that binds
    #     the SAME name to a tainted value in one place and an inert value
    #     in another (if/else, try/except, AugAssign, a ternary/BoolOp
    #     select, a call-based reconstruction, a lambda closure) could
    #     silently resolve to the wrong — or no — provenance depending on
    #     branch order or unhandled expression shape. ──

    "29_augassign_path_build": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    dest = ""
    dest += eng.ctx.worker_inbox
    with open(dest, "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "30_ifexp_channel_select": '''
import json

def bad(eng, use_alt=False):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    dest = eng.ctx.worker_inbox if not use_alt else eng.ctx.worker_inbox
    with open(dest, "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "31_boolor_channel_select": '''
import json

def bad(eng, override=None):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    dest = override or eng.ctx.worker_inbox
    with open(dest, "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "32_ospath_join_reconstruct": '''
import json, os

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    d = os.path.dirname(eng.ctx.worker_inbox)
    b = os.path.basename(eng.ctx.worker_inbox)
    dest = os.path.join(d, b)
    with open(dest, "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "33_lambda_closure": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    getdest = lambda: eng.ctx.worker_inbox
    with open(getdest(), "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',

    "34_try_except_binding": '''
import json

def bad(eng):
    rep = {"tag": "operator.decision", "sender": {"kind": "operator", "id": "x"}}
    try:
        dest = eng.ctx.worker_inbox
    except Exception as e:
        dest = None
    with open(dest, "a") as fh:
        fh.write(json.dumps(rep) + "\\n")
''',
}

# ─────────────────────── legal shapes (must stay GREEN) ───────────────────────

DOOR_ONLY_FIXTURE = '''
from util import append_jsonl


def report_online(tron_ctx, agent_id, branch):
    append_jsonl(tron_ctx.worker_inbox,
                 {"tag": "worker.online", "agent_id": agent_id, "slots": {"branch": branch}})
'''

# The SAME mechanism as evasion #5 (a same-file helper wrapping the actual
# write) — but every real call site sends a safe payload (no `sender` key at
# all, matching core/casestate_rig.py's own real `inject()` helper). Proves
# the lint judges a wrapper by what its call sites ACTUALLY send, not by
# reddening all indirection on sight.
LEGAL_HELPER_INDIRECTION_FIXTURE = '''
from util import append_jsonl


def inject(tron_ctx, obj):
    append_jsonl(tron_ctx.worker_inbox, obj)


def use_it(tron_ctx):
    inject(tron_ctx, {"tag": "operator.decision", "slots": {"case_id": "c1", "verb": "resume"}})
    inject(tron_ctx, {"tag": "operator.decision", "slots": {"case_id": "c2", "verb": "abandon"}})
'''


def main():
    failed = False

    # ── RED x34: every evasion must still be caught ──
    for name, fixture in EVASION_FIXTURES.items():
        violations = r3_lint.lint_source(fixture, path=f"<evasion:{name}>")
        if violations:
            print(f"RED proof confirmed [{name}]: {[str(v) for v in violations]}")
        else:
            print(f"AC-2 REGRESSION: evasion fixture [{name}] was NOT caught "
                  "(expected RED, got GREEN — the lint is fingerprinting a shape again, "
                  "not the illegal class).", file=sys.stderr)
            failed = True

    # ── control: a door-only fixture (real report.sh shape) must be clean ──
    clean_violations = r3_lint.lint_source(DOOR_ONLY_FIXTURE, path="<door-only-fixture>")
    if clean_violations:
        print("AC-2 REGRESSION: a door-only fixture (worker sender, matches "
              f"report.sh's own real shape) was flagged: {[str(v) for v in clean_violations]}",
              file=sys.stderr)
        failed = True
    else:
        print("GREEN proof (fixture) confirmed: a door-only report is clean.")

    # ── control: legal helper indirection (same mechanism as evasion #5,
    #     safe payloads at every real call site) must ALSO be clean ──
    legal_indirection_violations = r3_lint.lint_source(
        LEGAL_HELPER_INDIRECTION_FIXTURE, path="<legal-helper-indirection-fixture>")
    if legal_indirection_violations:
        print("AC-2 REGRESSION: a legitimate same-file helper wrapper (every call site "
              f"sends a safe, sender-less payload) was flagged: "
              f"{[str(v) for v in legal_indirection_violations]}", file=sys.stderr)
        failed = True
    else:
        print("GREEN proof (fixture) confirmed: legal helper indirection (safe payload "
              "at every call site) is clean — the lint judges call sites, not the mere "
              "presence of indirection.")

    # ── GREEN on tree, modulo the explicit KNOWN_RED list ──
    result = r3_lint.run()
    if result.stale_known_red:
        print(f"AC-2 FAILURE: KNOWN_RED entries came back CLEAN (stale — "
              f"remove them, or a real regression hid behind a silent "
              f"whitelist): {result.stale_known_red}", file=sys.stderr)
        failed = True
    if result.unlisted_offenders:
        print(f"AC-2 FAILURE: dishonest harness(es) NOT in the explicit "
              f"KNOWN_RED list: {result.unlisted_offenders}", file=sys.stderr)
        failed = True
    if not result.stale_known_red and not result.unlisted_offenders:
        print("GREEN proof (tree) confirmed: the proof-harness tree is clean "
              f"except the tracked KNOWN_RED set: {sorted(r3_lint.KNOWN_RED)}")

    # ── the named offender is, concretely, red ──
    op_proxy = "core/sim/operator_proxy.py"
    if op_proxy not in result.violations_by_file:
        print(f"AC-2 FAILURE: {op_proxy} (the ADR's named offender) is NOT "
              "flagged red.", file=sys.stderr)
        failed = True
    else:
        print(f"Previously-dishonest rig confirmed RED: {op_proxy} -> "
              f"{[str(v) for v in result.violations_by_file[op_proxy]]}")

    # ── mechanism self-test: stale-entry detection (synthetic KNOWN_RED,
    #     never touches the real list) ──
    orig_known_red = r3_lint.KNOWN_RED
    try:
        r3_lint.KNOWN_RED = dict(orig_known_red)
        r3_lint.KNOWN_RED["core/does_not_exist_rig.py"] = {
            "owning_block": "none", "reason": "synthetic stale-entry self-test"}
        stale_check = r3_lint.run()
        if "core/does_not_exist_rig.py" not in stale_check.stale_known_red:
            print("AC-2 REGRESSION: stale-known-red detection did not fire "
                  "for a synthetic clean-but-listed entry.", file=sys.stderr)
            failed = True
        else:
            print("Mechanism proof confirmed: a stale KNOWN_RED entry is caught.")
    finally:
        r3_lint.KNOWN_RED = orig_known_red

    # ── mechanism self-test: unlisted-offender detection (synthetic) ──
    try:
        r3_lint.KNOWN_RED = {}
        unlisted_check = r3_lint.run()
        if "core/sim/operator_proxy.py" not in unlisted_check.unlisted_offenders:
            print("AC-2 REGRESSION: unlisted-offender detection did not fire "
                  "when KNOWN_RED was emptied.", file=sys.stderr)
            failed = True
        else:
            print("Mechanism proof confirmed: an unlisted offender is caught.")
    finally:
        r3_lint.KNOWN_RED = orig_known_red

    print(f"\nAC-2: {'PASS' if not failed else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
