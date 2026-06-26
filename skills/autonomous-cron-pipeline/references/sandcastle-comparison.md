# Sandcastle vs Persistent Phase Engine — Session Notes (May 12, 2026)

## Sandcastle Overview
- **Repo**: github.com/mattpocock/sandcastle
- **Stars**: 3K+
- **Language**: TypeScript
- **Purpose**: Orchestrate AI coding agents in isolated Docker containers with git worktrees
- **Agent Support**: Claude Code, Codex (pluggable providers)
- **Key Features**:
  - `sandcastle.run()` spawns agent in sandboxed container
  - Git worktree isolation → agents work on branches, merge back when done
  - Supports parallel agents, review pipelines, CI integration
  - Lifecycle hooks (`onSandboxReady`, `onWorktreeReady`)
  - Provider-agnostic (Docker, Podman, Vercel)

## Comparison Matrix

| Dimension | Sandcastle | Persistent Phase Engine |
|-----------|-----------|------------------------|
| **Language** | TypeScript | Python + cron |
| **Isolation** | Docker containers + git worktrees | Cron job sessions (no container isolation) |
| **Branching** | First-class git worktrees + merge-back | Direct commits to main |
| **Parallelism** | Native — `Promise.all([run(), run(), run()])` | Sequential via cron scheduling |
| **State persistence** | Git branches + worktrees survive failures | JSON tracker + checkpoint files on disk |
| **Agent support** | Claude Code, Codex (pluggable) | Hermes Agent (this system) |
| **Failure handling** | Preserves worktree on failure, manual cleanup | Writes error state, stops safely |
| **Scope** | Library for orchestrating external agents | Built-in to the agent itself |
| **Maturity** | Production-ready, 3K+ stars | Custom-built May 2026 |

## Key Differences

### Sandcastle is better at:
- **Isolation** — Each agent runs in its own Docker container. No shared filesystem, no session pollution.
- **Branching** — Git worktrees are first-class. Agents can't corrupt `main` — changes only merge when verified.
- **Parallelism** — True parallel execution with proper merge conflict resolution.
- **Professional workflows** — CI integration, review pipelines, backlog management.

### Persistent Phase Engine is better at:
- **Simplicity** — No Docker containers, no worktrees, no merge conflicts. Just cron jobs that commit to main.
- **Self-contained** — Built into the agent. No external tool installation needed.
- **State tracking** — JSON tracker + checkpoints are explicit and human-readable. Sandcastle relies on git branches (implicit state).
- **Cost** — No container overhead. Cron jobs reuse the existing agent session.

## Docker Socket Discovery

During this session, we discovered:
```bash
docker info  # Works from container
docker ps    # Shows host containers
docker run --rm hello-world  # ✅ Works
```

The Docker socket at `/var/run/docker.sock` is mounted into the hermes-agent container. This means:
- We CAN run Docker commands from inside the container
- We CAN create isolated containers for builds/tests
- We do NOT need Docker-in-Docker
- The host's Docker daemon is accessible

## Why Not Switch to Sandcastle

1. **Agent mismatch** — Sandcastle expects Claude Code/Codex, not Hermes Agent
2. **Language mismatch** — Sandcastle is TypeScript, our system is Python
3. **Integration overhead** — Would need custom agent provider, Docker images, git worktree logic
4. **No guaranteed benefit** — Cron pipeline works, commits after each phase, reports to Discord
5. **Docker isolation available** — Can run builds/tests in containers without Sandcastle

## When to Use What

| Scenario | Recommended Approach |
|----------|---------------------|
| Single-agent large project | Persistent Phase Engine |
| Multi-agent parallel workflows | Sandcastle |
| Quick independent tasks | Chained cron jobs |
| Need Docker isolation per phase | Phase Engine + Docker containers for builds/tests |
| CI/CD integration | Sandcastle |
| Within Hermes ecosystem | Persistent Phase Engine |
