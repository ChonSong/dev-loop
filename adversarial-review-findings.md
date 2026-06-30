# Adversarial Review Findings — fix-game-tree-equal-action-rule Phase 1 (6e67d20)

## Novel Findings (6 total)

### 🔴 HIGH: isPreflopRoundComplete — folded players incorrectly required to act after raise
**File:** `apps/web/src/app/study/page.tsx`, lines 234–266

**Bug:** When a player folds BEFORE the last raise, the function requires them to have "acted after" the raise too, but they can't because they already folded. This causes a **false negative** for genuinely complete rounds.

**Trace:**
Given path: `[{UTG: fold}, {HJ: fold}, {CO: raise}, {BTN: call}, {SB: call}, {BB: call}]`
- Raisers: CO at idx 2 (actedAfter = {BTN, SB, BB})
- Loop checks all 5 positions after CO: BTN ✓, SB ✓, BB ✓, **UTG ✗** (actedAfter has no UTG)
- Returns **false** — but round IS complete (UTG & HJ folded, remaining 4 active players all called)

**Impact:** Auto-transition from preflop→postflop silently fails for common 2+ fold scenarios. User gets stuck in preflop mode.

**Fix:** Track which positions are still active (haven't folded) and only require those to have acted after the raise.

### 🔴 HIGH: Auto-advance timer not cleared on manual "Advance to Next Street"
**File:** `apps/web/src/components/study/PostflopTraining.tsx`, lines 544–553

**Bug:** `advanceToNextStreet()` does NOT call `clearTimeout(autoAdvanceRef.current)`. If a user:
1. Takes an action → 1.5s timer starts
2. Manually clicks "Advance to Turn" → street advances, but timer still pending
3. 1.5s timer fires → calls `advanceToNextStreetRef.current()` again → **double-advances to river with a default 'check' action** (user never chose turn action)

**Additionally:** Config panel board/pot/stack inputs (lines 649–657) also don't clear the timer. Changing board state while a timer is pending can lead to inconsistent state on auto-advance.

**Fix:** Add `if (autoAdvanceRef.current) clearTimeout(autoAdvanceRef.current)` at the start of `advanceToNextStreet()` and in config panel change handlers.

### 🟡 MEDIUM: CI workflow references non-existent E2E test file
**File:** `.github/workflows/e2e-game-tree.yml` (new file)

**Bug:** Workflow triggers on changes to `e2e/study-game-tree.spec.ts` and runs `npx playwright test --grep "game-tree"` — but **`e2e/study-game-tree.spec.ts` does not exist** in the repo (confirmed by `ls e2e/`). The workflow will fail loudly on any trigger.

**Also:** `BASE_URL: 'https://wiz.codeovertcp.com'` is hardcoded instead of using a GitHub Secret or variable.

### 🟢 LOW: `||` instead of `??` for pot_size fallback
**File:** `apps/web/src/app/study/page.tsx`, line 181

```tsx
setPfPot(treeNode?.pot_size || 5.5)
```

`||` incorrectly defaults to 5.5 if `pot_size` is literally 0 (theoretical but impossible in practice). Should use `??` for nullish coalescing.

### 🟢 LOW: Position order hardcoded to 6-max
**File:** `apps/web/src/app/study/page.tsx`, line 232

```tsx
const POSITION_ORDER = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB'] as const
```

Both `isPreflopRoundComplete` and `isAllFold` depend on this array being exactly 6 entries. Heads-up or short-handed configurations would break silently (wrong index math, wrapping issues).

## Summary

| Finding | Severity | Type | Novel? |
|---------|----------|------|--------|
| isPreflopRoundComplete ignores folded players | HIGH | Methodology bug | Yes |
| Manual advance doesn't clear auto-advance timer | HIGH | Logic bug | Yes |
| CI workflow references non-existent test file | MEDIUM | Dead code | Partially (primary noticed missing file) |
| Hardcoded production URL in CI | LOW | Robusness | Yes |
| `||` vs `??` fallback | LOW | Style/Robustness | Yes |
| Hardcoded 6-max positions | LOW | Extensibility | Yes |

**2 HIGH-severity novel bugs confirmed as missed by primary reviewer.**
