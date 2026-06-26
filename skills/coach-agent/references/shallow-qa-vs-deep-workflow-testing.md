# Shallow QA vs Deep Workflow Testing (2026-06-23)

## Problem

The Coach's Live Site QA protocol mandates "≥5 interactions" and "execute the full workflow end-to-end," but in practice the Coach has been doing **shallow page-load testing**:

- `browser_navigate(url)` → check 200
- `browser_console(clear=true)` → check 0 errors
- `browser_snapshot` → verify elements exist
- List all pages with HTTP status

This is what the 2026-06-23 coach reviews of gto-wizard-clone actually did. They confirmed "all pages return 200, 0 JS errors" but never once:
- Clicked a position button on the study page
- Selected an action and checked GTO feedback
- Advanced through streets (flop→turn→river)
- Tested the "Check vs GTO" flow end-to-end

## Why It Matters

The Player has completed 36 tasks and the study page *looks* functional (200 OK, 0 errors) but the core training loop — pick position → see range → take action → get GTO feedback → advance street → repeat — was never validated. This is the exact pattern that causes "plateau before MVP": pieces exist, core loop doesn't work.

## Root Cause

The skill says "≥5 interactions" but doesn't provide a **concrete test script** or **mandatory interaction sequence**. The Coach optimizes for coverage (check all pages quickly) rather than depth (test one workflow deeply). The "Minimal Acceptable Bar" is aspirational, not enforced.

## The Fix: Mandatory Workflow Test Sequence

For apps with an interactive core loop (study pages, calculators, games), the Coach MUST execute this sequence — not just page loads:

### GTO Wizard Study Page — Mandatory Workflow Test

```
1. browser_navigate("/study")
2. browser_console(clear=true) → record errors
3. browser_snapshot → identify position buttons, mode toggle
4. CLICK a position button (e.g., BTN) → verify visual state change (highlight, data update)
5. CLICK "Postflop Training" toggle → verify board cards appear
6. CLICK "Get GTO Strategy" or "Solve" → verify action buttons render with GTO frequencies
7. CLICK an action button (e.g., "Raise 2.5bb") → verify feedback (GTO comparison, EV, correct/incorrect)
8. CLICK "Advance to Turn" → verify new board card appears, pot updates, new action buttons
9. CLICK an action on turn → verify feedback
10. CLICK "Advance to River" → verify board, actions, feedback
11. browser_console → check for new errors after interactions
```

**If any step fails, that is a FINDING — record it, do not silently pass.**

### Equity Calculator — Mandatory Workflow Test

```
1. browser_navigate("/equity")
2. browser_console(clear=true)
3. Type hand inputs (e.g., "AKs" and "JJ")
4. CLICK "Calculate" → verify equity result appears
5. Check result is reasonable (e.g., AKs vs JJ ≈ 55-60%)
6. browser_console → check for errors
```

### General Rule

For any app with a primary user workflow:
- **Minimum 3 interactions** that change state (not just loading)
- **Console check AFTER interactions** (not just after page load)
- **Report each interaction and its result** — "Clicked X, expected Y, got Z"
- **If an interaction does nothing, that is a finding**

## Evidence from 2026-06-23

Coach review of gto-wizard-clone (23:17): Loaded 12 pages, all 200 OK, 0 errors. Never clicked a single button. Approved the project. User asked "has coach even tried to use study to see gTO solutions for a hand start to finish" — answer was no.
