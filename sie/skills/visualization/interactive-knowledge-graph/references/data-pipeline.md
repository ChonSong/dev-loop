# Data Pipeline for Knowledge Graphs

## Data Sources

| Format | Parser | Example |
|--------|--------|---------|
| README bullet list (`- **[name](url)** - desc`) | Extract last bold block containing a link | VoltAgent/awesome-agent-skills |
| README mixed (`- **[beta]** [name](url) by [author] - desc`) | Match `- ` then extract name from first link | 0xNyk/awesome-hermes-agent |
| Local SKILL.md (`namespace/skillname/SKILL.md`) | Parse YAML frontmatter | Local skills |

## Edge Generation Strategies

### 1. Hub-and-spoke (default for all group sizes)

One "hub" node per namespace connects to all others. Keeps edge count linear.

```python
if len(ids) > 1:
    hub = ids[0]
    for nid in ids[1:]:
        edges.append({"src": hub, "tgt": nid, "type": "member-of", "label": ns})
```

### 2. Quality-filtered edges

Only create edges where both nodes meet a minimum quality threshold. Dramatically reduces visual clutter.

```python
filtered_nodes = [n for n in nodes if n['quality'] >= min_q]
filtered_ids = {n['id'] for n in filtered_nodes}
filtered_edges = [e for e in edges if e['src'] in filtered_ids and e['tgt'] in filtered_ids]
```

### 3. Tag-based edges (runtime computation)

```javascript
const tagIndex = {};
nodes.forEach(n => (n.tags || []).forEach(t => {
  if (!tagIndex[t]) tagIndex[t] = [];
  tagIndex[t].push(n.id);
}));

function computeTagEdges(threshold) {
  const seen = new Set();
  const result = [];
  for (const ids of Object.values(tagIndex)) {
    if (ids.length < threshold) continue;
    if (result.length > 15000) break;  // safety cap
    for (let i = 0; i < ids.length; i++)
      for (let j = i + 1; j < ids.length; j++) {
        const key = ids[i] < ids[j] ? `${ids[i]}|${ids[j]}` : `${ids[j]}|${ids[i]}`;
        if (!seen.has(key)) {
          seen.add(key);
          result.push({ src: ids[i], tgt: ids[j], type: 'tag-shared', label: `${threshold}+ tags` });
        }
      }
  }
  return result;
}
```

## Namespace Color Assignment

```python
NAMESPACE_COLORS = [
    0x0A798C, 0xDF6A90, 0xFC2364, 0x3BBA2D, 0x2E4A7C,
    0xE87A3E, 0x4ECB71, 0x9B7ACC, 0x3498DB, 0xE84A5F,
    # ... extend as needed
]
ns_color_map = {ns: NAMESPACE_COLORS[i % len(NAMESPACE_COLORS)] for i, ns in enumerate(sorted_namespaces)}
```

## Quality Score Generation

For data without real quality metrics, generate deterministic scores:

```python
import hashlib
h = hashlib.md5(name.encode()).hexdigest()
quality = round((int(h[:4], 16) % 100) / 10, 1)  # 0.0 - 9.9
```

## Edge Count Budget

| Node count | Max edges | Pattern |
|-----------|-----------|---------|
| < 100 | < 500 | Any |
| 100-500 | < 2000 | Hub-and-spoke only |
| > 500 | < 3000 | Hub-and-spoke, member-of OFF by default |
| > 1000 | Use async fetch | Don't inline data in HTML |

## Inline vs Async Data

```python
# Inline (small graphs): JSON embedded in <script>
# Good for HTML < 200KB

# Async (large graphs): JSON in separate file
# Required for graphs > 500 nodes
# HTML stays small (~30KB), data loads separately
# wrap init in async IIFE:
const _main = async () => {
  const r = await fetch('graph_data.json');
  const data = await r.json();
  // ... rest of init
};
_main();
```
