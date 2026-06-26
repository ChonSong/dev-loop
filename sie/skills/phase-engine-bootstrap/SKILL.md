---
name: phase-engine-bootstrap
category: devops
description: Phase 0 environment detection and toolchain routing for autonomous cron Phase Engines.
tags: [cron, phase-engine, environment, bootstrap]
---

# Phase Engine Bootstrap

Load this skill at the START of any Phase Engine cron job prompt. It provides environment-aware toolchain routing so autonomous jobs don't fail on missing tools.

## Phase 0: Environment Detection

Every Phase Engine run MUST start with these checks before attempting any work:

```bash
# 1. Container vs Host detection
echo "=== Environment ==="
echo "Container: $(hostname)"
which go 2>/dev/null && echo "Go: $(go version)" || echo "Go: NOT in container PATH"
which node 2>/dev/null && echo "Node: $(node --version)" || echo "Node: missing"
which python3 2>/dev/null && echo "Python: $(python3 --version 2>&1)" || echo "Python: missing"
which git 2>/dev/null && echo "Git: $(git --version)" || echo "Git: missing"
ls -d /home/sean/.cache/ms-playwright 2>/dev/null && echo "Playwright browsers: on host" || echo "Playwright: not found"
```

## Toolchain Routing Rules

| Tool | Container | Host (SSH) |
|------|-----------|------------|
| `go` | ❌ NOT available | ✅ `/usr/bin/go` (v1.25.5) |
| `node` | ✅ `/home/hermeswebui/.hermes/home/.local/bin/node` (v22) | ✅ Available |
| `python3` | ✅ `/usr/local/bin/python3` (v3.12) | ✅ `/usr/bin/python3` |
| `git` | ✅ `/usr/bin/git` | ✅ Available |
| Playwright browsers | ❌ Not cached | ✅ `/home/sean/.cache/ms-playwright` |
| `docker` | ❌ Not in container | ✅ Available on host |
| `npm` | ✅ Via Node | ✅ Available |

## SSH Command Pattern

When Go, Docker, Playwright, or system-level tools are needed:

```bash
SSH_KEY="/home/hermeswebui/.hermes/container_key"
SSH_HOST="sean@172.19.0.1"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10"

# Single command
ssh $SSH_OPTS $SSH_HOST "go version && cd /path/to/repo && go build"

# Complex multi-step (use heredoc)
ssh $SSH_OPTS $SSH_HOST bash << 'EOF'
  cd /path/to/repo
  go build ./...
  go test ./...
EOF
```

## Path Verification

Before any file operations, verify the target exists:

```bash
if [ ! -d "/path/to/workspace" ]; then
  echo "ERROR: workspace not found. Check: git clone status, SSH mount points"
  echo "Common locations: /workspace, /home/hermeswebui/.hermes/, /tmp/"
  exit 1
fi
```

## Git State Check

Always verify git state before making changes:

```bash
cd /path/to/repo
git status --short
git log --oneline -3
echo "Branch: $(git branch --show-current)"
```

## Phase Marker Protocol

Use `/tmp/phase-N-*.json` markers for persistent state across cron ticks:

```bash
STATE_DIR="/tmp"
# Before starting: check for existing markers
ls $STATE_DIR/phase-*-DONE.json 2>/dev/null
# On completion:
echo '{"phase": "N", "status": "DONE", "completed_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' > $STATE_DIR/phase-N-DONE.json
# On failure:
echo '{"phase": "N", "status": "FAILED", "error": "description"}' > $STATE_DIR/phase-N.error
```

## Anti-Patterns

- NEVER assume Go is available in container — always route through SSH
- NEVER use `deliver: "all"` — it silently drops. Use `deliver: "origin"` or `deliver: "local"`
- NEVER assume `/opt/data/` exists — verify paths first
- NEVER attempt Playwright E2E tests in container without browser cache — route to host
- NEVER overwrite phase markers without reading existing ones first
- If 3+ consecutive cron ticks fail the same way, pause and escalate to user
