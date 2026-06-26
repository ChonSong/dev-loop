---
name: go
description: Build, test, and run Go projects on the host system. Covers module initialization, dependency management, cobra CLI patterns, cross-compilation, and Docker multi-stage builds for Go binaries.
tags: ["go", "golang", "cli", "cobra", "docker"]
---

# Go Development

## Host Environment

Go may or may not be installed on the host. **Always check first:**

```bash
which go && go version
```

### Installing Go Without Sudo (Tarball)

When `go` is not on the host PATH (Ubuntu 20.04, no `snap`, no `apt` install rights):

```bash
curl -sL https://go.dev/dl/go1.22.5.linux-amd64.tar.gz -o /tmp/go.tar.gz
tar -C ~ -xzf /tmp/go.tar.gz
export PATH=$HOME/go/bin:$PATH
go version
```

Pick the latest stable from https://go.dev/dl/. The tarball installs to `~/go/` — no root needed.

### Static Linking for Old glibc Hosts

If the binary was built with a newer Go toolchain (or on a container with newer glibc) and fails on the host with `version 'GLIBC_2.XX' not found`, rebuild with **CGO_ENABLED=0** for a fully static binary:

```bash
CGO_ENABLED=0 go build -o myapp ./cmd/server
file myapp
# → "statically linked" — no libc dependency
```

This eliminates all glibc version incompatibilities. Always use `CGO_ENABLED=0` when:
- The host is Ubuntu 20.04 (glibc 2.31) and build happens on a newer system
- The binary will be deployed across multiple Linux distros
- The Docker multi-stage pattern uses a `scratch` or `alpine` runtime stage

### Systemd User Service for Go Web Binaries

After building a Go web server, deploy it as a systemd user service:

```ini
# ~/.config/systemd/user/myapp.service
[Unit]
Description=My Go Web Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/user/repos/myapp/backend/myapp
WorkingDirectory=/home/user/repos/myapp/backend
Restart=on-failure
RestartSec=5
Environment=PORT=3005
Environment=MYAPP_STATE_DIR=/home/user/.hermes/myapp

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now myapp.service
systemctl --user status myapp.service
# Verify:
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:3005/
curl -s http://localhost:3005/health
```

Key points:
- `WorkingDirectory` matters — Go binaries resolve relative paths (e.g. `../frontend/dist`) from CWD
- Use `Restart=on-failure` not `always` for daemons that can fail on bad config
- `Environment=` for port, state dir, and any other config the binary reads from env
- No `User=` in user-mode services (runs as the logged-in user)

### Linter false positives

The Go linter in the container often reports `no required module provides package X` even when `go build ./...` succeeds. This is because the linter runs without full module context. **Trust `go build` and `go vet` over the linter.**

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

## Common Patterns

### Initialize a new Go module

```bash
ssh -o StrictHostKeyChecking=no sean@localhost "cd /path/to/module && go mod init module/path && go get github.com/spf13/cobra@v1 && go mod tidy"
```

### Build a Go package

```bash
ssh -o StrictHostKeyChecking=no sean@localhost "cd /path/to/module && go build -o /tmp/bin-name ."
```

### Run tests

```bash
ssh -o StrictHostKeyChecking=no sean@localhost "cd /path/to/module && go test ./..."
```

### Create a cobra CLI

```go
package main

import (
    "fmt"
    "github.com/spf13/cobra"
)

func main() {
    root := &cobra.Command{Use: "myapp"}
    root.AddCommand(&cobra.Command{
        Use:   "subcommand",
        Short: "Does something",
        RunE:  runSubcommand,
    })
    if err := root.Execute(); err != nil {
        panic(err)
    }
}

func runSubcommand(cmd *cobra.Command, args []string) error {
    fmt.Println("Running subcommand")
    return nil
}
```

### Docker multi-stage build for Go

```dockerfile
# Stage 1: build
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY *.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o /bin/myapp .

# Stage 2: runtime
FROM alpine:latest
COPY --from=builder /bin/myapp /usr/local/bin/
ENTRYPOINT ["myapp"]
```

## Go Version Compatibility

`go.mod` declares `go 1.26` but the container has `go1.24.4`. Forward compatibility works — builds and tests pass with the older version. Do NOT force toolchain upgrades if system Go works.

When inside the hermes container (with its custom toolchain path), use the exact path:
```
/home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
```
Outside the container (cron environment, bare metal), use system `go`.

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

Also: add new app type to `apps.go`'s `apps` slice, then update the test expected map.

## Path Conventions

- Go modules live under `/home/sean/.hermes/agent-os/infra/CasaOS/agent/` and `.../webhook-emitter/`
- Build outputs to `/tmp/` for testing, or to the module dir for final binaries
- Go module cache: `~/.cache/go-build`
- HWC backend: `/opt/data/hermes-web-computer/backend/` — build to `backend/hwc-server`, tests via `go test ./... -count=1 -timeout=120s`
