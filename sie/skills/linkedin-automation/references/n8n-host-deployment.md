# n8n Host Deployment (Fallback When TrueNAS Docker Fails)

When TrueNAS SCALE Docker is unavailable (e.g., VirtualBox NAT interface bug → `LINK_STATE_UNKNOWN`), deploy n8n on the host machine instead and use TrueNAS for storage via SMB/NFS.

## Docker Compose (Host)

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    volumes:
      - ~/n8n-data:/home/node/.n8n
    environment:
      - TZ=Etc/UTC
      - WEBHOOK_URL=http://172.19.0.1:5678/
    restart: unless-stopped
```

Deploy: `docker compose -f /tmp/n8n-compose.yml up -d`

## Owner Setup (First Run)

n8n requires owner account creation before API access:

```bash
# Create owner via REST API (no auth required on first boot)
curl -s -X POST http://172.19.0.1:5678/rest/owner/setup \
  -H "Content-Type: application/json" \
  -d '{"email":"hermes@hermes.local","password":"<strong-password>","firstName":"Hermes","lastName":"Agent"}'
```

After owner setup, authentication is cookie-based:

```bash
# Login to get session cookie
curl -s -X POST http://172.19.0.1:5678/rest/login \
  -H "Content-Type: application/json" \
  -c /tmp/n8n-cookies.txt \
  -d '{"emailOrLdapLoginId":"hermes@hermes.local","password":"<strong-password>"}'

# Use cookie for subsequent API calls
curl -s -H "Content-Type: application/json" -b /tmp/n8n-cookies.txt \
  http://172.19.0.1:5678/rest/workflows
```

**Pitfall**: The login field is `emailOrLdapLoginId`, not `email`.

## Workflow Import via CLI

The n8n CLI inside the container can import workflows:

```bash
# Copy workflow JSON to container
docker cp /tmp/linkedin_workflow.json n8n:/tmp/

# Import (requires 'id' field as UUID)
docker exec n8n n8n import:workflow --input=/tmp/linkedin_workflow.json
```

**Critical**: Workflow JSON must contain an `id` field with a UUID string. Without it, SQLite throws `SQLITE_CONSTRAINT: NOT NULL constraint failed: workflow_entity.id`. Generate one with `python3 -c "import uuid; print(uuid.uuid4())"`.

## Workflow Activation

Activation requires both the workflow ID and `versionId`:

```bash
# Get versionId from the workflow
VERSION_ID=$(sqlite3 ~/n8n-data/database.sqlite \
  "SELECT versionId FROM workflow_entity WHERE id='$WORKFLOW_ID';")

# Activate via API
curl -s -X POST \
  -H "Content-Type: application/json" -b /tmp/n8n-cookies.txt \
  -d "{\"versionId\": \"$VERSION_ID\"}" \
  "http://172.19.0.1:5678/rest/workflows/$WORKFLOW_ID/activate"
```

**Critical**: The POST body must include `{"versionId": "..."}`. Without it, activation fails silently or returns an error.

## Integration Pattern

Once running, Hermes can trigger workflows via webhooks:

```bash
# Content generation
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"topic":"system design"}' \
  http://172.19.0.1:5678/webhook/linkedin-generate

# Profile optimization
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"role":"SRE","industry":"fintech"}' \
  http://172.19.0.1:5678/webhook/linkedin-profile
```

For cron-based reminders, have the workflow write output to a file:
```json
// Write File node config
{"fileName": "/home/node/.n8n/linkedin-reminders.jsonl", "data": "..."}
```

This file is accessible on the host at `~/n8n-data/linkedin-reminders.jsonl` via the volume mount.
