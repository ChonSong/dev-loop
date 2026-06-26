---
name: inline-viz-debug
title: Debugging Large Inline Visualization Pages
description: Patterns for debugging single-file HTML pages with embedded data and force-graph / D3 visualizations
---

# Debugging Large Inline Visualization Pages

Trigger: working on a single-file HTML page (>100KB) with inline JSON data and force-graph, D3, or canvas visualization.

## Force-Graph v1 API Differences (version 1.43.5)

- **No `.linkOpacity()` method** — that's v2+. V1 uses `.linkColor()` + `.linkWidth()` only.
- To control edge opacity: make `linkColor` return `rgba(r,g,b,alpha)` with the desired alpha.
- Trigger re-render on slider change: call `graph.linkColor(getLinkColor)` (not `linkOpacity`).
- Available methods: `linkColor`, `linkWidth`, `linkCurvature`, `linkDirectionalParticles`, `linkDirectionalArrowColor`, `linkDirectionalArrowLength`, `linkDirectionalArrowRelPos`, `linkLabel`, `linkLineDash`, `linkHoverPrecision`, `linkAutoColorBy`, `linkCanvasObject`, `linkSource`, `linkTarget`.

## TDZ (Temporal Dead Zone) in Inline Scripts

When a single `<script>` block contains both inline JSON data (500KB+) and application logic:

1. **All `const`/`let` declarations must precede any usage**, even if the code is in different sections.
2. Common failure: edge filter buttons reference `TAG_SHARED`, `tagEdges`, and `edgeFilterDefault` before they're declared further down.
3. **Fix**: move all shared constants and empty-initialized arrays to the top of the script, right after the data destructuring.
4. **Symptoms of TDZ**: blank page, "Cannot access 'X' before initialization" in console, no render at all.
5. **Verify**: `grep -n "const\|let " file.html | head -30` to check declaration order against usage.

## Patching Strategy for Large Files

Avoid 30+ individual `patch` calls on 500KB+ files — they're brittle (whitespace mismatches, duplicate lines).

**Better approach**: Use `execute_code` with Python `str.replace()`:
```python
with open('file.html') as f:
    html = f.read()
html = html.replace(old_string, new_string)
# ... do all replacements in one pass ...
with open('file.html', 'w') as f:
    f.write(html)
```

This is atomic, handles any file size, and lets you batch all changes.

## References

- `references/force-graph-api-v1.md` — force-graph 1.x API quirks
- `references/tdz-inline-debug.md` — TDZ patterns in single-file apps
