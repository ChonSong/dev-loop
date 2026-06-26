# HWC E2E via SSH: Container → Host Chrome Pattern

## Context

The HWC Docker container (Debian 13, `hermeswebui` user) lacks `libglib-2.0.so.0` and other system libraries needed to run Chromium/Playwright browsers. The host (EndeavourOS/Arch) has `google-chrome-stable` and Playwright installed.

## Solution: `playwright.remote.config.ts`

Create a separate Playwright config that targets the host's HWC server via the Docker bridge IP:

```typescript
// e2e/playwright.remote.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://172.19.0.1:3005',  // Docker bridge → host
    headless: true,
    viewport: { width: 1440, height: 900 },
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
  timeout: 30000,
  workers: 1,
  reporter: [['list']],
})
```

## Running Tests

From the host (via SSH from container):

```bash
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "cd ~/.hermes/hermes-web-computer/e2e && \
   npx playwright test --config=playwright.remote.config.ts"
```

## Key Details

- **`172.19.0.1`** is the Docker bridge gateway IP (the host). This is NOT `localhost` — it reaches the host's HWC server from inside the container.
- **Server must be running** on host port 3005 before tests run (`playwright.remote.config.ts` has no `webServer` config).
- **Tests read files from host's copy** of the repo at `~sean/.hermes/hermes-web-computer/e2e/`
- **`workers: 1`** is required — HWC's WebSocket multiplexer doesn't handle concurrent test contexts.
- **`fullyParallel: false`** avoids WebSocket connection conflicts between tests.

## Verification

```bash
# Check server is up
curl -s -o /dev/null -w '%{http_code}' http://172.19.0.1:3005/
# Should return: 200

# Run smoke tests
ssh ... "npx playwright test tests/smoke.spec.ts --config=playwright.remote.config.ts"
```

## When to Use

- E2E testing from the HWC container
- Any container that lacks Chrome/Chromium system dependencies
- When you need the host's Chrome for headless screenshots
