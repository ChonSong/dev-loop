# Browser Tile Debugging (Session 2026-05-12)

## Root Cause Summary

Two bugs prevented Browser tile from appearing after clicking the dock button:

1. **App type mismatch in `apps.go`** — `switch` cases didn't match dock's `type` values
2. **Missing `browser_id` propagation** — `LayoutTree` didn't carry the CDP endpoint

## Fix Applied

### Fix 1: `backend/ws/apps.go` — App Type Matching

The `handleAppsLaunch` function had wrong `case` strings. Changed from:

```go
case "dash-overview", "dash-filemanager", "dash-observability":
    // dashboard
case "browser-instance":
    // browser
```

To:

```go
case "dashboard":
    // Dashboard app
case "browser":
    // Browser app  
case "voice":
    // Voice app
case "file-manager":
    // File manager app
```

Dock sends `{type: "browser", ...}`, backend must receive `"browser"`.

### Fix 2: `backend/layout/tree.go` — BrowserID Propagation

Added `BrowserID` field to `LayoutTree` struct and ensured it propagates in `applySplit` and `applyMount`:

```go
// In applySplit, when creating the new right child:
{
    ID:        node.ID + "_right",
    Type:      "leaf",
    Content:   op.Content,
    PTYID:     op.PTYID,
    BrowserID: op.BrowserID,  // Added
    Size:      0.5,
}

// In applyMount, new leaf creation:
newLeaf := LayoutTree{
    ID:        "mount_" + node.ID,
    Type:      "leaf",
    Content:   op.Content,
    PTYID:     op.PTYID,
    BrowserID: op.BrowserID,  // Added
    Size:      0.5,
}
```

Also need to add `BrowserID` to the `Op` struct:

```go
type Op struct {
    Op        string `json:"op"`
    TargetID  string `json:"target_id"`
    Direction string `json:"direction"`
    Content   string `json:"content"`
    PTYID     string `json:"pty_id,omitempty"`
    BrowserID string `json:"browser_id,omitempty"`  // Added
}
```

### Fix 3: Frontend Dock Component — Include browser_id in layout.update

When handling `apps.launch.response` for browser:

```typescript
send({ protocol: "ui", method: "layout.update", params: {
  op: "split",
  target_id: "root",
  direction: "h",
  content: "browser",
  browser_id: resp.browser_id,  // Must include this
}})
```

## WebSocket Message Flow

### Successful browser launch sequence:

1. **Frontend → Backend**: `{"protocol":"ui","method":"apps.launch","params":{"type":"browser"},"id":"...","ts":...}`
2. **Backend → Frontend**: `{"protocol":"ui","event":"apps.launch.response","data":{"browser_id":"browser_...","type":"browser","url":"about:blank"},"ts":...}`
3. **Frontend → Backend**: `{"protocol":"ui","method":"layout.update","params":{"op":"split","target_id":"root","direction":"h","content":"browser","browser_id":"browser_..."},"id":"...","ts":...}`
4. **Backend → Frontend**: `{"protocol":"ui","event":"layout.delta","data":{"layout_version":2,"ops":[{"Op":"split","TargetID":"root","Direction":"h","Content":"browser","PTYID":"..."}]},"ts":...}`
5. **Backend → Frontend**: `{"protocol":"ui","event":"layout.initial","data":{"layout_version":2,"tree":{...}},"ts":...}`

## Debug Console Commands

```javascript
// Check all WS events received
window.__wsEvents?.map(e => e.event)

// Check current tile count
document.querySelector('[role="region"]')?.children?.length + ' tiles'

// Check WebSocket connection state
document.querySelector('[class*="Disconnected"]') ? 'DISCONNECTED' : 'CONNECTED'

// Manual WS test - send browser launch
const s = new WebSocket('ws://localhost:3005/ws');
s.onopen = () => { 
  s.send(JSON.stringify({protocol:'ui',method:'apps.launch',params:{type:'browser'},id:'test',ts:Date.now()})); 
};
s.onmessage = (e) => console.log('RECV:', e.data);
```

## Chromium Setup

```bash
# Install chromium
apt-get install -y chromium

# Start server with chromium path
CHROMIUM_PATH=/usr/bin/chromium PORT=3005 /tmp/hwc-server

# Verify chromium processes
ps aux | grep chrom | grep -v grep
```

## Browser.svelte Expected Props

The Browser component receives `tileId` as a prop but the actual CDP connection URL comes from the layout tree's `browser_id`. The component structure:

```svelte
<script lang="ts">
  import { ptyOutputs } from "../stores/ws"
  let { tileId = "" }: { tileId?: string } = $props()
  
  // CDP URL from browser instance
  // Format: "http://localhost:{debuggingPort}"
  // Retrieved from backend via browser_id
</script>
```

The component mounts a `<iframe>` pointing to the CDP debugging URL. If the tile shows black, either:
1. The `browser_id` wasn't propagated (check Fix 2)
2. The `browser_id` wasn't included in `layout.update` (check Fix 3)
3. Chromium CDP isn't running (check Chromium Setup)

## Additional Root Causes Found (2026-05-12 Session)

### Fix 4: Dual Tree State in `layout.delta`

**Problem**: `layout.initial` sends `m.state.Tree` (type `state.LayoutTree`) while `layout.delta` sends `m.layout` (type `layout.LayoutTree`). These are DIFFERENT types. The frontend was receiving a `layout.delta` with a tree that wasn't the same structure as what `layout.initial` sent.

**Fix in `backend/ws/multiplexer.go`**: Changed `layout.delta` to send `m.layout` via the same `layout.LayoutTree` path as `layout.initial`:

```go
// Before: layout.delta only sent ops array
delta, err := m.layout.Apply(op)
sess.Send(Event{Protocol: "ui", Event: "layout.delta", Data: json.RawMessage(
    fmt.Sprintf(`{"layout_version":%d,"ops":[%s]}`, m.state.LayoutVersion, opsJSON))})

// After: layout.delta includes full tree
delta, err := m.layout.Apply(op)
m.state.Tree, _ = m.layout.Marshal()  // sync state→layout
sess.Send(Event{Protocol: "ui", Event: "layout.delta", Data: json.RawMessage(
    fmt.Sprintf(`{"layout_version":%d,"tree":%s,"ops":[%s]}`,
    m.state.LayoutVersion, treeJSON, opsJSON))})
```

### Fix 5: Svelte 5 Store Reactivity Bug

**Problem**: Even after fixing the backend dual-tree issue, the Svelte component wasn't re-rendering. The store's `.set()` was called successfully (confirmed via console logs), but `$layout.tree` and `$layout.version` subscriptions didn't trigger re-renders in the `{#key}` block.

**Root Cause**: Svelte 5's rune-based reactivity (`$state`/`$effect`) doesn't properly track Svelte 4-style store auto-subscriptions (`$store`) inside `{#key}` expressions and `$derived`.

**Fix: Window Bridge Pattern**

In `frontend/src/stores/ws.ts`:
```typescript
if (event.event === "layout.delta") {
  const newTree = event.data?.tree as LayoutTree
  const newVersion = event.data?.layout_version as number
  if (newTree) {
    layout.set({ tree: newTree, version: newVersion })
    // Bridge to Window for Svelte 5 reactivity
    ;(window as any).__layoutTree = newTree
    ;(window as any).__layoutVersion = newVersion
  }
}
```

In `frontend/src/components/MiddlePanel.svelte`:
```svelte
<script lang="ts">
  let windowTree = $state<LayoutTree | null>(null)
  let windowVersion = $state(0)

  $effect(() => {
    const t: LayoutTree | null = (window as any).__layoutTree
    const v: number = (window as any).__layoutVersion
    windowTree = t
    windowVersion = v
  })
</script>

{#if windowTree}
  {#key windowVersion}
    <Tile node={windowTree} />
  {/key}
{/if}
```

**Why it works**: `$effect` reads `window` properties (tracked by Svelte 5), assignments to `$state` vars trigger reactivity, `{#key}` on the version forces Tile remounts.

### Fix 6: TypeScript Set Iteration Error

**Problem**: `for (const handler of eventHandlers)` failed with `Type 'Set<...>' can only be iterated through when using '--downlevelIteration'`.

**Fix**: `const handlersArr = Array.from(eventHandlers)` before iterating.

## Files Modified

- `backend/ws/apps.go` — Fixed case statement for app types
- `backend/layout/tree.go` — Added BrowserID to LayoutTree, Op; propagated in applySplit/applyMount
- `backend/ws/multiplexer.go` — layout.delta now sends full tree; fixed int64/int type mismatch
- `frontend/src/stores/ws.ts` — Added window bridge for Svelte 5 reactivity, debug event logging, Array.from() for Set iteration
- `frontend/src/components/Dock.svelte` — Added layout.delta listener, include browser_id in layout.update
- `frontend/src/components/MiddlePanel.svelte` — Window bridge pattern + {#key} for forced remounts