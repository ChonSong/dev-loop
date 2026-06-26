# Phaser Game E2E Testing with Playwright

Phaser canvas games can't be tested with CSS selectors — all rendering is inside a WebGL/Canvas element. Traditional Playwright locators (`page.locator()`, `page.getByText()`) don't work on canvas content. This reference covers the `__PHASER_GAME__` bridge pattern: exposing the Phaser game instance globally and driving game state via `page.evaluate()`.

## Architecture

```
┌────────────┐     page.evaluate()     ┌──────────────────────┐
│  Playwright │ ──────────────────────► │  Phaser Game Instance │
│  Test Runner│ ◄────────────────────── │  (__PHASER_GAME__)   │
│             │   return value          │                      │
└────────────┘                          └──────────────────────┘
```

The key insight: instead of trying to click pixel-perfect positions on a canvas, we expose the game's internal state through `window.__PHASER_GAME__` and interact with it programmatically.

## Setup

### 1. Expose the Phaser Game Globally

In `src/main.ts`, assign the game instance to `window`:

```typescript
const game = new Phaser.Game(config);
(window as any).__PHASER_GAME__ = game;
```

This is the single-wire bridge between Playwright and the game engine.

### 2. Playwright Config

Keep Playwright tests separate from Vitest unit tests:

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests-e2e',
  timeout: 30000,
  retries: 0,
  use: {
    headless: true,
    viewport: { width: 800, height: 600 },
  },
});
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    exclude: ['tests-e2e', 'node_modules'],
  },
});
```

Run separately: `npx vitest run && npx playwright test`

## Core Helper Functions

```typescript
import { test, expect, Page } from '@playwright/test';

/** Navigate to game and wait for Phaser canvas to render */
async function loadGame(page: Page) {
  await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
  await page.waitForSelector('canvas', { timeout: 15000 });
  await page.waitForTimeout(2000);
}

/** Skip UI screens by calling Phaser's scene system directly */
async function startGame(page: Page, tribeIndex = 0) {
  await page.evaluate((idx) => {
    const game = (window as any).__PHASER_GAME__;
    if (!game) throw new Error('__PHASER_GAME__ not found');
    game.scene.start('GameScene', {
      humanTribeIndex: idx,
      mapType: 'CONTINENTS',
      gameMode: 'DOMINATION',
    });
  }, tribeIndex);
  await page.waitForTimeout(1500);
}

/** Mark the starting warrior (on the city tile) as hasActed so the city
 *  menu will open on the next click instead of selecting the unit */
async function markCityWarriorActed(page: Page) {
  await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    const tribe = gs.state.getCurrentTribe();
    const city = tribe.cities[0];
    const warrior = tribe.units.find((u: any) =>
      u.position.q === city.position.q && u.position.r === city.position.r
    );
    if (warrior) warrior.hasActed = true;
  });
}

/** Click the starting city tile via evaluate (bypasses pixel-coord math) */
async function clickStartingCity(page: Page) {
  await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    const tribe = gs.state.getCurrentTribe();
    const city = tribe.cities[0];
    const p = city.position.toPixel(32); // HEX_SIZE
    gs.handleClick(p.x, p.y);
  });
}
```

## Critical Insight: City Menu vs Unit Selection Priority

**Starting units sit on the city tile.** If clicking the city tile always opens the city menu (as earlier versions of this pattern recommended), the player can never select or move their starting warrior on turn 1.

The correct priority in `handleClick`:

1. If there's an **unacted friendly unit** on the clicked hex → **select the unit** (player needs to move it first)
2. If all units on the hex have acted AND there's a **friendly city** → **show city menu**
3. Enemy unit → attack preview
4. Empty hex → deselect/dismiss menus

This means **city menu tests MUST first mark the warrior as acted** before clicking the city tile. Use the `markCityWarriorActed()` helper above.

## Test Patterns

### 1. Basic Canvas Presence

```typescript
test('game loads canvas', async ({ page }) => {
  await page.goto(GAME_URL, { waitUntil: 'networkidle' });
  const canvas = await page.waitForSelector('canvas', { timeout: 15000 });
  expect(canvas).not.toBeNull();
  const hasGame = await page.evaluate(() => !!(window as any).__PHASER_GAME__);
  expect(hasGame).toBe(true);
});
```

### 2. City Menu Interaction (With Pre-Acted Unit)

```typescript
test('city menu opens and shows train options', async ({ page }) => {
  await loadGame(page);
  await startGame(page, 0);

  // Mark starting warrior as acted FIRST so city menu opens
  await markCityWarriorActed(page);
  await clickStartingCity(page);
  await page.waitForTimeout(300);

  // Verify menu appeared by inspecting game state
  const menuItems = await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    if (!gs.cityMenu) return [];
    return gs.cityMenu.getChildren().map((c: any) => c.text || '');
  });
  expect(menuItems.length).toBeGreaterThan(0);
  expect(menuItems.some((t: string) => t.includes('TRAIN'))).toBe(true);
});
```

### 3. Clicking on Non-city Hex to Dismiss Menu

```typescript
test('city menu closes when clicking elsewhere', async ({ page }) => {
  await loadGame(page);
  await startGame(page, 0);

  await markCityWarriorActed(page);
  await clickStartingCity(page);
  await page.waitForTimeout(200);

  // Click far away (maps to an empty tile)
  await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    const tribe = gs.state.getCurrentTribe();
    const city = tribe.cities[0];
    const p = city.position.toPixel(32);
    gs.handleClick(p.x + 500, p.y + 500);
  });
  await page.waitForTimeout(200);

  const menuClosed = await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    return gs.cityMenu === null;
  });
  expect(menuClosed).toBe(true);
});
```

### 4. Multi-turn Survival Test (using gs.endTurn())

```typescript
test('game survives 3 full turns without crash', async ({ page }) => {
  test.slow(); // AI turns can be slow with 3 tribes
  await loadGame(page);
  await startGame(page, 0);

  for (let turn = 0; turn < 3; turn++) {
    // End turn via evaluate — more reliable than pixel-clicking
    await page.evaluate(() => {
      const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
      gs.endTurn();
    });
    // Wait for AI phase — 3 AI tribes take ~5s total
    await page.waitForTimeout(8000);

    const alive = await page.evaluate(() => {
      const game = (window as any).__PHASER_GAME__;
      return game && game.scene.isActive('GameScene');
    });
    expect(alive).toBe(true);
  }
});
```

### 5. Post-AI State Validation

```typescript
test('city menu clears after AI turn', async ({ page }) => {
  await loadGame(page);
  await startGame(page, 0);

  await markCityWarriorActed(page);
  await clickStartingCity(page);
  await page.waitForTimeout(200);

  const menuOpen = await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    return gs.cityMenu !== null;
  });
  expect(menuOpen).toBe(true);

  // End turn via evaluate — AI should clear the menu
  await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    gs.endTurn();
  });
  await page.waitForTimeout(8000);

  const menuGone = await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    return gs.cityMenu === null;
  });
  expect(menuGone).toBe(true);
});
```

### 6. Entity Click Priority (Unacted Unit vs City Menu)

The correct behavior: clicking an unacted unit on a city tile selects the unit, not the city menu.

```typescript
test('unacted unit on city tile is selected instead of opening city menu', async ({ page }) => {
  await loadGame(page);
  await startGame(page, 0);

  // Click city tile — warrior is unacted, so unit should be selected
  await clickStartingCity(page);
  await page.waitForTimeout(200);

  const result = await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    return { menuOpen: gs.cityMenu !== null, selectedUnit: gs.selectedUnit !== null };
  });
  // Unacted unit gets selected, city menu stays closed
  expect(result.selectedUnit).toBe(true);
  expect(result.menuOpen).toBe(false);
});
```

### 7. Tech Panel Toggle (via evaluate)

```typescript
test('tech panel opens and closes', async ({ page }) => {
  await loadGame(page);
  await startGame(page, 0);

  // Toggle tech panel on via evaluate — more reliable than pixel-clicking
  await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    gs.toggleTechPanel();
  });
  await page.waitForTimeout(500);

  const techOpen = await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    return gs.techPanel !== null;
  });
  expect(techOpen).toBe(true);

  // Toggle off
  await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    gs.toggleTechPanel();
  });
  await page.waitForTimeout(500);

  const techClosed = await page.evaluate(() => {
    const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
    return gs.techPanel === null;
  });
  expect(techClosed).toBe(true);
});
```

### 8. Direct Tribe Selection (real pixel-mapped click)

When you need to click through a UI screen to test the full UX flow:

```typescript
test('select tribe via canvas click', async ({ page }) => {
  await loadGame(page);

  // Find tribe cards via scene state scan
  const tribeCards = await page.evaluate(() => {
    const game = (window as any).__PHASER_GAME__;
    const ss = game.scene.getScene('SelectScene');
    const kids = ss.children.list.filter((c: any) => c.type === 'Rectangle' && c.input?.enabled);
    return kids.map((r: any) => ({ x: r.x, y: r.y, w: r.width, h: r.height }));
  });

  const card = tribeCards[0];
  expect(card.x).toBeGreaterThan(0);

  // Convert game coord to canvas-relative coord
  const clickPos = await page.evaluate(({ gameX, gameY }) => {
    const canvas = document.querySelector('canvas')!;
    const rect = canvas.getBoundingClientRect();
    const game = (window as any).__PHASER_GAME__;
    return { x: gameX * (rect.width / game.config.width), y: gameY * (rect.height / game.config.height) };
  }, { gameX: card.x, gameY: card.y });

  await page.locator('canvas').click({ position: { x: clickPos.x, y: clickPos.y } });
  await page.waitForTimeout(1000);

  const onGameScene = await page.evaluate(() => {
    const game = (window as any).__PHASER_GAME__;
    return game.scene.isActive('GameScene');
  });
  expect(onGameScene).toBe(true);
});
```

## Passing Arguments to page.evaluate

Playwright's `page.evaluate()` accepts **exactly one argument** to the callback. Pass an object for multiple values:

```typescript
// WRONG — Playwright rejects >1 arg
await page.evaluate((a, b) => { ... }, a, b);

// RIGHT — destructure a single object
await page.evaluate(({ a, b }: { a: number; b: number }) => { ... }, { a, b });
```

## Why This Approach Works for Canvas Games

| Problem | Solution |
|---------|----------|
| Canvas has no DOM elements to query | Use `page.evaluate()` to access `__PHASER_GAME__` internals |
| Pixel coordinates change with camera scroll | Use game state to find entities, get their hex coords, convert to pixel |
| AI phase timing is unpredictable | Fixed generous timeout (6-8s for 3 AIs) + `test.slow()` marker |
| Starting a game requires clicks through menus | Call `game.scene.start('GameScene', data)` directly |
| Canvas click targets vary with viewport | Use Phaser's scale manager to map game coords → canvas coords |
| UI buttons (End Turn, Tech Panel) at fixed screen positions | Call the handler directly via `gs.endTurn()` / `gs.toggleTechPanel()` |
| City menu tests blocked by unit on same tile | Mark `warrior.hasActed = true` before clicking the city |

## What NOT to Do

- **Don't use hardcoded pixel coordinates** for entity interactions — they break with any hex layout or map change
- **Don't pixel-click End Turn / Tech buttons** — call `gs.endTurn()` and `gs.toggleTechPanel()` via evaluate for reliability; pixel-clicks on canvas can timeout when canvas overlays are present
- **Don't test game state with CSS selectors** — `page.textContent('.tribe-name')` won't work on canvas
- **Don't combine Vitest and Playwright globals** — they conflict. Separate test directories + configs
- **Don't blindly assert city menu opens on first city tile click** — the warrior on the tile gets selected first; you must mark it acted or the menu won't appear

## When to Use evaluate vs Real Canvas Clicks

| Approach | Use When | Example |
|----------|----------|---------|
| `page.evaluate(gs.endTurn())` | Reliable UI button interaction | End Turn, Tech toggle, city menu |
| `page.evaluate(gs.handleClick(x, y))` | Clicking game tiles by coord | City tile, unit tile, empty hex |
| `page.evaluate(gs.toggleTechPanel())` | Toggling UI panels | Tech tree, city list |
| `page.evaluate(() => { unit.hasActed = true })` | Setting up test preconditions | Mark warrior acted before city menu test |
| Real canvas click via locator coord | Testing tribe selection screen | Pixel-mapped card click through SelectScene |

## Key Pitfalls

1. **page.evaluate arg limit** — only 1 argument passed to the callback. Wrap multiple values in an object.
2. **Module access in evaluate** — imported classes (HexCoord, Unit) aren't available in `page.evaluate()`. Use the game scene's exposed methods instead (e.g., `gs.handleClick()` which internally imports HexCoord).
3. **Timer-based waits** — use generous timeouts (1.5s for scene init, 6-8s for AI turns). Add `test.slow()` for game loop tests. Add state assertion afterward instead of precise timing.
4. **Camera scroll changes click targets** — when testing with real canvas clicks, account for scrollX/scrollY if the camera may have moved. For `page.evaluate()` calls to `handleClick()`, note that it internally adds scrollX/scrollY, so pass screen coords directly.
5. **Unit-first click priority** — the correct order is: unacted friendly unit → city menu. **City-first is a bug** that prevents players from moving starting units. City menu tests must pre-mark the unit as acted.
6. **`test.slow()` for multi-turn tests** — AI processing time varies with tribe count and map size. Always add `test.slow()` to any test with AI turn processing to double the default timeout.
