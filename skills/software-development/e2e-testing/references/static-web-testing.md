# Testing Static Web Artifacts

Testing HTML/JS/CSS that deploys to GitHub Pages, S3, or any static host.

## The Core Rule

**Curl is NOT a browser test.** `curl -sI https://... | head -3` verifies the file is deployed. It does NOT verify JavaScript executes, DOM renders, or the UI works. Always test in a real browser before declaring a frontend fix complete.

## Verification Checklist

1. **Deploy verification** (curl acceptable):
```bash
curl -sI "https://chonsong.github.io/hermes-knowledge-graph/" | head -3
# Expect: HTTP/2 200, content-type: text/html
```

2. **File content verification** (curl acceptable):
```bash
curl -s "https://example.com/index.html" | grep "expected-string"
```

3. **JavaScript execution verification** (MUST use browser):
- Playwright `page.goto()` + check for console errors
- SSH to host → run `npx playwright screenshot` 
- Node.js smoke test with Chromium headless

## GitHub Pages Specifics

- Pages serves `index.html` at root by default — arbitrary HTML files need renaming
- GitHub Pages has ~2-3 minute propagation delay after push
- Check Pages build status: repo → Settings → Pages → "last deployment" timestamp
- If using CDN (unpkg, jsDelivr), CDN files are separate from GitHub Pages — verify CDN URL resolves independently

## Browser Testing Options by Environment

| Environment | Method | Command |
|-------------|--------|---------|
| Host has Chromium | SSH + `npx playwright screenshot` | `ssh -i ~/.hermes/container_key sean@172.19.0.1 "cd /repo && npx playwright screenshot --browser chromium http://localhost:3005 /tmp/s.png"` |
| Host has chrome-headless | SSH + direct invocation | `/home/sean/.cache/puppeteer/chrome-headless-shell/... --screenshot=/tmp/s.png http://localhost:3005` |
| Container with Playwright | Python `playwright.sync_api` | `python3 -m playwright install chromium && from playwright.sync_api import sync_playwright` |
| No browser available | Last resort: module syntax check | `curl -s https://cdn.example.com/file.mjs \| head -c 200` — check ESM syntax, but this is NOT a substitute for browser testing |

## Common Failure Patterns

### `t.appendChild is not a function` in force-graph (or similar libraries)

This error means the library is trying to call `.appendChild()` on something that isn't a DOM element. Causes:
1. Wrong initialization pattern — used curried call `ForceGraph()(element)` instead of direct `ForceGraph(element)`
2. UMD module served as `type="module"` — must use ESM build (`*.mjs`) for `<script type="module">`
3. CDN served wrong file — verify with local vendored copy
4. `new` keyword missing — `new ForceGraph(element)` not `ForceGraph(element)`

### Module vs Script Confusion

For `<script type="module">`:
- Use ESM build (`*.mjs`) — has `export` statements
- CDN: `unpkg.com/package@version/dist/file.mjs` or `cdn.jsdelivr.net/npm/package@version/dist/file.mjs`
- NOT the UMD/IIFE `.min.js` build — that won't export correctly as a module

For `<script>` (classic):
- Use UMD/IIFE build (`.min.js`)
- `new ForceGraph(element).graphData(data)` — constructor pattern

## Testing Workflow for Static HTML

```bash
# 1. Deploy
git add index.html && git commit -m "fix" && git push

# 2. Wait for Pages propagation  
sleep 45  # GitHub Pages ~2-3 min to build

# 3. Verify content (curl ok for this)
curl -s "https://user.github.io/repo/" | grep -E "expected-js|expected-css"

# 4. Verify JS execution (MUST use browser)
# Option A: SSH to host with Playwright
ssh -i ~/.hermes/container_key sean@172.19.0.1 \
  "cd /tmp && npx playwright screenshot --browser chromium https://user.github.io/repo/ /tmp/test.png"

# Option B: Python Playwright in container  
pip install playwright && python3 -m playwright install chromium
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on('console', lambda msg: print(f'ERROR: {msg.text}') if msg.type == 'error' else None)
    page.goto('https://user.github.io/repo/', wait_until='networkidle', timeout=30000)
    # verify something rendered
"
```

## Related

- `references/playwright-screenshot-technique.md` — SSH + host Playwright technique
- `references/playwright-direct-invocation.md` — Node.js smoke tests
- `references/stale-locators-hwc-e2e.md` — Selector stability patterns