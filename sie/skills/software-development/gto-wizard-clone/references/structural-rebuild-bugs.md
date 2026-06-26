# GTO Wizard Clone — Structural Rebuild Notes

## The Core Lesson

This session confirmed a critical process failure: **changing colors without fixing structure is wasted effort.**

The GTO Wizard equity page was "close" in color palette but completely wrong in layout. The page had a simple top header + single matrix + result cards, while the real GTO Wizard has:

1. Position flow bar (hand action history)
2. Sub-nav tabs (STRATEGY / RANGES / BREAKDOWN / REPORTS)
3. Position selectors row
4. Range input with Copy/Paste
5. DUAL 13×13 matrices side by side
6. Stats bar (Combos / EV / Equity% / EQR%)
7. Equity distribution bar (win/tie/lose segments)
8. Equity line graph
9. Action breakdown right panel
10. Bottom tabs (HANDS / SUMMARY / FILTERS / BLOCKERS)

## Bug Audit (Pre-Fix)

| # | Bug | Source | Severity |
|---|-----|--------|----------|
| 1 | `grid-cols-14` not in tailwind config — matrix cells stacked vertically | `tailwind.config.ts` | CRITICAL |
| 2 | `heroRange` starts empty, never synced from villain input | `page.tsx:306,396` | CRITICAL |
| 3 | Board input splits by character not by card | `page.tsx:483` | HIGH |
| 4 | Equity chart uses `Math.sin`/`Math.cos` — fake data | `page.tsx:162-172` | HIGH |
| 5 | Position flow bar hardcoded, not API-driven | `page.tsx:66-72` | MEDIUM |
| 6 | EQR formula is nonsensical (`ev/100 + 0.5`) | `page.tsx:427` | MEDIUM |
| 7 | Stats only show hero, not both players | `page.tsx:410-429` | MEDIUM |
| 8 | 3/4 bottom tabs show "coming soon" | `page.tsx:546-548` | MEDIUM |
| 9 | `gto` import unused | `page.tsx:5` | LOW |
| 10 | `MatrixCell` component defined but never used | `page.tsx:101-118` | LOW |

## How Bugs Were Found

Each bug was discovered by **systematic cross-reference** against vision analysis of the real GTO Wizard ranges_tab_overview screenshot:

1. **Grid breakage**: The reference shows 14 columns (1 label + 13 ranks). Checked `tailwind.config.ts` for `grid-cols-14` → missing.
2. **Data flow**: Reference shows hero matrix filled with orange cells. Traced `heroRange` → never populated from `villain` state. Added `useEffect`.
3. **Parsing**: Reference shows 3 card boxes for flop. Checked `board.split("")` → produces 6 chars. Fixed to `board.match(/.{1,2}/g)`.
4. **Formula**: Reference shows real equity line. Found `Math.sin` in chart code → fake data. Replaced with equity-based bars.
5. **Dead code**: Read through imports → found `MatrixCell` defined and `gto` import that were never used.

## The Vision QA Pipeline

Located at `/workspace/gto-vision-qa.py`.

Checks 29 structural elements across equity/solver/strategy pages. Run:

```bash
python3 /workspace/gto-vision-qa.py all          # Full sweep (5 pages)
python3 /workspace/gto-vision-qa.py check equity  # Single page
python3 /workspace/gto-vision-qa.py references    # Available screenshots
```

The QA script checks source code for keyword presence. It's a structural check, NOT a visual comparison tool. For true visual comparison, use `vision_analyze` on screenshots of the running app against reference screenshots.

## Critical: Design Skills Were Never Loaded

During the frontend redesign, these skills should have been loaded but weren't:
- `creative/vision-driven-ui-replication` — has the full structural audit process
- `software-development/systematic-debugging` — has the debugging patterns
- `creative/popular-web-designs` — design system references
- `creative/sketch` — for mockups before coding

Always check: "Does the task involve replicating an existing UI?" If yes, load `creative/vision-driven-ui-replication` as the primary skill.
