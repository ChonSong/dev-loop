#!/bin/bash
# session-gotcha-load.sh — smart session-startup gotcha loader
# Detects cwd, recent commands from history, and surfaces relevant gotchas.
# Designed to be the first thing called when starting a non-trivial task.
#
# Usage:
#   session-gotcha-load.sh                       # auto-detect from cwd
#   session-gotcha-load.sh /path/to/workspace    # explicit workspace
#   session-gotcha-load.sh --quiet                # exit cleanly, no output
#   session-gotcha-load.sh --json                 # machine-readable

set -e
GOTCHA_ROOT="/workspace/agent-ops"
WORKSPACE="${1:-$PWD}"

# If first arg is a flag, treat cwd as PWD
case "$WORKSPACE" in
    --*) WORKSPACE="$PWD" ;;
esac

# Try to extract recent commands from shell history
EXTRA_COMMANDS=""
if [ -f "$HOME/.bash_history" ]; then
    EXTRA_COMMANDS=$(tail -50 "$HOME/.bash_history" | grep -v "^#" | head -10)
fi

# Call gotcha show with cwd + recent commands as context
if [ "$1" = "--json" ] || [ "$2" = "--json" ]; then
    python3 "$GOTCHA_ROOT/gotchas/cli.py" show --cwd "$WORKSPACE" --json
elif [ "$1" = "--quiet" ] || [ "$2" = "--quiet" ]; then
    python3 "$GOTCHA_ROOT/gotchas/cli.py" show --cwd "$WORKSPACE" --quiet 2>/dev/null || true
else
    echo "[session-gotcha-load] Checking for relevant gotchas in $WORKSPACE..."
    echo
    python3 "$GOTCHA_ROOT/gotchas/cli.py" show --cwd "$WORKSPACE" --verbose
fi
