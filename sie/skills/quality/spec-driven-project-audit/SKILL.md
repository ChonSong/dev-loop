---
name: spec-driven-project-audit
description: >
  When asked to report on a project or verify a claim about it, launch the app
  and drive a real browser with Playwright — act as a user would. Do not infer
  behaviour from source code inspection alone. Only what happens in the runtime
  counts.
---

# Spec‑Driven Project Audit (Playwright-First)

## Why this exists

Polytopia clone failure: told "core gameplay loop" was functional because
`Unit.ts` and `City.ts` files existed and 228 tests passed — but **3 of 4
stages had zero runtime code** and zero tests exercising the loop. Source
reading + test count = lies. The only honest check is "I launched the app,
clicked around, and watched what happened."

## Mandatory protocol

### Step 0 — Build and serve the app

```
npm run build        # or vite build
npx serve dist -p 3001 &   # or npm run dev
wait for server ready (curl http://localhost:3001)
```

If no build command exists → **❌ Not Deployable** — report immediately.

### Step 1 — Locate the authoritative spec

Read (in priority order):
1. `GDD.md` / `PRD.md` / `SPEC.md`
2. `AGENTS.md` / `CLAUDE.md` / `.cursorrules`
3. `README.md`

Extract the exact list of features/rules the spec claims. Each one becomes a
Playwright test.

### Step 2 — For each claimed feature, write and run a Playwright script

Do NOT search source files. Do NOT grep for function names. Do NOT count tests.

For every feature the spec says should exist:

1. Write a Playwright script (or inline snippet) that:
   - Opens the app at `http://localhost:PORT`
   - Navigates to the relevant screen
   - Performs the user action that triggers the feature
   - Asserts that the expected UI state appears (text, element, class, visibility)
   - Takes a **screenshot** for documentation

2. Run it.

3. If the assertion passes → **✅ Verified**
4. If the assertion fails → **❌ Missing** — runtime says it's not there, full stop.

**Playwright scaffold (run with `npx playwright test` or inline script):**

```ts
import { test, expect } from '@playwright/test';

test('units can be spawned from a city', async ({ page }) => {
  await page.goto('http://localhost:3001');
  // Click on a city
  await page.click('.city-tile');
  // Look for spawn button
  const spawnBtn = page.locator('button:has-text("Spawn")');
  await expect(spawnBtn).toBeVisible({ timeout: 5000 });
  // Take evidence
  await page.screenshot({ path: 'evidence/spawn-ui.png' });
});
```

**Inline snippet (quicker for one-off checks):**

```bash
npx playwright test --grep "units can be spawned"
```

### Step 3 — Report as pass/fail per spec item

| Spec item | Runtime result | Method |
|-----------|---------------|--------|
| Units spawn from city | ❌ — no spawn button | Playwright click city → check DOM |
| First-turn immobility | ❌ — unit can attack T0 | Playwright spawn unit → try attack |
| City border enforcement | ❌ — buildings can be placed anywhere | Playwright build → check position |
| Building placement | ✅ — resource adjacency honoured | Playwright select tile → builds |

No ❌s get called "functional". No "Partial" — either the browser shows it or it
doesn't.

### Step 4 — On failure, only then read source

When a Playwright check fails, use source inspection to **diagnose why**:

- Search for the UI class/element that should exist
- Find the missing function call
- Identify the gap

Source reading is for **debugging failures**, not for claiming success.

## Supporting files

A `scripts/` directory under this skill holds reusable Playwright utilities for
common patterns (serve-and-test, screenshot with timestamp, error capture).

## When to use this skill

- Any time the user asks "report on X", "status of X", "is X working"
- Any time you are about to claim a feature is implemented
- Any time you are asked to verify a deployment

## Common pitfalls

- **Code-read fallacy**: seeing a class/function in source ≠ runtime behaviour.
  The only valid proof is seeing it in the browser.
- **Test-count fallacy**: green suite ≠ features work. Always ask "what did
  Playwright actually verify?"
- **Spec-neglect fallacy**: reporting without reading the GDD/PRD first. Open the
  spec before you open any source file.
- **Server-forget fallacy**: verifying against a stale build. Always rebuild
  before running Playwright checks.
