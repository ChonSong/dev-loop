# Visual QA Pipeline for hermes-web-computer

> Discovered 2026-05-22 during audit, extended 2026-05-23 during full pipeline build. Core lesson: **generate → verify → commit**, never just generate → commit.

## The Problem

hermes-computer development had no visual comparison step. Components were generated against a design spec (ILLOGICAL-IMPULSE-DESIGN.md), committed, but never verified against the spec visually. This produces UI that looks nothing like the inspiration.

Key failures observed:
- Browser OS from repo-transmute produced a "broken unfinished result" when the user asked for a visual reference (Illogical Impulse style)
- No Playwright screenshots were captured before/after component changes
- No vision model comparison against reference designs
- Playwright tests existed but Chromium was not installed, so they couldn't run

## The Closed-Loop Pipeline

```
Reference screenshot (from user or URL)
        ↓
Generate tile/component
        ↓
Serve frontend (Go backend on port 3113)
        ↓
Screenshot capture via chrome-headless on host (SSH)
        ↓
Pixel-diff regression check (current vs baseline) — threshold 1%
        ↓ fail
Block commit, emit repair plan
        ↓ pass
Pixel-diff reference check (current vs reference) — threshold 85%
        ↓ fail
Generate CSS fix list, delegate repairs
        ↓ pass
Commit
```

## Two-Stage Comparison

| Stage | Comparison | Threshold | Purpose |
|-------|-----------|-----------|---------|
| Regression | current vs baseline | ≤1% diff | Catch accidental breakage |
| Reference | current vs reference | ≥85% similarity | Verify against target design |

Without a reference image, only regression is possible (detect change from "now"). Reference image is the critical missing piece for true quality verification.

## Container Chrome + Svelte 5 `effect_orphan` Blocker

**Chrome headless CAN run in the container** with LD_LIBRARY_PATH set:
```bash
CHROME="/home/hermeswebui/.hermes/hermes-web-computer/.playwright/chromium-1223/chrome-linux64/chrome"
CHROME_LIBS="/home/hermeswebui/.local/chrome-libs/usr/lib/x86_64-linux-gnu:/home/hermeswebui/.local/chrome-libs/lib"
LD_LIBRARY_PATH="$CHROME_LIBS" "$CHROME" --version  # → Google Chrome for Testing 148.0.7778.96
```

**However HWC's Svelte 5 app crashes** with `effect_orphan` before rendering. Root cause: `layout.svelte.ts` uses `createSubscriber` + `$state` runes (Svelte 5 reactivity), but `ws.ts` calls `layoutState.setLayout()` on the first WebSocket message, which assigns `$state` before any component has mounted and called `subscribe()`. Svelte 5 throws `https://svelte.dev/e/effect_orphan` because `$state` mutation happens outside component initialization. Result: blank white page (4-8KB screenshots vs 91-97KB for working captures).

**Workaround:** When Chrome-in-container gets a blank page, either:
1. Fix the Svelte 5 init order (defer `setLayout` calls until a component subscribes, or switch from `createSubscriber`+`$state` to classic Svelte stores)
2. Run Chrome on the host via SSH (if SSH works): `ssh sean@172.19.0.1 /usr/bin/google-chrome-stable ...`

### Host-Side Screenshot Capture (Fallback)

Capture at 3 standard viewports:
- `1440x900` — common laptop
- `1280x720` — smaller displays
- `1920x1080` — full HD

Store baselines at `/tmp/hwc-qa/baselines/` on host. SCP screenshots to container for PIL analysis.

## Multi-Agent Pipeline Architecture

Built as `e2e/scripts/visual_pipeline.py` (448 lines):

```
┌─────────────────────────────────────────────────────────────┐
│  capture_agent  → screenshot_agent → diff_agent            │
│       │                  │                  │                │
│  chrome on        SCP to container       PIL pixel          │
│  host via SSH        for analysis         diff              │
│                                                             │
│  repair_agent  ← verify_agent                                 │
│       │              │                                        │
│  CSS fix plan   score ≥ 0.85                                 │
│  via LLM        → commit                                      │
└─────────────────────────────────────────────────────────────┘
```

Pipeline runs via cron every 12h. Screenshots on host at `/tmp/hwc-qa/screenshots/`, analyzed in container.

## Scripts Created (2026-05-23)

| Script | Purpose | Runs on |
|--------|---------|---------|
| `scripts/visual-qa.sh` | Bash screenshot + ImageMagick diff | Host (EndeavourOS) |
| `scripts/run-visual-qa.sh` | Host-side cron runner | Host |
| `e2e/scripts/visual_pipeline.py` | Full multi-agent pipeline (capture→diff→repair→verify) | Container |
| `e2e/scripts/visual_compare.py` | PIL pixel-diff engine (266 lines) | Container |
| `e2e/tests/visual-baseline.spec.ts` | Playwright test suite (needs host chromium) | Host |

## Pre-commit Visual Check

```bash
#!/bin/bash
# Block commit if regression diff > 1%
python3 e2e/scripts/visual_pipeline.py --regression
# Exit 1 if diff > threshold, else proceed
```

## Multi-Layer Verification (Fallback Order)

When vision API quota exhausts (429 errors after ~5-10 calls), use layered fallback:

### Layer 1: DOM Inspection (free, unlimited)

```javascript
// Check for glassmorphism CSS classes
document.querySelectorAll('[class*="glass"], [class*="backdrop-blur"]').length

// Check design tokens are applied
getComputedStyle(document.querySelector('.bg-\\[\\#12121a\\]')).backgroundColor

// Count interactive elements
document.querySelectorAll('button').length
```

### Layer 2: browser_snapshot (free, unlimited)

Gets accessibility tree without vision API cost. Use for layout structure verification.

### Layer 3: browser_vision (quota-limited, ~5-10 per session)

Reserve for:
- Final comparison before commit
- Critical visual decisions (color, glassmorphism depth)
- Understanding what's wrong when DOM inspection isn't enough

Use `annotate=true` to map interactive element refs to visual positions.

## Thresholds

| Score | Meaning | Action |
|-------|---------|--------|
| ≥ 0.85 | Good enough to commit | Commit |
| 0.60–0.84 | Close but needs fixes | Fix specific differences, re-verify |
| < 0.60 | Not recognizable | Redesign from reference, don't patch |

## Visual QA for Tile Development

### Before generating a tile:
1. Capture or locate the reference screenshot
2. List the 3-5 key visual elements (colors, glassmorphism depth, layout)
3. Write these as acceptance criteria

### After generating a tile:
1. `git diff --stat` to confirm files changed
2. Build backend on host: `cd /opt/data/hermes-web-computer/backend && go build -o /tmp/hwc-server ./cmd/server/`
3. Start server: `HERMES_HWC_ROOT=/opt/data/hermes-web-computer /tmp/hwc-server &`
4. Screenshot via chrome-headless on host
5. Vision compare against reference (score ≥ 0.85)
6. If fail: fix specific tokens, re-verify
7. Only then: `git add . && git commit`

## Dogfood Skill for hermes-computer

The `dogfood` skill (exploratory QA with systematic browser testing) can be used for hermes-computer:
1. Start the Go backend serving the frontend
2. Run `dogfood` skill targeting `http://localhost:3113`
3. Dogfood will: navigate, snapshot, console-check, vision-annotate, interact
4. It produces a bug report with screenshots

## Common Visual Issues + Fixes

| Issue | Root Cause | Fix |
|-------|------------|-----|
| Black screen on browser tile | Browser.svelte not mounting, CDP not connecting | Check `browser_id` propagation, verify chromedp running |
| No glassmorphism (flat gray) | `glass.css` not imported or `@theme` not applied | Verify `<link href="/assets/...">` in dist/index.html, check Tailwind v4 `@theme` in glass.css |
| Missing floating panels | Panels using hardcoded `bg-gray-900` instead of `bg-[#12121a]/90` | Replace with glassmorphism tokens from ILLOGICAL-IMPULSE-DESIGN.md |
| Wrong border radius | Using `rounded-lg` instead of `rounded-2xl` | Update to `--radius-panel: 16px` from glass.css |
| No backdrop blur | `backdrop-blur-xl` not on panels | Add `backdrop-blur-xl bg-[#12121a]/90 border-white/10` to Tile.svelte |

## Critical Prerequisite Check

Before attempting any visual QA:

```bash
# Verify Chrome is installed on host — use google-chrome-stable (already on host!)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "which google-chrome-stable"

# Verify Go backend can build and serve static files
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "cd /opt/data/hermes-web-computer/backend && go build -o /tmp/hwc-server ./cmd/server/"

# Verify backend is running
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:3113/"

# Quick screenshot test (Chrome CLI, no Playwright)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "google-chrome-stable --headless --disable-gpu --no-sandbox \
    --virtual-time-budget=10000 --window-size=1440,900 \
    --screenshot=/tmp/hwc-qa/screenshots/quick.png \
    --disable-web-security http://localhost:3113 2>/dev/null && \
  echo 'Screenshot OK' && ls -la /tmp/hwc-qa/screenshots/quick.png"
```

**Note:** Use `google-chrome-stable` exactly — not `chromium`, `chromium-browser`, or other variants.

## Canonical Paths

| Context | Path |
|---------|------|
| Host shell | `/home/sean/.hermes/hermes-web-computer` |
| Container (this env) | `/home/hermeswebui/.hermes/hermes-web-computer` |
| Backend port (HWC Go server) | `localhost:3005` (host), `172.19.0.1:3005` (from container) |
| Playwright snapshots dir | `e2e/tests/visual/baseline.spec.ts-snapshots/` |
| Visual QA screenshot dir (container) | `/tmp/hwc-qa/` |
| Baseline screenshots | `/tmp/hwc-qa/baselines/` |
| QA script | `~/.hermes/scripts/hwc-visual-qa.sh` |
| Chrome (in container) | `~/.hermes/hermes-web-computer/.playwright/chromium-1223/chrome-linux64/chrome` |
| Chrome libs (in container) | `/home/hermeswebui/.local/chrome-libs/usr/lib/x86_64-linux-gnu` |

## Baseline Screenshots

Captured 2026-05-23 from a working host-side Chrome session:

- `baseline-default.png` (93,956 bytes) — alias for 1440x900
- `baseline-1440x900.png` (93,956 bytes)
- `baseline-1280x720.png` (91,471 bytes)
- `baseline-1920x1080.png` (97,844 bytes)

All stored at `/tmp/hwc-qa/baselines/` in the container. `baseline-1440x900.png` was also copied to `e2e/tests/visual/baseline.spec.ts-snapshots/main-layout-chromium-linux.png` for Playwright e2e tests.

**Size comparison for regression detection:** The old baselines are 91-97KB (rendered UI). A blank page produces 4-8KB screenshots. The self-contained `hwc-visual-qa.sh` script uses size-based heuristic: screenshots under 10KB trigger a WARN (app didn't render).

## Cron Job

**HWC Visual QA** — job_id `fcf273002361`, runs every 720m (12h), no_agent mode, script `hwc-visual-qa.sh`.
- Checks HTTP 200 at `http://172.19.0.1:3005/`
- Captures screenshot via Chrome headless with LD_LIBRARY_PATH
- Compares byte size vs `baseline-default.png` (<10KB = WARN, >10% diff = REGRESSION)
- Silent on PASS, alerts on FAIL/WARN/REGRESSION
- Created 2026-06-10, replaces the previous `0f8d4f768e17` which was removed