# Force-Graph Visualization — Additional Pitfalls (July 2025 + June 2026 reviews)

Collected from reviewing `chonsong/hermes-knowledge-graph/graph/` — an 821-node, 1298-edge single-file force-graph page.

## Bugs Found (Original Review)

### 1. Filter chip selector mismatch (broken filters)
**HTML** uses class `filter-chip` but **JS** queries `#filter-chips .chip` (missing `filter-` prefix). Click handlers never attach. Chips look clickable but do nothing. Additionally, `chip.id` is used as the filter key but buttons have no `id` attribute, so the key is always `""`.

**Fix:** `document.querySelectorAll('#filter-chips .filter-chip')` and use `data-filter`/`data-value` as key.

### 2. "All" chip for verified filter hides everything
The "All" button has `data-value="all"` but `applyChipFilters` only handles `verified === 'true'`. No node satisfies `verified === "all"`, so all nodes disappear.

**Fix:** Make "all" a no-op that clears that filter dimension, or use a separate "Reset all" button.

### 3. Detail panel connections list shows hidden edges
When edge types are filtered off, connections list still shows them with "(hidden)" badge. Clutters the list.

**Fix:** Skip hidden edge types entirely in the connections render loop, or add a "show hidden" toggle.

### 4. Hash deep-link race condition
`handleHash()` reads `node.x`/`node.y` at 200ms timeout, but if simulation hasn't settled, coordinates may be `0,0` or `NaN`. Camera centers on origin instead of the node.

**Fix:** Retry loop waiting for `node.x !== undefined && node.x !== 0`, or wait for `onEngineStop`.

### 5. Mobile sidebar: no backdrop dismiss
Sidebar slides in on mobile with no backdrop overlay and no click-outside-to-close. Users must re-find the hamburger button.

**Fix:** Add a full-screen semi-transparent backdrop div that closes sidebar on click.

### 6. No "reset all filters" button
Combining namespace toggles + quality chips + edge filters has no one-click reset.

**Fix:** Button that resets `activeNamespaces`, chip filters, `activeTypes`, search, then calls `rebuildGraph()`.

### 7. Quality score gradient bar is misleading
Static rainbow `linear-gradient(90deg, #3498db, #9b59b6, #e84a5f)` looks identical for score 2/10 and 8/10 — only fill width changes.

**Fix:** Use threshold-based colors: green ≥7, yellow ≥4, red <4.

### 8. Edge legend not interactive
Edge type legend uses `cursor: default` and is display-only. Making them clickable toggles (like namespace legend) would be consistent.

### 9. Search match counter missing
Arrow up/down cycles search matches but no "3/15 matches" counter exists.

### 10. Detail panel has no close (✕) button
Only closes on Escape or background click. Mobile users have no obvious dismiss.

### 11. `tools` and `dependencies` fields always empty
All 821 nodes have `tools: []` and `dependencies: []`. Either populate from metadata or hide those sections.

### 12. No favicon
No `<link rel="icon">` — browser tab shows blank icon.

## Bugs Found (June 2026 Follow-up Review)

### 13. Hover highlight stuck after drag
After hovering a node (which dims non-neighbors), dragging the graph doesn't clear the hover state. The dimmed/focused state persists until explicitly hovering another node, causing confusing "stuck" highlighting.

**Fix:** Add `.onDrag()` handler that clears `hoveredNode = null` and hides tooltip:
```javascript
.onDrag(() => {
  hoveredNode = null;
  tooltip.style.display = 'none';
  if (graph) {
    graph.nodeColor(getNodeColor);
    graph.linkColor(getLinkColor);
    graph.nodeLabel(getNodeLabel);
  }
})
```

### 14. Camera resets on every filter change
`rebuildGraph()` calls `graph.zoomToFit(400, 120)` on every filter toggle, destroying the user's camera position.

**Fix:** Remove `zoomToFit` from `rebuildGraph`. Only zoom-to-fit on initial load:
```javascript
if (graph) {
  graph.graphData({ nodes: visibleNodes, links: gEdges });
  return;  // no auto-zoom on filter change
}
// In init:
if (savedCamera && graph) {
  graph.centerAt(savedCamera.x, savedCamera.y, 0);
  graph.zoom(savedCamera.zoom, 0);
} else if (graph) {
  graph.zoomToFit(400, 120);
}
```

### 15. Chip filters not persisted to localStorage
`saveState()` doesn't include `chipFilters`, so page reload loses active chip selections.

**Fix:** Add to saveState:
```javascript
chipFilters: Object.fromEntries(Object.entries(chipFilters).filter(([k,v]) => v)),
```
And restore in `restoreState()`:
```javascript
if (state.chipFilters && typeof state.chipFilters === 'object') {
  Object.entries(state.chipFilters).forEach(([k, v]) => { chipFilters[k] = v; });
  document.querySelectorAll('#filter-chips .filter-chip').forEach(chip => {
    const key = chip.id || `chip-${chip.dataset.filter}-${chip.dataset.value}`;
    if (chipFilters[key]) chip.classList.add('active');
  });
}
```

### 16. Stats show total counts not filtered
Stats bar always shows "821 nodes · 1298 edges" even when filters hide most nodes.

**Fix:** Pass visible counts to `updateStats()`:
```javascript
function updateStats(visibleNodeCount, visibleEdgeCount) {
  const totalEdges = edges.length + (activeTypes.has(TAG_SHARED) ? tagEdges.length : 0);
  stats.innerHTML = `<span>${visibleNodeCount}</span>/<span>${nodes.length}</span> nodes · <span>${visibleEdgeCount}</span>/<span>${totalEdges}</span> edges`;
}
// Call: updateStats(visibleNodes.length, gEdges.length);
```

### 17. Search matches not visually highlighted
Non-matching nodes dim to `#222236` but matching nodes render at full color with no distinguishing mark — hard to spot among 821 nodes.

**Fix:** Add canvas ring via `nodeCanvasObject`:
```javascript
function isSearchMatch(n) {
  const q = searchQuery.toLowerCase().trim();
  if (!q) return false;
  return n.name.toLowerCase().includes(q) || n.namespace.toLowerCase().includes(q);
}
// In nodeCanvasObject:
if (isSearchMatch(node)) {
  ctx.beginPath();
  ctx.arc(node.x, node.y, node.size + 4, 0, 2 * Math.PI);
  ctx.strokeStyle = '#f0c040';
  ctx.lineWidth = 2;
  ctx.stroke();
}
```

### 18. Connections list unsorted
Connections appear in edge construction order, making it hard to scan for high-degree nodes.

**Fix:** Sort visible first, then by type, then by name:
```javascript
allConns.sort((a, b) => {
  const aHidden = !activeTypes.has(a.type) ? 1 : 0;
  const bHidden = !activeTypes.has(b.type) ? 1 : 0;
  if (aHidden !== bHidden) return aHidden - bHidden;
  const aLabel = (a.label || a.type).localeCompare(b.label || b.type);
  if (aLabel !== 0) return aLabel;
  const aOther = nodes.find(n => n.id === (a.src === node.id ? a.tgt : a.src));
  const bOther = nodes.find(n => n.id === (b.src === node.id ? b.tgt : b.src));
  return (aOther?.name || '').localeCompare(bOther?.name || '');
});
```

### 19. Hidden connections always visible in detail panel
Filtered-out edge types still appear in the connections list with "(hidden)" badge, cluttering the list.

**Fix:** Hide by default with toggle:
```javascript
const hiddenConns = allConns.filter(e => !activeTypes.has(e.type));
// Add toggle button
hiddenToggle.textContent = `Show ${hiddenConns.length} hidden`;
hiddenToggle.addEventListener('click', () => {
  hiddenShown = !hiddenShown;
  connList.querySelectorAll('.hidden-conn').forEach(el => {
    el.classList.toggle('show-hidden', hiddenShown);
  });
});
// CSS: .conn-item.hidden-conn { display: none; }
// CSS: .conn-item.hidden-conn.show-hidden { display: flex; }
```

## Bugs Found (July 2026 Second Follow-up)

### 20. Legend invisible — edge type dots too dim
Edge type legend used `opacity: 0.6` circular dots on a dark background — nearly invisible. Namespace dots were 8px with no border, also hard to see.

**Fix:** For edge types, use colored **line swatches** (18px wide, 2px thick border-top) instead of dots — they look like the edges they represent. Raise base opacity to `0.85`. For namespace dots, increase to 10px with a subtle white border. Add node count badges per namespace. Increase legend container width to 180px with stronger background and box-shadow:
```css
.legend-row .dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  border: 1px solid rgba(255,255,255,0.15);
}
.legend-row .edge-line {
  width: 18px; height: 0; border-top: 2px solid; flex-shrink: 0; border-radius: 1px;
}
```

### 21. No line opacity control
Users cannot adjust edge transparency. Dense graphs with 1000+ edges become an opaque hairball.

**Fix:** Add an opacity slider that controls `graph.linkOpacity()`. Default 60% works well for 800+ node graphs. Persist to localStorage. Don't double-apply opacity via rgba in `linkColor` — `.linkOpacity()` handles it:
```javascript
let linkOpacity = 0.6;
// In graph init: .linkOpacity(linkOpacity)
// Slider handler:
document.getElementById('link-opacity').addEventListener('input', (e) => {
  linkOpacity = parseInt(e.target.value) / 100;
  if (graph) graph.linkOpacity(linkOpacity);
  saveState();
});
```

### 22. TDZ crash — `tagEdges` and `TAG_SHARED` referenced before declaration

When building edge filter buttons at load time, the code references `tagEdges.length` and `TAG_SHARED` in the `edge_types.forEach(...)` loop. If `let tagEdges = []` and `const TAG_SHARED = 'tag-shared'` are declared later in the script (e.g. in a "Tag edge system" section), the page crashes with `Uncaught ReferenceError: Cannot access 'tagEdges' before initialization`.

**Root cause**: `let`/`const` are hoisted but in the Temporal Dead Zone — accessing them before the declaration line throws a `ReferenceError`. Unlike `var`, they are NOT usable before their declaration.

**Fix**: Declare both at the very top of the script, before any load-time code:

```javascript
// At the TOP of the script, right after GRAPH_DATA destructuring:
const TAG_SHARED = 'tag-shared';
const edgeFilterDefault = GRAPH_DATA.edge_filter_default;
let tagEdges = [];  // will be populated later by computeTagEdges()

// ... later, in the edge filter buttons section, tagEdges.length works fine

// ... later still, in the tag edge system section:
tagEdges = computeTagEdges(tagThreshold);  // assignment, not redeclaration
```

**Key rule**: Any variable referenced in load-time code (not inside a function that runs later) must be declared before that code runs. Function bodies are safe — they execute when called, not when declared.

## Code Patterns

### Robust filter chip with data attributes
```javascript
document.querySelectorAll('#filter-chips .filter-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    chip.classList.toggle('active');
    const key = chip.id || `chip-${chip.dataset.filter}-${chip.dataset.value}`;
    chipFilters[key] = chip.classList.contains('active');
    rebuildGraph();
    saveState();
  });
});
```

### Hide filtered edges from connections list (with toggle)
```javascript
const visibleConns = allConns.filter(e => activeTypes.has(e.type));
const hiddenConns = allConns.filter(e => !activeTypes.has(e.type));
document.getElementById('conn-count').textContent =
  `${visibleConns.length} connections${hiddenConns.length > 0 ? ` (${hiddenConns.length} hidden)` : ''}`;
// Render visible normally, hidden with class "hidden-conn"
// Add toggle button to show/hide them
```

### Hash deep-link with simulation-ready guard
```javascript
function handleHash() {
  const hash = location.hash.replace(/^#/, '');
  if (!hash) return;
  const node = nodes.find(n => n.id === hash);
  if (!node) return;
  if (!graph || !graphInitialized) {
    setTimeout(handleHash, 100);
    return;
  }
  showDetail(node);
  graph.centerAt(node.x, node.y, 800);
  graph.zoom(2, 800);
}
```

### Mobile sidebar with backdrop dismiss
```javascript
const mobileBackdrop = document.getElementById('mobile-backdrop');
function openSidebar() {
  sidebarEl.classList.add('open');
  mobileBackdrop.classList.add('visible');
}
function closeSidebar() {
  sidebarEl.classList.remove('open');
  mobileBackdrop.classList.remove('visible');
}
mobileMenuBtn.addEventListener('click', () => {
  sidebarEl.classList.contains('open') ? closeSidebar() : openSidebar();
});
mobileBackdrop.addEventListener('click', closeSidebar);
```

### Quality bar with threshold colors
```javascript
const qColor = node.quality >= 7 ? '#4ecb71' : node.quality >= 4 ? '#f0c040' : '#e84a5f';
qFill.style.background = qColor;
```

### Search match counter
```javascript
const searchCounter = document.getElementById('search-counter');
function updateSearchCounter() {
  if (q && searchMatches.length > 0) {
    searchCounter.textContent = `${searchMatchIndex + 1}/${searchMatches.length}`;
    searchCounter.classList.add('has-matches');
  } else if (q) {
    searchCounter.textContent = '0/0';
    searchCounter.classList.add('has-matches');
  } else {
    searchCounter.textContent = '';
    searchCounter.classList.remove('has-matches');
  }
}
```

### Clear all filters button
```javascript
document.getElementById('btn-clear-filters').addEventListener('click', () => {
  activeNamespaces = new Set(namespace_order.filter(ns => ns_colors[ns]));
  document.querySelectorAll('#legend-item .legend-row').forEach(row => row.classList.add('on'));
  activeTypes.clear();
  Object.keys(edge_filter_default).forEach(t => {
    if (edge_filter_default[t]) activeTypes.add(t);
  });
  document.querySelectorAll('.filter-btn[data-type]').forEach(btn => {
    btn.classList.toggle('on', activeTypes.has(btn.dataset.type));
  });
  Object.keys(chipFilters).forEach(k => chipFilters[k] = false);
  document.querySelectorAll('#filter-chips .filter-chip').forEach(chip => chip.classList.remove('active'));
  document.querySelectorAll('#legend-edges .legend-row').forEach(row => row.classList.remove('disabled'));
  searchInput.value = '';
  searchQuery = '';
  applySearch();
  rebuildGraph();
  saveState();
});
```

### Interactive edge legend (sync with filter buttons)
```javascript
edge_types.forEach(([type, label, color]) => {
  const row = document.createElement('div');
  row.className = 'legend-row';
  row.dataset.edgeType = type;
  row.innerHTML = `<div class="dot" style="background:#${color.toString(16).padStart(6,'0')}"></div><span class="ns-label" style="font-size:10px">${label}</span>`;
  row.addEventListener('click', () => {
    if (activeTypes.has(type)) {
      activeTypes.delete(type);
      row.classList.add('disabled');
    } else {
      activeTypes.add(type);
      row.classList.remove('disabled');
    }
    const btn = document.querySelector(`.filter-btn[data-type="${type}"]`);
    if (btn) btn.classList.toggle('on', activeTypes.has(type));
    rebuildGraph();
    saveState();
  });
  legendEdges.appendChild(row);
});
```
