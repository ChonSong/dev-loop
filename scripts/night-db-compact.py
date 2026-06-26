#!/usr/bin/env python3
"""Nightly session DB compaction — VACUUM + reindex. Zero-token maintenance."""
import os, time, subprocess, sqlite3

DB = os.path.expanduser("~/.hermes/state.db")
KANBAN_DB = os.path.expanduser("~/.hermes/kanban.db")
LOG = os.path.expanduser("~/.hermes/cron/output/db-maintenance.log")

ts = time.strftime("%Y-%m-%d %H:%M:%S AEST", time.gmtime(time.time() + 36000))
results = []

for label, path in [("state.db", DB), ("kanban.db", KANBAN_DB)]:
    if not os.path.exists(path):
        results.append(f"{label}: not found, skipping")
        continue
    size_before = os.path.getsize(path)
    try:
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("VACUUM")
        # Rebuild FTS index for state.db
        if "state" in label:
            try:
                conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
            except: pass
        conn.close()
        size_after = os.path.getsize(path)
        saved = size_before - size_after
        results.append(
            f"{label}: {size_before/1e6:.1f}MB → {size_after/1e6:.1f}MB "
            f"({saved/1e3:.0f}KB freed)"
        )
    except Exception as e:
        results.append(f"{label}: error — {e}")

with open(LOG, "a") as f:
    f.write(f"[{ts}] {' | '.join(results)}\n")

print("DB MAINTENANCE " + ts)
for r in results:
    print(f"  {r}")
