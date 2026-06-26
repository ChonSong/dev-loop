# Svelte 5 Store Reactivity Investigation

## The Problem

Svelte 5 stores (writable/readable) do NOT trigger component re-renders when updated from external callbacks (WebSocket onmessage, setTimeout, event listeners, etc.). The store's internal update context is separate from Svelte's component reactivity context.

## Confirmed Working Pattern: `createSubscriber`

**File:** `frontend/src/stores/layout.svelte.ts`

```typescript
import { createSubscriber } from 'svelte/reactivity'
import { layout } from './ws'

export const layoutState = createSubscriber(layout, ($layout) => ({
  tree: $layout.tree,
  version: $layout.version,
  floatingTiles: $layout.floatingTiles
}))
```

**Usage in runes-mode component:**
```svelte
<script lang="ts">
  import { layoutState } from "../stores/layout.svelte"
  
  let currentTree = $derived(layoutState.tree)
  let currentVersion = $derived(layoutState.version)
</script>
```

`createSubscriber` runs the subscriber callback inside Svelte's reactivity context, so `$derived` tracking works correctly. This is the officially recommended pattern (see Svelte GitHub discussion #16880).

## Confirmed Broken Patterns

| # | Approach | Why It Fails |
|---|----------|--------------|
| 1 | `$layout.tree` in template | Runes mode doesn't track store subscriptions directly |
| 2 | `{#key $layout.version}` | Store update doesn't trigger key recomputation |
| 3 | `$derived($layout.tree)` | Same — derived doesn't track store subscriptions |
| 4 | `$effect(() => { x = $layout.tree })` | Effect runs in component context but store update is external |
| 5 | `$state` + setInterval polling | Works but hacky, adds latency |
| 6 | `$state` + rAF polling | Same |
| 7 | `$state` in `.svelte.ts` (plain) | Variable not tracked by Svelte's reactivity |
| 8 | Window DOM events + `$effect` | DOM events are external to Svelte context |
| 9 | sessionStorage polling | Same |
| 10 | flushSync wrapping | Doesn't fix the context mismatch |
| 11 | derived([ws, layout], ...) | Still store-based, same problem |
| 12 | window bridge + $state | Bridge updates are external callbacks |
| 13 | `<svelte:options runes={false} />` + onMount + subscribe | Subscribe fires but component context not re-evaluated |
| 14 | Legacy mode + `$layout` in template | Same |
| 15 | `on('layout.update', handler)` in onMount | Handler updates `let` var but no re-render in runes mode |

## Root Cause

Svelte's reactivity (both runes and legacy) only tracks state mutations within its own execution context. WebSocket `onmessage`, `setTimeout`, `addEventListener`, and store `subscribe` callbacks all run outside this context. The store IS updated (subscribe callbacks fire with correct data) but Svelte doesn't know the component needs to re-render.

## Background

- GitHub issues: #16007, #17526
- Svelte discussion: #16880 (createSubscriber recommendation)
- Session that discovered fix: 2026-05-13 — MiddlePanel.svelte refactor, commit `08ac287`
