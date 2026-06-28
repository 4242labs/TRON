#!/usr/bin/env bash
# hook_test.sh — proves the trunk-root guard (AC-4): direct commits/pushes to a protected
# branch are refused; a feature-branch merge passes. Self-contained, token-free, no network
# (the "remote" is a local bare repo). Exits 0 only if every assertion holds.
set -uo pipefail

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP="$(cd "$HOOKS_DIR/../scripts" && pwd)/setup-repo.sh"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
pass=0; fail=0
chk() { if [ "$1" = "$2" ]; then echo "  [PASS] $3"; pass=$((pass+1)); else echo "  [FAIL] $3 (want=$2 got=$1)"; fail=$((fail+1)); fi; }

cd "$tmp"
git init -q --bare remote.git
git init -q -b main work && cd work
git config user.email t@t && git config user.name t
git remote add origin "$tmp/remote.git"

# seed an initial main BEFORE the guard is active (real repos predate the hook install).
echo seed > seed.txt && git add seed.txt && git commit -qm "chore: seed main"

mkdir -p .githooks scripts
cp "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/pre-push" .githooks/
chmod +x .githooks/*
bash "$SETUP" >/dev/null

# a feature-branch merge into main is allowed (a merge fires pre-merge-commit, not pre-commit).
git checkout -q -b seed && echo a > a.txt && git add a.txt && git commit -qm "feat: a"
git checkout -q main && git merge -q --no-ff seed -m "merge seed" 2>/dev/null
chk "$?" "0" "feature-branch merge into main is allowed"

# direct commit on main -> REFUSED by pre-commit.
echo b > b.txt && git add b.txt
git commit -qm "direct on main" 2>/dev/null
chk "$?" "1" "direct commit on protected branch (main) is refused"

# direct commit on a feature branch -> allowed.
git checkout -q -b feat/x
echo c > c.txt && git add c.txt && git commit -qm "feat: x" 2>/dev/null
chk "$?" "0" "commit on a feature branch is allowed"

# push the feature branch (non-protected ref) -> allowed by pre-push.
git push -q origin feat/x 2>/dev/null
chk "$?" "0" "pushing a feature branch is allowed"

# establish remote main from pre-guard history (the initial push predates protection).
git checkout -q main
git push -q --no-verify origin main 2>/dev/null
chk "$?" "0" "initial main push (pre-guard history) succeeds"

# a direct-on-trunk commit (snuck in past pre-commit with --no-verify) -> refused on PUSH.
echo d > d.txt && git add d.txt && git commit -q --no-verify -m "sneaky direct on main"
git push -q origin main 2>/dev/null
chk "$?" "1" "direct-to-trunk commit refused on push (pre-push backstop)"

# drop the sneak; a proper feature-branch merge pushes to trunk fine.
git reset -q --hard origin/main
git checkout -q -b feat/y && echo e > e.txt && git add e.txt && git commit -qm "feat: y"
git checkout -q main && git merge -q --no-ff feat/y -m "merge feat/y"
git push -q origin main 2>/dev/null
chk "$?" "0" "feature-branch merge pushes to trunk fine"

echo "hook_test: $([ $fail -eq 0 ] && echo PASS || echo FAIL) ($pass/$((pass+fail)))"
[ $fail -eq 0 ]
