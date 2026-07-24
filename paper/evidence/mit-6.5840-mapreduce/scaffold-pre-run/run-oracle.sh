#!/usr/bin/env bash
# Gate for Lab 1 (MapReduce). Builds the COURSE-PROVIDED apps + main binaries
# (which compile the worker's mr/ code), then runs the COURSE-authored test
# suite src/mr/mr_test.go verbatim. This script and everything it runs are the
# third-party oracle: do not edit it, mr_test.go, or util.go.
set -e
export PATH="$HOME/.local/go/bin:/usr/local/go/bin:$PATH"
cd "$(dirname "$0")/src"
for app in wc indexer mtiming rtiming jobcount early_exit crash nocrash; do
  go build -buildmode=plugin -o "mrapps/$app.so" "mrapps/$app.go"
done
( cd main
  go build -o mrcoordinator mrcoordinator.go
  go build -o mrworker      mrworker.go
  go build -o mrsequential  mrsequential.go )
cd mr && go test -timeout 300s
