# Playwright E2E Test Reference

## Config (playwright.config.ts)

```typescript
export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,
  timeout: 30000,
  workers: 1,
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
  use: {
    baseURL: 'http://localhost:3005',
    viewport: { width: 1440, height: 900 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'cd backend && go run ./cmd/server',
    port: 3005,
    reuseExistingServer: true,
    timeout: 15000,
  },
})
```

## Test Categories

| Category | Path | Count | Frequency |
|----------|------|-------|-----------|
| Functional | `e2e/tests/01-*.spec.ts` | 2 | Every commit |
| Workflows | `e2e/tests/workflows/` | 5 | Every commit |
| Chaos | `e2e/tests/chaos/` | 4 | Nightly |
| A11y | `e2e/tests/a11y/` | 3 | Every commit |
| Visual | `e2e/tests/visual/` | 2 | Every commit |
| Perf | `e2e/tests/perf/` | 1 | Nightly |

## Running

```bash
npx playwright test                    # all tests
npx playwright test e2e/tests/01-*.spec.ts  # functional only
npx playwright test e2e/tests/workflows/    # workflows
```

## Screenshot Storage

`e2e/test-results/` — baseline and comparison screenshots.
Vision analysis script: `e2e/scripts/vision_analyze.py`
