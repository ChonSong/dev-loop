# Monte Carlo Test Determinism & Timeout Diagnosis

## Pattern: Monte Carlo Tests Timing Out

**Symptom:** A test file with Monte Carlo simulations times out (>90s) even though individual tests look fast.

**Root cause:** The Monte Carlo function defaults to a high iteration count (e.g., `n_simulations=100_000`). Each test call triggers 100K gammavariate iterations. When the test suite calls the function ~38 times (including indirect calls via helper functions), total iterations reach ~3.8M — enough to time out.

**Diagnosis steps:**
1. Run the slow test file individually with `timeout 90` to confirm it's the file causing the timeout
2. Find the Monte Carlo function and check its default `n_simulations` parameter
3. Count how many times the function is called across all tests (including through wrappers like `icm_calculate` → `calculate_bubble_factor` → `malmoud_harville`)
4. Calculate total iterations = n_simulations × call_count

**Fix:** Pass an explicit `n_simulations` parameter to test calls that makes the assertions reliable without the overhead.

## Pattern: Flaky Monte Carlo Tests (Non-Deterministic)

**Symptom:** A Monte Carlo test passes sometimes, fails other times with the same inputs. The assertion is close to the boundary (e.g., `abs(value - 1.0) < 0.01` and value is ~0.989).

**Root cause:** The Monte Carlo function was called without a `seed` parameter, making the result non-deterministic. With reduced `n_simulations` (needed to avoid timeouts), the variance is higher, and the assertion occasionally fails.

**Fix:** Add `seed=<fixed>` to every Monte Carlo test call. This makes results deterministic — same seed always produces same pseudo-random sequence.

## Principle: Seed Every Monte Carlo Test Call

**Rule:** Every call to a Monte Carlo function in a test context MUST pass both `n_simulations` and `seed`.

```python
# ❌ Flaky — non-deterministic, may timeout
bf = calculate_bubble_factor(stacks, prizes, player_idx=0)

# ✅ Deterministic, fast, reliable
bf = calculate_bubble_factor(stacks, prizes, player_idx=0, n_simulations=5000, seed=42)
```

## Choosing the Right n_simulations

| Assertion type | n_simulations needed | Example |
|---|---|---|
| Ordinal (A > B > C) | 1,000–5,000 | `assert equity[0] > equity[1]` |
| Approximate equality | 5,000–20,000 | `abs(bf - 1.0) < 0.01` |
| Precise match (<0.001) | 100,000+ (original default) | `abs(value - 0.6) < 0.001` |

## Batch Test Runner Pattern

When a test suite is too large to complete within a timeout, run tests file-by-file:

```python
import subprocess, sys, os, time
test_files = sorted(f for f in os.listdir('tests/') if f.startswith('test_') and f.endswith('.py'))
for tf in test_files:
    r = subprocess.run(
        [sys.executable, '-m', 'pytest', os.path.join('tests/', tf), '-q', '--tb=line'],
        capture_output=True, text=True, timeout=120
    )
    print(f'{"PASS" if r.returncode == 0 else "FAIL"}: {tf}')
```

## Path Verification at Session Start

Cron instructions may reference stale paths. Always verify paths exist at session start:

```python
import os, subprocess
for name, path in {'R1': '/p1', 'R2': '/p2'}.items():
    if not os.path.isdir(path):
        result = subprocess.run(['find', '/home', '/workspace', '-maxdepth', '3', '-name', os.path.basename(path), '-type', 'd'], capture_output=True, text=True, timeout=5)
        print(f'{name}: configured={path}, found={result.stdout.strip() or "NOT FOUND"}')
```

## Case Study: ICM Test Timeout + Flake

- **Symptom:** `test_icm.py` timed out at 90s in batch runner, occasionally failed 1/17 tests
- **Root cause:** 100K default n_simulations × ~38 calls = 3.8M gammavariate iterations → timeout. After reduction to 5K, missing `seed=` on 3 calls caused non-deterministic flake
- **Fix:** Added `n_simulations=5000` + `seed=42` to all Monte Carlo test calls
- **Result:** 17/17 deterministically pass in ~4s
