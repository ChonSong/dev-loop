# Hermes State Migration — Dev/Prod Workflow

Use this reference when moving Hermes SQLite state between environments (prod → dev or dev → prod).

## State Location

`$HERMES_HOME/hermes.db` — single SQLite file containing:
- Session transcripts
- FTS5 full-text search index (sessions, memory)
- Cron job definitions
- Skill metadata

## Migration Script

`hermes-state-migrate.sh` at `/opt/data/agent-os/scripts/hermes-state-migrate.sh`

```bash
# Snapshot production state
hermes-state-migrate.sh backup

# Load into local dev
hermes-state-migrate.sh restore ~/.hermes/backups/hermes-state-YYYYMMDD_HHMMSS.db.gz

# Inspect without restoring
hermes-state-migrate.sh inspect ~/.hermes/backups/hermes-state-YYYYMMDD_HHMMSS.db.gz

# Compare two snapshots
hermes-state-migrate.sh diff /tmp/state-a.db.gz /tmp/state-b.db.gz

# List all backups
hermes-state-migrate.sh list
```

## Safety Rules

1. **Never `vacuum` or `reindex` a live DB** — FTS5 index is actively written. Use `VACUUM INTO` (online backup) or stop the Hermes process first.
2. **Always backup before restore** — `backup` runs automatically before any restore.
3. **Pause Hermes before restore** — the script sends `SIGSTOP` to Hermes processes automatically.
4. **Backups are compressed with gzip** — `.db.gz` extension. Decompress with `gunzip -c <file> | sqlite3`.

## Hermes API Server vs nanobot Sidecar (migration context)

When migrating from a custom agent (nanobot) to Hermes, the backend proxy must be updated:

| | Old (nanobot) | New (Hermes) |
|---|---|---|
| API endpoint | `http://127.0.0.1:8001/v1/chat/completions` | `http://127.0.0.1:8642/v1/chat/completions` |
| Auth | `NANOBOT_API_KEY` env var | `HERMES_API_KEY` env var |
| Event forwarding | `/api/agent/forward` (nanobot POSTs events) | Same endpoint — Hermes POSTs to it |
| Socket events | `agent:start`, `agent:output`, `agent:end` | `start`, `output`, `end` |
| Event payload | `{ type, content, tools_used }` | `{ content, tool_calls, tool_results }` |

The backend Express server at `:3001` acts as the relay bridge. Update `backend/src/routes/agent.ts` to proxy to Hermes at `:8642` and keep the `POST /api/agent/forward` endpoint for Socket.IO relay.
