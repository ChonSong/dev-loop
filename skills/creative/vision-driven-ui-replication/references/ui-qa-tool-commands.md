# UI QA Tool — Puppeteer Visual Regression Pipeline

**Location:** `/workspace/ui-qa-tool/ui-qa.js`

A Puppeteer-based CLI tool for snapshot-based visual regression testing. Requires:
- Node.js with `puppeteer-core`, `pixelmatch`, `pngjs` installed
- A Chrome/Chromium binary (path configured via `CHROME_PATH` env or hardcoded default)

## Commands

### `ui-qa snapshot <url> <name> [--viewport=desktop|tablet|mobile]`

Full-page screenshot + metadata capture. Writes:
- `snapshots/<name>@<viewport>.png` — full-page screenshot
- `snapshots/<name>@<viewport>.json` — page metadata (title, headings, link/input count, scroll height, console logs)
- `snapshots/<name>@<viewport>-errors.json` — if console errors were captured

Page metadata includes:
```json
{
  "title": "Page Title",
  "url": "https://...",
  "htmlSize": 12345,
  "viewport": { "width": 1440, "height": 900 },
  "scrollHeight": 900,
  "linkCount": 12,
  "imgCount": 3,
  "headings": { "h1": 1, "h2": 3, "h3": 5, "h4": 0 },
  "buttons": 8,
  "inputs": 4
}
```

### `ui-qa diff <ref.png> <current.png>`

Pixel-level comparison between two screenshots. Output:
- Diff image with red pixel overlay (stored at `snapshots/diffs/`)
- JSON result: `{ match, diffPixels, totalPixels, changePct, diffImage }`

### `ui-qa audit <url>`

Full-page audit:
- Console errors (JS errors, network errors)
- HTTP 4xx/5xx response errors (captured via `page.on('response')`)
- Accessibility issues (missing `alt` on images, unlabeled inputs without `aria-label` or matching `<label for>`)
- Performance metrics (DOMContentLoaded time, load time, total DOM nodes)

### `ui-qa check <url> --selectors=h1,.nav,#main`

Verify specific CSS selectors exist and are visible on the page. Reports: selector, found (bool), count, visible count.

### `ui-qa pipeline <base-url> [--viewport=...]`

Full regression pipeline:
1. Reads `ui-qa-pages.json` for page definitions
2. Snapshot each page
3. Compare each snapshot against reference in `refs/` directory
4. Report visual diffs and console errors

**First run** (no references exist): all snapshots are saved as references, report shows "Set as reference".
**Subsequent runs**: each snapshot is pixel-diffed against its reference. Report shows pass/fail per page.

## Env Config

| Env | Default | Purpose |
|-----|---------|---------|
| `UI_QA_SNAPSHOTS` | `./ui-qa-snapshots` | Current run output |
| `UI_QA_REFS` | `./ui-qa-refs` | Baseline references |
| `CHROME_PATH` | Auto-detected Puppeteer Chrome | Chrome binary path |

## Integration with Replication Process

```
1. First deployment → ui-qa pipeline http://BASE  # creates refs
2. Fix a bug
3. Rebuild + restart
4. ui-qa pipeline http://BASE                       # compare against refs
5. Check output for:
   - ❌ Failed: >5% diff → visual regression
   - ⚠ Console errors → JS bugs or API 500s
   - ✅ Pass: <1% diff → no unexpected changes
6. If diff is EXPECTED change (e.g., intentional redesign), 
   copy snapshots to refs to update baseline:
   cp -r snapshots/* refs/
```
