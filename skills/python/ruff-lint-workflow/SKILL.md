---
name: ruff-lint-workflow
description: >-
  Systematic workflow for fixing common ruff violations in Python monorepos.
  Covers non-auto-fixable rules (E701, E741, F403, E402, F821) and the
  fix→verify→commit cycle. Use when doing a lint sweep after a ruff check
  pass that left >0 remaining violations.
category: python
tags: [ruff, linting, code-quality, python]
related_skills: [software-development/coding-standards]
---

# Ruff Lint Workflow

Systematic approach to fixing common ruff violations that `ruff check --fix` and `ruff format` don't handle automatically. Designed for recurring lint sweeps on Python monorepos.

## When to Activate

- After `ruff check .` returns violations, especially E-class or F-class
- Before committing code with known lint issues
- Cleaning up a codebase after importing/refactoring
- Recurring lint sweep tasks (cron, auto-continue)

## Quick Reference — Violation Fix Table

| Code | Meaning | Safe to auto-fix? | Manual strategy |
|------|---------|-------------------|-----------------|
| `F821` | Undefined name | NO | Add missing import or `# noqa: F821` |
| `F401` | Import unused | Conditional | `ruff check --fix` removes safe ones; manual for `__init__.py` re-exports (`import X as X`) and try/except availability checks (`importlib.util.find_spec`)
| `F403` | Wildcard import | NO | `import X as X` or `# noqa: F403` |
| `E701` | One-liner compound statement | NO | Expand to multi-line block |
| `E741` | Ambiguous variable name | NO | Rename `l`, `O`, `I` to descriptive names |
| `E402` | Import not at module top | NO | `# noqa: E402` or restructure |

## Workflow

### 1. Baseline — count and categorize
```bash
ruff check . 2>/dev/null | grep -c "^[A-Z]"   # count violations
ruff check . 2>/dev/null | head -80            # see categories
```

### 2. Auto-fix safe rules
```bash
ruff check --fix . 2>/dev/null
```

### 3. Manual fixes (in priority order)

#### F821 — Undefined name (potential runtime bug)
Look at the surrounding context. If the name should be imported, add the import.

**False positive: forward reference annotations.** When a class references another class that's defined later in the same package (e.g. `def __init__(self, game: "TexasHoldEm")`), ruff flags it as F821 because it can't resolve the string annotation at analysis time. The correct fix is:

**Preferred: `TYPE_CHECKING` guard + `from __future__ import annotations`**
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .texas_hold_em import TexasHoldEm, GameState
```
This provides proper type-checking support, avoids the lint, and follows PEP 604 annotation conventions. The `from __future__ import annotations` makes all annotations lazy strings; the `TYPE_CHECKING` block provides the types for static analysis without runtime import cost.

**Note:** `from __future__ import annotations` alone does NOT silence ruff's F821 — ruff checks name resolution at the source level, not at annotation-evaluation time. You MUST also have the `TYPE_CHECKING` guard or the actual import.

**Fallback:** `# noqa: F821` on the specific line if the annotation is truly unresolvable (e.g., conditional import in try/except).

**False positive: conditional imports.** Inside `try/except ImportError` blocks, `ruff` can't see the import at analysis time. Add noqa in those cases.

#### F401 — Re-exports in __init__.py
```python
# Bad:
from .module import Thing  # "imported but unused"

# Good (explicit re-export):
from .module import Thing as Thing

# Alternative (suppression):
from .module import Thing  # noqa: F401
```

#### F401 — Unused names in try/except ImportError blocks

Two sub-patterns:

**A) Availability check only** — the import exists solely to detect whether a module is installed. Replace with `importlib.util.find_spec`:

```python
# Bad — F401 on icm_for_push_fold, get_standard_prizes
try:
    from gto_poker.icm import icm_for_push_fold, get_standard_prizes
except ImportError:
    pytest.skip("icm_for_push_fold not available")

# Good — no import, just a spec check
import importlib
if importlib.util.find_spec("gto_poker.icm") is None:
    pytest.skip("icm_for_push_fold not available")
```

**B) Partial usage** — some names from the `try` block are used, but others aren't. Remove only the unused names from the import statement:

```python
# Bad — ActionType and Deck imported but never referenced
from games.texas_hold_em import TexasHoldEm, create_river_state, ActionType
from gto_poker.deck import Deck

# Good — only what's actually used
from games.texas_hold_em import TexasHoldEm, create_river_state
```

See `references/f401-try-import-patterns.md` for full details and health-endpoint examples.

#### F403 — Wildcard imports in __init__.py
```python
# Bad:
from .submodule import *

# Good:
from .submodule import ThingA, ThingB

# Acceptable (genuine re-export wrapper):
from .submodule import *  # noqa: F403
```

#### E701 — One-liner if/elif/else
**Ruff format does NOT fix this.** Must be done manually.

```python
# Bad (ruff E701):
if i <= 4: action = "bet_66"
elif i <= 7: action = "check"
else: action = "fold"

# Good:
if i <= 4:
    action = "bet_66"
elif i <= 7:
    action = "check"
else:
    action = "fold"
```

Use `patch()` with surrounding context for clean replacement. Preserve indentation.

#### E741 — Ambiguous variable name (`l`, `O`, `I`)
Look at the comprehension or loop context to find a meaningful name:

```python
# Bad:
for l in leaks: ...

# Good:
for leak in leaks: ...
```

#### E402 — Module-level import not at top
This typically happens when a module has top-level code before imports. Add `# noqa: E402` to the import if it's genuinely positioned (e.g., sys.path manipulation precedes it). Otherwise restructure the module.

### 4. Verify
```bash
ruff check . 2>/dev/null         # should have zero or fewer violations
pytest <test-dir> -x -q --tb=short  # tests still pass
```

## Common Patterns from Auto-Continue

- **Monorepo**: Always run ruff from the repo root so it picks up the workspace pyproject.toml config.
- **Batch fix**: Use `ruff check --fix --unsafe-fixes` for safe auto-fixes, but review each unsafe fix manually. Some "unsafe" fixes like removing unused imports are actually safe — the unsafe tag is conservative.
- **Commit pattern**: `auto: <repo> T3 — fix N <rule> violations in <file>`
- **Test gate**: 368 tests in gto-wizard-clone/packages/poker-core — always run after lint sweep.

## Pitfalls

- **`ruff format` does NOT fix E701.** This catches people every time. E701 is a lint rule (compound statement on one line), not a formatting rule. You must expand manually. See `references/e701-one-liner-expansion.md` for concrete examples from the gto-wizard-clone codebase.
- **Removing an import can break tests** if the import was the only thing pulling in a module with side effects. Always run the test suite.
- **F821 false positive on conditional imports** — inside `try/except ImportError` blocks, `ruff` can't see the import at analysis time. Add noqa in those cases.
- **Monorepo `__init__.py` re-exports** — these are intentional patterns, not accidental dead imports. Use `import X as X` to make the intent clear to ruff.
- **Don't suppress during review** — if a rule fires 20+ times in the same file, fix the root cause (e.g., `__init__.py` is better as explicit re-exporting than 20 noqa comments).
