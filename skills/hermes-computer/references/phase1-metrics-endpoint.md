# Phase 1 — Host Metrics Endpoint Implementation

**Commit:** `7566fdd` (2026-05-24)
**File:** `backend/ws/metrics.go` (new)
**Router changes:** `backend/ws/multiplexer.go` — `/api/system/metrics` HTTP route + `system.metrics` WS JSON-RPC case

## What was built

`metricsCollector` struct with 2-second cache TTL, providing:

| Field | Source | Notes |
|-------|--------|-------|
| `cpu.percent` | `/proc/stat` aggregate `cpu` line | `(1 - idle/total) * 100` |
| `cpu.cores` | `runtime.NumCPU()` | — |
| `memory.used_mb` | `/proc/meminfo` | `total - free - buffers - cached` |
| `memory.total_mb` | `/proc/meminfo` `MemTotal` | KB → MB |
| `network.rx/tx_bytes` | `/proc/net/dev` | Sum all non-loopback interfaces |
| `temperature.celsius` | `/sys/class/thermal/thermal_zone[0-1]/temp`, `/sys/class/hwmon/hwmon[0-1]/temp1_input` | First readable wins, °C |
| `audio.active/source/icon` | Injected via `SetAudioState()` | Falls back to `🔇` when inactive |

## Response shape

```json
{
  "cpu": {"percent": 12.4, "cores": 8},
  "memory": {"used_mb": 4096.0, "total_mb": 8192.0, "used_percent": 50.0},
  "network": {"rx_bytes": 1234567, "tx_bytes": 765432},
  "temperature": {"celsius": 54.2, "source": "/sys/class/thermal/thermal_zone0/temp"},
  "audio": {"active": true, "source": "fun-audio-chat", "icon": "🔊"},
  "timestamp": 1748078400000
}
```

## Two access patterns

1. **HTTP** — `GET /api/system/metrics` → `ServeMetricsHTTP()` → `json.NewEncoder(w).Encode(metrics)`
2. **WebSocket** — send `{"protocol":"ui","method":"system.metrics","id":"..."}` → `routeUI` case → `m.sendEvent(sess, Event{Protocol:"ui", Event:"system.metrics", Data:...})`

## Wiring to Waybar system tray

Phase 3 (system tray icons) will poll `GET /api/system/metrics` on a 5s interval and update the tray icons. The audio state (`SetAudioState`) should be called by the audio bridge when it connects/disconnects.

## Key implementation notes

- `globalCollector` is a package-level singleton, not attached to `Multiplexer` — metrics are shared across all WS sessions
- Cache TTL of 2s prevents `/proc` thrashing while staying fresh enough for real-time display
- Temperature source path varies by kernel/hardware — first readable file wins, falls back to `"unavailable"`
- CPU usage is a single-shot snapshot (not delta-based) — accurate enough for Waybar display, not for perf benchmarking
- `metricsCollector` struct lives in `ws/metrics.go`, `globalCollector` is the singleton instance

## Testing

```bash
# Local test (requires hermes-web-computer running on port 3005)
curl http://localhost:3005/api/system/metrics | jq .

# Go test
cd /opt/data/hermes-web-computer/backend
go test -v -run TestMetrics ./ws/  # if tests exist
```