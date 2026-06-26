---
name: parallel-subagent-conflicts
description: Detect, resolve, and prevent git conflict markers from sibling subagents writing to shared files in parallel delegation tasks.
category: devops
---

# Parallel Subagent Conflict Markers

When `delegate_task` spawns parallel subagents writing to the **same repository**, they can produce embedded git merge markers (`<<<<<<< HEAD`, `=======`, `>>>>>>> commit-hash`) in source files. These break Python imports with `SyntaxError: invalid digit` and must be resolved before tests can run.

## When to Activate

- After any `delegate_task` call with 2+ parallel subagents writing source files
- When tests fail with `SyntaxError: invalid digit 'N' in binary literal`
- When `ImportError: cannot import name 'X'` appears after parallel work
- When preparing to commit after a multi-agent build session

## Detection

```bash
# Fast scan — only look for the marker delimiters (avoid ======= false positives)
grep -rn "<<<<<<<\|>>>>>>>" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.yaml" --include="*.yml" .
```

**False positive trap:** The `=======` line alone appears in every Python `a = b` assignment. Never search for `=======` standalone — always pair it with `<<<<<<<` or `>>>>>>>`.

## Root Cause

Each parallel subagent reads the original file, modifies it independently, and writes back. Agent B's write arrives after Agent A's and may include conflict markers added by the delegation layer. This is **not a git merge** — the markers are injected by the sibling framework itself when two agents write to the same path.

## Resolution (Programmatic Script)

Use this script to strip conflict markers, keeping the "our" (HEAD) side:

```python
import os

EXTENSIONS = ('.py', '.ts', '.tsx', '.js', '.jsx', '.yaml', '.yml', '.json', '.md')
for root, dirs, files in os.walk('.'):
    for fname in files:
        if not fname.endswith(EXTENSIONS):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath) as f:
                content = f.read()
        except Exception:
            continue
        if '<<<<<<<' not in content:
            continue
        
        lines = content.split('\n')
        clean = []
        in_conflict = False
        in_ours = False
        for line in lines:
            if line.startswith('<<<<<<<'):
                in_conflict = True
                in_ours = True
                continue
            elif in_conflict and line == '=======':
                in_ours = False
                continue
            elif in_conflict and line.startswith('>>>>>>>'):
                in_conflict = False
                in_ours = False
                continue
            if not in_conflict or in_ours:
                clean.append(line)
        
        result = '\n'.join(clean)
        with open(fpath, 'w') as f:
            f.write(result)
        print(f"FIXED: {fname} ({len(content)} -> {len(result)} bytes)")
```

**What this keeps:**
- Content between `<<<<<<< HEAD` and `=======` ("our" side)
- Content outside any conflict marker block

**What this drops:**
- Content between `=======` and `>>>>>>> commit-hash` ("their" side)
- The marker lines themselves

**If both sides have valuable content:** modify the script to append both sides (without markers) instead of dropping "their" side.

## Post-Resolution Steps

```bash
# 1. Verify all markers are gone
grep -rn "<<<<<<<\|>>>>>>>" --include="*.py" --include="*.ts" . && echo "CONFLICTS REMAIN" || echo "CLEAN"

# 2. Run the test suite — dropped "their" side may have removed exports
python -m pytest tests/ -v -x --tb=short

# 3. Fix dropped-import errors
# Symptom: ImportError: cannot import name 'SomeClass' from 'module'
# Fix: check what SomeClass was in "their" side, re-add to module or update __init__.py
```

### Common After-Effect: Stale `__init__.py`

The most frequent downstream issue: the "their" side defined classes/functions that the "our" side's `__init__.py` was updated to reference. After stripping, `__init__.py` still has the imports but the classes are gone.

**Fix:** Check what the module actually exports after cleanup, then update `__init__.py` to match:
```python
# Run this to see what survived
python -c "from module import *; print([x for x in dir() if not x.startswith('_')])"
```

Or just regenerate `__init__.py` from the surviving classes in each file.

## Prevention (Preferred)

The best fix is avoiding the conflict entirely. Partition work by **directory ownership** in the delegation context:

```python
# Instead of overlapping write targets:
delegate_task(tasks=[
    {"goal": "Build all", "context": ""},                    # ❌ writes anywhere
    {"goal": "Build all", "context": ""},                    # ❌ writes anywhere
])

# Partition by directory:
delegate_task(tasks=[
    {"goal": "Build poker-core variant modules",
     "context": "Write ONLY to packages/poker-core/src/gto_poker/"},
    {"goal": "Build API routers",
     "context": "Write ONLY to apps/api/routers/"},
    {"goal": "Build frontend pages",
     "context": "Write ONLY to apps/web/src/app/"},
])
```

Each subagent gets an isolated terminal session. As long as directory targets don't overlap, filesystem conflicts are eliminated.

### Section-Based Single-File Prevention

**When the "one file" constraint prevents directory partitioning**, split the work by section boundaries instead. Works for large single-file HTML + CSS + JS apps.

**Partitioning strategy:** Agent A owns CSS + HTML body, Agent B owns JavaScript. Both need a shared DOM ID contract to avoid cross-agent breakage.

See `references/single-file-merge.md` in this skill's directory for the full pattern: merge script, `<body>` tag pitfall, `rfind` vs `find` for inline `<script>` detection, and post-merge verification steps.

## When NOT to Use This

Do NOT confuse sibling-subagent markers with real git merge conflicts. Real conflicts:
- Happen during `git merge` or `git rebase`
- Have actual semantic differences between branches
- Require human judgment to resolve (keep both, take ours, take theirs)

Sibling-subagent markers:
- Happen without any git operation
- Are always a programming error (the framework adding markers it shouldn't)
- Always resolved by keeping HEAD side (the most recent write)
