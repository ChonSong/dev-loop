# GTO Wizard E2E Test Audit — 2026-06-14

Full audit of 73 tests across 7 spec files. Key findings: 56% existence checks, 0% data validation.

## Aggregate Metrics

| Metric | Value |
|---|---|
| Total tests | 73 |
| Total assertions (expect()) | 161 |
| toBeVisible | 85 (52.8%) |
| toBe/toBeTruthy/toContain | 35 (21.7%) |
| toHaveCount/Length/Value/Greater | 19 (11.8%) |
| toHaveURL/toHaveTitle | 16 (9.9%) |
| toBeAttached/toBeEnabled | 5 (3.1%) |
| toContainText | 1 (0.6%) |
| Data validation | 0 (0.0%) |
| **Existence checks** | **~90 (55.9%)** |
| **Multi-step workflows (3+ actions)** | **15 (20.5%)** |
| Tests with conditional no-ops | 30+ |

## File-by-File Breakdown

| File | Tests | Expects | % Visible | Weaknesses |
|---|---|---|---|---|
| courses.spec.ts | 13 | 27 | 70% | 4 conditional tests, waitForTimeout flakiness |
| equity.spec.ts | 6 | 17 | 82% | Pure existence, no range interaction |
| icm.spec.ts | 9 | 23 | 52% | Weak ICM results assertion (anything passes) |
| spots.spec.ts | 13 | 24 | 71% | 11/13 may no-op silently |
| strategies.spec.ts | 9 | 14 | 57% | Tautologies (hasLegend\|\|true), generic selectors |
| pwa.spec.ts | 14 | 35 | 14% | Best coverage, 7 conditional tests |
| workflows.spec.ts | 9 | 21 | 48% | 0 data-validation assertions; 1 test has 0 expects |

## Tautological Assertions Found

These assertions always pass regardless of app state — they provide false confidence:

```
expect(progressCount).toBeGreaterThanOrEqual(0)     // always true
expect(hasLegend || true).toBe(true)                 // always true  
expect(newLikes >= 0).toBe(true)                     // always true (newLikes is number)
expect(hasContent || hasDetail).toBeTruthy()          // rarely falsifiable
expect(hasEquity || hasDollarValues || true).toBe(true) // always true
```

## Defensive No-Op Pattern

30+ tests guard every action with conditional checks, then skip assertions if the element doesn't exist:

```typescript
if (await firstCourse.count() > 0) {
  // only then test anything
}
```

This means the test passes even when the feature being tested doesn't render. A broken courses page with no course cards would still pass test #5.

## What's NOT Tested (Critical Gaps)

| Feature | Current Coverage | What's Missing |
|---|---|---|
| Solver (node lock solving) | Page loads, heading exists | Submit a solve job, wait for WebSocket response, verify heatmap renders |
| Equity calculation | Page loads, range grid headings | Select a range cell, set board, trigger calculate, verify equity % |
| Training quiz loop | Page loads, start session | Answer a spot, verify feedback (correct/incorrect), verify accuracy tracking |
| ICM calculation | Fill form fields | Click calculate, verify equity results render as dollar values |
| Course progression | Select a course | Start course, complete lesson, verify progress updates |
| Spots → Practice pipeline | Click a spot card | Click "Practice This Spot", verify redirect to practice with spot context |

## Workflow Test Design Template

Replace existence checks with this pattern:

```typescript
test("user browses spots and inspects solution", async ({ page }) => {
  // 1. Navigate to feature
  await page.goto("/spots");
  await expect(page.locator("h1, h2").filter({ hasText: /Spot/i })).toBeVisible();
  
  // 2. Interact (filter, search, click)
  const spotButton = page.locator("button").filter({ hasText: /BTN|BB/i }).first();
  if (await spotButton.count() > 0) {
    await spotButton.click();
    await page.waitForResponse(/api/);  // wait for API, not timeout
  }
  
  // 3. Verify state change
  await expect(page.locator("text=Strategy Heatmap").first()).toBeVisible();
  
  // 4. Navigate to related feature
  await page.locator('a[href="/study"]').first().click();
  
  // 5. Interact again
  const posButtons = page.locator("button").filter({ hasText: /UTG|HJ|CO|BTN|SB|BB/i });
  expect(await posButtons.count()).toBeGreaterThanOrEqual(3);
  await posButtons.nth(0).click();
  
  // 6. Verify cross-feature state
  await expect(page).toHaveURL(/\/study/);
});
```

## Automated Audit Script

Use this Python snippet to categorize assertions across any Playwright test suite:

```python
import re

def audit_test_file(content):
    expects = re.findall(r'expect\(.*?\)\.(to\w+)\(', content)
    interactions = re.findall(r'\.(click|fill|selectOption|goto|type)\(', content)
    tautologies = re.findall(r'toBeGreaterThanOrEqual\(0\)|toContain\(true\)\|\|true', content)
    return {
        "total_assertions": len(expects),
        "visible_checks": expects.count("toBeVisible"),
        "url_title_checks": expects.count("toHaveURL") + expects.count("toHaveTitle"),
        "data_checks": expects.count("toContainText") + expects.count("toHaveValue"),
        "interactions": len(interactions),
        "tautologies": len(tautologies),
    }
```

## Target Metrics for a Healthy Suite

| Metric | Current (GTO) | Target |
|---|---|---|
| Workflow tests (>3 steps) | 15 (20%) | >40 (55%) |
| Data validations | 0 | >30 (20%) |
| Existence checks | ~90 (56%) | <50 (30%) |
| Tautological assertions | 5+ | 0 |
| Conditional no-ops | 30+ | <5 |
| waitForTimeout usage | ~43 calls | 0 (use waitForResponse/waitForSelector) |
