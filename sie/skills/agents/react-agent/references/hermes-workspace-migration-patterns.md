# Hermes Workspace → Agent-OS Migration Patterns

## Overview

The hermes-workspace (`github.com/outsourc-e/hermes-workspace`) is a TanStack Start + React + Tailwind + Electron desktop app with 341 TSX files (~190K lines). Migrating its components to agent-os (Vite + React + Tailwind SPA) requires systematic conversion.

## Migration Conversions Applied

### Import Transformations
| Source | Target |
|--------|--------|
| `@tanstack/react-router` → `useNavigate` | `react-router-dom` or inject `navigate` callback prop |
| `@tanstack/react-query` → `useQuery`, `useMutation` | `useState` + `useEffect` + `fetch` |
| `@hugeicons/react` | `lucide-react` (12 icon mappings: BotIcon→Bot, Rocket01Icon→Rocket, etc.) |
| `@base-ui/react/*` | Standalone React implementations with context + portals |
| `electron` imports | Remove or replace with browser APIs (`window.location.reload()`) |
| `~/` path prefix | `@/` |

### Pattern Transformations
| Source Pattern | Target Pattern |
|----------------|----------------|
| `'use client'` directives | Remove (not needed in Vite SPA) |
| TanStack Router `useNavigate` | `react-router-dom` or `window.location` |
| TanStack Query hooks | Manual fetch + `useState` loading flags |
| Named exports | Default exports (`export default function`) |
| Inline prop types | TypeScript `interface` declarations |
| Complex state machines | Simplified `useState`/`useReducer` |

## Dependency Gaps

The following packages exist in hermes-workspace but NOT in agent-os:
- `recharts` (dashboard charts)
- `motion/react` (animations)
- `@monaco-editor/react` (code editor)
- `@react-three/*` (3D visualizations)
- `xterm` + addons (terminal)
- `@tanstack/react-query` (state management)
- `@tanstack/react-router` (routing)

**Before integrating migrated components:**
1. Install missing npm packages
2. Create stub files for missing internal modules (hooks, utils, types)
3. Verify no remaining `@tanstack`, `@hugeicons`, or `@base-ui` imports
4. Run `npx tsc --noEmit` to confirm compilation

## Staged Integration Strategy

1. **Start with small UI components** (switch, collapsible, toast, dialog) — these have minimal dependencies
2. **Move to page-level components** (dashboard-screen, mcp-screen) — these need more stubs
3. **Finally tackle complex screens** (chat-screen at 84K, chat-composer at 115K) — these need the most dependencies

## Verification Checklist

After each page replacement:
```bash
cd /opt/data/agent-os/apps/dashboard/frontend
npx tsc --noEmit 2>&1 | head -20
```

If compilation succeeds, rebuild:
```bash
cd /opt/data/agent-os && npm run build --workspace=@agent-os/dashboard-frontend
```

If build succeeds, redeploy and verify in browser.

## Migration Results (2026-05-10)

36 components migrated to `/opt/data/repo-transmute-v2/data/migrated/`:
- Chat: 10 components (~435KB)
- Dashboard: 8 components (~93KB)
- MCP: 3 components (~41KB)
- Settings: 3 components (~92KB)
- Agents: 5 components (~51KB)
- UI: 7 components (~24KB)

Full catalog: `github.com/ChonSong/features-list`
