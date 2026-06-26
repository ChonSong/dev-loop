# Skill Graph Edge Curation — Known Patterns

## Problem Observed (May 2025)

Hermes knowledge graph visualization had all 75 skill nodes appearing **disconnected** despite having thousands of raw edges.

### Root Cause

Two compounding issues:

1. **JSON schema surprise**: `enriched-skills-graph.json` is a dict with `{skills, edges: {same_category, same_tag, depends_on}, stats, categories}` — NOT a plain array. Code assuming array structure silently got nothing.

2. **`same_category` has zero signal when all skills share one category**: All 75 skills had `category: "uncategorized"`. The 2775 pair combinations connected everything to everything — graph exploded O(n²) AND had no discriminative power.

## Edge Curation Strategy That Worked

Five complementary strategies, each with hard limits:

| Strategy | Signal | Limit | Example |
|----------|--------|-------|---------|
| `member-of` | Same namespace | Top-3 per namespace | `creative` (19 skills) → 37 edges |
| `tool-use` | Shared tools | Top-2 per tool | `terminal` (12 uses) → 92 edges |
| `workflow-peer` | Same workflow_role | All-to-all for roles appearing 2+ times | `client`, `orchestrator` groups |
| `quality-hub` | High-quality skills connect | Top-3 per quality tier | verified/complexity rich skills |
| `cross-ref` | Explicit skill references | Unused in practice | — |

**Total curated: 190 edges for 75 nodes** — well within safe defaults (<500 for 100-500 nodes).

## Metadata Fields Available for Filtering

Skills came with rich metadata rarely used in edges:

```
verified, complexity, has_examples,
steps, examples, pitfalls,
namespace, tools_used, skill_dependencies,
workflow_role, collector
```

Filtering by these (especially `verified` + `complexity`) dramatically reduces edge noise vs pure category/tag similarity.

## Recipe: Compute Curated Edges

```python
import json
from collections import defaultdict

with open('enriched-skills-graph.json') as f:
    data = json.load(f)

skills = data['skills']
edges = data['edges']

# Build indexes
ns_skills = defaultdict(list)   # namespace → [skill_ids]
tool_skills = defaultdict(list) # tool → [skill_ids]
role_skills = defaultdict(list) # role → [skill_ids]
quality_hubs = []               # high-quality skill_ids

for s in skills:
    ns_skills[s.get('namespace', 'unknown')].append(s['id'])
    for t in s.get('tools_used', []):
        tool_skills[t].append(s['id'])
    r = s.get('workflow_role')
    if r: role_skills[r].append(s['id'])
    if s.get('verified') and s.get('complexity') in (3,4):
        quality_hubs.append(s['id'])

# 1. member-of: top-3 per namespace
# 2. tool-use: top-2 per tool (avoids O(n²) within popular tools)
# 3. workflow-peer: all pairs for roles appearing 2+
# 4. quality-hub: connect top-3 between quality tiers
# 5. cross-ref: explicit skill_dependencies
```

## Console Debug Commands

```javascript
// Check what data actually arrived
fetch('graph_data.json').then(r=>r.json()).then(d=>{
  console.log('nodes:', d.nodes.length, 'links:', d.links.length);
  console.log('edge types:', [...new Set(d.links.map(l=>l.type))]);
});

// Check SVG was populated
d3.selectAll('circle').size()   // 0 = SVG empty
d3.selectAll('.node').size()    // node count
d3.selectAll('.link').size()    // edge count
```

## Lessons

- **Always inspect JSON structure before assuming**: `enriched-skills-graph.json` is a dict, not an array
- **`same_category` is useless signal when all values are identical** — check cardinality before using
- **Hard limits per category prevent O(n²)** even when tool overlap is high
- **Namespace hierarchy is the most reliable connection signal** for skill graphs
- **Multiple weak signals (4 strategies) beat one strong signal** that doesn't exist in the data