# Playwright Direct Invocation (no `npx playwright test`)

When `npx playwright test` fails because:
- Root `node_modules` lacks `@playwright/test` (only `e2e/node_modules/playwright` exists)
- `playwright.config.ts` imports from `@playwright/test` which isn't installed at root

Use direct Node.js invocation instead.

## Pattern: ESM smoke test via stdin

```javascript
// Run with: node --input-type=module < e2e/smoke.mjs
import { chromium } from '/path/to/e2e/node_modules/playwright/index.mjs';

const browser = await chromium.launch({ 
  executablePath: '/opt/data/.playwright/chromium-1159/chrome-linux/chrome',
  headless: true 
});
const page = await browser.newPage();
await page.goto('http://localhost:3005');

// Assertions...
const title = await page.title();
if (title !== 'Hermes Web Computer') throw new Error(`Title mismatch: ${title}`);

const tiles = await page.locator('div.rounded-2xl').count();  // migrated from div.border-blue-500
if (tiles === 0) throw new Error('No tile containers found');

const input = await page.locator('[role=textbox]').count();
if (input === 0) throw new Error('No input box found');

await browser.close();
console.log('✅ All smoke checks passed');
```

## Pattern: CJS smoke test (.cjs file)

For `e2e/package.json` with `"type": "module"`, `.cjs` bypasses the module system:

```javascript
// e2e/smoke.cjs — run with: node e2e/smoke.cjs
const { chromium } = require('./node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:3005');
  const title = await page.title();
  if (!title.includes('Hermes')) throw new Error('App not responding');
  await browser.close();
  console.log('✅ Passed');
})();
```

## Key env vars

| Var | Value | Why |
|-----|-------|-----|
| `PLAYWRIGHT_BROWSERS_PATH` | `/opt/data/.playwright` | Default path is `/opt/hermes/.playwright` — permission denied in container |
| `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` | `1` | Don't auto-download during script run |

## Finding the Chromium executable

```bash
# List installed browsers
ls /opt/data/.playwright/

# Use the full path explicitly in chromium.launch()
executablePath: '/opt/data/.playwright/chromium-1159/chrome-linux/chrome'
```

## When to use this vs `npx playwright test`

| Scenario | Method |
|----------|--------|
| Full test suite available (`@playwright/test` in root) | `npx playwright test` |
| Quick smoke check during development | Direct Node.js script |
| CI without `@playwright/test` at root | Direct Node.js script or `cd e2e && npx playwright test` |
| Debugging a specific selector/element | `node --input-type=module` via stdin |

## Common failures

**`Error: Cannot find module 'playwright'`** → Script importing from wrong path. Use explicit relative path: `require('./node_modules/playwright')` from `e2e/` dir, or full path to `playwright/index.mjs`.

**`Error: ENOENT no such file ... chrome`** → Chromium not installed. Run: `PLAYWRIGHT_BROWSERS_PATH=/opt/data/.playwright npx playwright install chromium`