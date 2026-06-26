# Backend Testing Patterns

## Mock Session Pattern

```go
type mockSession struct {
    send chan Event
}

func newMockSession() *mockSession {
    return &mockSession{send: make(chan Event, 64)}
}

func drainEvents(sess *mockSession) []Event {
    var events []Event
    for {
        select {
        case e := <-sess.send:
            events = append(events, e)
        default:
            return events
        }
    }
}
```

Use `drainEvents()` to capture all events sent by a handler. The buffered channel prevents blocking.

## Integration Test Helpers

```go
func setupTestServer(t *testing.T) (*httptest.Server, *Multiplexer) {
    m := NewMultiplexer()
    server := httptest.NewServer(m.Router())
    t.Cleanup(server.Close)
    return server, m
}

func connectWS(t *testing.T, server *httptest.Server) *websocket.Conn {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    wsURL := "ws" + strings.TrimPrefix(server.URL, "http") + "/ws"
    conn, _, err := websocket.Dial(ctx, wsURL, nil)
    if err != nil {
        t.Fatalf("failed to connect websocket: %v", err)
    }
    t.Cleanup(func() { conn.Close(websocket.StatusNormalClosure, "test done") })
    return conn
}

func readEventsUntil(t *testing.T, ctx context.Context, conn *websocket.Conn,
    timeout time.Duration, match func(Event) bool) (Event, error) {
    deadline := time.Now().Add(timeout)
    for time.Now().Before(deadline) {
        remaining := time.Until(deadline)
        if remaining <= 0 { break }
        _, msg, err := conn.Read(context.WithValue(ctx, ...))
        // ... unmarshal and match
    }
    return Event{}, fmt.Errorf("timeout")
}
```

## Key Lessons

1. **Context timeouts**: Use 15-30s for WebSocket tests, not 5s. PTY startup adds latency.
2. **layout.initial structure**: `data.tree.pty_id`, not `data.pty_id`.
3. **sanitizePath behavior**: Sandboxes all paths under `allowedRoot`. `/etc/shadow` → `allowedRoot/etc/shadow`. Only `../` traversal rejected.
4. **mustMarshal helper**: Converts Go values to JSON `[]byte` for envelope params.

## Playwright Selector Patterns

```typescript
// ❌ Bad - strict mode violation (matches multiple elements)
await expect(page.getByText('Agent')).toBeVisible()

// ✅ Good - specific role + name
await expect(page.getByRole('heading', { name: 'Agent' })).toBeVisible()
await expect(page.getByRole('textbox', { name: 'Type a message...' })).toBeVisible()

// ✅ Good - specific class
await expect(page.locator('div.border-blue-500').first()).toBeVisible()

// ✅ Good - specific selector for resize handles
await page.locator('div.cursor-ew-resize').first()
```
