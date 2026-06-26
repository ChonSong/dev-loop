#!/bin/bash
# validate-api — validate JSON against a schema before parsing
# Usage:
#   validate-api <schema-name> < input.json
#   validate-api <schema-name> --curl "curl -s -H 'Auth: Bearer xxx' URL"
#   validate-api <schema-name> --url URL --auth "Bearer xxx"
#   validate-api --list
#   validate-api --self-test
#
# Schemas live in ../evidence/schemas/. Run --list to see available.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATE="$SCRIPT_DIR/../evidence/validate.py"

if [ ! -f "$VALIDATE" ]; then
    echo "validate.py not found at $VALIDATE" >&2
    exit 1
fi

exec python3 "$VALIDATE" "$@"
