# Socket.IO Backend Events Reference

## ⚠️ Delegation Rule — Read This First

**Before delegating any Socket.IO frontend work to a subagent, verify the backend emits the event.**

A subagent (2026-05-07) wired `onContainerUpdate()` in `socket.ts` and updated `ContainerPage.tsx` — but the backend never emitted `docker:containers`. Live mode silently failed with no errors.

**Check before delegating:**
```bash
grep -n "\.emit\(" /opt/data/agent-os/apps/dashboard/backend/src/index.ts
```
If the event isn't listed, add the backend emission first, then delegate the frontend. Or delegate both together with explicit backend instructions.

## All Backend Socket.IO Events

Backend (`apps/dashboard/backend/src/index.ts`) emits these events to all connected clients:

| Event | Payload | Trigger |
|-------|---------|---------|
| `events` | `{ type, data, ts }` | Every CasaOS webhook INSERT into `aie_events` |
| `cron:updated` | (no payload) | After every cron mutation (create, pause, resume, delete, trigger) |
| `log` | `{ ts, level, component, msg }` | Real-time Docker container log lines, batched every 500ms |
| `docker:containers` | `{ containers: Container[], stats: Record<string,Stats> }` | Every 5s when at least one client is connected |

## docker:containers Event (Live Container Updates)

### Backend Implementation

The backend emits `docker:containers` every 5 seconds when at least one Socket.IO client is connected:

```typescript
// apps/dashboard/backend/src/index.ts — io.on('connection') handler
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Start live log streams on first client connect
  if (io.engine.clientsCount === 1) {
    AGENT_CONTAINERS.forEach(name => startLogStream(name, io));
  }

  // Emit container snapshots every 5s to all connected clients
  const containerInterval = setInterval(async () => {
    try {
      const containers = await docker.listContainers({ all: true });
      const statsData = await Promise.all(
        containers.map(c => docker.getContainer(c.Id).stats({ stream: false }).catch(() => null))
      );
      const statsMap: Record<string, object> = {};
      statsData.forEach((s, i) => {
        if (!s) return;
        const name = containers[i].Names?.[0]?.replace(/^\//, '') ?? containers[i].Id.slice(0, 12);
        const cpu = s.cpu_stats?.cpu_usage?.total_usage ?? 0;
        const pre = s.precpu_stats?.cpu_usage?.total_usage ?? 0;
        const sys = s.cpu_stats?.system_cpu_usage ?? 1;
        const preSys = s.precpu_stats?.system_cpu_usage ?? 1;
        const cpuPercent = sys > 0 ? ((cpu - pre) / (sys - preSys)) * 100 : 0;
        statsMap[name] = {
          cpu_percent: +cpuPercent.toFixed(1),
          memory_usage: s.memory_stats?.usage ?? 0,
          memory_limit: s.memory_stats?.limit ?? 1,
          memory_percent: s.memory_stats?.limit
            ? +(s.memory_stats.usage / s.memory_stats.limit * 100).toFixed(1) : 0,
          network_rx: 0, network_tx: 0,
          pids: s.pids_stats?.current ?? 0,
        };
      });
      io.emit('docker:containers', {
        containers: containers.map(c => ({
          Id: c.Id, Names: c.Names, Image: c.Image,
          State: c.State, Status: c.Status, Ports: '',
        })),
        stats: statsMap,
      });
    } catch { /* ignore container fetch errors */ }
  }, 5000);

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
    if (io.engine.clientsCount === 0) clearInterval(containerInterval);
  });
});
```

**Note:** `container.stats({ stream: false })` uses `.then()` — see `references/dockerode-async-fix.md`.

### Frontend: socket.ts Interface

```typescript
// apps/dashboard/frontend/src/lib/socket.ts
export interface ContainerUpdate {
  containers: Array<{
    Id: string;
    Names: string;
    Image: string;
    State: string;
    Status: string;
    Ports: string;
  }>;
  stats: Record<string, {
    cpu_percent: number;
    memory_usage: number;
    memory_limit: number;
    memory_percent: number;
    network_rx: number;
    network_tx: number;
    pids: number;
  }>;
}

export function onContainerUpdate(cb: (update: ContainerUpdate) => void): () => void {
  socket.on("docker:containers", cb as (...args: unknown[]) => void);
  return () => socket.off("docker:containers", cb as (...args: unknown[]) => void);
}
```

### Frontend: ContainerPage Integration Pattern

```typescript
// apps/dashboard/frontend/src/pages/ContainerPage.tsx
import { onContainerUpdate, type ContainerUpdate } from "@/lib/socket";

function ContainerPage() {
  const [live, setLive] = useState(false);
  const [connected, setConnected] = useState(false);

  // Replace 5s setInterval with Socket.IO when live=true
  useEffect(() => {
    if (!live) {
      setConnected(false);
      return;
    }
    const unsubscribe = onContainerUpdate((update: ContainerUpdate) => {
      setContainers(update.containers);
      setStats(update.stats);
      setLoading(false);
      setConnected(true);
    });
    return unsubscribe;
  }, [live]);
}
```


