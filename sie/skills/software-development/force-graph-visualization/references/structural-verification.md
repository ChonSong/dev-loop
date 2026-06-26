# Structural Verification for Large ForceGraph Pages

When headless Chrome cannot capture a force-graph page (1000+ nodes, simulation takes >15s, VTB kills `onEngineStop`, or Chrome 143 `--screenshot` is broken), use **structural verification** — inspect the live page source via `curl` and validate the data + DOM programmatically. This confirms correctness when visual screenshots are impossible.

## Why structural verification works

For force-graph pages, "broken" almost always falls into one of these categories:

| Symptom | Catches... |
|---------|-----------|
| Inline JSON has mismatched braces | Data parse failure — nothing renders |
| Key element IDs missing from DOM | JS initialization skipped or threw |
| JS syntax errors (ReferenceError, SyntaxError) | Code never ran |
| `graphData()` called before `typeof DATA === 'undefined'` | Data variable not defined in scope |
| Edge types exist in data but not in `edge_types` array | Edges present but never render (silently) |

All of these are **structural** problems, visible in page source. A structural check catches every common failure mode *before* a screenshot would matter.

## Procedure

```bash
curl -sL https://chonsong.github.io/<repo>/ | python3 -c "
import sys, json, re
html = sys.stdin.read()
errors = []

# 1. Parse and validate inline JSON data
m = re.search(r'var D=(\{.*?\});', html, re.DOTALL)
if not m:
    m = re.search(r'const DATA\s*=\s*(\{.*?\});', html, re.DOTALL)
if m:
    try:
        d = json.loads(m.group(1))
        print(f'OK: {len(d[\"nodes\"])} nodes, {len(d[\"edges\"])} edges')
    except json.JSONDecodeError as e:
        errors.append(f'JSON PARSE FAILED: {e}')

    # Check brace balance in the data blob
    raw = m.group(1)
    ob = raw.count('{')
    cb = raw.count('}')
    if ob != cb:
        errors.append(f'BRACE IMBALANCE: {ob} open, {cb} close')
else:
    errors.append('NO INLINE DATA FOUND')

# 2. Verify key DOM element IDs
required = ['rebuild', 'showD', 'nodeSz', 'activeNS', 'activeTypes',
            'graphData', 'onNodeClick', 'zoomToFit', 'onEngineStop',
            'detail-panel', 'charge-strength', 'link-distance']
for el in required:
    if el not in html:
        errors.append(f'MISSING ELEMENT: {el}')

# 3. Verify JS functions are defined (not just referenced)
funcs = ['function filteredEdges', 'function rebuild', 'function nodeSize',
         'function updateStats']
for f in funcs:
    if f not in html:
        errors.append(f'MISSING FUNCTION: {f}')

# 4. Verify edge type completeness (data has types not in edge_types)
edge_types_match = re.findall(r\"'([a-z-]+)'.*?activeTypes\", html)
if edge_types_match:
    print(f'Active types: {set(edge_types_match)}')

# 5. Report
if errors:
    print('FAILURES:')
    for e in errors: print(f'  ✗ {e}')
    sys.exit(1)
else:
    print('ALL CHECKS PASSED: data valid, DOM present, JS functions defined')
"
```

## Interpretation

| Output | Meaning | Action |
|--------|---------|--------|
| "OK: 1351 nodes, 2671 edges" | Data loaded and parsed | ✅ |
| "BRACE IMBALANCE: 4026 open, 4027 close" | One extra/missing `}` in inline JSON | Check `write_file()` or `patch` for corruption |
| "NO INLINE DATA FOUND" | Data variable name doesn't match regex | Adjust regex or check if using async fetch |
| "MISSING ELEMENT: detail-panel" | JS didn't create the DOM or the feature was dropped | Check the commit diff for feature removal |
| "MISSING FUNCTION: function rebuild" | JS code block incomplete | Check for syntax errors in the inline script |
| "ALL CHECKS PASSED" | Everything structurally correct | User should verify in a real browser — simulation timing is the only remaining variable |

## When to use this vs other debugging approaches

| Approach | When | Cost |
|----------|------|------|
| **Structural verification (this)** | Screenshot fails, canvas is blank, VTB limited | 1 curl + 1 py script = 2 terminal calls |
| **PDF line-check** | Need to confirm canvas actually drew something | Needs Chrome + PDF bytes parse |
| **CDP runtime evaluation** | Structural checks pass but graph still blank | Needs Node.js + ws module + Chrome CDP |
| **Minimal test page** | Need to confirm ForceGraph library itself works | Static HTML + Python http.server |

**Use structural verification first** — it's the fastest, catches the most common failure modes, and doesn't depend on Chrome at all.

## Limitations

- Cannot detect runtime errors (ReferenceError for a variable used inside a closure, `d3Force('charge')` call on undefined)
- Cannot detect visual problems (wrong colors, overlapping text, incorrect sizing)
- Cannot detect timing problems (simulation never settles, nodes stuck at origin)
- For async fetch pages, only verifies the HTML shell — the JSON data must be checked separately with `curl graph_data.json`
