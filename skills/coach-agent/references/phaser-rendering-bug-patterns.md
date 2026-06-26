# Canvas Game Testing Protocol

## Why Canvas Testing Is Different

Canvas/WebGL/Pixi render everything to a `<canvas>` element. There is no DOM — no buttons, no aria labels, no text nodes, no accessibility tree. `browser_snapshot` returns an empty page. The Coach cannot use its standard tools:

| Standard Tool | Works on DOM apps? | Works on Canvas? |
|---------------|-------------------|-------------------|
| `browser_navigate` | ✅ | ✅ (loads page) |
| `browser_snapshot` | ✅ (accessible tree) | ❌ (empty) |
| `browser_click(ref)` | ✅ (by element ref) | ❌ (no refs) |
| `browser_vision` | ✅ (optional) | ✅ (required) |
| `browser_console` expression | ✅ (read DOM state) | ✅ (if game API exposed) |

## Protocol: Minimum Viable Canvas QA

When you cannot read DOM state or click elements by ref, use this pattern:

### 1. Initialise

```js
const canvas = document.querySelector('canvas');
if (!canvas) return 'no canvas — page may still be loading or broken';
const rect = canvas.getBoundingClientRect();
```

### 2. Click at Estimated Coordinates

```js
function clickCanvas(x, y) {
  ['pointerdown', 'mouseup', 'click'].forEach(function(type) {
    canvas.dispatchEvent(new PointerEvent(type, {
      clientX: rect.left + x,
      clientY: rect.top + y,
      bubbles: true, cancelable: true, pointerType: 'mouse'
    }));
  });
}
```

### 3. Coordinate Discovery via Vision

`browser_vision(annotate=true)` — ask for exact positions:
> "Describe the full screen with element names and approximate x,y coordinates on the {W}x{H} canvas. List every interactive element with its estimated bounding box."

Vision model returns ±20px accuracy. If a click doesn't register, try a spiral search around the estimated point (step 10px in each direction, up to 100px radius).

### 4. State Verification

Always verify with a second vision call. Canvas games don't trigger console output on state changes (unlike DOM apps). Compare:
- Did the screen content change?
- Did new UI elements appear?
- Did a loading screen appear and disappear?

## Cost Model

| Step | Tool Calls | Est. Cost |
|------|-----------|-----------|
| Read screen state | 1x vision | $0.02 |
| Click at coords | 1x console (dispatchEvent) | $0.00 |
| Verify result | 1x vision | $0.02 |
| Retry on miss | +1-2x vision + click | +$0.04-0.08 |
| **1 interaction** | **3-4 calls** | **~$0.06-0.10** |
| 5-step workflow | 15-20 calls | ~$0.30-0.50 |
| 10-step workflow | 30-40 calls | ~$0.60-1.00 |

## Game API Exposure Pattern

The single most impactful improvement: expose the game instance on `window`.

### For Phaser 3 games

In the game's boot code:
```js
const game = new Phaser.Game(config);
(window as any).__PHASER_GAME__ = game;
```

Then the Coach uses the **Hybrid Canvas QA Protocol** below.

### For Custom/Other Engines

Look for the game's global reference. Common patterns:
- `window.game` or `window.Game`
- `window.phaserGame`
- `window.app` or `window.application`
- `Phaser.GAMES` array (Phaser 3 internal registry)

Probe: `browser_console(expression="typeof window.game")` — if "undefined", try `Phaser.GAMES`, `typeof Phaser`, and inspect `document.querySelector('script')` src URLs.

### If No API Is Exposed

File a task: `Expose game JS API for automated testing — add window.__game = game to dev-mode boot code`.

Without it, canvas testing is limited to:
- Page loads (200 status)
- Canvas renders (canvas exists with expected dimensions)
- Console errors (0 errors)
- First-screen vision check
- **Multi-step workflows are unreliable**

---

## Hybrid Canvas QA Protocol (Game-State + Vision + Coords)

When the game exposes `window.__PHASER_GAME__`, use three layers for robust multi-step testing:

### Layer 1 — Game-State Reads (Precision)

```js
const g = window.__PHASER_GAME__;
const gs = g.scene.getScene('GameScene');
const tribe = gs.humanTribe;
const cities = tribe.cities;

// Scene, phase, turn, city menu
g.scene.getScenes(true).map(s => s.scene.key);
gs.currentPhase; gs.PHASE_ORDER;
gs.turnManager?.turn;
gs.cityMenu !== null;  // null = closed (city menu not showing)
gs.selectedCity;

// City screen position
city.position.toPixel(32)  // Phaser world coords → subtract camera scroll

// Units
tribe.units.map(u => ({ type: u.type || u.constructor.name, hp: u.hp }));
```

### Layer 2 — Phaser-Native Interactions (Reliable)

Trigger clicks directly on Phaser interactive objects:

```js
// Find interactive rects in a scene (e.g. tribe cards in SelectScene)
const rects = g.scene.getScene('SelectScene').children.list.filter(
  c => c.type === 'Rectangle' && c.input?.enabled
);
rects[index].emit('pointerdown', { x: rects[index].x, y: rects[index].y });

// Or dispatch DOM pointer events at exact game-space coords
const canvas = document.querySelector('canvas');
const r = canvas.getBoundingClientRect();
['pointerdown', 'pointerup', 'click'].forEach(type => {
  canvas.dispatchEvent(new PointerEvent(type, {
    clientX: r.left + gx, clientY: r.top + gy,
    pageX: r.left + gx, pageY: r.top + gy,
    bubbles: true, cancelable: true, pointerType: 'mouse', button: 0
  }));
});
```

### Layer 3 — Vision Verification

After each interaction, `browser_vision` confirms the screen rendered correctly. Catches rendering bugs (missing menus, visual glitches, broken layouts) that state reads can't.

### Coordinate Reference Cache

Maintain a JSON file mapping element names to game coordinates. Derive from state reads, not vision guesses. Update when layout changes.

## Common Canvas/Phaser Bugs

- **UI overlays missing setScrollFactor(0)** — menu elements drift when camera scrolls. Check: does the UI stay fixed position when the map pans?
- **Column layout collapsing** — e.g. `600 / seriesKeys.length` where a short array produces tiny columns
- **Depth ordering** — `setDepth` values wrong: overlay UI renders behind map tiles
- **Click dead zones** — transparent/invisible hit areas cover interactive elements
- **Canvas resize handling** — game doesn't re-render on window resize, leaving black bars or misalignment
- **Font rendering** — custom fonts fail to load, text shows as blocks or defaults
