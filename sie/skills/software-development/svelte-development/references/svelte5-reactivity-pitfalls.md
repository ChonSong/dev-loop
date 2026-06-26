# Svelte 5 Reactivity Pitfalls (Runes + Stores)

## Critical: Store Subscriptions Don't Trigger `{#key}` in Svelte 5

### The Problem

In Svelte 5 runes mode, using `{#key $store.value}` does NOT re-evaluate when the store updates:

```svelte
<script>
  import { layout } from '../stores/ws'
  // ❌ DOES NOT WORK in Svelte 5 runes mode
  // $layout.version changes but {#key} doesn't trigger remount
</script>

{#key $layout.version}
  <Tile node={$layout.tree} />
{/key}
```

Same issue with `$derived` referencing store values:

```svelte
// ❌ DOES NOT WORK
let tree = $derived($layout.tree)
let version = $derived($layout.version)
```

### Why

Svelte 5's rune system and Svelte 4's store auto-subscription (`$store`) use different reactivity primitives. When a writable store calls `.set()`, the `$store` subscription updates, but Svelte 5's compiler doesn't always connect this to the rune-based reactivity graph for `{#key}` and `$derived`.

### The Window Bridge Pattern (WORKING)

Set window properties directly in the store's message handler, then use `$state` + `$effect` in the component:

**In your WS store (stores/ws.ts):**
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

**In your component (Component.svelte):**
```svelte
<script lang="ts">
  import type { LayoutTree } from '../stores/ws'

  // Local reactive copies that Svelte 5 CAN track
  let windowTree = $state<LayoutTree | null>(null)
  let windowVersion = $state(0)

  // $effect reads window properties — Svelte 5 tracks these
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

### Why This Works

1. `$effect` reads `window` properties which Svelte 5's reactivity tracks
2. Assignments to `$state` variables (`windowTree = t`, `windowVersion = v`) trigger reactive updates
3. `{#key}` on the `$state` version number forces component remounts when it changes

### Alternative: Tick Counter Pattern (Partial Fix)

```svelte
<script>
  import { get } from 'svelte/store'
  import { layout } from '../stores/ws'

  let tick = $state(0)
  
  // Subscribe to store and increment tick on any change
  layout.subscribe(() => { tick++ })

  let currentTree = $derived.by(() => {
    tick // dependency forces re-read
    return get(layout).tree
  })
</script>
```

**Note:** This works for initial render but may not update `{#key}` reliably. Use the window bridge pattern for guaranteed reactivity.

## Other Svelte 5 Reactivity Rules

### `$state(prop)` from `$props()` Breaks Reactivity

```svelte
// ❌ BAD
let { value = '' } = $props()
let current = $state(value)  // Initializes once, never updates

// ✅ GOOD
let { value = '' } = $props()
let current = $state('')
$effect(() => { current = value })  // Sync on every prop change
```

### `{#key}` Works with `$state` Variables

```svelte
// ✅ This works fine
let version = $state(1)

<button onclick={() => version++}>
  {#key version}
    <Component />
  {/key}
</button>
```

The issue is ONLY when `{#key $store.something}` — the `$` store subscription doesn't feed into Svelte 5's reactivity graph correctly.

## Quick Diagnostic

If your store is updating (check with `layout.subscribe(v => console.log(v))`) but the UI isn't re-rendering:

1. Add `{#key $store.value}<div data-debug="{$store.value}"></div>{/key}`
2. If the debug div doesn't update, you hit this bug
3. Implement the window bridge pattern

## Build Times

Svelte 5 + Vite builds take ~2 minutes for full production build. Use `npm run dev` for iteration during active development.
