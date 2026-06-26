# Agent Streaming — Backend SSE + Frontend Token Accumulation

## Files

- `backend/agent/streamer.go` — Go SSE client for Hermes Agent streaming
- `backend/ws/multiplexer.go` — `handleChatWithHermes` streams events to WS
- `frontend/src/stores/sessions.svelte.ts` — token buffering + `getBuf()` for ChatPanel
- `frontend/src/stores/ws.ts` — `chatSend()` passes `session_id`
- `frontend/src/components/ChatPanel.svelte` — derives `allMessages` from store + buffer

## Architecture

```
Frontend                          Go Backend                          Hermes Agent
────────────────────────────────────────────────────────────────────────────────
chat.send ──────────────────────► handleChatWithHermes
                                  streamer.Stream() ───────────────► POST /api/chat/start
                                  ← SSE token stream ←──────────────
                                  StreamEvent{token} ──────────────► chat.token WS event
                                  StreamEvent{reasoning} ───────────► chat.reasoning WS event
                                  StreamEvent{tool_call} ───────────► chat.tool_call WS event
                                  StreamEvent{tool_result} ─────────► chat.tool_result WS event
                                  StreamEvent{stream_end} ──────────► chat.reply WS event
                                  StreamEvent{error} ───────────────► chat.error WS event
```

## Backend Agent Streamer (`backend/agent/streamer.go`)

Key struct and method:

```go
type StreamEvent struct {
    Type      string      // token | reasoning | tool_call | tool_result | stream_end | error
    Content   string      // text content (token, reasoning)
    ToolCall  *ToolCall   // tool call details (tool_call event)
    Result    string      // tool result (tool_result event)
    Error     string      // error message (error event)
}

type ToolCall struct {
    ID   string
    Name string
    Args string
}

// Stream calls the endpoint, invokes callback per SSE event.
func (s *Streamer) Stream(ctx context.Context, message string, cb func(StreamEvent)) error
```

Hermes URL defaults to `http://localhost:8787` — set via `HERMES_URL` env var.

## Five WS Event Types for Streaming

| Event | Frontend action |
|-------|----------------|
| `chat.stream_start` | (optional) set streaming=true |
| `chat.token` | append to `_bufText[sessionId]`, accumulate |
| `chat.reasoning` | flush pending text first, then show reasoning |
| `chat.tool_call` | flush pending text, add to `_bufToolCalls[sessionId]` |
| `chat.tool_result` | append as `tool` role message |
| `chat.reply {complete:true}` | flush all, resolve promise |
| `chat.error {message}` | flush, set error state, reject promise |

## Frontend Accumulation Strategy

```typescript
class SessionStore {
  // Per-session buffers — Map keyed by sessionId
  private _bufText = $state<Map<string, string>>(new Map())
  private _bufToolCalls = $state<Map<string, any[]>>(new Map())

  // getBuf — for ChatPanel to read live streaming state
  getBuf(sid: string): { text: string; toolCalls: any[] } {
    return {
      text: this._bufText.get(sid) ?? "",
      toolCalls: this._bufToolCalls.get(sid) ?? [],
    }
  }

  async send(content: string): Promise<void> {
    const sid = this.activeId!
    this._appendMsg(sid, "user", content)  // Optimistic user message
    this._bufText.set(sid, "")
    this._bufToolCalls.set(sid, [])

    return new Promise((resolve) => {
      let pendingText = ""
      let pendingToolCalls: any[] = []

      const flush = () => {
        if (pendingText || pendingToolCalls.length > 0) {
          this._appendMsg(sid, "assistant", pendingText,
            pendingToolCalls.length > 0 ? pendingToolCalls : undefined)
          pendingText = ""
          pendingToolCalls = []
        }
      }

      on("chat.token", (data) => {
        pendingText += (data as any)?.content ?? ""
        this._bufText.set(sid, pendingText)  // Live update for ChatPanel
      })
      on("chat.reasoning", () => { flush() })
      on("chat.tool_call", (data) => {
        flush()
        pendingToolCalls.push(data)
        this._bufToolCalls.set(sid, [...pendingToolCalls])
      })
      on("chat.tool_result", (data) => {
        this._appendMsg(sid, "tool", (data as any)?.result ?? "")
      })
      on("chat.reply", () => { flush(); resolve() })
      on("chat.error", (data) => {
        this.error = (data as any)?.message ?? "Unknown error"
        resolve()
      })

      send({ protocol: "agent", method: "chat.send", params: { message: content, session_id: sid } })
    })
  }
}
```

## ChatPanel derives from store + buffer

```typescript
let allMessages = $derived.by(() => {
  const msgs = [...(activeSession?.messages ?? [])]
  const { text, toolCalls } = sessionStore.getBuf(activeId ?? "")
  if (text || toolCalls.length > 0) {
    msgs.push({
      role: "assistant",
      content: text,
      tool_calls: toolCalls.map((tc: any) => ({
        id: tc.id ?? "",
        type: "function" as const,
        function: {
          name: tc.name ?? "",
          arguments: tc.arguments ?? {},
        },
      })),
    } as SessionMessage)
  }
  return msgs
})
```

## Key Implementation Notes

- **Flush before reasoning/tool events** — any accumulated text token is finalized as an assistant message before showing reasoning output or tool call cards
- **`getBuf()` for live state** — ChatPanel reads `_bufText` and `_bufToolCalls` directly from the store to render live tokens while streaming
- **`_appendMsg` mutates in-place** — uses `this.sessions = this.sessions.map(...)` pattern to trigger Svelte 5 reactivity
- **Optimistic user message** — appended immediately before `send()`, not after
- **Backend always sends `session_id`** — Go streamer uses session ID from `handleChatWithHermes` param; frontend `chatSend` passes it in params
- **Hermes Agent endpoint** — `POST /api/chat/start` with SSE Accept header; parses `event:` SSE lines into typed `StreamEvent`