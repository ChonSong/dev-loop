#!/bin/bash
# Refresh the seans-reporepo catalog
set -e

REPO_DIR="/home/sean/.hermes/cache/seans-reporepo"
SCRIPT_DIR="/home/sean/.hermes/scripts"

cd "$REPO_DIR" || { echo "Repo not found at $REPO_DIR"; exit 1; }

# Pull latest
git pull origin main 2>/dev/null || true

# Run the catalog generation script
python3 "$SCRIPT_DIR/generate-catalog.py" "$REPO_DIR"

# Commit and push if changes
cd "$REPO_DIR"
git add -A
if git diff --cached --quiet; then
    echo "No changes to commit."
else
    git commit -m "Auto-refresh: $(date '+%Y-%m-%d %H:%M UTC')"
    git push
    echo "Catalog updated and pushed."
fi
