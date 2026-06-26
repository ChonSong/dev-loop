# Session Analytics — Parsing Tool Call Metrics from Session Logs

## When to use

- User asks "how many tool calls per session", "efficiency analysis", "most active sessions"
- Auditing agent behavior across sessions
- Identifying which models/session-lengths produce the most tool usage

## Data location

```
/home/hermeswebui/.hermes/sessions/session_*.json
```

## JSON structure (critical — easy to get wrong)

```json
{
  "session_id": "20260510_105815_b0fe46",
  "model": "qwen3.6-plus",
  "platform": "tui",
  "session_start": "2026-05-10T10:58:00.000000",
  "last_updated": "2026-05-10T27:06:00.000000",
  "message_count": 1183,
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "...", "tool_calls": [...]},
    {"role": "tool", "name": "terminal", "tool_call_id": "call_xxx", "content": "..."}
  ]
}
```

**Key point:** Tool calls are in `message.tool_calls` on assistant-role messages.
They are NOT in `message.content` as `tool_use` blocks. Look here first.

## Extraction script

```python
import json, os, glob
from datetime import datetime

sessions = []
for f in glob.glob("/home/hermeswebui/.hermes/sessions/session_*.json"):
    with open(f) as fh:
        data = json.load(fh)
    
    msgs = data.get("messages", [])
    tool_calls = sum(
        len(m.get("tool_calls", []))
        for m in msgs
        if m.get("role") == "assistant"
    )
    tool_results = sum(1 for m in msgs if m.get("role") == "tool")
    
    duration_min = 0
    try:
        t1 = datetime.fromisoformat(data["session_start"])
        t2 = datetime.fromisoformat(data["last_updated"])
        duration_min = (t2 - t1).total_seconds() / 60
    except: pass
    
    sessions.append({
        "sid": data.get("session_id", "")[:16],
        "model": data.get("model", "?").split("/")[-1],
        "msgs": data.get("message_count", len(msgs)),
        "tools": tool_calls,
        "tool_results": tool_results,
        "duration_min": round(duration_min, 1),
    })
```

## Known findings (2,303 sessions, June 2026)

| Metric | Value |
|--------|-------|
| Max tool calls (session) | 569 |
| Max messages (session) | 1,183 |
| Max tool calls (single turn) | 20 |
| Avg tools/turn (when tools used) | 1.1 |
| Top tool | `terminal` (54%) |

### Efficiency curve (tools/min vs session length)

1–10 min sessions are **230x more tool-dense** than 12+ hr sessions (18.5 vs 0.08 tools/min).
But long sessions accumulate more total tools (avg 115 vs 61).
Tool-per-turn is stable (~0.9–1.0) regardless of session length.

### Most-used tools (ranked)

`terminal` > `execute_code` > `read_file` > `patch` > `write_file` > `search_files`

## Pitfalls

- **Don't look for `tool_use` blocks in `content`** — Hermes stores tool calls in the `tool_calls` key directly on the message object, not in the content array. This applies to the OpenRouter/hermes JSON session format. Other formats (Anthropic API) may differ.
- **Session files are cached locally** — not all sessions may be available if the server was restarted and sessions rotated. Don't assume completeness beyond what's on disk.
- **Cron sessions** have `platform: "cron"` — filter these out when analyzing interactive behavior.
