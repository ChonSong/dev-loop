# Workflow Test Audit Methodology

How to audit an existing Playwright test suite for real workflow coverage vs existence checks.

## Quick Assessment

Run this on any project's e2e directory to get the baseline:

```bash
for f in apps/web/e2e/*.spec.ts; do
  lines=$(wc -l < "$f")
  assertions=$(grep -c 'expect(' "$f" || true)
  clicks=$(grep -c '\.click(' "$f" || true)
  navigations=$(grep -c '\.goto\|waitForURL' "$f" || true)
  visible=$(grep -c 'toBeVisible\|toBeAttached\|toHaveCount' "$f" || true)
  echo "$(basename $f): ${lines}lines ${assertions}assertions ${clicks}clicks ${navigations}navs"
done
```

## Categorization Reference

### Existence Check (low value)
```typescript
await expect(heading).toBeVisible();
await expect(page.locator("button")).toHaveCount(3);
await expect(page).toHaveTitle(/GTO/);
```
These tell you the page rendered. They do NOT tell you:
- Whether clicking the button does anything
- Whether the data is correct
- Whether the user can complete a task

### Interaction Test (medium value)
```typescript
await filter.selectOption("intermediate");
await page.waitForTimeout(300);
await expect(heading).toBeVisible();
```

### Workflow Test (high value)
```typescript
await page.goto("/");
await page.locator('a[href="/courses"]').click();
await page.waitForURL(/\/courses/);
// interact with courses
await page.locator("button", { hasText: "Start" }).click();
// verify state change
await expect(page.locator("text=/Progress/)).toBeVisible();
```

## Pass Thresholds

| Metric | Threshold |
|---|---|
| Existence checks as % of total assertions | < 50% |
| Workflow tests as % of total tests | > 30% |
| Cross-app navigation tests | > 2 per app |
| Data validation tests per data-displaying page | > 1 |

## Session Audit (2026-06-14: GTO Wizard)

73 total tests (64 original + 9 new workflow tests).

Original 64 tests were ~90% existence checks, ~10% interaction, 0% workflow.
New 9 tests are 100% workflow (multi-step navigation, cross-app, solver interaction).
