# Svelte 5 `effect_orphan` Crash in HWC Headless Chrome

> Discovered 2026-06-10 during HWC visual QA baseline generation.

## Symptom

Chrome headless (v148) renders a completely blank white page when loading HWC:
- Screenshot: 4-8KB (blank white) vs 91-97KB (rendered interface)
- Console error: `https://svelte.dev/e/effect_orphan`
- 404 on a resource load
- Body text: empty (Svelte app never mounts)
- localStorage key `hwc-workspaces-v1` exists — app initialized briefly then crashed

## Root Cause

`frontend/src/stores/layout.svelte.ts` uses Svelte 5's `createSubscriber` + `$state` runes:

```typescript
import { createSubscriber } from "svelte/reactivity"

function createLayoutState() {
  let tree: LayoutTree | null = $state(null)
  let version = $state(0)
  let updateFn: (() => void) | null = null

  const subscribe = createSubscriber((update) => {
    updateFn = update
    return () => { updateFn = null }
  })

  return {
    get tree() {
      subscribe()
      return tree
    },
    get version() {
      subscribe()
      return version
    },
    setLayout(newTree, newVersion) {
      tree = newTree       // ← $state mutation outside component init
      version = newVersion // ← $state mutation outside component init
      updateFn?.()
    }
  }
}

export const layoutState = createLayoutState()
```

`ws.ts` imports `layoutState` and calls `layoutState.setLayout()` on the first WebSocket `layout.initial` event (line 197):

```typescript
import { layoutState } from "./layout.svelte"  // ← imports .svelte.ts module

// in onmessage handler:
if (event.event === "layout.initial") {
  layoutState.setLayout(newTree, newVersion)  // ← calls setLayout before any component subscribes
}
```

**The problem:** `createSubscriber` registers a callback when a component accesses `.tree` or `.version` inside its render/`$effect` context. No component has done this yet when the first WS message arrives (race condition — WS connects and receives layout before `MiddlePanel.svelte` mounts). So `$state` is being mutated outside of any component initialization → Svelte 5 throws `effect_orphan`.

## Why It Works in Normal Browsers

In normal Chrome/Firefox, Svelte's runtime is initialized differently, and the timing between WS connection and component mount may work out differently (or the `effect_orphan` check may be looser in non-headless mode). Only reproducible in headless Chrome v148 from the container.

## Possible Fixes

1. **Defer setLayout until subscriber exists** — Buffer WS events if `updateFn` is null, replay them once a component subscribes.
2. **Use classic Svelte stores** — Replace `createSubscriber`+`$state` with `writable` from `svelte/store`. Components read via `$layoutState.tree` subscription syntax. No runes = no effect_orphan.
3. **Initialize on component mount** — Move `layoutState` initialization to happen inside a component's `$effect` or `onMount`, not at module level.
4. **Wrap in $effect** — Have `App.svelte` create a `$effect` that touches `layoutState.tree` immediately on mount to register the subscriber before any WS message arrives.

## Second Source (2026-06-10): theme.svelte.ts Class Constructor

### Symptom

Same blank white page, same `effect_orphan` console error. Different root cause from the `layout.svelte.ts` case above.

### Root Cause

`frontend/src/stores/theme.svelte.ts` uses `$effect` inside a class constructor called at module level:

```typescript
class ThemeState {
  currentId = $state(loadTheme())
  constructor() {
    $effect(() => {                    // ← orphaned effect
      applyTheme(this.currentId)
      saveTheme(this.currentId)
    })
  }
}
export const themeStore = new ThemeState()  // ← module-level instantiation
```

Svelte 5.55+ treats `$effect` called outside component initialization as orphaned. Module-level class constructors that create effects need explicit root management via `$effect.root()`.

### Fix

Wrap the constructor's `$effect` in `$effect.root()`:

```typescript
class ThemeState {
  currentId = $state(loadTheme())
  constructor() {
    const cleanup = $effect.root(() => {
      $effect(() => {
        applyTheme(this.currentId)
        saveTheme(this.currentId)
      })
    })
    // cleanup() when the root should be destroyed (omit for app-lifetime effects)
  }
}
```

`$effect.root()` returns a destroy function. For app-lifetime effects (theme persists for entire session), cleanup can be safely ignored.

### Prevention

Any `$effect`/`$state`/`$derived` inside a module-level class constructor needs `$effect.root()`. This applies to `.svelte.ts` store files that export instantiated classes (`export const store = new StoreClass()`). Rule: if the effect isn't inside a component's reactive context, it needs an explicit root.

## Detection

The `hwc-visual-qa.sh` script detects failed renders via size heuristic:
```bash
if [ $SIZE -lt 10000 ]; then
  echo "RESULT: WARN — suspiciously small screenshot (${SIZE}B)"
fi
```
