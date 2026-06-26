# UI Replication Bug Taxonomy

When cross-referencing your implementation against a reference screenshot, search for these bug categories in order.

## 1. Grid & Layout Breakage

The most common and most visible bug. Custom grid layouts fail silently.

**Detection:** Does the page use custom grid column/row counts (e.g., 13-column hand matrix) that aren't in Tailwind defaults? Check `tailwind.config.ts`.

**Fix:** Add missing grid utilities:
```typescript
gridTemplateColumns: { '13': 'repeat(13, minmax(0, 1fr))', '14': 'repeat(14, minmax(0, 1fr))' }
```

**Real example:** A 13×13 hand matrix rendered as a single column (169 cells stacked) because `grid-cols-14` was used but only `grid-cols-13` was defined in the Tailwind config.

## 2. Data Flow Gaps

State A should update when State B changes, but no `useEffect` or callback bridges them.

**Detection:** Trace the data flow path: User input → state setter → component re-render. Is every step connected?

**Fix:** Add `useEffect(() => { setStateA(transform(stateB)); }, [stateB]);`

**Real example:** Hero range matrix showed all empty cells because `heroRange` was initialized as `Set()` and never synced when the villain range text input changed. The user would type "AA,KK" in the input field but the hero matrix stayed dark — no `useEffect` connected them.

## 3. String Parsing Errors

A string is split, parsed, or formatted incorrectly, producing wrong element counts or content.

**Detection:** Feed test input and check the output array/count. Common with card notation, comma-separated lists, and hand range syntax.

**Fix:** Use regex `match(/.{1,2}/g)` instead of `split("")` for card strings. For ranges, join with comma only on non-empty parse.

**Real example:** `"Kd7h2c".split("")` produces `["K","d","7","h","2","c"]` — 6 single characters shown as individual boxes instead of 3 two-character cards. Fix: `"Kd7h2c".match(/.{1,2}/g)` → `["Kd","7h","2c"]`.

## 4. Formula / Derived Data Errors

A calculated value uses a placeholder formula that produces wrong numbers.

**Detection:** Check every derived value against its real-world definition. If it looks like `Math.sin()`, `Math.random()`, or a made-up formula (`ev/100 + 0.5`), it's wrong.

**Fix:** Understand the real domain formula and implement it correctly. If you can't derive it, return null and let the UI handle missing data gracefully.

**Real example 1:** EQR (Equity Realized) = `result.ev_per_hand / 100 + 0.5` — this is completely unrelated to the real EQR formula (EV / pot_equity). Produced meaningless percentages.

**Real example 2:** Equity chart used `Math.sin(i/3)` and `Math.cos(i/4)` to generate wavy lines that had zero connection to actual equity data.

## 5. Dead Code

Components or imports that are defined but never rendered.

**Detection:** Search for component function definitions that appear only once (the definition itself). If the component appears in no JSX, it's dead. Same for imports — if the import alias appears only on the import line, it's dead.

**Fix:** Remove the definition and import, or render the component where it's needed.

**Real example:** `MatrixCell` component defined at 30 lines but never used in JSX — the `HandMatrix` component used inline button elements instead. Also `gto` imported from `@/styles/gto-tokens` but never accessed.

## 6. Placeholder Text

"Coming soon", "TODO", "Under construction", or similar text visible in the rendered UI.

**Detection:** `grep -in "coming soon\|todo\|under construction" app/gto/*/page.tsx`

**Fix:** Replace with real content from the reference (filter buttons, hand list, blockers display, etc.)

**Real example:** Three bottom tabs (FILTERS, HANDS, BLOCKERS) showed "coming soon" instead of actual controls. The FILTERS tab should show hand-type filter buttons, the HANDS tab should list equity results.

## 7. Mock Data Substitution

API responses are replaced with locally-generated random data instead of real API calls.

**Detection:** Search for `Math.sin`, `Math.cos`, `Math.random` in UI components that should display data from API. Also look for hardcoded result objects.

**Fix:** Call the real API endpoint and use the response. If the API endpoint doesn't exist yet, show a loading/empty state rather than fake numbers.

**Real example:** Equity chart line was generated from `Math.sin(i/3)` — it had no connection to actual win/tie/lose equity data from the `/api/v1/equity/calculate` response.

## 8. API Proxy / Rewrite Gaps

Frontend API calls 404 because Next.js rewrites don't cover all backend paths.

**Detection:** Try every frontend API call (`fetch("/api/v1/...")`) in the browser network tab. Failed requests with HTML response bodies indicate missing rewrites.

**Fix:** Add rewrite rules in `next.config.ts`:
```typescript
async rewrites() {
  return [
    { source: '/api/:path*', destination: 'http://localhost:8002/api/:path*' },
    { source: '/icm/:path*', destination: 'http://localhost:8002/icm/:path*' },
    { source: '/plo4/:path*', destination: 'http://localhost:8002/plo4/:path*' },
  ];
}
```

**Real example:** ICM and PLO4 API calls failed through the tunnel because Next.js didn't have rewrite rules for `/icm/*` and `/plo4/*` paths — only `/api/*` was proxied.

## Severity Guide

| Severity | Categories | Action |
|----------|-----------|--------|
| Critical | Grid breakage, Data flow | Page doesn't render meaningful content |
| High | Parsing, Formula, Placeholders | Page renders but shows wrong/damaged data |
| Medium | Mock data, Proxy | Features silently return wrong results or fail |
| Low | Dead code | No impact on functionality, but clutters codebase |
