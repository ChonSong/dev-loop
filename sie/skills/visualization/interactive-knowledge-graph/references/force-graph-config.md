# Force-Graph Library API Reference

Core API for [force-graph](https://github.com/vasturiano/force-graph) v1.43.x.

## Initialization

```javascript
const graph = ForceGraph()(containerElement)
  .graphData({ nodes, links })
  .nodeId('id')              // property name for unique ID
  .nodeLabel(n => n.name)    // hover tooltip
  .nodeVal(10)               // constant size, or 'fieldName' or function
  .nodeColor(n => '#hex')
  .linkColor(l => '#hex')
  .linkWidth(l => 1.5)
  .linkDirectionalParticles(0)
  .backgroundColor('#0d0d14')
```

## Force Parameters

```javascript
// Charge/repulsion — higher = more spacing
graph.d3Force('charge').strength(-80);  // default -30

// Link tension — higher = longer edges
graph.d3Force('link').distance(30);     // default depends on graph

// Center gravity — pulls graph to center
graph.d3Force('center').strength(1);

// Simulation decay — higher = settles faster
graph.d3AlphaDecay(0.02);     // default 0.0228
graph.d3VelocityDecay(0.4);   // default 0.4
```

## Performance Methods

```javascript
// Pre-compute positions before rendering
graph.warmupTicks(200);

// Stop simulation after N ticks
graph.cooldownTicks(50);

// Reheat the simulation (after data update or param change)
graph.d3ReheatSimulation();

// Force the graph to draw one frame
graph.tickFrame();
```

## Event Handlers

```javascript
graph
  .onNodeClick(node => showDetail(node))
  .onBackgroundClick(() => hideDetail())
  .onEngineStop(() => {
    if (!initialized) {
      initialized = true;
      graph.zoomToFit(400, 120);
    }
  })
  .onEngineTick(() => { /* per-frame callback */ });
```

## Custom Node Rendering

```javascript
graph
  .nodeCanvasObjectMode(() => 'after')  // 'replace' or 'after'
  .nodeCanvasObject((node, ctx, globalScale) => {
    // Custom drawing on canvas
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.size, 0, 2 * Math.PI);
    ctx.fillStyle = node.color;
    ctx.fill();
  });
```

## Zoom

```javascript
graph.zoomToFit(transitionMs, paddingPx);
graph.zoom(scale);           // absolute zoom
graph.centerAt(x, y);        // pan to position
```

## Dynamic Updates

```javascript
// Replace all data (keeps node positions for matching IDs)
graph.graphData({ nodes: newNodes, links: newLinks });

// Update single node property (no reheat)
graph.nodeColor(n => newColorFn(n));
graph.nodeVal(n => newSizeFn(n));
graph.nodeLabel(n => newLabelFn(n));
