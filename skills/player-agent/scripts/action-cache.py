#!/usr/bin/env python3
"""
Action Cache CLI — caches Solution Mapper outputs keyed by (task_type, project, file_glob).

Cache key = sha256(task_type + "::" + project + "::" + primary_file_glob)
Stored in SQLite at sie/knowledge-store/action-cache.db

Commands:
    get         — return cached mapper output (stdout) or exit 1 on miss
    set         — save a cache entry with file hashes {path: sha256}
    invalidate  — remove an entry by key
    stats       — print cache statistics (count, hit rate, size)
    prune       — evict entries older than 7 days or LRU when count > 50
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path.home() / "repos" / "autonomous-dev-system"
KNOWLEDGE_DIR = REPO_ROOT / "sie" / "knowledge-store"
DB_PATH = KNOWLEDGE_DIR / "action-cache.db"

# Limits
MAX_ENTRIES = 50
MAX_AGE_DAYS = 7


# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_db() -> sqlite3.Connection:
    """Open (or create) the cache DB and ensure schema exists."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache_entries (
            key              TEXT PRIMARY KEY,
            task_type        TEXT NOT NULL,
            project          TEXT NOT NULL,
            primary_file_glob TEXT NOT NULL,
            mapper_output    TEXT NOT NULL,
            file_hashes      TEXT NOT NULL,   -- JSON: {path: sha256}
            created_at       TEXT NOT NULL,   -- ISO 8601 UTC
            last_accessed_at TEXT NOT NULL,
            access_count     INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def make_key(task_type: str, project: str, primary_file_glob: str) -> str:
    """Produce a deterministic cache key."""
    raw = f"{task_type}::{project}::{primary_file_glob}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def file_sha256(path: str) -> str:
    """Return the SHA-256 hex digest of a file's contents, or empty string if missing."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except (FileNotFoundError, PermissionError):
        return ""


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_get(args: argparse.Namespace) -> None:
    """Retrieve a cached mapper output by key, verifying file hashes."""
    key = make_key(args.task_type, args.project, args.primary_file_glob)
    conn = ensure_db()
    row = conn.execute(
        "SELECT mapper_output, file_hashes FROM cache_entries WHERE key = ?",
        (key,),
    ).fetchone()

    if row is None:
        conn.close()
        print(f"[action-cache] MISS — no entry for key {key[:12]}…", file=sys.stderr)
        sys.exit(1)

    mapper_output, file_hashes_json = row
    stored_hashes: dict[str, str] = json.loads(file_hashes_json)

    # Verify every stored file still matches its hash
    for fpath, expected_hash in stored_hashes.items():
        current = file_sha256(fpath)
        if current != expected_hash:
            # File changed — invalidate stale entry
            conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            conn.commit()
            conn.close()
            print(
                f"[action-cache] STALE — {fpath} changed, entry invalidated",
                file=sys.stderr,
            )
            sys.exit(1)

    # Update access metadata
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE cache_entries SET last_accessed_at = ?, access_count = access_count + 1 WHERE key = ?",
        (now, key),
    )
    conn.commit()
    conn.close()

    print(f"[action-cache] HIT — key {key[:12]}… ({len(mapper_output)} bytes)", file=sys.stderr)
    # Output the mapper output to stdout for the caller to consume
    sys.stdout.write(mapper_output)


def cmd_set(args: argparse.Namespace) -> None:
    """Save a cache entry."""
    key = make_key(args.task_type, args.project, args.primary_file_glob)
    now = datetime.now(timezone.utc).isoformat()

    # Read mapper output from stdin or --file
    if args.file:
        mapper_output = Path(args.file).read_text()
    else:
        mapper_output = sys.stdin.read()

    # Build file hashes from --hash arguments: path:sha256 pairs
    file_hashes: dict[str, str] = {}
    if args.hash:
        for pair in args.hash:
            parts = pair.split(":", 1)
            if len(parts) == 2:
                file_hashes[parts[0]] = parts[1]

    conn = ensure_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO cache_entries
            (key, task_type, project, primary_file_glob, mapper_output, file_hashes, created_at, last_accessed_at, access_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT access_count FROM cache_entries WHERE key = ?), 0))
        """,
        (key, args.task_type, args.project, args.primary_file_glob,
         mapper_output, json.dumps(file_hashes), now, now, key),
    )
    conn.commit()
    conn.close()
    print(f"[action-cache] SET — key {key[:12]}… ({len(mapper_output)} bytes, {len(file_hashes)} file hashes)", file=sys.stderr)


def cmd_invalidate(args: argparse.Namespace) -> None:
    """Remove a cache entry by key."""
    key = make_key(args.task_type, args.project, args.primary_file_glob)
    conn = ensure_db()
    cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    if cursor.rowcount:
        print(f"[action-cache] INVALIDATED — key {key[:12]}…", file=sys.stderr)
    else:
        print(f"[action-cache] NOT FOUND — key {key[:12]}…", file=sys.stderr)


def cmd_stats(args: argparse.Namespace) -> None:
    """Print cache statistics."""
    conn = ensure_db()
    total = conn.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]
    total_accesses = conn.execute(
        "SELECT COALESCE(SUM(access_count), 0) FROM cache_entries"
    ).fetchone()[0]
    hits = total_accesses
    misses_est = max(0, total_accesses)  # best-effort
    hit_rate = (hits / (hits + misses_est)) * 100 if (hits + misses_est) > 0 else 0.0

    # DB file size
    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0

    # Oldest entry
    oldest = conn.execute("SELECT MIN(created_at) FROM cache_entries").fetchone()[0]
    newest = conn.execute("SELECT MAX(last_accessed_at) FROM cache_entries").fetchone()[0]

    conn.close()

    print(json.dumps({
        "total_entries": total,
        "max_entries": MAX_ENTRIES,
        "total_accesses": total_accesses,
        "hit_rate_pct": round(hit_rate, 1),
        "db_size_bytes": db_size,
        "oldest_entry": oldest,
        "newest_access": newest,
    }, indent=2))


def cmd_prune(args: argparse.Namespace) -> None:
    """Evict entries older than MAX_AGE_DAYS, then evict LRU if count > MAX_ENTRIES."""
    conn = ensure_db()
    removed = 0

    # 1. Remove entries older than 7 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).isoformat()
    cursor = conn.execute("DELETE FROM cache_entries WHERE created_at < ?", (cutoff,))
    removed += cursor.rowcount

    # 2. If still over max, evict least-recently-accessed
    count = conn.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]
    if count > MAX_ENTRIES:
        excess = count - MAX_ENTRIES
        # Find the keys with the oldest last_accessed_at
        rows = conn.execute(
            "SELECT key FROM cache_entries ORDER BY last_accessed_at ASC LIMIT ?",
            (excess,),
        ).fetchall()
        for (key,) in rows:
            conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            removed += 1

    conn.commit()
    conn.close()
    print(f"[action-cache] PRUNE — {removed} entries evicted", file=sys.stderr)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Action Cache — cache Solution Mapper outputs by task signature",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- get ---
    p_get = sub.add_parser("get", help="Retrieve cached mapper output")
    p_get.add_argument("--task-type", required=True, help="e.g. fix-layout, add-feature")
    p_get.add_argument("--project", required=True, help="Project name")
    p_get.add_argument("--primary-file-glob", required=True, help="Primary file glob pattern")
    p_get.set_defaults(func=cmd_get)

    # --- set ---
    p_set = sub.add_parser("set", help="Save a cache entry")
    p_set.add_argument("--task-type", required=True)
    p_set.add_argument("--project", required=True)
    p_set.add_argument("--primary-file-glob", required=True)
    p_set.add_argument("--file", default=None, help="Read mapper output from file (default: stdin)")
    p_set.add_argument("--hash", action="append", default=None,
                       help="File hash as path:sha256 (repeatable)")
    p_set.set_defaults(func=cmd_set)

    # --- invalidate ---
    p_inv = sub.add_parser("invalidate", help="Remove a cache entry")
    p_inv.add_argument("--task-type", required=True)
    p_inv.add_argument("--project", required=True)
    p_inv.add_argument("--primary-file-glob", required=True)
    p_inv.set_defaults(func=cmd_invalidate)

    # --- stats ---
    p_stats = sub.add_parser("stats", help="Print cache statistics")
    p_stats.set_defaults(func=cmd_stats)

    # --- prune ---
    p_prune = sub.add_parser("prune", help="Evict old / excess entries")
    p_prune.set_defaults(func=cmd_prune)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
