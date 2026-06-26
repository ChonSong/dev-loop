# n8n Deployment on TrueNAS SCALE

## Context
TrueNAS SCALE 25.10+ runs k3s (Kubernetes) under the hood. Apps deploy via IX-Charts (Helm-based), not Docker Compose. n8n is not in the default catalog, so it must be deployed as a **Custom App**.

## Option A: TrueNAS UI (Recommended for one-offs)

1. **Initialize Apps** (if not done):
   - Apps → Settings → Choose Pool → select your data pool
   - Settings → Enable App

2. **Create dataset for persistence**:
   - Storage → Create Dataset → Name: `tank/apps/n8n`
   - Share Type: APPS

3. **Deploy Custom App**:
   - Apps → Discover Apps → Custom App
   - Image: `n8nio/n8n:latest`
   - Container Port: `5678`
   - Host Port: `5678` (or whatever you want externally)
   - Add Volume:
     - Host Path: `/mnt/tank/apps/n8n`
     - Mount Path: `/home/node/.n8n`
   - Environment Variables:
     - `WEBHOOK_URL` = `http://your-truenas-ip:5678/` (or your domain)
     - `N8N_BASIC_AUTH_ACTIVE` = `true`
     - `N8N_BASIC_AUTH_USER` = `admin`
     - `N8N_BASIC_AUTH_PASSWORD` = `<strong-password>`
     - `TZ` = `Etc/UTC` (or your timezone)

4. **Access**: `http://truenas-ip:5678`

## Option B: WebSocket API (For Automation)

**Note**: The `app.create` middleware method expects an IX-Chart payload which is complex and poorly documented. For reliable automation, use the UI or a pre-built Helm chart. If you must automate:

```python
# 1. Ensure apps pool is set
call("app.pool_config", [])  # Check current pool

# 2. Create dataset
call("pool.dataset.create", [{
    "name": "tank/apps/n8n",
    "type": "FILESYSTEM",
    "share_type": "APPS"
}])

# 3. Query available apps (should show custom app capability)
call("app.available", [])

# 4. Deploy — payload varies by TrueNAS version
# See TrueNAS middleware docs for app.create schema
```

## Hermes Integration

### Webhook Endpoint Pattern
```
POST http://truenas-ip:5678/webhook/<workflow-id>
Content-Type: application/json

{"message": "Draft this week's LinkedIn post", "pillar": "technical"}
```

### Cron Jobs (Hermes)
```yaml
# Weekly content reminder
- schedule: "0 9 * * 1"
- prompt: "Call webhook http://truenas-ip:5678/webhook/linkedin-draft with weekly content request"

# Monthly network audit
- schedule: "0 10 1 * *"
- prompt: "Call webhook http://truenas-ip:5678/webhook/linkedin-audit for network review"
```

## Troubleshooting

- **Port already in use**: TrueNAS itself uses 80/443. Use a high port (5678 is safe).
- **Permission denied on volume**: Ensure the dataset is created with `share_type: APPS` and the n8n container runs as user `node` (UID 1000).
- **Webhook URL mismatch**: If n8n shows "Webhook not found", the `WEBHOOK_URL` env var doesn't match the actual access URL.
- **Apps not starting**: Check **Apps → Installed Apps → n8n → Logs** in TrueNAS UI.
