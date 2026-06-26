# Session DB Direct Query

Hermes stores all session transcripts in a SQLite database at `~/.hermes/state.db` (mapped to `/opt/data/state.db` in the container).

Use this when `session_search` returns empty results or when you need to read a specific session's full content.

## Quick Query

```python
import sqlite3
conn = sqlite3.connect('/opt/data/state.db')
c = conn.cursor()

# List recent sessions
c.execute("SELECT id, title, started_at, ended_at, message_count, source FROM sessions ORDER BY started_at DESC LIMIT 10")
for r in c.fetchall():
    print(r)

# Get all messages from a session
c.execute("SELECT role, substr(content, 1, 500), timestamp FROM messages WHERE session_id='SESSION_ID' ORDER BY timestamp")
for r in c.fetchall():
    print(f'[{r[0]}] {r[1]}')
```

## Schema

**sessions table columns:** `id, source, user_id, model, model_config, system_prompt, parent_session_id, started_at, ended_at, end_reason, message_count, tool_call_count, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, billing_provider, billing_base_url, billing_mode, estimated_cost_usd, actual_cost_usd, cost_status, cost_source, pricing_version, title, api_call_count`

**messages table columns:** `id, session_id, role, content, tool_call_id, tool_calls, tool_name, timestamp, token_count, finish_reason, reasoning, reasoning_content, reasoning_details, codex_reasoning_items, codex_message_items`

## Finding a Specific Session

```python
# By title (partial match via LIKE)
c.execute("SELECT id, title, started_at FROM sessions WHERE title LIKE '%nanobot%' ORDER BY started_at DESC")

# By date range (Unix timestamps)
import time
from datetime import datetime
start = datetime(2026, 5, 1).timestamp()
end = datetime(2026, 5, 3).timestamp()
c.execute("SELECT id, title, started_at FROM sessions WHERE started_at >= ? AND started_at <= ? ORDER BY started_at", (start, end))
```

## Session ID Format

Format: `YYYYMMDD_HHMMSS_<6_hex_chars>`  
Example: `20260502_014558_bee61b`

This makes them trivially sortable by timestamp.
