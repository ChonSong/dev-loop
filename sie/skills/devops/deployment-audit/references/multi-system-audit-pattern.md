# Multi-System Audit Pattern

Use when the user asks for a comprehensive state review across multiple projects, services, and systems — not just a single deployment check.

## Pattern Steps

### 1. Inventory Phase

List all known systems from:
- Cron job list (16+ jobs → discover which services they target)
- MEMORY.md active projects section
- REORGANIZATION_LOG.md for archived/moved projects
- Host systemd service list

### 2. Parallel Health Check

For each system, collect these data points in one SSH call:

```bash
# Model check — covers 80% of what you need
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "
echo '=== Frontend ==='
curl -sL --connect-timeout 3 http://localhost:PORT/ | grep -o '<title>[^<]*</title>' || echo 'DOWN'
echo ''
echo '=== API ==='
curl -s --connect-timeout 3 http://localhost:API_PORT/api/v1/health || echo 'API DOWN'
echo ''
echo '=== Systemd ==='
systemctl --user --no-pager is-active SERVICE1 SERVICE2 2>/dev/null || echo 'No systemd'
"
```

### 3. Cross-Reference Phase

Compare what's running against what SHOULD be running:

| Check | Purpose |
|-------|---------|
| Title tag | Confirms the right app, not a different one on the same port |
| API health | Confirms backend is responding with correct data |
| Systemd status | Confirms supervisor is managing the service |
| Git log | Confirms the running code is recent |
| Cron job status | Confirms scheduled maintenance is working |

### 4. Gap Analysis

For each system, classify:
- ✅ **Healthy** — all checks pass, systemd-managed
- 🟡 **Degraded** — running but with known issues (mock data, stale build, missing features)
- ❌ **Dead** — not running at all, no supervisor
- ❓ **Unknown** — can't verify from current context

### 5. Prioritization

Rank gaps by impact:
1. **Dead systems** (no process, no supervisor) — highest priority
2. **Silent failures** (service runs but serves wrong content) — critical because no alarm fires
3. **Degraded with known workarounds** — medium
4. **Waste** (redundant cron jobs, excessive frequency) — low but easy wins

## When to Use

- User asks "what's the current state of everything"
- Multi-project handoff or context restoration
- Before making infrastructure changes (baseline + priorities)
- After long gaps between sessions (2+ days)
