# Equity Algorithm: Hand vs Range — Full Fix

## The Bug (Two Problems)

### Problem 1: Board deck included villain cards
`equity_vs_range()` built `exclude_set = set(hero_cards + board)` — villain combo cards were NOT excluded from the deck. When the sampled board included villain's hole cards, the simulation created impossible runouts (e.g. board has KdKh but villain also "holds" KdKh). This drastically lowered hero equity.

### Problem 2: Hero had to beat ALL combos to win
The inner loop broke early only on villain win. Hero was required to beat EVERY combo in the range to score a win. But hero losing to any single combo means a loss — this is too conservative for proper equity calculation.

## The Fix

Replace the multi-comparison-per-iteration approach with: **one random combo per iteration**:

```python
for _ in range(iterations):
    v_cards = random.choice(villain_combos)  # pick ONE combo
    exclude_set = set(hero_cards + board + list(v_cards))
    remaining_cards = [c for c in Deck()._cards if c not in exclude_set]
    sampled = random.sample(remaining_cards, needed)
    full_board = board + sampled
    hero_hand = Hand(hero_cards + full_board)
    villain_hand = Hand(list(v_cards) + full_board)
    result = hero_hand.compare_to(villain_hand)
    if result > 0: wins += 1
    elif result == 0: ties += 1
```

## Verification

| Scenario | Before | After | Expected |
|----------|--------|-------|----------|
| AA vs KdKh preflop | 0.693 | 0.818 | ~0.812 |
| AA vs KdKh on QsJs2c | 0.839 (fluke) | 0.896 | ~0.88-0.92 |
| AA vs KK,AKs on K72 | 0.0 (bug) | 0.704 | ~0.70 |

## Same fix needed in equity_vs_range_multiway

Check the multiway method — it may have the same two bugs (no villain-card exclusion, and beat-all-or-lose logic).

## Performance

- ~1.5s per 1000 iterations (Heads-up, 1 combo)
- ~38s per 20000 iterations
- `n_threads` parameter is accepted but NOT used — implementation is single-threaded
- Python `Hand()` class evaluation is the bottleneck (it enumerates C(7,5) = 21 combos per call)

## Edge Cases

- Empty villain_range → returns 0.0
- Empty board → `needed = 5`, full board sampled from remaining deck
- Same-rank hands → `result == 0` handled as tie
