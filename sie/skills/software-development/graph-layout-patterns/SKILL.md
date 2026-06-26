---
name: graph-layout-patterns
description: Use when laying out force-directed graphs (or any clustered point cloud) on a 2D canvas — covers Vogel spiral packing, per-cluster Fruchterman-Reingold, namespace zone backgrounds, and when to sub-cluster a dominant group. Apply for any static-layout graph with >100 nodes, vendor-imported data with one dominant namespace, or a GitHub-Pages single-file visualization that needs clean clustering without runtime cost.
---

# Graph Layout Patterns

Reusable techniques for laying out clustered point clouds in 2D, especially for static-layout single-file visualizations (GitHub Pages, offline HTML, server-rendered).

## When to use

- Force-directed graph with >100 nodes
- Data dominated by one category (>40% of nodes)
- Need static pre-computed positions (no runtime simulation)
- Want visible clusters / grouping, not a single amorphous blob
- Single-file deployment (no Python back-end)

## Pattern 1: Vogel spiral packing (deterministic, fast, perfect containment)

Use for **initial placement** of nodes within a cluster zone. Predictable, no iterations, O(n).

```python
import math

def sunflower_positions(n, radius):
    """Vogel's sunflower spiral — uniform point distribution in a disk."""
    if n == 0: return []
    if n == 1: return [(0, 0)]
    c = radius / math.sqrt(n) * 0.95  # 0.95 prevents outermost point overshooting
    golden_angle = math.pi * (3 - math.sqrt(5))  # ~2.399 rad
    pts = []
    for i in range(1, n + 1):
        r = c * math.sqrt(i)
        theta = i * golden_angle
        pts.append((r * math.cos(theta), r * math.sin(theta)))
    return pts
```

**Why it works:** Vogel's spiral is the most uniform non-lattice point distribution in 2D. For a disk of radius R containing n points, set c ≈ R/√n so the outermost point lands at ~R.

**Pitfall:** Without the 0.95 multiplier, the n-th point overshoots R. With it, the n-th point is at ~0.95R (still well inside).

**Pitfall:** For n > 200 the inner points get crowded. Combine with a charge-repulsion pass after.

## Pattern 2: Per-cluster Fruchterman-Reingold (O(n²) globally → O(n²) per cluster)

Global FR is O(N²) per iteration. For 800+ nodes, that's hundreds of millions of operations. **Split by cluster first**, then run FR on each cluster independently. Each cluster is small (often 5-100), so total work is dramatically less.

```python
def per_cluster_layout(cluster_nodes, cluster_center, cluster_radius, iterations=80):
    """Run FR within one cluster, with strong gravity to keep it centered."""
    n = len(cluster_nodes)
    pos = [random_in_disk(cluster_nodes, cluster_center, cluster_radius * 0.7)
           for _ in cluster_nodes]
    area = math.pi * cluster_radius ** 2
    k = math.sqrt(area / max(n, 1)) * 0.55  # optimal distance
    k2 = k * k
    temp = cluster_radius * 0.15
    for it in range(iterations):
        # Repulsive (O(n²) — fine because n is small per cluster)
        for i in range(n):
            for j in range(i+1, n):
                dx, dy = pos[i][0]-pos[j][0], pos[i][1]-pos[j][1]
                d = math.hypot(dx, dy) + 0.01
                f = k2 / d
                vel[i][0] += f * dx/d; vel[i][1] += f * dy/d
                vel[j][0] -= f * dx/d; vel[j][1] -= f * dy/d
        # Attractive along within-cluster edges only
        # ...
        # Strong gravity toward cluster center
        for i in range(n):
            vel[i][0] += (cluster_center[0] - pos[i][0]) * 0.12
            vel[i][1] += (cluster_center[1] - pos[i][1]) * 0.12
        # Apply with cooling
        cool = temp * (1 - it / iterations)
        # ... standard apply step
```

**Why split:** 1 global run of 800 nodes × 100 iter = 64M ops. 8 clusters of 100 nodes × 80 iter = 3.2M ops. **20× faster** and converges better per cluster.

**Pitfall:** Make sure `iterations` scales with cluster size. Big clusters (>100) need 60-80 iters with `k * 0.55`. Small clusters (<10) need only 15-20 iters with `k = 40` hardcoded.

**Pitfall:** When `iterations` is too low, nodes clump on the center. When too high, charge overcomes gravity and nodes fly out. Tune `gravity` (0.05-0.15) and `temp` (15-30) together.

**Pitfall:** Per-cluster FR often gives WORSE results than Vogel packing for static layouts. Charge overcomes gravity, "donut" effects, and nodes drift from target center. **Default to Vogel packing for static layouts**; only use per-cluster FR if you have attractive edges within a cluster that Vogel can't represent.

## Pattern 3: Sub-cluster by secondary identifier when one namespace dominates

If one category has >40% of nodes, sub-group by a secondary key (author, source, tag) BEFORE laying out.

```python
def cluster_key(node, dominant_ns='voltagent'):
    ns = node['namespace']
    if ns == dominant_ns:
        # Sub-group by author prefix
        name = node.get('name', '')
        prefix = name.split('/')[0] if '/' in name else '_other'
        return f'{ns}/{prefix}'
    return ns
```

**Example result:** voltagent (678 nodes) → 120 distinct sub-clusters (NVIDIA, microsoft, anthropics, etc.). The previously-amorphous blob becomes a ring of 8 large sub-clusters + 36 medium + 94 small.

**Pitfall:** Don't sub-cluster if the secondary key is uniform (e.g., "voltagent" prefix for all voltagent nodes). Then sub-clustering produces one mega-cluster, not many.

## Pattern 4: Zone background ellipses via overlay canvas

Static graphs benefit from visible zone boundaries. Render on a separate `<canvas>` positioned behind the main graph, with `pointer-events: none` so it doesn't block interaction.

```html
<canvas id="zone-layer"></canvas>
<div id="graph-container">...</div>
```

```css
#zone-layer {
  position: absolute; top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none; z-index: 0;
}
#graph-container canvas:not(#zone-layer) { z-index: 1; }
```

```js
function drawZone(cluster) {
  const [cx, cy] = cluster.center;
  const screen = graph.graph2ScreenCoords(cx, cy);  // force-graph helper
  const screenR = cluster.radius * graph.zoom();
  // Cull off-screen: skip if rect is outside viewport
  if (screen.x + screenR < 0 || screen.x - screenR > w) return;
  // Draw filled ellipse at low alpha, stroke at higher alpha, label below
  ctx.globalAlpha = 0.07; ctx.fillStyle = cluster.color;
  ctx.beginPath(); ctx.arc(screen.x, screen.y, screenR, 0, 2*Math.PI); ctx.fill();
  ctx.globalAlpha = 0.25; ctx.strokeStyle = cluster.color; ctx.stroke();
  ctx.globalAlpha = 0.6; ctx.fillText(cluster.label, screen.x, screen.y + screenR + 4);
}
graph.onZoom(() => redrawZones());
graph.onEngineTick(() => redrawZones());  // redraws on pan
```

**Pitfall:** Don't put zones on the main graph canvas via `nodeCanvasObjectMode('before')` — this redraws 821 times per frame. Use a separate canvas with `requestAnimationFrame` coalescing.

**Pitfall:** Use `graph.graph2ScreenCoords()` to convert data coords → screen coords. Multiply radius by `graph.zoom()` so zones scale correctly with zoom.

**Pitfall (CRITICAL — graph can disappear):** A separate `<canvas id="zone-layer">` overlay placed as a SIBLING of `#graph-container` (child of the same parent) can cause the force-graph canvas to NOT RENDER, even with `position: absolute; pointer-events: none; z-index: 0`. Symptoms: the graph was working, you added the canvas overlay + `drawZones()` JS, and now the entire graph is missing (blank canvas, no console error). The mechanism is fragile — it can be the sibling canvas stealing layout space from the force-graph's dynamically-created canvas, the JS throwing inside `graph2ScreenCoords()` or `onEngineTick` (with `cooldownTicks(0)` this never fires reliably, so any thrown error blocks the rest of init), or z-index stacking with the force-graph's own canvas. **Safer alternatives:** (a) put the zone canvas INSIDE `#graph-container` as the first child with `z-index: 0` and let the force-graph canvas be `z-index: 1`, (b) prefer SVG `<g>` overlay synced via `graph.onZoom` (more predictable DOM ordering than two canvases), or (c) skip zone backgrounds entirely — Vogel packing already produces visible clusters from position alone. **Always verify post-deploy that the graph actually renders** (not just that the JS is syntactically valid). If user reports "the graph is missing now" after you added an overlay, suspect this first.

## Pattern 5: Static layout for GitHub Pages

GitHub Pages serves static files only. Pre-compute positions, freeze the simulation, ship the JSON inline.

```js
const GRAPH_DATA = { nodes: [...], edges: [...], ns_colors: {...}, ... };
graph = ForceGraph()(container)
  .d3AlphaDecay(1)        // max decay
  .d3VelocityDecay(1)     // max velocity damping
  .warmupTicks(0)         // no warmup
  .cooldownTicks(0)       // no cooldown
  .graphData({ nodes, links });
// One-time zoom-to-fit after canvas has size
setTimeout(() => graph.zoomToFit(400, 120), 100);
```

**Pitfall:** With simulation disabled, nodes use their pre-set `x, y`. The graph must be initialized with these positions already populated. Position drift on zoom/pan is normal — it doesn't recompute, it just transforms.

**Pitfall:** For very large inline JSON (>500KB), the initial render blocks the main thread. Wrap initial graph-data load in `requestIdleCallback` or just accept the brief freeze.

## Pattern 6: Edge filter init order

When building filter buttons from a dynamic types list, **add synthetic types (tag-shared, computed edges) BEFORE the button-builder loop runs**. Otherwise those types never get a button.

```js
// WRONG: TAG_SHARED added after filter button loop
edge_types.forEach(([type, label, color]) => buildFilterButton(type));
const TAG_SHARED = 'tag-shared';
GRAPH_DATA.edge_types.push([TAG_SHARED, '...', 0xF39C12, 0.5]);

// RIGHT: add first, then build
const TAG_SHARED = 'tag-shared';
GRAPH_DATA.edge_types.push([TAG_SHARED, '...', 0xF39C12, 0.5]);
edge_types.forEach(([type, label, color]) => buildFilterButton(type));
```

**Pitfall:** Even with the right order, the filter button DEFAULT state is critical. If the synthetic edge type is added with `default: true` in `edge_filter_default`, the graph renders thousands of edges by default. See Pattern 7.

## Pattern 7: Disable high-fanout edge types by default

When an edge type is computed from shared attributes (tags, namespaces), it can explode to thousands of edges if any shared group is large.

**Diagnosis recipe:** before shipping, compute the edge count for each tag/namespace threshold:

```python
def estimate_tag_edges(nodes, threshold, max_size=100, cap=5000):
    from collections import Counter
    tag_counts = Counter()
    for n in nodes:
        for t in n.get('tags', []):
            tag_counts[t] += 1
    total = sum(c * (c - 1) // 2 for c in tag_counts.values()
                if threshold <= c <= max_size)
    return total, total > cap
```

**Real example:** 821 nodes, 678 share the "voltagent" tag → C(678,2) = 229,803 possible tag-shared edges. Even threshold=8 still produces ~2,742 edges because the cap (5000) is hit immediately. **The threshold parameter is irrelevant when one tag dominates.**

**Fix:** exclude namespace-level tags from the tag-shared computation, AND set `edge_filter_default[TAG_SHARED] = false` so it's off by default. User can enable with the filter button if they want a different view.

```python
edge_filter_default = {
    'member-of': True,
    'workflow-peer': True,
    'tag-shared': False,  # 5K+ edges, opt-in
}
```

## Verification

After layout, check:
1. Each cluster's `max(xs) - min(xs) <= cluster_radius * 2` (Vogel packing guarantee)
2. Each cluster's `drift = sqrt((mean_x - target_x)² + (mean_y - target_y)²)` < radius/2
3. `JSON.parse(GRAPH_DATA_string).nodes[0].x` is a finite number (not NaN)
4. `graph.zoomToFit(400, 120)` produces a viewport that includes all clusters
5. On small viewports, the medium-cluster ring (radius 1100) should still fit in 1920×1080
6. **For each edge type, count expected edges at default settings. If any type >1000, default it OFF.** (Pattern 7)
7. **Post-deploy, open the URL and confirm the graph RENDERS.** JS validity ≠ visual correctness. If user reports "graph is missing now" after a deploy, suspect: (a) a newly-added canvas/SVG overlay (Pattern 4 pitfall), (b) a JS error inside the setTimeout that calls `graph.zoomToFit`, (c) z-index stacking issue, (d) inline GRAPH_DATA truncated or malformed JSON.

## Files in this skill

- `references/vogel-spiral-formula.md` — exact math + visualization + Vogel+charge variant for n>200
- `templates/build_static.py` — full working example combining all 6 patterns

## Anti-patterns to avoid

- **Global FR on 800+ nodes** — O(N²) = 640K ops/iter × 100 iters = 64M. Way too slow in Python.
- **Forgetting to disable simulation for static layout** — `warmupTicks(0), cooldownTicks(0), d3AlphaDecay(1)` are all required. Any one missing = positions drift.
- **Curved edges on >1000 edges** — visually noisy. Either reduce edge count or use opacity < 0.3.
- **Drawing zone backgrounds on the main canvas** — 800 redraws per frame = laggy pan/zoom.
- **Putting the namespace legend in the same DOM element as the filter bar** — they have different UX (legend = always visible, filters = toggleable). Separate them.
- **Adding a high-fanout edge type with default=true** — a single tag shared by 600+ nodes produces 180K+ possible edges. Always default such types OFF.
- **Adding a canvas/SVG overlay without verifying the graph still renders** — overlays can silently break the main canvas. Always visually verify after the change.
- **Per-cluster FR when Vogel would do** — Vogel is deterministic, faster, and gives tighter containment. Only use FR if you need to represent attractive within-cluster edges.
