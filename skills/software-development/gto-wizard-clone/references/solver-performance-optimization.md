# Solver Performance Optimization (2026-07-08)

## Status: Round 2 Complete

Two rounds of optimization completed. Hand eval is 160x faster, infoset keys use tuples instead of strings, and overall solver is 1.5-2x faster.

## Round 1: Fast Hand Evaluator

Created `packages/poker-core/src/gto_poker/hand_fast.py` with bitmask-based evaluation:
- `evaluate_5card_fast()`: ~6x faster than Counter+sort
- `evaluate_7card_cached()`: ~160x faster with LRU cache
- `compare_hands_fast()`: Routes to appropriate evaluator

Wired into `get_payoffs()` and `_resolve_terminal()` in `texas_hold_em.py` and `engine.py`.

## Round 2: Tuple-Based Infoset Keys

Replaced string concatenation in `infoset_key()` with tuple-of-integers keys:
- Eliminates 500+ `str.join()` calls per solve
- No collision risk (tuples compared element-by-element)
- Changed `InfoSetManager` to `Dict[tuple, InfoSet]`
- Updated all consumers: `solver_service.py`, `tasks.py`, tests

## Benchmark Results

| Operation | Original | Round 1 | Round 2 | Total |
|-----------|----------|---------|---------|-------|
| 7-card compare | 1.916ms | 0.012ms | 0.012ms | **160x** |
| River 25 iters | 47ms | 38ms | 30ms | **1.6x** |
| Flop 25 iters | 354ms | 377ms | 234ms | **1.5x** |
| Flop 10 iters | 179ms | 131ms | 89ms | **2.0x** |

## Bugs Fixed

1. **Suit index mismatch** — `SUIT_INDEX` must match `deck.SUITS` order (h=0,d=1,c=2,s=3)
2. **Wrong cache key** — `Card._card_by_index[card_keys[i]]` not `[i]`
3. **Hand size routing** — Handle 5/6/7+ cards separately in `compare_hands_fast`
4. **Tuple key consumers** — All `.split(":")` and `.startswith("p0:")` calls broke; fixed with isinstance checks
5. **Duplicate imports** — Multiple `patch` ops on same file introduced duplicates; always verify after patching

## Remaining Bottlenecks

1. `apply_action` — 29% of river solve (state copy + mutation)
2. `state.copy()` — 16% of river solve
3. `evaluate_5card_fast` — 55% of flop solve (3,510 calls)
4. `evaluate_7card_cached` — 49% of flop solve (low cache hit rate from random sampling)

## Next Opportunities

- Make/undo pattern for CFR recursion (eliminate copy+apply = ~45% of river solve)
- Precompute card bitmasks on Card object
- Increase LRU cache size for 7-card eval
- Numba JIT for `_cfr_iteration`

## Profiling Commands

```bash
# Quick benchmark
python3 -c "
import sys, time
sys.path.insert(0, 'packages/poker-core/src')
sys.path.insert(0, 'apps/solver')
from cfr.flop_solver import solve_flop
t = time.time()
s, _, _ = solve_flop(['Ah','Kh'], ['Qs','Js'], ['Ks','7d','2c'], 8.0, [100.0,100.0], 25)
print(f'Flop 25 iters: {(time.time()-t)*1000:.0f}ms, {len(s)} infosets')
"

# Detailed profile
python3 -c "
import sys, cProfile, pstats, io
sys.path.insert(0, 'packages/poker-core/src')
sys.path.insert(0, 'apps/solver')
from cfr.flop_solver import solve_flop
pr = cProfile.Profile()
pr.enable()
solve_flop(['Ah','Kh'], ['Qs','Js'], ['Ks','7d','2c'], 8.0, [100.0,100.0], 10)
pr.disable()
s = io.StringIO()
pstats.Stats(pr, stream=s).sort_stats('cumulative').print_stats(20)
print(s.getvalue())
"
