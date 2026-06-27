# Playwright E2E Test Failure Analysis — gto-wizard-clone

**Date:** 2026-06-27  
**Total tests:** 33 | **Passing:** 15 | **Failing:** 18  
**Focus specs:** practice.spec.ts (8), smoke.spec.ts (5), study.spec.ts (5)

---

## Summary of Root Causes

| Category | Count | Description |
|----------|-------|-------------|
| (a) Test selector brittle/outdated | 7 | Test POM detection logic or button name mismatches |
| (b) App feature missing / API unreachable | 6 | Backend API returns 400 or data not populated |
| (c) Timing/async issue | 5 | Elements not rendered within timeout |

---

## practice.spec.ts — 8 Failures

### 1. P2: switch to Timed Drill reveals Timer Duration
- **Error:** `Exercise type selection may not have worked. Wanted Timed Drill, detected GTO Quiz.`
- **Root cause:** **(a) Test selector is brittle/outdated** — The `getActiveExerciseType()` method in the POM detects "Timed Drill" by checking if `bodyText.includes('Timer Duration') || bodyText.includes('30s')`. The page snapshot shows the button `[active]` correctly switches to "Timed Drill", but the conditional section (`Timer Duration` / `30s`) is only rendered when `exerciseType === 'Timed Drill'`. The 500ms `waitForTimeout` is not enough for React to re-render the conditional section. The text "Timer Duration" appears in the DOM only after the state update + re-render completes.
- **Fix:** Increase wait or use `await expect(page.locator('text=Timer Duration')).toBeVisible()` instead of relying on `getActiveExerciseType()`.

### 2. P3: select 30s timer in Timed Drill mode
- **Error:** `Exercise type selection may not have worked. Wanted Timed Drill, detected GTO Quiz.`
- **Root cause:** **(a) Test selector is brittle/outdated** — Same detection issue as above. The POM fails to confirm Timed Drill is active because the conditional text hasn't appeared yet.

### 3. P4: switch to Spaced Repetition shows stats
- **Error:** `Exercise type selection may not have worked. Wanted Spaced Repetition, detected GTO Quiz.`
- **Root cause:** **(a) Test selector is brittle/outdated** — Same detection issue. The POM checks for `"spots tracked"` or `"due for review"` in body text. The Spaced Repetition section renders this text, but only after re-render. The 500ms wait is insufficient.

### 4. P5: switch back to GTO Quiz hides conditional sections
- **Error:** `Exercise type selection may not have worked. Wanted Timed Drill, detected GTO Quiz.`
- **Root cause:** **(a) Test selector is brittle/outdated** — Same root cause as P2/P3. The test first tries to select "Timed Drill" and the detection fails.

### 5. P7: start session renders overlay and detects API status
- **Error:** `Session did not start. No overlay detected. URL: http://localhost:3000/practice.`
- **Root cause:** **(b) App feature missing / API unreachable** — The session overlay requires a successful API call to `/api/v1/quiz/random`. The `startSession()` function calls `fetchSpot()` which hits the API. If the API returns non-200 (likely 400 given other failures), `setSpot(null)` is called and the "Select a Training Mode" placeholder is shown instead of the session overlay with "End Session" button. The backend API is unreachable or returning errors.
- **Fix:** Ensure the API server is running, or the app needs a fallback/mock data path.

### 6. S: Timed Drill loads without error (Exercise Type Smoke Test)
- **Error:** `Exercise type selection may not have worked. Wanted Timed Drill, detected GTO Quiz.`
- **Root cause:** **(a) Test selector is brittle/outdated** — Same POM detection issue.

### 7. S: Spaced Repetition loads without error (Exercise Type Smoke Test)
- **Error:** `Exercise type selection may not have worked. Wanted Spaced Repetition, detected GTO Quiz.`
- **Root cause:** **(a) Test selector is brittle/outdated** — Same POM detection issue.

### 8. T1: configure Timed Drill with 120s, Wet board, Advanced, and start
- **Error:** `Exercise type selection may not have worked. Wanted Timed Drill, detected GTO Quiz.`
- **Root cause:** **(a) Test selector is brittle/outdated** — Cascading failure from `selectExerciseType('Timed Drill')` detection.

---

## smoke.spec.ts — 5 Failures

### 1. Test 1: Landing page loads with feature navigation cards
- **Error:** `Expected length: 0, Received length: 4` (console errors: 4× "Failed to load resource: 400 Bad Request")
- **Root cause:** **(b) App feature missing / API unreachable** — The page loads correctly (all UI elements visible), but 4 resources fail with HTTP 400. These are likely API calls made from the landing page (e.g., fetching dynamic data). The test correctly flags these as console errors.
- **Fix:** Investigate which API endpoints return 400 and fix the requests or suppress expected errors.

### 2. Test 2: Equity calculator loads and renders game state
- **Error:** `locator('h3:has-text('Equity Breakdown')')` not visible within 15000ms
- **Root cause:** **(c) Timing/async issue** — The equity page auto-calculates on load, but the calculation depends on an API call that either fails or is slow. Without a successful calculation, the `Equity Breakdown` section never renders. The page shows "Enter hands and click Calculate to see equity results" instead of results.
- **Fix:** Either ensure the API is available, or the test should manually click "Calculate" and handle the API response.

### 3. Test 3: ICM calculator loads and displays calculator UI
- **Error:** `Expected length: 0, Received length: 4` (console errors: 4× 400 Bad Request)
- **Root cause:** **(b) App feature missing / API unreachable** — Same as Test 1. The ICM page renders correctly (all UI elements visible in snapshot), but 4 API requests fail with 400.
- **Fix:** Same as Test 1.

### 4. Test 4: Courses page fetches and displays courses from API
- **Error:** `locator('h2:has-text('Available Courses')')` not visible within 5000ms
- **Root cause:** **(b) App feature missing / API unreachable** — The page shows "Loading courses..." and "0 Available Courses" in a `div`, but the `<h2>` element never renders because the API call fails and the loading state persists. The test expects data to be loaded.
- **Fix:** Ensure courses API returns data, or the app should show the empty state with the h2 element.

### 5. Test 5: Variant selector loads and displays all 10 variants from API
- **Error:** `page.waitForResponse` timeout — `/api/v1/variants` never returns 200 within 30s
- **Root cause:** **(b) App feature missing / API unreachable** — The variants API endpoint is completely unreachable. The page shows "0 Total Variants" and "Loading variants..." indefinitely.
- **Fix:** The `/api/v1/variants` endpoint needs to be implemented or the API server started.

---

## study.spec.ts — 5 Failures

### 1. Preflop mode: 0 console errors (study-console-audit)
- **Error:** `Expected length: 0, Received length: 5` (5× 400 Bad Request)
- **Root cause:** **(b) App feature missing / API unreachable** — The study page loads correctly (matrix, buttons all visible), but 5 API calls fail with 400 errors. These are likely WebSocket or API calls for loading spot data.
- **Fix:** Investigate and fix the failing API endpoints.

### 2. Postflop mode: 0 console errors (study-console-audit)
- **Error:** `Expected length: 0, Received length: 5` (5× 400 Bad Request)
- **Root cause:** **(b) App feature missing / API unreachable** — Same as above. Postflop mode renders correctly but API calls fail.

### 3. Postflop mode with solver: 0 console errors (study-console-audit)
- **Error:** `page.waitForResponse` timeout — `/api/v1/solver/postflop-strategy` never returns 200 within 30s
- **Root cause:** **(b) App feature missing / API unreachable** — The solver API endpoint is unreachable. The test clicks "Get GTO Strategy" and waits for the API response which never comes.

### 4. at least one action marked GTO recommended (study.spec.ts)
- **Error:** `locator.click: Test timeout of 30000ms exceeded` waiting for `getByRole('button', { name: 'Get GTO strategy' })`
- **Root cause:** **(a) Test selector is brittle/outdated** — The button's visible text changes from "Get GTO Strategy" to "⟳ Refresh" once a strategy is already loaded. The page snapshot shows the button as "⟳ Refresh" (strategy state is populated from a random spot). The test uses `getByRole('button', { name: 'Get GTO strategy' })` which doesn't match because:
  1. The accessible name is `aria-label` which is "Refresh GTO strategy" (when strategy exists)
  2. The visible text is "⟳ Refresh"
  3. Neither matches "Get GTO strategy" (lowercase 's')
- **Fix:** Update the test to use `getByRole('button', { name: /Get GTO Strategy|Refresh GTO strategy/ })` or use `getByRole('button', { name: 'Get GTO Strategy' })` (capital S).

### 5. (Implied 5th failure from study.spec.ts — possibly related to console errors in afterEach)
- The `afterEach` hook checks for console errors and would fail on any test that had 400 errors. Tests 1-3 already explicitly fail; the afterEach would flag remaining tests.

---

## Consolidated Recommendations

### Immediate Fixes (Test Side)
1. **Practice POM `getActiveExerciseType()`**: Replace text-based detection with proper ARIA attributes or data-testid selectors. Or increase wait time to 2000ms+ after clicking exercise type buttons.
2. **Study "Get GTO strategy" button**: Update selector to handle both states: `page.getByRole('button', { name: /Get GTO Strategy|Refresh GTO strategy/ })`
3. **Smoke console error tests**: Either fix the API endpoints or add proper filtering for known-failing API calls.

### Immediate Fixes (App Side)
1. **API endpoints returning 400**: Investigate `/api/v1/variants`, `/api/v1/quiz/random`, `/api/v1/solver/postflop-strategy`, and other endpoints. The backend may not be running.
2. **Courses API**: Ensure the courses endpoint returns data so the h2 element renders.
3. **Equity auto-calculation**: The equity page should either show results on load or the test should trigger calculation manually.

### Infrastructure
- The majority of failures (11/18) stem from API endpoints returning 400 or being unreachable. The app needs either:
  - A running backend server
  - Mock service worker (MSW) for test environments
  - Proper error boundaries that don't throw console errors for expected API failures
