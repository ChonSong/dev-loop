# Visual QA Scripts — HWC

Created 2026-05-23 during visual QA pipeline setup. All scripts live in the hermes-web-computer repo on the host at `/opt/data/hermes-web-computer/`.

## Scripts Overview

| Script | Purpose | Runs on | Key command |
|--------|---------|---------|-------------|
| `scripts/visual-qa.sh` | Capture screenshots at 3 viewports, compare to baseline | Host | Chrome CLI screenshot |
| `scripts/run-visual-qa.sh` | Cron runner: capture → diff → log results | Host (cron) | ImageMagick `compare` |
| `e2e/scripts/visual_compare.py` | PIL-based pixel-diff with 5% threshold | Host | Python/Pillow |
| `e2e/tests/visual-baseline.spec.ts` | Playwright test suite (if Chromium deps available) | Host | Playwright |

## Quick Capture (No Script — One-Liner)

```bash
# On host — Chrome CLI screenshot (already installed as google-chrome-stable)
google-chrome-stable --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=10000 --window-size=1440,900 \
  --screenshot=/tmp/hwc-qa/screenshots/quick.png \
  --disable-web-security http://localhost:3113 2>/dev/null
```

The `--disable-web-security` flag bypasses CORS for local file access. `virtual-time-budget=10000` gives the page 10 seconds of virtual time to load before capturing.

## visual-qa.sh

Bash script for manual capture. Key flow:
1. Checks if HWC is running at localhost:3113
2. Captures 1440x900 screenshot
3. Stores as baseline if none exists
4. Captures at 1280x720 and 1920x1080
5. Uses ImageMagick `compare` for pixel diff if available

```bash
bash /opt/data/hermes-web-computer/scripts/visual-qa.sh
```

## run-visual-qa.sh (Cron Runner)

For cron: captures → compares → logs. Designed for the 12h HWC Visual QA cron job (job_id `0f8d4f768e17`).

```bash
# Manual run
bash /opt/data/hermes-web-computer/scripts/run-visual-qa.sh

# Check logs
cat /tmp/hwc-qa/qa-results.log
```

## visual_compare.py (Python PIL)

Pixel-diff using Pillow. More accurate than ImageMagick for small changes.

```bash
# Install Pillow on host
pip install Pillow

# Capture first
python3 /opt/data/hermes-web-computer/e2e/scripts/visual_compare.py --capture

# Then compare
python3 /opt/data/hermes-web-computer/e2e/scripts/visual_compare.py --compare
```

**Threshold:** 5% pixel difference — above this, regression is flagged.

## visual-baseline.spec.ts (Playwright)

Playwright test suite for visual regression. Requires Chromium installed and `npx playwright test` functional.

```bash
cd /opt/data/hermes-web-computer/frontend
npx playwright test e2e/tests/visual-baseline.spec.ts
```

Tests:
1. `baseline: default 1440x900 layout` — captures baseline screenshot
2. `baseline: 1280x720 layout`
3. `baseline: 1920x1080 layout`
4. `regression: pixel diff against baseline` — compares current to baseline
5. `layout: three columns visible` — DOM assertion
6. `design tokens: glassmorphism applied` — checks for backdrop-blur classes
7. `no console errors on load`

## Directory Structure (on host)

```
/tmp/hwc-qa/
├── screenshots/          # Current captures
│   ├── screenshot-1440x900.png
│   └── ...
├── baselines/            # Reference images for comparison
│   └── baseline-default.png  (1440x900, 120KB, captured 2026-05-23)
├── results/              # Diff images + JSON results
│   └── diff-{timestamp}.png
└── qa-results.log        # Cron job log
```

## Baseline Management

```bash
# Store current screenshot as new baseline
cp /tmp/hwc-qa/screenshots/current.png /tmp/hwc-qa/baselines/baseline-default.png

# Remove baseline to force re-capture
rm /tmp/hwc-qa/baselines/baseline-default.png
```

## Key Finding

**`google-chrome-stable` is installed on the host, not `chromium`.** All Chrome CLI commands must use this binary. The Chrome-based headless works on EndeavourOS even though Playwright's chromium headless shell (`~/.cache/ms-playwright/chromium_headless_shell-1223/`) can't launch due to missing system libs in the container.

The Chrome CLI screenshot works because it runs on the host (where all system libs are present), not in the container.