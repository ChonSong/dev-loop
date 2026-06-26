# GTO Wizard Clone — Cron Execution Notes

## Repo Location

- **Current**: `/workspace/gto-wizard-clone/` (moved from `/tmp/` on 2026-06-01 — tmpfs was wiped)
- **URL**: https://github.com/ChonSong/gto-wizard-clone
- **Stack**: Next.js 15/React 19/FastAPI/Python gRPC monorepo
- **Layout**: apps/{web,api,solver} + packages/{poker-core,ui-components,types}

## Cron Job Parameters (as of 2026-06-01)

| Job ID | Name | Schedule | Status | Notes |
|--------|------|----------|--------|-------|
| 5521adb0ed74 | Phase 2 Variant Polish | 15:00, 19:00 daily | Fixed | Skills removed, prompt rewritten as completion check, repeat 1/1. Uses `/workspace/` path. |
| 70eabe13c2e2 | Phase 4+5+6 Final Polish | 16:00, 20:00 daily | Fixed | Lightweight checks only, no Monte Carlo. Uses `/workspace/` path. |

## Key Decisions

1. **Skills removed from both jobs** — loaded skills caused PermissionError in cron context. Inline instructions instead.
2. **Phase 2 repeat set to 1/1** — work is done, one final check then stop.
3. **Phase 4+5+6 uses lightweight checks only** — no Monte Carlo, no hanging tests. Import checks, file existence grep, README status line count.
4. **deliver: local on both** — `origin` fails ("no delivery target resolved"). Accept no chat delivery.
5. **All paths updated to `/workspace/`** — `/tmp/` is ephemeral tmpfs, wiped on container restart.

## Test Suite Status (2026-06-01)

- **Fast tests (all pass, ~3s)**: deck(32), hand(36), range(29), bomb_pot(23), hand_history(38) = 158 total
- **Variant tests (all pass)**: plo4(18), plo5(17), omaha_hi_lo(14), shortdeck(27), double_board(11) = 87 total
- **Slow but passing**: equity (Monte Carlo), icm (prize extension) — avoid in cron, timeout >60s
- **Solver tests (pass, ~1.3s)**: cfr(16)

## Variant Implementation Status

All 7 variants fully implemented and tested:
1. NLH — OMPEval
2. PLO4 — PokerHandEvaluator
3. PLO5 — PokerHandEvaluator 5-card
4. Omaha Hi/Lo — 8-qualifier split pot
5. Shortdeck — flush > full house ranking
6. Double Board PLO — novel, scoop/chop scoring
7. Bomb Pot — novel, straddle round betting

## Frontend Build Status (2026-06-01)

- **Build**: `npx next build` passes — all 18 pages + root prerendered
- **Pages**: `/`, `/analyze`, `/analyze/hands`, `/analyze/leaks`, `/analyze/viewer`, `/bomb-pot`, `/courses`, `/double-board`, `/equity`, `/icm`, `/omaha`, `/plo`, `/spots`, `/strategies`, `/strategy`, `/train`, `/train/review`
- **TS errors fixed** (7 files): HandPlayback.tsx, HandTable.tsx, csvExport.ts, index.ts, StrategyHeatmap.tsx, card.tsx, socket.tsx
- **Key fixes**: `HeadingAttributes` removed (React 19), `Button ghost` → `Button variant="ghost"`, `window.__HERMES_SESSION_TOKEN__` removed, `critters` installed, duplicate `HHCard` export removed, `QuizSocket` type added, strict TS cast fixes
- **npm**: `node_modules` must be installed before build (`npm install`). `critters` dep needed for `optimizeCss`.

## verify_final.py Known Issues (2026-06-01 Fixed)

1. `tracker.adjusted_equity()` → `tracker.adjusted_equity` (changed from method to @property)
2. `model.create_straddle_map(6, 2)` → `model.create_straddle_map([0, 1, 2], {0: 2, 1: 4, 2: 8})` (signature changed: positions List[int], amounts Dict[int, int])