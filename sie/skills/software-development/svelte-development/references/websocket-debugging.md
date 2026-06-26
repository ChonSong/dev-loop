# WebSocket Debugging for Svelte 5 Stores

## Cross-Module State Sharing (globalThis Pattern)

When you need to share state between Svelte components and store modules (e.g., for browser console debugging), `window` isn't available in TypeScript type-checked modules without declarations.

**Problem:**
```typescript
// This causes TS2339: Property '__wsEvents' does not exist on type 'Window & typeof globalThis'
if (!window.__wsEvents) window.__wsEvents = []
```

**Solution — use `globalThis` with type assertion:**
```typescript
const win = globalThis as typeof globalThis & { __wsEvents?: Event[] }
if (!win.__wsEvents) win.__wsEvents = []
win.__wsEvents.push(event)
```

From browser console, access as `window.__wsEvents` (the type assertion doesn't affect runtime).

## Debug Logging in Store Modules

For WebSocket stores, add per-event logging to trace handler registration and message flow:

```typescript
// In ws.ts store module
const handlers = new Map<string, Set<(data: unknown) => void>>()

export function on(event: string, handler: (data: unknown) => void): () => void {
  if (!handlers.has(event)) {
    handlers.set(event, new Set())
  }
  handlers.get(event)!.add(handler)
  // Log handler registration for debugging
  console.log(`[WS] Handler registered for event: ${event}, total: ${handlers.get(event)!.size}`)
  return () => { /* cleanup */ }
}

// In socket.onmessage:
socket.onmessage = (ev) => {
  const event: Event = JSON.parse(ev.data)
  // Capture for browser console debugging
  const win = globalThis as typeof globalThis & { __wsEvents?: Event[] }
  if (!win.__wsEvents) win.__wsEvents = []
  win.__wsEvents.push(event)
  console.log('[WS] RECV event:', event.event, 'data:', JSON.stringify(event.data)?.substring(0, 200), '| total:', win.__wsEvents.length)
  
  // Handler dispatch
  const eventHandlers = handlers.get(event.event)
  console.log('[WS] Looking for handler:', event.event, 'found:', eventHandlers?.size || 0)
  if (eventHandlers) {
    for (const handler of eventHandlers) {
      handler(event.data)
    }
  }
}
```

## Debug Console Commands (Browser)

```javascript
// Check all WS events received (access via window)
window.__wsEvents?.map(e => e.event)

// Manual WebSocket test (send message directly)
const s = new WebSocket('ws://localhost:3005/ws');
s.onopen = () => { 
  s.send(JSON.stringify({protocol:'ui',method:'apps.launch',params:{type:'browser'},id:'test',ts:Date.now()})); 
};
s.onmessage = (e) => console.log('RECV:', e.data);
s.onerror = (e) => console.log('WS ERROR:', e);

// Check if layout delta was received
window.__wsEvents?.filter(e => e.event.includes('layout'))

// Check if browser launch response was received
window.__wsEvents?.filter(e => e.event.includes('apps.launch'))
```

## Handler Registration Order Issue

Handlers registered **before** the WebSocket connection opens may miss early events like `layout.initial`.

**Symptom:** `apps.launch.response` handler registered on component mount, but the response arrives before the handler is attached, so the tile never gets created.

**Fix:** The `on()` function attaches immediately and persists. The issue is likely that the backend **isn't sending** the event, not the handler missing it. Verify:
1. Backend receives the `apps.launch` message (check backend logs)
2. Backend sends `apps.launch.response` back
3. Event appears in `window.__wsEvents`

## Verifying Handler Is Attached

```typescript
// In the component using the handler
on("apps.launch.response", (data: unknown) => {
  console.log('[Dock] apps.launch.response received:', data)
})
```

If you see `Handler registered for event: apps.launch.response, total: 1` in the console but the handler never fires, the backend never sent the event. Check:
1. Backend received the request
2. Backend processed it
3. Backend sent the response

## Type-Safe Event Payloads

Use type assertions when handling event data:

```typescript
on("apps.launch.response", (data: unknown) => {
  const resp = data as { type?: string; browser_id?: string; pty_id?: string; note?: string }
  console.log('[Dock] apps.launch.response received:', resp)
  if (resp.type === "browser" && resp.browser_id) {
    // Handle browser launch
  }
})
```