# Stale Test Locators — hermes-web-computer E2E Tests
**Session:** 2026-05-25 (Phase 11 / v1.4 complete)

## Overview

hermes-web-computer E2E tests were written for component structures that have since changed. The test failures are NOT feature brokenness — the UI functions correctly. The tests have stale selectors.

## Specific Stale Locators Found

### 1. `getByRole('heading', { name: 'Agent' })` — chat-context.spec.ts

**Tests:** `chat-context.spec.ts` lines 13, 41, 72, 92, 119, 136  
**Expected element:** "Agent" heading in the right panel  
**Current state:** Panel structure changed (right panel shows Chat/Profiles/Skills tabs)  
**Fix:** Replace with `getByRole('textbox', { name: 'Type a message...' })` — the chat input is a more stable anchor

### 2. `locator('div.border-blue-500')` — pipeline.spec.ts, 01-layout.spec.ts

**Tests:** `pipeline.spec.ts` (all 4 tests), `01-layout.spec.ts`  
**Expected element:** Terminal tile with blue active border  
**Current state:** Theme commit changed from `border-blue-500` to `border-glass-border-active` class  
**Fix:** Use `page.locator('[role="button"][aria-label="Tile: xterm"]')` — the aria-label is stable across theme changes

### 3. `getByRole('button', { name: 'Files' })` — cross-panel.spec.ts, file-edit.spec.ts

**Tests:** `cross-panel.spec.ts` lines 30, 77, 110, 151; `file-edit.spec.ts` lines 16, 136  
**Expected element:** "Files" tab button in left panel  
**Current state:** Matches multiple elements — strict mode violation  
**Fix:** Use `page.getByRole('button', { name: 'Files', exact: true })` or `[aria-label="Files tab"]`

### 4. Command palette category tabs — hwc-features.spec.ts line 155

**Test:** `hwc-features.spec.ts:143` "command palette has category tabs"  
**Expected:** body text containing 'Layout', 'Terminal', 'Settings'  
**Current state:** Palette opens (Ctrl+K works), but body text is empty on that specific test  
**Fix:** Use `page.locator('[role="dialog"] [role="tab"]').count()` to verify tabs exist, rather than text content

## v1.4 Icon-Only Tab Locators

v1.4 changed LeftPanel from text-label tabs (`📁 Files`, `🚀 Apps`) to **icon-only** buttons (`📁`, `🚀`, `💬`). The accessible name is still the aria-label (e.g., `aria-label="Files"`), but the visible text is just the emoji.

**Pattern:** `getByRole('button', { name: 'emoji' })` — Playwright matches `aria-label` against `name`, so `getByRole('button', { name: '📁' })` finds the Files tab button even though only the emoji is visible.

| Tab | v1.3 selector (broken) | v1.4 selector (working) |
|-----|------------------------|------------------------|
| Files | `getByText('📁 Files')` | `getByRole('button', { name: '📁' })` |
| Apps | `getByText('🚀 Apps')` | `getByRole('button', { name: '🚀' })` |
| Chat | `getByRole('heading', { name: 'Agent' })` | `getByRole('button', { name: '💬 Chat' })` |

**Why `getByRole('button', { name: '💬 Chat' })` for Chat:** The right panel's "Agent" heading was replaced with tab buttons — `💬 Chat`, `👤 Profiles`, etc. The emoji+text label is the visible button text.

**Dock ambiguity:** The Dock also has a 📁 button (`aria-label="Files"`). If both Dock and LeftPanel tab use the same name, disambiguate by parent container:
```typescript
// Left panel tab (within .fixed.left-0 panel)
page.locator('.fixed.left-0 button[aria-label="Files"]')
// Dock tab (within .fixed.bottom-0 dock)
page.locator('.fixed.bottom-0 button[aria-label="Files"]')
```

## Stable Selector Hierarchy

1. **`aria-label`** — Most stable, never changes without explicit intent
   `page.getByRole('button', { name: 'Files', exact: true })`
   `page.locator('[aria-label="Tile: xterm"]')`
2. **`role` + `name`** — Second stable, semantic attributes
   `page.getByRole('textbox', { name: 'Type a message...' })`
3. **Structural classes** — `rounded-2xl`, `shadow-panel` survive theme changes; `border-blue-*` does NOT
   `page.locator('div.rounded-2xl')` — but use `.first()` since multiple elements have this class in v1.4
4. **Color classes** — AVOID `border-blue-*`, `text-purple-*`, `bg-gray-*` — first to change in theme refactors
5. **Text content** — Fragile; avoid `getByText('Files')` strict mode violations

## Multiple `rounded-2xl` Elements (v1.4)

v1.4 app starts with 3 `rounded-2xl` elements:
1. LeftPanel body (`backdrop-blur-xl rounded-2xl`)
2. RightPanel tab bar (`rounded-2xl`)
3. Terminal tile (`rounded-2xl cursor-pointer`)

Tests using `locator('div.rounded-2xl').count()` or `toHaveCount(1)` will fail. Use `.first()` for the tile, or add a more specific selector combining structural and behavioral attributes.

## Related

See `references/svelte5-vite-gotchas.md` in `hermes-computer` skill.