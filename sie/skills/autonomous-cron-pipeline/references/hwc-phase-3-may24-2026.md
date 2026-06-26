# HWC Phase 3 — System Tray Icons Execution Log

**Date:** 2026-05-24
**Commit:** `7612e58`
**Phase:** 3 (System tray icons — real data wiring)

## Discovery: Wrong Go Toolchain Path

**Problem:** Cron job instructions specified the wrong Go toolchain path:
```
/home/hermeswebui/.hermes/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
```
This path does NOT exist in the container. The actual path is:
```
/opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.3.linux-amd64/bin/go
```

**Discovery method:** 
```bash
which go  # → /usr/bin/go (go1.24.4)
find /opt/data -name "go" -type f 2>/dev/null | grep toolchain
```
Result:
- `/opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.3.linux-amd64/bin/go` ✅ works
- `/opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.25.0.linux-amd64/bin/go`
- `/opt/data/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.3.linux-amd64/bin/go`

**Lesson:** Always verify toolchain paths with `find` rather than assuming the path from memory or prior docs.

## Metrics Endpoint — Extending SystemMetrics

The Phase 1 backend `/api/system/metrics` endpoint already existed (`ws/metrics.go`). Phase 3 extended it:

### Backend changes

Added to `SystemMetrics` struct:
```go
Wifi struct {
    Connected bool   `json:"connected"`
    SSID      string `json:"ssid,omitempty"`
} `json:"wifi"`
Battery struct {
    Percent   int  `json:"percent"`
    Charging  bool `json:"charging"`
    Available bool `json:"available"`
} `json:"battery"`
Volume struct {
    Percent int  `json:"percent"`
    Muted   bool `json:"muted"`
} `json:"volume"`
```

New collector functions:
- `readWifiStatus()` — reads `/sys/class/net/` for wlan* interfaces + `operstate`
- `readBatteryStatus()` — reads `/sys/class/power_supply/BAT*/capacity` + `status`
- `readVolumeStatus()` — stub, returns default 100%/not muted (pactl integration deferred)

Bug fixed: `mc.audioSource` → `m.Audio.Source` (assigning to wrong variable).

### Frontend changes

`Waybar.svelte` updated to consume all new metrics fields with appropriate visual states:
- WiFi: `🌐` (connected) or `📡` (disconnected, 40% opacity)
- Volume: `🔊`/`🔉`/`🔇` based on percent + muted state
- Battery: only rendered when `batteryAvailable=true`; charging/low/critical states
- Temperature: `🔥` (>80°C, red) or `🌡️` (normal)

## Vite Build — Background Pattern

Vite build takes ~55s. Must run in background:
```python
terminal(background=True, notify_on_complete=True)
# then process(action='wait', session_id=..., timeout=180)
```
Foreground attempts with `timeout` parameter all failed with "long-lived server/watch process" error even with `timeout 120` prefix.

## Discord API — User-Agent Required

Cloudflare blocks Discord API requests without `User-Agent`. Found via trial: `403 error code: 1010` without it.

Working pattern:
```python
headers={
    'Authorization': f'Bot {token}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (compatible; DiscordBot/1.0)'
}
```

Token location: `/opt/data/.env` (not `~/.hermes/.env` which doesn't have DISCORD entries).

## Pre-existing Test Failures (not from this phase)

5 FS tests in `ws` package fail:
- `TestFSList_Root`
- `TestFSList_Nested`
- `TestFSRead_TextFile`
- `TestFSStat_File`
- `TestFSStat_Dir`

Root cause: tests assume CWD is repo root. `getAllowedRoot()` uses `os.Getwd()` which in the container returns `/opt/hermes` (the hermes session CWD), not `/opt/data/hermes-web-computer`. The tests pass when run from the correct directory manually.

These failures predate Phase 3 and were present in Phase 0 baseline.

## Files Changed

- `backend/ws/metrics.go` — Extended SystemMetrics + 3 new collector functions
- `frontend/src/components/Waybar.svelte` — Wired all new metrics fields