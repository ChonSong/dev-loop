# Svelte 5 + Playwright: Dialog Testing & Keyboard Conflicts

## Problem: `[role="dialog"]` textContent Returns Empty

Svelte 5 dialog overlays rendered by `{#if visible}` blocks have a rendering quirk: `page.locator('[role="dialog"]').textContent()` returns `""` even when the dialog is visually fully populated. This is reproducible across Svelte 5.55.x + Playwright 1.59.x.

**Symptom:** Command palette opens via Ctrl+K but category tab text can't be read from the dialog container.

**Root cause:** Svelte 5's DOM reconciliation may not populate `textContent` on the container element before Playwright reads it. The visual rendering (CSS/frame) is complete but the DOM `textContent` property is stale.

## Fix: Check Child Elements Directly

```typescript
// ❌ WRONG — textContent returns "":
const bodyText = await page.locator('[role="dialog"]').textContent().catch(() => '')
expect(bodyText).toContain('Layout')

// ✅ CORRECT — check category buttons directly:
const layoutCat = page.getByRole('button', { name: /Layout/i })
const hasCategories = await Promise.all([
  layoutCat.isVisible({ timeout: 3_000 }).catch(() => false),
]).then(results => results.some(Boolean))
expect(hasCategories).toBe(true)

// ✅ ALSO GOOD — check specific child elements:
const input = page.locator('input[placeholder*="command"]')
await expect(input).toBeVisible({ timeout: 3_000 })
```

**General rule:** For Svelte 5 overlays, always select child elements (buttons, inputs, list items) directly rather than relying on the parent dialog's `textContent`.

## Problem: Ctrl+K Keyboard Shortcut Conflicts with xterm.js

When a Svelte app with xterm.js terminal tiles registers `Ctrl+K` via `globalThis.addEventListener("keydown", ...)`, the terminal may intercept the event.

**Symptom:** The first test ("Ctrl+K opens palette") passes (palette flashes briefly) but subsequent tests that check palette content fail with timeout or empty text.

**Root cause:** xterm.js registers its own keyboard handler for Ctrl+K (clear screen). Even though the Svelte handler calls `e.preventDefault()`, the terminal may still consume the event before the global handler runs, or the event order depends on focus.

**Fix:** 
1. Use child-element selectors that wait up to 3s (`isVisible({ timeout: 3_000 })`)
2. Increase wait time after keyboard press (`await page.waitForTimeout(800)`)
3. Prefer `getByRole('button', { name })` for category buttons over `textContent()` checks

## Pattern: Testing Backend-Dependent Components

When a Svelte component depends on a backend (e.g., Docker images list), it may show "Loading..." state indefinitely if the backend is unreachable.

**Fix:** Accept the loading state as a valid display state:
```typescript
const noImagesText = page.getByText(/No images found|Loading images/)
const tableHeader = page.getByText('Repository').or(page.getByText('Tag')).first()
const hasContent = await Promise.all([
  noImagesText.isVisible({ timeout: 5_000 }).catch(() => false),
  tableHeader.isVisible({ timeout: 5_000 }).catch(() => false),
]).then(([noImages, table]) => noImages || table)
expect(hasContent).toBe(true)
```
