# F821 — Undefined Name Fix Patterns

After `ruff check --fix` removes unused imports, remaining F821 errors signal real or false-positive undefined names. Here's how to handle each pattern found in this codebase.

## Pattern 1: Missing `timezone` in datetime import

**Files affected:** `apps/api/websocket/broadcast.py`, `apps/api/websocket/handlers.py`

```python
# BROKEN — timezone.utc raises F821
from datetime import datetime

# FIXED
from datetime import datetime, timezone
```

**Detection:** Search files for `from datetime import datetime` where `timezone.utc` or `timezone.*` is used elsewhere in the file.

## Pattern 2: Missing `import os` in sys.path manipulation

**Files affected:** `apps/solver/test_grpc_service.py`, `apps/worker/tasks.py`

```python
# BROKEN — os.path.join raises F821
PROTO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proto')

# FIXED — add at top of imports
import os
```

**Detection:** Files using `os.path.join()`, `os.path.dirname()`, `os.path.abspath()`, `os.environ`, or `os.getenv()` without `import os` at the top. Common in solver test files and worker task files that manipulate `sys.path`.

## Pattern 3: String forward references in type annotations

**Files affected:** `apps/solver/games/nodes.py`

```python
# F821 false positive — valid PEP 484 string annotation
def __init__(self, game: "TexasHoldEm"):          # F821
def _build_tree_recursive(self, parent_node: Node, state: "GameState"):  # F821

# FIXED — suppress with noqa
def __init__(self, game: "TexasHoldEm"):           # noqa: F821
def _build_tree_recursive(self, parent_node: Node, state: "GameState"):  # noqa: F821
```

**Do NOT add real imports** for `TexasHoldEm` or `GameState` at module level — this would cause circular import errors. The string annotations are legitimate PEP 484 forward references.

## Full Fix Sequence

After any `ruff check --fix` sweep:

```bash
# 1. Find remaining F821
ruff check . --select F821

# 2. For each file:
#    a. Read the imports at the top
#    b. Read the lines flagged by F821
#    c. Decide: missing import? → add it at the top
#        forward reference? → # noqa: F821 on that line
#    d. Re-check
ruff check . --select F821  # should be empty

# 3. Full verify
python -m pytest packages/poker-core/tests/ -q
python -m pytest apps/solver/tests/ -q
```

## History

- **2026-06-10:** 16 F821 found after 267-issue autofix sweep. Fixed 4 missing imports (timezone×2, os×2) and 2 forward-ref noqa annotations. Verified 576 tests pass.
