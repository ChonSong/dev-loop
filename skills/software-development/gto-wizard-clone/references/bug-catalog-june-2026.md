# Bug Catalog — GTO Wizard Clone (June 2026)

Bugs found during the structural rebuild of the equity page, discovered by cross-referencing rendered code against vision-analyzed GTO Wizard reference screenshots.

## Bug 1: `grid-cols-14` Missing from Tailwind Config

**File**: `/workspace/open-lovable/tailwind.config.ts`
**Symptom**: The 13×13 hand matrix rendered as a single column — all 169 cells stacked vertically
**Root cause**: The `HandMatrix` and `RangeBuilder` components use `grid-cols-14` (1 label column + 13 rank columns) but only `grid-cols-13` was defined in `tailwind.config.ts`
**Fix**: Added `'14': 'repeat(14, minmax(0, 1fr))'` to `gridTemplateColumns` and `gridTemplateRows`
**Detection**: Check tailwind config against grid class usage in components

## Bug 2: Hero Range Matrix Never Populated

**File**: `/workspace/open-lovable/app/gto/equity/page.tsx`, line 306
**Symptom**: Left (hero) 13×13 matrix showed all cells as dark/unselected — looked broken
**Root cause**: `heroRange` initialized as `new Set<string>()` (empty) with no mechanism to sync from the villain range input. Clicking "Top 5%" called `setVillain("AA,KK,...")` but `heroRange` stayed empty
**Fix**: Added `useEffect(() => setHeroRange(parseRange(villain)), [villain])`
**Prevention**: Any pair of parallel UI elements sharing related data must have a sync mechanism. A `useEffect` that derives one state from the other is the standard React pattern.

## Bug 3: Board Input Split by Character, Not by Card

**File**: `/workspace/open-lovable/app/gto/equity/page.tsx`, line 483
**Symptom**: Board "Kd7h2c" displayed as 6 individual character boxes instead of 3 card pairs
**Root cause**: `board.split("")` splits every character. "Kd7h2c" → ["K","d","7","h","2","c"]
**Fix**: Replaced with `board.match(/.{1,2}/g)` to group into 2-character card pairs
**Prevention**: When displaying card strings, always group `.match(/.{1,2}/g)` or parse via regex `/([2-9TJQKA][shdc])/g`

## Bug 4: Equity Chart Used Fake Random Data

**File**: `/workspace/open-lovable/app/gto/equity/page.tsx`, lines 162-172
**Symptom**: The "equity graph" showed wavy lines based on `Math.sin(i/3)` and `Math.cos(i/4)` — completely unrelated to actual equity data
**Root cause**: The `EquityChart` component generated pseudo-random SVG polylines from trigonometric functions instead of using real result data
**Fix**: Replaced with data-derived action bars showing fold/call/raise percentages based on actual equity values
**Prevention**: Any data visualization component must derive from real API response data, not synthetic values. String search for `Math.sin`/`Math.cos`/`Math.random` in chart components.

## Bug 5: EQR Formula Was Nonsensical

**File**: `/workspace/open-lovable/app/gto/equity/page.tsx`, line 434
**Symptom**: EQR (Equity Realized) showed meaningless values
**Root cause**: Formula `result.ev_per_hand / 100 + 0.5` has no relationship to real EQR calculation
**Fix**: Replaced with `Math.abs(result.ev_per_hand) / result.equity / 100 * 100`
**Prevention**: Verify every derived-value formula against its mathematical definition. Do not write placeholder formulas.

## Bug 6: Unused `MatrixCell` Component

**File**: `/workspace/open-lovable/app/gto/equity/page.tsx`, lines 101-118
**Symptom**: Component defined but never imported or rendered anywhere in the JSX
**Root cause**: `HandMatrix` uses inline JSX for cells instead of the `MatrixCell` component
**Fix**: Removed the dead component
**Prevention**: After writing a component, verify it's actually imported and used. Search for the function name after the definition.

## Bug 7: Unused `gto` Import

**File**: `/workspace/open-lovable/app/gto/equity/page.tsx`, line 5
**Symptom**: `import { gto, actionColor, equityColor }` — `gto` never used
**Fix**: Removed `gto` from the import
**Prevention**: Check that all named imports are referenced at least once in the file body.

## Bug 8: "Coming Soon" Placeholders in Bottom Tabs

**File**: `/workspace/open-lovable/app/gto/equity/page.tsx`, lines 546-548
**Symptom**: Three of four bottom tabs (FILTERS, HANDS, BLOCKERS) show "coming soon" text
**Root cause**: Placeholder text never replaced with real content
**Fix**: Added filter buttons, hand list from heatmap data, blockers info showing known cards
**Prevention**: Before deploying any page, grep for "coming soon", "TODO", "placeholder", "TBD" and replace with real content or remove the element.

## Bug 9: Wrong API Endpoint Path

**File**: `/workspace/open-lovable/app/gto/strategy/page.tsx`, line 132
**Symptom**: Strategy page crashed with `e.map is not a function`
**Root cause**: Used `${API}/strategy/lookup` but the correct endpoint is `${API}/strategy` (GET list). `/strategy/lookup` was interpreted as strategy key "lookup" which failed the key parser
**Fix**: Changed URL to `${API}/strategy`
**Prevention**: Verify API endpoint paths against the actual Swagger docs at `/docs`. The path structure in FastAPI routers is explicit — check the `@router.get()` decorator, not assumptions about RESTful naming.

## Bug 10: API Response Shape Mismatch

**File**: `/workspace/open-lovable/app/gto/strategy/page.tsx`, line 140
**Symptom**: `setStrategies(await r.json())` followed by `strategies.map(s => ...)` — when API returns `{detail: "..."}` instead of an array, `.map` crashes
**Root cause**: No type guard before treating response as an array
**Fix**: Added `Array.isArray(data)` check, with fallback for `data?.strategies` property shape
**Prevention**: Always guard API responses: `if (Array.isArray(data)) { ... } else { handle gracefully }`. Never assume the API returns the expected shape.
