---
name: ui-qa-pipeline
description: Visual regression testing and UI QA with Puppeteer — screenshot diff, console error audit, a11y checks, and full pipeline
---

# UI QA Pipeline

Automated visual QA for UI development using Puppeteer + pixel-level diffing.

## Critical: QA Tests Rendered DOM, Not Source Code

**Never grep source files and call it QA.** Checking that a `.tsx` file contains the string `"UTG"` does not verify the page renders correctly. Real QA must:

1. Launch a real browser (Puppeteer/Chromium)
2. Navigate to the running page
3. Query the **rendered DOM** for elements, text, and structure
4. Check visibility, not just existence
5. Detect JS errors, console errors, and failed HTTP requests

The old `gto-vision-qa.py` was a grep checker misnamed as "vision QA." It reported 0 issues on broken pages because source code strings don't correlate with rendered output.

## Selector Strategy: Content-Based, Not Class-Based

**Don't use `data-testid` or semantic class names** unless you've verified they exist in the actual rendered DOM. Most Tailwind-based projects use utility classes like `w-[38px] h-[38px]` — not `class="hand-matrix"`.

**Use content-based selectors instead:**
- Button text: `button` elements with exact or `startsWith` text match
- Input placeholders: `input[placeholder*="Range"]`
- Heading text: `h1, h2, h3` with text content
- Label text: `label` elements

**Emoji-prefixed buttons** (common in modern UIs): Buttons like `"📥Import"` need `startsWith` matching — exact match for `"Import"` won't work. Use a 3-tier fallback: exact → startsWith → includes.

**Always dump the DOM first** when writing selectors for a new project:
```javascript
const info = await page.evaluate(() => ({
  buttons: [...document.querySelectorAll('button')].map(b => b.textContent?.trim()),
  inputs: [...document.querySelectorAll('input,textarea')].map(i => i.placeholder),
  headings: [...document.querySelectorAll('h1,h2,h3')].map(h => h.textContent?.trim()),
  labels: [...document.querySelectorAll('label')].map(l => l.textContent?.trim()),
}));
```

## Setup (one-time)

Puppeteer's Chromium fails in this minimal container due to missing system libs. The fix:

```bash
# Download & extract Debian packages for Chrome's missing deps
# Script at /tmp/install-chrome-deps.sh (already run — libraries at ~/.local/chrome-libs/lib)
export LD_LIBRARY_PATH="/home/hermeswebui/.local/chrome-libs/lib"
```

The wrapper `/home/hermeswebui/.local/bin/puppeteer-node` sets this automatically.

## Using the QA Tool

**Location:** `/workspace/ui-qa-tool/ui-qa.js` (symlinked as `ui-qa`)

```bash
# Single page snapshot
ui-qa snapshot http://localhost:3000/login login-page

# Pixel diff against reference
ui-qa diff refs/login.png snapshots/login.png

# Full audit (console errors, a11y, perf)
ui-qa audit http://localhost:3000/login

# Check selectors exist
ui-qa check http://localhost:3000/login --selectors=h1,.nav,#main

# Full pipeline — define pages in ui-qa-pages.json
ui-qa pipeline http://localhost:3000
```

## Defining Pages for Pipeline

Create `ui-qa-pages.json` in the project root:

```json
{
  "home": "",
  "login": "/login",
  "dashboard": "/dashboard"
}
```

Each key = page name, value = URL path relative to base URL.

## Workflow

```bash
# Initial run (no refs yet) — captures references
ui-qa pipeline http://localhost:3000

# After changes — detects regressions
ui-qa pipeline http://localhost:3000

# Failed checks produce a -diff.png showing changed pixels in red
```

## CI Integration

```bash
ui-qa pipeline $BASE_URL --viewport=desktop && \
ui-qa pipeline $BASE_URL --viewport=mobile
```

Exit code 0 = pass, 1 = visual regression detected.

## Console Error Investigation

When the pipeline reports errors (`⚠N errors` in output), find the details:

```bash
cat $UI_QA_SNAPSHOTS/<page>@desktop-errors.json
```

### Common error patterns

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| `e.map is not a function` | API returns wrapped object `{items: [...]}` but frontend expects raw array | Unwrap response: `Array.isArray(d) ? d : d?.items \|\| []` |
| `Failed to load resource: 500` | Backend endpoint broken | Check server logs for SQL/import errors |
| `Navigation timeout of 30000 ms exceeded` | Page hangs on API call or heavy render | Increase timeout or reduce API complexity |
| React error #31 (objects) | State contains `{value,label}` objects rendered directly | Access `.value`/`.label` properties in JSX |

### 99% Pixel Diff = Page Was Previously Broken

A 99%+ diff is NOT a regression — it means the page was showing an error state when the reference was captured and now renders properly. **Fix:** delete the stale reference from `$UI_QA_REFS` and re-run the pipeline to capture a clean baseline. Do NOT treat this as a failure.

## HWC-Specific Pitfalls

### Visual QA Scripts Target Wrong Port

HWC's `scripts/visual-qa.sh` and `scripts/run-visual-qa.sh` both hardcode `http://localhost:3113` — the legacy agent-os port. HWC runs on port **3005**. Before running visual QA:

```bash
# Fix the port in both scripts
sed -i 's/localhost:3113/localhost:3005/g' scripts/visual-qa.sh scripts/run-visual-qa.sh
```

### Playwright Browsers Path

HWC stores Playwright browsers at `/home/hermeswebui/.hermes/hermes-web-computer/.playwright/` (project-local), not the default system path. The `PLAYWRIGHT_BROWSERS_PATH` env var must be set or tests will fail with "browser not found".

### HWC E2E Pre-existing Failures

Three tests have been failing since before v1.4 and are NOT regressions:
1. `a11y/contrast.spec.ts:58` — Playwright `page.evaluate()` multi-arg API compat
2. `chaos/concurrent.spec.ts` — outdated `.bg-gray-950` selector
3. `chaos/ws-flood.spec.ts:95` — WebSocket CONNECTING state race

Do not treat these as new failures in regression reports.

When running QA against a Next.js dev server after source changes, you may see `400` errors for `/_next/static/chunks/app/...` and `ChunkLoadError` in console. This is the dev server serving stale chunk hashes — **not a real page error.**

Filter these in your QA code:
```javascript
// In console error handler
if (text.includes('Failed to load resource') && text.includes('400')) return;

// In HTTP response handler
if (url.includes('/_next/static/chunks/')) return;

// In page error handler
if (err.message?.includes('ChunkLoadError') || err.message?.includes('Loading chunk')) return;
```

Fix: clear `.next` cache and restart the dev server.

### `networkidle0` Timeout on Heavy Pages

Pages with many DOM elements (300+ buttons) may never reach `networkidle0` because the dev server keeps connections open. Use `domcontentloaded` instead:
```javascript
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.evaluate(() => new Promise(r => setTimeout(r, 2000))); // Let React hydrate
```

### Browser Connection Crashes

Running many pages in sequence can exhaust the browser process. Restart every 5 pages:
```javascript
if (pageCount > 0 && pageCount % 5 === 0) {
  try { await browser.close(); } catch(e) {}
  browser = await launchBrowser();
}
```

Add retry logic (3 attempts) around each page test to handle transient crashes.

### Pages Missing H1 Headings

Some pages may lack an `<h1>` title while all others have one. Check with:
```javascript
const h1 = await page.$eval('h1', el => el.textContent.trim()).catch(() => null);
```
If missing, it's a real bug — add the heading to the page component.

## Scripts

| Script | Purpose |
|--------|---------|
| `/workspace/ui-qa-tool/qa-suite-v2.js` | Full QA suite — 127 checks across 14 pages |
| `/workspace/ui-qa-tool/dom-inspector.js` | Dump rendered DOM structure for selector discovery |

Run `dom-inspector.js` first when writing selectors for a new project. Use its output to build the check list for `qa-suite-v2.js`.

## Port Management

Old `next start` processes create zombie IPv6 listeners that don't die with `kill -9`. They must be found via `/proc/net/tcp6` socket inodes:

```bash
# Find PID holding port (hex: 8555 = 0x216B)
cat /proc/net/tcp6 | grep "216B" | awk '{print $10}' | while read inode; do
  for f in /proc/*/fd/*; do
    link=$(readlink $f 2>/dev/null)
    if echo "$link" | grep -q "$inode"; then
      kill -9 $(echo $f | cut -d/ -f3)
    fi
  done
done
```

Easier workaround: use a fresh port for each test run (8560, 8561, 8562...) instead of fighting zombies on 8555.

## Pipeline Timing

- 14 pages × desktop viewport: ~4-5 minutes
- First run (no refs) is fastest — just snapshots
- Subsequent runs add pixel diffs (slower per page)
- Pages with API calls that return empty data (404/500) take the same time as working pages

The container lacks shared libraries needed by Chromium. The fix:

1. Download matching `.deb` packages from Debian Trixie
2. Extract to `~/.local/chrome-libs/`
3. Set `LD_LIBRARY_PATH` before running

Re-running the fix: execute `/tmp/install-chrome-deps.sh`. Already installed: 121 .so files at `~/.local/chrome-libs/lib/`.

## Env Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROME_PATH` | auto-detected from Puppeteer | Chrome binary path |
| `UI_QA_SNAPSHOTS` | `./ui-qa-snapshots` | Output dir |
| `UI_QA_REFS` | `./ui-qa-refs` | Reference screenshots |
| `LD_LIBRARY_PATH` | must include chrome-libs | System libs for Chrome |
