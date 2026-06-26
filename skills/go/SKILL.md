---
name: go
description: Build and test Go projects.
category: devops
tags: ["go", "golang", "cli", "cobra", "docker"]
source: local
is_imported: true
---

# go

Build and test Go projects.

**Category:** devops
**Source:** local

## HWC Build + Deploy Pattern

**Applies to:** `hermes-web-computer` (HWC) project.

### Environment-Specific Paths

| Context | Project Path | Go Binary | SSH Available |
|---------|-------------|-----------|---------------|
| Cron job / container | `/home/hermeswebui/.hermes/hermes-web-computer/backend/` | Go via module cache toolchain (see Go Version Compatibility) | No |
| Host (sean) | `/home/sean/.hermes/hermes-web-computer/backend/` | System `go` | N/A |

**Use** the container-specific toolchain path — it IS accessible and works for `go test`, `go build`, `go vet`, and `go fmt`:
```bash
GO=/home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
GOPATH=/home/hermeswebui/.hermes/home/go
cd /home/hermeswebui/.hermes/hermes-web-computer/backend && $GO test ./... -count=1 -timeout=120s
```

**Do NOT use SSH** from cron/container — SSH keys (`/home/hermes/.ssh/id_ed25519`, `/home/hermeswebui/.hermes/container_key`) are not accessible. Use `curl localhost` directly.

### Build and Test (Cron / Container)

```bash
# Build
cd /home/sean/.hermes/hermes-web-computer/backend
go build -o /tmp/hwc-server ./cmd/server

# Test
go test ./... -count=1 -timeout=120s

# Server health check (no SSH needed — shares host network)
curl -s -o /dev/null -w '%{http_code}' http://localhost:3005/
# Expect 200
```

### Systematic Code Quality Review (Static Analysis + Dead Code)

When tasked with cleaning up or reviewing a Go backend for quality, follow this systematic pattern beyond just `go vet` / `go build`:

### 1. Toolchain Baseline (always run first)

```bash
go test ./... -count=1 -timeout=120s
go build ./...
go vet ./...
gofmt -s -w .
```

Note: `go vet` may produce noise from the Go toolchain's own testdata files in the module cache (`.gopath/pkg/mod/golang.org/toolchain@...`). These are **intentional compiler test cases** — filter them out by grepping for project packages only.

### 2. Multi-file Static Analysis Sweep

After the baseline passes, do a deeper cross-file review:

1. **Read ALL .go files** in the project (not just changed files) — dead code accumulates silently
2. **Cross-reference every exported symbol** (function, type, method, variable) against all call sites across the codebase
3. **Check test-only dependencies** — if a function or method is only called from test files, flag it as a candidate for unexporting
4. **Look for these specific Go dead-code patterns:**

| Pattern | What to look for | Fix |
|---------|-----------------|-----|
| Redundant null check | `x := obj.Field; if x == "" { x = obj.Field }` — the guard checks against the same value | Remove the `if` block, use `obj.Field` directly |
| Empty if-block | `if condition { }` — body is empty, likely incomplete intent | Remove the if-block or add the intended logic |
| Double truncation | `WriteFile(path, nil, 0644)` immediately followed by `WriteFile(path, []byte(""), 0644)` — first write is wasted | Remove the first write |
| Dummy import suppressor | `import "pkg"` + `var _ = pkg.Type{}` where `pkg` is never used by any called method | Remove both import and dummy var (check no real usage exists) |
| Duplicate type declarations | Two packages define the same struct with overlapping fields (e.g. `state.LayoutTree` vs `layout.LayoutTree`) | Remove one, reference the canonical type |
| Duplicate sysfs/proc parsers | Two files parse `/proc/meminfo` or `/proc/stat` with different units | Unify into a shared helper in one package |
| Duplicate/redundant marshal methods | `MarshalJSON()` that re-marshals the struct identically to default | Remove the method |

### 3. Verification After Changes

```bash
# Always rebuild and re-vet after any change
go build ./...
go vet ./...
# Run full test suite
go test ./... -count=1 -timeout=120s
# Check formatting
gofmt -s -w . && git diff --stat
```

### Go vet module-cache noise

When running `go vet ./...` in a container with a custom `.gopath/` module cache path, permission-denied errors on Go toolchain testdata files are expected and harmless. Filter the output:

```bash
go vet ./... 2>&1 | grep -v "^\.gopath/pkg/mod/" | grep -v "^open \.gopath"
```

If that produces no output, the project code is clean. The noise is from the compiler's own negative-test fixtures.

## Go Version Compatibility

`go.mod` declares `go 1.26` but system Go is 1.24.4. Forward compatibility works — builds and tests pass. Do NOT force toolchain upgrades if system Go works.

### HWC Server Start (Host Only)

The server MUST be started from the `backend/` directory so the relative path `../frontend/dist` resolves correctly:

```bash
cd /home/sean/.hermes/hermes-web-computer/backend
HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer \
  nohup ./hwc-server server --port 3005 > /tmp/hwc-server.log 2>&1 &
```

### HWC hermesURL Default

The Hermes gateway runs on port **8787** on the host (not 8642). The default in `multiplexer.go` is `http://localhost:8787`.

## PTY Pattern (creack/pty)

When using `github.com/creack/pty`, **do not read from the PTY file descriptor in multiple goroutines** — only one reader will get the data. The fix is to add an output channel to the session:

```go
type PTYSession struct {
    PTY    *os.File
    Output chan []byte  // Single consumer reads from this
    mu     sync.Mutex
}

// In Start():
go func() {
    buf := make([]byte, 4096)
    for {
        n, err := p.Read(buf)
        if err != nil { return }
        session.mu.Lock()
        session.RingBuf.Write(buf[:n])  // Ring buffer for checkpoint
        session.mu.Unlock()
        // Forward to output channel (non-blocking)
        data := make([]byte, n)
        copy(data, buf[:n])
        select {
        case session.Output <- data:
        default: // Drop if channel full
        }
    }
}()

// Consumer reads from session.Output, not from session.PTY
```

## Pitfalls

### gofmt not in PATH inside container

In the container, `gofmt` is not directly available (`command not found`). Use `go fmt ./...` instead via the toolchain binary:

```bash
GO=/home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
cd /home/hermeswebui/.hermes/hermes-web-computer/backend && $GO fmt ./...
```

`go fmt` runs the toolchain's embedded `gofmt -s` under the hood. It's equivalent to `gofmt -s -w .` on the specified packages.

### gofmt scoping — avoid modifying vendored code

When a Go project has a `.gopath/` or `vendor/` directory, running `gofmt -s -w .` from the repo root reformats **all** Go files including vendored third-party code (which may have outdated `// +build` comments that gofmt auto-converts to `//go:build`). This creates an unexpectedly dirty working tree with hundreds of vendor-file changes.

**Always check with `-d` (dry-run) first:** `gofmt -d .` shows what would change without touching files. Inspect the output — if only vendor diffs appear, skip the format step or scope it.

**Safe approaches:**
- `gofmt -s -w ./cmd/... ./pkg/... ./internal/...` — scope to specific project packages
- `gofmt -s -w . && git checkout -- $(go env GOMODCACHE 2>/dev/null || echo .gopath)` — fix project files, revert vendor
- Or just skip `gofmt -w` if `go vet` and `go build` both pass — formatting is style, not correctness

## gofmt Module Cache Pitfall

When running `gofmt -s -w .` on a Go project that has a `.gopath/` subdirectory (a local GOPATH symlink or copy), gofmt recursively walks the module cache and tries to write to read-only files, producing hundreds of `permission denied` errors. The actual project source files are never touched.

**Fix:** Exclude `.gopath` from the recursive walk:

```bash
find . -path ./.gopath -prune -o -name "*.go" -print | xargs gofmt -s -w
```

The `.gopath/` directory is a local GOPATH used by the container's Go toolchain. Any recursive file operation (gofmt, grep, sed, git mv) that doesn't prune `.gopath` will either fail on permission errors or silently process irrelevant cached files.

**Proactive check:**
```bash
[ -d .gopath ] && echo "has module cache, use find -prune" || echo "safe to run gofmt -w ."
```

## Common Patterns

### Initialize a new Go module

```bash
cd /path/to/module
go mod init module/path
go get github.com/spf13/cobra@v1
go mod tidy
```

### Build a Go binary

```bash
cd /path/to/module
go build -o /tmp/bin-name .
```

### Maintenance Sweep Pattern

Periodic health checks on Go projects. Run in this order:

```bash
# 1. BUILD — catch compilation errors first
go build ./... 2>&1

# 2. TEST — catch regressions
go test ./... -count=1 -timeout=120s 2>&1

# 3. VET — catch suspicious constructs
go vet ./... 2>&1

# 4. FORMAT — enforce idiomatic style
gofmt -s -w .

# 5. DEPENDENCIES — prune and verify
go mod tidy && go mod verify 2>&1

# 6. CLEANUP — remove tracked build artifacts
# Find .gitignore candidates: state/, sessions/, tmp/ files, recorded test output
# For tracked artifacts: git rm --cached <file>, then add to .gitignore
```

**Git staging hygiene for cron maintenance:** When the working tree has developer WIP and developer files are already staged, unstage them first with `git restore --staged <files>` before staging only your maintenance changes. Never commit developer WIP in a sweep.

**Cron probe pattern:** If build → test → vet → tidy all pass, check T5 (artifact cleanup) before reporting `[SILENT]`. Build artifacts are the most commonly overlooked maintenance item.

### Run tests

```bash
ssh -o StrictHostKeyChecking=no sean@localhost "cd /path/to/module && go test ./..."
```
```

### Docker multi-stage build for Go

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY *.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o /bin/myapp .

FROM alpine:latest
COPY --from=builder /bin/myapp /usr/local/bin/
ENTRYPOINT ["myapp"]
```

## Linter False Positives

The Go linter in the container often reports `no required module provides package X` even when `go build ./...` succeeds. This is because the linter runs without full module context. **Trust `go build` and `go vet` over the linter.**

## Test Fix Pattern (HWC Example)

When a feature adds new types to an existing API, update test assertions:

```go
// Before (4 types): terminal, editor, preview, browser
if len(result.Apps) != 4 { ... }
expected := map[string]string{
    "terminal": "Terminal",
    "editor":   "Editor",
    "preview":  "Preview",
    "browser":  "Browser",
}

// After (5 types): add xpra
if len(result.Apps) != 5 { ... }
expected := map[string]string{
    "terminal": "Terminal",
    "editor":   "Editor",
    "preview":  "Preview",
    "browser":  "Browser",
    "xpra":     "Xpra",  // NEW
}
```
