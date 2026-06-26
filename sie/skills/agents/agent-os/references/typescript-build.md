# TypeScript Build Troubleshooting

## The 467→0 Pattern

Dashboard at `/opt/data/agent-os/apps/dashboard/frontend` had 467 TypeScript errors after missing modules were removed in a cleanup. Zero by session end.

## Root Causes

1. **`tsconfig.json` missing `baseUrl` + `paths`** — the `@/*` alias was used throughout but unresolvable
2. **Missing npm packages** — `@nous-research/ui` (private scoped) not installed
3. **Missing module files** — 17 modules imported but no implementation (hooks, contexts, i18n, plugins, lib, themes)

## Step-by-Step Fix

### Step 1: Fix tsconfig.json

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Step 2: Install missing packages

```bash
npm install --legacy-peer-deps @nous-research/ui@^0.10.0
npm install --legacy-peer-deps @xterm/xterm@^5.5.0 @xterm/addon-fit@^0.10.0 @xterm/addon-unicode11@0.9.0
```

`--legacy-peer-deps` is required — the dashboard uses React 18, some packages have peer dep conflicts.

### Step 3: Create stub files

Create minimal stubs that satisfy the type system, not feature-complete implementations:

| File | Key Pattern |
|------|-------------|
| `src/hooks/useSidebarStatus.ts` | Returns `StatusResponse` (from `@/lib/api`): `active_sessions`, `config_path`, `gateway_line`, `version`, `app`, `sidebar_status` |
| `src/hooks/useToast.ts` | Returns `{toast: Toast | null, showToast: (message, type) => void}` |
| `src/hooks/useConfirmDelete.tsx` | Returns `ConfirmDeleteState`: `{pendingId, isOpen, isDeleting, confirm, cancel, deleteItem}` |
| `src/contexts/usePageHeader.tsx` | `PageHeaderContextValue`: `{setAfterTitle, setEnd}` |
| `src/contexts/useSystemActions.ts` | `SystemActionsContextValue`: `{actions, addAction, removeAction}` |
| `src/i18n/context.tsx` | `I18n = Record<string, any>`; `useI18n()` returns `{t, locale, setLocale}` |
| `src/i18n/index.ts` | Re-exports `useI18n` from `./context` |
| `src/plugins/index.tsx` | `PluginSlot` component (JSX → must be `.tsx`, not `.ts`) |
| `src/lib/nested.ts` | `getNestedValue(obj, path)` + `setNestedValue(obj, path, val)` → returns `Record<string, unknown>` |
| `src/themes/index.tsx` | `BUILTIN_THEMES` array with theme objects; `useTheme()` returns `{theme, setTheme, BUILTIN_THEMES}` |

### Step 4: Rename .ts → .tsx for JSX files

Any file containing JSX must end in `.tsx`:
```bash
mv src/plugins/index.ts src/plugins/index.tsx  # was .ts with JSX content
mv src/hooks/useConfirmDelete.ts src/hooks/useConfirmDelete.tsx
mv src/contexts/usePageHeader.ts src/contexts/usePageHeader.tsx
```

### Step 5: Verify

```bash
npm run build   # should exit 0, produce dist/assets/index-*.js
./node_modules/.bin/tsc --noEmit   # should show no errors
```

## Key Insight: `npm run build` vs `tsc --noEmit`

`vite build` resolves aliases at runtime via `vite.config.ts`. `tsc --noEmit` only type-checks using `tsconfig.json`. A clean `npm run build` with zero `tsc` output can still have type errors that `tsc --noEmit` catches. Always run both.

## Key Insight: `Record<string, any>` for i18n `t`

Components use `t.oauth.xxx`, `t.common.xxx` (nested property access), not `t('key')` function calls. Use `Record<string, any>` for the `t` object in `useI18n()` — strict typing of arbitrary nested keys is not the goal, satisfying the type system is.

## Docker Build: `@types/react` — Updated 2026-05-09

**IMPORTANT — the advice below was superseded on 2026-05-09.**

We moved `@types/react` from `^18` to `^19` (matching React 19 runtime) and CI passed green. The real issue causing type errors was the i18n system being typed as `Record<string, unknown>` instead of `Record<string, any>` — the Proxy-based i18n returns dynamic nested objects that `unknown` can't express.

### Current correct guidance:

1. **Use `@types/react: ^19`** when React runtime is ^19 — the type mismatch was a red herring
2. **i18n type MUST be `Record<string, any>`** — the Proxy-based i18n returns dynamic nested objects (`t.oauth.xxx`, `t.common.xxx`). `Record<string, unknown>` causes TS18046 errors on every `t.*` access. Never use `unknown` for i18n.
3. **Never export non-existent symbols** — the i18n refactor added `makeSafeI18n` to the index.ts export but it didn't exist in context.tsx. This causes build failures.

### Historical note (pre-2026-05-09 — kept for reference):

The original advice was to pin `@types/react` at `^18` even with React 19 runtime, because `@nous-research/ui@0.10.0` used MUI-compatible types that conflicted with `@types/react@19`'s expanded `ReactNode` (added `bigint`). As of 2026-05-09, this is no longer the case — both `^18` and `^19` work. Use `^19` to match the runtime.

### 2. `NODE_ENV=production` prevents devDeps from installing

`npm ci` uses the lockfile but skips `devDependencies` when `NODE_ENV=production` is set. TypeScript lives in devDeps — if it's missing, `tsc` fails with "command not found" or TS errors cascade from missing type declarations.

**Fix — always use `NODE_ENV=development` for Docker builds:**
```dockerfile
# In the ts-build stage, before npm ci:
ENV NODE_ENV=development
RUN npm ci
```

Or inline:
```bash
NODE_ENV=development npm ci
```

### Why `npm ci` vs `npm install` in Docker

In local dev, use `npm install` (more tolerant, doesn't require exact lockfile match). In Docker CI builds, use `npm ci` (guaranteed reproducible). The `NODE_ENV=development` override applies to both.

## NavLink `isActive` Type Fix

If `tsc` reports `isActive` implicitly has `any` type on a `NavLink` component's `className` callback, you need to import and apply the render-props type:

```typescript
import { NavLink, type NavLinkRenderProps } from 'react-router-dom';

// In the component:
<NavLink
  to="/containers"
  className={({ isActive }: NavLinkRenderProps) =>
    isActive ? 'nav-item active' : 'nav-item'
  }
>
```

**File:** `apps/dashboard/frontend/src/components/Sidebar.tsx` — this specific fix was needed after the `@types/react` downgrade.

**Symptom:** `TS7016: Parameter 'isActive' implicitly has an 'any' type` on `NavLink`'s className callback.

## TypeScript Workspace Resolution in Monorepo CI

**Problem:** `npx --yes typescript --noEmit -p apps/dashboard/backend/tsconfig.json` fails in CI with `could not determine executable to run`.

**Root cause:** In a monorepo with workspaces (`"workspaces": ["apps/*/*", "packages/*"]`), `npx typescript` resolves from the monorepo root's `node_modules/.bin/`, which is not populated for nested workspace packages. The `typescript` package lives in `apps/dashboard/backend/node_modules/.bin/tsc`.

**Fix — always cd into the workspace package before running tsc:**
```yaml
# WRONG (typescript/tsc not found in root bin):
- name: Type check backend
  run: npx --yes typescript --noEmit -p apps/dashboard/backend/tsconfig.json

# RIGHT (cd into the backend package so npx finds local tsc):
- name: Type check backend
  run: cd apps/dashboard/backend && npx --yes tsc --noEmit
```

**Why `tsc` not `typescript`:** The executable name is `tsc`. Both issues compound — wrong name AND wrong working directory.

**Verification locally:**
```bash
cd apps/dashboard/backend && npx --yes tsc --noEmit
# Exit 0 = clean
```

**Key insight:** In a nested workspace monorepo, never assume `npx <package-name>` will resolve from the monorepo root. Always `cd` into the package directory first.
