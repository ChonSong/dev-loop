#!/bin/bash
# commit-gate — run the pre-commit gate before committing
# Usage:
#   commit-gate                          # full check (syntax + secrets + tests + diff)
#   commit-gate --diff-only              # skip tests (fast pre-commit)
#   commit-gate --no-tests --no-secrets  # minimal check
#   commit-gate --install                # install as git pre-commit hook
#
# Exit codes:
#   0 = safe to commit
#   1 = issues found, commit blocked
#   2 = not in a git repo or no staged changes

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="$SCRIPT_DIR/../enforcement/pre-commit-gate.py"

if [ ! -f "$GATE" ]; then
    echo "pre-commit-gate.py not found at $GATE" >&2
    exit 1
fi

exec python3 "$GATE" "$@"
