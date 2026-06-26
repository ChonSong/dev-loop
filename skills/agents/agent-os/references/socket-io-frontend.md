# Socket.IO Frontend Integration (2026-05-07)

## Overview

The frontend uses Socket.IO (`socket.io-client`) for real-time dashboard updates. A single shared connection is created in `src/lib/socket.ts` and exported as singleton hooks.

## Source: `apps/dashboard/frontend/src/lib/socket.ts`

```typescript
import { io, type Socket } from "socket.io-client";

export const socket: Socket = io("/", {
  path: "/socket.io/",
  transports: ["polling", "websocket"],
  autoConnect: false,
});

socket.connect();

export function onRealtimeEvent(cb: (event: unknown) => void) {
  const handler = (ev: unknown) => cb(ev);
  socket.on("events", handler);
  return () => socket.off("events", handler);
}

export function onCronUpdate(cb: () => void) {
  const handler = () => cb();
  socket.on("cron:updated", handler);
  return () => socket.off("cron:updated", handler);
}
```

## Backend Events

Backend (`apps/dashboard/backend/src/index.ts`) broadcasts:
- `io.emit('events', event)` — after every CasaOS webhook INSERT into `aie_events`
- `io.emit('cron:updated')` — after every cron mutation (create, pause, resume, delete, trigger)

## Usage in Pages

### ObservabilityPage (replaces 30s polling)
```typescript
useEffect(() => {
  load();
  const unsubEvent = onRealtimeEvent((ev) => {
    setRecentEvents(prev => [ev as Event, ...prev].slice(0, 50));
  });
  return unsubEvent;
}, [load]);
```

### CronPage (replaces manual refresh)
```typescript
useEffect(() => {
  loadJobs();
  const unsub = onCronUpdate(() => loadJobs());
  return unsub;
}, [loadJobs]);
```

## Cloudflare Limitation

Cloudflare free-tier blocks external WebSocket connections (HTTP 403 `error code: 1010`). This only affects clients OUTSIDE the LAN. Inside Docker network (`localhost:3001`), Socket.IO works fine. Frontend gracefully degrades to HTTP polling if Socket.IO fails — no user-visible error.
