#!/bin/bash
# show-context-gotchas — auto-detect context and show relevant gotchas
# Usage:
#   show-context-gotchas                    # auto-detect from cwd
#   show-context-gotchas <file_or_dir>      # show gotchas for that path
#   show-context-gotchas --topic <name>     # show specific gotcha set
#   show-context-gotchas --all              # include provisional gotchas
#
# This is the entry point most sessions should use. It infers context
# (current directory, file argument, recent commands) and asks the
# gotcha system what applies.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GOTCHA="$SCRIPT_DIR/../gotchas/cli.py"

if [ ! -f "$GOTCHA" ]; then
    echo "gotcha CLI not found at $GOTCHA" >&2
    exit 1
fi

TOPIC=""
INCLUDE_PROVISIONAL=""
TARGET=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --topic)
            TOPIC="$2"
            shift 2
            ;;
        --all)
            INCLUDE_PROVISIONAL="--all"
            shift
            ;;
        --help|-h)
            head -10 "$0"
            exit 0
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

# If a topic was given, use it directly
if [ -n "$TOPIC" ]; then
    exec python3 "$GOTCHA" show "$TOPIC" $INCLUDE_PROVISIONAL
fi

# If a file/dir was given, use it as context
if [ -n "$TARGET" ]; then
    exec python3 "$GOTCHA" show --file "$TARGET" $INCLUDE_PROVISIONAL
fi

# Default: auto-detect from cwd + any recent .py files in the path
ARGS=(--cwd "$PWD")

# Add any related files we can find
for pattern in "*.py" "*.js" "*.ts" "*.go" "*.json" "*.yaml" "*.yml"; do
    while IFS= read -r f; do
        ARGS+=(--file "$f")
    done < <(find . -maxdepth 2 -name "$pattern" -not -path '*/node_modules/*' -not -path '*/.venv/*' 2>/dev/null | head -3)
done

exec python3 "$GOTCHA" show "${ARGS[@]}" $INCLUDE_PROVISIONAL
