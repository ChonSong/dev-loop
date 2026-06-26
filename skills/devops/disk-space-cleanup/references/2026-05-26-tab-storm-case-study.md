# Case Study: May 2026 Tab Storm — 438 Empty Sessions in 14 Hours

## The Incident

On **2026-05-26**, the Hermes WebUI created **438 empty session tabs** (0 messages each) over a 14-hour period (01:55 to 16:01 UTC). These were interspersed with real user conversations, meaning the user was actively working while the storm happened in the background.

## Detection

```sql
-- Detected by checking 0-message webui sessions grouped by day
SELECT date(datetime(started_at, 'unixepoch')) as day,
       COUNT(*) as zero_msg_sessions
FROM sessions WHERE source='webui' AND message_count = 0
GROUP BY day ORDER BY zero_msg_sessions DESC LIMIT 10;
```

| Date | Empty Sessions | |
|------|---------------|-|
| 2026-05-26 | **438** | ← The storm |
| 2026-05-27 | 122 | ← Aftermath |
| 2026-05-28 | 73 | |
| 2026-05-29 | 41 | |
| Other days | 0-5 | Normal background |

Total: **701 empty webui sessions** across the DB's 47-day lifespan.

## Timing Pattern

```
2026-05-26 02:04:11   0 messages
2026-05-26 02:05:13   0 messages    ← every 1-2 minutes
2026-05-26 02:06:18   0 messages
2026-05-26 02:06:50   0 messages
2026-05-26 02:08:59   0 messages
...
```

The 30s-2min interval is consistent with an automatic page reload loop — not manual tab creation.

## Root Cause Chain

Traced through the webui source code:

1. **Connection disruption** — Something caused SSE/HTTP connections to drop (network blip, server restart, tunnel reconnect)
2. **Soft recovery fails** — `ui.js:123-131` tries `_recoverFromOfflineSoftly()` (reattach SSE, refresh session). If this throws (server mid-restart, DB timeout), it falls back to:
3. **Hard reload** — `window.location.reload()` at `ui.js:131`
4. **Boot can't restore session** — `boot.js` reads `localStorage.getItem('hermes-webui-session')` and tries `loadSession()`. If that fails (DB too slow), `S.session` stays null
5. **Empty session created** — `boot.js:1176` calls `await newSession()` because `S.session` is null
6. **Page loads, network drops again** → back to step 1

Each iteration creates a fresh 0-message session. 438 iterations in 14 hours.

## Compounding Factors

- **`sessions.auto_prune: false`** — No sessions ever cleaned up, so all 438 persisted
- **`messages.js` side-effect sessions** — Lines 694, 768, 789, 797, 812, 828 all call `if(!S.session){await newSession()}`. If the user typed a message while `S.session` was null, this created yet another session
- **`session_lifecycle.py` memory leak** — Every session added an entry to the process-global `_sessions` dict that never got removed

## Prevention

1. **Enable `sessions.auto_prune: true`** — Without this, every storm session lives forever
2. **Fix the soft-recovery path** — The hard-reload fallback at `ui.js:131` should be rate-limited (at most 1 reload per 30s)
3. **Decouple page load from session creation** — `boot.js:1176` should not create a new session on every init failure; it should show the empty state and wait for user intent

## Recovery

To clean up after a tab storm:

```sql
-- Delete all 0-message webui sessions
DELETE FROM messages WHERE session_id IN
  (SELECT id FROM sessions WHERE source='webui' AND message_count = 0);
DELETE FROM sessions WHERE source='webui' AND message_count = 0;

-- VACUUM to reclaim FTS index space
VACUUM;
```

This freed ~700 session rows and their FTS entries from a 1.9GB state.db.
