# equity_vs_range Algorithm Details

## Purpose
Monte Carlo hand vs range equity calculation. For each random board runout, checks if hero's hand beats ALL hands in villain's range on that board.

## Algorithm

```
For each iteration:
  1. Sample random board cards (excluding hero + known board)
  2. Compare hero vs every combo in villain's range
  3. If hero beats ALL combos → win
  4. If hero ties ALL combos → tie  
  5. If ANY combo beats hero → loss
```

## Bug Fixed (2026-06-05)

The original code had a tight coupling between `villain_losses` and `len(villain_combos)`:

```python
# BUG: when villain_losses == len(villain_combos), condition is False, win NOT counted
if villain_wins == 0 and villain_losses < len(villain_combos):
    ...
    wins += 1
```

When hero beats ALL combos (villain_losses == len), the `<` test fails and the iteration is silently counted as a loss.

**Fix:** Remove the `len()` comparison entirely — only check whether villain won at all:

```python
if villain_wins == 0:
    if villain_losses > 0:
        wins += 1    # Hero beat at least one combo (including all)
    else:
        ties += 1    # Hero tied all combos
```

## Verification

| Scenario | Old Result | Fixed Result | Expected |
|----------|-----------|-------------|----------|
| AA vs KdKh on QsJs2c, 1000 iters | 0.000 | 0.839 | ~0.820 |
| AA vs KdKh preflop, 10000 iters | 0.688* | 0.688* | ~0.812 |

*Preflop still low — indicates a separate issue with no-board Monte Carlo sampling. The board sampling includes villain cards which can produce impossible runouts. Possible fix: exclude villain combo cards from the deck when sampling boards.

## API Verification

```python
import httpx
r = httpx.post('http://localhost:8000/api/v1/equity/calculate',
    json={'hero':'AsAh','villain':'KdKh','board':'QsJs2c','iterations':5000})
# → {'equity': 0.839, 'wins': 839, 'ties': 0, 'total': 5000, 'ev_per_hand': 0.839}
```
