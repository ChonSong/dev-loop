#!/bin/bash
# hwc-host-visual-qa.sh — Host-native Visual QA for HWC
# Takes screenshots, compares to baselines
BASE_DIR="/tmp/hwc-qa"
SCREENS="$BASE_DIR/screenshots"
BASELINES="$BASE_DIR/baselines"
mkdir -p "$SCREENS" "$BASELINES"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S UTC')
echo "[$TIMESTAMP] HWC Visual QA (host)"

# Health check
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:3005/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "200" ]; then
  echo "RESULT: FAIL — Server HTTP $HTTP_CODE"
  exit 1
fi
echo "Server OK"

# Screenshot (1440x900)
SCREENSHOT="$SCREENS/host-screenshot-$(date '+%Y%m%d_%H%M%S').png"
google-chrome-stable --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=15000 --window-size=1440,900 \
  --screenshot="$SCREENSHOT" --disable-web-security \
  http://localhost:3005 2>/dev/null

if [ ! -f "$SCREENSHOT" ]; then
  echo "RESULT: FAIL — Screenshot failed"
  exit 1
fi

SIZE=$(stat -c%s "$SCREENSHOT")
echo "Screenshot: $(basename $SCREENSHOT) (${SIZE} bytes)"

# Compare to baseline
BASELINE="$BASELINES/baseline-default.png"
if [ ! -f "$BASELINE" ]; then
  cp "$SCREENSHOT" "$BASELINE"
  echo "RESULT: FIRST_RUN — baseline stored"
  exit 0
fi

SIZE_BASE=$(stat -c%s "$BASELINE")
DIFF=$((SIZE_BASE - SIZE))
DIFF_ABS=${DIFF#-}
DIFF_PCT=$(awk "BEGIN {printf \"%.1f\", ($DIFF_ABS / $SIZE_BASE) * 100}")

if [ "$DIFF_PCT" = "0.0" ]; then
  echo "RESULT: PASS"
elif [ "$(echo "$DIFF_PCT < 10" | bc)" = "1" ] 2>/dev/null || [ "${DIFF_PCT%.*}" -lt 10 ] 2>/dev/null; then
  echo "RESULT: PASS (diff ${DIFF_PCT}%)"
else
  echo "RESULT: REGRESSION — size changed ${DIFF_PCT}%"
  cp "$SCREENSHOT" "$BASELINES/regression-$(date '+%Y%m%d_%H%M%S').png"
fi
