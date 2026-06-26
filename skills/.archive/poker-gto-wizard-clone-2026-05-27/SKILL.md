---
name: poker-gto-wizard-clone
description: "Build a full-featured open-source GTO poker training platform at github.com/ChonSong/gto-wizard-clone. Clones gto-wizard.com: MCCFR GTO solver, equity calculator, training modes, hand history analysis, ICM, range builder, plus PLO4, double board PLO, bomb pot, and shortdeck. Uses HenryRLee/PokerHandEvaluator for Omaha. Integrates with repo-transmute, tdd, blueprint, docker-patterns, autonomous-development, and cron-driven phase execution."
tags: [poker, gto, cfr, equity-calculator, poker-hand-evaluator, omaha, plow, shortdeck, icm, hand-history, training-platform]
source: local
---

# Poker GTO Wizard Clone — Domain Skill

Build a full-featured open-source GTO poker training platform at `https://github.com/ChonSong/gto-wizard-clone`.

## GTO Wizard Feature Map

| Feature | What it does | Technical component |
|---------|-------------|---------------------|
| **GTO Solver Engine** | Nash equilibrium via MCCFR | Numba JIT, gRPC service |
| **Equity Calculator** | Hand vs range equity | OMPEval + poker-hand-evaluator |
| **Training Quizzes** | Random spots → guess GTO action → feedback | Quiz DB, spot randomizer, EV loss calc |
| **Hand History Analyzer** | Upload HH → parse → leak detection | HH parsers (PokerStars, GGPoker, Winamax) |
| **ICM Calculator** | Tournament chip equity | Malmoud-Harville formula |
| **Range Builder** | Visual 13×13 grid hand selector | React component |
| **Push/Fold Charts** | Based on stack depth + position | Strategy DB |

## Core Architecture

```
apps/web         — Next.js 15 (React 19, TypeScript, Tailwind v4, Shadcn UI)
apps/api        — FastAPI (Python 3.12) REST + WebSocket
apps/solver     — Python gRPC (CFR engine, Numba JIT, separate process)
packages/
  poker-core    — deck, hand eval, equity, range (Python + TypeScript)
  ui-components — shared React components
  types         — shared TypeScript types
```

## Omaha Variants

### PLO4 (Pot-Limit Omaha 4-card) — PRIMARY
**LIBRARY:** `HenryRLee/PokerHandEvaluator` (501⭐, C++/Python)
- Install: `pip install poker-hand-evaluator`
- Supports wheel, broadway, four-straight detection
- Must evaluate best 5 of 9 cards (4 hole + 5 community)

### PLO5 (Pot-Limit Omaha 5-card)
- Same `PokerHandEvaluator`, 5-card Omaha variant

### Omaha Hi-Lo 8-or-Better
- Same `PokerHandEvaluator` with hi/lo split logic
- Low hand qualification: 8-or-better (worst possible low is 8)
- Shared implementation patterns in `api/src/routes/equity.py`

### Shortdeck (6+ Hold'em)
- 36-card deck (9s through 2s removed)
- Flush > full house (reversed ranking from normal Hold'em)
- `poker-hand-evaluator` supports shortdeck via `DeckType.SHORTDECK`
- Add deck filter in `packages/poker-core/src/deck.ts`

### Double Board PLO — NOVEL
- Two simultaneous Omaha boards, split pot rules per variant
- Requires: two `poker-hand-evaluator` instances, merged hand ranking, UI board selector
- Strategy: evaluate each board separately, combine EV
- See `references/double-board-plomd`

### PLO Bomb Pot — NOVEL
- Pre-flop circular betting, 4 community cards revealed simultaneously
- Deck: bump cards removed in circle, then 4 community
- Pot structure: bomb pot total = sum of all antes + brings
- Custom betting handler separate from standard street-based

## Skills to Leverage

| Phase | Focus | Skill to Load |
|-------|-------|---------------|
| Phase 1 | Python equity + MCCFR engine | `test-driven-development` |
| Phase 2 | FastAPI + frontend scaffold | `docker-patterns`, `subagent-driven-development` |
| Phase 3 | Post-flop MCCFR + flop/turn/river | `test-driven-development`, `benchmark` |
| Phase 4 | Training modes (quiz, push/fold, spots) | `subagent-driven-development` |
| Phase 5 | Hand history parser + leak detection | `benchmark` |
| Phase 6 | ICM calculator + multi-table | `docker-patterns` |
| Phase 7 | PLO4/PLO5/Omaha Hi-Lo | `test-driven-development` |
| Phase 8 | Double board PLO + bomb pot | `autonomous-development` |
| Phase 9 | Shortdeck | `autonomous-development` |
| Phase 10 | Visual QA + polish + deploy | `autonomous-development`, `cronjob` |

## Key Libraries

### Hold'em
- `zekiel/OMPEval` (224⭐, C++) — 5-card hand evaluation
- `thotbreakerr/Texas-Holdem-AI` (1⭐, Python) — MCCFR reference
- `mcostalba/poker` (28⭐, Go) — equity calc

### Omaha — USE THIS
- **`HenryRLee/PokerHandEvaluator`** (501⭐, C++/Python) — PLO4/PLO5/Hi-Lo/Shortdeck. `pip install poker-hand-evaluator`

### ICM
- Native `apps/solver/icm/` implementation (Malmoud-Harville)

### Hand History
- `aneopsy/PokerStats` (18⭐, Python) — PokerStars HH parser
- `alexyz/poker` (140⭐, Java) — port to Python for GGPoker/Winamax

## Phase Execution via Cron

Each phase should run as a cron job with skill loading:
- Model: `mini-max/M2.7` (provider: minimax)
- Deliver: `all`
- Repeat: `100x`
- Skills: load the relevant skill(s) inline per phase

```bash
# Phase 1 example prompt (attach test-driven-development skill):
"Phase 1: Implement Python equity engine with OMPEval.
Use test-driven-development skill. Build hand evaluator, deck, and equity
calculator. All tests green before commit. Push to gto-wizard-clone main."
```

## References

- `references/double-board-plomd` — double board PLO rules and implementation notes
- `references/poker-platform-stackmd` — domain knowledge from repo-init skill
