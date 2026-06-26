# Inline Build for Large Data (500KB+ JSON)

When embedding large graph data as inline JSON in a self-contained HTML file, Python's `str.replace()` on a 1MB+ string often causes `MemoryError`. This reference covers the file-concatenation workaround.

## Problem

```python
# ❌ FAILS with MemoryError on 500KB+ data
with open('index.html') as f:
    html = f.read()
html = html.replace(old, new)  # MemoryError — double-allocates the full string
```

Python creates a new string in memory when replacing, doubling peak memory usage. For a 1MB HTML file with a 500KB data blob, peak usage is ~3MB — normally fine, but in constrained environments (Docker containers, Hermes subagents) it can fail.

## Solution: File-level concatenation

Split the HTML into three parts at the script tag boundary, then concatenate with `cat`:

```
_pre.html          → Everything before the data <script> tag
_data.json         → The graph data as compact JSON
_runtime.js        → The JS runtime code (filter buttons, rebuild, etc.)
_post.html         → Everything after the closing </script> of the data script
```

**Step 1: Split the template**

```python
with open('index.html') as f:
    h = f.read()

# The FIRST <script> is the CDN import. The SECOND <script> is the data script.
script_open = h.find('<script>', h.find('</script>') + 9)  # skip CDN tag
script_close = h.find('</script>', script_open)

pre = h[:script_open]     # up to and including '<script>'
post = h[script_close + 9:]  # after '</script>'
```

**Step 2: Build the data**

```python
import json
with open('graph_data.json') as f:
    data = json.load(f)
# Compact JSON — 40% smaller
compact = json.dumps(data, separators=(',', ':'))
with open('_data.json', 'w') as f:
    f.write(compact)
```

**Step 3: Write the JS runtime to a file**

The JS code that reads `var D=` and renders the graph. Write this to `_runtime.js` using `write_file`.

**Step 4: Concatenate**

```bash
cat _pre.html > index.html
printf '<script>var D=' >> index.html
cat _data.json >> index.html
printf ';\n' >> index.html
cat _runtime.js >> index.html
printf '\n</script>' >> index.html
cat _post.html >> index.html
```

Each `cat`/`printf` only appends data — no in-memory string replacement needed.

## Pitfalls

### `</script>` split bug

When finding the data script boundaries, the **first** `<script>` in the HTML might be a CDN import (e.g., `force-graph.min.js`), not the data script. Always skip the CDN script before looking for the data script:

```python
# Skip the first <script> tag (CDN import)
first_close = h.find('</script>')
script_open = h.find('<script>', first_close)
```

If you use `h.find('<script>')` (first match), you'll split at the CDN import — the "post" part will contain the data script plus everything else, and the data script's `</script>` will be orphaned, creating `</script></script>` in the output.

### Verify after concatenation

```bash
# Check the concatenation worked
python3 -c "
with open('index.html') as f:
    h = f.read()
print(f'Size: {len(h)/1024:.0f}KB')
print(f'</script> count: {h.count(\"</script>\")}')  # Should be 2 (CDN + data)
print(f'var D=: {\"var D=\" in h}')
# Verify data parses
import json, re
start = h.find('var D=') + 6
# ... parse matching braces ...
data = json.loads(h[start:end])
print(f'Nodes: {len(data[\"nodes\"])}')
"
```

### Avoid `read_file()` for large HTML

`read_file()` prefixes each line with `LINE_NUM|`, which corrupts inline JSON. Use `terminal("cat index.html")` or `execute_code` with `open().read()` for raw file content.
