# Web Debugging Tool Limitations (May 2026)

## vision_analyze cannot analyze remote HTML URLs

`vision_analyze(image_url="https://example.com/page.html")` → `"Only real image files are supported"`

The vision tool accepts:
- Local file paths (`/absolute/path/to/image.png`)
- `MEDIA:/path/to/file` (platform media delivery)
- HTTP URLs → only if they point to an **image file**, not HTML

**Workaround for verifying remote web pages:**
1. Use Playwright via cron job → write results to file → read file
2. Use Python urllib to fetch and analyze HTML structure
3. Use `execute_code` to check screenshot file size as proxy:
   - `<10KB` = blank/crashed page
   - `>50KB` = content rendered

## Playwright headless Chrome timeout on full browser installs

When Chrome is installed as a **full browser** (e.g., `google-chrome-stable` on Linux) rather than the headless-only Chromium binary:
- `--headless` still requires a display server
- Even with `--no-sandbox --disable-dev-shm-usage`, Chrome hangs on `New Page` for 30-45+ seconds
- Playwright never reaches the `load` event

**Workaround:**
- Use `chromium-browser` headless binary if available
- Use puppeteer instead of playwright (different binary)
- Use Python urllib for HTTP health checks (no browser needed)
- Set a hard timeout on Playwright calls and fall back to urllib when it fires

## Screenshot file reading limitation

`vision_analyze(image_url="/path/to/screenshot.png")` with a **file:// URL** → `"no image attached"`

The tool reads images only when embedded in an agent response, not from filesystem paths passed as URLs.

**Workaround:** Serve the screenshot via a local HTTP server and use the HTTP URL, or use `execute_code` to read and report the file size as a proxy for blank-vs-rendered.

## GitHub Pages live file inspection via GitHub API

When curl is unavailable in container and git clone fails (no CWD):

```python
import urllib.request, base64, json
token = "ghp_..."  # from memory
req = urllib.request.Request(
    "https://api.github.com/repos/ChonSong/hermes-guide/contents/docs/skills-graph.html",
    headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
)
data = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(data['content']).decode('utf-8')
lines = content.split('\n')
print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines, 1):
    if 'CATEGORY_MAP' in line:
        print(f"Line {i}: {line[:80]}")
```

Works without curl or git — token from memory is sufficient.

## skills-graph.html duplicate CATEGORY_MAP case study (May 2026)

**Problem:** All graph nodes clumped at center. No spread layout.
**Symptom:** User reported "all clumped together" — nodes at center of SVG canvas.
**Root cause:** `skills-graph.html` had two `const CATEGORY_MAP` declarations (lines 496 and 802).
JS engine: `Identifier 'CATEGORY_MAP' has already been declared` → module crashed → force simulation never started → nodes at center with no repulsive force.

**Fix workflow:**
1. Used Python urllib + GitHub API to count `CATEGORY_MAP` occurrences in **deployed** file
2. Confirmed 2 instances (line 496 = stub, line 802 = complete block)
3. Wrote `fix_catmap.py` to remove lines 496-801 surgically
4. Pushed commit `2f48051`. Deployed confirmed 1 instance, 5224 lines.
5. Created cron monitor job (6h interval) to catch future console errors

**Verification:** Playwright timed out (Chrome hang). Used curl + GitHub API line counting instead.

**Key lesson:** JS `Identifier already declared` errors crash entire modules. A graph with nodes at center = force simulation never started = check for module-level JS errors first.