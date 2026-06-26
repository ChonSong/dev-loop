---
name: force-graph-visualization
description: Build interactive force-directed graph visualizations using the 3d-force-graph / force-graph library. Covers setup, data preparation, common API pitfalls, edge filtering, node interaction, and large-graph performance tuning.
version: 1.3.0
author: Hermes Agent (derived from knowledge-graph session)
tags: [visualization, graph, force-graph, d3, frontend, data-viz]
---

# Force-Graph Visualization

Build interactive, browser-based force-directed graphs from structured node/edge data using the [force-graph](https://github.com/vasturiano/force-graph) library (2D canvas-based, loaded from CDN).

## When to use

- You have structured node/edge data and want an interactive graph in the browser
- Building a knowledge graph, dependency graph, network map, or similar
- Need filtering by edge type, node search, click-to-inspect panels
- Target: single self-contained HTML file (no build step)

## Setup

Load from CDN in `<head>`:

```html
<script src="https://cdn.jsdelivr.net/npm/force-graph@1.43.5/dist/force-graph.min.js"></script>
```

The container element must have explicit dimensions (CSS `flex: 1; height: 100vh` or fixed px). The graph occupies a single `<div>` in the DOM.

## Core workflow

### 1. Data structure

Nodes array — each node is an object with at least `id`:

```javascript
const nodes = [
  { id: "skill-a", name: "Skill A", namespace: "tools", color: 0x3498db, size: 10, quality: 7.2, ... }
];
```

Edges array — each edge references node IDs:

```javascript
const edges = [
  { src: "skill-a", tgt: "skill-b", type: "member-of", label: "tools" },
];
```

### 2. Create the graph

```javascript
const container = document.getElementById('graph-container');
const graph = ForceGraph()(container)
  .graphData({ nodes, links: edges })
  .nodeId('id')
  .nodeLabel(n => `${n.name} (${n.namespace})`)
  .nodeVal('size')
  .nodeColor(n => `#${n.color.toString(16).padStart(6,'0')}`);
```

### 3. Edge coloring (⚠️ COMMON PITFALL)

Pre-compute per-edge colors in a map, then use a **function** for `linkColor`:

```javascript
// ✅ CORRECT: use function that reads per-edge color
.linkColor(link => link.color || '#555')

// ❌ WRONG: hardcoded constant — ALL edges render same color
.linkColor(() => '#2a2a3a')
```

Build the edges with per-edge color/width:

```javascript
const gEdges = edges.map(e => ({
  source: e.src,
  target: e.tgt,
  color: edgeColorFor(e.type),
  width: edgeWidthFor(e.type),
}));
```

### 4. Edge filtering with toggle buttons

```javascript
const activeTypes = new Set(['workflow-peer', 'quality-hub']);

function filteredEdges() {
  return edges.filter(e => activeTypes.has(e.type));
}

function rebuildGraph() {
  const fEdges = filteredEdges();
  const gEdges = fEdges.map(e => ({ source: e.src, target: e.tgt, color: edgeColorFor(e.type), width: edgeWidthFor(e.type) }));

  if (graph) {
    graph.graphData({ nodes, links: gEdges });
    graph.d3ReheatSimulation();  // ⚠️ required on filter change
    return;
  }
  // ...initial creation
}
```

Build filter buttons from `edge_types` array:

```javascript
edge_types.forEach(([type, label, color, width]) => {
  const btn = document.createElement('button');
  btn.dataset.type = type;
  btn.addEventListener('click', () => {
    if (activeTypes.has(type)) activeTypes.delete(type); else activeTypes.add(type);
    btn.classList.toggle('on');
    rebuildGraph();
  });
  filterBar.appendChild(btn);
});
```

### 5. Zoom-to-fit after simulation settles (⚠️ COMMON PITFALL)

Do NOT call `zoomToFit()` immediately after creating the graph — all nodes start at center, so it captures a tiny bounding box, then nodes spread off-screen.

✅ **CORRECT** — use `onEngineStop`:

```javascript
let graphInitialized = false;

graph = ForceGraph()(container)
  .graphData({ nodes, links: gEdges })
  // ...other config...
  .onEngineStop(() => {
    if (!graphInitialized && graph) {
      graphInitialized = true;
      graph.zoomToFit(400, 120);  // 400ms animation, 120px padding
    }
  });
```

### 6. Detail panel on node click

Slide-in sidebar pattern:

```css
#detail-panel {
  width: 320px;
  position: fixed; right: 0; top: 0;
  transform: translateX(100%);
  transition: transform 0.25s ease;
}
#detail-panel.visible { transform: translateX(0); }
```

```javascript
graph.onNodeClick(node => {
  document.getElementById('detail-panel').classList.add('visible');
  document.getElementById('detail-name').textContent = node.name;
  // ...populate fields...
});
graph.onBackgroundClick(() => {
  document.getElementById('detail-panel').classList.remove('visible');
});
```

### 7. Node search/highlight

```javascript
graph.nodeColor(n => {
  const match = n.name.toLowerCase().includes(query);
  return match ? `#${n.color.toString(16).padStart(6,'0')}` : '#222236';
});
```

### 8. Verified/quality badge on nodes

```javascript
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

### 13. Quality-based node filtering (MinQ slider)

For graphs with many low-quality or placeholder nodes (500+ total), add a minimum-quality slider that completely removes low-scoring nodes from the graph — not just dims them. This reduces both node count AND edge count (edges with one filtered endpoint are dropped), dramatically improving rendering performance while keeping the graph readable.

**Data requirement**: each node must have a `quality` field (numeric, e.g. 0–10).

**Add a range slider in the header:**

```html
<div class="header-control">
  <span>MinQ:</span>
  <input type="range" id="min-quality" min="0" max="10" value="0" step="0.5">
  <span class="range-val" id="minq-val">0.0</span>
</div>
```

**JS for the slider — triggers a full rebuild (not just visual update):**

```javascript
let minQuality = 0;

document.getElementById('min-quality').addEventListener('input', (e) => {
  minQuality = parseFloat(e.target.value);
  document.getElementById('minq-val').textContent = minQuality.toFixed(1);
  rebuildGraph();
});
```

**Integrate with rebuildGraph** — filter nodes by quality BEFORE the namespace filter, then drop edges whose endpoints are gone:

```javascript
function rebuildGraph() {
  // Filter by quality threshold FIRST
  const qFiltered = nodes.filter(n => n.quality >= minQuality);
  const qIds = new Set(qFiltered.map(n => n.id));

  // Then filter by active namespaces
  const visibleNodes = qFiltered.filter(n => activeNamespaces.has(n.namespace));
  const visibleIds = new Set(visibleNodes.map(n => n.id));

  // Drop edges where either endpoint was removed by quality OR namespace filter
  const fEdges = filteredEdges().filter(e => qIds.has(e.src) && qIds.has(e.tgt));
  const nsFiltered = fEdges.filter(e => visibleIds.has(e.src) && visibleIds.has(e.tgt));

  // ... rest of graph update ...
}
```

**Stats tip**: update the stats display to show the quality floor:

```javascript
function updateStats() {
  const qCount = minQuality > 0 ? nodes.filter(n => n.quality >= minQuality).length : nodes.length;
  stats.innerHTML = `<span>${qCount}</span> nodes (q≥${minQuality.toFixed(1)})`;
}
```

**Choosing a default threshold**: inspect the quality distribution of your data:
- If most nodes have quality 0–3 (auto-generated placeholders), a default of `0` shows everything but users can quickly slide to `4` to reveal only curated content.
- For 1500 nodes with a flat quality distribution, default `0` is fine — the slider lets users incrementally reduce complexity.

**Performance impact** (observed with 1500 nodes):
| MinQ | Visible nodes | Edge count | Render time |
|------|--------------|------------|-------------|
| 0 | 1500 | 2954 | ~15s to settle |
| 4 | ~900 | ~1300 | ~8s |
| 6 | ~600 | ~800 | ~4s |

## Large graph performance (500+ nodes)

Add these to the graph creation chain to speed up simulation:

```javascript
.d3AlphaDecay(0.03)      // faster energy dissipation
.d3VelocityDecay(0.3)    // less momentum = settles faster
.warmupTicks(200)        // pre-compute positions before render
.cooldownTicks(50)       // stop early when settled
```

For truly large graphs (1000+ nodes):
- Use hub-and-spoke edges instead of complete subgraphs: `O(n)` instead of `O(n²)`
- Remove `nodeCanvasObject` drawing for performance
- Consider paginating or namespace-filtering the initial view

## Edge data patterns

| Pattern | Use case | Edge count | Clumping risk |
|---------|----------|------------|--------------|
| Complete subgraph | Small groups (<30 nodes) | `O(n²)` — can explode | Low — forces spread out |
| Hub-and-spoke | Medium groups (30–200 nodes) | `O(n)` — all to one hub | High—all nodes pull toward single hub |
| Chain / spanning tree | Large groups (200+ nodes) | `O(n)` — A→B→C→D chain | Low — forces distributed along path |
| Star cluster | When one node is the "hub" | Same as hub-and-spoke | High if many leaf nodes |
| Tag-based | Nodes sharing common tags | Runtime-computed, capped | Depends on density |

### ⚠️ Hub-and-spoke clumping problem

For large namespaces (300+ nodes all in one group), hub-and-spoke creates a **single center of gravity** pulling every node toward one point. With 600+ nodes, the cluster is so dense it looks like one solid blob — individual nodes and edges are invisible, and the graph loses all readability.

**Root cause**: force-directed layout treats connections as springs. When 600 nodes all connect to one hub node, the hub's position is the equilibrium point for all springs. The resulting force is net-zero AT the hub, so all nodes settle there.

**Solution — chain (sparse tree) for large groups:**

```python
import random

# Large namespace: connect into a sparse chain instead of all-to-hub
random.seed(hash(namespace))
samples = random.sample(ids, min(20, len(ids)))
edges = []
for i in range(len(samples) - 1):
    edges.append({
        "src": samples[i],
        "tgt": samples[i+1],
        "type": "member-of",
        "label": namespace
    })
```

This creates a path where each node connects to exactly one or two neighbors. No single hub exists, so the force is distributed along the chain. Nodes form a loose trail instead of a dense ball.

**Thresholds:**

| Namespace size | Strategy | Why |
|---------------|----------|-----|
| 1–30 | Complete subgraph | Compact, readable, natural clustering |
| 30–200 | Hub-and-spoke | O(n) edges, moderate clumping |
| 200+ | Chain (20-sample) | Prevents visual blobbing |

The 20-sample limit on chains keeps edge count manageable regardless of namespace size. Increasing the sample size makes chains straighter (more structure) but uses more edges.

## Full feature set (complete knowledge graph page)

The reference template for a fully-featured knowledge graph page (based on session building the Hermes Skills Knowledge Graph at `chonsong/hermes-knowledge-graph`, commit `f72bed0`) includes:

| Feature | Implementation |
|---------|---------------|
| **Size-by dropdown** | Select `Quality`, `Steps`, `Examples`, `Lines`, `Size` — normalizes to 3–25px radius via `SIZE_RANGES` map |
| **Spread slider** | Range 10–300, controls `d3Force('charge').strength(-chargeV)`, live via `input` event |
| **Link distance slider** | Range 5–150, controls `d3Force('link').distance(linkDist)`, live via `input` event |
| **Edge filter toggle buttons** | Dynamically built from `edge_types` array; each button shows dot color + label + count. Active types in `activeTypes` Set |
| **Toggle All** button | Toggles all edge types on/off; syncs button DOM class with `activeTypes` Set |
| **Search/highlight** | Dims non-matching nodes to `#222236`; gold ring on matches via `nodeCanvasObject`; match counter ("3/15"); clear button appears when query is active |
| **Namespace sidebar** | Left sidebar (`#side`, 140px width) with clickable namespace rows. At-least-one guard prevents hiding the last namespace. `.lrow.on` class toggles visibility |
| **Edge type color legend** | Below namespace legend, shows each edge type with its color dot and label. **Interactive** — click to toggle edge type visibility, synced with filter buttons |
| **Rich detail panel (right slide-in)** | `position:fixed; right:0; transform:translateX(100%)` slide-in panel with ✕ close button. Shows: name, namespace/role, verified badge (green ring), complexity badge, quality score bar (threshold colors), meta grid (steps/examples/pitfalls/lines), author, version, tools list, tags list, description, connections list (sorted, hidden-by-default with toggle, clickable to navigate). Copy-qualified-name button |
| **Verified node ring** | `.nodeCanvasObject()` draws green stroke (`#4ecb71`) around verified nodes |
| **Tag-based edges (runtime)** | `computeTagEdges()` builds edges from shared tags with threshold slider (1–10). Cap at 15000 edges |
| **Node labels** | `name (namespace)` format for context |
| **Stats bar** | Shows "247/821 nodes · 512/1298 edges · Z/W ns" — filtered/total counts |
| **Empty state** | `<div id="empty-state">` shown when no node is selected: "Skills Knowledge Graph / Click a node to inspect details / Drag to pan · Scroll to zoom" |
| **Zoom-to-fit** |only on initial load from `zoomToFit(400, 120)`. Camera position preserved across filter changes. |
| **Charge/link defaults by graph size** | <100 nodes: Spread 60, Link 20; 100-500: 80-120/25-30; 500-1000: 150-200/30; 1000+: 200-250/30-40 |
| **MinQ slider** (optional) | Range 0–10, filters nodes by `quality` field before namespace filter. Drops edges whose endpoints were removed. Useful for 500+ node graphs with placeholder data |
| **Line opacity slider** | Range 0–100%, controls `graph.linkOpacity()` live. Persisted to localStorage. Reset by "Clear filters" |
| **Favicon** | Inline SVG data URI favicon (spiderweb emoji 🕸️) |
| **Chip filter persistence** | Chip filter state saved to/restored from localStorage |
| **Connections sorting** | Sorted: visible first → by type label → alphabetically by name |
| **Hidden connections toggle** | Hidden connections hidden by default in detail panel with "Show N hidden" toggle |
| **Mobile backdrop dismiss** | Semi-transparent backdrop overlay closes sidebar on tap |
| **Hover highlight cleared on drag** | `.onDrag()` handler clears hover state to prevent stuck highlighting |

### Data loading strategies

| Strategy | HTML size | Pros | Cons |
|----------|----------|------|------|
| **Inline** `<script>var D={...}` | Large (1.1MB+ for 800+ nodes) | Zero network fetches, simulation starts immediately | Slow initial parse; headless screenshot may timeout before render |
| **Sync data.js** `<script src="data.js">` in `<head>` | Small (~30KB) + 508KB data.js | Data cached separately, HTML loads fast | Blocks rendering until data.js parsed |
| **Async fetch** `fetch('data.json')` in init | Small (~30KB) + 508KB data.json | HTML loads first, data loads after | Headless VTB must cover fetch + simulation settle (20-30s) |
| **Hybrid** inline small data + fetch for large | Medium | Best of both for moderate sizes | Complex init logic |

For headless screenshot reliability, **inline data with `--virtual-time-budget=20000`** works best. The async fetch approach requires VTB=30000 and risks the simulation not settling before the timer expires.

**⚠️ Performance warning for large tag groups**: If a single tag appears on 100+ nodes (e.g., `"voltagent"` on 678 nodes), `computeTagEdges()` with a low threshold (2) enters an O(n²) inner loop — ~230K candidate pairs for a 678-node group. The 15000-cap prevents memory explosion, but the nested iteration itself can freeze the main thread for 2-5 seconds in headless Chrome. This causes `--virtual-time-budget` screenshots to capture a blank canvas because the timer expires during tag edge computation, before ForceGraph() is ever called.

**Mitigation**: Move tag edge computation after graph initialization, or use a higher default threshold (5+), or pre-compute tag edges in the build script and include them in the static `edges` array.

**Build a tag index:**

```javascript
const tagIndex = {};
nodes.forEach(n => {
  (n.tags || []).forEach(t => {
    if (!tagIndex[t]) tagIndex[t] = [];
    tagIndex[t].push(n.id);
  });
});
```

**Compute edges at runtime with threshold:**

```javascript
const TAG_SHARED = 'tag-shared';
let tagEdges = [];

function computeTagEdges(threshold) {
  const seen = new Set();
  const result = [];
  const groups = Object.values(tagIndex).filter(ids => ids.length >= threshold);

  for (const ids of groups) {
    if (result.length > 15000) break; // safety cap — forces can explode
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const key = ids[i] < ids[j] ? `${ids[i]}|${ids[j]}` : `${ids[j]}|${ids[i]}`;
        if (!seen.has(key)) {
          seen.add(key);
          result.push({ src: ids[i], tgt: ids[j], type: TAG_SHARED, label: `${threshold}+ tags` });
        }
      }
    }
  }
  return result;
}
```

**Integrate with filtering:**

```javascript
// Add tag-shared to edge_types so a filter button appears
edge_types.push([TAG_SHARED, 'Shared tags', 0xF39C12, 0.5]);

// In filteredEdges():
function filteredEdges() {
  let base = edges.filter(e => activeTypes.has(e.type));
  if (activeTypes.has(TAG_SHARED)) {
    base = base.concat(tagEdges);
  }
  return base;
}
```

**Threshold control HTML:**

```html
<div class="header-control">
  <span>Tag edge:</span>
  <input type="number" id="tag-threshold" min="1" max="10" value="2">
</div>
```

**Threshold change handler** — recompute edges and update the filter button count:

```javascript
document.getElementById('tag-threshold').addEventListener('change', (e) => {
  tagThreshold = Math.max(1, parseInt(e.target.value) || 2);
  tagEdges = computeTagEdges(tagThreshold);
  const tagBtn = document.querySelector('.filter-btn[data-type="tag-shared"] .count');
  if (tagBtn) tagBtn.textContent = tagEdges.length;
  rebuildGraph();
});
```

**Filter button creation** — must handle runtime-only edge types (those not in the static `edges` array):

```javascript
edge_types.forEach(([type, label, color]) => {
  const count = edges.filter(e => e.type === type).length;
  if (count === 0 && type !== TAG_SHARED) return; // ← allow tag-shared even without static edges
  // ...rest of button creation...
  const c = count > 0 ? count : tagEdges.length; // ← use dynamic count
});
```

**Registering new edge types at runtime** — when adding an edge type dynamically (like tag-shared) that isn't in the static GRAPH_DATA, you must:
1. Push to `edge_types` array for the filter button loop to pick it up
2. Set its default in `edge_filter_default`
3. **Add to `activeTypes` set** if the default is ON — otherwise the filter button class and initial edge visibility won't match:

```javascript
const TAG_SHARED = 'tag-shared';
edge_types.push([TAG_SHARED, 'Shared tags', 0xF39C12, 0.5]);
edge_filter_default[TAG_SHARED] = true;
activeTypes.add(TAG_SHARED);  // ← required! Otherwise button starts 'on' but edges don't show
```

Without `activeTypes.add()`, the filter button appears in "on" state (because `isOn = edge_filter_default[type]` is true) but `filteredEdges()` checks `activeTypes.has(type)` which doesn't include it. Result: button says ON but edges don't render.

### 10. Dynamic node sizing (size-by controls)

Let users choose what metric determines node size via a dropdown:

```javascript
// Available size fields and their expected ranges (for normalization)
const SIZE_RANGES = {
  quality: { min: 0, max: 10 },
  steps: { min: 0, max: 30 },
  examples: { min: 0, max: 20 },
  lines: { min: 0, max: 500 },
  size: { min: 0, max: 30 },
};

// Normalize any field to a renderable radius (3–25px)
function nodeSize(n) {
  const field = sizeField;
  const r = SIZE_RANGES[field] || { min: 0, max: 10 };
  const raw = n[field] || r.min;
  const range = (r.max - r.min) || 1;
  return 3 + (Math.max(0, Math.min(1, (raw - r.min) / range))) * 22;
}
```

**Use in graph creation:**

```javascript
graph = ForceGraph()(container)
  .nodeVal(nodeSize)  // ← function, not string
  // ...
```

**Dropdown HTML:**

```html
<div class="header-control">
  <span>Size:</span>
  <select id="size-by">
    <option value="quality">Quality</option>
    <option value="steps">Steps</option>
    <option value="examples">Examples</option>
    <option value="lines">Lines</option>
    <option value="size" selected>Size</option>
  </select>
</div>
```

**Change handler:**

```javascript
document.getElementById('size-by').addEventListener('change', (e) => {
  sizeField = e.target.value;
  graph.nodeVal(nodeSize);
  graph.d3ReheatSimulation();  // re-layout with new sizes
});
```

> **Note**: When changing `nodeVal` without changing graph data, call `graph.d3ReheatSimulation()` to re-run the layout with the updated node sizes. Without this, node sizes change but positions don't adapt.

### 11. Edge type color legend

Add a second legend section below the namespace color legend showing edge type meanings.

**HTML (add inside the legend div after namespace items):**
```html
<div id="legend">
  <h4>Namespaces</h4>
  <div id="legend-item"></div>
  <hr style="border:none;border-top:1px solid #1e1e2e;margin:8px 0">
  <h4 style="margin-bottom:6px">Edge Types</h4>
  <div id="legend-edges"></div>
</div>
```

**JS (populate from edge_types array):**
```javascript
const legendEdges = document.getElementById('legend-edges');
edge_types.forEach(([type, label, color]) => {
  const row = document.createElement('div');
  row.className = 'legend-row';
  row.style.opacity = '0.6';
  row.style.cursor = 'default';
  row.innerHTML = `<div class="dot" style="background:#${color.toString(16).padStart(6,'0')}"></div><span style="font-size:10px">${label}</span>`;
  legendEdges.appendChild(row);
});
```

### 12. Namespace toggles (click-to-filter)

Make legend rows clickable to show/hide entire namespaces.

**CSS for toggle state:**

```css
.legend-row { cursor: pointer; opacity: 0.5; transition: opacity 0.15s; }
.legend-row.on { opacity: 1; }
```

**JS with at-least-one guard:**

```javascript
let activeNamespaces = new Set(allNamespaces);

namespace_order.forEach(ns => {
  const row = document.createElement('div');
  row.className = 'legend-row on';
  row.innerHTML = `<div class="dot" style="background:#${color}"></div><span>${ns}</span>`;
  row.addEventListener('click', () => {
    if (activeNamespaces.has(ns)) {
      if (activeNamespaces.size <= 1) return; // keep at least one visible
      activeNamespaces.delete(ns);
      row.classList.remove('on');
    } else {
      activeNamespaces.add(ns);
      row.classList.add('on');
    }
    rebuildGraph();
  });
  legendItem.appendChild(row);
});
```

### 13. Force controls (spread & link distance sliders)

Add range sliders to let users control force-simulation parameters live.

**HTML (header controls):**

```html
<div class="header-control">
  <span>Spread:</span>
  <input type="range" id="charge-strength" min="10" max="300" value="80">
  <span class="range-val" id="charge-val">80</span>
</div>
<div class="header-control">
  <span>Link:</span>
  <input type="range" id="link-distance" min="5" max="150" value="30">
  <span class="range-val" id="link-val">30</span>
</div>
```

**JS handlers:**

```javascript
let chargeStrength = 80;
let linkDist = 30;

document.getElementById('charge-strength').addEventListener('input', (e) => {
  chargeStrength = parseInt(e.target.value);
  document.getElementById('charge-val').textContent = chargeStrength;
  if (graph) {
    graph.d3Force('charge').strength(-chargeStrength);
    graph.d3ReheatSimulation();
  }
});

document.getElementById('link-distance').addEventListener('input', (e) => {
  linkDist = parseInt(e.target.value);
  document.getElementById('link-val').textContent = linkDist;
  if (graph) {
    graph.d3Force('link').distance(linkDist);
    graph.d3ReheatSimulation();
  }
});
```

**Recommended defaults by graph size:**

| Node count | Spread | Link distance | Notes |
|------------|--------|--------------|-------|
| < 100 | 60 | 20 | Small groups — minimal repulsion needed |
| 100–500 | 80–120 | 25–30 | Moderate — start at 80, increase if dense |
| 500–1000 | 150–200 | 30 | Higher spread prevents overlapping clusters |
| 1000+ | 200–250 | 30–40 | Large graphs need strong repulsion to avoid a single blob |

**Important: sync JS default with HTML slider value.** The slider `<input value="X">` and the JS `var chargeV = X` must agree.

## Sidebar layout for namespace legend

When your graph has 10+ namespaces, use a flex layout with a dedicated sidebar sibling to `#main`:

```css
#side { width: 140px; background: #12121c; border-right: 1px solid #1e1e2e; flex-shrink: 0; overflow-y: auto; }
#main-wrap { display: flex; flex: 1; overflow: hidden; }
#main { flex: 1; overflow: hidden; position: relative; }
```

## Pitfalls

- **`graph.center()` does not exist.** Use `graph.screen2GraphCoords(w/2, h/2)` to get the current pan center for save/restore.

- **`ForceGraph()(container)` wipes the container's contents.** Sidebar, legend, empty-state, custom tooltip — all destroyed. **Fix**: nest the graph container as a sibling of sidebar/legend, not their parent.

- **Deferred tag edge computation for large groups.** O(n²) inner loop with 600+ nodes can freeze main thread for 2-5s. Mitigate with `setTimeout(initTagEdges, 2000)` or higher threshold.

- **Verifying inline data was rebuilt.** Always verify after rebuild by extracting the inline JSON and comparing node/edge counts against the source data file.

- **Member-of edges off by default looks broken.** Default ON with thin opacity.

- **Edge type mismatch: edges in data but not in edge_types definition.** Silent exclusion. Validate that every edge type in data has a corresponding entry in `edge_types`.

- **`const` / `let` temporal dead zone (TDZ).** Declare ALL `const`/`let` at the top of the script before any code that references them. Unlike `var`, neither is hoisted. If `tagEdges` is declared with `let` in a later section but referenced in an `edge_types.forEach(...)` loop at load time, the page crashes with `Cannot access 'tagEdges' before initialization`. Function bodies are safe — they execute when called, not when declared.

- **Inline data rebuild may silently fail.** If `html.replace('PLACEHOLDER=', new_data)` finds no placeholder, it's a no-op. Always verify after rebuild.

- **Filter button visual state diverging from activeTypes.** After modifying `activeTypes`, update each button's `.classList.toggle('on', activeTypes.has(btn.dataset.type))`.

- **Async IIFE for large data (500K+ inline JSON).** Move to separate `.json` file loaded via `fetch()` to avoid parser freezes.

- **Edge legend too dim.** `opacity: 0.6` dots on dark background are nearly invisible. Use line swatches (colored border-top) instead of dots for edge types. Raise opacity to `0.85`. Add borders to namespace dots. Use stronger background/shadow on legend container. Add node count badges per namespace.

- **No line opacity control.** Add a range slider that controls opacity via `getLinkColor()` returning `rgba(r,g,b,alpha)` — NOT via `graph.linkOpacity()` which does NOT exist in force-graph 1.43.5 (added in a later version). On slider input, call `graph.linkColor(getLinkColor)` to update in-place. Default 60%. Persist to localStorage.

- **Many small patches cause cascading failures.** When patching a large single-file HTML/JS page, each `patch` call shifts line numbers for all subsequent patches. String-based `old_string` matches then fail silently, leaving bugs half-fixed. **Fix**: for >5 changes, use a single Python script that loads the full file and does all replacements in memory, then writes once.

- **Filter chip selector/class mismatch.** If buttons use class `filter-chip` but JS queries `.chip`, buttons silently do nothing. Always verify the selector matches the actual HTML class. Use `data-filter`/`data-value` attributes as the filter key instead of `chip.id` (which may be empty).

- **"All" filter chip without no-op handler.** If `data-value="all"` but the filter function doesn't handle it, all nodes disappear. Make "all" clear the filter dimension or use a separate reset button.

- **Detail panel shows hidden connections.** Skip filtered-out edge types in the connections render loop, or add a "show hidden" toggle.

- **Hash deep-link race condition.** Wait for `graphInitialized` flag before calling `centerAt` from `handleHash()`. Use retry loop with `setTimeout(handleHash, 100)`.

- **Mobile sidebar: no backdrop dismiss.** Add a backdrop div (`#mobile-backdrop`) that closes sidebar on click.

- **Quality gradient bar misleading.** Use threshold-based colors (green ≥7, yellow ≥4, red <4) instead of a static rainbow.

- **Hover highlight stuck after drag.** Add `.onDrag()` handler that clears `hoveredNode = null` and hides tooltip. Without this, the dimmed/focused state persists after panning.

- **Camera resets on every filter change.** Don't call `zoomToFit` in `rebuildGraph`. Only zoom-to-fit on initial load. Preserve user's camera position across filter toggles.

- **Chip filters not persisted.** Include `chipFilters` in `saveState()` and restore in `restoreState()`.

- **Stats show total not filtered counts.** Pass `visibleNodes.length` and `gEdges.length` to `updateStats()`.

- **Search matches not highlighted.** Add gold ring via `nodeCanvasObject` for search matches. Add match counter ("3/15") near search input.

- **Connections list unsorted.** Sort by: visible first → by type label → alphabetically by name.

- **Edge legend not interactive.** Make legend rows clickable to toggle edge types, synced with filter buttons via `activeTypes` Set.

## Verifying canvas render in headless Chrome (PDF line-check)

```bash
google-chrome-stable --headless --disable-gpu \
  --print-to-pdf=/tmp/graph.pdf --window-size=1600,900 \
  https://chonsong.github.io/hermes-knowledge-graph/
```

```python
with open('/tmp/graph.pdf','rb') as f: d=f.read()
print(f"Line ops: {d.count(b' l ')}, Matrix ops: {d.count(b' cm ')}")
```

`cm` but zero `l` = canvas painted but nothing drawn. Both present = graph rendered.

## User preferences

- **Feature parity with old version**: Do NOT rebuild JS from scratch when making data changes. Diff old vs new before deploying.
- **Proactive old-version comparison**: When user says "this looks different", immediately diff. Don't ask "what's missing?"
- **Screenshots after every visual deploy.** If `--screenshot` produces blank canvases, use CDP or Xvfb.
- **Iteration tightness**: Prefer small targeted patches over full-page rewrites.

## References

- `references/force-graph-api-notes.md` — per-edge color/width, zoomToFit timing, graphData update patterns
- `references/canvas-render-debugging.md` — PDF line-check technique, `--virtual-time-budget` freeze diagnosis, CDP runtime debugging, GitHub Pages deployment debugging
- `references/data-pipeline.md` — scanning SKILL.md directories, extracting frontmatter, building hub-and-spoke edges, generating graph_data.json
- `references/structural-verification.md` — `curl | python3` structural validation for large graphs when headless Chrome cannot capture screenshots
- `references/inline-build-large-data.md` — building self-contained HTML by file-level concatenation to avoid MemoryError on 500KB+ inline data
- `references/cdp-screenshot-capture.md` — CDP-based screenshot capture for ForceGraph pages
- `references/feature-recovery-workflow.md` — restoring old features from git commits
- `references/tdz-and-patch-ordering.md` — TDZ errors, multi-patch cascading failures, verification checklist