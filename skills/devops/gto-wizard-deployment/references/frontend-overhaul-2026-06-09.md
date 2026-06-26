# Frontend Pages Added This Session

## Overview

Two new pages were created from user-provided reference HTML files:

| Page | Route | Source Reference | Key Features |
|------|-------|-----------------|--------------|
| **Study** | `/study` | `study_page.html` | 13×13 strategy matrix, position chips, action cards, hand combo grid, pot odds |
| **Equity Calculator** | `/equity` | `poker_calcultor.html` | Poker table with seats, card selector, Monte Carlo engine, hand ranking breakdown |

The home page (`/`) now redirects to `/study`.

## Nav Overhaul

The header nav was completely replaced to match the reference design:

| Tab | Route | Notes |
|-----|-------|-------|
| Hold'em | `/equity` | Links to new calculator |
| PLO | `/plo` | Existing page |
| Play | `/play` | Route exists, no page yet |
| Study | `/study` | Active (green) tab, new page |
| Practice | `/practice` | Route exists, no page yet |
| Analyze | `/analyze` | Existing page |

Nav styling: #111111 background, pill-group tabs (#0a0a0a bg, 10px borderRadius, 1px #1d1d1d border), active tab highlighted with green bg for Study.

## Study Page Architecture

Single `"use client"` page component at `app/study/page.tsx`. Components:
- **PositionBar** — ♠ Cash 100bb button + six position buttons (UTG through BB) with "Take action" sub-label on active
- **Matrix Panel (left column)** — PanelHeader with Strategy/Ranges/Breakdown/Reports: Flops tabs + pagination
- **HandMatrix** — 13×13 grid, color-coded cells (red raise, blue fold, gradient for mixed), cell hover transform, border-2px-white on selected
- **Overview Panel (right column)** — Overview/Table/Equity chart sub-tabs
- **PlayerChips** — Position chip buttons with active highlighting
- **ActionCards** — Allin/Raise/Fold cards with EV bar
- **HandsGrid** — Suit-colored combo detail grid (selectable by clicking matrix cell)

## Equity Calculator Architecture

Single `"use client"` page component at `app/equity/page.tsx`. Architecture:

### State Machine

```
Click card in selector → find next empty slot (you → board → player slots order)
  → fill card data → auto-run Monte Carlo (2000 iterations)
Click filled card → clear slot → auto-run Monte Carlo
Click "Add" on inactive player → set active=true → show card slots
Click Reset → clear all → set players 1-2 active only
```

### Components
- **Table visual** — Oval felt (#1A6B3A) with brown border (#5E391D), centered board cards
- **Seats** — 9 seats (You + 8 players) with absolute positioning (left%/right%/top%/bottom%)
- **Board cards** — 5 slots (flop 3 + turn + river), clickable to remove
- **Card selector** — 52 cards (13 ranks × 4 suits), 26×36px grid, grayed out when used
- **Odds panel** — Win% (green), Tie%, Others Win% (red), 2000-iteration Monte Carlo
- **Hand ranking table** — Royal Flush through High Card with percentage breakdown

### Monte Carlo Engine

Adapted verbatim from the reference HTML's vanilla JS. Key components preserved:
- `evaluate5(hand)` — 5-card hand rank evaluator (returns score, higher = better)
- `evaluate7(cards)` — best 5-card hand from 7 cards (iterates COMBOS5: 21 combos)
- `getRankCategory(score)` — maps score to 0-9 hand ranking category
- Monte Carlo loop: 2000 iterations, Fisher-Yates shuffle, random draws for unknown cards

Triggered via `useEffect` with 50ms setTimeout debounce. Cancellation via `useRef(cancelled)`.
