#!/usr/bin/env bash
# Gate for Lab 3 (Raft). Mirrors MIT's own `make raft1` recipe: build the
# per-peer daemon binary the tester exec's (src/main/raft1d), then run the
# COURSE-authored test suite src/raft1/raft_test.go verbatim, selecting the
# part(s) to grade with -run. This script is the third-party-oracle wrapper:
# do not edit raft_test.go, test.go, util.go, server.go, proxy.go, or anything
# under raftapi/, labrpc/, labgob/, tester1/.
#
# Usage:  bash run-oracle.sh [PART]
#   PART is one of 3A | 3B | 3C | 3D (default: the full suite, 3A|3B|3C|3D).
#
# Selection is CUMULATIVE by design: block N's gate re-runs every part up to and
# including N, so a later part may never silently regress an earlier one. The
# final block therefore runs MIT's COMPLETE Raft suite. -run is test selection,
# not test authoring: the tests are MIT's, unmodified.
#
# Grade config: MIT grades Raft WITHOUT -race (see LAB.md), so the gate matches
# that. -race is the recommended developer bar and is verified separately, out of
# band, after delivery.
set -e
export PATH="$HOME/.local/go/bin:/usr/local/go/bin:$PATH"

case "${1:-3D}" in
  3A) RUN='3A' ;;
  3B) RUN='3A|3B' ;;
  3C) RUN='3A|3B|3C' ;;
  3D|"") RUN='3A|3B|3C|3D' ;;
  *) echo "unknown part: $1 (want 3A|3B|3C|3D)" >&2; exit 2 ;;
esac

cd "$(dirname "$0")/src"
# The 2026 tester (tester1/daemonclnt.go) runs each simulated Raft peer as a
# separate OS process, exec'ing main/raft1d. MIT's Makefile builds it before
# testing (`raft1-build: go build -o main/raft1d main/raft1d.go`); do the same,
# so a fresh checkout is self-contained (raft1d is gitignored). No -race, to
# match MIT's grade config.
go build -o main/raft1d main/raft1d.go

# -timeout guards against a non-terminating implementation (an un-elected
# cluster would otherwise block on the tester's waits): a hang -> timeout ->
# non-zero -> RED. The suite also exits non-zero on any assertion failure.
cd raft1 && go test -timeout 900s -run "$RUN"
