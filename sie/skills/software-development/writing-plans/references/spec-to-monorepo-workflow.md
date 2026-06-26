# Spec-to-Monorepo Build Workflow

## When to Use
When a user provides a detailed spec and asks to build a new monorepo from it.

## Process

### Phase 1: Ground the Spec in Reality
1. **Explore every referenced repo** — check actual dependencies, entry points, protocols
2. **Validate architectural claims** — does the repo actually work the way the spec says?
3. **Identify spec-to-reality gaps** — report discrepancies and adapt the design
4. **Design-tree interrogation** — for ambiguous decisions, walk the tree one decision at a time with recommended answers

### Phase 2: Lock Decisions
- Present one decision at a time with your recommended answer
- If user says "you decide", lock it and move on immediately
- Resolve dependencies between decisions before moving forward

### Phase 3: Build Incrementally
- Start with `go mod` + directory structure + README
- Add one package at a time, commit after each
- Wire packages together before moving to the next layer
- Push after every meaningful increment (user may be interrupted)

### Phase 4: Frontend Integration
- Set up build toolchain (Vite, Svelte, etc.)
- Wire frontend to backend incrementally
- Add visual feedback (border states, connection status) before polish

## Key Patterns

### Go Backend Structure
```
backend/
├── cmd/server/main.go      # Entry point
├── ws/                     # WebSocket multiplexer
├── pty/                    # PTY supervisor
├── state/                  # State management
├── security/               # Permission model
├── audio/                  # External service bridges
└── telemetry/              # Logging/telemetry
```

### Svelte Frontend Structure
```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── svelte.config.js
└── src/
    ├── main.ts
    ├── App.svelte
    ├── app.css
    ├── stores/             # WebSocket store, state
    └── components/         # Terminal, tiles, etc.
```

### Deployment
```
deploy/
├── docker-compose.yml
└── Caddyfile
```

## Parallel Track Delegation (After PLAN.md)

Once the PLAN.md is written and the spec is grounded, delegate 3-6 parallel tracks:

1. Each track owns **exclusive, non-overlapping file sets**
2. Dispatch simultaneously via `delegate_task` with full context
3. Each track pushes commits independently
4. Verify `go build ./...` after all tracks complete

**Typical track split for Agent-OS-style monorepo:**
- Track 1: Backend Go packages (layout, security, telemetry)
- Track 2: Frontend Svelte components + stores
- Track 3: Integration (multiplexer wiring, deploy, CI, Makefile)

**Pitfall: Heavy dependencies cause timeouts.** Monaco editor, large Node modules, or ML packages can timeout a subagent at 600s. If the first attempt times out, retry with the heavy dependency removed from scope. Build it separately later.

**Escaping Gotcha:** When writing file content via Python's `execute_code`, string escaping is a nightmare for complex files (especially with quotes in Svelte/JS/Go). **Use `write_file` directly** — it handles escaping cleanly.

## Push Discipline
Commit after every meaningful increment:
1. Initial skeleton (go.mod, directories, README)
2. Each new package (ws/, pty/, state/, etc.)
3. Each frontend component
4. Wiring changes (connecting packages together)
5. Deploy config
