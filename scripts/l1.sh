#!/usr/bin/env bash
# l1.sh — block 01-40 T1 (ADR-0012 §3 P1): the ONE command that discovers and
# runs every mutation-proof rig under core/ — glob-based (core/*_rig.py +
# core/sim/*_rig.py), never a hand-maintained list, so a newly added rig is
# picked up here with zero code edits. This is the CI L1 gate (~2 min budget).
# Paired with the R3 honesty lint (core/r3_lint.py, wired as its own CI step) —
# a rig that lies is worthless to run fast.
#
# RUNTIME WRITE-GUARD (Opus-pivot item 1, ruling-independent half): every rig
# below runs with core/r3_guard.py's sys.addaudithook installed via a
# sitecustomize.py directory prepended to PYTHONPATH (see materialize_site_dir
# in core/r3_guard.py — never PYTHONSTARTUP, which does not fire for
# scripts). THIS SCRIPT IS THE ONLY PLACE THE PROTECTED-PATH POLICY LIVES —
# core/r3_guard.py itself hardcodes no path. Today that policy is
# operator-inbox.jsonl only: R8 (ADR-0012 §2) already forbids ANY rig from
# writing it, under any circumstance, so blanket-protecting it can never
# legitimately trip a rig. worker-inbox.jsonl is NOT in R3_GUARD_PROTECT
# because block 01-38 T1 already DELETED the legacy shared drop-box from the
# live core/ path entirely (the root invariant — no core/*.py reader is left
# for a guard to defend; mutation-proven by core/hostile_minter_rig.py's
# drop-box-removed assertion) — not because a ruling is outstanding. R3
# MODEL A (route every rig through the real door) is the operator-approved
# model as of 2026-07-14 (blocks/01-38-the-engine-close.md's binding-rules
# section); this is settled, not pending. If the frozen legacy engine/fsm.py
# path (out of core/'s scope) ever needs the SAME runtime protection for its
# own worker-inbox.jsonl, that is a ONE-LINE change to R3_GUARD_PROTECT below
# — never a code change here.
#
# A rig's own instance dir is minted at RUNTIME (tempfile.mkdtemp(), a random
# suffix this script can't predict) — TMPDIR is pointed at a fresh sandbox for
# the whole run so every rig's instance dir lands under one known root, and
# R3_GUARD_PROTECT carries a GLOB (fnmatch's `*` matches across path
# separators too) that covers any depth/suffix under it — the
# "protected-DIRECTORY prefix match" unit-style rigs need without this script
# ever having to know an individual rig's directory-naming scheme.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

R3_SANDBOX="$(mktemp -d)"
R3_SITE_DIR="$(mktemp -d)"
cleanup() { rm -rf "$R3_SANDBOX" "$R3_SITE_DIR"; }
trap cleanup EXIT

python3 core/r3_guard.py --write-site-dir "$R3_SITE_DIR" >/dev/null

export TMPDIR="$R3_SANDBOX"
export PYTHONPATH="$R3_SITE_DIR${PYTHONPATH:+:$PYTHONPATH}"
export R3_GUARD_PROTECT="$R3_SANDBOX"'/*operator-inbox.jsonl'

shopt -s nullglob
rigs=(core/*_rig.py core/sim/*_rig.py)
if [ "${#rigs[@]}" -eq 0 ]; then
  echo "l1.sh: no rigs discovered under core/*_rig.py or core/sim/*_rig.py — that's a broken glob, not an empty proof suite." >&2
  exit 1
fi

fail=0
pass_n=0
echo "l1.sh: discovered ${#rigs[@]} rig(s)"
echo "l1.sh: runtime write-guard active — protecting: $R3_GUARD_PROTECT"
for r in "${rigs[@]}"; do
  echo "::group::$r"
  if R3_GUARD_RIG="$r" python3 "$r"; then
    pass_n=$((pass_n + 1))
  else
    echo "FAILED: $r"
    fail=1
  fi
  echo "::endgroup::"
done

echo "l1.sh: ${pass_n}/${#rigs[@]} rig(s) passed"
exit $fail
