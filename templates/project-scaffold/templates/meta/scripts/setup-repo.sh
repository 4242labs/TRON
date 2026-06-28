#!/usr/bin/env bash
# setup-repo.sh — one-time (idempotent) per-clone bootstrap. Activates the canon trunk-root
# guard and portable-worktree settings. Run once after cloning; safe to re-run.
#   - worktree.useRelativePaths=true  -> the workspace tree is movable without `git worktree repair`
#   - the .githooks/ guard            -> direct commits/pushes to a protected branch are refused
# If lefthook owns the hooks (lefthook.yml present), it already invokes .githooks/ — we leave
# core.hooksPath alone so lefthook's other checks keep running. Otherwise we point git at .githooks.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

git config worktree.useRelativePaths true

if [ -d .githooks ]; then
  chmod +x .githooks/* 2>/dev/null || true
  if [ -f lefthook.yml ] || [ -f lefthook.yaml ]; then
    echo "setup-repo: lefthook present — it invokes .githooks/; core.hooksPath left unchanged."
  else
    git config core.hooksPath .githooks
    echo "setup-repo: core.hooksPath -> .githooks (trunk-root guard active)."
  fi
else
  echo "setup-repo: no .githooks/ directory — nothing to activate." >&2
fi

echo "setup-repo: done."
