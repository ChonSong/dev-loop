---
name: debug-live-website
description: Systematic workflow for diagnosing and fixing visual/functional bugs in deployed web UIs — fetch source, screenshot, analyze, patch, deploy, verify.
---

# Debug Live Website

Debug a deployed web page by combining source analysis with visual screenshots. Covers the full loop: understand the issue → fix → deploy → confirm.

## When to use

- User reports a visual bug, layout issue, or functional problem on a live site
- You need to see what a page looks like before you can diagnose it
- The issue involves client-side rendering (SVG, Canvas, JS-rendered content) that doesn't appear in HTML source alone
- A static site (GitHub Pages, Netlify, etc.) needs JS/CSS fixes

## Meta-rule: verify your verification toolchain first

**Before you diagnose a problem, confirm your diagnostics work.** This session is a case study: Chrome 143's `--screenshot` flag produced corrupted PNGs (header only, no pixel data). I interpreted "empty screenshot" as "the page is broken" and did an unnecessary full rewrite. The page was fine — my verification tool was broken.

**Checklist before assuming the page is broken:**

1. **Validate your screenshot tool** — take a screenshot of a known-working page (e.g. `google.com`) first. If that also comes out blank/corrupted, your tool is broken, not the target.
2. **Check PNG validity** — a valid PNG must contain IDAT chunks. Any screenshot file that's suspiciously small (~21KB at any viewport) is not a real image. Run the IDAT check (see Step 2).
3. **Check file-size heuristics** — for the same page at the same resolution, a rendered capture is typically 8-10x larger than a blank one. Suspiciously small = suspect the tool.
4. **Try an alternative capture method** — `--print-to-pdf` or CDP (see Step 2) before concluding the page is empty.
5. **Ask the user** — if you've tried 2+ capture methods and still can't confirm, describe what you see to the user: "The screenshot tool keeps producing invalid output. The page source and JS validate OK. Could you check <url> in your browser and tell me if the graph renders?"

**Golden rule**: when your instruments disagree with your expectations, suspect the instruments first. A full source rewrite is the last resort, not the default.

## Workflow

### 1. Fetch page source

```bash
curl -sL <url> | head -200          # check <head>, styles, script imports
curl -sL <url> | wc -c             # total size
curl -sL <url> | grep -o '<pattern>'  # find specific elements
```

Look for:
- Inline `<script>` data (JSON blobs, graph data, config)
- External CDN imports (force-graph, d3, React, etc.) — may indicate version issues
- CSS structure and class names
- Single-line JSON data embedded in script tags (common in static generators)

### 2. Take a screenshot

**From inside a container without a browser:** use SSH to the host:

```bash
ssh -i <key> user@host "google-chrome-stable --headless --disable-gpu \
  --virtual-time-budget=10000 \
  --screenshot=/tmp/screenshot.png --window-size=1920,1080 <url>"
```

**CRITICAL**: Use `--virtual-time-budget=10000` for pages with async JS rendering (force-graph, React, Svelte). Without this flag, the screenshot captures the page before the JS finishes rendering — you'll get a blank dark background or skeleton UI instead of the actual content. The flag tells Chrome to wait up to N ms of virtual time for page to settle.

**⚠️ Chrome 143 `--screenshot` bug** — Chrome 143.0.7499.40 writes a placeholder PNG header (IHDR) but NO image data (IDAT chunks). Output is always ~21KB regardless of viewport. Fixes:

**Fix A — combine `--dump-dom --screenshot`** (most reliable):
```bash
google-chrome-stable --headless --disable-gpu --dump-dom --screenshot=/tmp/page.png --window-size=1600,900 <url>
```
`--dump-dom` goes to stdout (discard) but forces Chrome to complete paint.

**Fix B — `--print-to-pdf`** (always works):
```bash
google-chrome-stable --headless --disable-gpu --print-to-pdf=/tmp/page.pdf --window-size=1600,900 <url>
```
>50KB = rendered content.

**Fix C — Chrome DevTools Protocol** via Node.js + `ws` (see `references/chrome-headless-screenshot-workarounds.md`).

### 2b. Alternative: Delegate to a browser subagent

When `web_extract` isn't configured (no extract provider), or SSH access to the host is unavailable or unreliable, you can have a subagent visit the URL with browser automation tools and report back what they see:

```python
delegate_task(
  goal='Visit <url>. Take a full-page screenshot and describe all visual/functional issues you see — layout problems, broken elements, blank areas, JS console errors, misplaced content.',
  context='The user reports issues on this page. Provide a detailed visual and functional assessment. If you can evaluate JS (console errors, typeof checks on global variables), do that too.',
  toolsets=['browser', 'file', 'terminal']
)
```

This works because `["browser"]` toolsets include real Chromium automation that loads JS-rendered pages, fires `fetch()` calls, executes JS, and captures screenshots via CDP — all the things headless Chrome CLI does, but without needing SSH access to a host or fighting with `--virtual-time-budget` timing.

**When to use this**:

| Situation | Use delegate_task browser tools |
|-----------|-------------------------------|
| `web_extract` returns "no provider configured" | ✓ — bypasses missing web provider |
| Page is JS-rendered (React, force-graph, Svelte) | ✓ — real browser executes all JS |
| User is in Hermes WebUI, no host SSH access | ✓ — no host dependency |
| Need visual + functional assessment simultaneously | ✓ — subagent can do both |

**Trade-off**: The subagent returns a text-based summary, not a raw screenshot file you can pass to `vision_analyze`. You're trusting the subagent's visual description. For cases where you need pixel-level analysis, prefer the host-side headless Chrome approach. Use delegation as a quick triage — get the high-level picture fast, then decide if deeper work is needed.

### 2c. PDF line-check (canvas rendering verification)

When debugging canvas-based visualizations (ForceGraph, D3 canvas, HTML5 canvas), `--screenshot` may fail or produce invalid images. Use `--print-to-pdf` and check for PDF line operators to determine if the canvas actually rendered:

```bash
# Capture as PDF
google-chrome-stable --headless --disable-gpu \
  --print-to-pdf=/tmp/page.pdf --window-size=1600,900 <url>

# Check for line operations
python3 -c "
with open('/tmp/page.pdf', 'rb') as f: d = f.read()
line_ops = d.count(b' l ')
cm_ops = d.count(b' cm ')
print(f'Line ops (l): {line_ops}  (>{' '}0 = canvas rendered)')
print(f'Matrix ops (cm): {cm_ops}  (>{' '}0 = canvas element existed)')
if cm_ops > 0 and line_ops == 0:
    print('Canvas exists but EMPTY — nothing was drawn')
elif line_ops > 50:
    print('Canvas rendered with content')
"
```

**Why it works**: Chrome's PDF pipeline serializes canvas content as PDF path operators. `cm` (matrix transform) ops appear for any canvas element. `l` (lineTo) ops only appear when actual content was drawn. An empty canvas has `cm > 0` but `l == 0`. A rendered graph has both.

This technique requires no vision model and no image transfer — just the PDF file and a one-liner Python check. Use it as a **quick sanity gate** before investing in screenshot transfer and vision analysis.

**Validate the PNG** — check for IDAT chunks:
```bash
python3 -c "
import struct
with open('/tmp/page.png','rb') as f: d=f.read()
while (pos:=8)<len(d):
 l=struct.unpack('>I',d[pos:pos+4])[0]; ct=d[pos+4:pos+8]
 if ct==b'IDAT': print('VALID'); break
 pos+=12+l+4
else: print('INVALID - no IDAT')
"
```

**Transfer the screenshot back** (when SCP is unavailable):

```bash
# From host via SSH to stdout, then base64 decode locally
ssh -i <key> user@host "base64 /tmp/screenshot.png" > /tmp/screenshot.b64
python3 -c "
import base64
b64 = open('/tmp/screenshot.b64').read().strip()
b64 += '=' * ((4 - len(b64) % 4) % 4)   # fix padding (base64 requires length multiple of 4)
with open('/workspace/screenshot.png', 'wb') as f:
    f.write(base64.b64decode(b64))
"
```

**Quick proxy for rendering quality**: compare screenshot file sizes. A rendered graph yields a much larger PNG (e.g. 491KB) vs a blank/skeleton page (e.g. 57KB). If the screenshot is suspiciously small, the content likely didn't render.

**Show inline in Hermes WebUI**: Use the MEDIA protocol instead of Drive uploads — `MEDIA:/absolute/path/to/screenshot.png` renders inline with full Markdown support. This avoids the need for Google Drive OAuth setup and works instantly.

**Screenshot file-size heuristic** — compare screenshot sizes as a quick sanity check. For the same graph page, a fully rendered PNG is typically 8-10x larger than a blank/skeleton capture (e.g. 491KB vs 57KB at 1920x1080). A suspiciously small file means the content didn't render — check `--virtual-time-budget`, JS console errors, or CDN availability.

**Analyze visually** using `vision_analyze(image_url='/workspace/screenshot.png')` or the model's built-in vision. Note: `vision_analyze` falls back to an auxiliary vision model; if the active model (e.g. DeepSeek) doesn't support image inputs, try delegating the analysis via `delegate_task` with `["vision"]` toolsets, or switch to a vision-capable model.

### 3. Diagnose

Cross-reference visual issues with the source:

| Visual symptom | Likely root cause |
|---|---|
| All edges gray / same color | `linkColor` hardcoded instead of using per-link value |
| Nodes disconnected / sparse | Edge filter defaults hiding member-of/backbone edges |
| Blank page | JS error from missing CDN or syntax error |
| Layout broken | Missing CSS class, responsive breakpoint issue |
| Content not rendering | Inline JSON parse error, missing data field |

Common force-graph bugs to check:
- `.linkColor(() => '#xxx')` → should be `.linkColor(link => link.color)` to respect per-edge type colors
- `.linkWidth(N)` → should be `.linkWidth(link => link.width)` to respect per-edge type widths
- `edge_filter_default` values — if backbone/`member-of` edges are off by default, most nodes appear disconnected and floating. With them ON (they form complete subgraphs per namespace), the force layout naturally clusters nodes. Set defaults to showcase the graph best on first load.
- `nodeColor(n => ...)` — check that color integers convert to valid hex with `.toString(16).padStart(6,'0')`
- **zoomToFit called too early** — `graph.zoomToFit(400, 60)` fires immediately after construction, but at that point all nodes are still clustered at center. It captures a tiny bounding box, then the simulation spreads nodes off-screen. **Fix**: call zoomToFit only after the simulation settles by using `.onEngineStop()`:
  ```js
  let graphInitialized = false;
  // ... graph chain ...
  .onEngineStop(() => {
    if (!graphInitialized) {
      graphInitialized = true;
      graph.zoomToFit(400, 120); // 120px padding for breathing room
    }
  });
  ```
- **d3ReheatSimulation** — when updating graph data on filter changes via `graph.graphData({...})`, the simulation may not re-layout automatically. Call `graph.d3ReheatSimulation()` after the data update to recalculate positions.
- **Member-of edge complete subgraphs** — a pattern where every node in the same namespace is connected to every other node via `member-of` edges. With N nodes in a namespace, this creates N×(N-1)/2 edges. Compact namespaces cluster nicely but large ones become hairballs — users need toggle controls.

### 4. Fix

```bash
# Clone the source repo
git clone <repo_url>
cd <repo>

# Read and patch
```

Use the `patch` tool for targeted edits. For inline JSON inside a single-line HTML file, use `grep -o` to verify the exact match before patching.

### 5. Deploy & verify

```bash
git add -A
git commit -m "Fix: description of changes"
git push
```

**Wait for deployment** (GitHub Pages: 10–60s). Verify the source is live:

```bash
curl -sL <url> | grep -c '<signature of fix>'   # should be > 0
```

### 6. ⚠️ VERIFY WITH VISION MODEL (REQUIRED — do not skip)

After deploying visual fixes, you MUST verify the result visually using a vision-capable model. Do not rely on source-code checks alone — they cannot catch rendering bugs, JS runtime errors, layout issues, or async-rendered content that appears broken to the human eye.

```bash
ssh -i <key> user@host "google-chrome-stable --headless --disable-gpu \
  --virtual-time-budget=10000 \
  --screenshot=/tmp/verify.png --window-size=1920,1080 <url>"
```

Then analyze the screenshot:

```python
# Copy the file from host via base64 SSH pipeline (see screenshot section above)
# Then:
vision_analyze(image_url='/workspace/verify.png', question='Is the page rendering correctly? List any visual bugs, layout issues, blank areas, JS errors, or broken elements.')
```

**Verification checklist** (run through every item after the vision model responds):
- [ ] Graph nodes are visible and not bunched in a corner
- [ ] Edges have distinct colors by type (not all gray)
- [ ] Filter buttons toggle edges correctly
- [ ] Search/highlight works
- [ ] Detail panel opens on node click
- [ ] No blank/white areas where content should be
- [ ] Stats header shows correct node/edge counts

If the vision model reports issues, fix them before telling the user the deploy is complete. If the vision model cannot analyze the image (e.g. active model like DeepSeek doesn't support image inputs, error: `unknown variant 'image_url'`), delegate the analysis:

```python
delegate_task(
  goal='Analyze this screenshot for visual bugs',
  context='Screenshot at /workspace/verify.png. URL was <url>. Check for rendering issues.',
  toolsets=['vision', 'file']
)
```

If that also fails, rely on file-size heuristics and manual comparison against the known-good screenshot pattern from earlier rounds. A graph that rendered will have visible node clusters at various colors and edge lines; a blank/corrupted page will be nearly uniform dark background plus header text.

If the vision model cannot analyze the image and no workaround succeeds, **say so explicitly**. Do not gloss over the gap or imply verification passed. Tell the user: "I cannot visually verify because [specific reason — model doesn't support images, fallback also failed, etc.]. The page source confirms the fix is deployed correctly, but visual confirmation needs a human eye." This is better than a false "looks good" based on source inspection alone.

| Vision failure mode | Honest response |
|---|---|
| Model doesn't support `image_url` | "My current model can't see images. The fix is deployed and JS validates. Please check <url> in your browser and tell me what you see." |
| Fallback vision model also fails | Same — acknowledge the limitation, don't retry indefinitely |
| Screenshot capture produces invalid file | "Screenshot failed (Chrome bug — no IDAT data). PDF was captured instead but I can't view it. Check the page manually." |

Only mark the deploy as successful after visual confirmation passes.

## Pitfalls

- **JS `let`/`const` temporal dead zone**: When inserting new JS into an existing `<script>` block, `let`/`const` are NOT hoisted. Referencing a variable before its declaration throws a silent `ReferenceError` that breaks the entire page. Always check that all shared variables are declared before your insertion point. See `references/js-declaration-ordering.md` for the full debugging recipe.

- **GitHub Pages deploy delay**: wait 10–30s before verifying. The old version may still be cached. Use `?v=$(date +%s)` cache-busting param or check `curl -sI` for `last-modified` header. If curl shows your fix but headless Chrome still sees old content, the browser itself is hitting a cached version — use `--incognito` or pass a `?v=` param to the actual URL.
- **Headless Chrome error `vaInitialize failed`**: harmless, ignore. Screenshot is still written.
- **SCP between container and host may fail** (SSHD not running in container). Use `cat | base64` via SSH as fallback.
- **Single-line HTML with inline JSON**: hard to diff/read. Use `grep -o` and `sed` for targeted checks. The `patch` tool handles single-line files fine because it does fuzzy matching.
- **Canvas/SVG renderings don't show in HTML source**: you must take a screenshot to see rendered output.
- **force-graph CDN version matters**: the `ForceGraph()(element)` vs `new ForceGraph(element)` API changed between versions. Check the imported version if the graph doesn't render.
- **Don't give up on runtime testing just because the container can't run a browser.** When the container has no working Chromium, the natural reflex is to fall back to static analysis. The user considers that a failure mode — they want runtime evidence. Before accepting "can't test from here", exhaust the options:
  1. SSH to host. For this container, the host is at Docker bridge IP `172.19.0.1` (NOT `localhost` — that gets connection refused). Key is `/home/hermeswebui/.hermes/container_key`, user `sean@172.19.0.1`. Host has `/opt/google/chrome/chrome` and `/usr/bin/node` (v22+ with native `WebSocket`).
  2. Delegate a subagent with `toolsets=['browser', 'file', 'terminal']`. It runs against a real browser toolchain.
  3. Native Node `WebSocket` + Chrome DevTools Protocol from a Node script (full recipe in `references/cdp-native-websocket-recipe.md`).

  Only after exhausting all three is static analysis acceptable. Even then, label the work "static analysis, not runtime" so the user knows what kind of evidence they're getting.
- **`read_file()` returns line-numbered content**: Hermes's `read_file()` tool returns `LINE_NUM|CONTENT` format — the `9876|` prefix is part of the output, NOT part of the actual file! If you read a file with `read_file()`, extract a section, and write it back, the line-number prefixes corrupt the file. **Always use `terminal("cat path")` or `execute_code` with `open(path).read()` when you need raw file content for manipulation.** If you must use `read_file()`, strip the `^\s+\d+\|` prefix before writing back:

  ```python
  # ❌ WRONG — will inject line numbers into the file
  result = read_file(path='file.html', limit=2000)
  content = result['content']
  # ... modify content ...
  write_file(path='file.html', content=content)  # CORRUPTED!

  # ✅ CORRECT — use terminal for raw content
  result = terminal("cat file.html")
  content = result['output']
  # ... modify content ...
  write_file(path='file.html', content=content)  # clean
  ```

  **The specific symptom of this bug**: the corrupted file looks like `   620|   620|  const container = ...` — the line number appears TWICE (once from read_file's format prefix, once as actual injected content). JavaScript fails with `SyntaxError: Unexpected identifier` or `Illegal return statement`.

- **JS `let`/`const` temporal dead zone when inserting code into an existing script**: When adding new JS code to an existing `<script>` block, `let` and `const` declarations are NOT hoisted (unlike `var`). If your new code references a variable that was declared with `let` later in the script, you get a silent `ReferenceError` that breaks the entire script — the page renders nothing, with no visible error unless you check the console. **Before inserting code that references existing variables, find where those variables are declared and ensure the declaration comes BEFORE your insertion point.** If the declaration is far away, either move it earlier or restructure your code to not depend on forward references. The symptom: the page is blank/broken after your change, and `curl` confirms the source is deployed correctly.

- **Large inline JSON in HTML** (>500KB): When injecting large JSON blobs into a `<script>` tag, verify the resulting HTML is valid. Check for:
  - No `</script>` string inside the JSON (would close the script tag early)
  - File still opens and closes with `<script>` / `</script>` exactly once each
  - No `Unexpected identifier` JS errors from corrupted content
  - The browser can actually download and parse the full file before timeout

- **Chrome 143 `--screenshot` produces invalid PNGs** (Chrome bug, observed with Chrome 143.0.7499.40). The flag writes a placeholder file that contains IHDR (image header) but NO IDAT chunks (actual pixel data). The file size is always exactly ~21KB regardless of viewport size. You cannot display or decode this file — it has no image data. **Symptoms**: PNG decodes to 0 bytes, image viewers show blank/corrupted image. **Fixes**:
  - `--print-to-pdf` instead: `google-chrome-stable --headless --print-to-pdf=/tmp/page.pdf <url>` — produces a valid PDF reliably.
  - Chrome DevTools Protocol (CDP) via Node.js + `ws` module for PNG:
    ```
    npm install ws
    ```
    Then use `Page.captureScreenshot` via the WebSocket debugger URL (see `references/chrome-headless-screenshot-workarounds.md` for the full script).
  - Combine `--dump-dom --screenshot` together — the `--dump-dom` output goes to stdout while the screenshot file still writes (sometimes fixes the IDAT issue).
  - If all else fails, file-size heuristic: a rendered graph at 1600x900 produces a 400-500KB PNG; a blank/corrupted capture produces ~21KB.

- **`--virtual-time-budget` and `--screenshot` interaction**: with very large inline data (1MB+ JSON), virtual-time-budget can cause Chrome to exit before the page paint completes because VTB freezes real-time progress and synchronous script execution doesn't count toward virtual time. For JS-heavy pages, try `--screenshot` without VTB, or use CDP with a generous delay before capturing.

- **CDP navigation timing**: When using CDP to debug a live page, don't pass the URL as a Chrome CLI argument. Start Chrome with `about:blank`, connect via WebSocket, then use `Page.navigate` to load the target URL after the CDP session is established. This ensures you don't miss the `Page.frameNavigated` event and can properly time your Runtime.evaluate calls. Common timing bug: evaluating JS too early (before scripts finish loading) returns `null` for elements that exist in the HTML. Wait 6-8 seconds after navigation for CDN scripts and inline JS to finish, or listen for the `Page.loadEventFired` event.

- **Edge type mismatch in graph data**: If a static JSON data file contains edge types not present in the filter/edge_types definition, those edges are silently excluded from rendering but still inflate raw counts. Debug by comparing `new Set(data.edges.map(e => e.type))` against the defined types.

## Related

- `dogfood` — exploratory QA (finding bugs)
- `systematic-debugging` — general code debugging discipline
- `garrytan-investigate` — root cause debugging workflow

## References

- `references/force-graph-patterns.md` — detailed force-graph API patterns (zoomToFit timing, per-edge colors, search, filter toggles)
- `references/screenshot-rendering-tells.md` — quick heuristics for whether a headless Chrome screenshot captured real content vs skeleton (file sizes, common failure modes)
- `references/chrome-headless-screenshot-workarounds.md` — Chrome 143 screenshot bug fixes: CDP script, PDF fallback, --dump-dom workaround, and PNG validation
