# JS Variable Declaration Ordering — `let`/`const` Temporal Dead Zone

## The Pattern

When inserting new JavaScript code into an existing `<script>` block, you **must** check that all variables the new code references are already declared before the insertion point.

`let` and `const` are **not hoisted** like `var`. Referencing them before their declaration line throws a `ReferenceError`:

```
Uncaught ReferenceError: Cannot access 'activeNamespaces' before initialization
```

This error is **silent** in production — the page just renders nothing or partially renders, with no visible error message to the user (unless they open the DevTools console).

## Symptoms

- Feature you just deployed is invisible/broken
- `curl` confirms the new source code IS deployed correctly
- On GitHub Pages: takes 30–60s to deploy (verify with `curl -sL <url> | grep`)
- Headless Chrome screenshot shows blank/broken page

## Reproduction (this session)

1. Graph page had an existing `let activeNamespaces = ...` declaration at line ~1022
2. I inserted new JS code at line ~930 that referenced `activeNamespaces.has(...)`
3. The new code ran first at parse time, hit the temporal dead zone, and threw
4. The entire `<script>` block failed execution — no graph, no legend, nothing
5. Fix: moved the `let activeNamespaces` declaration to line ~928, before the insertion

## Prevention Checklist

When inserting new JS code into an existing script:

- [ ] Search for all variables your new code uses (function calls, property access, assignments)
- [ ] Find where each variable is declared (`let`, `const`, `var`, or function param)
- [ ] If any declaration comes AFTER your insertion point → move it earlier, OR
- [ ] Replace the forward reference with a self-contained approach
- [ ] After deploying, verify the page works (not just that the source changed)
