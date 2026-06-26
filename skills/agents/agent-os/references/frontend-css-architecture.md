# Frontend CSS Architecture & Bento Theme Guide

## CSS/Build Architecture

**Tailwind is NOT a direct dependency.** The frontend has no `tailwindcss` in `package.json`. Styles come from `@nous-research/ui` which uses `tailwind-merge` internally.

**How styles are applied:**
1. `src/index.css` → `@import '@nous-research/ui/styles/globals.css'` → Vite bundles into `dist/assets/index-*.css`
2. Components use inline Tailwind arbitrary-value classes (e.g. `bg-[#FFF5E6]`) — these are NOT from a Tailwind config, they're manually written utility class names
3. No PostCSS config, no Tailwind config needed in the frontend itself

**Vite build** (inside running container):
```bash
docker exec -e NODE_PATH=/app/node_modules agent-os-backend /app/node_modules/.bin/vite build /home/sean/.hermes/agent-os/apps/dashboard/frontend
```

**Deploy compiled assets (host patch dir → container via docker cp):**
```bash
# 1. Clean old assets from host patch dir
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "rm -f /home/sean/.hermes/agent-os-patched/frontend-dist/assets/*"

# 2. Copy built assets to persistent host directory (docker cp from container to host)
docker cp agent-os-backend:/home/sean/.hermes/agent-os/apps/dashboard/frontend/dist/assets/. /home/sean/.hermes/agent-os-patched/frontend-dist/assets/
docker cp agent-os-backend:/home/sean/.hermes/agent-os/apps/dashboard/frontend/dist/index.html /home/sean/.hermes/agent-os-patched/frontend-dist/

# 3. Restart backend (picks up new assets from volume mount)
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "cd /home/sean/.hermes/agent-os && docker compose restart backend"
```

**Full build-and-deploy workflow:**
```bash
# 1. Build inside running container
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost \
  "docker exec -e NODE_PATH=/app/node_modules agent-os-backend /app/node_modules/.bin/vite build /home/sean/.hermes/agent-os/apps/dashboard/frontend 2>&1 | tail -10"

# 2. Deploy to persistent patch dir (docker cp from container to host)
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost \
  "rm -f /home/sean/.hermes/agent-os-patched/frontend-dist/assets/* && \
   docker cp agent-os-backend:/home/sean/.hermes/agent-os/apps/dashboard/frontend/dist/assets/. /home/sean/.hermes/agent-os-patched/frontend-dist/assets/ && \
   docker cp agent-os-backend:/home/sean/.hermes/agent-os/apps/dashboard/frontend/dist/index.html /home/sean/.hermes/agent-os-patched/frontend-dist/"

# 3. Restart backend
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "cd /home/sean/.hermes/agent-os && docker compose restart backend"
```

**Shortcut — run inside container via docker exec:**
```bash
docker exec agent-os-backend bash /tmp/build-deploy-frontend.sh
# See scripts/build-deploy-frontend.sh
```

**Google Fonts** (loaded in `apps/dashboard/frontend/index.html`):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
```

## CSS Import Order — CRITICAL

Vite enforces `@import` must precede ALL non-@charset statements. This order works:
```
/* Google Fonts MUST be first */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@...');

/* Then @nou-research/ui */
@import '@nous-research/ui/styles/globals.css';

/* Then rest of Bento overrides */
```

Putting font-face declarations or other rules before the `@import` statements causes build failure.

## Bento Theme Application

Since there's no Tailwind config to extend, Bento design tokens are applied as **pure CSS in `index.css`**:
- CSS custom properties (`:root { --color-bg-primary: #FFF5E6; ... }`)
- Override classes (`.bento-card { background: #FFFBF5; border: 1px solid #F0E6D8; ... }`)
- Button, badge, input, table, progress component classes

### CRITICAL — `html,body` Background Override

`@source "."` in `@nouix/ui` generates low-specificity `html,body{@apply bg-background}` rules that resolve **after** CSS custom properties. This means `:root{--background:#FFF5E6}` gets overridden by the equivalent of `html,body{background:#FFFBF5!important}`.

**You MUST use an explicit `html,body` rule with `!important`** to beat it:

```css
/* index.css — MUST be at the top of the file */
html,body { background: #FFF5E6 !important; }
```

Python script approach (preferred for precision):
```python
path = '/home/sean/.hermes/agent-os/apps/dashboard/frontend/src/index.css'
with open(path) as f:
    content = f.read()
content = "html,body { background: #FFF5E6 !important; }\n" + content
with open(path, 'w') as f:
    f.write(content)
```

**Verification:**
```js
getComputedStyle(document.body).backgroundColor  // → rgb(255, 245, 230) = #FFF5E6 ✓
```

### Vite Build Cache — CRITICAL for New Components

When adding **new React components** (e.g., stat cards, new page sections), the Vite cache at `node_modules/.vite` inside the container must be cleared BEFORE rebuilding. Without this, the new components compile into the bundle but don't appear at runtime.

**Always clear cache before rebuilding when adding components:**
```bash
docker exec agent-os-backend rm -rf /home/sean/.hermes/agent-os/apps/dashboard/frontend/node_modules/.vite
```

**Signs you need to clear the cache:**
- A React component exists in the source `.tsx` file
- The component string appears in the built JS bundle (`grep "ComponentName" dist/assets/index-*.js`)
- But the component doesn't appear in the DOM or renders with 0 bounding box

### IMPORTANT — Override `@import` processed rules with `!important`

`@import` rules are processed BEFORE all other CSS rules. A `:root {}` block appended to `index.css` has the **same specificity** as the imported `globals.css` and gets overridden by it. **You MUST use `!important`** to override `@nous-research/ui` CSS variables.

**Preferred: Python script** — copy a Python script into the container and run it for precise string replacements. Far more reliable than `sed` for multi-line edits involving quotes.

**Fallback: sed** — for simple single-line replacements:
```bash
docker exec agent-os-backend sed -i 's/old/new/g' /home/sean/.hermes/agent-os/apps/dashboard/frontend/src/index.css
```

**Verification in browser console:** `getComputedStyle(document.documentElement).getPropertyValue('--background').trim()` → should return `#FFF5E6`.

**Warm Bento palette values (actual CSS variable names):**
| Token | Value | Usage |
|-------|-------|-------|
| `--background` | `#FFF5E6` | cream page background |
| `--foreground` | `#111827` | near-black text |
| `--card` | `#FFFBF5` | card surface |
| `--border` | `#F0E6D8` | borders/dividers |
| `--muted` | `#F0E6D8` | muted surfaces |
| `--accent` | `#FAD4C0` | peach accent |
| `--success` | `#16A34A` | running state |
| `--warning` | `#D97706` | paused/warning state |
| `--destructive` | `#DC2626` | error/exited state |

**Bento component classes** (defined in `index.css`):
- `.bento-card` — warm card with hover shadow
- `.bento-grid` — CSS grid container with 16px gap
- `.bento-badge` — pill badge with warm tones
- `.bento-bar-fill` — progress bar fill with accent color
- `.btn-primary/secondary/danger/ghost` — warm button variants
- `.btn-bento-*` — additional Bento button variants
- `.input-bento` — warm input field with peach focus ring
- `.shadow-bento-sm/md/lg/xl` — warm shadow scale
- `.divider-bento` — gradient horizontal divider
- `.bento-focus` — peach focus ring utility
- `.data-table` — striped table with warm borders
- `.progress-bar/.progress-fill` — usage bars
- `.animate-fadeIn` — fade-in animation

### Bento-ifying a Page — Conversion Pattern

To convert a flat-list page (e.g., CronPage, ProfilesPage) to Bento card grid:

1. Wrap the list item in a `bento-card` div:
   ```tsx
   // Before: <Card>...</Card>
   // After:
   <div className="bento-card bg-[#FFFBF5] border border-[#F0E6D8] rounded-2xl p-5 flex flex-col gap-3">
     ...card content...
   </div>
   ```

2. Wrap the full list in a `bento-grid`:
   ```tsx
   <div className="bento-grid">
     {items.map(item => (
       <div className="bento-card ...">...</div>
     ))}
   </div>
   ```

3. Fix any closing `</Card>` tags → `</div>`

4. Fix empty states: wrap in `bento-card` too

5. After editing, ALWAYS clear Vite cache and rebuild:
   ```bash
   docker exec agent-os-backend rm -rf /home/sean/.hermes/agent-os/apps/dashboard/frontend/node_modules/.vite
   ```

## Frontend Crash Patterns

### 1. I18nContext missing Provider (Root cause of 3 crashes)
- `I18nContext` default `t = {}` — every `t.common.X` returns `undefined`
- Crashed Sessions, Chat, and Cron pages
- **Fix**: `context.tsx` uses cached Proxy-based safe i18n; `App.tsx` no longer wraps with `I18nContext.Provider`

### 2. `getModelName` returning empty string for null models
- `getModelName(null)` returned `""` → `"" || t.common.unknown` evaluated to Proxy object
- `Proxy.split("/")` threw `TypeError`
- **Fix**: `getModelName` returns `"—"` for null/undefined; callers use `model?.split("/").pop() ?? "—"`

### 3. ChatSidebar — `info.model.split("/")` on object
- `info.model` is an object, not string — `.split()` crashes
- **Fix**: `getModelName(info.model)` wrapper

### 4. FilesPage — React Error #31 on mtime
- `new Date(null)` → Invalid Date rendered as React child
- **Fix**: `file.mtime ? new Date(file.mtime).toLocaleString() : '—'`

### 5. ChatPage SSE EventSource — React 19 StrictMode double-invocation
- `gatewayClient.sessions SSE` opened twice, creating duplicate subscriptions
- `.clear()` on Map during cleanup caused "Item not found" errors
- **Fix**: `= new Map()` instead of `.clear()` in `gatewayClient.ts`

### 6. ContainerPage — React Error #31 "object is not valid as a React child" + `typeof x === object` TSX trap
- Docker API returns `Ports` as a JSON string (e.g. `'[{"IP":"127.0.0.1","PrivatePort":3001,"PublicPort":1331,"Type":"tcp"}]'`)
- Frontend rendered it directly as `{c.Ports}` — JS engine parsed it to an object, then React tried to render the object as a child
- **First fix attempt FAILED**: used `typeof c.Ports === object` (bare identifier) → `ReferenceError: object is not defined`. In TSX, bare identifiers are treated as variables, not JS language keywords.
- **Correct fix**: Use `"object"` string literal in an IIFE:
  ```tsx
  {c.Ports && (() => {
    const ports = typeof c.Ports === "object" ? c.Ports : JSON.parse(c.Ports || "[]");
    if (!ports || ports.length === 0) return null;
    return (
      <H2 variant="sm" className="text-[#6B7280] font-mono">
        {ports.map((p: any) =>
          p.PublicPort ? `${p.PublicPort}:${p.PrivatePort}/${p.Type}` : `${p.PrivatePort}/${p.Type}`
        ).join(", ")}
      </H2>
    );
  })()}
  ```
- Also update the TypeScript type: `Ports: string | Record<string, unknown>[] | null`

### 7. ModelsPage — `aux?.main?.provider` null guard
- **Error**: `Cannot read properties of undefined (reading 'provider')`
- **Root cause**: `aux` from API is `{}` (empty object), so `aux.main` is `undefined`. `aux?.main?.provider` still evaluates the left-to-right chain and throws when accessing `.provider` on `undefined`.
- **Also affected**: `main?.provider === provider` in ModelCard's `isMain` check; `a?.provider === provider` in `aux.find()` callback
- **Fix** — normalize at component boundary, not at each access site:
  ```tsx
  // At the render level, normalize before passing to children:
  main={aux?.main ?? { provider: "", model: "" }}
  aux={aux?.tasks ?? []}

  // Inside ModelCard, use TWO optional chains:
  const mainProv = aux?.main?.provider ?? "";  // aux?.main?.provider, NOT aux?.main.provider
  const mainModel = aux?.main?.model ?? "";

  // isMain check:
  const isMain = !!main && main?.provider === provider && main?.model === entry.model;

  // aux.find callback:
  const mainAuxTask = aux.find((a) => a?.provider === provider && a?.model === entry.model)?.task ?? null;
  ```
- **TypeScript note**: `aux` is typed as `AuxiliaryModelsResponse | null`, so `aux?.main?.provider` is technically type-safe — the runtime issue is that the API sometimes returns `aux = {}` (empty object, not null), making `aux.main` be `undefined` at runtime despite the type saying `main?: {...}`

## Chat Page
- Direct navigation to `http://localhost:1331/chat` loads the page and shows "Session token unavailable" (expected — must open via dashboard flow)
- Embedded chat panel in sidebar works correctly
- Page does NOT crash

## Build Artifacts (deployed)
- JS: `index-EXr5Xu2a.js` (~1,200 KB, Bento warm theme)
- CSS: `index-CZI-AOVL.css` (~15.42 KB, full Bento grid system + !important overrides)

## Persistence — Volume Mount Override (Recommended)

Container's `/home/sean/.hermes/agent-os/` is ephemeral — fixes survive `docker restart` but NOT `docker compose up --force-recreate`.

**Simple persistence approach — volume mount override:**

1. Build the patched frontend bundle in the running container
2. Copy the built dist to a user-writable host directory:
```bash
mkdir -p /home/sean/.hermes/agent-os-patched/frontend-dist/assets
cp /tmp/patched-dist/assets/* /home/sean/.hermes/agent-os-patched/frontend-dist/assets/
cp /tmp/patched-dist/index.html /home/sean/.hermes/agent-os-patched/frontend-dist/
```
3. Add a volume mount to `docker-compose.yml` backend service that overrides the baked-in dist:
```yaml
# In backend service volumes section (after the agent-os :ro bind):
- /home/sean/.hermes/agent-os-patched/frontend-dist:/app/apps/dashboard/frontend/dist:ro
```
4. `docker compose up -d backend` — this survives `--force-recreate`

**Why this works:** The backend's `index.js` resolves `../../frontend/dist` relative to its own `__dirname` in the baked image. The volume mount overlay replaces that path at runtime without needing a custom image build.
