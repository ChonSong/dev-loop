# Equity Page — GTO Wizard Layout Blueprint

Extracted from real GTO Wizard screenshots via vision_analyze. This is the pixel-accurate layout structure to match.

## Full Page ASCII Tree

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ GTO WIZARD GLOBAL TOP BAR                                                                                   │
├──────────────┬──────────────────────────┬──────────────────────────────────────────────────┬──────────────┤
│ LEFT: Logo + │ MIDDLE: STUDY | PRACTICE | RIGHT: UPLOAD + Fullscreen + Help + Settings +  │
│ Sidebar Icons│          ANALYZE        │ Profile Icon                                     │
│              │ (STUDY is active, cyan) │                                                  │
├──────────────┴──────────────────────────┴──────────────────────────────────────────────────┴──────────────┤
│ HAND HISTORY ACTION BAR                                                                                    │
│ ┌───────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┐                                 │
│ │ CASH  │ UTG   │ HJ    │ CO    │ BTN   │ SB    │ BB    │ FLOP  │ BB    │ BTN (active, teal highlight) │
│ │ [6max │ FOLD  │ FOLD  │ FOLD  │ RAISE │ FOLD  │ CALL  │ CHECK │ CHECK │ ▸ Your turn                    │
│ │ NL50] │       │       │       │ 2.5   │       │ 12    │       │       │                                 │
│ └───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┘                                 │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ SUB-TOP TABS                                                                                                │
│ STRATEGY | RANGES (active, cyan underline) | BREAKDOWN | REPORTS                                             │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ POSITION SELECTORS ───────────────────────────────────────────────────────────────────────────────────┐ │
│ │ UTG(100) | HJ(100) | CO(100) | BTN(active,100) | SB(99.5) | BB(97.5)  | [Copy] [Paste] [Range▼] 🎯 │ │
│ └────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│ ┌─ MAIN CONTENT (flex row) ───────────────────────────────────────────────────────────────────────────────┐ │
│ │ ┌─ LEFT PANEL ─────────────────────────────┐ ┌─ RIGHT PANEL ──────────────┐                            │ │
│ │ │ ┌── DUAL MATRICES ────────────────────┐  │ │ │ ┌─ CALCULATE BUTTONS ──┐ │                            │ │
│ │ │ │  ┌──────────┐  ┌──────────┐        │  │ │ │ │ Calculate Equity     │ │                            │ │
│ │ │ │  │ HERO     │  │ VILLAIN  │        │  │ │ │ │ ╔══╗ ══╗             │ │                            │ │
│ │ │ │  │ MATRIX   │  │ MATRIX   │        │  │ │ │ │ ║HM║ EV║             │ │                            │ │
│ │ │ │  │ 13×13    │  │ 13×13    │        │  │ │ │ │ ╚══╝ ══╝             │ │                            │ │
│ │ │ │  │ (orange) │  │ (teal)   │        │  │ │ │ └──────────────────────┘ │                            │ │
│ │ │ │  └──────────┘  └──────────┘        │  │ │ │ ┌─ BOARD INPUT ────────┐ │                            │ │
│ │ │ └─────────────────────────────────────┘  │ │ │ │ K♠ 7♥ 2♣           │ │                            │ │
│ │ │                                          │ │ │ └──────────────────────┘ │                            │ │
│ │ │ ┌─ STATS ROW ─────────────────────────┐  │ │ │ ┌─ ACTION BREAKDOWN ──┐ │                            │ │
│ │ │ │ Combos │ EV    │ Equity │ EQR      │  │ │ │ │ Fold   ████████ 31%  │ │                            │ │
│ │ │ │ 301.1  │ +1.86 │ 47%    │ 71.8%    │  │ │ │ │ Call   ██████  57%   │ │                            │ │
│ │ │ └──────────────────────────────────────┘  │ │ │ │ Raise  ████    12%  │ │                            │ │
│ │ │                                          │ │ │ └──────────────────────┘ │                            │ │
│ │ │ ┌─ EQUITY DISTRIBUTION ────────────────┐  │ │ │ ┌─ QUICK RANGES ──────┐ │                            │ │
│ │ │ │ Win (34%) ██████████░░░░░░░░ 68%    │  │ │ │ │ AA | Top5% | AnyPr...│ │                            │ │
│ │ │ │          ░░░░░░░░░░░░░░░░░░░ 32%    │  │ │ │ └──────────────────────┘ │                            │ │
│ │ │ │ Lose                                │  │ │ │                         │                            │ │
│ │ │ └──────────────────────────────────────┘  │ │ └─────────────────────────┘                            │ │
│ │ │                                          │ │                                                         │ │
│ │ │ ┌─ EQUITY GRAPH ───────────────────────┐  │ │                                                         │ │
│ │ │ │  100% ─╱╲────                        │  │ │                                                         │ │
│ │ │ │   50% ───╲╱─────                     │  │ │                                                         │ │
│ │ │ │    0% ────────╱╲──                  │  │ │                                                         │ │
│ │ │ │    └─ BB ── BTN ─┘                  │  │ │                                                         │ │
│ │ │ └──────────────────────────────────────┘  │ │                                                         │ │
│ │ └────────────────────────────────────────────┘ │                                                         │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ BOTTOM TABS:                                                                                                │
│ HANDS | SUMMARY (active, cyan) | FILTERS | BLOCKERS                                                          │
│ ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Summary: AhKh vs AA,KK,AKs on Kd7h2c: 33.7% equity, EV 0.34                                             │ │
│ └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Key Component Specifications

### 1. Header
- **Height**: 48px (3rem)
- **Background**: `#1a1a1a`
- **Border bottom**: `1px solid #2a2a2a`
- **Max width**: 1600px, centered
- **Logo**: 🧙 emoji (22px) + "GTO Wizard" (15px bold, gradient #00C9A7 → emerald-300)
- **Nav tabs**: STUDY / PRACTICE / ANALYZE — 13px medium, white (active), #888 (inactive)
- **Active indicator**: 2px #00C9A7 underline, rounded full
- **Right**: Upload icon + help icon + settings icon + profile avatar (28×28 circle, #333 bg)

### 2. Position Flow Bar
- **Height**: ~28px
- **Background**: transparent
- **Position boxes**: 64px min-width, flex-row wrap
- **Inactive**: `bg-[#2a2a2a]` with `border-[#333]`
- **Active/current**: `bg-[#333] border-[#444]` OR `border-2 border-[#00C9A7] bg-[#00C9A7]/10` for the current position
- **Text**: Position name (11px bold white), action (9px colored by action type), stack (9px #666)
- **Action colors**: Fold=#888, Raise=#FF9F0A, All-in=#FF3B30, Call=#34C759, Check=#30B0C7

### 3. Sub-Tabs (STRATEGY / RANGES / BREAKDOWN / REPORTS)
- **Container**: flex with `border-b border-[#2a2a2a]` and `pb-2 -mb-2`
- **Tab**: 12px font-semibold uppercase tracking-wider
- **Active**: white text, 2px #00C9A7 bottom border
- **Inactive**: #666 text, hover → #aaa
- **Gap**: 16px between tabs

### 4. Position Selectors Row
- **Height**: ~30px
- **Positions**: UTG / HJ / CO / BTN / SB / BB — clickable buttons
- **Active position**: `bg-[#00C9A7]/20 text-[#00C9A7]`
- **Inactive**: `bg-[#333] text-[#888] hover:text-white`
- **Range description**: right-aligned text "BTN vs BB, 100bb, FLOP"
- **Range input**: 48ch wide input with font-mono 12px

### 5. 13×13 Hand Matrices
- **Cell size**: 38×38px (can vary 34-48px depending on viewport)
- **Gap**: 1-2px between cells
- **Background grid**: `#444` (visible through gaps)
- **Row/column headers**: 18px wide (row), 18px tall (col) — 9px bold #555
- **Font inside cells**: 11px bold system font
- **Hero matrix label**: "BTN (Your Range)" — 10px bold #FF9F0A
- **Villain matrix label**: "BB (Villain Range)" — 10px bold #00C9A7
- **Selected cell**: `#FF9F0A` bg, white text
- **Heatmap cell**: `rgba(0,201,167, opacity)` where opacity = min(1, max(0.05, equity * 1.2))
- **Empty cell**: `#2a2a2a` bg

### 6. Stats Row (Combos / EV / Equity% / EQR%)
- **Container**: `grid grid-cols-4 gap-3`
- **Each stat card**: `bg-[#2a2a2a] rounded-lg p-3 border border-[#3a3a3a]`
- **Label**: 10px uppercase tracking-wider #888
- **Value**: 16px bold, color varies by stat
  - Combos: white
  - EV: #34C759 (positive) or #FF3B30 (negative)
  - Equity: gradient red→yellow→green (use equityColor())
  - EQR: #30B0C7

### 7. Equity Distribution Bar
- **Height**: 16px (h-4)
- **Container**: `bg-[#333] rounded-full overflow-hidden flex`
- **Win segment**: `bg-[#34C759]` — width proportional
- **Tie segment**: `bg-[#FF9F0A]` — width proportional
- **Lose segment**: `bg-[#FF3B30]` — width proportional
- **Below bar**: 3 labels with counts — Win (#34C759), Tie (#FF9F0A), Lose (#FF3B30) — 9px, space-between

### 8. Equity Graph
- **Container**: `bg-[#2a2a2a] rounded-lg p-3 border border-[#3a3a3a]` — 160px height
- **SVG viewBox**: 0 0 280 140
- **Grid lines**: #333 stroke at 0%, 25%, 50%, 75%, 100%
- **Y-axis labels**: 8px #555 at each grid line
- **Hero line (BTN)**: polyline, #00C9A7 stroke, 1.5px
- **Villain line (BB)**: polyline, #30B0C7 stroke, 1.5px
- **Legend**: circles + labels at top-right of chart

### 9. Right Panel (Action Breakdown)
- **Width**: 256px (w-64)
- **Order of sections** (top to bottom):
  1. Calculate buttons (primary + secondary)
  2. Board input (5 card slots + text input)
  3. Action breakdown (if EV data loaded)
  4. Quick ranges (preset buttons)
  5. Iterations selector

### 10. Bottom Tabs (HANDS / SUMMARY / FILTERS / BLOCKERS)
- **Container**: `bg-[#2a2a2a] rounded-lg border border-[#3a3a3a]`
- **Tab bar**: flex, `border-b border-[#3a3a3a]`
- **Tab**: 12px uppercase tracking-wider, 8px horizontal padding
- **Active**: white + 2px #00C9A7 bottom border
- **Inactive**: #666

## Design Tokens Reference

See `/workspace/open-lovable/styles/gto-tokens.ts` for all color, typography, and spacing constants. Import via:
```typescript
import { gto, actionColor, equityColor, heatmapOpacity, suitDisplay, formatCards } from "@/styles/gto-tokens";
```

## Reference Screenshots Used

| # | File | What It Shows |
|---|------|--------------|
| 1 | `ranges_tab_overview.jpg` | Full page layout: position bar, sub-tabs, dual matrices, stats, right panel |
| 2 | `equity_matrix_13x13.jpg` | Board texture filter UI (cropped — use for matrix cell sizing) |
| 3 | `breakdown_tab_overview.jpg` | Equity distribution bars, stat summary, action breakdown |
| 4 | `breakdown_tab_ev_chart.jpg` | EV chart with action percentages |
| 5 | `strategy_full_view.jpg` | Strategy table with action bars and EV columns |

All at `/workspace/gto-wizard-references/`.
