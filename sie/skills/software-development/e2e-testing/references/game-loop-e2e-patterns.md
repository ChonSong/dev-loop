# Game Loop E2E Testing Patterns (Phaser / Canvas)

Turn-based games rendered on `<canvas>` (Phaser, PixiJS, raw WebGL) have unique E2E testing challenges — no DOM elements inside the canvas, AI processing time is variable, and game state lives in the engine, not the DOM.

## The Core Problem: Blind Waits

```typescript
// WRONG — fragile, slow when fast, times out when slow
await page.locator('button:has-text("End Turn")').click();
await page.waitForTimeout(5000);  // magic number
// repeat 4 more times → 25s minimum, easily hits 30s timeout
```

With 3+ AI tribes on a medium map, AI turn processing can range from 1s to 8s. Fixed waits must be tuned to the *worst case*, making fast tests artificially slow — and miss the worst case anyway when map size changes.

## The Fix: Poll for State Change (or Call Directly via evaluate)

For AI turn waits, poll for a **reliable state signal** — the UI element that indicates "it's your turn" (re-enabled button, updated turn counter, etc.):

For **UI buttons** (End Turn, Tech Panel) and **game tile clicks**, use `page.evaluate()` to call the game handler directly instead of pixel-clicking the canvas:

```typescript
// PREFERRED — call the handler directly
await page.evaluate(() => {
  const gs = (window as any).__PHASER_GAME__.scene.getScene('GameScene');
  gs.endTurn();
});
```

This is more reliable than pixel-clicking, which can fail due to:
- Canvas compositing timing (element "stable" check hangs)
- Camera scroll changing where the pixel lands
- UI overlays intercepting the click
- Headless rendering differences

```typescript
async function waitForMyTurn(page: Page, timeout = 15000): Promise<void> {
  const endTurn = page.locator('button:has-text("End Turn")');
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    // Button is enabled when it's the human player's turn
    if (await endTurn.isEnabled().catch(() => false)) return;
    await page.waitForTimeout(300);  // short polling interval
  }
  throw new Error(`Timed out waiting for player turn after ${timeout}ms`);
}
```

Then:

```typescript
for (let turn = 1; turn <= 5; turn++) {
  await page.locator('button:has-text("End Turn")').click();
  await waitForMyTurn(page);  // no magic number
}
```

This is **fast when AI is fast, safe when AI is slow**.

## Canvas Clicking

Since the game renders on `<canvas>`, you click by dispatching mouse events at pixel coordinates:

```typescript
const canvas = page.locator('canvas');
const box = await canvas.boundingBox();
// Click at relative coordinates within the canvas
await canvas.dispatchEvent('click', {
  clientX: box!.x + pixelX,
  clientY: box!.y + pixelY,
  bubbles: true,
});
```

### Getting Canvas Coordinates

For hex-grid games, log the canvas and ask the AI/smart model to compute coordinates, or add a temporary overlay:

```typescript
// In browser console (development only):
await page.evaluate(() => {
  const canvas = document.querySelector('canvas');
  const rect = canvas!.getBoundingClientRect();
  console.log('Canvas bounding:', rect);
  // Or add a debug overlay
  const div = document.createElement('div');
  div.id = 'coords';
  div.style.cssText = 'position:fixed;bottom:0;left:0;background:#000;color:#0f0;z-index:9999';
  document.body.appendChild(div);
  canvas!.addEventListener('mousemove', (e) => {
    div.textContent = `${e.clientX},${e.clientY}`;
  });
});
```

## State Signals for Turn-Based Games

| Signal | How to Detect | Reliability |
|--------|-------------|-------------|
| **"End Turn" button enabled** | `button:has-text("End Turn")` → `.isEnabled()` | High — explicit UI signal |
| **Turn counter text updates** | `text=/Turn \\d+/` → wait for value change | Medium — depends on game rendering it in DOM |
| **Canvas renders differently** | Take screenshot and pixel-diff (last resort) | Low — expensive, fragile |
| **Phaser game state** | `page.evaluate(() => Phaser.GAMES?.[0]?.scene?.scenes?.find(s => s.scene.key === 'Game').turnManager.currentTurn)` | High but fragile — depends on global Phaser.GAMES and scene structure |

Prefer the **button-enabled signal** as it's the most stable across refactors.

## Per-Test Timeout Strategy

For game-loop tests with variable turn count, set the test timeout explicitly based on expected worst case:

```typescript
test.setTimeout(60_000);  // 60s for 5-turn game loop

test('game survives 5 full turns without errors', async ({ page }) => {
  // ... turns loop with smart polling ...
});
```

Don't rely on the config-level `timeout: 30000` for game-loop tests. Config timeouts are for standard interaction tests; game loops need explicit overrides.

## Avoiding the "30s Test Timeout" Trap

When a test combines a multi-step game loop with `waitForTimeout`, each blind wait consumes time the test can't reclaim. Accrual:

| Waits | Per Wait | Total | Against 30s timeout |
|-------|----------|-------|-------------------|
| 5 × 5s `waitForTimeout` | 5s | 25s | ❌ Crashes on any delay |
| Smart polling (avg) | 1.5s avg | 7.5s | ✅ Comfortable margin |

Always prefer polling over blind waits in game loops — the variance is too high for fixed sleep durations.

## Polytopia Clone Specifics

- **"End Turn" button**: Call `gs.endTurn()` via page.evaluate instead of pixel-clicking — more reliable
- **"Tech Panel" button**: Call `gs.toggleTechPanel()` via page.evaluate instead of pixel-clicking
- **City menu**: Click via `gs.handleClick()` with the city's pixel coordinates — but **first mark the starting warrior as `hasActed = true`** since clicking a tile with an unacted unit selects the unit, not the city menu
- **Starting unit on city tile**: Every tribe starts with a warrior on the city hex. The correct click priority is: unacted unit → city menu. City menu tests must pre-mark the warrior as acted
- **Tribe selection**: 4 tribe cards rendered as clickable elements — scan `SelectScene.children.list` for interactive rectangles
- **Game survival check**: `page.evaluate(() => game.scene.isActive('GameScene'))`
- **Testing multi-turn loops**: Always add `test.slow()` to double the 30s default timeout
- **Canvas presence check**: `page.$('canvas')` — verify game didn't crash to a white screen

### Common Failure Modes

1. **Timeout on turn wait** → Switch from `waitForTimeout` to polling pattern
2. **Click lands on wrong hex** → Use `boundingBox()` for accurate coordinate computation
3. **Test passes but game is broken** → Add a canvas content check after each turn (screenshot or verify no error overlay)
4. **Console errors during AI processing** → Filter expected AI/animator errors from real crashes; use `page.on('pageerror', ...)` to capture JS exceptions
5. **30s test timeout on multi-turn test** → Add `test.slow()` at the top of the test to double the timeout, or use `test.setTimeout(60_000)`
6. **City menu never appears when clicking city tile** → The starting warrior sits on the city hex. Mark it `hasActed = true` before clicking the city tile, or the unit gets selected instead of the menu
7. **Canvas click hangs on "element stable"** → Switch from pixel-clicking the canvas to calling the game handler via `page.evaluate()` — e.g., `gs.endTurn()` instead of `canvas.click({ position })`
