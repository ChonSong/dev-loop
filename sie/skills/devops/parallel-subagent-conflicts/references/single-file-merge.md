# Section-Based Single-File Merge Pattern

## When to Use

You have a large single-file HTML app (CSS + HTML + JS + inline JSON, 600KB+) and need to parallelize feature implementation across subagents. The file is too large for one agent and the dependency constraint ("each track MUST have exclusive file ownership") seems to block parallelism.

## Solution: Partition by HTML Section Boundaries

### File Structure

```
<head_prefix>       <!-- <head>, CDN scripts, metadata — typically no changes needed -->
<style>
  ...               /* CSS section — owned by Agent A */
</style>
<body>
  ...               /* HTML DOM — owned by Agent A (adds buttons, panels, etc.) */
<script>
  ...               /* JavaScript — owned by Agent B (adds event handlers, graph config, etc.) */
</script>
</body>
</html>
```

### Partitioning

| Agent | Owns | Creates |
|-------|------|---------|
| A | CSS + HTML body | New buttons, panels, responsive CSS, filter chips, mobile layout |
| B | JavaScript (inline `<script>` block) | Event handlers, localStorage, keyboard shortcuts, graph configuration |

### Shared DOM ID Contract

Both agents get a spec document listing every DOM ID Agent A creates and Agent B references. Without this contract, Agent B's JS silently fails (null references) and the page breaks with no error message visible.

**Example contract (from a knowledge graph single-file app):**

| Agent A creates | Agent B references |
|----------------|-------------------|
| `#btn-reset-view` | `document.getElementById('btn-reset-view')` |
| `#filter-chips` (with `.chip` children) | `document.querySelectorAll('#filter-chips .chip')` |
| `#btn-mobile-menu` | `document.getElementById('btn-mobile-menu')` |
| `#sidebar` | `document.getElementById('sidebar').classList.toggle('open')` |

Agent A must create every listed ID. Agent B should use optional chaining (`?.`) or null guards.

### Merge Script

```python
def merge(agent_a_html: str, agent_b_html: str) -> str:
    """Merge two edits of the same single-file HTML by section boundaries.
    
    Takes CSS + HTML body from Agent A, JavaScript from Agent B.
    """
    def split(text):
        style_s = text.find('<style>')
        hp = text[:style_s]
        
        se = text.find('</style>') + len('</style>')
        st = text[style_s:se]
        
        bs = text.find('<body>') + len('<body>')
        # Crucial: use rfind, not find — inline JSON may contain "<script>"
        si = text.rfind('<script>', 0, text.find('</body>'))
        bh = text[bs:si]
        
        be = text.find('</body>', si)
        sc = text[si:be]
        
        sx = text[be:]
        return hp, st, bh, sc, sx
    
    a = split(agent_a_html)
    b = split(agent_b_html)
    
    return a[0] + a[1] + '<body>\n' + a[2] + b[3] + a[4]
```

### CRITICAL: Post-Merge Verification

After the merge, run these checks before committing:

```bash
# 1. Tag structure — verify every tag exists and is in the right order
grep -n '<head>\|</head>\|<body>\|</body>\|<script\|</script>\|<style>\|</style>\|<html>\|</html>' index.html
```
Expected order:
```
N:<head>
N:<script src="CDN..."></script>
N:<style>
N:</style>
N:<body>
N:<script>
N:</script>
N:</body>
N:</html>
```

```python
# 2. Structural completeness
for tag in ['DOCTYPE html', 'body', '/body', '/html', 'style', '/style', '/script']:
    if tag not in html:
        print(f'❌ MISSING: {tag}')
```

```bash
# 3. JSON data integrity — check inline data survived the merge
python3 -c "
import re, json
with open('index.html') as f:
    html = f.read()
m = re.search(r'const GRAPH_DATA = ({.*?});', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print(f'Nodes: {len(data[\"nodes\"])}, Edges: {len(data[\"edges\"])}')
else:
    print('DATA NOT FOUND — JSON may be corrupted')
"
```

### Known Pitfalls

#### 1. Missing `<body>` Tag

The `split` function's `body_html` starts AFTER the `<body>` tag (`+ len('<body>')`), but the merge must re-insert it. Without it, the browser renders all CSS as visible text content.

**Fix:** Always insert `<body>\n` explicitly in the merge concatenation.

#### 2. `find` vs `rfind` for `<script>` Detection

When the inline JSON data (500KB+) contains the literal string `<script>` inside a value (e.g. a skill description mentioning "writes `<script>` tags"), `text.find('<script>', body_start)` returns the position INSIDE the JSON data, not the actual script tag.

**Fix:** Use `text.rfind('<script>', 0, text.find('</body>'))` to get the LAST `<script>` before `</body>` — the inline script block.

#### 3. CSS Count vs Inline JSON Lines

After merge, verify that:
- The CSS section starts and ends properly (`<style>` → `</style>`)
- The body HTML starts with `<body>` (not raw text)
- The JSON data is valid (parseable)
- The static layout config is preserved (e.g., `d3AlphaDecay(1)`)

**Quick scan:**
```bash
grep -c 'd3AlphaDecay(1)\|linkCurvature\|localStorage\|location.hash' index.html | xargs
```
Expected: each feature appears at least once.
