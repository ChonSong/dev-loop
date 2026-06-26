# GTO Wizard Training Page Design — June 2026

Canonical design spec provided as a single-file HTML mockup by the user. Rebuilt as React/Next.js in `app/gto/training/page.tsx` and `app/gto/layout.tsx`.

## Layout Architecture

```
app/
  gto/
    layout.tsx       ← Nav + sidebar wrapper (client component, inline styles)
    training/
      page.tsx        ← Full training page (setup view + training view + modal)
```

Both are `"use client"` components. No Tailwind classes in the new layout — all styling via inline `style={{}}`.

## Component State Machine

### State variables

| Variable | Type | Default | Controls |
|----------|------|---------|----------|
| `showTraining` | boolean | false | Which view is visible (setup vs training) |
| `selectedAction` | string | "Any" | Active preflop action chip |
| `startingSpot` | string | "Flop" | Active segment in starting-spot control |
| `modalOpen` | boolean | false | Solutions library modal visibility |
| `bannerVisible` | boolean | true | Guide banner visibility |
| `activeTool` | string | "focus" | Active tool in the toolbar |
| `infoTab` | "strategy"\|"range" | "strategy" | Active tab in info panel |

### View transitions
- START TRAINING → `setShowTraining(true)` — hides setup view, shows training view
- Practice tab click (from top nav) → `setShowTraining(false)` — returns to setup
- Banner close → `setShowBannerVisible(false)`
- Solutions pill / ALL SETTINGS → `setModalOpen(true)`
- Modal backdrop click / CONFIRM / close button → `setModalOpen(false)`

## Design Spec Commands

### Seat Positions (setup view oval)
```javascript
const SEATS = [
  { name: "CO",  top: "0%",  left: "50%" },
  { name: "BTN", top: "20%", left: "82%" },  // has dealer button badge
  { name: "SB",  top: "54%", left: "94%" },
  { name: "BB",  top: "92%", left: "74%" },
  { name: "UTG", top: "92%", left: "26%" },
  { name: "HJ",  top: "54%", left: "6%" },
];
```
All seats: 64×64px circle, `#222426` bg, `#44474c` border, 16px bold font.

### Training View Table Oval
- BB seat: `16% 22%`, `#e67e22` border with 3px glow
- CO seat: `84% 82%`, `#00b894` border with 3px glow
- Hero cards attached to CO: 44×62px white cards, 24px suit symbols (♥ red #e23b3b, ♣ green #0a7a4f)
- Board cards: 58×80px white cards with 34px rank + 20px suit

### Action Buttons
```
CHECK: #27ae60 bg, #1e8449 inset shadow, #eafff1 text, 17px padding, 13px radius
BET:   #c0392b bg, #922b21 inset shadow, #ffeae8 text, 17px padding, 13px radius
```
Both: `fontWeight:800, fontSize:16, textTransform:uppercase, letterSpacing:.4px`

### 13×13 Matrix Colors
| Class | Background | Text |
|-------|-----------|------|
| `green3 hl` | `#1a7a44` (diamond highlight) | `#e2ffe9` |
| `green1` | `#27ae60` | `#eafff3` |
| `green2` | `#219653` | `#eafff3` |
| `green3` | `#1a7a44` | `#e2ffe9` |
| `green4` | `#58d68d` | `#062c18` |
| `red1` | `#c0392b` | `#ffe9e6` |
| `red2` | `#a93226` | `#ffd5d0` |
| `gray` | `#3a3f44` | `#9aa1a9` |

Cells: 3px gap, 6px padding, 4px radius, 10px font weight 700, `#171a1d` border.

### Solutions Modal Filter Groups
Locked filters (`isLocked`): Short, Ante, Straddle, Bomb pot, 9max, Multi Size, NL50-NL500, 3x, 2x, 2.25x
NEW-badge filter: Single Size (postflop bet sizes)
Multi-select rows: Effective stack, Opening size (toggle, not singleton)

## Files to Edit for Future Design Changes

- Layout structure (nav + sidebar): `app/gto/layout.tsx`
- Training page: `app/gto/training/page.tsx`
- Design tokens: `styles/gto-tokens.ts` (exported constants used by other pages)
- Old layout still on disk but overridden: `app/gto/layout.tsx` was fully replaced

## Pitfalls Encountered

1. **Duplicate style properties crash compilation** — TypeScript rejects objects with the same key twice. When a style object spread has `cursor:"pointer"` and a conditional `cursor: isLocked ? "not-allowed" : "pointer"`, the build fails with `An object literal cannot have multiple properties with the same name.` Fix: remove the static default from the spread, keep only the conditional.

2. **Zombie dev servers serve stale code** — Old `next-server` processes survive across sessions. The new `next dev` fails with EADDRINUSE silently, and the old process (with old code) continues serving. Fix: `kill -9 $(lsof -t -i :PORT)` before starting.

3. **Background process PATH issues** — `npx` and `node` are at `/home/hermeswebui/.hermes/home/.local/bin/` which isn't on the default PATH for background processes. Always export PATH explicitly in background terminal commands.

4. **Backend needs PYTHONPATH** — When running `uvicorn apps.api.main:app` from the repo root, set `PYTHONPATH=/workspace/gto-wizard-clone` to resolve imports like `from apps.api.websocket.manager import ...`.
