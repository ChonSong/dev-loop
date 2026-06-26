# Blank React Page — Diagnostic Sequence

When the browser shows an empty/blank page at a React app URL, follow this exact sequence to isolate the failure point.

## The 5-Step Diagnostic

```python
# Step 1: Verify server is up (Python urllib — curl not always available)
import urllib.request
r = urllib.request.urlopen('http://localhost:1332/', timeout=5)
print(f"Status: {r.status}")
body = r.read(500).decode('utf-8', errors='replace')
print(body)
# Look for: <div id="root"> and <script type="module" src="...">
```

```python
# Step 2: Check server headers and content-type
r = urllib.request.urlopen('http://localhost:1332/', timeout=5)
print(dict(r.headers))
# Content-Type should be text/html; status should be 200
```

```python
# Step 3: Try fetching the JS bundle directly
import urllib.request
try:
    bundle_url = 'http://localhost:1332/assets/index-D-84fo57.js'  # find from HTML
    r = urllib.request.urlopen(bundle_url, timeout=10)
    print(f"Bundle HTTP {r.status}, size: {r.headers.get('Content-Length')}")
except Exception as e:
    print(f"Bundle fetch failed: {e}")
```

```
Step 4: browser_snapshot — confirms empty page
Step 5: browser_console — checks for JS exceptions
Step 6: browser_console expression: document.getElementById('root')
  - If null → React crashed before mount (JS exception)
  - If element exists but has 0 children → React mounted but rendered nothing
```

## Decision Tree

| browser_snapshot | #root in DOM | JS exception | Interpretation |
|-----------------|--------------|--------------|----------------|
| (empty page) | null | yes | JS bundle throws before React mounts |
| (empty page) | exists, 0 children | no | React mounted but App returned null/empty |
| (empty page) | exists, has children | n/a | Content exists but CSS hides it |
| has content | — | — | App is rendering; look at data/API |

## What to Check After Isolation

### JS bundle throws before mount (most common)
- Run `npm run build` locally — does TypeScript compile clean?
- Check `tsconfig.json` — is `baseUrl` present? Are `@/*` path aliases resolving?
- Check for missing stub modules — look for hundreds of TS errors from `src/lib/plugins`, `src/i18n`, etc.
- Check for unhandled promise rejections in `main.tsx` or `App.tsx`

### React mounted but renders nothing
- App component or a root provider is returning `null`
- Check for conditional rendering that's always false
- Check for async initialization that fails silently

### Server returns wrong content-type
- Express static middleware misconfigured
- Vite build output not being served
- Wrong Content-Type prevents browser from parsing the JS

## Real Session Transcript

**Session: 2026-05-04 — Blank page at http://localhost:1332**

Steps run:
1. `browser_navigate` → title: "agent-os dashboard", snapshot: (empty page), 0 elements
2. `browser_console` → 3 JS exceptions, all with empty `message` strings
3. `urllib` (Python) → HTTP 200, valid HTML with `<div id="root"></div>` and module script
4. Bundle fetch via `performance.getEntriesByType('resource')` → JS loaded (HTTP 200, 269KB, 7ms)
5. `browser_console` expression → `document.getElementById('root')?.innerHTML` → `'ROOT MISSING'`
6. `window.React` → `'React NOT loaded'`
7. After fresh navigation: `document.getElementById('root')` EXISTS with 0 children (React mounted!)
8. `window.__react_error` → null (no captured errors)
9. `window.io` → `'io NOT found'` (socket.io-client not in bundle)
10. `browser_console` expression → `document.body.innerHTML` → `<div id="root"></div>` (no other content)
11. External sites work fine in browser (e.g. example.com renders)
12. 3 renderers running, all attached — not a GPU/compositing issue

**Key findings this session:**

- **Two failure modes observed on same URL:** First navigation → `document.getElementById('root')` was `null` (JS threw before mount). Retry → `#root` EXISTS with 0 children (React mounted, rendered nothing). This means the issue is NOT "JS bundle crashes before React" but "React mounts but App returns zero content."

- **`window.React` NOT loaded** — the global `React` variable is not exposed. This is expected in React 19 ESM bundles (no global `window.React`). Do NOT use this as evidence of failure.

- **socket.io-client (`window.io`) not found** — `socket.io-client` is imported in the app's code but was NOT detected in the bundled JS. This could mean: (a) the import was tree-shaken out, (b) the component using it is behind a flag/feature that hasn't rendered yet, or (c) the dynamic `import()` call hasn't fired. Not a primary suspect for blank-page but worth noting.

- **`browser_console` empty exceptions** — `{"message": "", "source": "exception"}` with empty message is NOT the same as no error. In a minified production bundle, the error message gets minified too. Do NOT dismiss this as "no error." The presence of ANY exception from `source: "exception"` is significant.

- **`browser_snapshot` vs actual DOM** — the accessibility tree shows 0 elements even when `#root` exists with children if those children have no accessible content. Use `browser_console` expression to check actual DOM, not `browser_snapshot`.

- **The dist bundle ends correctly:** `X1.createRoot(document.getElementById("root")).render(g.jsx(f0.StrictMode,{children:g.jsx(bp,{})}));` — React init is properly bundled. If you see this at the end of the JS, the build itself is fine.

- **Screenshots can't be read by vision tools** — use `ls -la /opt/data/cache/screenshots/browser_screenshot_*.png` file size as proxy: blank = ~3-4KB, content = 50KB+.

- **Blank + React mounted + 0 children = likely cause:** Either (a) the App component itself returns `null`, (b) a root-level provider throws during render and the error boundary catches it silently, or (c) an async initialization fails before the first render produces content. Check: container logs for unhandled errors, API endpoint availability, and whether `socket.io` connection failure prevents app initialization.

**Diagnosis workflow update:**
```
Step 1: urllib → is HTML served? (yes = server OK)
Step 2: browser_navigate → does it load? (yes = browser can reach it)
Step 3: browser_console expression → document.getElementById('root')?.children?.length
  - null → JS throws before mount → check container logs
  - 0 → React mounted but rendered nothing → check API endpoints + container logs
  - >0 → React rendered → content exists → CSS/visibility issue
Step 4: Check performance entries for JS bundle load status
Step 5: Check container logs for unhandled exceptions (docker logs)
Step 6: If blank + React mounted: verify API endpoints respond with JSON (not HTML)
```

## New Session Findings (2026-05-04, Part 2)

### `npx vite build` direct — bypassing turbo/npm version issues

The host's npm (11.6.4) is incompatible with `package.json`'s `packageManager` field (`npm@10.9.2`). Running `npm run build` fails at the package manager version check. Turbo cache also fails to invalidate on App.tsx changes (cache key unchanged even after `rm -rf .turbo`).

```bash
ssh -i /home/hermes/.ssh/id_ed25519 -o StrictHostKeyChecking=no sean@localhost \
  "cd /home/sean/.hermes/hermes-sync/projects/agent-os/apps/dashboard/frontend && npx vite build"
```

### `docker cp` hot-deploy — getting files into a running container

The container can't pull images. Docker isn't available from hermes. To update a running container without rebuilding:

```bash
# 1. Build on host
ssh -i /home/hermes/.ssh/id_ed25519 -o StrictHostKeyChecking=no sean@localhost \
  "cd /home/sean/.hermes/hermes-sync/projects/agent-os/apps/dashboard/frontend && npx vite build"

# 2. docker cp from host into running container
ssh -i /home/hermes/.ssh/id_ed25519 -o StrictHostKeyChecking=no sean@localhost \
  "docker cp /home/sean/.hermes/hermes-sync/projects/agent-os/apps/dashboard/frontend/dist/assets/index-*.js \
   agent-os:/app/apps/dashboard/frontend/dist/assets/"

# 3. Verify the new bundle is served
curl -s http://localhost:1332/ | grep 'src="/assets/'
```

### Bundle verification via `grep -o`

To verify a fresh build contains expected components:
```bash
docker exec agent-os grep -o "CasaOS\|Sidebar\|ContainerPage\|ChatPanel" \
  /app/apps/dashboard/frontend/dist/assets/index-MARGtVlu.js | head -20
```
String not found = bundle doesn't include that code.

### `gatewayClient.ts` — known silent failure suspect

The `gatewayClient.ts` WebSocket singleton initializes at **module import time** (module-level `new GatewayClient()`). If the WebSocket connection throws during initialization, it fails the entire module graph silently in ESM contexts. Prime suspect for blank pages where React mounts but renders nothing.

```typescript
// apps/dashboard/frontend/src/lib/gatewayClient.ts
// This runs on import — if it throws, the entire import graph fails silently
const gatewayClient = new GatewayClient();
export default gatewayClient;
```

### Blank page persisted with MINIMAL App — what this proves

After restoring the full CasaOS App from git `b766193`, we also tested a minimal App.tsx (white div with "Hello"). The blank page **still occurred**. This confirms:
- The issue is NOT in component code
- The issue is NOT in the number/type of imports
- React can mount (blank but not crashed)
- The problem is likely: module preload failure, ESM execution context, or silent runtime error in a module-level initializer

### Build sizes for reference

| Bundle | App | Size |
|--------|-----|------|
| `index-CjPk0y1G.js` | Minimal (white div) | 193,675 bytes |
| `index-D-84fo57.js` | Full CasaOS (local vite) | 269,343 bytes |
| `index-MARGtVlu.js` | Full CasaOS (host vite) | 219,329 bytes |

Size difference between local and host vite builds is due to different minification/bundling environments. Both are valid.

---

## ROOT CAUSE FOUND (2026-05-04, full resolution)

**The actual root cause: Missing `<BrowserRouter>` in `main.tsx`**

`App.tsx` uses React Router v6 `<Routes>`. Nothing in the component tree provided the router context. React Router throws `useRoutes() may be used only in the context of a Router object` on mount — silent crash, no visible error.

**Fix applied to `apps/dashboard/frontend/src/main.tsx`:**
```typescript
import { BrowserRouter } from 'react-router-dom';

// Wrap <App /> with BrowserRouter
root.render(
  <ErrorBoundary>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </ErrorBoundary>
);
```

**Why it was hard to find:**
- `browser_console` showed empty exceptions — `{"message": "", "source": "exception"}` — easy to dismiss as noise
- Container logs showed no errors
- API endpoints all returned correct JSON
- React mounted (`#root` existed) but rendered nothing
- No sourcemap in production bundle — stack trace useless

**Lessons:**
1. Empty `message` in `source: "exception"` IS an error — don't dismiss it
2. When React mounts but renders nothing, the issue is always a missing context provider or failed root-level initialization
3. For React Router v6: `<Routes>` requires `<BrowserRouter>` somewhere above it in the tree
4. Add ErrorBoundary to `main.tsx` as a safety net — makes render errors visible instead of blank

## New Failure Mode: API Routes Return HTML → Blank Page

**Symptom:** React mounts (root element exists, 0 children), `browser_console` shows `{"message": "", "source": "exception"}`, page is blank.

**Root cause:** The Express backend has **no `/api/*` route handlers** — only `/health` and the SPA fallback (`app.get('*', ...)`). Any `fetch('/api/...')` call from the frontend gets the HTML `index.html` instead of JSON. When the frontend calls `response.json()` on HTML, it throws an unhandled promise rejection that crashes the React component tree silently.

**How to diagnose:**
```python
import urllib.request
for path in ['/api/system/uptime', '/api/docker/containers/json?all=true']:
    r = urllib.request.urlopen(f'http://localhost:1332{path}', timeout=5)
    ct = r.headers.get('Content-Type', '')
    body = r.read(100).decode('utf-8', errors='replace')
    print(f"{path}: {r.status}, {ct} → {body[:80]}")
    # Expected: content-type: application/json
    # Actual: content-type: text/html → BUG
```

**The backend is a stub.** Current `apps/dashboard/backend/dist/index.js` only has:
```javascript
app.get('/health', ...)
app.get('*', ...)  // serves index.html (SPA fallback)
```
Missing entirely: `/api/system/uptime`, `/api/docker/containers`, and 40+ other routes the frontend expects.

**Fix:** Add the missing API route handlers to `apps/dashboard/backend/src/index.ts`. The backend needs expansion to match the frontend's API expectations. See `references/docker-backend-fix.md` for the target architecture.

**`browser_console` with empty message is NOT "no error":** In production minified bundles, unhandled promise rejections from `fetch().then(r => r.json())` failing on HTML often show as `{"message": "", "source": "exception"}` — the empty message is an artifact of minification + V8 stack formatting for rejected promises, not an absence of error. Do NOT treat this as "no error."

## New Failure Mode: `a.Names.replace is not a function`

**Symptom:** Dashboard renders on most pages but shows "App Error" then blank screen on the Containers/Docker page. Error: `a.Names.replace is not a function`.

**Root cause:** Docker Engine API returns `Names` as `string[]` (e.g. `["/agent-os", "/agent-os-nanobot"]`). The frontend's `ContainerPage.tsx` calls `c.Names.replace(/^\//, "")` expecting a `string`. Calling `.replace()` on an array throws.

**How to diagnose:**
```python
import urllib.request, json
r = urllib.request.urlopen('http://localhost:1332/api/docker/containers/json?all=true', timeout=5)
data = json.loads(r.read())
names = data[0]['Names']
print(f"Type: {type(names)}, Value: {names}")
# Expected: <class 'str'>, '/agent-os'
# Actual: <class 'list'>, ['/agent-os'] → BUG
```

**Fix in backend (`apps/dashboard/backend/src/index.ts`):**
```typescript
const normalized = containers.map(c => ({
  ...c,
  Names: c.Names?.[0] || c.Names?.join(',') || ''
}));
res.json(normalized);
```

**This is NOT a frontend bug to fix — normalize in the backend.** The Docker API contract returns arrays; the frontend expects strings. Fix the translation layer, not the consumer.
