---
name: casaos-webhook-emitter-impl
description: "Build casaos-webhook-emitter: Go service subscribing to CasaOS MessageBus WebSocket and fanning out HTTP webhooks. Part of Track A (event backbone) for the Casa frontend integration plan."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Go, CasaOS, WebSocket, Webhooks]
    track: A
    project: casaos-webhook-emitter
---

# casaos-webhook-emitter Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a Go service that subscribes to CasaOS MessageBus WebSocket events and fans them out as HTTP POSTs to registered webhook endpoints.

**Architecture:** One long-running Go process with a WebSocket client to CasaOS MessageBus, an in-memory webhook registry with disk persistence, and an HTTP fan-out dispatcher with retry logic.

**Tech Stack:** Go 1.21+, standard `net/http`, `Gorilla WebSocket`, `github.com/google/uuid`, `gopkg.in/yaml.v3`.

---

## Preconditions

- CasaOS MessageBus running at `http://{CASAOS_HOST}:{CASAOS_PORT}` (default `http://127.0.0.1:8080`)
- API Key auth: `Authorization: Bearer {CASAOS_API_KEY}` header on MessageBus WebSocket upgrade
- Subscribe to `source_id = "app-management"` (app lifecycle) and `source_id = "local-storage"` (disk events)
- Webhook emitter listens on `:{EMITTER_PORT}` (default `9393`)

---

## Project Structure

```
casaos-webhook-emitter/
├── main.go
├── internal/
│   ├── config/config.go
│   ├── bus/websocket.go
│   ├── registry/registry.go
│   ├── registry/webhook.go
│   ├── dispatcher/dispatch.go
│   └── server/server.go
├── config.yaml
└── README.md
```

---

## Task 1: Project Scaffolding

**Files:** Create `go.mod`, directory structure, empty files.

**Step 1: Initialize module**

```bash
cd casaos-webhook-emitter
go mod init github.com/ChonSong/casaos-webhook-emitter
go get github.com/gorilla/websocket@v1.5.1
go get github.com/google/uuid@v1.5.0
go get gopkg.in/yaml.v3@v3.0.1
```

**Step 2: Create config.yaml template**

```yaml
casaos_host: "127.0.0.1"
casaos_port: 8080
casaos_api_key: "your-api-key-here"
emitter_port: 9393
data_dir: "/opt/data/casaos-webhook-emitter"
log_level: "info"
```

Commit after files created.

---

## Task 2: Config Package

**File:** `internal/config/config.go`

```go
package config

import (
    "os"
    "strconv"
)

type Config struct {
    CasaOSHost   string
    CasaOSPort   int
    CasaOSAPIKey string
    EmitterPort  int
    DataDir      string
    LogLevel     string
}

func Load() *Config {
    port := 8080
    if p := os.Getenv("CASAOS_PORT"); p != "" {
        if v, err := strconv.Atoi(p); err == nil {
            port = v
        }
    }
    emitterPort := 9393
    if ep := os.Getenv("EMITTER_PORT"); ep != "" {
        if v, err := strconv.Atoi(ep); err == nil {
            emitterPort = v
        }
    }
    dataDir := "/opt/data/casaos-webhook-emitter"
    if dd := os.Getenv("DATA_DIR"); dd != "" {
        dataDir = dd
    }
    return &Config{
        CasaOSHost:   getEnv("CASAOS_HOST", "127.0.0.1"),
        CasaOSPort:   port,
        CasaOSAPIKey: getEnv("CASAOS_API_KEY", ""),
        EmitterPort:  emitterPort,
        DataDir:      dataDir,
        LogLevel:     getEnv("LOG_LEVEL", "info"),
    }
}

func getEnv(key, defaultVal string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    return defaultVal
}
```

Verify: `go build ./...`

---

## Task 3: Webhook Registry

**Files:** `internal/registry/webhook.go`, `internal/registry/registry.go`

`webhook.go`:
```go
package registry

import "time"

type Webhook struct {
    ID        string    `json:"id"`
    URL       string    `json:"url"`
    Events    []string `json:"events"` // ["*"] = all, or "app-management:app:installed"
    Secret    string    `json:"secret,omitempty"`
    Enabled   bool      `json:"enabled"`
    CreatedAt time.Time `json:"created_at"`
}

type Delivery struct {
    ID          string    `json:"id"`
    WebhookID   string    `json:"webhook_id"`
    Event       string    `json:"event"`
    Payload     string    `json:"payload"`
    StatusCode  int       `json:"status_code"`
    Attempt     int       `json:"attempt"`
    Response    string    `json:"response,omitempty"`
    DeliveredAt time.Time `json:"delivered_at"`
    Success     bool      `json:"success"`
}
```

`registry.go`: In-memory store with YAML persistence. Methods:
- `New(dataDir string) (*Registry, error)` — loads persisted webhooks on startup
- `Add(url string, events []string, secret string) (*Webhook, error)`
- `List() []*Webhook`
- `Delete(id string) error`
- `Match(eventName string) []*Webhook` — pattern matching: `"*"` matches all; `"app-management:*"` matches `"app-management:app:installed"`

Persistence: `webhooks.yaml` in `dataDir`. Save on every write, load on startup.

Verify: `go build ./...`

---

## Task 4: Dispatcher (HTTP Fan-out with Retry)

**File:** `internal/dispatcher/dispatch.go`

```go
package dispatcher

import (
    "bytes"
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "io"
    "log"
    "net/http"
    "time"
)

type Dispatcher struct {
    client *http.Client
}

func New() *Dispatcher {
    return &Dispatcher{client: &http.Client{Timeout: 10 * time.Second}}
}

// Deliver sends event payload to webhook URL. Signs with HMAC-SHA256 if secret set.
// Retries 3x with exponential backoff: 1s, 2s, 4s.
func (d *Dispatcher) Deliver(webhookURL string, secret string, eventName string, payload []byte) error {
    body := bytes.NewReader(payload)
    req, _ := http.NewRequest("POST", webhookURL, body)
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("X-CasaOS-Event", eventName)
    req.Header.Set("User-Agent", "CasaOS-Webhook-Emitter/1.0")
    if secret != "" {
        sig := hmacSha256(secret, payload)
        req.Header.Set("X-CasaOS-Signature", "sha256="+sig)
    }

    var lastErr error
    for attempt := 1; attempt <= 3; attempt++ {
        if attempt > 1 {
            time.Sleep(time.Duration(1<<(attempt-1)) * time.Second)
        }
        resp, err := d.client.Do(req)
        if err != nil {
            lastErr = err
            log.Printf("[dispatch] attempt %d error: %v", attempt, err)
            continue
        }
        defer resp.Body.Close()
        bodyBytes, _ := io.ReadAll(io.LimitReader(resp.Body, 200))
        if resp.StatusCode >= 200 && resp.StatusCode < 300 {
            return nil
        }
        lastErr = fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(bodyBytes))
    }
    return fmt.Errorf("all 3 attempts failed: %w", lastErr)
}

func hmacSha256(secret string, payload []byte) string {
    mac := hmac.New(sha256.New, []byte(secret))
    mac.Write(payload)
    return hex.EncodeToString(mac.Sum(nil))
}
```

Verify: `go build ./...`

---

## Task 5: WebSocket Client (MessageBus Subscriber)

**File:** `internal/bus/websocket.go`

```go
package bus

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "sync"
    "time"

    "github.com/ChonSong/casaos-webhook-emitter/internal/config"
    "github.com/ChonSong/casaos-webhook-emitter/internal/dispatcher"
    "github.com/ChonSong/casaos-webhook-emitter/internal/registry"
    "github.com/gorilla/websocket"
)

type MessageBusEvent struct {
    SourceID    string                 `json:"sourceID"`
    Name        string                 `json:"name"`
    UUID        string                 `json:"uuid"`
    Properties  map[string]interface{} `json:"properties"`
    Timestamp   string                 `json:"timestamp"`
}

type WebSocketClient struct {
    cfg        *config.Config
    registry   *registry.Registry
    dispatcher *dispatcher.Dispatcher
    dialer     websocket.Dialer
    subs       map[string]*websocket.Conn
    mu         sync.Mutex
    ctx        context.Context
    cancel     context.CancelFunc
}

func NewWebSocketClient(cfg *config.Config, reg *registry.Registry) *WebSocketClient {
    ctx, cancel := context.WithCancel(context.Background())
    return &WebSocketClient{
        cfg:        cfg,
        registry:   reg,
        dispatcher: dispatcher.New(),
        subs:       make(map[string]*websocket.Conn),
        ctx:        ctx,
        cancel:     cancel,
    }
}

func (c *WebSocketClient) Start() error {
    for _, sid := range []string{"app-management", "local-storage"} {
        go c.subscribeLoop(sid)
    }
    log.Printf("[bus] WebSocket client started")
    return nil
}

func (c *WebSocketClient) Stop() {
    c.cancel()
    c.mu.Lock()
    defer c.mu.Unlock()
    for _, conn := range c.subs {
        conn.Close()
    }
}

func (c *WebSocketClient) subscribeLoop(sourceID string) {
    for {
        select {
        case <-c.ctx.Done():
            return
        default:
        }
        if err := c.subscribe(sourceID); err != nil {
            log.Printf("[bus] %s error: %v, reconnecting in 5s", sourceID, err)
            time.Sleep(5 * time.Second)
        }
    }
}

func (c *WebSocketClient) subscribe(sourceID string) error {
    wsURL := fmt.Sprintf("ws://%s:%d/v2/message_bus/event/%s",
        c.cfg.CasaOSHost, c.cfg.CasaOSPort, sourceID)
    header := http.Header{}
    if c.cfg.CasaOSAPIKey != "" {
        header.Set("Authorization", "Bearer "+c.cfg.CasaOSAPIKey)
    }
    conn, _, err := c.dialer.Dial(wsURL, header)
    if err != nil {
        return fmt.Errorf("dial: %w", err)
    }
    defer conn.Close()
    c.mu.Lock()
    c.subs[sourceID] = conn
    c.mu.Unlock()
    log.Printf("[bus] connected: %s", wsURL)
    for {
        _, msg, err := conn.ReadMessage()
        if err != nil {
            c.mu.Lock()
            delete(c.subs, sourceID)
            c.mu.Unlock()
            return fmt.Errorf("read: %w", err)
        }
        c.handleEvent(msg)
    }
}

func (c *WebSocketClient) handleEvent(msg []byte) {
    var event MessageBusEvent
    if err := json.Unmarshal(msg, &event); err != nil {
        return
    }
    fullName := fmt.Sprintf("%s:%s", event.SourceID, event.Name)
    matched := c.registry.Match(fullName)
    if len(matched) == 0 {
        return
    }
    payload, _ := json.Marshal(event)
    for _, wh := range matched {
        go func(w *registry.Webhook) {
            if err := c.dispatcher.Deliver(w.URL, w.Secret, fullName, payload); err != nil {
                log.Printf("[dispatch] deliver failed to %s: %v", w.URL, err)
            }
        }(wh)
    }
}
```

Subscribes to `app-management` and `local-storage` source IDs. On each event, matches registry and dispatches asynchronously. Auto-reconnects on disconnect with 5s backoff.

Verify: `go build ./...`

---

## Task 6: HTTP API Server

**File:** `internal/server/server.go` (routing + handlers in one file for simplicity)

Routes and handlers:

| Method | Path | Handler | Response |
|--------|------|---------|----------|
| GET | `/health` | `Health` | `{"status":"ok"}` |
| GET | `/webhooks` | `ListWebhooks` | `{"ok":true,"webhooks":[...]}` |
| POST | `/webhooks?url=&events=&secret=` | `CreateWebhook` | `{"ok":true,"id":"..."}` |
| DELETE | `/webhooks/{id}` | `DeleteWebhook` | `{"ok":true}` |
| GET | `/webhooks/{id}/test` | `TestWebhook` | fires test ping, returns deliver result |
| POST | `/events/casaos` | `ReceiveCasaOSEvent` | direct event injection for testing |

Pattern matching: use a single `http mux` with explicit pattern registration. Handle `/webhooks/`, `/webhooks/{id}`, `/webhooks/{id}/test`, `/webhooks/{id}/deliveries`.

Verify: `go build ./...`

---

## Task 7: Main.go

```go
package main

import (
    "fmt"
    "log"
    "os"
    "os/signal"
    "syscall"

    "github.com/ChonSong/casaos-webhook-emitter/internal/bus"
    "github.com/ChonSong/casaos-webhook-emitter/internal/config"
    "github.com/ChonSong/casaos-webhook-emitter/internal/registry"
    "github.com/ChonSong/casaos-webhook-emitter/internal/server"
)

func main() {
    cfg := config.Load()
    os.MkdirAll(cfg.DataDir, 0755)

    reg, err := registry.New(cfg.DataDir)
    if err != nil {
        log.Fatalf("registry error: %v", err)
    }

    wsClient := bus.NewWebSocketClient(cfg, reg)
    if err := wsClient.Start(); err != nil {
        log.Fatalf("websocket error: %v", err)
    }

    addr := fmt.Sprintf(":%d", cfg.EmitterPort)
    go func() {
        if err := server.Run(addr, reg); err != nil {
            log.Fatalf("HTTP server error: %v", err)
        }
    }()

    log.Printf("[main] running on %s, CasaOS at %s:%d", addr, cfg.CasaOSHost, cfg.CasaOSPort)

    sig := make(chan os.Signal, 1)
    signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
    <-sig
    log.Println("[main] shutting down...")
    wsClient.Stop()
}
```

Verify: build binary, run, `curl http://localhost:9393/health`, kill.

---

## Task 8: README + Systemd Unit

**README.md**: Usage, env vars, API reference, HMAC signing, subscribed events, systemd instructions.

**systemd unit** (`casaos-webhook-emitter.service`):
```ini
[Unit]
Description=CasaOS Webhook Emitter
After=network.target casaos.service

[Service]
Type=simple
ExecStart=/usr/local/bin/casaos-webhook-emitter
Environment=CASAOS_HOST=127.0.0.1
Environment=CASAOS_PORT=8080
Environment=EMITTER_PORT=9393
Environment=DATA_DIR=/opt/data/casaos-webhook-emitter
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## Verification Commands

```bash
# Health
curl http://localhost:9393/health

# Register webhook
curl -X POST "http://localhost:9393/webhooks?url=http://localhost:9999/hook&events=app-management:*&secret=mysecret"

# List
curl http://localhost:9393/webhooks

# Test
curl http://localhost:9393/webhooks/<id>/test

# Direct event injection (simulate CasaOS event)
curl -X POST http://localhost:9393/events/casaos \
  -H "Content-Type: application/json" \
  -d '{"sourceID":"app-management","name":"app:installed","uuid":"test-123","properties":{"app_id":"test-app"},"timestamp":"2026-05-01T00:00:00Z"}'
```

---

## Pitfalls

1. **CASAOS_API_KEY**: Without it, WebSocket upgrade returns 401. Check CasaOS gateway config for the key.
2. **source_id discovery**: Before hardcoding `app-management` and `local-storage`, call `GET /v2/message_bus/event_type` on the MessageBus HTTP API to enumerate registered types.
3. **Reconnection**: The goroutine loops indefinitely — fine for production, but means the process never exits on disconnect.
4. **HMAC verification**: Signature covers raw JSON bytes, hex-encoded HMAC-SHA256. Use `hmac_sha256(secret, body_bytes)` to verify.
