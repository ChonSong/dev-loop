---
name: canary-watch
description: Post-deploy monitoring — check deployed URLs for regressions after deploys, merges, or dependency upgrades. Watch HTTP status, console errors, performance, and content.
origin: ECC (adapted for Hermes)
---

# Canary Watch — Post-Deploy Monitoring

Monitor deployed URLs for regressions after deploys, merges, or dependency upgrades.

## When to Activate

- After deploying to production or staging
- After merging a risky PR
- Verifying a fix actually worked
- During a launch window
- After dependency upgrades

## What It Watches

1. **HTTP Status** — is the page returning 200?
2. **Console Errors** — new JS errors that weren't there before?
3. **Network Failures** — failed API calls, 5xx responses?
4. **Performance** — LCP/CLS regression vs baseline?
5. **Content** — did key elements disappear? (h1, nav, footer, CTA)
6. **API Health** — are critical endpoints responding within SLA?

## Hermes Implementation

Use browser tools to check deployed URLs:

```
1. browser_navigate(url)
2. browser_snapshot() — check key elements present
3. browser_console() — check for errors
4. browser_vision(question="Is the page rendering correctly?")  # optional, see pitfall below
5. Compare results against known-good baseline
```

## Pitfalls

### Vision API Quota Errors (429)

`browser_vision` calls Qwen via Alibaba Cloud and can fail with `insufficient_quota` (429). This is NOT a page error — it's an API limit. When this happens:

**Fallback**: Use `browser_snapshot()` alone. The accessibility tree snapshot is usually sufficient to verify:
- Key headings present (e.g., "Dashboard", "Settings")
- Navigation items visible
- No "Error" / "404" / "500" text in the tree
- Expected interactive elements (buttons, inputs) present

If snapshot is inconclusive, use `web_extract` on the URL to get the raw HTML and search for error indicators.

## Alert Thresholds

**Critical** (immediate alert):
- HTTP status != 200
- Console error count > 5 (new errors only)
- API endpoint returns 5xx

**Warning** (flag in report):
- New console warnings
- Response time > 2x baseline

**Info** (log only):
- Minor performance variance
- New network requests (third-party scripts added?)

## Quick Check Workflow

1. `browser_navigate` to the deployed URL
2. `browser_console(clear=true)` to get errors
3. `browser_snapshot()` to verify page structure
4. Compare against expected state
5. Report findings

## Cron Integration

Can be scheduled as a cron job for continuous monitoring:
```
cronjob(action='create', schedule='every 15m', prompt='Run canary watch on https://your-app.com', name='canary-watch')
```
