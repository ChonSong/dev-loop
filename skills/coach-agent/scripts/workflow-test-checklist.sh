#!/bin/bash
# workflow-test-checklist.sh — Interactive QA verification for GTO Wizard clone
# Run after deployment to verify the core study workflow actually works end-to-end.
# This is a companion to the coach-agent skill's Workflow Test Protocol.

set -e

BASE_URL="${1:-http://localhost:3000}"
API_URL="${2:-http://localhost:8001}"

echo "=== Workflow Test Checklist ==="
echo "Frontend: $BASE_URL | API: $API_URL"
echo ""

FAILURES=0

# Test 1: Study page loads
echo -n "T1 /study loads... "
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE_URL/study")
if [ "$CODE" = "200" ]; then echo "✅ $CODE"; else echo "❌ $CODE"; FAILURES=$((FAILURES+1)); fi

# Test 2: Strategy lookup API returns data
echo -n "T2 /strategy/lookup returns 200... "
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$API_URL/api/v1/strategy/lookup?board=preflop&stack_depth=100&position=UTG")
if [ "$CODE" = "200" ]; then echo "✅ $CODE"; else echo "❌ $CODE"; FAILURES=$((FAILURES+1)); fi

# Test 3: Solver postflop endpoint responds
echo -n "T3 solver/postflop-strategy responds... "
RESPONSE=$(curl -s --max-time 10 -X POST "$API_URL/api/v1/solver/postflop-strategy" \
  -H 'Content-Type: application/json' \
  -d '{"board":"KsKc3s","position":"BTN","street":"flop","pot_size":5.5,"stack_depth":97.5}' 2>&1)
if echo "$RESPONSE" | grep -q '"actions"'; then echo "✅ actions returned"; else echo "❌ no actions: $(echo $RESPONSE | head -c 100)"; FAILURES=$((FAILURES+1)); fi

# Test 4: Leaderboard page loads
echo -n "T4 /leaderboard loads... "
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE_URL/leaderboard")
if [ "$CODE" = "200" ]; then echo "✅ $CODE"; else echo "❌ $CODE"; FAILURES=$((FAILURES+1)); fi

# Test 5: Practice page loads
echo -n "T5 /practice loads... "
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE_URL/practice")
if [ "$CODE" = "200" ]; then echo "✅ $CODE"; else echo "❌ $CODE"; FAILURES=$((FAILURES+1)); fi

# Test 6: Progress page loads
echo -n "T6 /progress loads... "
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE_URL/progress")
if [ "$CODE" = "200" ]; then echo "✅ $CODE"; else echo "❌ $CODE"; FAILURES=$((FAILURES+1)); fi

# Test 7: Equity calculator API
echo -n "T7 equity calculation... "
RESPONSE=$(curl -s --max-time 10 -X POST "$API_URL/api/v1/equity/calculate" \
  -H 'Content-Type: application/json' \
  -d '{"hero":"AKs","villain":"JJ"}' 2>&1)
if echo "$RESPONSE" | grep -q 'equity\|error'; then
  if echo "$RESPONSE" | grep -q '"error"'; then echo "❌ API error"; FAILURES=$((FAILURES+1)); else echo "✅ ok"; fi
else echo "❌ unexpected: $(echo $RESPONSE | head -c 80)"; FAILURES=$((FAILURES+1)); fi

echo ""
echo "=== Results: $((7 - FAILURES))/7 passed, $FAILURES failed ==="
exit $FAILURES
