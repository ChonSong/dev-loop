# Phase 5 Summary — Electron Desktop Shell (2026-05-14)

## What was built

### `desktop/` — Electron app

| File | Purpose |
|------|---------|
| `src/main/index.ts` | Main process: window management, system tray (Tray + nativeImage), app menu (Agent-OS, Edit, View, Window, Help), IPC handlers, single-instance lock (`requestSingleInstanceLock`), auto-start (`setLoginItemSettings`), minimize-to-tray |
| `src/preload/index.ts` | Context-isolated `electronAPI` bridge: `getBackendURL`, `isDev`, `setBackendPort`, `setAutoStart`, `setMinimizeToTray` |
| `vite.config.mts` | `vite-plugin-electron` builds ONLY main+preload (frontend pre-built separately) |
| `package.json` | electron-builder: mac dmg/zip, win nsis, linux AppImage/deb |
| `dist/main/index.js` | Built main process (4.85KB, CJS with `require('electron')`) |
| `dist/preload/index.js` | Built preload (0.44KB) |

### Go backend static file serving

`backend/ws/multiplexer.go` `Router()` automatically detects and serves `../frontend/dist`:
```go
for _, distPath := range []string{"/opt/data/hermes-web-computer/frontend/dist", "../frontend/dist", "../../frontend/dist"} {
    if _, err := os.Stat(distPath); err == nil {
        fs := http.FileServer(http.Dir(distPath))
        mux.Handle("/", fs)
        break
    }
}
```
This enables single-binary distribution — the Go server serves both API and frontend.

## Key Technical Decisions

### vite-plugin-electron pattern

**Critical insight:** The vite config must NOT try to rebuild the Svelte frontend. The Svelte frontend is built separately (`cd frontend && npm run build`). The Electron vite config only builds the electron main+preload TypeScript files.

Working `vite.config.mts`:
```typescript
import electron from 'vite-plugin-electron'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    electron([
      {
        entry: resolve(__dirname, 'src/main/index.ts'),
        onstart(options) { options.startup() },
        vite: { build: { outDir: 'dist/main', rollupOptions: { external: ['electron', 'electron-store', 'electron-log'] } } }
      },
      {
        entry: resolve(__dirname, 'src/preload/index.ts'),
        onstart(options) { options.reload() },
        vite: { build: { outDir: 'dist/preload', rollupOptions: { external: ['electron'] } } }
      }
    ])
  ],
  root: __dirname,  // Keep root as desktop dir so 'vite' resolves from node_modules
  build: {
    outDir: 'dist/electron',
    emptyOutDir: true
  }
})
```

The `root: __dirname` (desktop dir) is critical — without it, Vite tries to resolve `vite` from the wrong location and fails with `UNRESOLVED_IMPORT` for 'vite'.

### vite-plugin-electron `.mts` extension required

The vite config MUST use `.mts` extension (not `.ts`). TypeScript's ESM `import` statements don't work in `.ts` files without `--experimental-specifier-resolution=node`. Using `.mts` avoids this.

### index.html stub required

Vite build requires an `index.html` at root even when using vite-plugin-electron for main+preload only. Created a minimal stub:
```html
<!DOCTYPE html><html><head></head><body></body></html>
```

### Dev vs Prod loading

In main process:
```typescript
if (isDev) {
  await mainWindow.loadURL('http://localhost:5173')  // Vite dev server
  mainWindow.webContents.openDevTools()
} else {
  await mainWindow.loadURL('http://localhost:3113')  // Go backend (serves frontend/dist)
}
```

## Build workflow

```bash
# 1. Build frontend (once)
cd /opt/data/hermes-web-computer/frontend && npm run build

# 2. Build electron main+preload
cd /opt/data/hermes-web-computer/desktop && npm install --legacy-peer-deps
npx vite build

# 3. Package for distribution
cd /opt/data/hermes-web-computer/desktop
npm run build:mac   # creates .dmg
npm run build:win   # creates .exe
npm run build:linux # creates .AppImage

# 4. Run electron app
# In dev: cd desktop && npm run dev (starts vite build then electron .)
# In prod: Go backend must be running on port 3113 first, then electron loads it
```

## electron-store for settings persistence

```typescript
const store = new Store<{
  backendPort: number
  autoStart: boolean
  minimizeToTray: boolean
  launchMinimized: boolean
  windowBounds?: { x?: number; y?: number; width?: number; height?: number }
}>({ defaults: { backendPort: 3113, autoStart: false, minimizeToTray: true, launchMinimized: false } })
```

Settings survive app restarts. Window bounds are saved on every resize/move (but NOT when maximized).

## Common issues fixed

1. **`UNRESOLVED_IMPORT` for 'vite'** — `root` was pointing to `../frontend`. Fixed: set `root: __dirname` so Vite resolves `vite` from desktop/node_modules.

2. **Subagent timeout** — Subagents complete all file writes but time out before summarizing. Always check `git status --short` after timeout. The Phase 5 electron files were all written correctly by the subagent despite the timeout.

3. **Duplicate vite.config.ts.bak** — Left over from a failed config attempt. Deleted cleanly before commit.