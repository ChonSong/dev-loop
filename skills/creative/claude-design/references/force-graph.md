# force-graph API patterns and troubleshooting

## The correct API pattern

From the [official basic example](https://vasturiano.github.io/force-graph/example/basic/index.html):

```javascript
const Graph = new ForceGraph(document.getElementById('graph'))
  .graphData(data)
  .nodeLabel('id')
  // ... other config chain
```

From the [load-json example](https://vasturiano.github.io/force-graph/example/load-json/index.html):

```javascript
const Graph = new ForceGraph(document.getElementById('graph'))
  .graphData(data)
  .nodeId('id')
  .nodeVal('val')
  .nodeLabel('id')
  .nodeAutoColorBy('group')
  .linkSource('source')
  .linkTarget('target')
```

**Key rules:**
1. Always use `new ForceGraph(element)` — the `new` keyword is required
2. Chain `.graphData(data)` — data is NOT passed as a second function call
3. Configuration methods chain off the returned object

## What does NOT work

```javascript
// WRONG — container fails to attach
const Graph = ForceGraph(document.getElementById('graph'))(data)

// WRONG — missing new keyword  
const Graph = ForceGraph(document.getElementById('graph'))
  .graphData(data)
```

The broken pattern `ForceGraph(element)(data)` fails with:
```
Uncaught TypeError: t.appendChild is not a function
```
at the force-graph init code `t.innerHTML=""; var r=document.createElement("div"); ... t.appendChild(r)`.

Root cause: Without `new`, the ForceGraph factory (a Jr state machine wrapper) is called as a plain function, losing the `this = container element` binding that drives the internal DOM initialization chain.

## Vendoring the library

force-graph has peer dependencies on d3-force but bundles everything in the UMD build. The minified file works standalone.

```bash
# Download a specific version
curl -s https://unpkg.com/force-graph@{version}/dist/force-graph.min.js -o vendor/force-graph.min.js

# Verify integrity — compare byte count with CDN
# Both should report identical size (e.g., 161737 for v1.43.5)
```

Always vendor locally — CDN-hosted minified JS can silently fail, serve stale cached versions, or return non-functional content. The local file must be committed to the same repo as the HTML that references it, and served from the same origin (or relative path) as the page.

## GitHub Pages specific issues

- `index.html` must be at repo root — any other filename returns 404
- File references are case-sensitive even on macOS-hosted runners
- The deployed page URL pattern: `https://{user}.github.io/{repo}/`

## Diagnostic checklist for broken force-graph pages

1. [ ] Uses `new ForceGraph(element).graphData(data)` not `ForceGraph(element)(data)`
2. [ ] Vendor JS file committed to repo and accessible at deployed URL
3. [ ] `index.html` exists at repo root (not `hermes-knowledge-graph.html`)
4. [ ] HTTP 200 confirmed for page AND vendor JS at deployed URLs
5. [ ] Container element (`#graph`) exists in DOM before ForceGraph call
6. [ ] `const Graph = ...` declaration appears before any code that references `Graph`