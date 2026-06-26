# D3 Force Simulation "Clumped to Center" Debug

## Symptoms
- ~3900 D3 force simulation nodes all collapse to center on initial render
- Nodes visible but massed at single point, no outward spread
- Slider tweaks (linkDist, repulse, gravity) don't help

## Root Cause: O(n²) Edge Density

Two O(n²) loops in `buildGraph()`:
1. **Category edges**: all node pairs in same category get edges (dense intra-category springs)
2. **Tag-sharing edges**: at `tagThresh=1`, every node pair sharing ≥1 tag gets an edge. With 3900 nodes × ~3-5 tags each = millions of implicit edges

The simulation settles in ~30 ticks (default alphaDecay ~0.0228). With millions of spring edges, forces collapse to center before nodes can spread.

## Fix Applied (May 2026 — hermes-guide/skills-graph.html)

```javascript
// In initSim() — added alphaDecay
simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(edges).id(d => d.id).distance(linkDist).strength(0.3))
    .force("charge", d3.forceManyBody().strength(repulse))
    .force("center", d3.forceCenter(w / 2, h / 2).strength(gravity))
    .alphaTarget(0.3)
    .alphaDecay(0.01)   // ← ADDED: ~3x more ticks before settling

// In HTML slider defaults — reduced edge density
<input id="tagThresh" type="range" min="1" max="5" value="3">  <!-- was 1 -->
```

| Parameter | Was | Now | Effect |
|-----------|-----|-----|--------|
| tagThresh | 1 | 3 | Shared-tag edges: millions → thousands |
| alphaDecay | ~0.023 (default) | 0.01 | ~100 ticks vs ~30 before settling |
| linkDist | 80 | 120 | Longer links = more spread |
| repulse | -300 | -600 | Stronger node separation |
| gravity | 0.05 | 0.02 | Less pull to center |

## Key Insight
Slider tweaks to forces without fixing edge density don't work — the spring budget from millions of edges overwhelms any force parameter tuning. Fix edge density first (tagThresh), then tune alphaDecay to give the simulation time to spread.

## Verification
```bash
curl -s https://chonsong.github.io/hermes-guide/skills-graph.html | grep -E 'value="[0-9]|alphaDecay'
```

## Next-Step Debug Options
- `velocityDecay(0.4)` — slows velocity buildup per tick, more spread control
- Increase tagThresh to 4-5 for further edge reduction
- Reduce category edge density (currently all-pairs within category)

## File Location
`docs/skills-graph.html` in the ChonSong/hermes-guide repo (deployed via GitHub Pages from `docs/` dir — NOT `slides/`)
