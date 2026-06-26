# GTO Wizard Study Page: Purpose Reference

## What it IS
The `/study` page is a **GTO range browser/explorer**. Its job is to let the user browse preflop and postflop ranges by position and stack depth, see GTO action frequencies for each hand, and explore how ranges change across different scenarios. It is a **read-only reference tool**.

Key features (range browser):
- Hand matrix (13×13) with color-coded GTO action frequencies
- Position buttons (UTG/HJ/CO/BTN/SB/BB) that switch the displayed ranges
- Stack depth selector (30bb–200bb)
- Right sidebar with analysis tabs: Overview, Table, Equity Chart
- Sub-tabs: Hand (GTO action display), Summary, Filters, Actions, Blockers
- Postflop mode: board cards, street breadcrumb, pot size, action buttons with GTO frequencies
- "Get GTO Strategy" — queries the live solver for the current spot
- Configure Spot panel for custom postflop scenarios
- Random Spot button

## What it is NOT
The `/study` page is **NOT** a quiz/training tool. Do NOT add:
- "Check vs GTO" action → feedback (correct/incorrect) flows
- Action selection buttons that the user picks to test themselves
- Performance tracking (score/streak/stats)
- "Try Again" buttons
- Hotkeys for action selection during training

## Where training features belong
Interactive training/quiz features (select an action, compare against GTO, track accuracy) belong on the `/practice` or `/train` pages, NOT on `/study`.

## How to work on it
1. Load `docs/reference-study.png` (preflop) or `docs/reference-study-interface.png` (postflop) via `vision_analyze`
2. Load `https://wiz.codeovertcp.com/study` via `browser_navigate` + `browser_vision`
3. Compare element-by-element — match layout, colors, spacing, typography
4. Each visual fix is one commit
5. After each commit, load the live page again and re-compare
6. Do NOT add interactive quiz/training elements

## Historical note
A previous build added an `ActionSelector` component with "Check vs GTO" feedback loop, localStorage stats tracking, and action hotkeys. This was stripped on 2026-06-24 (commit cb0994c — "refactor(study): strip quiz/training flow, convert to pure range viewer"). The `ActionSelector.tsx` file was deleted — do not recreate it.
