# GTO Wizard Clone — 2026-06-01 Update

## Project State

**Location**: `/tmp/gto-wizard-clone/` — **EPHEMERAL, will be wiped on container restart**
**Git**: 1 commit (`7b58866`), no remote configured
**Tests**: 139+ passing in <4s (deck, hand, hand_history, bomb_pot, plo4, plo5, omaha_hi_lo, shortdeck, double_board, range). Full suite 500+ tests but Monte Carlo equity/ICM tests are slow (timeout at 120-300s).

## Architecture

### poker-core (`packages/poker-core/src/gto_poker/`)
- `deck.py` — Card, Deck, parsing (32 tests passed)
- `hand.py` — NLH hand evaluation (35+ tests passed)
- `plo4.py` / `plo4_range.py` — PLO4 evaluator + range parser (17 tests passed)
- `plo5.py` — PLO5 evaluator (16 tests passed)
- `omaha_hi_lo.py` — Omaha Hi/Lo split pot, 8-qualifier (16 tests passed)
- `shortdeck.py` — Shortdeck rankings, flush > full house (25 tests passed)
- `double_board.py` — Double Board PLO, scoop/chop scoring (9 tests passed)
- `bomb_pot.py` — Bomb Pot game state, straddle round (22 tests passed)
- `equity.py` — EquityCalculator, exact + Monte Carlo (20 tests, slow)
- `icm.py` — ICM calculator, Malmoud-Harville (20 tests, slow)
- `hand_history.py` — Hand history parser (25 tests passed)
- `range.py` — Range parsing and operations (15+ tests passed)

### solver (`apps/solver/`)
- `cfr/engine.py` — MCCFR engine (16 tests passed in 1.3s)
- `cfr/flop_solver.py`, `turn_solver.py`, `river_solver.py` — Street solvers
- `cfr/solve_pipeline.py` — Full pipeline

### API (`apps/api/`)
- `main.py` — FastAPI server stub
- Routers: equity, solver, quiz, hh, plo, double_board, bomb_pot, icm, courses, auth

### Web (`apps/web/`)
- Next.js 15 + React 19 pages for all variants
- 6 E2E test spec files (equity, courses, spots, icm, pwa, strategies)

## Development Plan Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1-2d | Core + all variants (NLH, PLO4, PLO5, Omaha Hi/Lo, Shortdeck, Double Board, Bomb Pot) | Complete |
| 3 | CFR Solver | Complete |
| 4 | Training Mode (quiz) | Partial (models exist, no quiz logic) |
| 5 | Hand History Analysis | Partial (parser exists, no analysis) |
| 6 | ICM Calculator UI | Partial (backend exists, frontend page exists) |

## Critical Issues

1. **Ephemeral storage**: `/tmp/gto-wizard-clone/` will be wiped on container restart. Move to `/workspace/gto-wizard-clone/`.
2. **No git remote**: Work will be lost if not pushed. Configure `ChonSong/gto-wizard-clone`.
3. **Test suite too slow for CI**: Full suite times out at 120-300s. Tag Monte Carlo tests with `@pytest.mark.slow`.
4. **Cron jobs broken**: Both GTO cron jobs erroring (PermissionError on /opt/data/.env + deliver failure).

## Recommended Next Steps

1. Move to `/workspace/gto-wizard-clone/` and configure git remote
2. Fix cron jobs: update workdir, fix deliver, add model/provider explicitly
3. Tag slow tests: `@pytest.mark.slow` on Monte Carlo tests
4. Implement Phase 4 quiz service logic (models and routes already exist)
