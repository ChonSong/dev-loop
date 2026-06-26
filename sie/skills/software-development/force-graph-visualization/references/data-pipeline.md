# Data Pipeline: SKILL.md → graph_data.json

How to scan a skills directory tree and produce the nodes/edges that feed a force-graph visualization.

## Overview

Walk `~/.hermes/skills/` (or any category-skill tree), parse each `SKILL.md` YAML frontmatter, build hub-and-spoke edges per namespace, write `graph_data.json`.

## Data source: SKILL.md directories

Hermes stores skills in a two-level tree:
```
~/.hermes/skills/
  namespace-a/
    skill-name-a/
      SKILL.md
      references/
      templates/
    skill-name-b/
      SKILL.md
  namespace-b/
    skill-name-c/
      SKILL.md
```

Each `SKILL.md` has YAML frontmatter:
```yaml
---
name: skill-name-a
description: Does X and Y
version: 1.0.0
author: Hermes
tags: [tag1, tag2]
---
...
```

## Python scanner

### Walk and parse

```python
import os, yaml, json, re, hashlib

SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
nodes = []
edges = []

for ns in sorted(os.listdir(SKILLS_DIR)):
  ns_path = os.path.join(SKILLS_DIR, ns)
  if not os.path.isdir(ns_path): continue
  for skill_name in sorted(os.listdir(ns_path)):
    skill_dir = os.path.join(ns_path, skill_name)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md): continue
    
    with open(skill_md) as f:
      content = f.read()
    
    # Parse YAML frontmatter (between ---\n and ---\n)
    parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
    meta = yaml.safe_load(parts[1]) if len(parts) >= 2 else {}
    
    node = {
      "id": skill_name,
      "name": meta.get('name', skill_name),
      "namespace": ns,
      "desc": meta.get('description', ''),
      "author": meta.get('author', ''),
      "version": meta.get('version', ''),
      "tags": meta.get('tags', []),
      "quality": deterministic_quality(skill_name),
      "lines": count_lines(skill_md),
    }
    nodes.append(node)
```

### Deterministic quality scoring

When real quality metrics aren't available, generate stable pseudo-random scores:

```python
def deterministic_quality(name):
  h = hashlib.md5(name.encode()).hexdigest()
  return round((int(h[:4], 16) % 100) / 10, 1)  # 0.0 - 9.9
```

### Hub-and-spoke edges per namespace

```python
from collections import defaultdict

ns_ids = defaultdict(list)
for n in nodes:
  ns_ids[n['namespace']].append(n['id'])

edges = []
for ns, ids in ns_ids.items():
  if len(ids) < 2: continue
  hub = ids[0]
  for nid in ids[1:]:
    edges.append({"src": hub, "tgt": nid, "type": "member-of", "label": ns})
```

### Namespace color assignment

```python
NAMESPACE_COLORS = [
  0x0A798C, 0xDF6A90, 0xFC2364, 0x3BBA2D, 0x2E4A7C,
  0xE87A3E, 0x4ECB71, 0x9B7ACC, 0x3498DB, 0xE84A5F,
  0x1ABC9C, 0xF39C12, 0x2980B9, 0x8E44AD, 0xD35400,
  0x27AE60, 0xC0392B, 0x7F8C8D, 0x16A085, 0xF1C40F,
]

sorted_ns = sorted(set(n['namespace'] for n in nodes))
ns_color_map = {ns: NAMESPACE_COLORS[i % len(NAMESPACE_COLORS)] for i, ns in enumerate(sorted_ns)}
```

### Write output (compact JSON)

Use compact JSON to reduce payload size by ~40%:

```python
output = {
  "nodes": nodes,
  "edges": edges,
  "ns_colors": ns_color_map,
  "edge_types": [
    ["member-of", "Same namespace", 0x0A798C, 0.3],
  ],
  "edge_filter_default": {"member-of": True},
  "namespace_order": sorted_ns,
}
with open("graph_data.json", "w") as f:
  json.dump(output, f, separators=(',', ':'), indent=1)  # compact (40% smaller)

print(f"Generated {len(nodes)} nodes, {len(edges)} edges")
print(f"File size: {os.path.getsize('graph_data.json')/1024:.0f}KB")
```

**Compact vs pretty**: `separators=(',', ':')` removes whitespace between JSON tokens. For 500KB of structured data this saves ~200KB. The graph page loads faster and the inline HTML stays under 600KB.

## Quality field extraction (when available)

Some SKILL.md files have richer frontmatter. Extract numeric fields for size-by controls:

```python
SKILL_METRICS = ['quality', 'steps', 'examples', 'pitfalls']

for metric in SKILL_METRICS:
  val = meta.get(metric)
  if val is not None:
    try:
      node[metric] = float(val) if '.' in str(val) else int(val)
    except (ValueError, TypeError):
      pass
```

### Score distribution analysis

After building the dataset, print stats to inform default thresholds:

```python
import numpy as np

scores = [n.get('quality', 0) for n in nodes]
print(f"Quality range: {min(scores):.1f} - {max(scores):.1f}")
print(f"Quality median: {np.median(scores):.1f}")
print(f"Quality mean: {np.mean(scores):.1f}")
print(f"Nodes with quality < 4: {sum(1 for s in scores if s < 4)}")
```

Use these to set the default MinQ slider value.

## Edge patterns compared

| Pattern | Implementation | Edge count | Clumping risk | Best for |
|---------|---------------|------------|--------------|----------|
| Hub-and-spoke (static) | First node → all others in namespace | O(n) | High — all nodes pull to one hub | Medium groups (30-200) |
| Complete subgraph (static) | Every node → every other in group | O(n²) | Low — forces spread evenly | Small groups (<15) |
| Chain/sparse tree (static) | Random sample connected A→B→C | O(n) | Low — distributed along path | Large groups (200+) |
| Tag-based (runtime) | JS computes on page, threshold slider | O(n·t²) worst | Depends on density | Cross-cutting connections |
| Workflow-peer (static) | Same-role nodes connect | O(n) per role | Moderate | Role-based structure |

### Chain/sparse tree implementation

For large namespaces (200+ nodes), hub-and-spoke creates a single gravity well. Use a random chain of ~20 sampled nodes instead:

```python
import random
random.seed(hash(namespace))
samples = random.sample(ids, min(20, len(ids)))
for i in range(len(samples) - 1):
    edges.append({
        "src": samples[i], "tgt": samples[i+1],
        "type": "member-of", "label": namespace
    })
```

This distributes force along the chain path instead of concentrating at one hub. Nodes spread out instead of clumping. The 20-sample cap keeps edge count constant regardless of namespace size.

## Edge count budgeting

| Node count | Max safe edges | Pattern | HTML strategy |
|-----------|---------------|---------|--------------|
| < 100 | < 500 | Any | Inline in <script> |
| 100-500 | < 2000 | Hub-and-spoke only | Inline OK |
| 500-1500 | < 3000 | Hub-and-spoke, member-of OFF default | Async fetch |
| > 1500 | < 5000 | Hub-and-spoke, namespace filter initial | Async fetch |
