# Trainer Tool Workflow

## Overview

The Trainer Tool (`/gto/training`) implements a complete GTO training loop:
1. **Preset Scenario** → 2. **Filter Flop Texture** → 3. **Generate Question** → 4. **Select Action** → 5. **Color-coded Feedback** → 6. **Street-by-street Review** → 7. **Range View**

## Component Architecture

All training components live in `/workspace/open-lovable/app/gto/training/`:

| Component | File | Purpose |
|-----------|------|---------|
| `TrainerMode` | `TrainerMode.tsx` | Main orchestrator (363 lines) |
| `ScenarioSelector` | `ScenarioSelector.tsx` | 10 preset scenario buttons |
| `FlopTextureFilter` | `FlopTextureFilter.tsx` | 8 board texture filter chips |
| `ActionButtons` | `ActionButtons.tsx` | Action selection + feedback grades |
| `StreetNav` | `StreetNav.tsx` | Preflop→Flop→Turn→River navigation |
| `RangeViewModal` | `RangeViewModal.tsx` | 13x13 action-split matrix modal |

## Trainer Flow

### 1. Scenario Preset
`ScenarioSelector` displays 10 preset scenarios split by category:
- **Post-flop**: C-betting BTN vs BB, SRP IP, SRP OOP, 3-bet Pot IP, 3-bet Pot OOP
- **Pre-flop**: BTN Open Raise, CO vs BTN 3-bet, BB vs SB Steal, 4-bet Pot, SB vs BTN 3-bet

Selected scenario highlighted with `bg-[#00C9A7]/20 border-[#00C9A7]/50 text-[#00C9A7]`.

### 2. Flop Texture Filter
`FlopTextureFilter` shows 8 texture chips: Random, Paired, Monotone, Flush Draw, Connected, Dry, High Cards, Low Cards. Each has an emoji icon.

### 3. Generate Question
`POST /api/v1/trainer/question` — Backend (created June 2026, `routers/trainer.py`):
```python
@router.post("/question")
async def generate_question(req: QuestionRequest):
    # Picks random hand from scenario's hand pool
    # Returns: id, spot_id, scenario, hand, board, street, pot, positions, description
```

Returns a `QuestionResponse` with hero hand, board cards, pot size, positions, and scenario description.

### 4. Select Action
`ActionButtons` renders context-appropriate actions:
- **No bet facing:** Fold, Check, Bet 1/3, Bet 1/2, Bet 2/3, Bet Pot (+ All-in on river)
- **Bet facing:** Fold, Call, Raise 33%, Raise Pot, All-in
- Each button has a `shortcut` key (F, X, B1-B4, R1, R2, A)
- Actions are color-coded by category: Fold=red, Check/Call=green, Bet=orange, Raise=blue, All-in=pink

### 5. Color-coded Feedback
`POST /api/v1/trainer/submit` evaluates the selected action against GTO:

| Grade | Color | Display | Meaning |
|-------|-------|---------|---------|
| `optimal` | `#34C759` (green, full) | ✅ Optimal! | Preferred GTO action — highest EV line |
| `acceptable` | `#34C759` (green, dim) | ✓ Acceptable | Not the primary GTO action but positive EV |
| `inaccuracy` | `#FF9F0A` (amber) | ⚠️ Inaccuracy | Negative EV compared to GTO line |
| `blunder` | `#FF3B30` (red) | ❌ Blunder | Significant EV loss |

Feedback is shown via:
- Button border/bg/ring style using `FEEDBACK_COLORS` from `ActionButtons.tsx`
- Result card with colored border + icon + explanation text
- EV comparison showing user's EV vs GTO EV

### 6. Street-by-street Navigation
`StreetNav` shows 4 connected segments: Preflop → Flop → Turn → River
- Current street: `bg-[#00C9A7]/20 border-[#00C9A7] text-[#00C9A7]`
- Completed street: `bg-[#34C759]/10 border-[#34C759]/40 text-[#34C759]/60` with ✓
- Future street: dimmed, `cursor-not-allowed`
- Connecting lines between segments, green if completed

Board cards update per street (boardForStreet helper):
- Preflop: no board
- Flop: first 3 cards
- Turn: first 4 cards
- River: all 5 cards

### 7. Range View
`RangeViewModal` shows a 13×13 action-split matrix when user clicks "Range View" button.
- `POST /api/v1/trainer/range-view` returns 169 hands (all 13×13 combos)
- Each cell colored by action: Fold=red, Check=gray, Call=green, Bet/Raise=orange
- Legend shows color→action mapping + hand/action counts
- Empty cells (no data) shown as `#2a2a2a`

## Backend API

File: `/workspace/gto-wizard-clone/apps/api/routers/trainer.py` (225 lines)

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/trainer/question` | Generate question from scenario + texture |
| POST | `/api/v1/trainer/submit` | Evaluate action, return feedback grade |
| POST | `/api/v1/trainer/range-view` | Return 169-hand action-split matrix |

### Scenario Data
`SCENARIOS` dict in `trainer.py` defines 4+ scenarios with:
- `label`, `hero_pos`, `villain_pos`, `preflop_action`, `flop`, `hands[]`

### GTO Solution Database
`GTO_SOLUTIONS` dict maps `hand:board` → `{action, ev, grade, alt_actions}`.
Currently holds 6 entries as seed data. Expand for production use.

### Range View Generation
Generates 169 simulated hands with action assignment based on:
- Pairs (higher = bet, middle = check, lower = fold)
- Suited (broadways = bet, connectors = check/fold)
- Offsuit (premium = bet/raise, middle = check, weak = fold)
- Random frequency (0.3-1.0) for EV display

## Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `/workspace/open-lovable/app/gto/training/TrainerMode.tsx` | 363 | Main trainer orchestrator |
| `/workspace/open-lovable/app/gto/training/ScenarioSelector.tsx` | 60 | 10 preset scenario buttons |
| `/workspace/open-lovable/app/gto/training/FlopTextureFilter.tsx` | 54 | 8 board texture chips |
| `/workspace/open-lovable/app/gto/training/ActionButtons.tsx` | 161 | Action buttons + feedback grades |
| `/workspace/open-lovable/app/gto/training/StreetNav.tsx` | 62 | Street-by-street nav |
| `/workspace/open-lovable/app/gto/training/RangeViewModal.tsx` | 195 | 13x13 action-split matrix |
| `/workspace/open-lovable/app/gto/training/page.tsx` | 550 | Training page entry (hosts TrainerMode) |
| `/workspace/gto-wizard-clone/apps/api/routers/trainer.py` | 225 | Backend trainer API |

## Future Improvements

- Expand GTO_SOLUTIONS database with solver-generated data
- Add WebSocket for real-time solver feedback (instead of polling)
- Add difficulty levels (beginner → advanced)
- Add session tracking (history of past training sessions)
- Add leaderboard integration for competitive training
