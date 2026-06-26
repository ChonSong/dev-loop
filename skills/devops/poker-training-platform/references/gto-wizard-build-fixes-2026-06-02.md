# GTO Wizard Clone — Build Fix Log

## 2026-06-02 Build Fixes (commits `cbe085b` and `5aef5dc`)

### Commit `cbe085b` — Fix TypeScript build errors across 7 files

| File | Error | Fix |
|------|-------|-----|
| `HandPlayback.tsx:367` | `window.__HERMES_SESSION_TOKEN__` — TS type error + SSR crash | Guard with `typeof window !== "undefined"` + `(window as any)` cast |
| `HandPlayback.tsx:527-543` | `<Button ghost>` — invalid prop | Change to `<Button variant="ghost">` |
| `HandTable.tsx:185-186` | Sort comparator type mismatch | Cast: `as unknown as Record<string, unknown>` |
| `HandTable.tsx:329` | Cell render cast | Same intermediate cast pattern |
| `HandPlayback.tsx:84` | `parseCards` cast | Explicit type cast |
| `csvExport.ts:18` | Type cast | Explicit type cast |
| `index.ts` | Duplicate `HHCard` export from barrel | Remove duplicate re-export, keep from original module |
| `card.tsx` | `HeadingAttributes` removed in React 19 | Remove unused import |
| `StrategyHeatmap.tsx:414,489` | `data` possibly undefined in comparison | Add `data &&` guard |
| `StrategyHeatmap.tsx:632` | `indexOf` on `as const` array | Cast: `as typeof RANKS[number]` |
| `useQuizSocket.tsx` | Type/value export mismatch | Add explicit type export |

### Commit `5aef5dc` — Add missing critters dependency

- Next.js 15 requires `critters` for CSS inlining during prerender (`optimizeCss`)
- Error: `Cannot find module 'critters'`
- Fix: `npm install -D critters`

### Post-fix state
- Build: ✅ 3/3 turbo tasks, 20 pages prerendered
- Tests: 78/78 variant tests pass
- Note: `docker compose` plugin not available on host; use `npx turbo build` instead
