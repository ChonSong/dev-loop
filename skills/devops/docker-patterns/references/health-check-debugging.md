# Debugging Unhealthy Docker Containers

A container showing `unhealthy` in `docker ps` doesn't mean the app is broken — it means the **health check** itself is failing. Distinguish between "app is down" and "health check tool not found."

## Diagnosis Flow

### 1. Check health check logs

```bash
docker inspect <container> --format '{{json .State.Health}}' | python3 -m json.tool
```

Key fields:
- `Status`: `healthy`, `unhealthy`, or `starting`
- `FailingStreak`: how many consecutive failures
- `Log[].ExitCode`: exit code of each check attempt
- `Log[].Output`: any stdout/stderr from the check

### 2. Check what the health check actually runs

```bash
docker inspect <container> --format '{{json .Config.Healthcheck}}' | python3 -m json.tool
```

The `Test` array shows the command. Pay attention to:
- `CMD curl ...` — requires curl in the image
- `CMD wget ...` — requires wget in the image
- `CMD-SHELL pg_isready ...` — Postgres-native, self-contained

### 3. Common exit codes

| Exit code | Meaning |
|-----------|---------|
| `-1` | Command not found (binary missing) |
| `0` | Success |
| `1` | Failure (health check ran but app not ready) |
| `6` | curl: could not resolve host |
| `7` | curl: failed to connect |
| `22` | curl: HTTP page not retrieved |

### 4. Check if the app itself is actually running

```bash
# Test from inside the container using what IS available:
docker exec <container> python3 -c "import urllib.request; r = urllib.request.urlopen('http://localhost:8000/health'); print(r.status, r.read().decode())"

# Or check the app logs (healthy 200 responses = app is fine):
docker logs --tail 20 <container>
```

## Common Fixes

### Fix 1: `curl` not found → use `python3`

When the health check is `CMD curl -f http://localhost:8000/health` but curl isn't in the image:

```yaml
healthcheck:
  test: ["CMD-SHELL", "python3 -c \"import urllib.request; exit(0 if urllib.request.urlopen('http://localhost:8000/health').status == 200 else 1)\""]
  interval: 30s
  timeout: 10s
  retries: 3
```

Works for any Python-based image. Change the URL and port to match the target.

### Fix 2: `wget` not found

Same pattern with `urllib.request` as above, or install wget/curl at image build time.

### Fix 3: Service not yet ready

Increase `start_period` to give the service time to initialize before health checks begin counting:

```yaml
healthcheck:
  test: [...]
  start_period: 30s  # Wait 30s before first check
```

## Orphaned Container Pattern

A container that passes its own startup but depends on a sibling service that doesn't exist will show `unhealthy` indefinitely.

**Symptom:** Health check tries to reach another service by hostname (e.g. `http://backend:3001/health`) and gets DNS resolution failure (exit code 6).

**Diagnosis:** Check if the target service actually exists on the same Docker network:

```bash
# List all containers on the same network
docker network inspect <network-name> --format '{{range .Containers}}{{.Name}} {{end}}'

# Check ALL containers (including stopped/created) for sibling services
docker ps -a --format '{{.Names}} {{.Status}}' | grep <stack-prefix>
```

**If the sibling is missing (status `Created`):**
- Either start the full stack: `docker compose up -d` from the compose file
- Or stop/remove the orphan: `docker stop <container> && docker rm <container>`

### Verification after fix

```bash
# Wait for next health check interval
sleep 35
docker inspect <container> --format '{{.State.Health.Status}}'
```
