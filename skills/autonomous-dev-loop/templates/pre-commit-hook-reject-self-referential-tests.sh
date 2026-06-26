#!/bin/sh
# Pre-commit hook: reject AGENTS.md changes containing "Add E2E test for"
#
# Install: cp this file to .git/hooks/pre-commit and make executable
# This hook prevents the self-referential testing pattern where the Player
# writes a test for code it just implemented (methodology failure).
#
# Installed in:
#   /home/sc/repos/gto-wizard-clone/.git/hooks/pre-commit
#   /home/sc/repos/polytopia-clone/.git/hooks/pre-commit

AGENTS_CHANGED=$(git diff --cached --name-only | grep -i 'AGENTS\.md$')

if [ -n "$AGENTS_CHANGED" ]; then
  echo "$AGENTS_CHANGED" | while read -r file; do
    if git diff --cached "$file" | grep -qE '^\+\s*###\s+Task:\s*.*Add\s+E2E\s+test'; then
      echo "ERROR: Commit rejected — AGENTS.md task describes 'Add E2E test for X' pattern."
      echo "This creates self-referential tests (test validates implementation, not requirement)."
      echo "Rewrite the task to describe the behavior to verify, not the test to write."
      echo "Affected file: $file"
      exit 1
    fi
  done
  # Capture exit code from the pipe — last command's exit, not grep's
  exit $?
fi

exit 0
