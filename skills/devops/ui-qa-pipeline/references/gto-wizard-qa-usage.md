# GTO Wizard QA Pipeline — Session Notes

## What Was Built

A comprehensive Puppeteer QA suite (`/workspace/ui-qa-tool/qa-suite-v2.js`) that tests all 14 GTO Wizard clone pages:

- **127 total checks** across 14 pages
- Content-based selectors (text, placeholders, labels, headings)
- JS error, console error, and HTTP error detection
- Screenshots of every page
- Retry logic (3 attempts) and browser restart every 5 pages
- Filters out Next.js dev server stale chunk noise

## Final Result

**14/14 pages pass, 127/127 checks pass, 0 warnings, 0 failures.**

## Key Bugs Found and Fixed

1. **Equity page missing H1 heading** — Every other page had `<h1>Page Title</h1>` but equity didn't. Fixed by adding `<h1 className="text-[16px] font-bold text-white">Equity Calculator</h1>` to `/workspace/open-lovable/app/gto/equity/page.tsx`.

2. **Button selectors with emoji prefixes** — Hands page tabs were `"📥Import"`, `"📜History"`, `"🔍Analysis"` (no space between emoji and text). Required `startsWith` matching instead of exact match.

3. **Old QA was grep-based** — The previous `gto-vision-qa.py` grepped source code for string patterns. It reported 0 issues on broken pages. Replaced with real DOM testing.

## DOM Inspector Tool

`/workspace/ui-qa-tool/dom-inspector.js` — Dumps the rendered DOM structure of every page to JSON. Use this to discover actual selectors before writing QA checks.

```bash
cd /workspace/ui-qa-tool && node dom-inspector.js
# Output: /workspace/qa-dom-dumps/<page>.json
```

## Running the Suite

```bash
cd /workspace/ui-qa-tool && node qa-suite-v2.js
```

Screenshots: `/workspace/qa-screenshots/<page>.png`
Reports: `/workspace/qa-reports/qa-v2-<timestamp>.json`

## Page Check Coverage

| Page | Checks | Key Elements Verified |
|------|--------|----------------------|
| equity | 19 | H1, sub-nav tabs, position selectors, range input, hand matrix, copy/paste, quick ranges, calculate/heatmap/EV buttons |
| solver | 9 | H1, game type selector, board input, stack/pot/iterations labels, run solver button, presets |
| strategy | 11 | H1, filter headings, game type/position/street/action labels, reset button, NLH/PLO toggles |
| hands | 9 | H1, import/history/analysis tabs, textarea, import button, batch upload, file input |
| training | 7 | H1, new question/review/leaderboard buttons, accuracy/correct/streak stats |
| bomb-pot | 10 | H1, hero/villain/board inputs, iterations/pot/players labels, calculate/resolve buttons, street tabs |
| courses | 3 | H1, empty state text |
| double-board | 8 | H1, hero/villain/boards inputs, iterations label, calculate button, presets |
| icm | 7 | H1, players/stacks/prizes inputs, calculate button, presets |
| leaks | 13 | H1, analyze/baseline/compare headings, hand IDs/spot category inputs, analyze/compare/summary buttons, category quick buttons |
| omaha | 10 | H1, Hi-Lo/PLO5/Short Deck sub-tabs, hero/villain/board inputs, calculate button, hand presets |
| plo4 | 10 | H1, hero/villain/board inputs, iterations label, calculate/heatmap/rankings buttons, hand presets |
| spots | 4 | H1, new spot button, empty state |
| auth | 7 | H1, email/password inputs, login/register toggle, sign in button, continue without account |
