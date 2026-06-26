---
name: svelte-development
description: "Svelte 5 development: runes mode syntax, Vite build patterns, common pitfalls."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [svelte, frontend, javascript, typescript, vite, runes]
    related_skills: [writing-plans, subagent-driven-development]
---

# Svelte 5 Development

## Overview

Svelte 5 introduced **runes mode** — a fundamentally different reactivity model from Svelte 4. Code written in Svelte 4 syntax will NOT compile in Svelte 5 runes mode.

**When to use this skill:** Building or modifying Svelte 5 applications, especially with `runes: true` in svelte.config.js.

## Svelte 5 Syntax Rules (Runes Mode)

### Rule 1: No `$:` reactive statements

**Svelte 4 (WRONG in Svelte 5):**
```svelte
<script>
  import { ws } from "./stores/ws"
  $: connected = $ws.connected  // ❌ COMPILE ERROR
</script>
```

**Svelte 5 (CORRECT):**
```svelte
<script>
  import { ws } from "./stores/ws"
  let connected = $derived($ws.connected)  // ✅
</script>
```

### Rule 2: No `export let` for props

**Svelte 4 (WRONG in Svelte 5):**
```svelte
<script>
  export let visible: boolean = false  // ❌ COMPILE ERROR
  export let node: LayoutTree          // ❌ COMPILE ERROR
</script>
```

**Svelte 5 (CORRECT):**
```svelte
<script>
  let { visible = $bindable(false) }: { visible?: boolean } = $props()  // ✅
  let { node }: { node: LayoutTree } = $props()                          // ✅
</script>
```

### Rule 3: No `on:event` handlers

**Svelte 4 (WRONG in Svelte 5):**
```svelte
<div on:click={handleClick} on:focus={handleFocus}>  <!-- ❌ COMPILE ERROR -->
```

**Svelte 5 (CORRECT):**
```svelte
<div onclick={handleClick} onfocus={handleFocus}>    <!-- ✅ -->
```

**Note:** Mixing old (`on:click`) and new (`onclick`) event syntax in the same component is not allowed.

### Rule 4: Use `$state()` for local reactive state

```svelte
<script>
  let count = $state(0)        // Reactive local state
  let query = $state("")       // Reactive string
  let items = $state([])       // Reactive array
</script>
```

### Rule 5: Use `$derived()` for computed values

```svelte
<script>
  let items = $state([])
  let filtered = $derived(items.filter(i => i.active))  // Auto-updates when items changes
</script>
```

### Rule 7: `$` prefix is reserved for variable names

**Svelte 5 (WRONG):**
```svelte
<script>
  import { workspaceStore } from "./stores/workspace"
  let $ws = $state($workspaceStore)  // ❌ COMPILE ERROR: dollar_prefix_invalid
</script>
```

**Svelte 5 (CORRECT):**
```svelte
<script>
  import { workspaceStore } from "./stores/workspace"
  let wsState = $derived($workspaceStore)  // ✅ Use non-$ variable name
</script>
```

The `$` prefix is reserved for Svelte runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`, `$inspect`) and store subscriptions (`$store`). You cannot use it as the first character of a variable name.

### Rule 8: Workspace store with localStorage persistence

When building workspace/multi-state systems, convert from plain module state to a writable store with auto-save:

```typescript
import { writable, get } from "svelte/store"

interface WorkspaceStoreState {
  activeWorkspace: number
  workspaces: WorkspaceState[]
}

const initialState: WorkspaceStoreState = { /* ... */ }

// Restore from localStorage
try {
  const saved = localStorage.getItem("hwc-workspaces-v1")
  if (saved) {
    Object.assign(initialState, JSON.parse(saved))
  }
} catch {}

export const workspaceStore = writable<WorkspaceStoreState>(initialState)

// Auto-save on every change
workspaceStore.subscribe((state) => {
  try {
    localStorage.setItem("hwc-workspaces-v1", JSON.stringify(state))
  } catch {}
})

// In components, use $derived for reactivity:
let wsState = $derived($workspaceStore)  // NOT let $ws = $state(...)
```

```svelte
<script>
  let visible = $state(false)
  
  $effect(() => {
    if (!visible) {
      // Reset state when overlay closes
      query = ""
      selectedIndex = 0
    }
  })
</script>
```

## Component Template

```svelte
<script lang="ts">
  // Props
  let { title, count = 0, onAction }: { 
    title: string
    count?: number
    onAction?: () => void
  } = $props()
  
  // Local state
  let expanded = $state(false)
  let searchText = $state("")
  
  // Derived values
  let filtered = $derived(searchText ? items.filter(i => i.name.includes(searchText)) : items)
  let displayCount = $derived(filtered.length)
</script>

<div class="container">
  <h2>{title}</h2>
  <p>Count: {displayCount}</p>
  <input bind:value={searchText} placeholder="Search..." />
  {#each filtered as item}
    <div onclick={() => onAction?.()}>
      {item.name}
    </div>
  {/each}
  <button onclick={() => expanded = !expanded}>
    {expanded ? 'Collapse' : 'Expand'}
  </button>
</div>
```

## Vite Build Configuration

### package.json (Svelte 5 + Vite 6)

```json
{
  "name": "my-svelte-app",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "svelte": "^5.0.0"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^5.0.0",
    "vite": "^6.0.0"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from "vite"
import { svelte } from "@sveltejs/vite-plugin-svelte"

export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      "/ws": {
        target: "ws://localhost:3001",
        ws: true,
      },
    },
  },
  build: {
    outDir: "dist",
    target: "esnext",
  },
})
```

### svelte.config.js

```javascript
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte"

export default {
  preprocess: vitePreprocess(),
  compilerOptions: {
    runes: true,  // Enables Svelte 5 runes mode
  },
}
```

## Common Build Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `Unexpected token` on `{:if}` inside `{#if}` block | Svelte 5 requires `{:else if}` when chaining after `{#if}` at same nesting level | Use `{:else if}` instead of standalone `{:if}` for else-branch conditions |
| `$:` is not allowed in runes mode | Svelte 4 reactive statement | Use `$derived()` |
| Cannot use `export let` in runes mode | Svelte 4 props syntax | Use `$props()` |
| Mixing old and new event syntax | `on:click` with `onclick` | Use only `onclick` style |
| `<div>` with click handler must have ARIA role | a11y warning | Use `<button>` or add `role="button"` |
| `vite: not found` after `npm install` | NODE_ENV=production skips devDeps | `NODE_ENV=development npm install` |
| `<li>` should not have click handler | a11y: non-interactive element | Use `<button>` inside `<li>` |

## ARIA/A11y Rules in Svelte 5

Svelte 5 has stricter a11y checks:

1. **Non-interactive elements** (`<div>`, `<span>`, `<li>`) cannot have `tabindex` ≥ 0
2. **Non-interactive elements** with click handlers need keyboard handlers too
3. **`autofocus`** attribute triggers a11y warning — use programmatic focus instead
4. **Solution:** Use semantic elements (`<button>`, `<a>`) for interactive content

```svelte
<!-- BAD: div with click handler -->
<div onclick={handleClick}>Click me</div>

<!-- GOOD: button element -->
<button onclick={handleClick}>Click me</button>

<!-- GOOD: div with role and keyboard handler -->
<div role="button" onclick={handleClick} onkeydown={(e) => e.key === 'Enter' && handleClick()}>
  Click me
</div>
```

## WebSocket Store Pattern

```typescript
// stores/ws.ts
import { writable } from "svelte/store"

export const ws = writable<{ connected: boolean; lastError: string | null }>({
  connected: false,
  lastError: null,
})

export const layout = writable<{ tree: LayoutTree | null; version: number }>({
  tree: null,
  version: 0,
})

let socket: WebSocket | null = null

export function connect(url: string = "ws://localhost:3001/ws") {
  if (socket?.readyState === WebSocket.OPEN) return
  socket = new WebSocket(url)
  
  socket.onopen = () => ws.set({ connected: true, lastError: null })
  socket.onmessage = (ev) => {
    const event = JSON.parse(ev.data)
    if (event.event === "layout.initial" || event.event === "layout.delta") {
      layout.update(l => ({ ...l, tree: event.data?.tree, version: event.data?.layout_version || l.version + 1 }))
    }
  }
  socket.onclose = () => {
    ws.set({ connected: false, lastError: "Connection closed" })
    setTimeout(() => connect(url), 2000)
  }
}

export function send(envelope: { protocol: string; method: string; params?: Record<string, unknown> }) {
  socket?.send(JSON.stringify({ ...envelope, id: `req_${Date.now()}`, ts: Date.now() }))
}

connect()
```

## Terminal Integration Pattern (xterm.js)

```svelte
<script lang="ts">
  import { onMount } from "svelte"
  import { Terminal } from "@xterm/xterm"
  import { FitAddon } from "@xterm/addon-fit"
  import { send, ptyOutputs } from "../stores/ws"

  let { ptyId = "" }: { ptyId?: string } = $props()
  let container: HTMLDivElement
  let term: Terminal
  let outputBuffer = $derived(ptyId ? ($ptyOutputs.get(ptyId) || "") : "")
  let lastLength = $state(0)

  onMount(() => {
    term = new Terminal({ cursorBlink: true, fontSize: 14 })
    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(container)
    fitAddon.fit()

    term.onData((data) => {
      send({ protocol: "agent", method: "pty.write", params: { data } })
    })

    const ro = new ResizeObserver(() => fitAddon.fit())
    ro.observe(container)
    return () => { ro.disconnect(); term.dispose() }
  })

  $effect(() => {
    if (term && outputBuffer.length > lastLength) {
      term.write(outputBuffer.slice(lastLength))
      lastLength = outputBuffer.length
    }
  })
</script>

<div bind:this={container} class="w-full h-full"></div>
```

## Build Commands

```bash
# Install (include devDependencies! NODE_ENV=production skips them)
NODE_ENV=development npm install

# Build for production
NODE_ENV=development node_modules/.bin/vite build

# Dev server
NODE_ENV=development node_modules/.bin/vite
```

## Tailwind 4 CSS Requirement

With `@tailwindcss/vite` plugin, CSS is **not auto-injected** into the build output. The CSS file must be explicitly imported in your entry point:

```typescript
// src/main.ts
import { mount } from "svelte"
import App from "./App.svelte"
import "./app.css"  // ← REQUIRED or Tailwind styles won't appear

const target = document.getElementById("app")
if (target) {
  mount(App, { target })
}
```

**Symptom:** Blank page — HTML and JS load correctly but no styling.
**Check:** `curl http://localhost:3001/` should show `<link rel="stylesheet">` in the `<head>`.
**If missing:** Add `import "./app.css"` to main.ts and rebuild.

## Mount() Tree-Shaking Pitfall

Svelte 5's `mount()` function can be **tree-shaken out** of production builds when called directly at module scope. The compiler sees it as unused code.

**Symptom:** Blank page — JS loads, no errors in console, nothing renders. The compiled JS may contain the mount call but it gets optimized away.

**Fix:** Call `mount()` from within an if-guarded block (checking the target element):

```typescript
// src/main.ts
import { mount } from "svelte"
import App from "./App.svelte"
import { connect } from "./stores/ws"
import "./app.css"

const target = document.getElementById("app")
if (target) {
  mount(App, { target })
  console.log("App mounted")
  connect()  // Call connect AFTER mount, not on store import
}
```

**Also:** Don't auto-connect WebSocket on store import. The store module loads before the DOM is ready, causing race conditions. Call `connect()` explicitly after `mount()` in main.ts.

### Svelte 5 Store Reactivity Bug → See references/svelte5-reactivity-pitfalls.md

Svelte 5 rune-based reactivity (`$state`/`$effect`) does NOT properly track Svelte 4-style store auto-subscriptions (`$store`) in `{#key}` expressions and `$derived` when the store is updated from async callbacks (WebSocket, setTimeout, etc.). If your store is updating but the UI isn't re-rendering, see `references/svelte5-reactivity-pitfalls.md` for the full analysis and workarounds.

**Never use `new App({ target })`** — this is the Svelte 4 constructor pattern. In Svelte 5 runes mode it silently fails to render. Always use `mount(App, { target })`.

## Common Build Errors & Fixes (Extended)

| Error | Cause | Fix |
|---|---|---|
| `vite: not found` after `npm install` | NODE_ENV=production skips devDeps | `NODE_ENV=development npm install` |
| Blank page, JS loads, no errors | `mount()` tree-shaken out | Guard mount with `if (target)` |
| Blank page, JS loads, no errors | Used `new App()` instead of `mount()` | Use `mount(App, { target })` |
| Blank page, no CSS | Missing `import "./app.css"` in main.ts | Add explicit CSS import |
| Blank page, WebSocket race | Auto-connect in store on import | Call `connect()` after `mount()` |
| `<div>` with dblclick/keydown handler must have ARIA role | a11y warning | Add `role="button"` or use `<button>` |
| `Node.js v20.19.2` module not found | Running from wrong directory (not frontend/) | Always `cd frontend/` before `npm install` |

## Playwright E2E Testing for Svelte Apps

### Selector Strategy

Svelte 5 + Tailwind components need **Tailwind class selectors**, not generic attributes or placeholder text.

**WRONG selectors (will fail):**
```typescript
page.locator('#app')              // #app exists but may have no visible dimensions
page.locator('div[tabindex="0"]') // May not exist if Tailwind class differs
page.locator('[role="dialog"]')   // Svelte overlays may not set ARIA role
page.getByText('Agent')           // Strict mode violation if multiple elements match
```

**CORRECT selectors:**
```typescript
page.locator('div.h-screen').first()          // Outer container
page.locator('div.border-blue-500').first()   // Terminal tile (blue border class)
page.locator('.cursor-ew-resize').first()     // Resize handles (unique cursor class)
page.locator('.w-96.bg-gray-900')             // Command palette (width + background)
page.getByRole('heading', { name: 'Agent' })  // Use specific role + name combo
page.getByRole('textbox', { name: 'Type a message...' })  // Use accessible name
```

### Key Patterns

```typescript
// Wait for WebSocket connection (no "Disconnected" text visible)
await expect(page.getByText('Disconnected')).not.toBeVisible({ timeout: 10_000 })

// Screenshot for visual regression (full page)
await page.screenshot({ path: 'e2e/test-results/layout.png', fullPage: true })

// Keyboard shortcuts (Svelte global listeners)
await page.keyboard.press('Control+K')  // Command palette
await page.keyboard.press('Control+b')  // Toggle left panel
await page.keyboard.press('Escape')     // Close overlays
```

### Playwright Config for Svelte + Backend

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,
  timeout: 30000,
  workers: 1,  // Svelte apps need sequential tests to avoid WS conflicts
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
  use: {
    baseURL: 'http://localhost:3005',
    viewport: { width: 1440, height: 900 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'cd backend && go run ./cmd/server',
    port: 3005,
    reuseExistingServer: true,
    timeout: 15000,
  },
})
```

### Common Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| `strict mode violation: getByText resolved to N elements` | Multiple elements contain the text | Use `getByRole()` with name, or add `.first()` |
| `locator('#app')` not visible | #app div has no dimensions/content | Select children: `.bg-gray-950` or `.h-screen` |
| WebSocket tests flaky | Shared context between tests | Use `context.newPage()` for each test |
| Command palette not detected | Looking for `[role="dialog"]` | Use actual class: `.w-96.bg-gray-900` |
| `workers > 1` causes failures | Multiple WS connections interfere | Set `workers: 1` |

## Subagent Timeout Pattern for Large Svelte Changes

Subagents running `delegate_task` for complex multi-file Svelte changes frequently hit the 600s timeout — **even when they've completed all the file writes**. The timeout means "didn't finish summarizing", not "didn't finish coding".

**Always check the filesystem after a subagent timeout:**
```bash
cd /opt/data/hermes-web-computer && git status --short
```
If files are modified or new files exist, the work is done. Review, fix any issues, and commit. Don't re-run the task.

## Build Pitfalls from Svelte 5.55+

### `{/* */}` Comments Break Compilation

Svelte 5.55+ **fails to compile** templates containing HTML comments (`{/* ... */}`) in the template section (after `</script>`). The compiler reports `Unexpected token` or `js_parse_error` pointing at the comment line.

**Fix:** Strip all `{/* */}` comments from templates. Use standard HTML `<!-- -->` comments instead.

```bash
# Remove all {/* ... */} from template sections
python3 -c "
import re
with open('src/Component.svelte', 'r') as f:
    content = f.read()
idx = content.find('</script>')
template = content[idx + 9:]
cleaned = re.sub(r'\{/\*.*?\*/\}', '', template, flags=re.DOTALL)
with open('src/Component.svelte', 'w') as f:
    f.write(content[:idx + 9] + cleaned)
"
```

### `$state(prop)` Where `prop` Comes from `$props()`

Initializing `$state()` with a prop value from `$props()` is not supported:

```svelte
<!-- BAD: Svelte 5 rejects $state(prop) where prop is reactive -->
<script>
  let { path = "" }: { path?: string } = $props()
  let currentPath = $state(path)  // ❌ Compile error or reactivity break
</script>
```

**Fix:** Initialize with a default, then sync via `$effect`:
```svelte
<script>
  let { path = "" }: { path?: string } = $props()
  let currentPath = $state("")
  $effect(() => { currentPath = path })  // ✅
</script>
```

### `$state.snapshot` Without Parentheses

`$state.snapshot` is a function — calling it without `()` triggers "Cannot use rune without parentheses":

```svelte
<!-- BAD -->
$state.snapshot // force reactivity  ❌

<!-- GOOD (if actually needed) -->
$state.snapshot(data)  ✅
```

### Naming Collision: Handler Parameter vs `$state` Variable

When using the `on()` event handler pattern from a WS store, naming the handler parameter the same as a `$state` variable causes the compiler to confuse them:

```svelte
<script>
  let data = $state(null)  // state variable
  
  on("analytics.result", (data: any) => {  // ❌ shadows the $state variable
    data = data  // ambiguous
  })
</script>
```

**Fix:** Use a distinct name for the handler parameter:
```svelte
  on("analytics.result", (rawData: any) => {
    if (rawData) {
      const d = rawData as AnalyticsData
      data = d  // ✅ unambiguous
    }
  })
```

## Svelte 5 Store Reactivity Bug — Detailed Analysis

### The Bug

When a Svelte 4-style `writable` store's `set()` is called from an async callback (WebSocket `onmessage`, `setTimeout`, `rAF`, Promise, event listener), Svelte 5 rune-mode components that read the store via `$store` auto-subscription do NOT re-render.

**Confirmed in Svelte 5.55.5.** GitHub issues: #16007, #13169, #11065.

### Why All Standard Workarounds Fail

Svelte 5's `$state` rune only triggers re-renders when the assignment happens inside a "tracked scope" — either directly in the component's script block or inside an `$effect`. But:

- `store.subscribe(callback)` — callback runs in untracked scope
- `setTimeout`/`setInterval`/`rAF` — callbacks run in untracked scope  
- `window.addEventListener` — handler runs in untracked scope
- `$effect(() => { ... })` — the effect body IS tracked, but `subscribe`/`setTimeout`/etc. callbacks created inside it are NOT
- `$state` in `.svelte.ts` files — mutations from external callbacks are untracked regardless of where the `$state` is declared

### Approaches Tried (All Failed)

1. `$layout.tree` directly in template
2. `{#key $layout.version}` for forced remount
3. `$derived($layout.tree)` 
4. `$effect` + `layout.subscribe` → `$state` assignment
5. `$state` + `setInterval` polling `window.__layoutTree`
6. `$state` + `requestAnimationFrame` polling
7. Custom DOM events (`window.dispatchEvent`) + `$effect` listener
8. `$state` in `.svelte.ts` file (plain variable)
9. `$state` in `.svelte.ts` class instance
10. `sessionStorage` polling
11. `flushSync` in polling callback

### What Might Work (Not Confirmed)

**Top-level component reads store + passes as props:**

```svelte
<!-- App.svelte -->
<script>
  import { layout } from './stores/ws'
  import MiddlePanel from './components/MiddlePanel.svelte'
  let tree = $derived($layout.tree)
  let version = $derived($layout.version)
</script>
<MiddlePanel {tree} {version} />
```

Reading the store at the top-level and passing data as props may work because the top-level component's re-render propagates to children. Not confirmed in this session.

### Nuclear Options

1. **Disable runes mode for specific files:** `<svelte:options runes={false} />`
2. **Avoid stores for async data:** Use context API, prop drilling, or service modules
3. **In-place mutation:** `layout.update(l => { l.tree = newTree; return l })` — same reference, may trigger depending on reading pattern (from GitHub discussion, not confirmed)

### Diagnostic

```
1. Confirm store updates: layout.subscribe(v => console.log(v.version))
2. Check DOM: document.querySelector('[data-debug]')?.getAttribute('data-debug')
3. Debug div updates but Tile doesn't → this bug
4. Debug div doesn't update → JS error, check console
5. Build takes ~2min — wait 120s before assuming failure
```

## Remember

```
Svelte 5 Runes Mode:
  $: derived → $derived()
  export let → $props()
  on:click → onclick
  $state() for local state
  $effect() for side effects
  Use semantic HTML for a11y
  {/* */} comments break compilation → use <!-- -->
  $state(prop) → $state("") + $effect(() => { state = prop })
  Store.set() from async callback → component won't re-render (known bug)
  {:if} inside {#if} block → {:else if} (not standalone {:if})
```
