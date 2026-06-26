# Monte Carlo Sampling Scope Errors

## Pattern

A class of algorithmic bug where simulation code samples from a population that includes elements logically excluded by the problem domain. The sampling pool is too large — it contains elements the model assumes aren't there.

## Real Example (Poker equity)

`equity_vs_range` computed hand-vs-range equity by:
1. Removing hero's cards from the deck
2. Sampling 5 board cards from the remaining 50
3. Comparing hero vs villain's possible holdings on that board

**The bug:** The 50-card pool still contained villain's hole cards. When a villain card appeared on the board (impossible in real poker), villain's hand evaluation effectively had duplicates, creating unfair comparisons and systematically lowering hero's equity.

Result: AA vs KK preflop returned 0.69 instead of 0.81.

## The Fix Pattern

For each simulation iteration:
1. Sample the **entire scenario's** excluded elements first (hero cards + this iteration's villain cards)
2. Remove ALL of them from the sampling pool
3. Sample remaining cards

```python
# WRONG:
exclude = hero_only
remaining = all_cards - exclude
sample_board(remaining)

# RIGHT:
for iteration:
    villain_hand = pick_random_combo(range)
    exclude = hero + villain_hand + known_board
    remaining = all_cards - exclude
    sample_board(remaining)
```

## When To Suspect

1. **Systematic bias** — results always slightly too low/high vs ground truth
2. **Works with known board but fails preflop** — known boards constrain deck naturally
3. **Discrepancy >2%** vs brute-force enumeration
4. **Parallel implementation gives different results**

## Debugging Steps

```python
# 1. Direct MC
wins = ties = 0
for _ in range(N):
    sampled = random.sample(remaining, needed)
    h1 = Hand(hero + sampled)
    h2 = Hand(villain + sampled)
    r = h1.compare_to(h2)
    if r > 0: wins += 1
    elif r == 0: ties += 1
direct = (wins + ties * 0.5) / N

# 2. Algorithm version
algo = calc.equity_vs_range(hero, [specific_hand], iterations=N)

# 3. Compare
assert abs(direct - algo) < 0.02
```

## Broader Applications

- **Game AI**: Sampling future states without removing active pieces
- **Statistical testing**: Bootstrap resampling without held-out observations
- **Physics simulation**: Particles colliding with entities that don't exist yet
- **Database queries**: WHERE clause missing impossible combinations
- **Monte Carlo tree search**: Selecting already-explored branches

## Key Insight

The exclusion set should be recomputed per iteration when the scenario changes between iterations.
