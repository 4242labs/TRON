#!/usr/bin/env bash
# Every relative .md reference inside modes/ must resolve.
#
# This exists because nothing else in the repo lints modes/ — a dead path to the shared law breaks
# every boot silently, and no test catches it. Run it after touching any mode doc.
#
# Two anchors, and they are not the same:
#   * install/tron-<mode>-command.md refers to things as $MODE_ROOT/... → anchored at the MODE dir
#   * every other file → anchored at the FILE's own directory (plain file-relative)
set -uo pipefail

MODES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$MODES_DIR" || exit 1

FAILED=0

# Deliberately absent at rest: gitignored operator files, and kit files resolved from another root.
expected_absent() {
  case "$(basename "$1")" in
    projects.md|backlog.md|tokens.md) return 0 ;;
    *) return 1 ;;
  esac
}

check() { # $1 = anchor dir, $2 = ref, $3 = source file
  [ -f "$1/$2" ] && return 0
  expected_absent "$2" && return 0
  echo "BROKEN  $3 → $2"
  FAILED=1
}

for file in $(find . -name '*.md' | sort); do
  case "$file" in
    ./*/install/tron-*-command.md)
      # $MODE_ROOT/x → anchor at the mode dir (two levels up from install/)
      mode_dir="$(dirname "$(dirname "$file")")"
      for ref in $(grep -oE '\$[A-Z]+_ROOT/[A-Za-z0-9_./-]+\.md' "$file" | sed 's|^\$[A-Z]*_ROOT/||' | sort -u); do
        check "$mode_dir" "$ref" "$file"
      done
      ;;
    *)
      dir="$(dirname "$file")"
      for ref in $(grep -oE '(\.\./)+[A-Za-z0-9_./-]+\.md' "$file" | sort -u); do
        check "$dir" "$ref" "$file"
      done
      ;;
  esac
done

if [ "$FAILED" -ne 0 ]; then
  echo
  echo "FAIL — the paths above do not resolve."
  echo "  Inside modes/<mode>/skills/ the shared law is ../../shared/tron.md;"
  echo "  a sibling skill is skill-foo.md (no skills/ prefix)."
  exit 1
fi

echo "OK — every relative reference under modes/ resolves."
