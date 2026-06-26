# Study Page ActionSelector Auto-Select Fix

## Problem

On `/study`, the ActionSelector component (FOLD/CALL/RAISE/ALL IN buttons) rendered with `opacity: 0.4` and `cursor: default` — disabled state. The user had to know to first click a hand cell in the range matrix before the buttons became usable. There was zero visual feedback that action was required.

The user clicked the UTG position button (which already showed "Acting") expecting action buttons to appear immediately. Nothing happened because clicking the already-active position doesn't re-fetch data.

## Root Cause

The `ActionSelector` component receives `disabled={!selectedHandData}`. On the server-rendered initial render, `selectedHandData` is `null` because no hand has been selected. The `useEffect` that fetches range data doesn't set any initial hand selection — it just populates the `ranges` map.

## Fix

In `apps/web/src/app/study/page.tsx`, inside the `fetchRange()` success handler (called by `useEffect` when position/stack changes), auto-select the first non-fold hand:

```typescript
// After setRangeData(map) and setIsSolverMode(true):
const firstActionable = data.hands?.find((h: any) => h.action !== 'fold')
if (firstActionable) {
  setSelectedCell(firstActionable.hand)
} else {
  setSelectedCell(null)
}
```

This goes in the `try` block, right after `setIsSolverMode(true)` and before the `catch`.

## Verification

After deploying the fix:

1. Navigate to `/study`
2. Wait for the API call to complete (~130ms)
3. Look at the right panel — should show "AA" (or whichever first non-fold hand) and enabled FOLD/CALL/RAISE/ALL IN buttons
4. Click a different position (e.g., HJ) — buttons should briefly show disabled state, then re-enable when new data loads
5. Click a different hand cell — the selected hand should update and the GTO action/frequency should change accordingly

## Bundle Verification

After build + server restart, verify the new bundle is served:

```bash
curl -s http://localhost:3000/study | grep -oP 'page-[^"]+'
# Should show: page-<new_hash>.js (not the old hash)
```

## Server Restart (critical)

`npx next build` writes to `.next/` but the running `next-server` keeps the old bundle cached in memory. You MUST kill the old process and restart:

```bash
ps aux | grep 'next.*3000' | grep -v grep
# Get the PID, then:
kill <PID>
npx next start -p 3000 &
# Verify:
curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/study
```
