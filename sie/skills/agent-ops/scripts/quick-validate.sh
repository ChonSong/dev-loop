#!/bin/bash
# quick-validate.sh — pipe JSON through the validator with minimal typing
# Usage:
#   quick-validate.sh <schema>
#   quick-validate.sh <schema> --curl "curl -s -H 'Auth: Bearer xxx' https://api..."
#   cat response.json | quick-validate.sh <schema>

set -e
SCHEMA="${1:?Usage: quick-validate.sh <schema> [curl-cmd]}"
shift

if [ $# -gt 0 ]; then
    # Pass remaining args to validate (e.g., --curl "...")
    python3 /workspace/agent-ops/evidence/validate.py "$SCHEMA" "$@"
else
    # Read from stdin
    python3 /workspace/agent-ops/evidence/validate.py "$SCHEMA"
fi
