# Svelte 5 `effect_orphan` — Class-Based Stores

## The Error

The Svelte app fails to mount. Browser console shows:
```
PAGE_ERROR: https://svelte.dev/e/effect_orphan
Error: https://svelte.dev/e/effect_orphan
    at or (svelte-vendor-xxx.js)
    at fi (svelte-vendor-xxx.js)
    at ai (svelte-vendor-xxx.js)
    at new Ni (index-xxx.js)
    at index-xxx.js:31:7176
```

The page renders as a blank shell (`<div id="app"></div>` with no children).

## Root Cause

Svelte 5.55+ enforces that `$effect()` calls have a reactive parent root. A class constructor that uses `$effect()` and is called at module level violates this.

### Offending Pattern
```typescript
// stores/theme.svelte.ts
class ThemeState {
  currentId = $state(loadTheme())

  constructor() {
    $effect(() => {           // ❌ effect_orphan
      applyTheme(this.currentId)
      saveTheme(this.currentId)
    })
  }
}

export const themeStore = new ThemeState()  // module-level instantiation triggers constructor
```

## Fix

Wrap the `$effect()` in `$effect.root()`:

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
    // No cleanup needed — singleton lives for app lifetime
  }
}
```

## Verification

After applying the fix:
1. Rebuild the frontend: `cd frontend && npm run build`
2. Restart the server
3. Load the page — the app should render fully (check `#app` has children)
4. Run smoke tests: `cd e2e && npx playwright test tests/smoke.spec.ts`

## When to Apply

- **Required** for ANY `$effect()` in a class constructor that's instantiated at module level
- **Not needed** for `$effect()` inside `.svelte` component files (framework manages lifecycle)
- **Not needed** for `$effect()` inside functions called from existing reactive contexts
