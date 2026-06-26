# Docker Image Frontend Debugging — agent-os

## Key Finding: Frontend is Baked Into the Docker Image

The frontend is NOT served from the host source mount. It is built into the Docker image at build time.

- **Container serves from**: `/app/apps/dashboard/frontend/dist/` (inside container)
- **Host mount (ro)**: `/home/sean/.hermes/agent-os` → `/opt/agent-os` (NOT what gets served)
- **Build process**: Multi-stage Dockerfile, Stage 1 runs `npx turbo build` to produce the dist

This means:
1. Editing source files on the host does NOT affect the running app
2. To fix frontend bugs: need to rebuild the Docker image and redeploy
3. The `npm run build` inside the container fails (no turbo.json, no tsc installed)

## Known Frontend Bugs (as of 2026-05-07)

### Files Page — React Error #31
- **Symptom**: Clicking Files link → full "App Error" crash
- **Error**: `Minified React error #31` — "Objects are not valid as a React child"
- **Status**: Intermittent — sometimes loads, sometimes crashes
- **Likely cause**: React 19 hydration or object rendered as React child somewhere in FileExplorerPage

### Sessions Page — TypeError: Cannot read properties of undefined (.clear)
- **Symptom**: Navigating to Sessions page → console error `TypeError: Cannot read properties of undefined (reading 'clear')`
- **Likely cause**: `ResizeObserver` or xterm terminal ref cleanup on unmount

### Chat Page — createPortal to document.body
- **Symptom**: Mobile panel portal may fail in React 19 StrictMode
- **Code**: `createPortal(..., document.body)` in ChatPage.tsx and Toast.tsx

## Rebuilding the Frontend

The container has Node 22 and npm 10.9.7 but:
- No `tsc` (TypeScript not installed as dev dependency in runtime image)
- No `turbo.json` (only in source, not in image)
- Build command in image: `npx turbo build` (fails — turbo needs turbo.json)

To rebuild: need to do so on the host with the source, then push a new image:
```bash
# On host — from agent-os source
docker build -t ghcr.io/chonsong/agent-os:latest .
docker push ghcr.io/chonsong/agent-os:latest
# Then restart container: docker compose up -d backend
```

## Browser Testing

Chrome is available at `/usr/bin/chromium` in the hermes container. Use browser tools:
- `browser_navigate(url)` — navigate
- `browser_snapshot()` — get accessible element tree
- `browser_console()` — get console messages and errors
- `browser_vision(question)` / `vision_analyze(image)` — screenshot analysis

Console error format from `browser_console`:
```json
{"type": "error", "text": "{stack: \"...\", message: \"...\"}"}
```
