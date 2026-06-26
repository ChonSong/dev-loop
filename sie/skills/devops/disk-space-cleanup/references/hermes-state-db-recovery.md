# Hermes State DB Recovery

When a Hermes session becomes unresponsive (prompts fail immediately, no response generated), the root cause is often a bloated or corrupted `state.db` caused by disk space exhaustion.

## Core Insight: FTS Index Bloat

The SQLite FTS5 full-text search index is the primary space consumer. Raw message text averages ~1KB per message, but the FTS token-position index creates ~10x overhead:

```
Raw message content (157K msgs):   163MB
DB file on disk:                   1.9GB   (11.7x)
FTS index + metadata overhead:     ~1.7GB  (the rest)
```

This matters because:
- FTS indexes are rebuilt on VACUUM — if VACUUM never runs, they fragment forever
- Each `content`, `tool_calls`, `reasoning_content`, and `reasoning_details` field is FTS-tokenized
- Session rows are tiny — most of the bloat is FTS, not message content
- 56K rows have `reasoning` content, 60K have `reasoning_content`, 38K have `reasoning_details` — these are all FTS-indexed

## Symptoms

- Prompts submitted in a session return instantly with no response or an error
- SQLite queries against `state.db` time out (>30s for simple queries)
- `PRAGMA integrity_check` or `PRAGMA quick_check` times out
- High disk usage (>92%) alongside a 1-2GB+ `state.db`
- System load >5.0, swap usage 3GB+, zombie hermes processes accumulating

## Diagnosis Sequence

### 1. Check Disk Space
```bash
df -h /          # overall usage
```

### 2. Check State DB Size
```bash
ls -lh ~/.hermes/state.db
```

### 3. Check Session Count
```bash
sqlite3 ~/.hermes/state.db 'SELECT source, COUNT(*) FROM sessions GROUP BY source;'
```

### 4. Check DB Integrity
```bash
sqlite3 ~/.hermes/state.db 'PRAGMA quick_check;'    # fast check
sqlite3 ~/.hermes/state.db 'PRAGMA integrity_check;' # thorough check (may be slow)
```
If either times out (>60s), the DB is severely fragmented or corrupted.

### 5. Identify Bloat Sources

```bash
# Sessions by source
sqlite3 ~/.hermes/state.db 'SELECT source, COUNT(*) as cnt, SUM(message_count) as msgs FROM sessions GROUP BY source ORDER BY msgs DESC;'

# Largest sessions (by message count)
sqlite3 ~/.hermes/state.db 'SELECT id, source, message_count, started_at FROM sessions ORDER BY message_count DESC LIMIT 10;'
```

Cron jobs and long-running webui sessions are the top contributors.

### 5. Session Age Distribution Analysis

Understanding the age profile helps decide what's safe to prune:

```bash
# Sessions by age range
sqlite3 ~/.hermes/state.db '
SELECT '< 7 days' as age, COUNT(*) as sessions, SUM(message_count) as msgs
FROM sessions WHERE started_at > strftime('%s','now','-7 days')
UNION ALL
SELECT '7-30 days', COUNT(*), SUM(message_count)
FROM sessions WHERE started_at > strftime('%s','now','-30 days')
  AND started_at <= strftime('%s','now','-7 days')
UNION ALL
SELECT '30-60 days', COUNT(*), SUM(message_count)
FROM sessions WHERE started_at > strftime('%s','now','-60 days')
  AND started_at <= strftime('%s','now','-30 days')
UNION ALL
SELECT '> 60 days', COUNT(*), SUM(message_count)
FROM sessions WHERE started_at <= strftime('%s','now','-60 days');'

# Sessions by message count (find empty/abandoned sessions)
sqlite3 ~/.hermes/state.db '
SELECT message_count, COUNT(*) as sessions
FROM sessions GROUP BY message_count ORDER BY message_count ASC LIMIT 15;'
```

A large number of 0-1 message sessions (1,649 in a 3,600-session DB) indicates tab leaks or abandoned sessions consuming DB pages for no value.

### 6. FTS Index Size Diagnosis

Compare raw content size to DB file size to quantify FTS bloat:

```bash
# Raw message content size
sqlite3 ~/.hermes/state.db 'SELECT ROUND(SUM(LENGTH(CAST(content AS BLOB)))/1048576.0, 1) || " MB" FROM messages;'

# DB file size
ls -lh ~/.hermes/state.db

# Column-wise content breakdown
sqlite3 ~/.hermes/state.db '
SELECT COUNT(*) as rows_with_reasoning FROM messages WHERE reasoning IS NOT NULL AND LENGTH(reasoning) > 0;
SELECT COUNT(*) as rows_with_reasoning_content FROM messages WHERE reasoning_content IS NOT NULL AND LENGTH(reasoning_content) > 0;
SELECT COUNT(*) as has_tool_calls FROM messages WHERE tool_calls IS NOT NULL AND LENGTH(tool_calls) > 0;
SELECT COUNT(*) as has_reasoning_details FROM messages WHERE reasoning_details IS NOT NULL AND LENGTH(reasoning_details) > 0;'
```

Ratio > 5x (e.g., 163MB content → 1.9GB DB → 11.7x) means VACUUM is overdue.

### 7. Empty Session Tab Leak Detection

WebUI sessions with 0 messages are usually leaked tabs — session creation triggered by page reloads or connection recovery loops. Find them:

```bash
# Count empty webui sessions by day
sqlite3 ~/.hermes/state.db '
SELECT date(datetime(started_at, "unixepoch")) as day, COUNT(*) as zero_msg_sessions
FROM sessions WHERE source="webui" AND message_count = 0
GROUP BY day ORDER BY zero_msg_sessions DESC LIMIT 10;'

# Check timing pattern — close-together timestamps indicate programmatic creation
sqlite3 ~/.hermes/state.db '
SELECT datetime(started_at, "unixepoch"), id FROM sessions
WHERE source="webui" AND message_count = 0
ORDER BY started_at ASC LIMIT 30;'
```

**Leak patterns:**
- Sessions with 30s-2min spacing → automatic refresh/reconnect loop
- 400+ sessions in one day → page refresh storm or WebSocket reconnect bug
- IDs with timestamp prefix (`20260526_020411_a9ae89`) — generated by webui on initial connection

**Server-side cause**: The boot flow at `boot.js:1176` calls `await newSession()` when no session is restored on page load. The soft recovery path (`ui.js:123-131`) tries to reconnect without reload, but if it fails, it falls back to `window.location.reload()` which starts the cycle over.

**Frontend trace path (for debugging):**
- `sessions.js:579` — `newSession()` function — POSTs to `/api/session/new`
- `sessions.js:658` — sets `S.session` from API response
- `messages.js:694, 768, 789, 797, 812, 828` — calls `newSession()` when `!S.session`
- `boot.js:1176` — boot path creates session if none restored
- `boot.js:2017` — boot path creates session from PWA launch action
- `ui.js:131` — hard reload fallback when soft recovery fails

### 8. Session Lifecycle Memory Leak

Found in `api/session_lifecycle.py` (documented in the code itself):

> "The `_sessions` dict is process-global and historically only ever grew: `register_agent` / `mark_turn_completed` insert keys but no runtime path ever removed them, so every unique session_id the WebUI touched leaked a"

Every session the webui touches adds an in-memory dictionary entry that never shrinks. This is a process-level memory leak that compounds with the tab leak. Monitoring `_sessions` dict growth can catch tab leaks early.

```
# Does a simple SELECT on a specific session take too long?
sqlite3 ~/.hermes/state.db 'SELECT COUNT(*) FROM messages WHERE session_id="<session_id>";'
```

If >5s, the DB is the bottleneck.

## Recovery Options

### Option A: Prune Old Sessions (Lowest Risk)

Recommended clean-up sequence, run in this order:

**1. Backup first:**
```bash
cp ~/.hermes/state.db ~/.hermes/state.db.bak
```

**2. Delete 0-message sessions** (tab leaks, empty shell sessions — no content to lose):
```bash
sqlite3 ~/.hermes/state.db "DELETE FROM messages WHERE session_id IN
  (SELECT id FROM sessions WHERE message_count = 0);"
sqlite3 ~/.hermes/state.db "DELETE FROM sessions WHERE message_count = 0;"
```

**3. Delete watchdog/specific cron job by pattern** (e.g., GTO Watchdog):
```bash
# Identify watchdog job ID pattern first
sqlite3 ~/.hermes/state.db "SELECT substr(id, 6, 12) as job_id, COUNT(*) as runs,
  SUM(message_count) as msgs FROM sessions WHERE source='cron' AND id LIKE 'cron_%'
  AND title IS NOT NULL GROUP BY job_id ORDER BY runs DESC;"

# Delete by job ID prefix
sqlite3 ~/.hermes/state.db "DELETE FROM messages WHERE session_id IN
  (SELECT id FROM sessions WHERE source='cron' AND id LIKE 'cron_JOB_ID_PREFIX%');"
sqlite3 ~/.hermes/state.db "DELETE FROM sessions WHERE source='cron' AND id LIKE 'cron_JOB_ID_PREFIX%';"
```

**4. Delete 1-message sessions** (abandoned/errored starts):
```bash
sqlite3 ~/.hermes/state.db "DELETE FROM messages WHERE session_id IN
  (SELECT id FROM sessions WHERE message_count = 1);"
sqlite3 ~/.hermes/state.db "DELETE FROM sessions WHERE message_count = 1;"
```

**5. Delete low-value untitled cron sessions** (runs with few messages and no title):
```bash
sqlite3 ~/.hermes/state.db "DELETE FROM messages WHERE session_id IN
  (SELECT id FROM sessions WHERE source='cron' AND message_count < 5
   AND (title IS NULL OR title = ''));"
sqlite3 ~/.hermes/state.db "DELETE FROM sessions WHERE source='cron'
   AND message_count < 5 AND (title IS NULL OR title = '');"
```

**6. Rebuild FTS index then VACUUM** (reclaims space from deleted FTS entries):
```bash
sqlite3 ~/.hermes/state.db "INSERT INTO messages_fts(messages_fts) VALUES('rebuild');"
sqlite3 ~/.hermes/state.db "VACUUM;"
```

The FTS rebuild step is critical — without it, VACUUM can't reclaim FTS index pages from deleted rows.

**7. Verify:**
```bash
sqlite3 ~/.hermes/state.db 'SELECT source, COUNT(*) as sessions, SUM(message_count) as msgs FROM sessions GROUP BY source;'
ls -lh ~/.hermes/state.db
```

**Old content from here onwards remains:**

### Option B: VACUUM Only (When DB is Bloated but Not Corrupted)

If disk space is the only issue (DB operations work, just slow):
```bash
sqlite3 ~/.hermes/state.db 'VACUUM;'
```

VACUUM rebuilds the entire DB file, reclaiming space from deleted rows and defragmenting indexes. Can reduce a 1.9GB DB to 200-400MB.

**VACUUM may fail if:**
- Disk is too full (needs free space equal to ~1.5x the DB size)
- DB has corrupted pages (run `PRAGMA quick_check` first)

### Option C: Dump and Recreate (When VACUUM Fails)

```bash
# Dump schema and data to SQL script
sqlite3 ~/.hermes/state.db '.dump' > /tmp/state-dump.sql

# Create a fresh DB from the dump
sqlite3 ~/.hermes/state.db.new < /tmp/state-dump.sql

# Swap
mv ~/.hermes/state.db ~/.hermes/state.db.bak2
mv ~/.hermes/state.db.new ~/.hermes/state.db
```

This works around corruption and fragmentation issues but preserves all data.

### Option D: Restore from Sync DB (Last Resort)

The hermes-sync `state.db` is a 270MB+ partial backup (depends on sync timing):
```bash
cp ~/.hermes/hermes-sync/state.db ~/.hermes/state.db
```
**Will lose sessions newer than the sync copy's last update.**

## Prevention

### Enable Auto-Prune (Single Most Important Config)

The config `sessions.auto_prune: false` is the root cause of DB bloat. Change it:

```yaml
# config.yaml
sessions:
  auto_prune: true           # ← enable automatic cleanup
  retention_days: 30         # keep last 30 days (adjust as needed)
  min_interval_hours: 24     # how often to check
  vacuum_after_prune: true   # reclaim disk after each prune cycle
```

Without this, no sessions are ever cleaned up — even with `retention_days` and `vacuum_after_prune` defined.

### Regular Session Pruning (Manual Fallback)

If auto-prune can't be enabled, set up a weekly cron job:
```yaml
# config.yaml
sessions:
  auto_prune: true
  retention_days: 30
```

Or set up a weekly cron job:
```python
cronjob(action='create',
  name='prune-old-sessions',
  schedule='0 3 * * 0',     # Sunday 3am
  prompt="Prune sessions from state.db older than 30 days for all sources. Delete from messages and sessions tables. Then VACUUM.",
  enabled_toolsets=['terminal'])
```

### Disk Space Monitoring

- Set a cron alert at 85% disk usage
- Track `state.db` size — if it exceeds 500MB, prune
- Review session retention policy: cron jobs can be pruned aggressively (7-14 days), webui sessions more conservatively (60-90 days)

## Common Pitfalls

- **VACUUM on a full disk fails silently** — free 2x the DB size before attempting
- **Deleting messages without deleting the session row** — orphaned session references remain in FTS tables
- **Pruning active sessions** — don't prune sessions the user is actively using (check `ended_at IS NULL`)
- **Running VACUUM during active use** — VACUUM locks the DB; do it during low-usage hours
- **Restoring from sync DB loses recent data** — always try Option A or C first
