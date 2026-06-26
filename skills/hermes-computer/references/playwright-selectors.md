# Playwright Selector Patterns for hermes-web-computer

## Selector Cheat Sheet

| Target | Selector | Why |
|--------|----------|-----|
| Terminal tile | `div.rounded-2xl` | Unique rounded-2xl class on Tile component (NOT `border-blue-500` — removed in v1.4) |
| Left panel tabs (📁 emoji-only, v1.4+) | `.rounded-2xl.shadow-panel button:nth(1)` | LeftPanel uses icon-only emoji buttons without text labels or aria-label; `nth(1)` = 📁 Files, `nth(0)` = 💬 Sessions |
| Left panel tab via Dock | `getByRole('button', { name: '📁' })` | Dock uses `aria-label="Files"` — does NOT switch left panel to Files tab (dock dispatches `hwc-dock-panel` with `"file-manager"` which RightPanel doesn't handle) |
| Left panel tab (text label, v1.3) | `getByRole('button', { name: 'Files' })` | v1.3 had text labels; v1.4 icon-only broke these selectors |
| Agent heading (v1.3) | `getByRole('heading', { name: 'Agent' })` | Replaced in v1.4 by tab button `getByRole('button', { name: '💬 Chat' })` |
| Right panel tab (v1.4) | `getByRole('button', { name: '💬 Chat' })` | RightPanel uses tab buttons with emoji+text, not heading elements |
| Dock 📁 button | `getByRole('button', { name: '📁' })` | Dock uses `aria-label="Files"` on icon-only button; unambiguous |
| Chat input | `getByRole('textbox', { name: 'Type a message...' })` | Distinguishes from xterm textarea |
| Resize handles | `.cursor-ew-resize` | Unique class on ResizeHandle |
| Main container | `div.h-screen` or `.bg-gray-950` | Root layout div |
| Command palette | `[role="dialog"]` or `.fixed.inset-0` | Dialog overlay; use `.or()` with `.first()` to avoid strict mode: `page.locator('[role="dialog"]').or(page.locator('.fixed.inset-0')).first()` |

## Cross-Panel Test Pattern

When testing cross-panel workflows (create file via terminal → verify in file tree), the left panel's Files tab uses an emoji-only button. The Dock's Files button with `aria-label="Files"` conflicts with LeftPanel selectors.

**Correct approach — target left panel directly:**
```typescript
// Switch to Files tab in the left panel sidebar
const leftPanel = page.locator('.rounded-2xl.shadow-panel').first()
const filesButton = leftPanel.locator('button').nth(1)  // 💬=0, 📁=1, 🚀=2
await filesButton.click()
await page.waitForTimeout(1500)

// Navigate file tree from root "/"
await page.getByRole('button', { name: '/' }).first().click()
await page.waitForTimeout(1500)
const tmpEntry = page.locator('li:has-text("tmp")').first()
if (await tmpEntry.isVisible({ timeout: 5_000 })) {
  await tmpEntry.click()
}
```

## RightPanel Tab Switching Behavior

RightPanel tabs are switched by the `activeTab` rune state. The tab buttons in the right panel header have `onclick={() => activeTab = "containers"}` handlers. Dock-dispatched tab switches go through `hwc-dock-panel` custom events.

| Dock `item.type` | RightPanel handler | Works? |
|-------------------|-------------------|--------|
| `"profiles"` | ✅ `activeTab = "profiles"` | Yes |
| `"skills"` | ✅ `activeTab = "skills"` | Yes |
| `"crons"` | ✅ `activeTab = "crons"` | Yes |
| `"memory"` | ✅ `activeTab = "memory"` | Yes |
| `"settings"` | ✅ `activeTab = "settings"` | Yes |
| `"config"` | ✅ `activeTab = "config"` | Yes |
| `"observability"` | ✅ `activeTab = "observability"` | Yes |
| `"containers"` | ✅ `activeTab = "containers"` | Yes |
| `"file-manager"` | ❌ **NOT handled** | Bug — Dock dispatches but RightPanel ignores |
| `"agent"` | ❌ NOT handled | Agent chat is the default tab, not a switchable event |
| `"dashboard"` | ❌ NOT handled | No dashboard tab in RightPanel |
| `"audio"` | ❌ NOT handled | Voice is embedded in chat tab, not a separate panel |

## Common Pitfalls

### Emoji Button Strict Mode Violations

`getByRole('button', { name: '📁' })` can hit strict mode violations because multiple elements share the same emoji. LeftPanel 📁 and Dock 📁 both exist. Always scope to a container.

### RightPanel "📦 Containers" Tab Not Switching

If clicking the "📦 Containers" button in the RightPanel tab header doesn't change the displayed content, the issue is likely in Svelte 5 reactive interpolation. The button code at `RightPanel.svelte:338-343` has:
```svelte
class="... {activeTab === 'containers' ? 'text-white bg-white/10' : '...'}"
onclick={() => activeTab = "containers"}
```
And the content switch at `RightPanel.svelte:459`:
```svelte
{:else if activeTab === "containers"}
  <DockerPanel />
```
If the button class doesn't change (remains gray instead of `bg-white/10`), the `activeTab` assignment isn't propagating. Check for:
1. Console JS errors (type mismatches in template expressions)
2. Whether `DockerPanel.svelte` imports/exports cause Svelte 5 compilation edge cases
3. Whether the `$state()` rune for `activeTab` is correctly typed as `TabId` with `"containers"` in the union type

### Dock → RightPanel FileManager Gap

The dock dispatches `hwc-dock-panel` with `{ panel: "file-manager" }` when the Files 📁 button is clicked, but RightPanel's `handleDockPanel` doesn't handle `"file-manager"`. The left panel has its own tab state (`activeTab: "files" | "apps" | "sessions"`) which is independent of RightPanel. There's no event bridge from Dock to LeftPanel for switching the Files tab.

## Running Tests

```bash
# Single test
PLAYWRIGHT_BROWSERS_PATH=/opt/data/.cache/playwright npx playwright test tests/01-layout.spec.ts

# Suite
PLAYWRIGHT_BROWSERS_PATH=/opt/data/.cache/playwright npx playwright test tests/workflows/

# All tests
PLAYWRIGHT_BROWSERS_PATH=/opt/data/.cache/playwright npx playwright test --reporter=list

# Update visual baselines
PLAYWRIGHT_BROWSERS_PATH=/opt/data/.cache/playwright npx playwright test tests/visual/ --update-snapshots
```

## Config

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://localhost:3005',
    headless: true,
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
});
```
