---
name: subagent-driven-development
description: Execute plans via delegate_task subagents (2-stage review).
category: software-development
tags: [delegation, subagent, implementation, workflow, parallel]
source: local
is_imported: true
---

# subagent-driven-development

Execute plans via delegate_task subagents (2-stage review).

**Category:** software-development
**Source:** local

---

## Parallel Track Mode & Conflict Recovery

**Parallel subagents that modify overlapping files produce git merge conflict markers** (`<<<<<<< HEAD`, `=======`, `>>>>>>> hash`). Most common in `__init__.py` lines.

### Detection
```bash
grep -rn "<<<<<<\|=======\|>>>>>>" src/ 2>/dev/null | grep -v "^[^:]*:.*======" | head -20
```
### Systematic Fix (Python pattern)
```python
for rel_path in files:
    with open(full_path) as f:
        lines = f.read().split('\n')
    clean, in_conflict, in_ours = [], False, True
    for line in lines:
        if line.startswith('<<<<<<<'): in_conflict, in_ours = True, True; continue
        elif in_conflict and line == '=======': in_ours = False; continue
        elif in_conflict and line.startswith('>>>>>>>'): in_conflict = False; continue
        if not in_conflict: clean.append(line)
    with open(full_path, 'w') as f: f.write('\n'.join(clean))
```
### Verification Layers
1. Imports: `python -c "from pkg import *"` — SyntaxError = leftover markers
2. Class inventory vs __init__.py imports
3. Unit tests (skip slow): `pytest -k "not slow" -x`
4. Router/API imports: one import per file
5. Full test suite

**Prevention:** One subagent owns `__init__.py` and `main.py` exclusively. Never let two subagents both modify wiring files.
