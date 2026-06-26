---
name: poker-platform-stack
description: "Domain knowledge for building a poker/GTO training platform (GTO Wizard clone): feature areas, open-source library stack, CFR algorithm notes, HH format overview, and recommended tech stack."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [poker, gto, training, platform, domain-knowledge]
    track: domain
    project: gto-wizard-clone
---

# Poker Platform Stack — GTO Wizard Clone Domain Knowledge

## What GTO Wizard Is
**gto-wizard.com** — subscription SaaS poker training platform. Web + mobile. Core: GTO strategy training via quizzes, hand history analysis, and equity tools.

## Core Feature Areas

| Feature | What it does | Technical component |
|---------|-------------|---------------------|
| **GTO Solver Engine** | Nash equilibrium via CFR (Counterfactual Regret Minimization) | MCCFR algorithm, NumPy/Numba, gRPC service |
| **Equity Calculator** | Hand vs range equity via Monte Carlo + exact enumeration | OMPEval, PokerHandEvaluator, range expansion |
| **Training Quizzes** | Random spots → user guesses GTO action → feedback | Quiz DB, spot randomization, EV loss calc |
| **Hand History Analyzer** | Upload HH files → parse → leak detection vs GTO | HH parsers (PokerStars, GGPoker, Winamax) |
| **ICM Calculator** | Tournament chip equity via Independent Chip Model | Monte Carlo simulation, push/fold charts |
| **Range Builder** | Visual 13x13 grid hand selector | React component, range string parsing |

## Open-Source Libraries (Used in GTO Wizard Clone)

### Poker Engine
- `zekyll/OMPEval` (224⭐, C++) — fast 5-card NLH hand evaluation
- `HenryRLee/PokerHandEvaluator` (501⭐, C++/Python) — PLO4/PLO5/Hi-Lo hand evaluation
- `siavashg87/poker-odds-calc` (99⭐, Node) — multi-variant equity (Hold'em, Omaha, Shortdeck)

### GTO Solver (Custom Implementation)
- No open-source MCCFR solver was suitable — built custom in `apps/solver/cfr/`
- Street progression: preflop → flop → turn → river → showdown
- Chance sampling at each street for incomplete information
- gRPC service for inter-process communication (solver separate from API)

### ICM & Tournament
- `apcode/poker-mtt-icm` (12⭐, Python) — tournament ICM reference
- Custom Monte Carlo ICM implementation for the clone

### Hand History
- `aneopsy/PokerStats` (18⭐, Python) — PokerStars HH parser reference
- Custom parsers in `packages/poker-core/src/gto_poker/hand_history.py`

## Game Variants Supported

| Variant | Evaluator | Notes |
|---------|-----------|-------|
| NLH | OMPEval (C++) | Standard 2-card hold'em |
| PLO4 | PokerHandEvaluator (C++/Python) | 4 hole cards, best 2-of-4 + 3-of-5 board |
| PLO5 | PokerHandEvaluator | 5 hole cards, best 4-of-5 eval |
| Omaha Hi/Lo | PokerHandEvaluator (native) | Split pot, 8-or-better qualifier |
| Shortdeck | Custom (modified rankings) | 6+ hold'em, flush > full house |
| Double Board PLO | Novel — custom implementation | Two boards, scoop/chop scoring |
| Bomb Pot | Novel — custom implementation | Action-first betting, straddle games |

## Reference Files
- `references/gto-wizard-db-seed-troubleshooting.md` — Seed script fixes, aiosqlite venv setup, deployment architecture, API route map

## Recommended Tech Stack (Proven)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind v4, Shadcn UI | SSR + routing, component library |
| Backend | FastAPI (Python 3.12), Pydantic v2, WebSockets | Async, good Python solver integration |
| Solver | Python 3.12, NumPy, MCCFR, gRPC | CPU-intensive CFR needs isolation |
| Database | PostgreSQL (Neon serverless) | Free tier, JSONB for strategy storage |
| Cache | Redis | Equity result caching, pub/sub for solver progress |
| Containers | Docker + Docker Compose | Solver needs isolation |
| CI/CD | GitHub Actions (path-filtered) | Per-app builds |
| Monorepo | Turbo + Nx dual config | Task scheduling + Go/WSL support |

## Architecture Pattern (Proven)

```
apps/web         — Next.js frontend (pages: /equity, /plo, /train, /analyze, /icm, etc.)
apps/api        — FastAPI (REST + WebSocket)
apps/solver     — Python gRPC (CFR engine, separate process)
packages/
  poker-core    — Shared: deck, hand eval, equity, range, variants (Python + TS)
  ui-components — Shared React components
  types         — Shared TypeScript types
```

## CFR Algorithm Notes

MCCFR (Monte Carlo CFR) is the standard approach:
1. Initialize empty strategy for all infosets
2. Sample game tree (chance sampling for cards)
3. Play to terminal → compute regrets
4. Update regrets at each infoset
5. Normalize → Nash equilibrium

Performance targets (2-player):
- River: <1s
- Turn: <10s
- Flop: <60s

Multi-way (3+ players): multiply times by ~5-10x.
## GTO Solver Implementation (June 2026)

- CFREngine in `apps/solver/cfr/engine.py` with chance sampling
- Flop solver: `solve_flop()` samples turn/river via chance
- Turn solver: `solve_turn()` samples river via chance
- River solver: `solve_river_spot()` — all cards known, no sampling
- Street progression: street=0 (preflop) → street=1 (flop) → street=2 (turn) → street=3 (river)
- gRPC service wraps solver for API consumption
- Redis-to-WebSocket bridge streams progress to frontend

## Strategy Page UI (June 2026)

- **Pages:** `/study` (367 lines) — main strategy exploration; `/strategy` (704 lines, legacy)
- **Layout:** Position bar + two-column grid (matrix left, actions right)
- **Matrix:** 13×13 hand grid with red/blue action colors, split gradients for mixed strategies
- **Right panel:** Position chips, action cards (Allin/Raise/Fold with % + combos), hand combo grid
- **Styling:** Inline styles for exact color matching, CSS classes in globals.css for hover effects
- **Color map:** RED_HANDS set (AA-88, broadways) + SPLIT_HANDS gradients for mixed strategies

## GTO Wizard Clone Repo
- **Repo:** `https://github.com/ChonSong/gto-wizard-clone`
- **Created:** 2026-05-25
- **Current state (June 2026):** v1.0.0-alpha, 110+ commits, all 7 variants + solver + training + ICM
- **Tests:** 580+ unit tests passing, E2E with Playwright (needs container system deps)

## HH File Formats

**PokerStars** — `PokerStars Hand #123456789: Hold'em No Limit`
**GGPoker** — different header format, same underlying structure
**Winamax** — similar to PokerStars

Key fields: `player`, `position`, `hole cards`, `actions`, `board`, `pot`, `winner`

## Common Gotchas (from building the clone)

1. **Protobuf version mismatch** — pin `protobuf~=5.29` explicitly; generated code from `protoc` must match runtime
2. **FastAPI DB session naming** — `get_db_session` for DI, `get_session_factory` for internal use; don't mix them
3. **Missing `timezone` import** — `from datetime import datetime, timezone` (not just `datetime`)
4. **Playwright in containers** — needs `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers` AND system libs (`glib2`)
5. **PLO4 evaluator install** — `pip install git+https://github.com/HenryRLee/PokerHandEvaluator` (not on PyPI)
6. **Strategy key format** — 6-part colon-separated: `{game_type}:{players}:{street}:{board_hash}:{bet_size}:{stack_depth}`
7. **Double Board equity formula** — `adjusted_equity = (scoop_wins × 1.0 + chop_wins × 0.5) / total_sims`
8. **Shortdeck API rename (June 2026)** — `shortdeck.ShortdeckEvaluator` was renamed to `shortdeck.ShortdeckEquity` in a post-pull change. Update any cron verification scripts or imports. Old name will `ImportError`.

---

*Last updated: 2026-06-04*
