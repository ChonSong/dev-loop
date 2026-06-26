# Theming & Settings Panel Patterns

## 7-Theme CSS Variable System

HWC uses a `[data-theme]` attribute-based theme system. All themes define the same 18 CSS custom properties via selectors:

```css
:root { /* base defaults — Illogical Impulse */ }
[data-theme="catppuccin"] { /* overrides */ }
[data-theme="nord"] { /* overrides */ }
```

**Properties themed per theme:**
- `--bg-primary` — page background
- `--bg-panel`, `--bg-panel-hover`, `--bg-dock`, `--bg-input` — surface colors
- `--border-subtle`, `--border-default`, `--border-active`, `--border-glow` — border colors
- `--accent-primary`, `--accent-secondary`, `--accent-warm`, `--accent-danger` — accent palette
- `--text-primary`, `--text-secondary`, `--text-tertiary`, `--text-muted` — text hierarchy
- `--shadow-panel`, `--shadow-float`, `--glow-active` — shadows

## Theme Store (`stores/theme.svelte.ts`)

Svelte 5 reactive store using `$state` + `$effect`:

```typescript
class ThemeState {
  currentId = $state(loadTheme())  // loaded from localStorage on init
  constructor() {
    $effect(() => {
      document.documentElement.setAttribute("data-theme", this.currentId)
      saveTheme(this.currentId)    // persists to localStorage
    })
  }
  setTheme(id: string) { this.currentId = id }  // triggers effect
}
export const themeStore = new ThemeState()
```

**Key patterns:**
- `$state()` for reactive state, not `$state` runes in stores (works in `.svelte.ts` files)
- `$effect()` auto-runs on every `currentId` change — no manual listeners
- `data-theme` on `<html>` — CSS selectors override vars by specificity
- Theme data exported as typed `Theme[]` array with `colors` object (primary, accent, bg, surface, text) — used by SettingsPanel for theme card previews

## SettingsPanel Architecture

5 collapsible sections, each independently functional:

| Section | Backend | Frontend Store |
|---------|---------|---------------|
| General | localStorage | direct read/write |
| Appearance | localStorage + `data-theme` attribute | `themeStore` from `stores/theme.svelte.ts` |
| Shortcuts | none (static display) | none |
| Connection | WebSocket | `wsState` from `stores/ws.ts` |
| Advanced | localStorage | direct clear/reset |

**Pattern for toggle controls (grain, opacity):**
1. Read from `localStorage` in `onMount`
2. Persist to `localStorage` on every change
3. Apply to DOM via `document.documentElement.style.setProperty()` or element class toggle
4. State is local `$state()` — no need for a global store

**Pattern for visual theme picker:**
```svelte
{#each themes as theme (theme.id)}
  <button
    class:border-purple-500/50={themeStore.currentId === theme.id}
    onclick={() => themeStore.setTheme(theme.id)}
  >
    <!-- Color swatch row -->
    <span class="w-4 h-4 rounded-sm" style="background:{theme.colors.bg}"></span>
    <span class="w-4 h-4 rounded-sm" style="background:{theme.colors.accent}"></span>
    <div class="text-sm">{theme.name}</div>
    {#if themeStore.currentId === theme.id}<span>✓</span>{/if}
  </button>
{/each}
```

**Pattern for connection status display:**
```svelte
{#if $wsState.connected}
  <span class="bg-green-400"></span> Connected
{:else if $wsState.reconnecting}
  <span class="bg-yellow-400"></span> Reconnecting ({$wsState.retryCount}/10)…
{:else}
  <span class="bg-red-400"></span> Disconnected — click to retry
{/if}
```

## Adding a New Theme

1. Add entry to `themes[]` array in `stores/theme.svelte.ts`:
   ```typescript
   { id: "my-theme", name: "My Theme", description: "Description",
     colors: { primary: "#...", accent: "#...", bg: "#...", surface: "#...", text: "#..." } }
   ```
2. Add `[data-theme="my-theme"] { ... }` block in `styles/glass.css` with all 18 CSS variable overrides
3. Theme appears automatically in the visual picker

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/stores/theme.svelte.ts` | Theme definitions, reactive store, localStorage persistence |
| `frontend/src/styles/glass.css` | All `[data-theme]` CSS variable blocks (last section of file) |
| `frontend/src/components/SettingsPanel.svelte` | 5-section settings panel with all functional controls |
| `frontend/src/App.svelte` | Background uses `var(--bg-primary)`, grain overlay class for toggle |
| `frontend/src/main.ts` | Imports theme store to initialize on load |

## Gotchas

- **Tailwind v4:** Can't use `@apply` with CSS custom properties — use inline `style=""` or `<style>` blocks with `var()`. The `bg-[var(--bg-primary)]` syntax works in Tailwind v4 arbitrary values.
- **`[data-theme]` must be on `<html>`**, not `<body>` — `document.documentElement` is the correct target. `:root` and `<html>` are the same element, so `[data-theme]` selector overrides `:root` by specificity.
- **Theme store init on load:** Import the store file in `main.ts` as `import "./stores/theme.svelte"` so the `$effect()` runs on page load and restores the saved theme before hydration.
- **Svelte 5 `$state` in `.svelte.ts`:** Works differently than `.svelte` — use `$state()` at class field level, and `$effect()` in constructor. No `$derived` or `$props` available in `.svelte.ts` context.
- **localStorage key convention:** Use `hwc-*` prefix for all HWC-persisted settings to avoid collisions with other apps on the same domain.
