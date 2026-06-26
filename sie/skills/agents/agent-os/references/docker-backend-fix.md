# Backend Stub → Production Fix

## The Three-Service Problem

The current container runs 3 separate processes via shell `&`:
```
nanobot serve --host 0.0.0.0 --port 8900 &
node /app/apps/dashboard/backend/dist/index.js &      # Express on 9120
npx serve /app/apps/dashboard/frontend/dist -l 8901   # Static on 8901
```

Problems:
1. **Port 8901 (frontend) is separate** — must be mapped independently in compose
2. **No proxy** — frontend (8901) can't reach backend (9120) without CORS
3. **Shell process supervision** — if Express crashes, `&` doesn't restart it
4. **Healthcheck complexity** — two different ports to check

## The Fix: Express Serves Everything on Port 9120

Modify `apps/dashboard/backend/src/index.ts`:

```typescript
import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();

app.use(cors());
app.use(express.static(path.join(__dirname, '../../frontend/dist')));

// API routes first
app.get('/api/docker/containers/json', ...);
app.post('/api/docker/containers/:id/:action', ...);
app.get('/api/system/uptime', ...);
// ... other routes matching frontend/src/lib/api.ts expectations

// SPA fallback (must be LAST)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../../frontend/dist/index.html'));
});

app.listen(9120, '0.0.0.0');
```

Then update Dockerfile CMD to remove the `npx serve` line entirely.

## Frontend API Callers (from src/lib/api.ts)

| Route | Used By |
|-------|---------|
| `GET /api/status` | StatusBar, App.tsx |
| `GET /api/containers/json` | ContainerPage |
| `POST /api/containers/:id/start\|stop\|restart` | ContainerPage actions |
| `GET /api/containers/:id/logs` | ContainerPage |
| `GET /api/sessions` | ChatPanel |
| `POST /api/sessions` | ChatPanel |
| `GET /api/cron/jobs` | CronPage |
| `POST /api/cron/jobs` | CronPage |
| `GET /api/env` | EnvPage |
| `PUT /api/config` | ConfigPage |
| `GET/POST /api/profiles` | ProfilePage |
| `GET /api/skills` | SkillsPage |
| `GET /api/plugins` | PluginPage |
| `GET /api/analytics/*` | AnalyticsPage |

## Dockerode Dynamic Import Fix

```typescript
// WRONG — may not resolve at runtime in Docker
import('dockerode')

// RIGHT — ensure the module exists first
let Docker: typeof import('dockerode');
try {
  Docker = (await import('dockerode')).default;
} catch {
  Docker = await import('dockerode');
}
const docker = new Docker({ socketPath: '/var/run/docker.sock' });
```

Also ensure `COPY --from=ts-build /app/node_modules /app/node_modules` is in the Dockerfile runtime stage, AND that `package.json` / `package-lock.json` are copied so npm can resolve workspace hoisting at runtime.

## Docker Volume Mount Modes — `:ro` Silently Breaks Writes

**Symptom:** A volume appears to be mounted correctly in `docker inspect`, but writes to the mount point fail with `EROFS` (read-only filesystem) — even though the mount mode shows `:rw` in docker-compose.yml.

**Root cause:** The `:ro` suffix in docker-compose volume declarations marks the mount as read-only from the container's perspective. If multiple services share the same volume and one declares `:ro`, Docker enforces read-only at the kernel level. If the docker-compose.yml was manually edited and only one `:ro` → `:rw` change was made, the change must be verified in the actual deployed containers.

**Example:** The nanobot config volume was mounted as `/home/sean/.nanobot:/root/.nanobot:ro` for both `backend` and `nanobot` services. The backend's PUT `/api/config` handler tried to write to `/root/.nanobot/config.json` and got `EROFS` — the error was only visible in backend logs, not in Docker's compose output.

**Fix — verify both services and force recreate:**
```bash
# Check actual mount modes on LIVE containers:
docker inspect agent-os-backend --format '{{json .Mounts}}' | python3 -c \
  'import json,sys; [print(m["Source"], "->", m["Destination"], m["Mode"]) for m in json.load(sys.stdin) if "/nanobot" in m["Destination"]]'

docker inspect agent-os-nanobot --format '{{json .Mounts}}' | python3 -c \
  'import json,sys; [print(m["Source"], "->", m["Destination"], m["Mode"]) for m in json.load(sys.stdin) if "/nanobot" in m["Destination"]]'

# If either shows :ro, change in docker-compose.yml:
# WRONG (only changes one occurrence):
sed -i 's|:nanobot:ro|:nanobot:rw|g' docker-compose.yml

# RIGHT (change ALL nanobot volume references):
sed -i 's|/home/sean/.nanobot:/root/.nanobot:ro|/home/sean/.nanobot:/root/.nanobot:rw|g' docker-compose.yml

# Force containers to use new volume modes (volume mounts are not updated on docker compose up):
docker compose -f docker-compose.yml up -d --force-recreate backend nanobot
```

**Prevention:** After any docker-compose.yml volume change, always force recreate AND verify with `docker inspect`. Docker does not warn when a `:ro` volume fails to mount as read-write — it silently succeeds with the read-only constraint.
