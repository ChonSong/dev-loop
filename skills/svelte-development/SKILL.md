---
name: svelte-development
description: "Svelte 5 development: runes mode syntax, Vite build patterns, common pitfalls."
category: software-development
tags: [svelte, frontend, javascript, typescript, vite, runes]
source: local
is_imported: true
---

# svelte-development

Svelte 5 development: runes mode syntax, Vite build patterns, common pitfalls.

**Category:** software-development
**Source:** local

## Svelte 5 Playwright Testing Patterns

See `references/playwright-svelte5-patterns.md` for Playwright configuration and selector strategies for Svelte 5 apps.

## Class-Based Stores in `.svelte.ts` Files

Svelte 5 runes work in `.svelte.ts` files inside classes, but with a critical caveat for `$effect` in constructors.

### The `$effect.root()` Pattern

```typescript
// stores/theme.svelte.ts
class ThemeState {
  currentId = $state(loadTheme())

  constructor() {
    // WRONG — throws effect_orphan in Svelte 5.55+
    // $effect(() => { applyTheme(this.currentId) })

    // CORRECT — wrap in $effect.root()
    const cleanup = $effect.root(() => {
      $effect(() => {
        applyTheme(this.currentId)
        saveTheme(this.currentId)
      })
    })
  }
}

export const themeStore = new ThemeState()  // module-level instantiation
```

### Why

Svelte 5 treats `$effect` outside component init as "orphaned" — lacking a reactive root. `$effect.root()` creates one. The cleanup handle can be ignored for singleton stores that live for the app's lifetime.

### Diagnostic: `effect_orphan` Error

If the app fails to mount with `https://svelte.dev/e/effect_orphan`:
1. Find `$effect()` calls in class constructors
2. Check for module-level `new ClassName()` instantiation
3. Wrap with `$effect.root(() => { $effect(() => { ... }) })`

- `[role="dialog"]` textContent returning empty string - fix with child-element selectors
- Ctrl+K keyboard shortcut conflicts with xterm.js terminals
- Testing backend-dependent components in loading state
