# TDZ Patterns in Single-File Inline-JS Apps

## The Problem

When a single HTML file embeds a large JSON dataset (>100KB) directly in a `<script>` tag, the natural pattern is:

```js
const GRAPH_DATA = { nodes: [...], edges: [...], ... };
const { nodes, edges } = GRAPH_DATA;
// ... more declarations ...
// ... edge filter buttons built here, referencing TAG_SHARED ...
// ... 200+ lines later ...
const TAG_SHARED = 'tag-shared';  // TDZ! Accessed above
```

This triggers `ReferenceError: Cannot access 'TAG_SHARED' before initialization` — the entire script block fails silently.

## Root Cause

- `const` and `let` are hoisted but in the Temporal Dead Zone until their declaration line executes
- The massive JSON literal (~570KB) takes a while to parse, and the script continues execution sequentially
- Any code between the destructuring and the declaration that references the variable will crash

## Fix: Group All Constants at Top

Immediately after the data destructuring, declare ALL shared constants with their initial values:

```js
const GRAPH_DATA = { ... };  // inline JSON
const { nodes, edges } = GRAPH_DATA;

// EARLY declarations — all shared constants here
const TAG_SHARED = 'tag-shared';
const edgeFilterDefault = GRAPH_DATA.edge_filter_default;
let tagEdges = [];

// Then rest of the code — safe to reference them
```

## Fix: Move Dependencies Into Functions

If a variable can't be declared early (e.g., depends on data computation), wrap the code that uses it in a function called after initialization:

```js
function buildNeighborMap() {
  tagEdges.forEach(...);  // safe — called later
}
```

## Detection

The error is always `ReferenceError: Cannot access 'X' before initialization`.
Find all uses of variable X, then find its declaration. If any use appears textually before the declaration (in the same `<script>` block), that's the bug.

```bash
# Check order of all declarations and usages
grep -n "TAG_SHARED\|tagEdges\|const\|let " index.html | head -40
```

Variables that commonly trigger this in knowledge-graph style apps: `TAG_SHARED`, `tagEdges`, `edgeFilterDefault`, `TAG_SHARED`.
