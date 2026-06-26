# Docker Build Cache Staleness — Debug Notes (2026-05-06)

## Symptom

Docker build on server completes without errors but ts-build stage appears cached:
- `dist/index.js` has old code despite `--no-cache`
- No visible build step output in `docker buildx build --progress=plain`
- `grep 'as any' dist/index.js` returns 0 matches even after source fix

## Root Cause

**Disk at 95-100% capacity.** When `/dev/sda2` hits 100%:
1. Docker buildx cannot allocate temp space for buildkit snapshotter
2. Buildkit silently falls back to cached layers without indicating failure
3. All stages show `#N cached` even when source changed
4. No error is surfaced — build reports success

## Diagnosis

```bash
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "df -h /"
# If Use% = 100% or Avail ≤ 1GB, disk is the problem
```

## Fix

Clear Docker build cache to free space:
```bash
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost \
  "docker builder prune -a -f && df -h /"
```

This freed ~22GB on the server (build cache was 1.9GB, plus image layers).
After clearing, rebuild with `--no-cache --load`.

## Prevention

Monitor disk before building:
```bash
df -h / | awk 'NR==2 {print "Disk:", $5 "used, " $4 "available"}'
```

**Safe prune commands (on any disk state):**
```bash
docker image prune -f         # dangling images only — fast, safe, ~0-2GB
docker builder prune -f       # build cache only — fast, safe, ~1-5GB
```

**Dangerous prune commands (on 100% disk — HANG indefinitely):**
```bash
docker system prune -f --volumes   # tries to delete volumes; blocks forever on full disk
docker system prune -a             # same — blocks forever
```

**Recovery sequence on 100% disk:**
```bash
# Step 1: reclaim space with safe commands
docker image prune -f
docker builder prune -f

# Step 2: if still full, restart postgres (its WAL may have filled the disk)
docker restart agent-os-postgres
sleep 5

# Step 3: try safe prunes again
docker image prune -f
docker builder prune -f

# Step 4: if needed, restart other containers to release log buffers
docker restart agent-os-backend agent-os-nanobot

# Step 5: verify
df -h / | tail -1
```

After space is reclaimed, restart crashed containers:
```bash
docker restart agent-os-postgres
docker compose -f /home/sean/.hermes/agent-os/docker-compose.yml up -d
```

## `sync` Before File Operations on Full Disk

When disk shows 100% full (`df -h /` → `Use%=100%`, `Avail=0`) but `du` reports far less used space (e.g., `du -sh /home/sean/` → 105G while `df` shows 437G used), the discrepancy is **deleted file handles still held open by running processes**. Linux buffers haven't flushed.

**Fix**: Run `sync` to force pending deletions through filesystem buffers:
```bash
ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "sync && df -h / | tail -1"
# After sync: 100% → 96%, ~18GB freed
```

**Why it works**: A process (likely Docker container logging) held open file handles to deleted log files. `sync` flushes the filesystem dirty buffers, completing the deletion accounting even though the processes still hold the handles.

## Frontend Dist Cleanup (Every Deploy)

Each `vite build` produces a new `index-HASH.js` (~1.2MB). Old hashes accumulate in `/home/sean/.hermes/agent-os-patched/frontend-dist/assets/`. After 2-3 builds, disk fills.

**Before every deploy**, clean old assets:
```bash
ssh ... "rm -f /home/sean/.hermes/agent-os-patched/frontend-dist/assets/index-*.js"
# Then cp new build
```

Or keep only the current one:
```bash
ssh ... "ls /home/sean/.hermes/agent-os-patched/frontend-dist/assets/"
# Delete all except the one you're about to deploy
```
