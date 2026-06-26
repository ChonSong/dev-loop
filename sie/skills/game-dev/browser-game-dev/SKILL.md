---
name: browser-game-dev
description: Build and deploy browser-based games (Phaser, canvas, WebGL) from zero to served behind Cloudflare Tunnel with auto-deploy watchdog. Covers hex grid math, map generation, rendering pipeline, turn state machines, test patterns, and production deployment.
category: game-dev
tags:
  - game-dev
  - phaser
  - hex-grid
  - browser-game
  - vite
  - deployment
source: local
is_imported: true
---

# Browser Game Development

End-to-end workflow for building a browser-based game from scratch: project scaffold → game logic → rendering → testing → deployment behind Cloudflare Tunnel.

## When to Activate

- Scaffolding a new Phaser 3 + TypeScript browser game
- Implementing hex/tile grid systems (strategy games, tactical RPGs)
- Setting up map generation (procedural terrain, biome distribution)
- Writing a turn-based game state machine
- Configuring deployment for a static game (Vite + systemd + CF tunnel)
- Building a deploy watchdog (no-agent cron)

## Architecture Decisions

### Framework Choice

| Framework | Best for | Trade-off |
|-----------|----------|-----------|
| **Phaser 3** | 2D games (strategy, platformers, RPGs) | Largest community, built-in tilemap/camera/input/audio, WebGL + Canvas fallback |
| **Raw Canvas API** | Full control, tiny bundles | Must build everything — input, camera, game loop, asset loading |
| **Three.js** | 3D games | Overkill for 2D hex grid games |
| **Godot (Web export)** | Desktop + mobile later | Heavy WASM download, overkill for browser-only |

### Hex Grid Coordinate System

Always use **axial coordinates (q, r)** for hex grids — not offset coordinates. Axial makes neighbor calculations, distance, and pixel conversion trivial.

Key formulas (pointy-top):

```
// Axial → pixel
x = size * (√3 * q + √3/2 * r)
y = size * (3/2 * r)

// Pixel → axial (round to nearest hex)
q = (√3/3 * px - 1/3 * py) / size
r = (2/3 * py) / size
// Then cube-round the fractional q, r, s=-q-r

// Distance
max(|q1-q2|, |r1-r2|, |s1-s2|)

// Neighbors (6 directions)
(1,0), (0,1), (-1,1), (-1,0), (0,-1), (1,-1)
```

### Rendering Approach

Prefer **Phaser Graphics API** (`this.add.graphics()`) for fast iteration — no sprite assets needed during prototype. Draw hexagons as filled polygons with strokes:

```
for each tile:
  compute 6 corner points from center + size
  fill with biome color
  stroke with border
```

Camera controls are built-in Phaser: `this.cameras.main.scrollX/Y` + drag on `pointermove`.

### Turn State Machine

Define phases as an enum/union type. Game logic should be **pure functions** — no side effects, testable without Phaser:

```typescript
enum TurnPhase {
  EXPLORE = 'EXPLORE',
  BUILD = 'BUILD', 
  MOVE = 'MOVE',
  ATTACK = 'ATTACK',
  END = 'END',
}

interface GameState {
  phase: TurnPhase;
  tiles: Map<string, TileData>;
  cities: City[];
  units: Unit[];
  currentTribe: number;
  turn: number;
}

function advancePhase(state: GameState): GameState {
  // Pure function — returns new state, no mutations
}
```

## Project Scaffold

```bash
# Create project
mkdir -p my-game/src/hex src/scenes src/entities tests
cd my-game
npm init -y
npm install phaser
npm install -D typescript vite vitest @playwright/test
```

### File Structure

```
my-game/
  src/
    hex/         # HexCoord, Tile, constants, MapGenerator
    scenes/      # Phaser scenes (BootScene, GameScene, MenuScene)
    entities/    # City, Unit, Tribe, components
    ai/          # Opponent AI
  tests/
    hex.test.ts  # Hex math unit tests
    game.test.ts # Playwright E2E
  AGENTS.md      # Development conventions
```

### Vite Config

```typescript
export default defineConfig({
  base: './',
  server: { port: 3001, host: true },
  build: { outDir: 'dist', assetsDir: 'assets' },
});
```

### Hex Math — Must Unit Test

Write tests FIRST for hex math — these are pure function tests with no Phaser dependency:

```typescript
describe('HexCoord', () => {
  it('creates axial coordinates', () => {
    const h = new HexCoord(1, 2);
    expect(h.q).toBe(1);
    expect(h.r).toBe(2);
    expect(h.s).toBe(-3);
  });
  it('computes distance', () => {
    expect(new HexCoord(0,0).distanceTo(new HexCoord(3,0))).toBe(3);
  });
  it('round-trips pixel to hex', () => {
    const original = new HexCoord(5, 3);
    const pixel = original.toPixel(HEX_SIZE);
    const roundtrip = HexCoord.fromPixel(pixel.x, pixel.y, HEX_SIZE);
    expect(roundtrip.equals(original)).toBe(true);
  });
});
```

### Exclude Playwright from Vitest

Vitest and Playwright have conflicting `test()` globals. Exclude Playwright test files in vitest.config.ts:

```typescript
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    exclude: ['tests/game.test.ts', 'node_modules'],
  },
});
```

Run Playwright tests separately: `npx playwright test`

### Map Generation (Simple Noise)

Use distance-from-center + seeded pseudo-random for biome distribution. No Perlin/Simplex library needed for V1:

```typescript
for each hex:
  dist = distance from center
  rand = seeded_pseudorandom((seed + q * 31 + r * 17) % 100)
  val = dist / maxDim + rand * 0.3
  
  if val < 0.2 → WATER
  elif val < 0.3 → SAND
  elif val < 0.5 → GRASS
  elif val < 0.7 → FOREST
  elif val < 0.85 → MOUNTAIN
  else → SNOW
```

## Deployment Pipeline

### Systemd User Service

Run the Vite preview server as a user-level systemd service for auto-restart:

```ini
[Unit]
Description=My Game Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/sc/repos/my-game
ExecStart=/home/sc/.hermes/node/bin/npx vite preview --port 3001 --host
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now my-game.service
```

### Cloudflare Tunnel Ingress

Add a local config.yml for the tunnel (see `references/cloudflare-tunnel-local-config.md`):

```yaml
tunnel: <tunnel-uuid>
credentials-file: /home/sc/.cloudflared/<tunnel-uuid>.json

ingress:
  - hostname: mygame.codeovertcp.com
    service: http://localhost:3001
  # ... other ingress rules
  - service: http_status:404
```

Update the systemd service to use the config:

```
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/sc/.cloudflared/config.yml run <tunnel-name>
```

Restart: `systemctl --user daemon-reload && systemctl --user restart <tunnel-service>`

**Important:** The DNS CNAME record for the subdomain must point to the tunnel endpoint (`<tunnel-uuid>.cfargotunnel.com`). Create this in the Cloudflare DNS dashboard.

### No-Agent Deploy Watchdog

Set up a cron job with `no_agent=true` and a script that builds, tests, and checks the server every N minutes:

```bash
#!/bin/bash
# deploy-watchdog.sh
set -e
cd /home/sc/repos/my-game

BUILD_OK=$(npm run build 2>&1 | grep -c "built in")
TESTS_PASSED=$(npx vitest run 2>&1 | grep -oP 'Tests\s+\d+ passed')

echo "BUILD:$BUILD_OK"
echo "TESTS:$TESTS_PASSED"

if [ "$BUILD_OK" -eq 0 ]; then
  echo "BUILD_FAILED"
  exit 1
fi

if curl -sf http://localhost:3001/ > /dev/null 2>&1; then
  echo "SERVER:OK"
else
  echo "SERVER:RESTARTING"
  # Kill stale processes first
  for pid in $(lsof -ti:3001 2>/dev/null); do kill "$pid" 2>/dev/null; done
  sleep 1
  cd /home/sc/repos/my-game && nohup npx serve dist -p 3001 --cors > /tmp/game-preview.log 2>&1 &
  sleep 3
fi

echo "DEPLOY_OK"
```

Cron job setup:

```
action: create
no_agent: true
schedule: "every 5m"
script: deploy-watchdog.sh
```

When `no_agent=true`, the script runs without an LLM loop — its output is delivered verbatim. Empty output = silent (nothing sent). Non-zero exit sends an error.

### DNS Setup

The one manual step in CF Tunnel setup: create a CNAME record in Cloudflare DNS:

```
CNAME hex.codeovertcp.com → <tunnel-uuid>.cfargotunnel.com
```

Without this, DNS resolves to Cloudflare edge but the tunnel doesn't know to route traffic for that hostname.

## Entity Interaction Menu (City Build / Action UI)

When the player needs to interact with a game entity (city, unit, structure) to perform actions (train, upgrade, build), add a contextual floating menu.

### Pattern

```typescript
// Track menu state
private cityMenu: Phaser.GameObjects.Group | null = null;
private selectedCity: City | null = null;

// Show menu when entity is clicked
private showActionMenu(city: City, coord: HexCoord): void {
  this.hideActionMenu();
  this.selectedCity = city;

  // Position the menu near the entity in screen space
  const p = coord.toPixel(HEX_SIZE);
  const sx = p.x + this.cameras.main.scrollX + 40;
  const sy = p.y + this.cameras.main.scrollY - 20;

  // Style for active vs disabled buttons
  const activeStyle = {
    fontSize: '14px', color: '#ffd', fontFamily: 'monospace',
    backgroundColor: '#222', padding: { x: 8, y: 4 },
  };
  const disabledStyle = { ...activeStyle, color: '#555' };

  // Build action list with afford checks
  const actions: { label: string; handler: () => void; enabled: boolean }[] = [];

  // Each action checks player resources
  actions.push({
    label: 'TRAIN WARRIOR (5⭐)',
    enabled: tribe.stars >= 5,
    handler: () => {
      tribe.addUnit(new Unit(city.position, UnitType.WARRIOR, tribe.id));
      tribe.stars -= 5;
      this.hideActionMenu();
      this.renderAll();
    },
  });

  actions.push({
    label: `UPGRADE Lv${city.level}→${city.level+1} (${city.level * 5}⭐)`,
    enabled: city.canGrow() && tribe.stars >= city.level * 5,
    handler: () => {
      city.grow();
      tribe.stars -= city.level * 5;
      this.hideActionMenu();
      this.renderAll();
    },
  });

  // Render menu as a Phaser Group (cleanup on dismiss)
  this.cityMenu = this.add.group();
  actions.forEach((action, i) => {
    const lbl = this.add.text(sx, sy + i * 24, action.label,
      action.enabled ? activeStyle : disabledStyle)
      .setDepth(25).setInteractive({ useHandCursor: action.enabled });
    if (action.enabled) {
      lbl.on('pointerdown', action.handler);
      lbl.on('pointerover', () => lbl.setStyle({ backgroundColor: '#444' }));
      lbl.on('pointerout', () => lbl.setStyle({ backgroundColor: '#222' }));
    }
    this.cityMenu!.add(lbl);
  });

  // Dismiss hint
  const hint = this.add.text(sx, sy + actions.length * 24 + 4,
    '[click elsewhere to close]', { fontSize: '11px', color: '#888', fontFamily: 'monospace' })
    .setDepth(25);
  this.cityMenu.add(hint);
}

// Dismiss — call on background click or before showing new menu
private hideActionMenu(): void {
  if (this.cityMenu) {
    this.cityMenu.destroy(true);
    this.cityMenu = null;
  }
  this.selectedCity = null;
}

// In the click handler, route entity clicks to the menu:
// Priority: unacted friendly unit → city menu.
// - If clicking own city hex and there's an UNACTED unit → select the unit first
// - If clicking own city hex and all units have acted → showActionMenu()
// - If clicking elsewhere → hideActionMenu() and handle unit/empty hex
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Phaser Group for temp UI** | `this.add.group()` lets you destroy all menu elements at once. Alternative: track individual refs. |
| **Disabled (grey) vs hidden** | Grey shows the player what they COULD do if they had more resources — important for learning the game. |
| **Screen-space positioning** | Menu follows the entity even as the camera scrolls: `worldPos + camera.scrollX/Y`. |
| **Dismiss on any background click** | Prevents stale menus. Call `hideActionMenu()` at the top of the click handler's non-menu paths. |
| **Dismiss on AI turn start** | When `startTurn()` hands control to the AI, call `hideActionMenu()` (or equivalent). If not dismissed, the menu stays rendered throughout the AI's entire phase, and when it's the player's turn again, clicking their city calls `showActionMenu()` which calls `hideActionMenu()` first — BUT the old menu was never destroyed, so the AI phase shows a stale, unresponsive menu. |
| **Single action per click** | Each enabled button pointerdown fires the action and immediately rebuilds state. No multi-step forms. |

### When to Use

- The player needs to spend resources at a fixed location (city, base, workshop)
- The entity has a small, bounded set of possible actions (train, upgrade, build, research)
- You need to show afford/disafford state (can/can't afford)

### When NOT to Use

- Building selection requires sub-menus or nested categories → use a sidebar panel instead
- The list of actions is dynamic and long (more than 5-6 items) → use a dedicated build panel, not a floating menu
- Actions have multiple configurable parameters (choose which unit type AND how many) → use a dialog, not a floating menu

## Asset Generation Phase (Phase 2+)

Once game logic is solid, generate sprites/tiles:

1. Define sprite descriptions as JSON
2. Loop over ComfyUI MCP or fal.ai MCP to generate each sprite
3. Download generated images
4. Use ImageMagick to composite into spritesheets
5. Load spritesheets into Phaser

## Multiplayer Architecture (Phase 3+)

When adding multiplayer:

| Layer | Tool | Purpose |
|-------|------|---------|
| Game rooms | **Colyseus** | State sync, matchmaking, room management |
| Transport | **WebSocket** | Real-time game state updates |
| Auth | **JWT** | Player identity |
| Server logic | **Node.js** | Shared game logic, runs server-authoritative |

The game state machine (pure functions) runs identically on server and client. Server is authoritative — client predicts, server validates.

## Debugging an Existing Game

When a game "clearly hasn't been tested" or has visible gameplay bugs, use this systematic checklist. These are the most common game dev bugs that unit tests miss but players immediately notice.

### 1. Screen-to-World Coordinate Conversion

The single most common bug in clickable canvas games. Verify by:

- **Check the formula**: `worldX = event.clientX + camera.scrollX; worldY = event.clientY + camera.scrollY`. Then pass `worldX, worldY` to the pixel-to-hex/map function. Never add a hardcoded centering offset unless you've confirmed the origin.
- **Verify with the info panel**: Click a hex you know the position of (e.g., the tile a unit sits on at creation). If the info panel shows the wrong [q,r], the formula is wrong.
- **Round-trip test**: Hex(0,0) → toPixel → fromPixel should return Hex(0,0) at any camera position.

### 2. Object Lifecycle / Collection Cleanup

When ownership of an entity changes (city captured, unit converted):

- The entity MUST be removed from the original owner's array (`splice`)
- The entity MUST be added to the new owner's array (`push`)
- Check ALL code paths that read the old owner's collection:
  - `isDefeated()` — checks `cities.length === 0`, won't fire if captured cities linger
  - `getEnemyCities()` / `getEnemyUnits()` — AI targeting gets confused by stale entries
  - `findCity()` / `findUnit()` — might return entities at wrong-owner locations
  - `renderAll()` — might double-render or skip entities

### 3. AI Action Completeness

For each action type the AI can emit, verify there's a handler on the game engine side:

- **Unit attack** → `CombatSystem.executeAttack()`
- **City attack** → `CombatSystem.executeCityAttack()` + ownership transfer
- **Move** → update position, set `hasActed`
- **Train** → create unit, deduct cost
- **Upgrade** → call `city.grow()`, deduct cost

Missing handlers silently drop the AI's action — the AI wastes its turn without any error.

### 4. AI Dependency Injection

If the AI needs access to game data (tile map, tribe list, combat instances), check at runtime:

- Is the data being SET by the game engine? Search for `(gameState as any).tileMap =` or equivalent.
- Is the AI getting an empty map, null list, or undefined? Add a debug log.
- The most common failure: AI pathfinding returns null because the tile map was never shared.

### 5. Input Dead Zone for Click vs Drag

When the game supports both click-to-select and drag-to-pan on the same pointer:

- `p.wasTouch` is not sufficient — mouse users also drag.
- Add a distance threshold: `if (Math.abs(dx) + Math.abs(dy) > 3) { pan }`.
- Without this, every click registers as a micro-drag and the map jitters.

### 6. Server Infrastructure

- **Check for accumulated processes**: `ps aux | grep <port>` — stale server instances stack up from repeated deploy-script runs.
- **Process cleanup**: Use `for pid in $(lsof -ti:<port> 2>/dev/null); do kill "$pid"; done` before starting a new server.
- **Verify the build is fresh**: Check the dist JS bundle hash against what the browser is loading. Browser caching can serve an old build.

### 7. HUD / UI Visibility

The most common UI bugs players notice immediately but unit tests never catch:

- **HUD scrolls with the map.** Phaser text/graphics created with `this.add.text()` or `this.add.graphics()` are placed in **world space** by default. When the camera scrolls, they scroll too and quickly disappear off-screen. Fix: call `.setScrollFactor(0)` on every HUD element to lock it to screen coordinates. This applies to ALL heads-up display elements: tribe name, turn counter, star count, action buttons, info panels.

  ```typescript
  // Wrong — scrolls with the map
  this.add.text(10, 10, 'Hello').setDepth(20);
  
  // Right — stays fixed on screen
  this.add.text(10, 10, 'Hello').setScrollFactor(0).setDepth(20);
  ```

- **Text blends into the terrain below.** Light-colored text (`#fff`, `#ffd`) on a hex map with sand, snow, and gold city markers is invisible. Fix one of:
  - Put a **semi-transparent dark background panel** behind the HUD text. Use `this.add.graphics().fillStyle(0x000, 0.65).fillRoundedRect(...)` with `.setScrollFactor(0)` at depth one below the text.
  - Use **text stroke** for an outline effect.
  - Choose HUD colors that don't appear anywhere on the map (e.g., bright cyan `#0ff` or orange `#f80` — but remember the user might add those to the map later, so the dark background is safest).

- **End Turn / action buttons also scroll off.** Apply `.setScrollFactor(0)` to EVERY interactive UI element, not just text.

### 8. Version Control

- Initialize git with `git init` if absent, then add `.gitignore` (node_modules/, dist/, *.log).
- Without version control, you can't diff changes or roll back broken builds.

### 9. E2E Test Health — Playwright + Vitest Conflict

Many game projects have both vitest unit tests and Playwright E2E tests. These frameworks have conflicting `test()` globals. Verify E2E test health:

- **Check the Playwright config exists**: Look for `playwright.config.ts` or `.js` in the project root.
- **Run the Playwright tests**: `npx playwright test --reporter=list`. A crash with syntax error on `describe` or `it` means a test file imports vitest globals that Playwright can't parse. This is a common silent failure — the E2E test suite has **never run successfully** since project creation.
- **Fix**: Keep Playwright-only test files in `tests/e2e/` or explicitly exclude vitest files from Playwright's test match pattern in `playwright.config.ts`.
- **Check for hardcoded pixel coordinates**: grep for `page.click|locator.click` in test files. If E2E tests click at absolute pixel positions like `(466, 396)`, they only work at camera scroll (0,0) with one specific hex layout. Breakage after any map change is silent — the click lands on empty hex space and the test passes anyway because there's no assertion on canvas state.

### 10. Programmatic E2E Testing with `__PHASER_GAME__` Bridge

Canvas games have no DOM for locators. The solution: expose the Phaser game instance globally and drive game state via `page.evaluate()`. This eliminates pixel-coordinate fragility from E2E tests and lets you test game logic at the state level.

**Core technique:** In `src/main.ts`, assign `(window as any).__PHASER_GAME__ = game`. Then in tests, call `page.evaluate()` to interact with game scenes directly — spawn scenes with custom data, call click handlers with precise game coordinates, and assert on private fields like `cityMenu`, `selectedUnit`, `techPanel`.

For full patterns and test templates, see `references/phaser-e2e-testing.md`.

### 11. Canvas Rendering — Module Script Loading

For Phaser/Canvas/WebGL games loaded via `<script type="module">`:

- Some browser environments (headless, Hermes browser, CI) may not execute module scripts on initial navigation, leaving the page blank even though the bundle is served correctly.
- **Diagnostic**: Navigate to the game URL, then check `document.querySelector('canvas')`. If absent after 3s, try a manual dynamic `import('/assets/index-<hash>.js')` (find the hash from the HTML script tag). If the canvas appears after dynamic import, the static module-loading path failed silently.
- **Mitigation**: Add a `<script nomodule>` fallback or switch to classic `<script>` tag with the bundle directly.
- **Lesson**: Unit tests and code review never catch this. Only browser-probing with the actual deployment catches canvas rendering failures.

## Pitfalls

See also:
- `references/cloudflare-tunnel-local-config.md` — full tunnel config YAML setup and troubleshooting
- `references/deploy-watchdog-pattern.md` — no-agent cron watchdog with delivery semantics

- **Don't use offset coordinates.** Axial (q, r) is simpler for all hex operations. Offset is legacy from display-oriented thinking.
- **Vite preview on `--host`** exposes to all interfaces — fine behind tunnel, use `--host 127.0.0.1` if restricting to localhost.
- **systemd user services fail with `User=sc`** in a user-scoped unit — omit the `User=` directive (it runs as the owning user automatically).
- **Port conflicts** — kill stale processes before restarting. `pkill -f "vite preview"` is too broad. Use port-specific cleanup: `for pid in $(lsof -ti:3001 2>/dev/null); do kill "$pid"; done`. This avoids killing unrelated processes.
- **Playwright + Vitest don't share `test()`** — they have conflicting globals. Keep test files separate and configure excludes in vitest.config.ts.
- **CF tunnel DNS record is manual** — the tunnel connects to Cloudflare edge automatically but needs a CNAME record to route specific hostnames. This cannot be done from inside the container without the CF API token.
- **Hex pixel origin + screen-to-world conversion** — the most common game bug. When converting screen clicks to hex coordinates, the formula is: `worldX = screenX + camera.scrollX`. Do NOT add a hardcoded centering offset (e.g., `fromPixel(worldX - 400, worldY - 300)`) unless you're certain the hex origin (0,0) is at that exact world position. The `fromPixel()` function converts world-space pixel coords to hex — pass worldX/worldY directly. Verify with a round-trip test: hex → toPixel → fromPixel should return the same hex regardless of camera position.
- **Collection cleanup on ownership change** — when an entity changes owner (e.g., city captured), it must be removed from the original owner's array AND added to the new owner's array. Leaving it in the old owner's collection breaks `isDefeated()` (which checks `cities.length === 0`), breaks win-condition detection, and confuses AI targeting. Common pattern: `for each tribe: find index, splice out, add to capturing tribe`.
- **Entity click priority — unit on city tile** — when a unit occupies the same tile as a city, the click handler must decide which interaction takes priority. The most common and critical bug: checking `findCity(coord)` before `findUnit(coord)` and returning early, so clicking the starting city tile (which always has a warrior on it) **never selects the unit** — the player can't move their starting units.

  The correct priority order:
  1. If there's an **unacted friendly unit** on the tile → **select the unit** first (player needs to move it before using the city)
  2. If all units on the tile have acted AND there's a **friendly city** → **show city menu**
  3. Enemy units → show attack preview
  4. Empty hex → deselect, dismiss menus

  **Key insight**: Starting units sit on the city tile every game. If city check comes first, the starting warrior can never be selected for movement on turn 1. The player's first click on their starting city should select their warrior — the city menu becomes available after the unit has moved or acted.
- **AI turn doesn't dismiss floating menu** — when `startTurn()` passes control to the AI, any open contextual menu (city build menu, action panel) must be dismissed. If not, the menu stays rendered through the entire AI phase at its old state. Fix: call `hideCityMenu()` / `hideActionMenu()` at the top of `startTurn()` alongside nulling `selectedUnit` and `selectedHex`.
- **AI action handler completeness** — every action type the AI can emit (TRAIN, MOVE, ATTACK, UPGRADE) must have a corresponding handler in the game engine. A common hole: AI `ATTACK` targeting a city has no handler while unit-vs-unit `ATTACK` does. The engine silently ignores the action and the AI turn wastes its chance. When adding new AI actions, always verify the switch/case in `executeAiAction` (or equivalent).
- **AI dependency injection** — AI logic needs access to the tile map (for terrain-aware pathfinding), the full game state, and visibility data. Don't let AI query a property the game engine never sets. If the AI accesses `(gameState as any).tileMap`, the engine MUST set `(gameState as any).tileMap = this.tiles` at init time. Miss this and the AI gets an empty map — all pathfinding returns null, AI units never move.
- **Player can't see their own cursor position** — when implementing hex click-selection, confirm the hex info panel updates with correct [q,r] coordinates that match the tile's actual grid position. If clicking the top-left corner reports hex (-4,-6), the coordinate conversion is wrong.
