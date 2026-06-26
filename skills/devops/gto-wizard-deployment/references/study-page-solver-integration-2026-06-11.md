# Study Page Solver Integration + Preflop-Range Endpoint — 2026-06-11

## Preflop-Range Endpoint

A new endpoint was added to `apps/api/routers/solver.py` for the study page:

```
POST /api/v1/solver/preflop-range
```

**Request:**
```json
{"position": "BTN", "stack_depth": 100, "game_type": "nlh"}
```

**Response:** Returns all 169 preflop hands with solver data per position:
```json
{
    "position": "BTN",
    "stack_depth": 100,
    "hands": [
        {"hand": "AA", "action": "raise", "frequency": 1.0, "equity": 1.0},
        {"hand": "AKs", "action": "raise", "frequency": 1.0, "equity": 1.0},
        {"hand": "AKo", "action": "raise", "frequency": 1.0, "equity": 0.917}
    ]
}
```

**Current implementation:** Formula-based (not real CFR) for speed. Uses position tightness thresholds to determine raise/call/fold for each hand. Position tightness values:

| Position | Tightness |
|----------|-----------|
| UTG | 0.12 |
| HJ | 0.15 |
| CO | 0.22 |
| BTN | 0.35 |
| SB | 0.38 |
| BB | 0.45 |

## Study Page Wiring (`apps/web/src/app/study/page.tsx`)

The study page now calls `POST /api/v1/solver/preflop-range` on position change. Cell coloring by solver action:

| Action | Color | Hex |
|--------|-------|-----|
| raise | Red (RED_BRIGHT) | #E53935 |
| call | Blue | #3A6EA5 |
| fold | Gray | #2a2a2a |
| all_in | Dark Red | #7B1E1E |

Opacity indicates frequency: fold→0.3, raise/call→0.5 + frequency*0.5

**Error handling:** Loading indicator, "Offline" fallback to hardcoded colors.

## Overnight Cron Pattern

Crons for overnight continuation (23:39→07:00 Sydney):

```bash
cronjob(action='create',
  schedule='0 */3 * * *',     # or '0 0,2,4,6 * * *'
  repeat=3,
  model={'provider':'openrouter', 'model':'google/gemini-2.5-flash-preview-04-17'},
  enabled_toolsets=['terminal','file','web'],
  prompt='...')
```

SSH pattern for host commands: `ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "command"`

Key: use `repeat=N` to expire, set `enabled_toolsets` tightly, stagger schedules (0/30), verify with `cronjob(action='list')`.
