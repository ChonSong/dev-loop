# Force-Graph Patterns

Common patterns, pitfalls, and fixes for the [force-graph](https://github.com/vasturiano/force-graph) library (version 1.43.x).

## Initialization

```js
// Modern API (1.43+)
const graph = ForceGraph()(containerElement)
  .graphData({ nodes, links })
  .nodeId('id')
  .nodeVal('size')
  .nodeColor(n => `#${n.color.toString(16).padStart(6,'0')}`)
  .backgroundColor('#0d0d14');
```

**Watch out**: the API changed across versions. `ForceGraph()(el)` (curried) vs `new ForceGraph(el)` (constructor) — check the CDN version.

## Per-Edge Colors & Widths

The most common bug: computing per-edge colors/widths in the data array but then hardcoding them in the chain:

```js
// ❌ WRONG — all edges same color and width
.graphData({ nodes, links: gEdges })  // gEdges has .color and .width per edge
.linkColor(() => '#2a2a3a')
.linkWidth(1.5)

// ✅ CORRECT — use per-edge values
.linkColor(link => link.color || '#555')
.linkWidth(link => link.width || 1)
```

Build the edge array with computed values:
```js
const gEdges = edges.map(e => ({
  source: e.src,
  target: e.tgt,
  color: edgeColorFor(e.type),
  width: edgeWidthFor(e.type),
}));
```

Edge type definitions usually include a width field:
```js
edge_types: [
  ["member-of", "Same namespace", 0xDFA6A, 0.4],  // thin
  ["workflow-peer", "Same role", 0x3BBA2D, 1.0],
  ["quality-hub", "Quality hub", 0x6010C6, 1.2],   // thick
]
```

## zoomToFit Timing (Critical)

**NEVER** call `zoomToFit` immediately after `.graphData()`. At that point all nodes are at their initial positions (clustered at center), so zoomToFit captures a tiny bounding box, then the simulation spreads nodes off-screen.

```js
// ❌ WRONG — nodes end up off-screen
graph.graphData({ nodes, links });
graph.zoomToFit(400, 60);

// ✅ CORRECT — wait for simulation to settle
let graphInitialized = false;
// ... chain ...
.onEngineStop(() => {
  if (!graphInitialized) {
    graphInitialized = true;
    graph.zoomToFit(400, 120);
  }
});
```

Use the `graphInitialized` flag to ensure zoomToFit only runs on first load, not on every `onEngineStop` (which fires multiple times).

## Updating Graph Data (Filter Changes)

When toggling edge filters, update data and reheat the simulation:

```js
// On filter change:
graph.graphData({ nodes, links: gEdges });
graph.d3ReheatSimulation();  // needed to re-layout
```

Note: on filter updates, node positions are preserved. Only the edge set changes. This avoids jarring re-layouts.

## Edge Filter Defaults

For graphs with dense "member-of" edges (complete subgraphs per namespace), choose defaults carefully:

- **member-of ON**: nodes cluster by namespace, graph looks connected but dense
- **member-of OFF**: nodes appear disconnected/sparse
- **Recommendation**: ON for first-visit, with toggle buttons for power users

Default toggle pattern:
```js
const activeTypes = new Set(
  Object.keys(edge_filter_default).filter(k => edge_filter_default[k])
);
```

## Adding Search

Highlight matching nodes, dim the rest:

```js
function applySearch() {
  const q = searchQuery.toLowerCase().trim();
  if (!q) {
    graph.nodeColor(n => `#${n.color.toString(16).padStart(6,'0')}`);
  } else {
    graph.nodeColor(n => {
      const match = n.name.toLowerCase().includes(q);
      return match ? `#${n.color.toString(16).padStart(6,'0')}` : '#222236';
    });
  }
}
```

## Node Canvas

Draw custom decorations after force-graph's built-in rendering:

```js
.nodeCanvasObjectMode(() => 'after')
.nodeCanvasObject((node, ctx) => {
  if (node.verified) {
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.size + 2.5, 0, 2 * Math.PI);
    ctx.strokeStyle = '#4ecb71';
    ctx.lineWidth = 1.2;
    ctx.stroke();
  }
});
```

## Large Graph Performance (500+ nodes)

For graphs with hundreds or thousands of nodes, add these to speed simulation settle:

```js
.d3AlphaDecay(0.03)      // faster energy dissipation (default 0.02)
.d3VelocityDecay(0.3)    // less momentum/oscillation (default 0.4)
.warmupTicks(200)        // pre-compute positions before first render
.cooldownTicks(50)       // stop simulation early when mostly settled
```

### Edge density control

Complete subgraphs (every node connected to every other in same namespace) grow at `O(n²)`:
- 10 nodes → 45 edges
- 50 nodes → 1,225 edges
- 200 nodes → 19,900 edges

For large namespaces, use **hub-and-spoke** instead:

```js
// Instead of: for i in ids: for j in ids[i+1:]: edges.push({...})
// Use:
const hub = ids[0];
for (const nid of ids.slice(1)) {
  edges.push({ src: hub, tgt: nid, type: "member-of", label: ns });
}
```

This reduces `O(n²)` to `O(n)` while still connecting all nodes visually. The force layout naturally clusters the spokes around the hub.

### Other large-graph tips

- Remove or simplify `nodeCanvasObject` callbacks — drawing arcs per node every frame is expensive at 1000+
- Consider hiding node labels by default (set `.nodeLabel(null)`), show on hover via custom hover handler
- Pre-filter on initial load — show a subset of namespaces, let user expand
- Avoid `linkDirectionalParticles > 0` — particle animation is frame-expensive with many edges

## Common Color Bug

`ns_colors` values are decimal integers. Convert correctly:

```js
// Always use padStart(6, '0') to get a full 6-char hex
`#${n.color.toString(16).padStart(6,'0')}`

// Demo: 686476 → 0xA798C → "#0A798C"
```
