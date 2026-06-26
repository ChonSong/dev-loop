# agent-os Dashboard Debug: Blank Page with Empty Exception

**Date:** 2026-05-04
**URL:** `http://localhost:1332`
**Symptom:** Blank page, `#root` has 0 children, `{"message": "", "source": "exception"}` in console

---

## What I Found

### Network (3 requests, ALL succeeded HTTP 200)
| URL | Size | Duration |
|-----|------|----------|
| `http://localhost:1332/` (HTML) | 552B | 162ms |
| `http://localhost:1332/assets/index-D-84fo57.js` | 269KB | 27ms |
| `http://localhost:1332/favicon.ico` | 552B | 12ms |

**No API calls made** — the app crashes before any `fetch()` to `/api/docker/containers/json` or `/api/system/uptime`.

### Page State
- Title: `agent-os dashboard`
- `#root` div: empty (0 children)
- `document.readyState`: `'complete'`
- No React error overlay visible
- `window.onerror`: `null`
- `performance.getEntriesByType('resource')`: all resources loaded successfully

### The Exception
```json
{"message": "", "source": "exception"}
```
- `message` is **empty string** — this is a V8 artifact for certain error types in minified bundles
- `window.onerror` is null — no global handler installed by the app
- The error fires **before** any `window.onerror` handler can be installed (module-level synchronous throw)
- All capture methods (error listeners, console interceptors, MutationObserver) failed to get details

### Bundle Analysis (reverse-engineered via Python urllib)
- **React 19.2.5** (`react.production.js` + `react-dom-client.production.js`)
- **Remix router v1.23.2** (`@remix-run/router`)
- **lucide-react** icons
- Entry: `X1.createRoot(document.getElementById("root")).render(g.jsx(f0.StrictMode,{children:g.jsx(bp,{})}))`
- `StrictMode` enabled (double-render in development, not production)
- Routes: `/containers` (default), `/appstore`, `/files`, `/tools`, `/settings`
- Suspicious dead code: `new Promise(()=>{})` injected between router utility functions
- `gp()` function checks `window.__HERMES_DASHBOARD_EMBEDDED_CHAT__` and `window.__HERMES_DASHBOARD_TUI__` flags

### Backend Context
```
docker logs agent-os:
  Server running on port 9120
  Error: No API key configured for provider 'None'.
  (from nanobot backend, unrelated to dashboard render)

docker ps --format '{{.Names}} {{.Ports}} {{.Status}}':
  agent-os         0.0.0.0:1331->8900/tcp, 0.0.0.0:1332->9120/tcp  Up 27m (healthy)
  agent-os-nanobot 127.0.0.1:8900->8900/tcp, 9120/tcp               Up 3h (unhealthy)
  agent-os-postgres Up 3h (healthy)
```

The dashboard serves on **port 9120 inside container**, mapped to **1332 on host**. The backend Express server serves the React build + has an SPA fallback for all non-API routes.

### What DID NOT Work
- `window.onerror` override — never fires for module-level synchronous throws
- `window.addEventListener('error')` — same
- `window.addEventListener('unhandledrejection')` — same  
- `console.error` interceptor — never captures
- React error overlay search (`react-error-overlay`, shadow DOM) — not found
- MutationObserver on `#root` — fires nothing (render never starts)
- `browser_vision` on screenshots — returns "no image attached" (tool limitation)
- Screenshot file size check — confirmed blank (~3KB PNG)

### What MIGHT Work Next
1. Run the dashboard via **dev server** (`npm run dev` in `/home/sean/.hermes/agent-os/apps/dashboard/frontend`) to get sourcemapped errors
2. Check TypeScript compilation errors in `apps/dashboard/frontend/src` — tsconfig path aliases (`@/*`) need vite config to resolve
3. Check `window.__HERMES_DASHBOARD_TUI__` flag — `gp()` returns `false` without it, which affects chat panel conditional rendering but shouldn't crash
4. Check if the Docker container's `PORT=9120` environment variable is being read correctly by the backend

---

## Key Lesson

**When all capture methods fail on a blank React page:** the error is at **module initialization time** — before React's error handlers attach, before the first `createElement` call. The `{"message": "", "source": "exception"}` with null `window.onerror` is the signature of a module-level synchronous throw. Next step is always: run the dev server to get sourcemapped errors. Don't keep trying browser capture techniques — they have hit their ceiling.
