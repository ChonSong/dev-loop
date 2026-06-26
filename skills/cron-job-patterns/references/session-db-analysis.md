# Session DB Analysis for Cron Diagnosis

When cron jobs are failing, bloating the DB, or behaving unexpectedly, the session state database (`state.db`) is the best source of truth. SQLite queries reveal what jobs exist, how many sessions they've created, their message patterns, and their actual prompts.

## Key Queries

### List all cron jobs by frequency and volume

```sql
SELECT substr(id, 6, 12) as job_id, title, COUNT(*) as runs,
       SUM(message_count) as msgs, MAX(started_at) as last_run
FROM sessions WHERE source='cron' AND id LIKE 'cron_%'
  AND title IS NOT NULL AND title != ''
GROUP BY job_id, title ORDER BY last_run DESC;
```

### Find cron job prompts (from request_dump JSON files)

Cron job prompts are logged as `request_dump` JSON files on disk:

```bash
ls -lt /home/sean/.hermes/sessions/request_dump_cron_<job_id>_*.json | head -3
cat /home/sean/.hermes/sessions/request_dump_cron_<job_id>_latest.json | python3 -m json.tool | head -60
```

The JSON contains the full system prompt and user message sent to the model, including all injected tools and the available_skills list.

### Identify zero-message webui sessions (tab leaks)

```sql
SELECT date(datetime(started_at, 'unixepoch')) as day,
       COUNT(*) as empty_sessions
FROM sessions WHERE source='webui' AND message_count = 0
GROUP BY day HAVING COUNT(*) >= 5 ORDER BY day DESC;
```

Spikes of empty sessions (>5/day) indicate a connection/reload loop in the webui.

### Session DB size vs content size (FTS bloat indicator)

```sql
-- Total DB size
SELECT page_count * page_size / 1048576.0 || ' MB' as db_size
FROM pragma_page_count, pragma_page_size;

-- Raw content size
SELECT 'messages content' as component,
       ROUND(SUM(LENGTH(CAST(content AS BLOB)))/1048576.0, 1) || ' MB' as size
FROM messages;
```

A large gap means FTS index bloat. FTS5 indexes typically add 2-5x overhead. >10x means VACUUM is needed or DB is corrupted.

### Raw content per column

```sql
SELECT 'content' as col,
       ROUND(SUM(LENGTH(CAST(COALESCE(content,'') AS BLOB)))/1048576.0, 1) || ' MB'
FROM messages
UNION ALL
SELECT 'reasoning_content',
       ROUND(SUM(LENGTH(CAST(COALESCE(reasoning_content,'') AS BLOB)))/1048576.0, 1) || ' MB'
FROM messages
UNION ALL
SELECT 'tool_calls',
       ROUND(SUM(LENGTH(CAST(COALESCE(tool_calls,'') AS BLOB)))/1048576.0, 1) || ' MB'
FROM messages;
```

Large `reasoning_content` is normal for reasoning models. Large `tool_calls` suggests verbose tool usage.

### DB fragmentation check

```sql
SELECT page_count, page_size,
       page_count * page_size / 1048576.0 || ' MB' as total_bytes,
       freelist_count,
       ROUND(freelist_count * 100.0 / page_count, 1) || '%' as free_pct
FROM pragma_page_count, pragma_page_size, pragma_freelist_count;
```

A `free_pct` near 0% means DB is fully packed — no internal fragmentation to reclaim by VACUUM alone (needs prune + VACUUM).

### Source volume breakdown

```sql
SELECT source, COUNT(*) as sessions, SUM(message_count) as msgs,
       ROUND(AVG(message_count), 1) as avg_msgs
FROM sessions GROUP BY source ORDER BY sessions DESC;
```

High `avg_msgs` (>50) for cron sources indicates verbose sessions or debug loops.

## Diagnostic Patterns

### Pattern: Tab leak storm (100+ empty webui sessions/day)

Empty webui sessions with message_count=0 at regular 30s-2min intervals indicate a reload loop. Root cause chain:

1. Connection drop triggers `_recoverFromOfflineSoftly()` in `ui.js:123`
2. Soft recovery fails (server mid-restart, DB timeout) → falls back to `window.location.reload()` at `ui.js:131`
3. On reload, boot flow tries to restore saved session from localStorage
4. If that fails too, calls `await newSession()` → creates a fresh empty session
5. If the post-reload request also fails → another reload → loop

**Check:** Were there deployments, server restarts, or cloudflare tunnel issues on the storm day?

**Fix:** Rate-limit session creation in boot path, or ensure the server/gateway is healthy before allowing reload.

### Pattern: Watchdog creates too many sessions

A 5-min health check creates ~288 sessions/day. If it only checks HTTP status:
- Convert to `no_agent: true` script mode (zero sessions)
- Or if LLM reasoning wanted (trend analysis): use `skills: []` + `enabled_toolsets: ["terminal"]`

### Pattern: DB too large for VACUUM

If `PRAGMA quick_check` times out (>60s), recovery options:
1. Prune sessions first (DELETE old data), then VACUUM
2. Dump valuable sessions as JSON, rebuild DB, reinsert
3. Restore from sync copy (`hermes-sync/state.db`)

**Prevention:** `sessions.auto_prune: true` + `sessions.vacuum_after_prune: true` keeps DB under 500MB with 30-day retention.

### Pattern: Vision provider failure traps agent in debug loop

If `vision_analyze` calls fail, the agent may loop trying to debug it. Check config:
```yaml
auxiliary:
  vision:
    base_url: https://openrouter.ai/api/v1
    model: google/gemini-2.0-flash-001
    # api_key: ''   ← empty = silent failure
```

The "jb" session hit this: 25+ turns debugging vision before the user gave up.

**Fixes:**
1. Configure a working API key
2. Switch provider
3. Use pixel-diff QA (Puppeteer + screenshot comparison) — see `ui-qa-pipeline` skill
