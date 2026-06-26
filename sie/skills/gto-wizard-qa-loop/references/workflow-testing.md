# Playwright Workflow Testing — Quality Standard

Current E2E tests (~50+ across 6 spec files) are **~90% existence checks** ("heading is visible", "filter dropdown exists", "stat card shows"). The user has correctly identified this as insufficient. Real value comes from **end-user workflow tests** that simulate how a person actually uses the app.

## Existence Check vs Workflow Test

```
❌ Existence check:
test("page loads", async ({ page }) => {
  await page.goto("/courses");
  await expect(page.locator("h1")).toBeVisible();
});

✅ Workflow test:
test("user browses courses, selects NLH Fundamentals, starts lesson", async ({ page }) => {
  // 1. Navigate from home
  await page.goto("/");
  await page.locator("a[href='/courses']").click();
  await expect(page).toHaveURL(/\/courses/);

  // 2. Find and click a course
  await page.locator("text=NLH Fundamentals").click();

  // 3. Verify detail view loaded
  await expect(page.locator("text=Start Course")).toBeVisible();

  // 4. Start the course
  await page.locator("button:has-text('Start Course')").click();
  await expect(page).toHaveURL(/\/lesson/);

  // 5. Verify lesson content rendered
  await expect(page.locator("h2:has-text('Lesson 1')")).toBeVisible();

  // 6. Interact — submit answer or advance
  await page.locator("button:has-text('Check Answer')").click();

  // 7. Verify feedback shown
  await expect(page.locator("text=Correct")).toBeVisible();
});
```

## Key Differences

| Dimension | Existence Check | Workflow Test |
|-----------|----------------|---------------|
| **What it proves** | Element renders | User can accomplish goal |
| **Assertions** | `toBeVisible()`, `toHaveCount()` | URL change, state change, data mutation |
| **Steps** | 1-2 (goto + assert) | 4-8 (navigate → interact → wait → verify) |
| **Catches** | Missing element | Broken navigation, API failure, state bug, UX gap |
| **Fragility** | Higher (brittle selectors) | Lower (tests real user paths) |

## Workflow Test Priority (GTO Wizard)

1. **Solver workflow**: Browse spots → select "BTN vs BB SRP" → view heatmap → click "Practice This Spot" → solver loads → adjust range → verify results update

2. **Course workflow**: Home → Courses → select course → start lesson → answer question → get feedback → next lesson

3. **Equity calculator workflow**: Home → Equity → set hero range → set villain range → set board → calculate → verify equity percentages shown

4. **ICM workflow**: Home → ICM → configure tournament parameters → calculate → verify payouts and ranges

5. **Cross-page navigation**: Home → Courses → click on course → follow "Practice" link → verify solver page with correct context

## Anti-patterns to Avoid

- **`page.waitForTimeout()`** — fragile. Use `waitForResponse()`, `waitForURL()`, or `waitForSelector()` instead
- **`toBeVisible()` on `.first()`** — hides rendering issues. Be specific about which element
- **`has-text()` without context** — matches any element containing text. Use with `.locator()` chains for precision
- **Conditional assertions** (`if(element.count() > 0)`) — masks test gaps. Tests should assert known state, not conditionally skip
- **Testing the same page load in every spec** — navigation tests belong in one place, not duplicated per spec
