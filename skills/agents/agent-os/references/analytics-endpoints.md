# Analytics & Observability Endpoints

Verified working as of 2026-05-07. All return `source: postgresql`.

## `GET /api/analytics/usage?days=7`

Returns daily session/message/token totals from `dashboard_messages`, with per-model breakdown.

**Actual response shape (verified 2026-05-07):**
```json
{
  "total_tokens": 73,
  "total_sessions": 10,
  "daily": [
    {
      "day": "Tue May 05 2026 00:00:00 GMT+0000 (Coordinated Universal Time)",
      "input_tokens": 0,
      "output_tokens": 0,
      "cache_read_tokens": 0,
      "reasoning_tokens": 0,
      "estimated_cost": 0,
      "actual_cost": 0,
      "sessions": 8,
      "api_calls": 15
    },
    {
      "day": "Wed May 06 2026 00:00:00 GMT+0000 (Coordinated Universal Time)",
      "input_tokens": 29,
      "output_tokens": 44,
      "cache_read_tokens": 0,
      "reasoning_tokens": 0,
      "estimated_cost": 0.0002,
      "actual_cost": 0.0002,
      "sessions": 2,
      "api_calls": 4
    }
  ],
  "by_model": [
    {
      "model": "claude-3-5-sonnet-20241022",
      "input_tokens": 29,
      "output_tokens": 44,
      "estimated_cost": 0.0002,
      "sessions": 2
    }
  ]
}
```

**Key field names (not `by_date`):** `daily[]` not `by_date[]`, `day` is a full JS date string, `by_model[]` not `models[]`.

Token estimation: `Math.ceil(content.length / 4)` where actual token counts not provided. Cost in USD.

## `GET /api/analytics/models?days=7`

Returns per-model breakdown from `dashboard_messages`.

**Actual response shape (verified 2026-05-07):**
```json
{
  "models": [
    {
      "model": "claude-3-5-sonnet-20241022",
      "input_tokens": 29,
      "output_tokens": 44,
      "estimated_cost": 0.0002,
      "sessions": 2,
      "message_count": 4
    }
  ]
}
```

**Key fields:** `models[]` (array), each has `message_count` (not `messages`).

## `GET /api/events/recent?limit=N`

Returns the last N events from `aie_events` ordered by timestamp DESC.

```json
{
  "events": [
    {
      "id": "b960c8a4-e124-49cb-997c-eda089d670bb",
      "session": null,
      "type": "container_state_change",
      "ts": "2026-05-05T10:23:08.892419+00",
      "name": "agent-os-nanobot",
      "data": {
        "name": "agent-os-nanobot",
        "type": "container_state_change",
        "image": "ghcr.io/chonsong/agent-os:latest",
        "state": "Up 9 seconds (healthy)",
        "timestamp": "2026-05-05T10:23:08Z"
      }
    }
  ]
}
```

Columns: `id` (UUID string), `session` (UUID string or null), `type` (text), `ts` (timestamptz), `name` (from `data->name`), `data` (full jsonb payload).

Event types in `aie_events`: `container_state_change` (4100+), `task_complete` (7), `tool_call` (3). Total ~5300 events as of 2026-05-07.

## `GET /api/analytics/real`

Returns aggregate event counts from `aie_events`, grouped by type.

```json
{
  "sessions": [],
  "events": 3,
  "event_breakdown": [
    { "event_type": "container_state_change", "count": 1 },
    { "event_type": "task_complete", "count": 1 },
    { "event_type": "tool_call", "count": 1 }
  ],
  "source": "postgresql"
}
```

## Docker Stats: `GET /api/docker/stats`

Per-container real-time resource stats. Only running containers have stats.

```json
{
  "stats": [
    {
      "id": "abc123def456",
      "name": "agent-os-backend",
      "state": "running",
      "cpu_percent": 2.45,
      "memory_usage": 134217728,
      "memory_limit": 2147483648,
      "memory_percent": 6.25,
      "network_rx": 18432,
      "network_tx": 8192,
      "pids": 12
    }
  ]
}
```

Units: `memory_usage`, `memory_limit`, `network_rx`, `network_tx` are bytes. `memory_percent` is `memory_usage / memory_limit * 100`. `cpu_percent` is instantaneous CPU %. Powers the ContainerPage live stat bars.

## Docker Info: `GET /api/docker/info`

Docker system-wide information.

```json
{
  "ContainersRunning": 4,
  "ContainersPaused": 0,
  "ContainersStopped": 1,
  "NCPU": 4,
  "MemTotal": 1979543552,
  "Images": 11,
  "KernelVersion": "6.6.0-50-generic",
  "ServerVersion": "27.5.1",
  "OperatingSystem": "Ubuntu 22.04.4 LTS"
}
```

Powers ObservabilityPage Docker system info card.

## Frontend pages needing wiring

### AnalyticsPage.tsx (RESOLVED 2026-05-07)
Fully implemented and routed at `/analytics`. Shows token tracking, model breakdown, 7/30/90 day period selector. Data from `GET /api/analytics/usage` and `GET /api/analytics/models`. Previously built but never routed — now wired with sidebar link.

### LogsPage.tsx (RESOLVED 2026-05-07)
Backend endpoint `GET /api/logs` implemented. Returns log lines from Docker container logs via dockerode. ContainerPage uses it for viewing container logs.

### FileExplorerPage.tsx (RESOLVED 2026-05-07)
Fully implemented. Browse `/opt/data` and `/home/sean` host paths via `GET /api/files/*` and `GET /api/files/read/*`. Backend mounts `/opt/data:rw` and `/home/sean:rw`. Path traversal protected at backend level.

### ModelsPage.tsx (RESOLVED 2026-05-07)
Model picker now accessible via ChatSidebar `ModelPickerDialog`. `GET /api/model/info` returns current model from nanobot config. `GET /api/model/options` returns available models from nanobot `/v1/models`.
