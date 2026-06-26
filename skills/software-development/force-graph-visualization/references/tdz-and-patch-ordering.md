# TDZ Errors and Patch Ordering in Large Single-File JS

## The TDZ Problem

`const` and `let` in JavaScript are NOT hoisted like `var`. Referencing them before declaration throws:
```
Uncaught ReferenceError: Cannot access 'X' before initialization
```

This is especially dangerous in large single-file HTML pages where:
- Data (GRAPH_DATA JSON) is at the top
- Variable declarations are scattered
- Functions reference variables declared later

### Common pattern that breaks:

```javascript
// Line 900: GRAPH_DATA declared
const GRAPH_DATA = { ... };

// Line 902: Early declarations (GOOD)
const TAG_SHARED = 'tag-shared';
let tagEdges = [];

// Line 1036: tagEdges used in button count — OK, declared at 902
btn.innerHTML = `...${tagEdges.length}`;

// Line 1068: updateStats() references tagEdges — OK, tagEdges declared at 902
updateStats(nodes.length, edges.length + tagEdges.length);

// Line 1191: tagEdges assigned
tagEdges = computeTagEdges(tagThreshold);
```

### What breaks it:

If `let tagEdges = []` is declared at line 1125 (after the edge_types.forEach loop at line 1036), the loop at 1036 crashes because `tagEdges` is in TDZ.

**Fix**: Move ALL `let`/`const` declarations to the top of the script, before any code that references them. Function bodies are safe (they execute when called, not when declared).

### Debugging TDZ:

1. Look for `Cannot access 'X' before initialization` in console
2. Find the line where `X` is declared with `let`/`const`
3. Find all references to `X` before that line
4. Move the declaration before the first reference

## The Multi-Patch Cascading Failure Problem

When using many small `patch` calls on a large file:

1. Patch 1 changes line 100, adding 5 lines → everything after shifts +5
2. Patch 2 targets `old_string` at original line 105 → now line 110 → **no match, silent failure**
3. Patch 3, 4, 5... all fail silently

**Symptoms**: Some fixes apply, others don't. File is partially patched. No error thrown.

**Fix**: For >5 changes to a single file, use a single Python script:
```python
with open('file.html') as f:
    content = f.read()

content = content.replace(old1, new1)
content = content.replace(old2, new2)
# ... all replacements ...

with open('file.html', 'w') as f:
    f.write(content)
```

This avoids line-number shifts entirely since all replacements operate on the original string.

**When to use many small patches**: Only when each patch is independent (targets unique strings that won't shift) and you verify each one succeeded.

## Verification Checklist After Patching

After any patch session on a large JS file:

1. **Syntax balance**: Count `{}`, `[]`, `()` — all must balance
2. **TDZ scan**: Verify every `const`/`let` declaration appears before its first use
3. **Feature scan**: `grep` for key function/feature names to confirm they exist
4. **Deploy and test**: `curl` the deployed page, check for JS errors in console
5. **Diff review**: `git diff` to confirm all intended changes landed
