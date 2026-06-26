# GTO Wizard Clone — Frontend Architecture Reference

Captured June 14, 2026 session. Project at `/home/sc/repos/gto-wizard-clone`.

## Directory Structure

```
apps/
  api/
    main.py              — FastAPI app, router registration
    variants.py           — Variant registry (10 variants via pokerkit)
    routers/
      equity.py           — NLH equity calculator (Monte Carlo)
      variants.py         — Unified variant endpoints: list, info, equity
      solver.py           — gRPC solver proxy
      icm.py, auth.py, hh.py, strategy.py, quiz.py, ...
    models/               — Pydantic models
    Dockerfile
  solver/
    cfr/engine.py         — Core MCCFR engine (CFREngine class)
    cfr/flop_solver.py    — Flop solver wrapper
    cfr/solve_pipeline.py — Multi-street orchestration
    server.py             — gRPC bootstrap (port 50051)
    service.py            — gRPC service implementation
    strategy/             — Strategy storage + chart gen
    games/                — Texas hold'em game state + infosets
    Dockerfile
  web/
    src/
      app/
        layout.tsx
        page.tsx          — Home page with feature cards
        equity/
          page.tsx        — NLH equity (748 lines, ~12 inline components)
          variant-page.tsx — Shared VariantEquityPage component (used by PLO only)
          plo/page.tsx    — Uses VariantEquityPage shared component
          stud/page.tsx   — Custom page with StudHandDisplay visual component + live API
          stud8/page.tsx  — Custom page with StudHandDisplay (hi-lo variant)
          razz/page.tsx   — Custom page with StudHandDisplay visual component + live API
          badugi/page.tsx — Custom page with BadugiHandDisplay 4-card visual + live API
          2-7td/page.tsx  — Functional page, needs visual component (pending meta.ai)
          2-7sd/page.tsx  — Functional page, needs visual component (pending meta.ai)
        icm/page.tsx
        train/page.tsx
        analyze/
        study/page.tsx
        play/page.tsx
        practice/page.tsx
        strategies/page.tsx
        strategy/page.tsx
        spots/page.tsx
        courses/page.tsx
        bomb-pot/page.tsx
        double-board/page.tsx
        omaha/page.tsx
      components/
        Header.tsx        — Inline-styled navTabs array
        badugi/
          index.ts        — Barrel: BadugiHandDisplay, makeBadugiHand
          BadugiHandDisplay.tsx — 4-card dark gradient display, empty slot support
        stud/
          index.ts        — Barrel: StudHandDisplay, makeDefaultStudHand
          StudHandDisplay.tsx — 7-card display (2 down + 4 up + 1 down per player), equity readout
        equity/
          index.ts        — Barrel: RangeGrid, RangeSelector, EquityChart, EquityHeatmap, EquityBar
          RangeGrid.tsx   — 13×13 hand matrix grid
          RangeSelector.tsx
          EquityChart.tsx
          EquityHeatmap.tsx
          EquityBar.tsx
        hh/               — Hand history components
        icm/              — ICM calculator components
        strategy/         — Strategy components
        train/            — Training/quiz components
        ui/               — Shared UI primitives (button, card, StrategyCard, StrategyHeatmap)
      lib/
        api.ts            — API client: api.fetch(), api.getHand(), variantApi.list()/get()/equity()
        utils.ts          — cn(), RANKS, SUITS, getHand(), getHandIndex(), parseHand(), formatBoard()
        socket.ts         — WebSocket client
      styles/
        gto-tokens.ts     — gtoTheme object (all colors, strategy actions, equity buckets)
    Dockerfile
    package.json          — Next.js 15, React 19, Tailwind CSS 4, lucide-react
```

## Theming System (`gto-tokens.ts`)

From `@/styles/gto-tokens`:
```typescript
gtoTheme = {
  felt: '#1a1a2e', feltLight: '#16213e',
  surface: '#1f2937', border: '#2d3748',
  gold: '#d4af37', greenAccent: '#22c55e',
  strategy: {
    fold: '#4a4a4a', check: '#166534',
    bet33: '#22c55e', bet50: '#84cc16',
    bet75: '#f59e0b', bet100: '#f97316',
    bet150: '#ef4444', bet200: '#dc2626',
    raise: '#7c3aed', allin: '#991b1b',
  },
  strength: { strong: '#22c55e', medium: '#f59e0b', weak: '#6b7280', trash: '#4b5563' },
  bucket: { best: '#22c55e', good: '#84cc16', weak: '#f59e0b', trash: '#ef4444' },
  position: { utg: '#60a5fa', hj: '#818cf8', co: '#a78bfa', btn: '#c084fc', sb: '#34d399', bb: '#f87171' },
  text: { primary: '#f9fafb', secondary: '#9ca3af', muted: '#6b7280' },
  stat: { positive: '#22c55e', negative: '#ef4444', neutral: '#f59e0b' },
}
```

## Equity Page Pattern (NLH)

The NLH equity page at `/equity` is ~748 lines with these inline sub-components:
- `NavBar` — Top nav with Study/Practice/Analyze tabs, Upload button, settings icons
- `GameSettingsSidebar` — Left sidebar with game type/stakes/scenario selectors
- `PositionFlowBar` — Position action flow (UTG→HJ→CO→BTN→SB→BB)
- `BoardSection` — Board card display (3 flop cards)
- `StatsPanel` — Equity stats + equity bucket bars
- `ActionBreakdownPanel` — Action frequency with colored bar visualization
- `EquityLineChart` — Inline SVG equity-over-streets line chart
- `SuitIcon`, `BoardCardView` — Utility display components

## Variant Equity Page Pattern (live)

The shared `VariantEquityPage` at `variant-page.tsx` is a lightweight scaffold for variants without custom visuals (currently only PLO uses it).

**Custom variant pages** (stud, razz) bypass the shared component entirely and implement their own layout:

```tsx
// Pattern for a live variant page with visual component
export default function StudEquityPage() {
  // 1. State: variant info, hero/villain ranges, result, loading, error
  const [result, setResult] = useState<EquityResult | null>(null);
  
  // 2. On mount: fetch variant metadata
  useEffect(() => { variantApi.get("stud").then(setVariant); }, []);
  
  // 3. Calculate: call equity API on button click
  const calculate = useCallback(async () => {
    const r = await variantApi.equity("stud", heroRange, villainRange);
    if (r) setResult(r);
  }, [heroRange, villainRange]);
  
  // 4. Transform API data → visual component props
  const heroHand = result ? makeDefaultStudHand(upCards, result.hero_equity, "Hero", true) : null;
  
  // 5. Render: header → visual component → input form → result numbers
}
```

**Data flow:** Range strings → API → equity numbers → helper function → visual component props

## Hand Display Components

### StudHandDisplay (`components/stud/StudHandDisplay.tsx`)
- Two players (top = villain, bottom = hero)
- 7 cards each: 2 down + 4 up + 1 down (standard stud deal)
- Cards use inline styles for face-down patterns (repeating-linear-gradient) and face-up (rank + suit)
- Suit colors: h/d = red (#e53e3e), c/s = black (#1a202c)
- Felt container has rotateX(10deg) 3D perspective with vignette overlay
- Player name + equity % below cards
- Fully responsive via container-based sizing down to 42px card width
- Helper: `makeDefaultStudHand(upCards, equity, name, isHero)` — accepts 4 up cards, pads to 7

### Pattern for New Variant Components
1. Extract meta.ai HTML → TypeScript types interface
2. Create sub-components (card face, card back, player hand, divider)
3. Create main display component accepting typed props
4. Create helper function mapping API data → component props
5. Export all from barrel index.ts

### BadugiHandDisplay (`components/badugi/BadugiHandDisplay.tsx`)
- Two players (top = villain, bottom = hero)
- 4 cards each: all face-up, null = empty slot (dashed border)
- Dark gradient card body: `linear-gradient(180deg, #23233a 0%, #1c1c2d 100%)`
- Rank top-left, suit bottom-right (different layout from Stud)
- Purple radial vignette overlay on felt container
- Player info: "Name · equity%" on one line
- Partial hands: accept fewer than 4 cards, pad with null
- Helper: `makeBadugiHand(upCards, equity, name, isHero)` — accepts 0-4 cards, pads to 4

## API Layer

```
GET  /api/v1/variants                    → { variants: [...], count: 10 }
GET  /api/v1/variants/{key}              → { key, name, short_name, category, hole_count, board_count, description }
POST /api/v1/variants/{key}/equity       → { hero_equity, villain_equity, iterations, variant, variant_name }
```

Frontend client: `variantApi.list()`, `variantApi.get(key)`, `variantApi.equity(key, hero, villain, board, iterations)`

## Header Navigation Pattern

`apps/web/src/components/Header.tsx` — navTabs array:
```typescript
const navTabs = [
  { href: '/equity', label: "Hold'em" },
  { href: '/equity/plo', label: 'PLO' },
  { href: '/equity/stud', label: 'Stud', badge: 'NEW' },
  { href: '/equity/stud8', label: 'Stud8' },
  { href: '/equity/razz', label: 'Razz' },
  { href: '/equity/badugi', label: 'Badugi' },
  { href: '/equity/2-7td', label: '2-7 TD' },
  { href: '/equity/2-7sd', label: '2-7 SD' },
  { href: '/play', label: 'Play' },
  { href: '/study', label: 'Study', highlight: true },
  { href: '/practice', label: 'Practice' },
  { href: '/analyze', label: 'Analyze' },
]
```
Inline-styled nav with `highlight` prop for accent color on active tab. Emoji badges for NEW tags.

## Git Practices for This Repo

- Always unstage build artifacts before commit: `git restore --staged apps/web/.turbo/ apps/web/public/`
- Run `git add -A` before commit to catch all new files
- Deploy: `docker stop gto-wizard-clone && docker rm gto-wizard-clone` then restart with current image
