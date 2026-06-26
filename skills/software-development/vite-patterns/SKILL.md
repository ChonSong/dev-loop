---
name: vite-patterns
description: Vite build tool patterns — config, plugins, HMR, env variables, proxy setup, SSR, build optimization, Docker setup. Critical for agent-os and hermes-web-computer.
origin: ECC (adapted for Hermes)
---

# Vite Patterns

Vite 8+ configuration, plugins, HMR, env, proxy, and build optimization. Covers both agent-os (React) and hermes-web-computer (Svelte).

## When to Activate

- Configuring `vite.config.ts`
- Setting up dev server proxy for API backends
- Optimizing build output (chunks, minification, assets)
- Troubleshooting HMR, dev server, or build errors
- Docker/container Vite setup
- Adding Vite plugins

## Critical Callouts

1. **`vite build` does NOT type-check** — type errors silently ship to production. Add `vite-plugin-checker` or run `tsc --noEmit` in CI.
2. **`VITE_` prefix is NOT a security boundary** — statically inlined into client bundle. Never put secrets in `VITE_` vars.
3. **`vite preview` is NOT a production server** — smoke test only. Deploy `dist/` to real server (NGINX, Cloudflare Pages).

## Config Patterns

### Docker/Container Setup

```typescript
// vite.config.ts — required for container dev
server: {
  host: true,             // bind 0.0.0.0 (localhost unreachable from host)
  hmr: { clientPort: 3000 },  // if behind reverse proxy
}
```

### Dev Server Proxy

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

### Essential Plugins

| Plugin | Purpose |
|--------|---------|
| `@vitejs/plugin-react-swc` | React HMR via SWC (faster than Babel) |
| `@sveltejs/vite-plugin-svelte` | Svelte 5 HMR + runes |
| `vite-plugin-checker` | TypeScript + ESLint in dev (fills type-check gap) |
| `vite-tsconfig-paths` | Honor tsconfig paths aliases |
| `rollup-plugin-visualizer` | Bundle size analysis |

### Build Optimization

```typescript
build: {
  rolldownOptions: {
    output: {
      manualChunks: {
        'react-vendor': ['react', 'react-dom'],
        'ui-vendor': ['@radix-ui/react-dialog'],
      },
    },
  },
}
```

## Performance

### Avoid Barrel Files

```typescript
// BAD — forces Vite to load entire barrel
import { slash } from '@/utils'

// GOOD — only loads the one file
import { slash } from '@/utils/slash'
```

### Warm-Up Hot-Path Routes

```typescript
server: {
  warmup: {
    clientFiles: ['./src/main.tsx', './src/routes/**/*.tsx'],
  },
}
```

### Profile Slow Dev Servers

```bash
vite --profile   # interact, then press p+enter
# Load .cpuprofile in https://www.speedscope.app
```

## Environment Variables

- Only `VITE_`-prefixed vars exposed to client code
- `.env.local` files are gitignored for local secrets
- Use `loadEnv(mode, process.cwd(), ['VITE_'])` in config (explicit prefix)

```typescript
// GOOD: explicit prefix list
const env = loadEnv(mode, process.cwd(), ['VITE_', 'APP_'])

// BAD: '' loads ALL env vars including secrets
const env = loadEnv(mode, process.cwd(), '')
```

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Dev doesn't match build | Always `vite build && vite preview` before deploy |
| Stale chunks after deploy | Keep old `dist/assets/` live for deployment window |
| Docker unreachable | `server.host: true` in config |
| Monorepo file access blocked | `server.fs.allow: ['..']` |
| Stale pre-bundle cache | Delete `node_modules/.vite` after dep changes |
| Splitting every node_module into chunks | Creates hundreds of tiny files — use object form for major vendors only |

## Container/CI npm Cache Pitfalls

When running npm inside a container (Docker, cron job) with a shared `/tmp`:

**Symptom:** `EACCES: permission denied` on npm cache operations because a previous run as root left root-owned files in `/tmp/npm-cache`.

**Fix — use a repo-local cache:** Most repos already have a local `.npm-cache/` directory (often gitignored). Point npm there:

```bash
npm outdated --json --cache=/path/to/repo/.npm-cache
npm run build --cache=/path/to/repo/.npm-cache
```

**Permanent fix (host-level):** Reclaim ownership:
```bash
sudo chown -R $UID:$GID /tmp/npm-cache
```

## Node.js Version Requirements for Tailwind v4

**`@tailwindcss/oxide`** (Tailwind v4's native Rust binding) requires **Node.js ≥ 20.19**. Projects that use Tailwind v4 (`@tailwindcss/vite` or `tailwindcss@^4`) will fail to build on Node 18 with errors like:

```
Error: /node_modules/@tailwindcss/oxide/index.js:573:11
    at Module._compile (node:internal/modules/cjs/loader)
```

### Fix When Only Node 18 Is Available on Host

Install Node 20+ from binary tarball (no root needed):

```bash
# Download and extract to home directory
curl -sL https://nodejs.org/dist/v20.20.0/node-v20.20.0-linux-x64.tar.xz -o /tmp/node20.tar.xz
tar -xf /tmp/node20.tar.xz -C ~
export PATH=$HOME/node-v20.20.0-linux-x64/bin:$PATH
node --version  # v20.20.0
```

Then clean rebuild the frontend (stale Node 18 bindings persist in `node_modules`):

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Why Clean Rebuild Matters

`node_modules` installed under Node 18 contains `@tailwindcss/oxide` binaries compiled for the older ABI. Switching Node versions without reinstalling causes cryptic binding failures. Always delete `node_modules` + `package-lock.json` before `npm install` after changing Node versions.

### Quick Diagnostic

```bash
# Check if your project uses Tailwind v4
grep -r "tailwindcss" package.json | head -3
# Check current Node
node --version
# Test if build will work
npx --yes @tailwindcss/oxide --version 2>&1 | head -3
```

## Build Time Expectations

Large vendor chunks increase build time significantly. In CI/cron automation: set timeouts to at least 120s for Svelte projects with editor components (Monaco, xterm.js push build time to 60–90s). Build still succeeds despite Svelte a11y warnings — these are warnings only, not errors.

## Tracking Outdated Dependencies

`npm outdated --json` shows three version levels per package:

- **`current` ≠ `wanted`:** Safe to run `npm update` — patch/minor within semver range.
- **`wanted` ≠ `latest` (major gap):** Needs package.json bump, changelog review, migration testing. Not safe for auto-update.

Major gaps to watch for in Svelte 5 projects: `@sveltejs/vite-plugin-svelte` (5→7), `vite` (6→8), `@xterm/xterm` (5→6), `typescript` (5→6). These are informational markers — installed versions continue to work; auto-updating major versions in a monorepo can break the build chain.

## Security Checklist

- [ ] No secrets in `VITE_` vars
- [ ] `build.sourcemap: false` in production (or upload to Sentry and delete)
- [ ] `.env.local` in `.gitignore`
- [ ] `loadEnv` uses explicit prefix list, not `''`
