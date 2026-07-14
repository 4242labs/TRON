#!/usr/bin/env python3
"""vocab_lint_check.py — block 01-37 (ADR-0012 R1/R2, T2/T5) CI proof.

Two independent RED/GREEN gates, mirroring `content_field_lint_check.py`'s
own shape:

  T5/AC-6  the emit-id lint (`engine/lint.py::emit_id_lint`): a literal
           string at a `.emit(` call site, in a throwaway fixture file,
           MUST be caught (RED); the real `core/*.py` tree MUST currently
           be clean (GREEN).
  T2/AC-2  the schema regen/diff gate (`core/vocab.py::schema_diff`): a
           `vocab.schema.json` seeded with drift (hand-edited, or stale
           against the live `core/vocab.py`) MUST be caught (RED); the
           repo-root committed `vocab.schema.json` MUST currently match a
           fresh regen (GREEN) — that is what keeps it "generated, never
           hand-committed" honest: CI regenerates and diffs it every run.

Exit 0 only if all four checks land as expected.
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "engine"))

# `lint` FIRST — its own `from fsm import TABLE, Engine` needs `engine/`'s
# bare `state`/`gitobs`/... modules to resolve BEFORE `core/` ever lands on
# sys.path (see `core/vocab.py`'s own module docstring on this exact
# cross-engine collision). `lint.py` loads `core/vocab.py` itself via
# `importlib.util.spec_from_file_location` — no path pollution.
import lint    # noqa: E402 — engine/lint.py

sys.path.insert(0, os.path.join(ROOT, "core"))
import vocab   # noqa: E402 — core/vocab.py


def check_emit_id_lint():
    failed = False
    with tempfile.TemporaryDirectory(prefix="tron-ci-vocab-lint-") as d:
        fixture = os.path.join(d, "fixture.py")
        with open(fixture, "w", encoding="utf-8") as fh:
            fh.write('eng.emit("literal.template.id", "fallback", worker_id=wid)\n')
        red_ok, red_violations = lint.emit_id_lint([fixture])
        if red_ok:
            print("T5/AC-6 REGRESSION: the seeded literal emit-id was NOT caught "
                  "(expected RED, got GREEN).", file=sys.stderr)
            failed = True
        else:
            print(f"T5/AC-6 RED proof confirmed: {red_violations}")

    green_ok, green_violations = lint.emit_id_lint(lint._core_source_files())
    if not green_ok:
        print(f"T5/AC-6 FAILURE: the real core/ tree has literal emit-id call "
              f"sites: {green_violations}", file=sys.stderr)
        failed = True
    else:
        print("T5/AC-6 GREEN proof confirmed: core/ tree is clean.")
    return failed


def check_schema_drift():
    failed = False
    with tempfile.TemporaryDirectory(prefix="tron-ci-vocab-schema-") as d:
        fixture = os.path.join(d, "vocab.schema.json")
        drifted = json.loads(vocab.schema_json())
        drifted["version"] = "DRIFTED-" + str(drifted["version"])
        with open(fixture, "w") as fh:
            json.dump(drifted, fh, indent=2, sort_keys=True)
            fh.write("\n")
        red_ok, red_detail = vocab.schema_diff(fixture)
        if red_ok:
            print("T2/AC-2 REGRESSION: a seeded schema drift was NOT caught "
                  "(expected RED, got GREEN).", file=sys.stderr)
            failed = True
        else:
            print(f"T2/AC-2 RED proof confirmed: {red_detail}")

    live_schema = os.path.join(ROOT, "vocab.schema.json")
    green_ok, green_detail = vocab.schema_diff(live_schema)
    if not green_ok:
        print(f"T2/AC-2 FAILURE: the committed {live_schema} has drifted from "
              f"a fresh regen of core/vocab.py: {green_detail}", file=sys.stderr)
        failed = True
    else:
        print("T2/AC-2 GREEN proof confirmed: committed vocab.schema.json matches "
              "a fresh regen.")
    return failed


def main():
    failed = check_emit_id_lint()
    failed = check_schema_drift() or failed
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
