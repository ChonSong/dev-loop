#!/usr/bin/env python3
"""
Rotate cron output directories for coach, player, and polytopia loops.
Keeps last 30 days of output files. Run as no_agent cron job.
"""
import os
import time
from pathlib import Path

DIRS = [
    "/home/sc/.hermes/cron/output/5e1bba516d87",  # coach-development-loop
    "/home/sc/.hermes/cron/output/b4f35d68ede1",  # player-development-loop
    "/home/sc/.hermes/cron/output/752d51adb96d",  # Polytopia deploy loop
]

CUTOFF = time.time() - (30 * 86400)  # 30 days ago

total_removed = 0
total_freed = 0

for dirpath in DIRS:
    d = Path(dirpath)
    if not d.exists():
        continue
    removed = 0
    freed = 0
    for f in d.iterdir():
        if f.is_file():
            mtime = f.stat().st_mtime
            if mtime < CUTOFF:
                size = f.stat().st_size
                try:
                    f.unlink()
                    removed += 1
                    freed += size
                except OSError:
                    pass
    total_removed += removed
    total_freed += freed
    if removed:
        print(f"  {d.name}: removed {removed} files, freed {freed/1024/1024:.1f} MB")

if total_removed == 0:
    print("  Nothing to rotate")
else:
    print(f"  Total: removed {total_removed} files, freed {total_freed/1024/1024:.1f} MB")
