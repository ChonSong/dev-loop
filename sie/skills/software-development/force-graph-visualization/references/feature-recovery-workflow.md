# Git-Based Feature Recovery for Knowledge Graphs

When iterating on a force-graph page, it's common to accidentally strip features by rebuilding from scratch (e.g., replacing the entire `<script>` block with a simpler version). The old version often has working tag-edge computation, rich detail panels, nodeCanvasObject overrides, edge filter logic, and other UX details that the new version lacks.

## Recovery workflow

### 1. Find the last good commit

```bash
git log --oneline | head -20
```

Old version commits typically have descriptive messages like "Add tag edge threshold and size-by controls" or "Enable tag edges by default".

### 2. Extract the old HTML's JS structure

```bash
git show <OLD_COMMIT>:index.html > /tmp/old.html
```

### 3. Extract the old JS body (without inline data)

```bash
python3 -c "
import re
with open('/tmp/old.html') as f:
    h = f.read()
# Find the script start after data
si = h.find('const GRAPH_DATA')  # or 'var D='
if si == -1: si = h.find('var D=', h.find('<script>'))
ei = h.find('</script>', si)
old_js = h[si:ei]
# Remove data assignment
old_js = re.sub(r'(var D|const GRAPH_DATA|const D)\s*=\s*\{.*?\};', '', old_js, 1, re.DOTALL)
# Remove destructuring lines
old_js = re.sub(r'const \{.*?\} = (D|GRAPH_DATA);\n', '', old_js)
# Update references
old_js = old_js.replace('GRAPH_DATA.', 'D.')
with open('/tmp/clean_old.js', 'w') as f:
    f.write(old_js)
print(f'Extracted: {len(old_js)} chars')
"
```

### 4. Validate the old JS syntax

```bash
node -e "
const fs = require('fs');
try {
    new Function(fs.readFileSync('/tmp/clean_old.js', 'utf8'));
    console.log('Syntax OK');
} catch(e) {
    console.log('Syntax error:', e.message.slice(0, 200));
}
"
```

### 5. Merge with current data

Append `var D = <current_data_json>;` before the old JS, or use a separate `<script src="data.js">` tag.

## Comparison technique

To detect what features differ between old and new versions:

```bash
python3 -c "
with open('/tmp/old.html') as f: old = f.read()
with open('index.html') as f: cur = f.read()

features = [
    'tag-threshold', 'quality-bar', 'detail-badges', 'conn-list',
    'copy-qname', 'nodeCanvasObject', 'TAG_SHARED', 'toggle-all-btn',
    'search-input', 'zoomToFit', 'empty-state', 'min-quality', 'graph-info',
    'charge-strength', 'link-distance', 'size-by', 'legend-edges'
]
for f in features:
    in_old = f in old
    in_cur = f in cur
    if in_old and not in_cur:
        print(f'MISSING in new: {f}')
    elif not in_old and in_cur:
        print(f'NEW feature: {f}')
"
```

## Common features that get stripped on rebuild

- Tag edge system (`TAG_SHARED`, `computeTagEdges`, `tag-threshold` input)
- Detail panel quality bar (`quality-bar`, `quality-val`, `quality-fill`)
- Detail badges (verified, complexity)
- Connections list with click-to-navigate (`conn-list`, `conn-item`)
- Copy qualified name button (`copy-qname`)
- Verified node ring (`nodeCanvasObject`)
- Node labels showing namespace context (`name (namespace)`)
- Stats showing namespace visibility (`Z/W ns`)
- Empty state message
- MinQ slider
- Tool/tag chips in detail panel
