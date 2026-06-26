# force-graph API Quirks & Reference

## Per-edge color/width — MUST use function, not constant

The `linkColor()` and `linkWidth()` setters accept either a constant value OR a function. When you pass a constant, ALL links get that value regardless of per-edge properties set in the data.

```javascript
// ❌ BROKEN — all edges gray
.linkColor(() => '#2a2a3a')
.linkWidth(1.5)

// ✅ WORKS — reads per-edge color/width
.linkColor(link => link.color || '#555')
.linkWidth(link => link.width || 1)
```

The `gEdges` mapping must compute per-edge values:

```javascript
const gEdges = fEdges.map(e => ({
  source: e.src,
  target: e.tgt,
  color: edgeColorFor(e.type),   // function returning hex string
  width: edgeWidthFor(e.type),   // function returning number
}));
```

## zoomToFit timing

The initial node positions are randomized by the force simulation. Calling `zoomToFit()` immediately after `graphData()` captures the bounding box of nodes still clustered at center, producing a very close zoom. Then the simulation spreads nodes off-screen.

**Fix:** Call `zoomToFit()` from `onEngineStop` with a guard flag:

```javascript
let graphInitialized = false;

graph = ForceGraph()(container)
  .graphData({ nodes, links: gEdges })
  // ...
  .onEngineStop(() => {
    if (!graphInitialized && graph) {
      graphInitialized = true;
      graph.zoomToFit(400, 120);  // 120px padding so nodes don't touch edges
    }
  });
```

## graphData update on filter change

When `graph.graphData({ nodes, links: gEdges })` is called on an existing graph, the simulation pauses. Call `d3ReheatSimulation()` to restart it:

```javascript
if (graph) {
  graph.graphData({ nodes, links: gEdges });
  graph.d3ReheatSimulation();  // required after every .graphData() call
  return;
}
```

## Decimal-to-hex color conversion

force-graph expects hex color strings. If your data stores colors as decimal integers:

```javascript
// Integer → hex string
`#${colorInt.toString(16).padStart(6, '0')}`
```

Example: `686476` → `#0A798C`, `916074` → `#0DFA6A`

For edge type colors stored in arrays: `edge_types[i][2]` is the color int, `edge_types[i][3]` is the width.

## Large graph tuning

| Setting | Default | Large graph (500+) |
|---------|---------|-------------------|
| `d3AlphaDecay` | 0.02 | 0.03 (faster settle) |
| `d3VelocityDecay` | 0.4 | 0.3 (less oscillation) |
| `warmupTicks` | 0 | 200 (pre-compute) |
| `cooldownTicks` | Infinity | 50 (stop early) |

## Edge data structure

```javascript
edge_types = [
  ["member-of",    "Same namespace", 0x0A798C, 0.3],   // [type, label, color, width]
  ["workflow-peer","Same role",      0x3BBA2D, 0.8],
  ["quality-hub",  "Quality hub",    0x6010C6, 1.2],
  ["tool-use",     "Shared tools",   0x2ECC71, 0.6],
]
```

## Known limitations

- force-graph@1.43.5 does NOT support arrow-heads on edges natively (requires `linkDirectionalArrowLength` config)
- `nodeCanvasObject` runs every frame for all visible nodes — skip expensive drawing on 1000+ node graphs
- No built-in label collision detection; labels overlap in dense clusters
