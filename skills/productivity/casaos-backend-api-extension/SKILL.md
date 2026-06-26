---
name: casaos-backend-api-extension
description: "Extend casaos-dashboard FastAPI backend (:8090) to add CasaOS event ingestion endpoint and SSE stream for everything-dashboard React frontend. Part of Track A (event backbone) for Casa frontend integration."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Python, FastAPI, CasaOS, SSE, Events]
    track: A
    project: casaos-dashboard
---

# FastAPI Backend Extension Plan — CasaOS Events + SSE for everything-dashboard

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add two endpoints to `casaos-dashboard/backend/main.py` that allow everything-dashboard React frontend to:
1. Receive CasaOS events from the webhook-emitter via HTTP POST
2. Stream those events to the React frontend via Server-Sent Events (SSE)

**Architecture:** The webhook-emitter (Go) calls `POST /api/events/casaos` on this FastAPI backend. The backend broadcasts the event to all active SSE clients connected to `GET /api/events/stream`.

**Existing codebase:** `ChonSong/casaos-dashboard/backend/main.py` (FastAPI on port 8090).

---

## Preconditions

- `casaos-dashboard` FastAPI backend already running on `localhost:8090`
- Webhook-emitter (Go) will call `POST /api/events/casaos` with CasaOS event JSON
- everything-dashboard React frontend will call `GET /api/events/stream` with `EventSource`

---

## Task 1: Add Event Models

**File:** `backend/main.py` — add imports and models (append before `run_cli` function)

**Step 1: Add imports**

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from collections import defaultdict
```

Note: If `sse-starlette` is not installed, add to requirements and install:
```bash
pip install sse-starlette
```

**Step 2: Add CasaOS event model**

```python
@dataclass
class CasaOSEvent:
    source_id: str
    name: str
    uuid: str
    properties: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict) -> "CasaOSEvent":
        return cls(
            source_id=d.get("sourceID", d.get("source_id", "")),
            name=d.get("name", ""),
            uuid=d.get("uuid", ""),
            properties=d.get("properties", {}),
            timestamp=d.get("timestamp"),
        )

    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "uuid": self.uuid,
            "properties": self.properties,
            "timestamp": self.timestamp or datetime.utcnow().isoformat() + "Z",
        }
```

---

## Task 2: Add In-Memory Event Broadcaster

**File:** `backend/main.py` — add after the models

**Step 1: Add a broadcaster**

```python
# In-memory broadcaster: maps event names to sets of asyncio Queues
# Each SSE client gets its own queue
class EventBroadcaster:
    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._all_events_queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._lock = asyncio.Lock()

    async def subscribe(self, event_name: str = "*") -> asyncio.Queue:
        """Subscribe to events. event_name="*" means all events."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[event_name].append(q)
        return q

    async def unsubscribe(self, event_name: str, q: asyncio.Queue):
        async with self._lock:
            if q in self._subscribers.get(event_name, []):
                self._subscribers[event_name].remove(q)

    async def publish(self, event: CasaOSEvent):
        """Publish an event to all matching subscribers."""
        # Publish to "all events" subscribers
        for q in self._subscribers.get("*", []):
            try:
                q.put_nowait(event.to_dict())
            except asyncio.QueueFull:
                pass
        # Publish to specific event subscribers
        for q in self._subscribers.get(event.name, []):
            try:
                q.put_nowait(event.to_dict())
            except asyncio.QueueFull:
                pass
        # Also put in the all-events queue
        try:
            self._all_events_queue.put_nowait(event.to_dict())
        except asyncio.QueueFull:
            pass

broadcaster = EventBroadcaster()
```

---

## Task 3: Add API Routes

**File:** `backend/main.py` — add after the broadcaster, before the `run_cli` function

**Step 1: POST /api/events/casaos — receive events from webhook-emitter**

```python
@app.post("/api/events/casaos")
async def receive_casaos_event(request: Request):
    """
    Called by the webhook-emitter (Go) when CasaOS events arrive.
    Body: CasaOS MessageBus event JSON.
    """
    body = await request.json()
    event = CasaOSEvent.from_dict(body)
    await broadcaster.publish(event)
    return {"ok": True, "event": event.name}
```

**Step 2: GET /api/events/stream — SSE endpoint for React frontend**

```python
@app.get("/api/events/stream")
async def events_stream(request: Request):
    """
    Server-Sent Events stream of CasaOS events.
    React frontend connects via: new EventSource('/api/events/stream')
    """
    async def event_generator():
        q = await broadcaster.subscribe("*")
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                event_data = await asyncio.wait_for(q.get(), timeout=30)
                yield {
                    "event": "message",
                    "data": json.dumps(event_data),
                }
        except asyncio.TimeoutError:
            # Send keepalive comment every 30s
            yield {"event": "ping", "comment": "keepalive"}
        finally:
            await broadcaster.unsubscribe("*", q)

    return EventSourceResponse(event_generator())
```

**Step 3: GET /api/events — list recent events (last 200)**

```python
# In-memory ring buffer of last 200 events
_recent_events: List[Dict] = []
_max_events = 200

@app.get("/api/events")
async def list_events():
    """Return last N events (for initial page load without SSE)."""
    return {"events": list(reversed(_recent_events))}

# Patch the broadcaster publish to also populate _recent_events
# Add to EventBroadcaster.publish():
#     _recent_events.append(event.to_dict())
#     if len(_recent_events) > _max_events:
#         _recent_events.pop(0)
```

Actually, modify the `publish` method to also update the ring buffer. Add this inside `EventBroadcaster.publish` before the `except` clauses:

```python
_recent_events.append(event.to_dict())
if len(_recent_events) > _max_events:
    _recent_events.pop(0)
```

---

## Task 4: Wire everything-dashboard React Frontend

**File to create:** `everything-dashboard/frontend/src/components/CasaOSEventFeed.tsx`

```tsx
import { useEffect, useRef, useState } from 'react'

interface CasaOSEvent {
  source_id: string
  name: string
  uuid: string
  properties: Record<string, unknown>
  timestamp: string
}

export function CasaOSEventFeed() {
  const [events, setEvents] = useState<CasaOSEvent[]>([])
  const [connected, setConnected] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const es = new EventSource('http://localhost:8090/api/events/stream')
    esRef.current = es

    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)

    es.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data) as CasaOSEvent
        setEvents(prev => {
          const next = [evt, ...prev]
          return next.length > 200 ? next.slice(0, 200) : next
        })
      } catch {}
    }

    return () => {
      es.close()
      setConnected(false)
    }
  }, [])

  return (
    <div className="event-feed">
      <div className="event-feed__header">
        <span>📡 CasaOS Events</span>
        <span className={connected ? 'connected' : 'disconnected'}>
          {connected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>
      <div className="event-feed__list">
        {events.length === 0 && <div className="event-feed__empty">Waiting for events...</div>}
        {events.map((evt, i) => (
          <div key={evt.uuid || i} className="event-item">
            <div className="event-item__name">{evt.name}</div>
            <div className="event-item__source">{evt.source_id}</div>
            <div className="event-item__time">
              {new Date(evt.timestamp).toLocaleTimeString()}
            </div>
            <pre className="event-item__props">{JSON.stringify(evt.properties, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**CSS (append to `index.css` or component-scoped):**
```css
.event-feed {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}
.event-feed__header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #e6edf3;
}
.event-feed__header .connected { color: #3fb950; }
.event-feed__header .disconnected { color: #f85149; }
.event-feed__list {
  max-height: 300px;
  overflow-y: auto;
}
.event-item {
  padding: 6px 0;
  border-bottom: 1px solid #21262d;
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } }
.event-item__name { color: #58a6ff; font-weight: 600; }
.event-item__source { color: #8b949e; font-size: 11px; }
.event-item__time { color: #484f58; font-size: 10px; }
.event-item__props { color: #7ee787; font-size: 10px; margin-top: 4px; }
```

**Wire into App.tsx routes:**
```tsx
import { CasaOSEventFeed } from './components/CasaOSEventFeed'
// Add route: <Route path="/events" element={<CasaOSEventFeed />} />
```

---

## Verification

```bash
# 1. Start the FastAPI backend
cd casaos-dashboard/backend
pip install sse-starlette
python main.py &
# Expected: [backend] CasaOS Agent Dashboard starting on :8090

# 2. Inject a test event (simulate webhook-emitter)
curl -X POST http://localhost:8090/api/events/casaos \
  -H "Content-Type: application/json" \
  -d '{"sourceID":"app-management","name":"app:installed","uuid":"test-123","properties":{"app_id":"test-app"},"timestamp":"2026-05-01T00:00:00Z"}'
# Expected: {"ok":true,"event":"app:installed"}

# 3. Check event list
curl http://localhost:8090/api/events
# Expected: {"events":[{"source_id":"app-management","name":"app:installed",...}]}

# 4. Check SSE stream (should hang, then return event after step 2)
curl -N http://localhost:8090/api/events/stream
# Expected: event:message\r\ndata:{"source_id":"app-management",...}
```

---

## Integration with everything-dashboard React

In `everything-dashboard/frontend/src/App.tsx`, add the EventFeed component:

```tsx
import { CasaOSEventFeed } from './components/CasaOSEventFeed'
```

And a route:
```tsx
<Route path="/events" element={<CasaOSEventFeed />} />
```

---

## Pitfalls

1. **CORS**: The FastAPI backend has `allow_origins=["*"]` — SSE from `localhost:3000` to `localhost:8090` will work without CORS issues.
2. **SSE reconnection**: React's `EventSource` auto-reconnects on drop. The broadcaster holds queues per subscriber — disconnected clients' queues will fill up and drop oldest events. This is fine for a live feed.
3. **Port mismatch**: everything-dashboard Express server runs on `:3001`. The React frontend calls `localhost:8090` directly for SSE — this works as long as CORS is open (it is).
4. **sse-starlette package**: Must be added to `requirements.txt` or `pyproject.toml` of the FastAPI backend. If it can't be installed, use thestdlib `asyncio` generator approach with `StreamingResponse` instead.
