# Playwright E2E Setup for hermes-web-computer

## Quick Start

```bash
cd /opt/data/hermes-web-computer/frontend

# Install dependencies
npm install --save-dev @playwright/test vitest @vitest/ui @types/node

# Install Chromium browser
npx playwright install chromium

# Run tests
npx playwright test --reporter=list

# Run with UI
npx playwright test --ui
```

## Files Created

```
frontend/
  playwright.config.ts   # Config with system chromium + no-sandbox
  tsconfig.json          # TypeScript config for tests (moduleResolution: bundler)
  tests/
    e2e/
      app.spec.ts       # 6 critical path tests (all passing)
```

## playwright.config.ts Pattern

```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,  // Use 1 worker to avoid race conditions with WebSocket state
  timeout: 30000,

  projects: [{
    name: 'chromium',
    use: {
      launchOptions: {
        executablePath: '/usr/bin/chromium',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
      },
    },
  }],
})
```

**Critical settings:**
- `executablePath: '/usr/bin/chromium'` — system chromium in container
- `args: ['--no-sandbox', ...]` — required for running as root in container
- `--disable-dev-shm-usage` — prevents /dev/shm size errors in Docker
- `workers: 1` — WebSocket state means parallel workers can race

## Running Against Live Backend

Tests run against live servers (not mock). Ensure both are running:

```bash
# Terminal 1: backend
cd /opt/data/hermes-web-computer/backend && go run cmd/server/main.go

# Terminal 2: frontend dev server
cd /opt/data/hermes-web-computer/frontend && npx vite --host

# Terminal 3: tests
cd /opt/data/hermes-web-computer/frontend && npx playwright test
```

**URLs used in tests:**
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:3113`

## Current Tests (6 Passing)

| Test | What It Checks |
|------|---------------|
| `app loads without JS errors` | No `pageerror` events, page renders |
| `+ New Chat creates session` | No crash, session appears in list |
| `RightPanel all 7 non-chat tabs render` | Panel visible after clicking each tab |
| `SessionsPanel lists sessions` | "ALL SESSIONS" heading, session buttons |
| `Dock panel buttons switch RightPanel tab` | No crash when clicking Files |
| `chat tile receives messages` | App alive after typing + Enter |

## Selector Patterns

```typescript
// Dock item buttons
page.click('button:has-text("Files")')

// RightPanel tabs
page.click('button:has-text("👤 Profiles")')
page.click('button:has-text("◆ Skills")')

// ⚙️ tab — use aria-label (not has-text, see svelte5-aria-label.md)
page.click('button[aria-label="Settings tab"]')

// Sessions
page.locator('button:has-text("New conversation")')

// Chat input
page.locator('input[placeholder*="Type"]')
```

## What NOT to Test (Unreliable)

| Target | Why Unreliable |
|--------|---------------|
| Tile count before/after | Race condition — tiles mount asynchronously |
| "Disconnected" state | WS reconnects immediately on load |
| `data-tile` attribute | Not consistently applied to all tile types |

## Key Fixes Applied During Setup

1. **Dock.svelte** — `handleDockPanelClick` was undefined; replaced with direct `handleLaunch()` call
2. **RightPanel.svelte** — Added `aria-label="Settings tab"` to ⚙️ button
3. **vite.config.ts** — Renamed to `.mts` to avoid "Unknown file extension" error
4. **node_modules corruption** — Clean reinstall fixed after vitest installation broke vite

## Adding New Tests

```typescript
// tests/e2e/app.spec.ts
test.describe('Category', () => {
  test('description', async ({ page }) => {
    await page.goto('http://localhost:5173')
    await page.waitForSelector('button:has-text("+ New Chat")')
    // test steps...
  })
})
```

Run specific test:
```bash
npx playwright test tests/e2e/app.spec.ts:23 --reporter=list
```