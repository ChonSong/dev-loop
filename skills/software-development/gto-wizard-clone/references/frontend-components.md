# Frontend Component Architecture

## Directory Layout

```
apps/web/src/
├── app/                          # Next.js 15 App Router pages
│   ├── page.tsx                  # Home page (hero, feature cards, stats)
│   ├── layout.tsx                # Root layout (Header + main + footer)
│   ├── globals.css               # Global styles (Tailwind v4, CSS vars)
│   ├── equity/page.tsx           # Equity calculator
│   ├── icm/page.tsx              # ICM tournament calculator
│   ├── train/page.tsx            # Training mode
│   │   └── review/page.tsx       # Review missed spots
│   ├── courses/page.tsx          # Training courses
│   ├── spots/page.tsx            # Community spots
│   ├── analyze/page.tsx          # Hand history analysis
│   │   ├── hands/page.tsx        # Hand viewer
│   │   ├── leaks/page.tsx        # Leak analysis
│   │   └── viewer/page.tsx       # Hand playback
│   ├── plo/page.tsx              # PLO4 equity
│   ├── omaha/page.tsx            # Omaha variants
│   ├── double-board/page.tsx     # Double board PLO
│   ├── bomb-pot/page.tsx         # Bomb pot
│   ├── strategies/page.tsx       # Push/fold charts
│   └── strategy/page.tsx         # Strategy detail
├── components/
│   ├── equity/
│   │   ├── RangeSelector.tsx     # 13x13 hand grid with drag-to-select
│   │   ├── EquityHeatmap.tsx     # HSL gradient equity heatmap
│   │   ├── EquityChart.tsx       # Hero/tie/villain stacked bar
│   │   ├── EquityBar.tsx         # Compact inline equity bar
│   │   ├── RangeGrid.tsx         # Base grid component
│   │   └── index.ts
│   ├── strategy/
│   │   └── StrategyMatrix.tsx    # GTO action-frequency matrix
│   ├── icm/
│   │   ├── ICMResults.tsx
│   │   ├── ChipStackPanel.tsx
│   │   ├── SMPZone.tsx
│   │   ├── BubblePressure.tsx
│   │   └── index.ts
│   ├── hh/
│   │   ├── HandTable.tsx
│   │   ├── HandViewer.tsx
│   │   ├── BatchImport.tsx
│   │   ├── TagInput.tsx
│   │   ├── BoardDisplay.tsx
│   │   ├── HandPlayback.tsx
│   │   ├── FileUpload.tsx
│   │   ├── LeakChart.tsx
│   │   ├── csvExport.ts
│   │   └── index.ts
│   ├── ui/
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── StrategyCard.tsx
│   │   └── StrategyHeatmap.tsx
│   ├── video/
│   │   ├── VideoEmbed.tsx
│   │   └── index.ts
│   ├── Header.tsx                # 7-link nav with gold active/hover
│   └── SolverProgress.tsx
├── styles/
│   └── gto-tokens.ts             # Design system tokens
└── lib/
    └── utils.ts                  # RANKS, SUITS, getHand, cn
```

## Key Component Specs

### RangeSelector (the centerpiece of GTO UI)
- 13x13 grid (ranks A-2 × A-2)
- Cell color by hand type: pocket=amber, suited=green, offsuit=blue
- Drag-to-select: onMouseDown starts selection, onMouseEnter adds cells, onMouseUp ends
- Shift+click: selects range from last clicked to current cell
- Legend below showing hand type colors
- Min 44px touch targets for mobile

### EquityHeatmap
- Same 13x13 grid layout
- HSL gradient: 0%→hsl(0,70%,50%) red, 50%→hsl(60,70%,55%) yellow, 100%→hsl(120,70%,50%) green
- 34x34px cells with tight gap
- Equity percentage text inside each cell
- Hover tooltip (hand name + equity%)
- Color scale legend (21-step gradient bar, "Low" to "High")

### EquityChart
- Horizontal stacked bar: hero(green) | tie(gray) | villain(red)
- Large percentage text overlaid in each segment
- Win/tie counts below
- EV per hand in header

### StrategyMatrix
- Same 13x13 layout
- Action color: bet=blue, check=green, fold=red
- Opacity = action frequency (0-100%)
- Action indicators: ↑ bet, ● check, ✕ fold
- Detail panel on click (hand, action, freq%, EV)
- Legend above grid

## API Proxy Pattern

All API calls from frontend use relative URLs. Next.js rewrites proxy them:
- `/api/v1/equity/calculate` → `http://localhost:8002/api/v1/equity/calculate`
- `/icm/calculate` → `http://localhost:8002/icm/calculate`
- etc.

The `NEXT_PUBLIC_API_URL` env var controls the backend target.

## Heatmap Request Pattern

When calling the heatmap endpoint from the equity page, cap iterations to 10000 since it evaluates all 169 hands:

```typescript
const response = await fetch("/api/v1/equity/heatmap", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    villain: villainStr,
    board: boardStr || undefined,
    iterations: Math.min(iterations, 10000),  // cap for 169-hand eval
  }),
});
```

## 3-Phase Polish Process

When making a GTO Clone look like the real GTO Wizard:

1. **Range Matrix Phase** — interactive 13x13 grid, drag-to-select, hand-type coloring
2. **Equity Visualizations Phase** — heatmap with HSL gradient, equity bar chart, inline bars
3. **Strategy View Phase** — action-frequency matrix, polished home page, working nav

Skills to load: `creative/claude-design`, `creative/popular-web-designs` (Linear/Supabase tokens), `test-driven-development`
