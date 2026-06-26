# E701 — One-Liner Expansion Examples

Concrete examples from auto-continue sessions on the gto-wizard-clone monorepo showing the before/after of E701 fixes.

## Pattern: if/elif/else → action assignment

### Before
```python
if i <= 4: action = "bet_66"
elif i <= 7: action = "check"
else: action = "fold"
```

### After
```python
if i <= 4:
    action = "bet_66"
elif i <= 7:
    action = "check"
else:
    action = "fold"
```

### Broader context

This was in a hand-range generation function that iterates over rank pairs. The full block spans 3 if/elif/else trees (9 E701 violations total), one for each hand type (pairs, suited, offsuit).

## Fix method

Use `patch()` with the full block as `old_string` (include surrounding blank lines for uniqueness), replace with properly indented multi-line version. Verify with:
```bash
ruff check <file>
pytest <test-dir> -x -q --tb=short
```

## Occurrence frequency

E701 is the most common non-auto-fixable lint violation in the gto-wizard-clone codebase. Previous sweeps found:
- 9 in `trainer.py` — fixed June 2026
- 0 remaining in `apps/api/` after sweep

Total remaining across codebase (June 2026): ~33 violations, all E402 (module-level import ordering).
