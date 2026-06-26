# Hermes Session DB Diagnostics

Diagnosing why Hermes is slow, prompts drop immediately, or sessions won't load. The DB is SQLite at `~/.hermes/state.db` and the most common failure mode is **disk full + no auto-prune**.

## Investigation sequence (do this before deleting anything)

### 1. Check disk and DB health

```bash
df -h /                    # is disk nearly full? (97%+ is critical)
ls -lh ~/.hermes/state.db  # how big is the DB? (1.9GB is too big)
sqlite3 ~/.hermes/state.db 'PRAGMA quick_check;'
# If this times out (>60s) the DB is fragmented or corrupted
```

### 2. Check session config

```bash
cat ~/.hermes/home/.hermes/config.yaml | grep -A 5 '^sessions:'
```

Key settings:
```yaml
sessions:
  auto_prune: false          # ← MUST be true for automatic cleanup
  retention_days: 30         # keep last N days
  vacuum_after_prune: true   # reclaim disk after pruning
```

**Common trap:** `auto_prune: false` is the default. The config can have `retention_days` and `vacuum_after_prune` defined but they're completely dormant — they only activate when `auto_prune: true`.

### 3. Count sessions by source to find bloat

```sql
SELECT source, COUNT(*) as sessions, SUM(message_count) as msgs,
  ROUND(AVG(message_count),1) as avg_msgs
FROM sessions GROUP BY source ORDER BY sessions DESC;
```

### 4. Identify tab leaks (webui sessions with 0 messages)

```sql
-- Total zero-msg webui sessions
SELECT COUNT(*) FROM sessions WHERE source='webui' AND message_count = 0;

-- Find the day with the most empty sessions (== tab leak)
SELECT date(datetime(started_at, 'unixepoch')) as day, COUNT(*)
FROM sessions WHERE source='webui' AND message_count = 0
GROUP BY day ORDER BY COUNT(*) DESC LIMIT 10;

-- Check timing: if sessions were created every 1-2 minutes for hours,
-- that's an auto-refresh loop, not manual tab creation
SELECT datetime(started_at, 'unixepoch'), id
FROM sessions WHERE source='webui' AND message_count = 0
ORDER BY started_at ASC LIMIT 30;
```

**Pattern:** 438+ empty sessions in a single day with 1-2 minute spacing = page auto-refresh loop. Browser extension or tab crash-retry.

### 5. Identify cron session noise

```sql
-- Count watchdog-specific sessions
SELECT id LIKE 'cron_b664efd%' as is_watchdog, COUNT(*) as sessions,
  SUM(message_count) as msgs
FROM sessions WHERE source='cron' GROUP BY is_watchdog;
```

**Pattern:** 5-minute watchdog runs create whole new sessions. A `no_agent: true` script-only cron job creates NO sessions. The watchdog `b664efd` alone creates 342+ sessions in 47 days.

### 6. Understand DB size vs content

Raw message text is typically ~10% of total DB size. The rest is SQLite FTS (full-text search) indexes. Content is stored in `messages.content`; FTS indexes everything in `content`, `tool_calls`, `reasoning_content`, and `reasoning_details` — ~11x overhead is normal.

```sql
-- Raw content size
SELECT ROUND(SUM(LENGTH(CAST(content AS BLOB)))/1048576.0, 1) || ' MB'
FROM messages;

-- DB page stats
PRAGMA page_count;   -- total 4KB pages
PRAGMA freelist_count; -- free pages (0 = no room to VACUUM)
```

### 7. When to suspect corruption

- `PRAGMA quick_check` times out (>60s) — not a good sign
- Sessions that loaded fine yesterday fail today
- `DELETE` / `VACUUM` hang or crash
- The DB file is >2GB on a 460GB disk that's 97% full

## Root cause patterns (recurring)

| Symptom | Most likely cause |
|---------|-------------------|
| Prompts immediately fail / no response | DB write timeout due to 97%+ disk |
| "Session not found" for tabs that existed | Session row or messages corrupted in DB |
| Slow dashboard startup | 1.9GB DB loading + FTS index |
| Thousands of empty sessions | WebUI tab leak (page auto-refresh loop) |
| DB keeps growing despite few conversations | `auto_prune: false` + cron watchdog sessions + FTS index bloat |
| Zombie hermes processes | Aborted sessions not properly cleaned up |

## What to do about it

**Before any destructive action:** trace root cause. Ask: "Why is the DB this size?" The answer is almost always a combination of (auto_prune off) × (tab leak) × (cron noise) × (FTS overhead).

**Fix the config (prevents recurrence):**
```yaml
sessions:
  auto_prune: true
  retention_days: 30
  vacuum_after_prune: true
```

**Fix cron watchdog (reduces session creation rate):**
- Health-check style cron jobs should use `no_agent: true` script-only mode
- This creates zero sessions in the state DB

**To reclaim space NOW:**
1. Backup: `cp state.db state.db.pre-prune`
2. Delete low-value sessions (old cron, 0-msg webui, abandoned sessions)
3. VACUUM (requires free disk space — at least as much as the DB size)
4. If VACUUM fails, dump + recreate: `sqlite3 state.db .dump | sqlite3 state.db.new`

## Investigation-first principle

The user has a strong preference: **investigate and understand root causes before taking any destructive action.** Never prune, delete, or VACUUM without first:
1. Counting what would be removed (sessions, messages, sources)
2. Understanding WHY it accumulated
3. Presenting the findings with options
4. Getting explicit buy-in on what's safe to remove
