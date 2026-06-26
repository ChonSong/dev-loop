#!/bin/bash
# Deploy verification — checks all active projects' deployed endpoints
# Runs via no_agent cron, every 30min. Silent when all OK.
set -u

RESULTS=""

# ── polytopia-clone ──────────────────────────────────────────────────
POLYP_URL="https://hex.codeovertcp.com"
POLYP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$POLYP_URL" 2>/dev/null || echo "000")
if [ "$POLYP_CODE" = "200" ]; then
  :  # silent — healthy
else
  RESULTS="${RESULTS}POLYTOPIA:$POLYP_CODE (expected 200)\n"
fi

# ── hermes-webui-dev ─────────────────────────────────────────────────
WEBUI_URL="https://dev.codeovertcp.com"
WEBUI_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$WEBUI_URL" 2>/dev/null || echo "000")
if [ "$WEBUI_CODE" = "200" ]; then
  :  # silent — healthy
else
  RESULTS="${RESULTS}HERMES-WEBUI:$WEBUI_CODE (expected 200)\n"
fi

# ── gto-wizard-clone ─────────────────────────────────────────────────
GTO_URL="https://wiz.codeovertcp.com"
GTO_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$GTO_URL" 2>/dev/null || echo "000")
if [ "$GTO_CODE" = "200" ]; then
  :  # silent — healthy
else
  RESULTS="${RESULTS}GTO-WIZARD:$GTO_CODE (expected 200)\n"
fi

# ── Report only on failures ──────────────────────────────────────────
if [ -n "$RESULTS" ]; then
  echo -e "DEPLOY_VERIFY_FAILURES\n$RESULTS"
  exit 1
fi
