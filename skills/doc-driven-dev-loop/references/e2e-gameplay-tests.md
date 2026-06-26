# E2E Gameplay Test Template — Playwright

Use this pattern to create gameplay tests that simulate a human playing a Phaser/canvas-based game.  
These tests are the automated "coach" — they catch regressions that unit tests miss.

## Basic Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Game — Gameplay E2E', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:PORT', { waitUntil: 'networkidle' });
  });

  test('game loads and renders canvas', async ({ page }) => {
    const canvas = await page.waitForSelector('canvas', { timeout: 10000 });
    expect(canvas).not.toBeNull();
  });

  test('game survives N turns without crash', async ({ page }) => {
    await page.waitForSelector('canvas', { timeout: 10000 });
    await page.waitForTimeout(1500); // wait for Phaser init

    const canvas = await page.$('canvas')!;

    // Click UI elements by screen position
    // Phaser uses screen coordinates, not DOM coordinates
    await canvas!.dispatchEvent('click', { clientX: X, clientY: Y, bubbles: true });
    await page.waitForTimeout(1000);

    for (let turn = 0; turn < 5; turn++) {
      await canvas!.dispatchEvent('click', { clientX: 700, clientY: 30, bubbles: true });
      await page.waitForTimeout(5000); // wait for AI processing
      const alive = await page.$('canvas');
      expect(alive).not.toBeNull();
    }
  });
});
```

## Key Patterns for Canvas Games

1. **`page.waitForSelector('canvas')`** — confirms Phaser initialized and rendered
2. **`page.waitForTimeout(1500)` — Phaser needs time to create scenes after canvas appears
3. **`canvas.dispatchEvent('click', { clientX, clientY })` — Phaser reads pointer events from the canvas element. Screen coordinates map to Phaser camera coordinates.
4. **Long waits between turns** — AI processing can take several seconds; be generous with timeouts.
5. **Check canvas still exists** — if the game crashed, the canvas element is removed or the tab crashes. Checking `page.$('canvas') !== null` confirms the game is still running.

## Converting World Coords to Screen Coords (Phaser)

Screen position = World position - Camera scroll offset

```
screenX = worldX - camera.scrollX
screenY = worldY - camera.scrollY
```

If camera starts at scroll (-300, -300), world hex (0,0) is at screen (300, 300).

## Vitest Exclusion

Add Playwright spec files to `vitest.config.ts` exclude list so Vitest doesn't try to run them:

```typescript
exclude: ['tests/game.test.ts', 'tests/gameplay.spec.ts', 'node_modules'],
```

Run Playwright separately:
```bash
npx playwright test
```
