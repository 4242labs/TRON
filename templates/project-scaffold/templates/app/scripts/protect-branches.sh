#!/usr/bin/env bash
# protect-branches.sh — the operator one-shot that turns on GitHub branch protection.
# The .githooks/ guard stops direct commits LOCALLY; this enforces the same on the REMOTE:
# a protected branch takes only PRs whose required checks are green. Run once per repo by an
# operator/admin (it changes repo settings — an outward, admin act TRON itself never performs).
#
#   Usage:  scripts/protect-branches.sh <owner/repo> [branch ...]
#   e.g.    scripts/protect-branches.sh acme/widgets main staging
#
# Requires: gh (authenticated, admin on the repo). Idempotent — re-running re-asserts the rule.
set -euo pipefail

REPO="${1:?usage: protect-branches.sh <owner/repo> [branch ...]}"; shift || true
BRANCHES=("$@"); [ ${#BRANCHES[@]} -eq 0 ] && BRANCHES=(main staging)

for b in "${BRANCHES[@]}"; do
  echo "protecting ${REPO}@${b} (require PR + green checks, no direct push, no force-push)…"
  gh api -X PUT "repos/${REPO}/branches/${b}/protection" \
    --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": [] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
done

echo "done. Set required_status_checks.contexts to your CI job names to gate on green."
