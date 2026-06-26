# Go Backend Package Wiring Audit

How to determine if a Go backend package is actually wired (used at runtime) vs dead code (compiled but never invoked).

## Investigation Layers (in order)

### Layer 1: Import Graph
```bash
# Find who imports a package
grep -rn "\"hermes-web-computer/backend/<pkg>\"" --include="*.go" backend/
```
- **`main.go`** imports = the package is initialized at server start
- **`ws/multiplexer.go`** imports = the package is part of the core routing infrastructure
- **Only `*_test.go`** imports = used in tests only, not at runtime
- **Nothing** = dead code

### Layer 2: Struct Field Existence
In `multiplexer.go`, check if the Multiplexer struct (or the package's Manager) has a field for the type:
```go
mcpMgr      *mcp.Manager     // Has field → at least the type is referenced
telemetry   *telemetry.RingBuffer  // Has field + initialized in constructor
```
Search for type references: `grep -n "type.*\*<pkg>\." ws/multiplexer.go`

### Layer 3: Constructor Initialization
In `NewMultiplexer()`, check if the package is initialized:
```go
browser.NewManager()                    // ✅ Created in constructor
telemetry.NewRingBuffer(...)            // ✅ Created in constructor
m.mcpMgr = mcp.NewManager()             // ✅ Lazy init on first use
```
- Direct call in constructor = eagerly wired
- `if m.mcpMgr == nil { m.mcpMgr = mcp.NewManager() }` = lazy wired
- No call = potentially dead

### Layer 4: WS Route Handlers
Check if the package has WebSocket route entries in `routeUI()` or `routeAgent()`:
```bash
grep -n "case \"<pkg>\.\|m\.<pkg>\." ws/multiplexer.go
```
- `case "mcp.list": m.handleMCPList(...)` = WS protocol wired
- `m.browser.GetInstance(...)` = runtime usage present
- Just import + field without handler = type-safe but not used

### Layer 5: Frontend Integration
Check if the frontend sends WS messages for these methods:
```bash
grep -rn "method: \"<pkg>\." --include="*.svelte" --include="*.ts" frontend/src/
```
- Frontend calls exist = full integration
- Only backend handlers, no frontend = half-wired (backend ready, UI missing)

### Layer 6: Test Files
```bash
find . -name "*_test.go" -path "*/<pkg>/*"
```
- No test files = no test coverage (even for wired packages)

## Common Patterns

| Pattern | Status | Example |
|---------|--------|---------|
| No import, no field, no handler | Dead ❌ | `llm` |
| Imported, field exists, no init, no handler | Structural stub ⚠️ | — |
| Imported, field exists, lazy init, handlers exist, no frontend | Half-wired 🟡 | `mcp` |
| Imported, field exists, constructor init, handlers exist, frontend calls | Fully wired ✅ | `browser`, `telemetry` |

## Verifying Build Health
```bash
cd backend && go build ./...   # Must pass (imports are correct)
cd backend && go vet ./...     # Must pass (no suspicious constructs)
```

## One-Time Investigation Commands (full audit)
```bash
# Find all backend packages that exist
find backend -maxdepth 2 -name "*.go" -not -name "*_test.go" | sed 's|.*/\([^/]*\)/.*|\1|' | sort -u

# For each package, check if main.go imports it
grep -rln "hermes-web-computer/backend/<pkg>" --include="*.go" backend/cmd/

# Check if multiplexer.go imports it
grep "hermes-web-computer/backend/<pkg>" backend/ws/multiplexer.go

# Check if any WS handlers reference it
grep -c "m\.<pkg>\." backend/ws/multiplexer.go
```
