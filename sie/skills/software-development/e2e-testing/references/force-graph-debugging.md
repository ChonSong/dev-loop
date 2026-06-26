# Force-Graph Initialization Debugging

Common errors when integrating `force-graph` library (vasturiano/force-graph).

## Error: `t.appendChild is not a function`

**Root cause:** The container element passed to `ForceGraph()` is not recognized as a DOM element by the library's internal wrapper.

**Diagnosis steps:**
1. Check initialization pattern (see below)
2. Check module vs script mismatch — ESM build used with `<script>` tag vs UMD build used with `<script type="module">`
3. Check for stray HTML characters (`>` between `</head>` and `<body>`) that corrupt DOM parsing

## Force-Graph API Patterns

### ESM (`<script type="module">`) — Correct
```javascript
import ForceGraph from 'https://cdn.jsdelivr.net/npm/force-graph@1.43.5/dist/force-graph.mjs';
const Graph = ForceGraph(graphEl)        // ← Kapsule constructor: element in, instance out
  .graphData(data)
  .backgroundColor('#0d0d0d');
```

### Classic UMD (`<script>`) — Correct
```javascript
// CDN: force-graph.min.js (UMD/IIFE build)
const Graph = new ForceGraph(document.getElementById('graph'))  // ← new + direct element
  .graphData(data);
```

### Common Mistakes

| Wrong | Correct | Why |
|-------|---------|-----|
| `ForceGraph()(graphEl)` (ESM) | `ForceGraph(graphEl)` | ESM Kapsule takes element directly, no curried call |
| `ForceGraph(element)(data)` | `new ForceGraph(element).graphData(data)` | UMD needs `new` and chain pattern |
| `<script src=".mjs">` (no type) | `<script type="module">` | ESM must be loaded as module |
| `<script type="module" src=".min.js">` | `<script type="module" src=".mjs">` | UMD build won't export correctly as ESM |

## Verified Working CDNs

- **jsDelivr ESM**: `https://cdn.jsdelivr.net/npm/force-graph@1.43.5/dist/force-graph.mjs` ✓
- **unpkg UMD**: `https://unpkg.com/force-graph@1.43.5/dist/force-graph.min.js` ✓

## Key Signal

If the same code works in a local HTML file but fails on GitHub Pages: check for stray characters in the HTML, especially between `</head>` and `<body>` — any `>` outside a tag breaks DOM parsing and the container element lookup fails silently.