---
name: d3-performance-debugging
description: Debug D3.js force simulation performance issues — O(n²) edge explosions, DOM thrash, tick overload, and browser hang. Trigger when graph/page is unresponsive, memory balloons, or graph nodes appear clumped/stuck.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [d3, force-simulation, performance, graph-debugging, dom-thrash]
    related_skills: [software-development/systematic-debugging]
---

# D3 Performance Debugging

## When to Use

Trigger when:
- Graph page loads blank or unresponsive
- Browser RAM reaches 3-5GB for a single page
- Graph nodes appear clumped together (simulation didn't run) or spread stuck
- Page renders fine with 100 nodes but hangs at 1000+

**Prerequisite:** Load `software-development/systematic-debugging` first — this skill applies systematic root-cause analysis to D3 graph performance.

## Phase 1: Classify the Bottleneck

D3 performance failures cluster into three buckets. Identify which:

### Bucket A: Edge Count Explosion (O(n²))

**Signal:** Nodes spread OK at low counts, browser hangs at ~500+ nodes with category/group similarity edges.

**Mechanism:** Code generates edges for every pair in a group:

```javascript
// PROBLEMATIC: O(n²) — every same-category pair gets an edge
for (const s of SKILLS) {
  for (const t of SKILLS) {
    if (s.category === t.category) {
      graph.addEdge(s.name, t.name, { category: s.category });
    }
  }
}
// 3928 nodes → ~7.7 million edges (3928 × 3927 / 2)
```

**Detection:** Count edges and nodes at render time:
```javascript
console.log('nodes:', d3.selectAll('.node').size(), 'edges:', d3.selectAll('.edge').size());
```

### Bucket B: Tick DOM Thrash

**Signal:** Page loads but is laggy/scrolling stutters. High CPU even after nodes settle.

**Mechanism:** `simulation.on('tick', () => render())` calls expensive DOM updates every frame (300-500 iterations).

### Bucket C: Safe Defaults Missing

**Signal:** Graph looks random, no category clustering visible even though nodes have categories.

**Mechanism:** Category clustering relies on hub nodes being visible by default. Default state IS architecture — unsafe defaults create O(n²) on page load without any user action.

## Phase 2: Fixes by Bucket

### Fix A: Hub-and-Spoke (Reduce O(n²) to O(n))

Replace pair edges with one hub node per category:

```javascript
// GOOD: O(n) edges — one hub per category, each node connects once
const categoryHubs = new Set(SKILLS.map(s => s.category));
categoryHubs.forEach(cat => graph.addNode(`__cat_hub_${cat}`, { hub: true }));

SKILLS.forEach(s => {
  graph.addEdge(s.name, `__cat_hub_${s.category}`);
});
```

**Result:** ~N + N_hubs edges instead of O(n²). At 3928 skills with 50 categories → ~4000 edges vs 7.7M (−99.95%).

### Fix B: Tick Throttling

```javascript
// GOOD: Only render during active simulation phase
simulation.on('tick', () => {
  if (simulation.alpha() > simulation.alphaMin()) {
    render();
  }
});

// GOOD: Final stable render when simulation ends
simulation.on('end', () => render());
```

### Fix C: Safe Defaults for Graph Data Size

Before shipping any graph visualization:

| Data size | Max edges target |
|-----------|-----------------|
| <100 nodes | 200 edges |
| 100-500 | 500 edges |
| 500-2000 | 1000 edges |
| 2000+ | O(n) via hub-spoke |

## Phase 3: Verify Fix

1. Count elements: `d3.selectAll('.node').size()` and `d3.selectAll('.edge').size()`
2. Screenshot file size: <10KB = blank/empty, >50KB = content
3. Memory: task manager should show <300MB for graph page

## Phase 4: Replace Force Simulation with Static Layout

When D3 force simulation is causing O(n²) or tick thrash issues even after edge optimization, **pre-compute node positions statically and use D3 only for zoom/pan/tooltips**.

**Signal:** After fixing edges, simulation still causes 3-5GB RAM or page hang at 2000+ nodes.

**Approach — Static Radial Layout:**
```
1. Pre-compute all node (x,y) positions in JS at page load (just math — no physics)
2. D3 simulation = null; use D3 only for:
   - SVG element creation/update
   - Zoom/pan behavior (d3.zoom)
   - Drag (move is disabled — positions are static)
   - Tooltip positioning
   - Transitions on filter/search
3. render() positions nodes via transform, not physics — instant
4. Node positions computed once at load (<100ms for 4000 nodes)
```

**Stratified Sampling for Large Datasets (4000+ nodes):**
```javascript
function stratifiedSample(skills, maxTotal = 600) {
  const byCat = {};
  skills.forEach(s => { (byCat[s.category] = byCat[s.category] || []).push(s); });
  const total = skills.length;
  const sampled = [];
  Object.entries(byCat).forEach(([cat, catSkills]) => {
    // Proportional quota capped at 20 per category
    const quota = Math.min(20, Math.max(3, Math.ceil(catSkills.length / total * maxTotal * 1.5)));
    catSkills.sort((a, b) => b.tags.length - a.tags.length || a.name.localeCompare(b.name));
    sampled.push(...catSkills.slice(0, quota));
  });
  return sampled;
}
```

**Radial Layout Algorithm:**
```javascript
function layoutNodes(sampledSkills, W, H) {
  const cats = [...new Set(sampledSkills.map(s => s.category))].sort();
  const nCats = cats.length;
  const CX = W / 2, CY = H / 2;
  const OUTER_R = Math.min(W, H) * 0.42;
  const INNER_R = OUTER_R * 0.28;
  const catAngle = {};
  cats.forEach((cat, i) => { catAngle[cat] = (i / nCats) * 2 * Math.PI - Math.PI; });

  const byCat = {};
  sampledSkills.forEach(s => { (byCat[s.category] = byCat[s.category] || []).push(s); });

  const positioned = [];
  cats.forEach((cat, i) => {
    const catSkills = byCat[cat];
    const startAngle = catAngle[cat];
    const endAngle = catAngle[cats[(i + 1) % nCats]] ?? startAngle + (2 * Math.PI / nCats);
    const span = endAngle - startAngle;
    // Hub at wedge center
    const hubAngle = startAngle + span / 2;
    positioned.push({ id: '__hub__' + cat, name: cat, category: cat,
      x: CX + INNER_R * Math.cos(hubAngle), y: CY + INNER_R * Math.sin(hubAngle), displayR: 18, isHub: true });
    // Skills in ring within wedge
    const ringR = OUTER_R * 0.78;
    catSkills.forEach((skill, i) => {
      const t = catSkills.length === 1 ? 0.5 : i / (catSkills.length - 1);
      const angle = startAngle + t * span;
      const r = ringR + (i % 3) * 14 + (Math.random() - 0.5) * 8;
      skill.x = CX + r * Math.cos(angle);
      skill.y = CY + r * Math.sin(angle);
      skill.displayR = 5;
      positioned.push(skill);
    });
  });
  return positioned;
}
```

## Pitfalls

- **Don't scale-test with toy data**: A graph that works with 100 nodes can have O(n²) edges that only manifest at 4000+. Test at production scale.
- **Default state IS architecture**: A checkbox default ON created 7.7M edges without any user action. Defaults determine the failure mode, not just the UI.
- **Don't forget the final render**: Throttle ticks but never call `render()` on settle → graph renders at intermediate (wrong) positions. Always add `simulation.on('end', () => render())`.
- **Circle count is the litmus test**: After load, check `d3.selectAll('circle').size()` — 0 means SVG was never populated.
- **SSH heredoc/shell escaping**: When passing Python scripts via SSH, write the script to a local file first, then `ssh host "cat > /tmp/script.py" < script.py && python3 /tmp/script.py`. Using `ssh host "python3 -c '...complex code...'"` hits shell quote escaping limits. Node.js inline `node -e` has the same problem; write to file first.
- **Playwright timeout on headless Chrome**: Full Chrome browser (google-chrome-stable) requires a display server and hangs in headless mode on some Linux setups. Use `timeout N` wrapper and check process exit, not just stdout.

## Support Files

- `references/deployment-verification.md` — Playwright test scripts, skill data extraction recipes, HTML merge patterns, and known failure signatures.
- `references/edge-curation-patterns.md` — Original May 2025 patterns and JSON schema traps.
- `references/edge-curation-refined.md` — Refined June 2025 taxonomy: edge type table (member-of, workflow-peer, quality-hub, tool-use), quality score formula, filter toggle behavior, and revised limits.
