# Playwright Test Quality Assessment — June 2026

## Current State (gto-wizard-clone)

73 tests across 7 spec files, 161 assertions. **56% are `toBeVisible` checks.**

| Category | % of assertions | What's checked |
|---|---|---|
| `toBeVisible` | 56% | "Did the page render?" |
| Truthy/contain | 22% | "Is this truthy?" (often tautologically) |
| Count/length | 12% | "Are there enough elements?" |
| URL/Title | 10% | "Did navigation work?" |
| **Real data validation** | **0%** | **Nothing computes, mutates, or persists** |

## Key Weaknesses

1. **Defensive patterns mask no-ops** — 30+ tests guard every action with `if (await x.count() > 0)` then skip assertions. Tests pass even when features don't exist.
2. **`waitForTimeout(300)`** — Nearly every interaction uses arbitrary timeouts instead of `waitForResponse`, `waitForSelector`, or `waitForLoadState`.
3. **Tautological assertions** — `expect(progressCount).toBeGreaterThanOrEqual(0)`, `expect(hasLegend || true).toBe(true)`, `expect(newLikes >= 0).toBe(true)` — always pass.
4. **No data validation** — No test checks that a calculation produced correct results, that a solver solved, that a quiz gave feedback, that a like persisted, or that a course progressed.
5. **0% real user workflows** — No test simulates a complete user journey (navigate → interact → verify outcome).

## What a Real Workflow Test Looks Like

```typescript
// ❌ Current: existence check
await expect(page.locator("h1:has-text('Equity Calculator')")).toBeVisible();

// ✅ Should be: workflow with data validation
await page.goto("/equity");
await page.click("[data-testid='range-bb']");    // select BB range
await page.click("[data-testid='hand-AdKh']");     // pick AdKh
await page.click("[data-testid='range-btn']");
await page.click("[data-testid='hand-QcQd']");
await page.waitForResponse("/api/v1/equity/calculate");
await expect(page.locator("[data-testid='equity-value']")).not.toBeEmpty();
```

## Critical Workflows Currently Untested

| Workflow | Page | What Should Be Tested |
|---|---|---|
| Node lock solving | /strategies | Set board → solve → heatmap renders |
| Equity calculation | /equity | Select ranges → calculate → verify % |
| Training loop | /train | Answer → feedback → scoring |
| ICM calculation | /icm | Set stacks → calculate → verify equity |
| Course progression | /courses | Enroll → complete lesson → progress |
| Spots → practice | /spots | Select → practice spot → answer |
| HH analysis | /analyze | Upload → hands table → leak report |

## Rewrite Priority

1. **Phase 1:** Remove tautologies, defensive patterns, waitForTimeout. Set `retries: 1`.
2. **Phase 2:** Write solve.spec.ts (node lock solving — the user's specific concern)
3. **Phase 3:** Rewrite equity.spec.ts, icm.spec.ts with real calculation tests
4. **Phase 4:** Write training.spec.ts, courses.spec.ts, analyze.spec.ts
