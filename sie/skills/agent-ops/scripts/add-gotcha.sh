#!/bin/bash
# add-gotcha.sh — interactive gotcha adder
# Prompts for ID, summary, symptom, fix; adds to the named set as provisional.
# Use `gotcha bump <id>` after seeing the same failure again to promote to authoritative.
#
# Usage:
#   add-gotcha.sh <set-name>
#   add-gotcha.sh <set-name> --id <id> --summary "..." --fix "..."

set -e
SET="${1:?Usage: add-gotcha.sh <set-name> [--id X --summary Y --fix Z]}"
shift

# Parse optional named args
ID=""
SUMMARY=""
SYMPTOM=""
FIX=""
while [ $# -gt 0 ]; do
    case "$1" in
        --id) ID="$2"; shift 2 ;;
        --summary) SUMMARY="$2"; shift 2 ;;
        --symptom) SYMPTOM="$2"; shift 2 ;;
        --fix) FIX="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

# Interactive prompts for missing fields
[ -z "$ID" ] && { read -p "Gotcha ID (e.g., $SET-001): " ID; }
[ -z "$SUMMARY" ] && { read -p "One-line summary: " SUMMARY; }
[ -z "$SYMPTOM" ] && { read -p "Symptom (what does the failure look like): " SYMPTOM; }
[ -z "$FIX" ] && { read -p "Fix (one-liner): " FIX; }

if [ -z "$ID" ] || [ -z "$SUMMARY" ]; then
    echo "ID and SUMMARY are required." >&2
    exit 1
fi

python3 /workspace/agent-ops/gotchas/cli.py add "$ID" "$SUMMARY" \
    --symptom "${SYMPTOM:-TBD}" \
    --fix "${FIX:-TBD}" \
    --set "$SET"

echo
echo "Added as PROVISIONAL. Run 'gotcha bump $ID' after seeing this failure again to promote."
