# SSE Streamer Retry Pattern

## Overview
The Hermes Web Computer (HWC) agent streamer (`backend/agent/streamer.go`)
connects to the Hermes Agent SSE endpoint at `/api/chat/start`. Originally had
zero retry — single-shot HTTP POST that failed silently on connection drops.

The fix adds exponential backoff retry at three layers so failures are visible
and self-healing.

## Architecture (3 Layers)

### 1. Backend Streamer (`backend/agent/streamer.go`)
- `RetryConfig`: MaxAttempts (default 3), BaseDelay (1s), MaxDelay (30s)
- `doSSERequest()`: Isolated HTTP POST method extracted from old `Stream()`
- `readSSEStream()`: SSE line reader that returns `bool` (clean end vs dropped).
  Emits `stream_error` on scanner error, tracks `stream_end` receipt.
- `StreamWithRetry()`: Retry loop with exponential backoff (1s→2s→4s).
  Retries on **both** initial connection failure and mid-stream connection drops.
  Emits `stream_reconnect` event between attempts with human-readable message.
  After exhausting retries, emits `stream_error` + returns final error.
- `Stream()`: Backward-compatible wrapper (sets MaxAttempts=1, delegates to
  StreamWithRetry).
- `parseSSELine()`: Returns `StreamEvent` struct (not callback-based like the
  original). Caller in `readSSEStream` calls `onEvent(evt)`.

### 2. Backend Multiplexer (`backend/ws/multiplexer.go`)
- Chat handler (`handleChatWithHermes`): switched to `StreamWithRetry()`
- Tool handler (`handleToolExecute`): switched to `StreamWithRetry()`
- Maps `stream_reconnect` → `chat.reconnecting` WebSocket event
- Maps `stream_error` → `chat.error` WebSocket event

### 3. Frontend (`frontend/src/stores/sessions.svelte.ts`)
- `reconnecting` reactive state on `SessionStore`
- Handler for `chat.reconnecting` event registered in `send()` method
- `ChatPanel.svelte` renders amber banner with spinner + message + dismiss

## Pitfalls
- **Partial buffer + new token**: When changing `parseSSELine()` from
  callback-style (calling `onEvent` internally) to return-value-style, both
  `case "token"` and `default` case flush the partial buffer. The fix is to
  **COMBINE** `partial.String() + text` into one event. Emitting only the
  partial flush and returning drops the new token content.
- **Clean vs broken stream detection**: `readSSEStream` returns `true` only if
  `stream_end` event was actually seen. Scanner errors (connection reset,
  timeout) return `false` so `StreamWithRetry` can distinguish a normal
  completion from a mid-stream drop.
- **Context cancellation**: Every retry loop iteration checks `ctx.Err()` to
  respect upstream cancellation. The `select` between `ctx.Done()` and
  `time.After(delay)` ensures timely cancellation during backoff sleep.
- **WebSocket event routing**: The multiplexer's `sendEvent` must write to the
  correct session's WebSocket. The `stream_reconnect` event is mapped to
  `chat.reconnecting` and forwarded via the existing `sendEvent` path.

## Event Flow
```
Hermes Agent → SSE stream → StreamWithRetry → stream_reconnect → multiplexer
→ chat.reconnecting (WS) → sessionStore → ChatPanel reconnecting banner
```
