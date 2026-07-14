#!/usr/bin/env bash
# operator-reply.sh — the operator's REAL inbound channel (ADR-0012 R8, block
# 01-38 T3). A human (or a trusted relay driving the operator's own reply
# surface — e.g. a Telegram bot handler) runs this to settle a parked case:
#
#   operator-reply.sh <case-id> <resume|amend|abandon> ["<note>"]
#
# Writes ONE structured `operator.decision` line to `operator-inbox.jsonl`,
# drained EVERY TICK by `core/snapshot.py::build` (alongside every per-agent
# channel) and resolved through the real door (`core/classify.py` ->
# `core/router.py::_route_decision` -> `core/casestate.py::settle`) — the
# SAME path a real operator's reply travels, never a shortcut. This is the
# ONE legitimate writer of `operator-inbox.jsonl`: no rig may append to it
# in-process (R3; `core/r3_lint.py`'s OPERATOR_INBOX_WRITE rule, enforced
# both statically and at runtime by `core/r3_guard.py`) — a test double that
# needs to act as the operator (e.g. `core/sim/operator_proxy.py`, the
# MODERATE-tier LLM stand-in) runs THIS script as a real subprocess, exactly
# like a human would, never a Python file write of its own.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRON_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INBOX="$TRON_DIR/operator-inbox.jsonl"

usage() {
  echo "usage: operator-reply.sh <case-id> <resume|amend|abandon> [\"<note>\"]" >&2
}

if [ "$#" -lt 2 ]; then
  usage
  exit 2
fi

CASE_ID="$1"
VERB="$2"
NOTE="${3:-}"

case "$VERB" in
  resume|amend|abandon) ;;
  *)
    echo "operator-reply: '$VERB' is not one of resume|amend|abandon" >&2
    usage
    exit 2
    ;;
esac

[ -n "$CASE_ID" ] || { echo "operator-reply: empty case id" >&2; exit 2; }

mkdir -p "$(dirname "$INBOX")"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
jq -cn --arg case_id "$CASE_ID" --arg verb "$VERB" --arg note "$NOTE" --arg at "$TS" \
  '{at:$at, tag:"operator.decision", sender:{kind:"operator", id:"operator"},
    slots: ({case_id:$case_id, verb:$verb} + (if $note != "" then {note:$note} else {} end))}' \
  >> "$INBOX"

echo "operator-reply: recorded $VERB $CASE_ID"
