# System Health Reference — 2026-04-30

## Last Investigation (this session)

### 🔴 Critical
| Issue | Status | Notes |
|-------|--------|-------|
| **Disk at 98%** (11GB free of 461GB) | OPEN | 426GB used. Find large temp files, old Docker images, logs. |
| **Rate smoother DOWN** (port 4001) | OPEN | Connection refused. Was also down Apr 27 with 18× HTTP 429 errors from OpenRouter. Never restarted. |

### 🟡 Known Issues
| Issue | Status | Notes |
|-------|--------|-------|
| Hermes Sync — GitHub Push cron (`63dc626e478e`) | **NEVER FIRED** | `last_run_at: null`. Never executed. Force-run: `hermes cron run 63dc626e478e` |
| hermes-sync rolling rebuild cron (`33ee3807d679`) | **NEVER FIRED** | `last_run_at: null`. Never executed. Force-run: `hermes cron run 33ee3807d679` |
| Night Owl Report cron (`53fc35f11ccf`) | **NEVER FIRED** | `last_run_at: null` |
| Morning Briefing cron (`56685e569e5f`) | **NEVER FIRED** | `last_run_at: null` |
| Gateway health (port 3000) | UNCLEAR | Returns `Connection refused` from inside container — but container localhost ≠ host localhost. Verify from host with `curl http://localhost:3000/health` |

### 🟢 Healthy (last_run_at ok)
| Job | Last Run | Status |
|-----|----------|--------|
| Memory Curation (`0175050d9c29`) | 2026-04-29 15:01 | ok |
| Cross-Agent Bridge Poll (`6d747879c7c5`) | 2026-04-29 22:15 | ok |
| System Monitor & Cleaner (`d3aac3ef0953`) | 2026-04-29 17:00 | ok |
| HKUDS/ClawTeam Daily Summary (`4e516a10190d`) | 2026-04-30 00:58 | ok |
| Delegation Monitor (`f53d0f3da390`) | 2026-04-30 04:36 | ok |
| OpenClaw Backup (`37a68f8c2ca0`) | 2026-04-28 10:54 | ok |
| Autonomy Digest (`65d287b7c3c9`) | 2026-04-29 18:41 | ok |
| Infrastructure Daily Assessment (`72e05c65c1e0`) | 2026-04-30 01:08 | ok |
| Rate Smoother Backoff Digest (`2c355018fae2`) | 2026-04-30 01:02 | ok |
| Overnight Autonomy Engine (`c9aa6d0bef3b`) | 2026-04-29 15:00 | ok |

## Tool Availability (inside container)
```
curl:        NOT FOUND
docker:      NOT FOUND (Docker socket not mapped into container)
gh:          NOT FOUND
git:         /usr/bin/git ✅
python3:     ✅ (use instead of curl for HTTP checks)
rclone:      NOT FOUND
```

**For HTTP health checks inside container, use Python:**
```python
import urllib.request
try:
    r = urllib.request.urlopen('http://localhost:4001/', timeout=3)
    print(f"HTTP {r.status}")
except Exception as e:
    print(f"DOWN: {e}")
```

## Cron Job Schedule Conflicts
Three jobs fire at **00:00 UTC** (10:00 Sydney):
- Cross-Agent Bridge Poll (`6d747879c7c5`)
- Hermes Sync — GitHub Push (`63dc626e478e`) 
- hermes-sync rolling rebuild (`33ee3807d679`)

Consider merging the two hermes-sync jobs into one.

## Disk Cleanup Commands (run from host)
```bash
# Find large directories
du -sh /home/sean/* 2>/dev/null | sort -rh | head -20

# Docker system prune
docker system prune -af --volumes

# Find largest files
find / -type f -size +500M 2>/dev/null | head -20

# Docker images
docker images | grep -v hermes-sync
```
