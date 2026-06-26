#!/bin/bash
# Daily Hermes backup via hbackup
set -e
. "$HOME/.cargo/env"
OUTDIR="$HOME/hermes-backups"
mkdir -p "$OUTDIR"
OUTFILE="$OUTDIR/hbackup-$(date +%Y%m%d-%H%M%S).tar.zst"
"$HOME/.local/bin/hbackup" backup -o "$OUTFILE"
# Keep only the 2 most recent backups (permanent/ excluded by pattern)
ls -t "$OUTDIR"/hbackup-*.tar.zst 2>/dev/null | tail -n +3 | xargs -r rm
echo "Backup complete: $OUTFILE"
