---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing. Trigger on: user reports a bug / something is broken / throwing / failing / not working / error / stack trace / asks to debug/diagnose/investigate. Never propose a fix before completing Phase 1."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers + thananon/9arm-skills)
license: MIT
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development, debug-mantra]
---

# Systematic Debugging

## Core principle

**ALWAYS find root cause before attempting fixes. Symptom fixes are failure.**

**The Iron Law:**
```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```
If you haven't completed Phase 1, you cannot propose fixes.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

**Case study: nanobot 413 "File too large"** — See `references/nanobot-413-debug.md`. A bare `except Exception` returned 413 for every request. The real error (`get_media_dir()` raising `OSError`) was silently caught and logged with wrong context. Key lesson: "File too large" error messages that happen on all requests = investigate exception handlers, not body size limits.

**Log Absence as Diagnostic Evidence (May 2026):** When a line that SHOULD appear in logs based on code inspection DOESN'T appear, it is primary evidence of a code path difference — not a logging bug. Compare `agent.log` between a working foreground session and a broken cron session for the same function call. If `"Creating OpenAI client"` appears for foreground but not cron (both reaching the same function), the cron path is taking a different branch upstream. This is more powerful than adding new logging — comparing existing log output across session types reveals the divergence without instrumentation.

**HTML body vs JSON body diagnostic distinction:** When an API returns `"HTTP 404: 404 page not found"` with an HTML body (not JSON), the HTTP request reached a web server (likely a proxy or gateway) that doesn't understand the API protocol — not the intended API endpoint. A JSON API returns structured errors. An HTML "404 page not found" means the request was routed to the wrong server entirely.

**API key discovery pattern:** `MINIMAX_API_KEY` and `MINIMAX_API_KEYB` are DIFFERENT keys (both 125 chars). MiniMax requires `Authorization: Bearer <key>` for `/v1/chat/completions` path and `X-Api-Key` header for `/anthropic/v1/messages` path. If the config resolves the wrong key, the API returns 401 even though the key is valid for its own endpoint.

**Cron httpx 404 case study:** See `references/minimax-httpx-404-debug.md`. `"Creating OpenAI client"` absent from cron sessions' `agent.log` despite reaching the same function — log absence revealed code path divergence. Two patches applied (scheduler.py debug logging, run_agent.py HERMES_PROXY logging). Fix direction: force HTTP/1.1 in `_build_keepalive_http_client` for `api.minimax.io`.

**Log Absence as Diagnostic Evidence (May 2026):** When a line that SHOULD appear in logs based on code inspection DOESN'T appear, it is primary evidence of a code path difference — not a logging bug. Compare `agent.log` between a working foreground session and a broken cron session for the same function call. If `"Creating OpenAI client"` appears for foreground but not cron (both reaching the same function), the cron path is taking a different branch upstream. This is more powerful than adding new logging — comparing existing log output across session types reveals the divergence without instrumentation.

**HTML body vs JSON body diagnostic distinction:** When an API returns `"HTTP 404: 404 page not found"` with an HTML body (not JSON), the HTTP request reached a web server (likely a proxy or gateway) that doesn't understand the API protocol — not the intended API endpoint. A JSON API returns structured errors. An HTML "404 page not found" means the request was routed to the wrong server entirely.

**API key discovery pattern:** `MINIMAX_API_KEY` and `MINIMAX_API_KEYB` are DIFFERENT keys (both 125 chars). MiniMax requires `Authorization: Bearer <key>` for `/v1/chat/completions` path and `X-Api-Key` header for `/anthropic/v1/messages` path. If the config resolves the wrong key, the API returns 401 even though the key is valid for its own endpoint.

**The Layered Failure Pattern (CI Pipeline Debugging):**

When fixing multi-stage CI pipelines, fixing one failure often reveals failures in the next. Key lessons:

1. **Don't assume the pipeline is fixed after one commit** — wait for CI to fully complete before declaring success. The observability pytest failure (66 vs 67 rounding) was invisible while mypy was failing earlier.

2. **CI environment differs from local in subtle ways**: Local hermes had `npm config omit=dev` + `NODE_ENV=production` masking devDeps. CI uses `uv pip install -e packages/nanobot` installing the real package with actual imports — more accurate than source-only analysis.

3. **Pytest collection errors surface after earlier failures are fixed**: When mypy fails, pytest also fails (collection errors from missing optional deps in nanobot tests), but this is invisible. Once mypy passes, pytest collection errors immediately surface. Always check: are there failures below the first failure line?

4. **CI not triggering is a separate problem**: If pushing a fix doesn't produce a new CI run, the push may not have triggered the workflow. Force with a trivial tracked-file change or dispatch via GitHub API.

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Hermes Agent Investigation Patterns

### Remote Repo Inspection via GitHub API

When you cannot `git clone` (no CWD, network constraints, or credential issues), use Python's `urllib` to inspect repos directly:

```python
import urllib.request, json, base64

token = "ghp_..."  # from memory

def gh_api(path):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/{path}",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def ls(path):
    data = gh_api(f"contents/{path}")
    return data if isinstance(data, list) else []

def get_file(path):
    data = gh_api(f"contents/{path}")
    return base64.b64decode(data['content']).decode('utf-8', errors='replace')
```

- `ls("")` → root directory listing
- `get_file("path/to/file.md")` → file content as string
- `gh_api("git/trees/HEAD?recursive=1")` → full tree (use sparingly, rate-limited)

**Key advantage over `gh` CLI:** Works without pre-configured git credentials. Token in memory is sufficient.

### CWD Workaround (container environment)

The `terminal` tool hardcodes CWD to `/home/sean/workspace`. If that path doesn't exist, every command fails with `FileNotFoundError` — and no `cd` command can recover it.

**Always verify CWD first** in a new session:
```python
import os
os.path.exists(os.environ.get('PWD', '/opt/hermes'))
```

**Use `execute_code` (Python subprocess) as the reliable fallback:**
- `execute_code` defaults CWD to `/opt/hermes` (always exists inside container)
- `terminal` defaults CWD to `/home/sean/workspace` (host bind, may not exist)
- If `terminal` fails with `FileNotFoundError`, immediately switch to `execute_code` for all work

**Always use full path to hermes binary** (not on PATH):
```python
subprocess.run(['/opt/hermes/.venv/bin/hermes', 'chat', '-q', 'hello'])
```

### Service Health Checks (no curl)

When `curl` is unavailable (common in minimal containers), use Python's `urllib`:
```python
import urllib.request
try:
    r = urllib.request.urlopen('http://localhost:4001/', timeout=3)
    print(f"Rate smoother: HTTP {r.status}")
except Exception as e:
    print(f"Rate smoother: DOWN — {e}")
```

### Cron Job Never-Run Pattern

When a cron job has `last_run_at: null` but is scheduled:
1. Force-run to test: `hermes cron run <job_id>`
2. Check if the script path exists on the host (cron jobs run on host, not container)
3. Verify `$HOME` paths resolve on host (`/home/sean/` not `/root/`)
4. Check the job prompt for container-vs-host context confusion

**Overnight Autonomy Engine — Dead Path Case Study**

Job `c9aa6d0bef3b` (`systematic-debugging` skill) runs `cd /home/sean/workspace && python3 scripts/overnight_engine.py` on schedule `0 15 * * *`. Two problems:

1. `/home/sean/workspace` doesn't exist inside the container — every `terminal` call would have failed silently
2. `scripts/overnight_engine.py` doesn't exist anywhere in the mounted volumes

The job shows `last_status: ok` (scheduler didn't crash) but produced zero output. This is the silent failure pattern. See `references/cron-delivery-failures.md` for full analysis and the non-negotiable delivery testing rule.

### PostgreSQL Network Diagnosis

When PostgreSQL reports "accepting connections" but is unreachable:

```
docker ps -a | grep pg                    # is container running?
docker logs <pg-container> --tail 20     # startup logs
ss -tlnp | grep 5432                    # host listening?
docker exec <pg-container> ss -tlnp      # container listening?
docker network inspect <net>             # which network?
docker inspect <pg-container> --format "{{range .NetworkSettings.Networks}}{{.NetworkID}}:{{.IPAddress}}{{end}}"
docker inspect <client-container> --format "{{range .NetworkSettings.Networks}}{{.NetworkID}}:{{.IPAddress}}{{end}}"
```

**Common fixes:**
- If containers on same Docker network: use `postgresql://user:pass@<container-name>:5432/db`
- If hermes uses `--network=host`: use `postgresql://user:pass@127.0.0.1:5432/db`
- If using Docker Desktop: `host.docker.internal` resolves host machine
- If neither works: connect containers to same Docker network (`docker network connect <net> <container>`)
- **Never** use `host.docker.internal` when container uses `--network=host` — container IS the host

### GitHub Credentials for Push Operations

When cron agents need to `git push` to `ChonSong/agent-os`:

**Token vs SSH:** The `ghp_...` token works for HTTPS git operations from any machine — no SSH key needed. Check `~/.git-credentials` on the host to see what's configured.

**Test push access:**
```bash
git ls-remote https://github.com/ChonSong/agent-os.git HEAD
git push -u https://github.com/ChonSong/agent-os.git test-branch
```

**Identity:** Ensure `~/.gitconfig` has correct user.name and user.email before committing:
```bash
git config --global user.name "ChonSong"
git config --global user.email "seanos1a@gmail.com"
```

**Token scope:** The `ghp_...` token from memory works for both read (GitHub API) and push (HTTPS git). Host's stored credentials may be for a different repo (`openclaw-backup`) but work for `ChonSong` repos via HTTPS.

### GitHub API vs Git Clone for Large Diffs

When diff exceeds terminal buffer or session context limits:
1. Use `gh_api("git/trees/HEAD?recursive=1")` for file listing (one API call)
2. Use `get_file("path")` for individual file content (base64 decoded)
3. For full diff: clone with `--depth=1`, generate diff locally, push branch

### Cron Job Chain Dependency Issues

When phases run sequentially (cron-to-cron handoff):
- Each cron is independent — no shared context between jobs
- If Phase N commits code to git, Phase N+1 must `git pull` or `git clone` fresh
- Cron prompts must include `cd /opt/data/agent-os && git pull` before making changes
- If Phase N fails, Phase N+1 will still run on schedule — design prompts to be idempotent or check for prior completion

### Browser DOM State Checks (browser_console)

When debugging blank/rendering issues in a browser session, use `browser_console(expression)` to inspect DOM state directly:

```javascript
// Check if #root exists and has children
document.getElementById('root')  // null = JS crashed before React mount

// Check page title and element count
document.title + ' | root: ' + (document.getElementById('root')?.children.length ?? 'null')

// Check for failed network resources (0-byte or 4xx)
performance.getEntriesByType('resource')
  .filter(r => r.transferSize === 0 || r.responseStatus >= 400)

// Check unhandled errors
window.onerror?.toString()  // may be empty for minified exceptions
```

**Key pattern from blank React page diagnosis:** If `browser_snapshot` shows 0 elements but `browser_console(expression="document.getElementById('root')")` returns null, the JS bundle threw an unhandled exception before React could mount. The browser console may show the exception with no message (minified). The fix path is: verify build compiles clean → check runtime errors via dev server or error boundary → verify all imports resolve.

**See also:** `references/agent-os-dashboard-blank-page.md` — full case study of blank React page with empty exception (production minified bundle, all capture methods failed, dev server was the next step).

When a React app renders as a blank page with `{"message": "", "source": "exception"}` in `browser_console`:

**The `#1 BLANK-PAGE PATTERN FOR React Router v6 apps: Missing `<BrowserRouter>`**

If `App.tsx` uses `<Routes>` (React Router v6) but nothing wraps the app with `<BrowserRouter>`, React Router throws `"useRoutes() may be used only in the context of a Router object"` on mount. This crashes React silently — no visible error, just a blank screen.
- `#root` element exists but has 0 children (React mounts, renders nothing)
- `browser_console` may show `{"message": "", "source": "exception"}` — empty message is a minification artifact
- Container logs show no errors
- API endpoints return correct JSON

**Fix:** Add `<BrowserRouter>` wrapping to `main.tsx` (the entry point, not `App.tsx`):
```tsx
import { BrowserRouter } from 'react-router-dom';
root.render(<BrowserRouter><App /></BrowserRouter>);
```

Also add an ErrorBoundary to prevent silent crashes from propagating to blank screens.

**See also:** `agent-os` skill — `references/react-blank-page-debug.md` has the full case study.

**The `browser_vision` tool cannot read local screenshots** — even valid PNG paths (`/opt/data/cache/screenshots/browser_screenshot_*.png`) return "no image attached." The tool reads images only when embedded in an agent response, not from filesystem paths. **Workaround:** use screenshot **file size** as a proxy — blank pages produce ~3KB PNGs, content-bearing pages produce 50KB+:
```python
with open('/opt/data/cache/screenshots/browser_screenshot_xxx.png', 'rb') as f:
    data = f.read()
print(len(data), 'bytes')  # <10KB = blank, >50KB = content
```
This is a hard limitation of `vision_analyze` with `file://` URLs. Use `execute_code` to inspect binary files directly.

**The `{"message": "", "source": "exception"}` pattern is real and significant.** In production minified bundles, unhandled exceptions from `DOMException`, failed dynamic `import()`, and some third-party libraries report with empty `.message` — this is a V8 stack formatter artifact. It is NOT "no error." Possible causes:
- Dynamic `import()` failure (module not found, CORS, network)
- `DOMException` from browser APIs (`localStorage`, `matchMedia`, etc.)
- Module-level synchronous throw during initialization
- React error boundary throwing before attachment

**Capturing the full stack trace — known limitations:**
- `window.onerror` override → may never fire for module-level errors
- `window.addEventListener('error')` → may never fire
- `window.addEventListener('unhandledrejection')` → may never fire
- `console.error` interceptor → may never capture
- React error overlay → may render to shadow DOM we cannot access
- MutationObserver on `#root` → fires nothing if render never starts

If all capture methods fail and `browser_snapshot` shows 0 elements with an empty `#root`, the error is happening at module initialization time — before React's error handlers attach. **Next step: use Python urllib to reverse-engineer the minified bundle for API endpoints, routes, and import references, then run the app via dev server to get sourcemapped errors.**

**Reverse-engineering a production JS bundle (when dev server unavailable):**
```python
import urllib.request
r = urllib.request.urlopen('http://localhost:1332/assets/index-D-84fo57.js', timeout=5)
js = r.read().decode('utf-8', errors='replace')

# Find createRoot entry point (end of bundle = app bootstrap)
last_create = js.rfind('createRoot')
print(js[last_create-200:last_create+300])

# Find API endpoints called via fetch
import re
for match in re.finditer(r'fetch\(["\']([^"\']+)["\']\)', js):
    print(f"fetch endpoint: {match.group(1)}")

# Find route definitions
for match in re.finditer(r'path:["\']([^"\']+)["\']', js):
    print(f"route: {match.group(1)}")

# Find module imports (dynamic import analysis)
for match in re.finditer(r'import\(['\'"]([^"\']+)['\'']\)', js):
    print(f"dynamic import: {match.group(1)}")
```

**Blank page diagnostic sequence:**
1. `browser_snapshot` → 0 elements + empty `#root`?
2. `browser_console` → any `source: "exception"` entries?
3. `browser_console` → `performance.getEntriesByType('resource')` — did resources load?
4. `browser_console` → `document.readyState` — is it 'complete'?
5. Screenshot file size → <10KB means blank
6. If all resources loaded but blank → reverse-engineer bundle for runtime errors
7. If can't find error → run `npm run dev` locally to get sourcemapped stack trace

**No `curl` in container? Use Python:**
```python
import urllib.request
r = urllib.request.urlopen('http://localhost:1332/', timeout=5)
print(f"HTTP {r.status} | {dict(r.headers)['Content-Type']}")
print(r.read(300).decode('utf-8', errors='replace'))
```

**`file` command unavailable** — `file /path/to/screenshot.png` returns `command not found`. Use Python read or screenshot file size instead.

### GitHub Credentials for Push Operations

When system shows degraded behavior (`Connection refused`, missing files, silent failures):
```python
subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
```
98%+ disk causes cascading failures. Check before investigating individual services.

### Container vs Host Context

Many tools behave differently inside vs outside the container:
| Tool | Inside Container | On Host |
|------|-----------------|---------|
| `docker` | NOT available (container's docker socket is not mapped) | Available |
| `git` | Available | Available |
| `curl` | Often NOT available | Usually available |
| `python3`/`urllib` | Available (use for HTTP checks) | Available |
| Service ports | Services bind to container localhost | Services bind to host localhost |

**For service health checks from inside the container, use Python. For host-level operations (docker, docker compose), exec into container or run from host.**

### Disk Full Cascade Pattern (98%+ disk causes silent multi-service death)

When disk reaches ~98% capacity, services die silently and appear as unrelated "Connection refused" errors. This is a cascading failure where each service fails independently due to inability to write logs, fork processes, or access temp files.

**Symptoms:**
- Rate smoother on port 4001: `Connection refused` (died Apr 27)
- Gateway on port 3000: `Connection refused`
- Any service relying on temp files or log rotation

**The pattern:** Multiple unrelated services failing simultaneously with `Connection refused` = investigate disk first.

**Diagnosis from inside container (Python):**
```python
import subprocess
result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
print(result.stdout)
# Filesystem      Size  Used Avail Use% Mounted on
# overlay         461G  426G   11G  98% /
```

**Diagnosis from host:**
```bash
docker system df  # Docker space consumers
df -h /          # Host disk
```

**Recovery order:**
1. `docker system prune -a --volumes` — reclaim Docker space (often 100GB+)
2. Clear old session logs: `find /opt/data/sessions/ -name "*.json" -mtime +30 -delete`
3. Clear Playwright cache: `rm -rf /root/.cache/ms-playwright/`
4. Restart affected services

**Prevention:** Add disk-check to the System Monitor cron job. Alert at >85% usage.

### Service Availability from Inside vs Outside Container

**CRITICAL DISTINCTION:** A service that is UP on the host (`curl http://localhost:4001/` succeeds from host shell) will return `Connection refused` when checked from inside the container — because container localhost ≠ host localhost (unless `--network host` is used).

When verifying services are running:
- From **inside container**: Use Python urllib with the container's own network namespace
- From **host**: Use `docker exec hermes curl localhost:4001/` or run from host shell directly
- If a service appears DOWN from inside but is UP from host → the service is actually running, the verification method was wrong

**Exception:** When container uses `--network host` (as this setup does), container localhost IS host localhost for port bindings. In that case, `Connection refused` from inside truly means the service is down.

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
