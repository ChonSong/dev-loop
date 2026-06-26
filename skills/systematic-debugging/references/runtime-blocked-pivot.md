# Runtime-Blocked Pivot — When the Tool Won't Run in the Container

## The Trap

You need a runtime (headless browser, JS engine, network access, native binary) to test/verify Phase 1 evidence. The container is missing the system libs to launch it. You find yourself:

1. `ldd` shows 24 missing libs
2. You `dpkg-deb -x` libglib, libnss, libxcb, libxrandr, libpango, libatomic, libfreetype, libxkbcommon, libpng16, libfontconfig, libxcb-render, libxcb-shm, libxau, libxdmcp, libdatrie, libatk-bridge…
3. `LD_LIBRARY_PATH=/tmp/libs/combined` → 0 missing libs, but `g_once_init_leave_pointer` symbol mismatch → upgrade glib
4. Now hits NSS version mismatch `NSSUTIL_3.108 not found` → upgrade NSS
5. Now hits `FATAL: SkFontMgr_FontConfigInterface.cpp:163] Not implemented` → install fonts + fontconfig
6. `fc-cache -f` succeeds, but even a `data:text/html,<h1>test</h1>` URL times out at 30s

**You are not debugging anymore. You are rebuilding the OS userland in `/tmp/`.**

## The Rule of Three (adapted)

| Attempt | What you tried | Result |
|---------|---------------|--------|
| 1 | Bundled playwright chromium-1223 | 24 missing libs |
| 2 | Download missing libs via dpkg-deb | libpango symbol mismatch |
| 3 | Upgrade glib, NSS, freetype | FATAL Skia font config |
| 4 | Install fonts, configure fontconfig | Data URL times out |
| 5 | Try puppeteer chrome 148 | Same hangs |
| 6 | Try different headless modes (`--headless`, `--headless=new`, `--single-process`) | All hang |

By attempt 3, the right move was to stop. The error mode after attempt 3 was the same shape as attempt 1 ("chrome won't run in this container") — every fix is just uncovering the next missing piece of the same fundamental fact.

## The Pivot

```python
import subprocess
# 1. Fetch the resource
r = subprocess.run(['curl', '-sL', 'https://example.com/'], capture_output=True, text=True)
with open('/workspace/index.html', 'w') as f:
    f.write(r.stdout)

# 2. Extract inline JS/data
import re
js = re.search(r'<script>(.*?)</script>', open('/workspace/index.html').read(), re.DOTALL).group(1)
with open('/workspace/script.js', 'w') as f:
    f.write(js)

# 3. Read it
# (then use read_file, search_files to find patterns, undefined refs, dead code)

# 4. Delegate to a host-capable subagent
delegate_task(
    goal="Test https://example.com/ in a real browser, capture console errors, save screenshot",
    context="Page is at /workspace/index.html, inline JS at /workspace/script.js. I can't run a browser here.",
    toolsets=['browser', 'terminal', 'file'],
)
```

## What Static Analysis Caught (chrome-in-container case)

On a 620KB static site with 604KB of inline JS:

- **0 edges in graph data** (data had `edges` key but destructuring was `links`) — would have shown as blank graph in browser
- **Dead `cluster_centers` / `cluster_radii` fields** — never consumed by the script
- **`n.color.toString(16)` without null check** — would have thrown on any node missing `color`
- **Missing `tags` defensive check** in tag-edge builder
- **`document.getElementById('tag-threshold')` listener** attached before element guaranteed to exist

None of these required a browser to find. All were findable with `search_files` and `read_file`.

## Anti-Pattern: What NOT To Do

- ❌ Add more `--no-sandbox` / `--disable-gpu` / `--single-process` flags after the third attempt
- ❌ Try different bundled chromium versions (puppeteer 148, playwright 1217, playwright 1223) — same missing-libs problem
- ❌ Try `--headless=new` vs `--headless` vs `--headless=old` — different code paths, same fundamental env-block
- ❌ Spend more than 3 attempts on any tool that requires system userland not present in the container
- ❌ Capture the negative claim as a durable rule

## Anti-Pattern: What NOT To Save

**DO NOT save:** "Chromium doesn't work in minimal containers" — environment-dependent, fixable, and would make future sessions refuse to even try in a different (working) container.

**DO save:** "When 3 attempts to make a tool run fail, pivot to evidence the environment CAN produce, and ask the user before proceeding blind."

## Verification

After pivot, the user can:
1. Run the site locally and check DevTools Console
2. Run a CI-based browser test
3. Provide a session where the browser tool works

In all three cases, the static analysis + the browser-validated evidence combine cleanly. The pivot didn't waste the previous work — the 6+ downloaded debs aren't useful, but the curl'd page + extracted JS is.

## Time Cost

| Path | Tool calls | Wall time | Bugs found |
|------|-----------|-----------|------------|
| Force chromium to work | ~15 | 10+ min | 0 (never got runtime) |
| Pivot early (after attempt 3) | ~5 | 2 min | 6+ via static analysis |
| Pivot immediately (no attempts) | ~3 | 1 min | 6+ via static analysis + delegate to host |

**Optimal:** Skip the chromium attempts entirely when you see "24 missing libs." That's the pivot signal.
