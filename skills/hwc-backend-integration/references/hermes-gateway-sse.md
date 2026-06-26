# Hermes Gateway SSE — Event Flow & Session Lifecycle
**Source**: Discovered 2026-06-01 during HWC backend integration work

## Session Lifecycle

```
GET /api/sessions → pick session_id → POST /api/chat/start → receive stream_id
                                                          ↓
                                              SSE events stream back
                                              (token, reasoning, tool_call, tool_result, stream_end)
                                              ↓
                                              Next turn: POST /api/chat/start with same session_id
```

## SSE Event Types

| Event Type | Fields | When |
|------------|--------|------|
| `text` / `token` | `text`, `reasoning?` | Model token output. `reasoning` field present for chain-of-thought |
| `interim_assistant` | `text` | Partial model response before tool calls |
| `tool_call` | `tool_calls[{id, function{name, arguments}}]` | Model invoking a tool |
| `tool_result` | `result` | Tool execution result |
| `stream_end` | — | Stream complete |
| `cancel` | — | Stream cancelled |
| `error` | — | Error occurred |

## Python Usage (himalaya/hermes context)

Not directly relevant to Go — the streamer is in `backend/agent/streamer.go`.

Usage in multiplexer:
```go
streamer := agent.NewStreamer(m.hermesURL, "")
err := streamer.Stream(ctx, message, func(evt agent.StreamEvent) {
    switch evt.Type {
    case "token":       // evt.Content has text
    case "tool_result": // evt.Result has output
    case "tool_call":   // evt.ToolCall.Name, .Args
    }
})
```

## Stream ID vs Session ID

- `session_id`: Persistent conversation (e.g., `20260529_025917_36f9a5`)
- `stream_id`: Per-turn stream handle (e.g., `2407feec31d14cb5bde896fddf81ad6`)
- `turn_id`: Per-turn identifier with timestamp (e.g., `20260601T081504Z-077036313a2d`)

## Error Responses

| Error | Meaning | Fix |
|-------|---------|-----|
| `"Session not found"` | session_id doesn't exist | Create session or use existing one from `/api/sessions` |
| `"Missing required field(s): session_id"` | No session_id in request body | Add `session_id` field |
| `"not found"` | Wrong endpoint path | Use `/api/chat/start` not `/v1/chat/completions` |
