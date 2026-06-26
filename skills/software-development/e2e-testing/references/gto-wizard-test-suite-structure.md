# GTO Wizard Test Suite Structure — 2026-06-16

Current state: **79 tests across 8 spec files**, all passing. This is the reference
for a real-world implementation of the layered test architecture (smoke → POM → workflow → infra).

## Per-File Inventory

### smoke.spec.ts — 5 tests (Smoke Layer)

Fast API integration checks. Tests wait for real data to render, not just DOM elements.

```
Smoke: Landing Page → loads feature cards
Smoke: Equity Calculator → renders range data and game state
Smoke: ICM Calculator → loads and displays ICM results
Smoke: Courses List → fetches and displays courses from API
Smoke: Variant Selector → loads variants from API and renders cards
```

### courses.spec.ts — 13 tests (POM Layer)

```
Classes: CoursesPage (constructor: page)
1. Page loads without errors at /courses
2. Course list displays with correct information
3. Difficulty filter works
4. Category filter works
5. Course selection shows detail view
6. Progress bars display correctly
7. Continue/Start course buttons
8. Quick stats section
9. Navigation between pages
(+ 4 more — interaction + detail tests)
```

### equity.spec.ts — 6 tests (POM Layer)

```
Classes: none (inline selectors)
1. Page loads without console errors at /equity
2. Range grid renders with both BB and BTN sections
3. Board and position elements are present
4. Statistics panel renders
5. Navigation from home page works
6. (one more edge case)
```
Key: uses H2 "Game" for heading, NOT H1 "Equity Calculator" (page is game-view layout).

### icm.spec.ts — 9 tests (POM Layer)

```
Classes: ICMPage (constructor: page)
1. Page loads without errors at /icm
2. PrizePoolPanel — prize distribution editing
3. ChipStackPanel — player stack management
4. ICMResults — equity calculations display
5. Tournament buy-in and total chips inputs
6-9. Navigation, filtering, edge cases
```
Console error filter: `!e.includes("500")` (backend optional, API may 500 without Docker stack).

### spots.spec.ts — 13 tests (POM Layer)

```
Classes: SpotsPage (constructor: page)
1. Page loads without errors at /spots
2. Spots list displays community strategy spots
3. Spot filtering by position and board type
4. Search functionality
5. Sorting by recent and popular
6. Spot selection and detail view
7. Like/unlike functionality
8. Share new spot button
9. Strategy heatmap display
10. Navigation between pages
(+ 3 more edge cases)
```

### strategies.spec.ts — 10 tests (POM Layer)

```
Classes: StrategiesPage (constructor: page)
1. Page loads without errors at /strategies
2. Chart displays with grid structure
3. Position filter works
4. Stack depth filter works
5. Chart type toggle (push vs call)
6. Export button exists
7. Navigation between pages
(+ 3 more edge cases — filter combinations, responsive)
```

### workflows.spec.ts — 9 tests (Workflow Layer)

These chain 5-10 interactions across 2-3 pages per test:

```
1. Home → Study → Select position → View range matrix → Inspect hand
2. Home → Courses → Browse → Filter → Select course
3. Home → Practice → Start session → Answer spot quiz → See score
4. Home → ICM → Set stacks → Calculate → View results
5. Cross-app: Study (range) → Practice (quiz) → Train (review)
6. Navigation persistence: deep-link → use app → go back
7. Home Page Feature Discovery
8. Responsive Layout Check
9. Node Lock Solving: Spot → Configure → Solve
```

### pwa.spec.ts — 14 tests (Infrastructure Layer)

```
Classes: PWAPage (constructor: page)
1. Service worker registration
2. Web app manifest presence and validity
3. Installability requirements
4. Offline functionality (when SW caches content)
5. App shortcuts (manifest shortcuts)
6. Theme colors and display modes
7. Mobile viewport handling (390px)
(+ 7 more — icons, splash screen, meta tags)
```

## Playwright Configuration

Config at `apps/web/playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // CI: browsers at /tmp/pw-browsers, server started externally
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run dev',
        url: 'http://localhost:3000',
        reuseExistingServer: true,
        timeout: 120 * 1000,
      },
});
```

Key decisions:
- Single browser (Chromium) — no mobile Safari or Firefox coverage
- 1 worker — sequential execution, no flaky parallel state
- 0 retries — expects deterministic results; retries mask flaky tests
- `CI=true` disables webServer config — production server managed externally
- Screenshots on failure only — no visual regression baseline (intentional gap)

## Execution

```bash
# One-time browser install
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright install chromium

# Run all tests
CI=true PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright test

# Single file
CI=true PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright test apps/web/e2e/equity.spec.ts

# Single test by line number
CI=true PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright test apps/web/e2e/equity.spec.ts:12
```

## Known Pitfall: Nested node_modules

The `e2e/` directory contains its own `node_modules/` with a local `@playwright/test`
package. When running Playwright from the workspace root, the nested package can
shadow the workspace-level playwright, causing "No tests found" errors.

**Symptoms:**
```
Error: No tests found
    at .../e2e/workflows.spec.ts:1:1
```

**Root cause:** The `playwright.config.ts` sets `testDir: './e2e'`, but if there's
a `node_modules/@playwright/test` at `e2e/node_modules/`, Playwright resolves from
the nested location instead of the workspace root.

**Fix:**
```bash
# Remove nested node_modules (they're not needed — deps managed at workspace root)
rm -rf apps/web/e2e/node_modules

# Or run from within apps/web directory
cd apps/web && PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright test
```

**Prevention:** Add `e2e/node_modules` to the project's `.gitignore` and ensure
CI/clean-install workflows don't recreate it.

## API Proxy Filtering

The Next.js rewrites proxy API calls to localhost:8000 (FastAPI). When the backend
isn't running, tests that check console errors must filter expected proxy failures:

```typescript
const criticalErrors = consoleErrors.filter(
  (e) => !e.includes("favicon")
    && !e.includes("404")
    && !e.includes("500")
    && !e.includes("Failed to fetch")
    && !e.includes("Failed to load resource")
);
```

This was applied to `icm.spec.ts` and `spots.spec.ts`. The filter admits false
negatives (a real 500 from the backend would be ignored) but prevents false
positives when running without the Docker stack.

## Related References

- `gto-wizard-e2e-audit-2026-06-14.md` — Full test quality audit (assertion types,
  tautological assertions, defensive no-op patterns, gaps)
- `gto-wizard-e2e-fixes.md` — Complete catalog of fix patterns (stale selectors,
  API proxy ports, mobile overflow, PWA navigation)
