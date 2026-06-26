# Parallel Subagent Conflict Resolution

## The Problem

When multiple `delegate_task` subagents are dispatched in parallel to modify overlapping files, they produce git merge conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>> hash`). This happens most often in:
- `__init__.py` — two agents add different imports
- Source modules — subagent A creates clean file, subagent B overwrites with different implementation
- Test files — each agent writes tests using different class names

## Systematic Fix

Batch Python script that strips conflict markers from all affected files:

```python
import os

root = '/tmp/project'
files = [
    'packages/core/src/mypackage/__init__.py',
    'packages/core/src/mypackage/plo4.py',
    # ... list all affected files
]

for rel_path in files:
    full_path = os.path.join(root, rel_path)
    with open(full_path) as f:
        content = f.read()
    if '<<<<<<<' not in content:
        continue
    lines = content.split('\n')
    clean, in_conflict, in_ours = [], False, True
    for line in lines:
        if line.startswith('<<<<<<<'):
            in_conflict, in_ours = True, True
            continue
        elif in_conflict and line == '=======':
            in_ours = False
            continue
        elif in_conflict and line.startswith('>>>>>>>'):
            in_conflict = False
            continue
        if not in_conflict or in_ours:
            clean.append(line)
    with open(full_path, 'w') as f:
        f.write('\n'.join(clean))
```

**Strategy:** Keep the "ours" side (between `<<<<<<< HEAD` and `=======`), drop "theirs" (between `=======` and `>>>>>>>`). This preserves whichever subagent committed last.

## Verification Sequence (Never Skip Layers)

### Layer 1: Remaining Conflict Markers
```bash
grep -rn "<<<<<<\|=======\|>>>>>>" src/ 2>/dev/null | grep -v "^[^:]*:.*======" | head -20
```
Note: `=======` inside multi-line strings (docstrings, comments) are NOT conflict markers.

### Layer 2: Import Check
```bash
python -c "from mypackage import *; print('OK')"
```
A `SyntaxError` means leftover conflict markers.

### Layer 3: Class Inventory
Use `ast.parse` to list all classes and functions in each module. Cross-reference against `__init__.py` imports. The conflict-resolved files may have lost classes/functions that were only in the "theirs" side.

```bash
python -c "
import ast
for f in ['file1.py', 'file2.py']:
    with open(f) as fh:
        tree = ast.parse(fh.read())
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    print(f'{f}: {classes}')
"
```

### Layer 4: Fast Tests
```bash
python -m pytest tests/ -k "not slow and not integration and not monte_carlo" -x
```

### Layer 5: API Router Validation
One import per router to catch `__init__.py` export mismatches:
```python
from routers.plo4_equity import router as r_plo4
from routers.omaha import router as r_omaha
# etc.
```

### Layer 6: Full Suite
Last step only after Layers 1-5 pass:
```bash
python -m pytest tests/ -v
```

## Real Example: GTO Wizard Clone (May 2026)

6 parallel subagents built 92 files across overlapping directories. After the timer ran, 18 files had conflict markers across 3 directories (poker-core, API routers, tests).

**Pass 1 (poker-core):** 8 files fixed in ~2s. Result: `ModuleNotFoundError: No module named 'phevaluator'`.
**Fix:** `pip install phevaluator`

**Pass 2 (API routers):** 4 files fixed. Result: `ImportError: cannot import name 'ShortdeckEquityCalculator'` — the class was renamed by the other subagent.
**Fix:** Updated import in the router to match actual class name.

**Pass 3 (hybrid):** After updating `__init__.py` exports, tests passed at 115/115 in 49s.

**Key insight:** The conflict fix script always keeps one side. The OTHER side's contributions (different class names, extra imports, alternate implementations) are LOST. After cleanup, always update `__init__.py` to match what actually exists in the modules.

## Prevention

**In PLAN.md:**
- Designate ONE subagent as owner of `__init__.py` and `main.py`
- Specify exact file paths per track — never let two tracks write to the same path
- Use a final integration track that wires packages together
- When in doubt, prefer serial execution over parallel when file boundaries aren't clear
