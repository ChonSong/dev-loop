# Backend API Reference

## Source of Truth

Frontend API calls are defined in `apps/dashboard/frontend/src/lib/api.ts`. Every function there = an endpoint the backend must serve with valid JSON (not HTML).

## Implemented Routes (2026-05-04)

All routes below are implemented in `apps/dashboard/backend/src/index.ts` using an in-memory store.

### System
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/system/uptime` | `{ uptime: number }` |

### Docker (proxied via dockerode + `/var/run/docker.sock`)
| Method | Path | Response |
|--------|------|---------|
| GET | `/api/docker/containers/json?all=true` | Docker container list (⚠️ `Names` normalized from array to string) |
| GET | `/api/docker/info` | Docker system info (ContainersRunning/Paused/Stopped, NCPU, MemTotal, Images, KernelVersion, ServerVersion, OperatingSystem) |
| GET | `/api/docker/system` | `{version, apiVersion, containers, images, memoryTotal, cpus}` — aggregate Docker info + stats for all containers |
| GET | `/api/docker/version` | `{ Version: string }` |
| GET | `/api/docker/stats` | `{stats: [{id, name, state, cpu_percent, memory_usage, memory_limit, memory_percent, network_rx, network_tx, pids}]}` — live per-container CPU/mem/network |
| POST | `/api/docker/containers/:id/:action` | `{ ok: true }` — action: `start`, `stop`, `restart`, `remove` |

**`Names` normalization — CRITICAL:** Docker API returns `Names` as `string[]` (e.g. `["/agent-os"]`). The frontend calls `c.Names.replace(/^\//, "")` expecting a `string`. This causes `a.Names.replace is not a function` at runtime.

**Fix in backend** — normalize before returning:
```typescript
const normalized = containers.map(c => ({ ...c, Names: c.Names?.[0] || c.Names?.join(',') || '' }));
res.json(normalized);
```

**Symptom:** Dashboard shows "App Error — a.Names.replace is not a function" then blank screen on the Containers page.

### Status
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/status` | `StatusResponse` (active_sessions, gateway_*, version, config_path, etc.) |

### Sessions
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/sessions?limit=N&offset=N` | `{ sessions: SessionInfo[], total, limit, offset }` |
| DELETE | `/api/sessions/:id` | `{ ok: boolean }` |
| GET | `/api/sessions/:id/messages` | `{ session_id, messages: SessionMessage[] }` |
| GET | `/api/sessions/search?q=` | `{ results: SessionInfo[], total }` |

**Shape fix (2026-05-09):** Changed from `{sessions: [...]}` to `{results: [...]}` to match frontend `SessionSearchResponse` type.

### Logs
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/logs?lines=N&level=ALL&component=all` | `{ file, lines: string[] }` |

### Analytics
| Method | Path | Response |
|--------|------|---------|
| GET | `/api/analytics/usage?days=N` | `{total_tokens, total_sessions, daily:[{day, input_tokens, output_tokens, estimated_cost, sessions, api_calls}], by_model:[{model, input_tokens, output_tokens, estimated_cost, sessions}]}` |
| GET | `/api/analytics/models?days=N` | `{models:[{model, input_tokens, output_tokens, estimated_cost, sessions, message_count}]}` |

Note: `daily[].day` is a full JS date string. `analytics/usage` returns `daily[]` + `by_model[]`; `analytics/models` returns `models[]` with `message_count`. See `references/analytics-endpoints.md` for full verified shapes.

### Config
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/config` | `Record<string, unknown>` |
| PUT | `/api/config` | `{ ok: boolean }` |
| GET | `/api/config/defaults` | `Record<string, unknown>` |
| GET | `/api/config/schema` | `{ fields, category_order }` |
| GET | `/api/config/raw` | `{ yaml: string }` |
| PUT | `/api/config/raw` | `{ ok: boolean }` |

### Model
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/model/info` | `ModelInfoResponse` — flat `{model, provider, capabilities}` |

**Shape fix (2026-05-09):** Was `{current: {model, provider, capabilities}}`, flattened to match frontend expectations.
| GET | `/api/model/options` | `ModelOptionsResponse` |
| GET | `/api/model/auxiliary` | `AuxiliaryModelsResponse` |
| POST | `/api/model/set` | `{ ok: boolean }` |

### Env
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/env` | `Record<string, EnvVarInfo>` |
| PUT | `/api/env` | `{ ok: boolean }` |
| DELETE | `/api/env` | `{ ok: boolean }` |
| POST | `/api/env/reveal` | `{ key: string; value: string }` |

### Cron Jobs
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/cron/jobs` | `CronJob[]` |
| POST | `/api/cron/jobs` | `CronJob` |

**Shape fix (2026-05-09):** Now accepts frontend field names `{prompt, schedule, name, deliver}`. Maps `schedule` → `schedule_expr` internally.
| POST | `/api/cron/jobs/:id/pause` | `{ ok: boolean }` |
| POST | `/api/cron/jobs/:id/resume` | `{ ok: boolean }` |
| POST | `/api/cron/jobs/:id/trigger` | `{ ok: boolean }` |
| DELETE | `/api/cron/jobs/:id` | `{ ok: boolean }` |

### Profiles
| Method | Path | Response |
|--------|------|---------|
| GET | `/api/profiles` | `{ profiles: [{name, path, is_default, model, provider, has_env, skill_count}] }` |
| POST | `/api/profiles` | `{ ok: boolean; name, path }` |
| PATCH | `/api/profiles/:name` | `ProfileInfo` |
| DELETE | `/api/profiles/:name` | `{ ok: boolean }` |
| GET | `/api/profiles/:name/setup-command` | `{ command: string }` |
| GET | `/api/profiles/:name/soul` | `{ content: string; exists: boolean }` — reads from DB (006_profiles_soul.sql) |
| PUT | `/api/profiles/:name/soul` | `{ ok: boolean }` — writes `soul` column to DB (006_profiles_soul.sql) |

### Skills
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/skills` | `SkillInfo[]` |
| PUT | `/api/skills/toggle` | `{ ok: boolean }` |

### Toolsets
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/tools/toolsets` | `ToolsetInfo[]` |

### OAuth Providers
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/providers/oauth` | `{ providers: [] }` |
| DELETE | `/api/providers/oauth/:providerId` | `{ ok: boolean; provider }` |
| POST | `/api/providers/oauth/:providerId/start` | `{ auth_url: string }` |
| POST | `/api/providers/oauth/:providerId/submit` | `{ ok: boolean; provider }` |
| GET | `/api/providers/oauth/:providerId/poll/:sessionId` | `{ status, provider }` |
| DELETE | `/api/providers/oauth/sessions/:sessionId` | `{ ok: boolean }` |

### Gateway / Actions
| Method | Path | Response |
|--------|------|----------|
| POST | `/api/gateway/restart` | `{ name: string; ok: boolean; pid: number }` |
| POST | `/api/hermes/update` | `{ name: string; ok: boolean; pid: number }` |
| GET | `/api/actions/:name/status` | `{ name, running, exit_code, lines, pid }` |

### Dashboard Plugins
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/dashboard/plugins` | `PluginManifestResponse[]` |
| POST | `/api/dashboard/plugins/rescan` | `{ ok: boolean; count: number }` |

### Dashboard Themes
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/dashboard/themes` | `{ themes: Theme[]; current: string }` |
| PUT | `/api/dashboard/theme` | `{ ok: boolean; theme: string }` |

### Agent / Nanobot Chat
| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/agent/chat` | `{"text": string, "stream"?: boolean, "session_id"?: string}` | SSE stream or JSON ChatCompletion |

**Non-streaming** (`stream=false`): Full JSON response `{id, choices: [{message: {content}}]}`.
**Streaming** (`stream=true`): SSE with `data: {...}` prefix per chunk, terminates with `data: [DONE]`.

Backend proxies to nanobot at `http://nanobot:8900/v1/chat/completions` with OpenAI-format JSON body (`{messages: [{role: "user", content: text}], stream}`). Nanobot must be reachable from backend container via Docker DNS. Handles AbortController for client disconnect.

### CasaOS Webhook
| Method | Path | Request Body | Response |
|--------|------|-------------|----------|
| POST | `/api/webhooks/casaos` | `{"type": "...", "name": "...", "state": "...", "timestamp": "..."}` | `{"received": true, "event_type": "...", "timestamp": "..."}` |

**Bug to avoid:** `ON CONNECTION LOSS TO POSTGRES DO NOTHING` is not valid PostgreSQL — causes `syntax error at or near "CONNECTION"`. Use plain `INSERT INTO aie_events (session_id, type, data) VALUES (NULL, $1, $2)`.

### Events (Agent Observability)
| Method | Path | Request Body | Response |
|--------|------|-------------|----------|
| POST | `/api/events/agent` | `{"session_key": string, "event": object}` | `{"received": true, "event_type": "...", "session_key": "..."}` |

Resolves `session_id` via nanobot API before INSERT into `aie_events`.

### Deploy Webhook
| Method | Path | Request Body | Response |
|--------|------|-------------|----------|
| POST | `/api/deploy` | Plain text (deploy token) | `{"ok": true, "containers_restarted": N, "deployed_at": "..."}` |

Protected by `DEPLOY_TOKEN` env var — returns 401 if missing, 403 if wrong token. Uses dockerode to pull latest from GHCR and restart all agent-os containers (except postgres). See `references/deploy-webhook.md` for full implementation details.

### Agent Config (2026-05-07)
| Method | Path | Response |
|--------|------|---------|
| GET | `/api/agent/config` | `{agents: {defaults: {provider, model, temperature, max_tokens, timezone}}}` |

Reads `/root/.nanobot/config.json` (mounted into backend container). Redacts `api_key` fields. Requires `/home/sean/.nanobot:/root/.nanobot:ro` volume mount in compose.

### Events Recent (2026-05-07)
| Method | Path | Response |
|--------|------|---------|
| GET | `/api/events/recent?limit=N` | `{events: [{id, session, type, ts, name, data}]}` |

Returns last N events from `aie_events` ordered by timestamp DESC. Powers the ObservabilityPage live timeline.

### File Browser (2026-05-07)
| Method | Path | Response |
|--------|------|---------|
| GET | `/api/files/*path` | `FileEntry[]` — dirs and files with name, type, size, mtime |
| GET | `/api/files/read/*path` | `{content, size, mtime}` — file contents (max 1MB) |

Path traversal protected. Allowed roots: `/opt/data`, `/home/sean`. Backend needs these mounted as volumes. Powers FileExplorerPage.

### Tunnel Status (2026-05-07)
| Method | Path | Response |
|--------|------|---------|
| GET | `/api/tunnel` | `{hostname, tunnel_id, connected}` |

Queries cloudflared container for tunnel status. Powers SettingsPage tunnel section.

### Sessions (with dashboard persistence)
| Method | Path | Request Body | Response |
|--------|------|-------------|----------|
| GET | `/api/sessions?limit=N&offset=N` | — | `{sessions: [{id, title, created_at, last_active, message_count, preview}], total, limit, offset}` |
| POST | `/api/sessions` | `{"title": string}` | `{id, title, created_at}` |
| DELETE | `/api/sessions/:id` | — | `{ok: boolean}` |
| GET | `/api/sessions/:id/messages` | — | `{session_id, messages: [{id, role, content, created_at}]}` |

`message_count` is from `COUNT(dashboard_messages.id)` LEFT JOIN. `preview` is first 120 chars of the last user message. `last_active` is an alias of `updated_at`. Multi-turn context: prior messages are loaded (up to 20) and prepended to nanobot requests.

## Common Mistakes

- `GET /api/gateway/restart` → returns HTML (SPA fallback catches it). Must be `POST`
- `POST /api/skills/toggle` → returns HTML. Must be `PUT`
- Any route returning HTML means the route is missing from `backend/src/index.ts` or the compiled `dist/index.js`
- **Container dist path**: `/app/apps/dashboard/backend/dist/index.js` (the `apps/` prefix is required inside the container)

## Backend Crash Patterns

### PostgreSQL FK Violation → Process Exit (CRITICAL)

When the backend proxies a chat request to nanobot, it then tries to INSERT the user's message into `dashboard_messages`. This table has a FK constraint: `dashboard_messages_session_id_fkey` references `dashboard_sessions(id)`.

**Crash path**: Client passes `session_id` in the request body → backend uses that `session_id` directly → tries to INSERT user message → FK violation → PostgreSQL error → backend process **exits** (uncaught exception).

**Symptom**: `curl` returns `Empty reply from server` (HTTP 000). Backend container restarts immediately.

**Root cause**: When `session_id` is provided by the client, the old code only created a `dashboard_sessions` row when `!sid` (i.e., when the backend auto-generated the session ID). Client-provided session IDs were assumed to already exist.

**Fix**: Always run the session INSERT before inserting messages, for both auto-generated and client-provided session IDs:
```typescript
// Always ensure the session row exists before inserting messages
await pgQuery(
  'INSERT INTO dashboard_sessions (id, title) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING',
  [sid, sid === session_id ? `Chat ${new Date().toISOString().slice(0, 16).replace('T', ' ')}` : text.slice(0, 60) + '…'],
);
```

### Socket Exhaustion Under Concurrent Chat Load

Node.js HTTP agent defaults to `maxSockets: 5`. Under 5+ concurrent `/api/agent/chat` requests, additional requests queue and can timeout or cause `socket hang up` errors.

**Fix**: Raise global agent limit and add AbortController timeout:
```typescript
import http from 'http';
http.globalAgent.maxSockets = 50;

async function fetchWithTimeout(url: string, init?: RequestInit, timeoutMs = 60_000): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...init, signal: controller.signal });
    clearTimeout(timer);
    return res;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}
```

**Note**: Node.js `RequestInit` does NOT support the `agent` property (TypeScript error TS2769). Use `http.globalAgent.maxSockets` instead of passing a custom agent.

### Backend Crashes Under Concurrent Request Load

Even with socket fixes, a backend under heavy concurrent load from multiple `/api/agent/chat` requests (each blocking on nanobot's LLM inference) can exhaust memory and OOM. Keep an eye on `docker stats` memory usage. If backend memory climbs toward `mem_limit: 1g`, it may become unstable.

**Recovery**: `docker compose up -d --force-recreate backend`
