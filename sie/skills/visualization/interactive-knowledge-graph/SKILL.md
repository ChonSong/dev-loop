---
name: interactive-knowledge-graph
description: "Build interactive force-directed graph visualizations with the force-graph library — data ingestion, performance tuning, interactive controls, and deployment"
version: 1.0.1
author: Hermes
tags: [visualization, graph, force-graph, d3, javascript, html, github-pages]
related_skills: [graph-layout-patterns, force-graph-visualization]
---

# Interactive Knowledge Graph

Build a responsive, interactive force-directed graph visualization. Covers data modeling, force-graph library configuration, interactive controls, performance optimization, and headless screenshot verification.

## When to use

- Visualizing relationships between entities (skills, packages, concepts, people)
- Building an interactive graph for a website (GitHub Pages, static hosting)
- User wants density controls (spread sliders, namespace filters, edge type toggles)

**For static layout algorithms** (Vogel spiral packing, per-cluster FR, sub-clustering dominant namespaces, zone background overlays) → see `graph-layout-patterns` in software-development/. That skill is the layout-algorithm complement to this library/UX one.

**For deep force-graph library API coverage** (per-edge color, charge/link forces, `onEngineStop` zoomToFit timing, headless Chrome debugging, async data loading) → see `force-graph-visualization` in software-development/.

## References

- `references/force-graph-config.md` — force-graph library API reference and performance tuning
- `references/data-pipeline.md` — data ingestion, node/edge modeling, namespace coloring

## Quick start

### 1. Data structure

Graph data format (JSON):

```json
{
  "nodes": [
    {
      "id": "skill-name",
      "name": "display name",
      "qualified_name": "namespace/skill-name",
      "namespace": "category",
      "color": 123456,
      "complexity": "high|medium|low",
      "role": "worker|creator|analyzer",
      "verified": true,
      "quality": 7.5,
      "steps": 10,
      "examples": 5,
      "pitfalls": 3,
      "lines": 200,
      "size": 15,
      "desc": "Description text",
      "author": "",
      "version": "",
      "tools": [],
      "tags": ["tag1", "tag2"],
      "dependencies": []
    }
  ],
  "edges": [
    { "src": "nodeA", "tgt": "nodeB", "type": "member-of", "label": "namespace" },
    { "src": "nodeA", "tgt": "nodeB", "type": "workflow-peer", "label": "role" }
  ],
  "ns_colors": { "namespace": 123456 },
  "edge_types": [
    ["edge-type", "Display Label", 0xHEXCOLOR, 0.5],
    ["member-of", "Same namespace", 0x0A798C, 0.3],
    ["workflow-peer", "Workflow role", 0x3BBA2D, 0.8]
  ],
  "edge_filter_default": { "member-of": true, "workflow-peer": true },
  "namespace_order": ["alpha", "sorted"]
}
```

### 2. Edge patterns

| Pattern | Description | Best for |
|---------|-------------|----------|
| **Hub-and-spoke** | One hub node connects to all others in group | Large groups (>30 nodes) — manageable edge count |
| **Complete subgraph** | Every node connects to every other | Small groups (<15 nodes) — shows full connectivity |
| **Tag-based** | Nodes sharing N+ tags get edges | Cross-cutting semantic connections |
| **Role-based** | Nodes with same role get edges | Workflow/career-path visualization |

For graphs >200 nodes, use hub-and-spoke for all groups to keep the force simulation fast.

### 3. Interactive controls to add

| Control | Implementation | Purpose |
|---------|---------------|---------|
| **Edge type filter buttons** | Filter `filteredEdges()` by `activeTypes` Set | Show/hide edge categories |
| **Namespace toggle** | Clickable legend rows toggling `activeNamespaces` Set | Show/hide entire groups |
| **Spread slider** | `graph.d3Force('charge').strength(-val)` | Node repulsion control |
| **Link distance slider** | `graph.d3Force('link').distance(val)` | Edge stretch control |
| **Size by dropdown** | `graph.nodeVal(nodeSizeFn)` with dynamic field | Visual emphasis by metric |
| **Search** | `graph.nodeColor()` dims non-matching nodes | Find specific nodes |
| **Quality threshold** | Filter `nodes.filter(n => n.quality >= minQ)` | Reduce visual clutter |

### 4. Force-graph config for different scales

```javascript
// < 100 nodes — snappy defaults
.d3AlphaDecay(0.02)
.d3VelocityDecay(0.4)

// 100-500 nodes — warmup for faster settle
.d3AlphaDecay(0.03)
.d3VelocityDecay(0.3)
.warmupTicks(200)
.cooldownTicks(50)
.backgroundColor('#0d0d14')

// > 500 nodes — aggressive performance
.d3AlphaDecay(0.05)
.d3VelocityDecay(0.2)
.warmupTicks(100)
.cooldownTicks(30)
// Consider async data loading to avoid blocking HTML parse
```

### 5. HTML size management

- **Inline data**: Good for <200 nodes (<150KB HTML). Simple, no extra HTTP request.
- **Async fetch**: Load `graph_data.json` via `fetch()`. Required for >500 nodes. Wrap init in async IIFE.
- **HTML size target**: Keep under 200KB for responsive page load.

```javascript
// Async fetch pattern
const _main = async () => {
  const r = await fetch('graph_data.json');
  const data = await r.json();
  const { nodes, edges, ... } = data;
  // ... rest of init
};
_main();
```

### 6. Debugging headless screenshots

Chrome headless `--screenshot` may fail on JS-heavy pages:

```bash
# Add --dump-dom to force full rendering before screenshot
google-chrome-stable --headless --disable-gpu --dump-dom --screenshot=/tmp/output.png --window-size=1600,900 https://example.com

# For pages with async data, use --virtual-time-budget
google-chrome-stable --headless --disable-gpu --virtual-time-budget=15000 --screenshot=/tmp/output.png --window-size=1600,900 https://example.com
```

### 7. "Graph is missing" diagnostic (overlays, sibling elements, JS throws)

When a deployed graph that was working suddenly renders blank, check in this order:

1. **New HTML sibling element with `position: absolute`**: a canvas, SVG, or div added next to `#graph-container` (as a sibling, not child) can break the force-graph's own canvas, even with `pointer-events: none` and `z-index: 0`. Fix: make it a child of `#graph-container`, or use SVG with `graph.onZoom` for re-renders.
2. **JS error inside the `setTimeout` that calls `zoomToFit`**: a thrown error inside any callback (e.g., `graph2ScreenCoords(undefined)`, `onEngineTick` with `cooldownTicks(0)` not firing reliably) aborts the rest of init. Wrap each call in try/catch when uncertain.
3. **Inline GRAPH_DATA was corrupted by the build script**: read the deployed HTML, extract the JSON, parse it, check node/edge counts.
4. **Force-graph CDN version changed**: the CDN URL is pinned (`@1.43.5`) but new major versions break.

See `graph-layout-patterns` Pattern 4 (zone background pitfalls) for the canvas-overlay case in detail.

## Common pitfalls

- **TDZ (Temporal Dead Zone)**: `const` variables referenced before declaration cause ReferenceError. Move all `const` declarations to the top of the script.
- **read_file line numbers**: `read_file()` returns `LINE|CONTENT` format. Using this as source for patch/inject will bake line numbers into the file. Use `terminal("cat file")` for raw content.
- **zoomToFit timing**: Call `graph.zoomToFit()` inside `onEngineStop` callback, not immediately after construction. The force simulation needs to settle first.
- **Edge count explosion**: Complete subgraphs within large groups create O(n²) edges. Use hub-and-spoke pattern instead.
- **member-of default OFF**: For graphs >100 nodes, intra-group edges overwhelm the visualization. Default them OFF and let users toggle ON.
- **Force-graph CDN**: Pin the version (`force-graph@1.43.5`) to avoid breaking changes.
- **Canvas/SVG overlay breaks force-graph canvas**: a passive overlay with `position: absolute; pointer-events: none; z-index: 0` placed as a SIBLING of `#graph-container` can cause the graph to stop rendering. Make it a child of `#graph-container` instead. (See "Graph is missing" diagnostic above and `graph-layout-patterns` Pattern 4.)
- **Always visually verify post-deploy**: JS validity ≠ visual correctness. If you can't take a screenshot in the container, the user will. The "graph is missing" failure mode is silent — no console error, no Network failure, just a blank canvas. Catch it before the user does.
