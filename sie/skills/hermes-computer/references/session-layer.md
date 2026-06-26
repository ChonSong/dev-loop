# Session Layer — Frontend Store + Components

## Files

- `frontend/src/stores/sessions.svelte.ts` — Svelte 5 reactive session store ($state, $derived, $effect, WS promise-based API)
- `frontend/src/stores/ws.ts` — WS helpers + session CRUD functions (sessionNew, sessionList, sessionGet, sessionDelete, sessionRename, sessionSearch)
- `frontend/src/components/SessionsPanel.svelte` — Left panel tab: list, search, pin/unpin, delete, create, session selection
- `frontend/src/components/ChatPanel.svelte` — Tile-based chat: message list, streaming token display, tool call cards, auto-scroll, optimistic user message

## SessionsStore API

```typescript
// State
sessionStore.sessions    // Session[]
sessionStore.activeId    // string | null
sessionStore.activeSession  // Session | null (derived: sessions.find(s => s.session_id === activeId))

// Methods
sessionStore.select(id: string)          // Sets activeId, fetches full session via WS
sessionStore.create(workspace?, model?)  // Calls sessionNew WS, waits for ok
sessionStore.delete(id: string)          // Calls sessionDelete WS
sessionStore.rename(id: string, title: string)
sessionStore.togglePin(id: string)
sessionStore.refresh()                   // Re-fetches session list
```

## WS Event Flow

```
Session creation:
  session.new → backend creates JSON file → session.new.ok → frontend updates store

Session selection:
  session.get (WS) → backend returns full session JSON → frontend sets activeSession

Chat send:
  agent.chat.send → backend streams tokens → chat.streaming (live) → chat.reply (final) → store updated

Session delete:
  session.delete → backend removes JSON → session.delete.ok → store.refresh()
```

## ChatPanel Streaming Pattern

```typescript
let streaming = $state(false)
let streamingContent = $state("")
let cleanupFns: (() => void)[] = []

async function handleSend() {
  inputValue = ""
  streaming = true
  streamingContent = ""

  cleanupFns.push(
    on("chat.streaming", (data) => {
      streamingContent = (data as { content: string }).content ?? ""
    }),
    on("chat.reply", (data) => {
      cleanupFns.forEach(fn => fn())
      streaming = false
      // Add final message to store
    }),
    on("chat.error", (data) => {
      cleanupFns.forEach(fn => fn())
      streaming = false
      errorMsg = (data as { message?: string }).message ?? "Unknown error"
    })
  )

  send({ protocol: "agent", method: "chat.send", params: { message: text, session_id: activeId } })
}

$effect(() => {
  return () => cleanupFns.forEach(fn => fn())  // Cleanup on destroy
})
```

## SessionsPanel Safe Split Pattern

```typescript
import { layoutState } from "../stores/layout.svelte"

function openChatTile() {
  function findLeaf(node: any, path: string): string | null {
    if (node.type === 'leaf') return path
    if (node.children) {
      for (const child of node.children) {
        const found = findLeaf(child, child.id)
        if (found) return found
      }
    }
    return null
  }
  const targetId = layoutState.tree ? findLeaf(layoutState.tree, layoutState.tree.id) : "root"
  sendOp({
    op: "split",
    target_id: targetId ?? "root",
    direction: "v",
    content: "chat",
    size: 0.5,
  })
}

function handleSelectSession(sess: Session) {
  const firstOpen = !sessionStore.activeId
  sessionStore.select(sess.session_id)
  if (firstOpen) openChatTile()
}
```

## Backend Session Store (Go)

- `backend/session/store.go` — JSON file-based, `NewStore(dataDir)`, methods: `New()`, `List()`, `Get()`, `Save()`, `Delete()`, `Search()`, `AddMessage()`, `Rename()`, `TogglePin()`
- Sessions stored as `sessions/{id}.json` with `_index.json` for listing
- Workspace auto-created as `$HOME/.hermes/workspace/` per session