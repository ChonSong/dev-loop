# Poker Platform Reference Stack — GTO Wizard Clone Domain Knowledge

## What GTO Wizard Is
**gto-wizard.com** — subscription SaaS poker training platform. Web + mobile. Core: GTO strategy training via quizzes, hand history analysis, and equity tools.

## Core Feature Areas

| Feature | What it does | Technical component |
|---------|-------------|---------------------|
| **GTO Solver Engine** | Nash equilibrium via CFR (Counterfactual Regret Minimization) | MCCFR algorithm, NumPy/Numba, gRPC service |
| **Equity Calculator** | Hand vs range equity via Monte Carlo + exact enumeration | OMPEval, poker-odds-calc, range expansion |
| **Training Quizzes** | Random spots → user guesses GTO action → feedback | Quiz DB, spot randomization, EV loss calc |
| **Hand History Analyzer** | Upload HH files → parse → leak detection vs GTO | HH parsers (PokerStars, GGPoker, Winamax) |
| **ICM Calculator** | Tournament chip equity via Independent Chip Model | Malmoud-Harville formula, push/fold charts |
| **Range Builder** | Visual 13x13 grid hand selector | React component, range string parsing |

## Open-Source Libraries to Leverage

### Poker Engine
- `zekyll/OMPEval` (224⭐, C++) — fast 5-card hand evaluation
- `siavashg87/poker-odds-calc` (99⭐, Node) — fast equity calc
- `thotbreakerr/Texas-Holdem-AI` (1⭐, Python) — MCCFR + GTO reference impl
- `sweeterthancandy/CandyPoker` (13⭐) — equity + solver
- `mcostalba/poker` (28⭐, Go) — equity calc in Go

### ICM & Tournament
- `apcode/poker-mtt-icm` (12⭐, Python) — tournament ICM
- `pwn2ooown/Simple-ICM-Calculator-Python` — DFS-based ICM

### Hand History
- `aneopsy/PokerStats` (18⭐, Python) — PokerStars HH parser
- `alexyz/poker` (140⭐, Java) — PokerStars + Full Tilt parser

### Range Equity
- `battermann/equiweb` (8⭐) — in-browser range equity (Node)
- `sol5000/gto` (14⭐) — Streamlit GUI + Monte Carlo equity

## Recommended Tech Stack (for a GTO Wizard Clone)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind v4, Shadcn UI | SSR + routing, component library |
| Backend | FastAPI (Python 3.12), Pydantic v2, WebSockets | Async, good Python solver integration |
| Solver | Python 3.12, NumPy, Numba JIT, MCCFR | CPU-intensive CFR needs Numba |
| Database | PostgreSQL (Neon serverless) | Free tier, JSONB for strategy storage |
| Cache | Redis | Equity result caching |
| Containers | Docker + Docker Compose | Solver needs isolation |
| CI/CD | GitHub Actions (path-filtered) | Per-app builds |

## Architecture Pattern

```
apps/web         — Next.js frontend
apps/api        — FastAPI (REST + WebSocket)
apps/solver     — Python gRPC (CFR engine, separate process)
packages/
  poker-core    — Shared: deck, hand eval, equity, range (Python + TS)
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

## GTO Wizard Clone Repo
- **Repo:** `https://github.com/ChonSong/gto-wizard-clone`
- **Created:** 2026-05-25
- **Initial commit:** `7b58866` — poker-core scaffold + FastAPI skeleton

## HH File Formats

**PokerStars** — `PokerStars Hand #123456789: Hold'em No Limit`
**GGPoker** — different header format, same underlying structure
**Winamax** — similar to PokerStars

Key fields: `player`, `position`, `hole cards`, `actions`, `board`, `pot`, `winner`

## ICM Formula (Malmoud-Harville)

```
EV_i = Σ(p_j * prize_j) / chips_i
where p_j = probability of finishing in place j
```

Computed via dynamic programming over payout structure.

---

*Last updated: 2026-05-25*