# StudHandDisplay — meta.ai → React Conversion Log

Converted June 14, 2026 from meta.ai HTML output to a reusable Next.js component.

## Source
meta.ai prompt: "Create a dark-themed Seven Card Stud hand display component..."
Output: Single self-contained HTML file (~412 lines) with inline CSS.

## What meta.ai Did Well
- Responsive breakpoints at 780px, 620px, 440px, 360px — production-quality
- Card face-down pattern using repeating-linear-gradient — looked great
- 3D perspective on felt container (rotateX + box-shadows) — immersive feel
- Suit symbols and rank positioning — correct typography
- Divider with gradient glow effect — nice touch
- Hover animation on cards (translateY(-5px))

## What Needed Changing
1. **Pseudo-elements** — CSS `::before`/`::after` became separate `<div>` elements with absolute positioning
2. **CSS variables/classes** → all inlined into React `style={}` objects
3. **Static HTML** → dynamic React props (cards, equity, player names)
4. **No TypeScript** → added full type interfaces (`StudCardData`, `StudPlayerData`)
5. **No reuse abstractions** → extracted `StudCard`, `PlayerHand` sub-components
6. **No data wiring** — needed `makeDefaultStudHand()` helper to bridge API → component props
7. **Fixed width cards** → added `flexShrink: 0` / `shrink-0` to prevent flex collapse

## Final Component API

```tsx
interface StudCardData {
  rank?: string;     // undefined for face-down cards
  suit?: string;     // undefined for face-down cards
  faceUp: boolean;
}

interface StudPlayerData {
  name: string;
  cards: StudCardData[];  // 7 elements
  equity: number;
  isHero: boolean;
}

interface StudHandDisplayProps {
  hero: StudPlayerData;
  villain: StudPlayerData;
  className?: string;
}
```

## Usage in a Page

```tsx
import { StudHandDisplay, makeDefaultStudHand } from "@/components/stud";

// Transform API result into visual props
const heroHand = makeDefaultStudHand(
  [{ rank: "A", suit: "s" }, { rank: "K", suit: "h" }, ...],
  result.hero_equity,
  "Hero",
  true
);

<StudHandDisplay hero={heroHand} villain={villainHand} />
```

## File Locations
- `apps/web/src/components/stud/StudHandDisplay.tsx` — main component (~225 lines)
- `apps/web/src/components/stud/index.ts` — barrel export
- `apps/web/src/app/equity/stud/page.tsx` — page using the component
- `apps/web/src/app/equity/razz/page.tsx` — reuses the same component
