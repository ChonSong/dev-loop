# BadugiHandDisplay — meta.ai → React Conversion Log

Converted June 14, 2026 from meta.ai HTML output (~236 lines) to a reusable Next.js component.

## Source
meta.ai prompt: "Create a dark-themed Badugi hand display component..."
Output: Single self-contained HTML file with inline CSS.

## Key Differences from StudHandDisplay

| Aspect | StudHandDisplay | BadugiHandDisplay |
|--------|-----------------|-------------------|
| Cards per player | 7 (2 down + 4 up + 1 down) | 4 (all face-up) |
| Card style | White face-up (#f7fafc), patterned face-down | Dark gradient (#23233a → #1c1c2d) |
| Rank/suit layout | Center suit, both corners rank | Top-left rank only, bottom-right suit |
| Empty slots | Not applicable (always 7 cards) | Dashed border, transparent (partial hands) |
| Container width | max-width: 900px | max-width: 360px |
| Player info | name above, equity below | Both on same line with · separator |
| Felt transform | rotateX(10deg) with heavy shadow | No 3D, simpler shadow, purple vignette |
| Hero glow | Text shadow only | Card border glow (rgba(120,130,255,0.08)) |

## What meta.ai Did Well
- Compact layout works at 360px max width — more appropriate for 4 cards
- Empty slot dashes are clear and thematic
- Dark gradient card body looks premium (better than white for this context)
- Purple vignette overlay on felt is subtle and adds depth
- Divider gradient matched the dark theme

## What Needed Changing
1. **Static data** → dynamic React props (`BadugiCardData`, `BadugiPlayerData`)
2. **No TypeScript** → added full interfaces
3. **Hardcoded equity** → accepts equity number from API
4. **No helper** → added `makeBadugiHand()` for API data → props
5. **No empty slot abstraction** → `BadugiCard({ card })` handles null → empty slot rendering
6. **No barrel export** → created `components/badugi/index.ts`

## Final Component API

```tsx
interface BadugiCardData {
  rank: string;
  suit: string;
}

interface BadugiPlayerData {
  name: string;
  cards: (BadugiCardData | null)[];  // null = empty slot
  equity: number;
  isHero: boolean;
}

interface BadugiHandDisplayProps {
  hero: BadugiPlayerData;
  villain: BadugiPlayerData;
  className?: string;
}
```

## Usage

```tsx
import { BadugiHandDisplay, makeBadugiHand } from "@/components/badugi";

const heroHand = makeBadugiHand(
  [{ rank: "A", suit: "s" }, { rank: "2", suit: "h" }, { rank: "3", suit: "d" }, { rank: "4", suit: "c" }],
  result.hero_equity, "Hero", true
);

// Partial hand (3 cards, 4th is null → empty slot)
const villainHand = makeBadugiHand(
  [{ rank: "K", suit: "h" }, { rank: "7", suit: "h" }, { rank: "5", suit: "s" }],
  result.villain_equity, "Villain", false
);

<BadugiHandDisplay hero={heroHand} villain={villainHand} />
```

## File Locations
- `apps/web/src/components/badugi/BadugiHandDisplay.tsx` — main component
- `apps/web/src/components/badugi/index.ts` — barrel export
- `apps/web/src/app/equity/badugi/page.tsx` — page using the component

## Key Pattern: Empty Slot Rendering

```tsx
function BadugiCard({ card }: { card: BadugiCardData | null }) {
  if (card === null) {
    return (
      <div style={{
        width: 72, height: 100, borderRadius: 10,
        border: "2px dashed #3a3a5a",
        flexShrink: 0, opacity: 0.7,
      }} />
    );
  }
  // ... face-up card rendering
}
```
