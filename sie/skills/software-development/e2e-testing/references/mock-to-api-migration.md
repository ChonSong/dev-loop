# Mock Data to API Migration — E2E Test Impact

When a page switches from hardcoded mock data to live API responses, E2E tests that assert on mock-specific text, values, or element structure will break. This reference catalogs what to expect and how to fix.

## What Breaks

### 1. Static labels change
Mock data pages often have descriptive labels that don't match the real API schema.

| Mock label | API label | Root cause |
|------------|-----------|-----------|
| "Courses Started" | "Courses Available" | Mock showed user progress; real API shows catalog |
| "Lessons Completed" | "Total Lessons" | Per-user mock vs global aggregate |
| "Time Spent" | "Started" | Hardcoded sidebar vs computed fields |

**Fix:** Update text assertions to match the API-backed page. Use `.first()` when text appears twice (stat cards + sidebar).

### 2. Numeric counts change
Mock data had hardcoded totals (6 courses, 61 lessons, 13.5h). The API returns whatever is seeded.

**Fix:** Assert on computed properties ("total lessons = sum of course.lesson_count") rather than hardcoded numbers. Or just test that stat cards render with *a* number.

### 3. Page object model selectors break
When page structure differs from what the test expects (e.g. "Hero Range"/"Villain Range" vs "BB Range"/"BTN Range"), all selectors using the old text need updating.

**Fix — diagnose with:**
```typescript
const headings = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('h1, h2, h3'))
    .map(h => h.tagName + ': ' + h.textContent.trim());
});
console.log(JSON.stringify(headings));
```

### 4. Strict mode violations from duplicated text
When the same label appears in both the stats summary header and a sidebar panel, locators like `page.locator("text=Total Lessons")` hit strict mode.

**Fix:** Use `.first()` or scope to a container: `page.locator(".stats-summary").locator("text=Total Lessons")`.

### 5. Loading/empty states now visible
Pages that were instant-rendering with mock data now show loading spinners or empty states while the API call is in flight. Tests that assert on content immediately after `goto()` may see the loading state.

**Fix:** Add `waitForResponse` or `waitForSelector` for an element that only appears after data loads:
```typescript
await page.waitForResponse(resp => resp.url().includes('/api/v1/courses') && resp.status() === 200);
```

## When Not to Fix the Test

- **Tool/game-view pages** that intentionally lack standard H1s (e.g. interactive equity calculator) — don't force-add elements. Update the test to match the intentional layout.
- **Backend unavailable in CI** — filter console errors with backend-path exclusions rather than removing the console check entirely.
- **Seed data not guaranteed** — make tests resilient to empty states if the seed script hasn't run.

## CI Notes

- Without backend: data-fetching pages show loading/error states
- Console error filters: permit 500/404 from expected API calls when backend is optional
- Run with `CI=true` to disable webServer config
