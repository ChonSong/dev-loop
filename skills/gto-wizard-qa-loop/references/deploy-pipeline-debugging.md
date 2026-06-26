# Deploy Pipeline Debugging

When the user says "I haven't noticed any changes" despite commits being made, the deploy pipeline is broken. Run through this checklist in order.

## 1. Are Commits Being Pushed to GitHub?

The deploy script (`deploy.sh`) only checks `origin/main`. If the Player never pushed, the deploy never fires.

```bash
cd /home/sc/repos/gto-wizard-clone
git rev-parse HEAD          # local
git rev-parse origin/main   # remote
git log --oneline origin/main..HEAD  # unpushed commits
```

**Fix**: The Player skill now includes `git push origin main` after every commit. If commits are unpushed, push manually:
```bash
git push origin main
```

## 2. Are Backend Dependencies Installed?

The deploy script does `npm install` (frontend) but the backend (FastAPI via uvicorn) needs its own deps. If the Python API returns `Internal Server Error` on any endpoint:

```bash
journalctl --user -u gto-wizard-api.service --since "5 min ago" --no-pager | grep -i "ModuleNotFoundError\|error"
```

Common missing deps:
- `aiosqlite` — needed for SQLAlchemy async SQLite. Not in the original `pyproject.toml`. Fix: `uv sync --group runtime` or add to pyproject.toml runtime group.
- Any new dep added in recent commits that `pyproject.toml` references but the venv doesn't have yet.

**Fix**: The deploy script now runs `uv sync --group runtime` after `npm install`. For immediate fix:
```bash
cd /home/sc/repos/gto-wizard-clone && uv sync --group runtime
systemctl --user restart gto-wizard-api.service
```

## 3. Is the Frontend Build Stale?

Turbo caches aggressively. If a new route was added (e.g., `/variants`) but doesn't appear in the Next.js build output, the cache is stale.

Check what routes were actually built:
```bash
grep "Route (app)" /home/sc/.hermes/logs/gto-wizard-deploy.log
```

**Fix**: The deploy script now clears `.next` and `.turbo` before each build. To force a fresh build now:
```bash
cd /home/sc/repos/gto-wizard-clone/apps/web
rm -rf .next .turbo
cd ..
npm run build
systemctl --user restart gto-wizard-web.service
```

## 4. Are Playwright Browsers Installed?

The deploy script runs E2E tests as a quality gate. If browsers aren't installed, ALL tests fail instantly and the deploy auto-rolls back (event to the same commit, so future deploy checks say "Already up to date").

```bash
ls /tmp/pw-browsers/ 2>/dev/null || echo "not installed"
```

**Fix**:
```bash
cd /home/sc/repos/gto-wizard-clone
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright install chromium
```

## 5. Is the API Service Running?

The web service proxies `/api/v1/*` to the FastAPI backend (port 8001, systemd user service). If the backend is down, all API features break silently.

```bash
systemctl --user status gto-wizard-api.service   # must be active (running)
curl -s http://localhost:8001/api/v1/health       # must return {"status":"healthy"}
```

## 6. Is the Web Service Running?

```bash
systemctl --user status gto-wizard-web.service    # must be active (running)
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/  # must be 200
```

## 7. Is the Tunnel Running?

If the public URL (wiz.codeovertcp.com) returns 502 or connection refused:
```bash
ps aux | grep cloudflared | grep -v grep
cloudflared tunnel list 2>&1 | head -5
```

**Fix**:
```bash
kill $(pgrep -f cloudflared)
cloudflared tunnel --config /home/sc/.cloudflared/config.yml run codeovertcp &
sleep 3
curl -s -o /dev/null -w "%{http_code}" https://wiz.codeovertcp.com/
```

## Common Failure Mode: Stale Deploy Rollback Loop

The deploy script:
1. Fetches origin/main → detects new SHA → pulls → builds → runs E2E tests
2. If E2E tests fail (e.g., browsers not installed), it does `git reset --hard <sha>` to rollback
3. This resets HEAD to the SAME commit that's already on origin/main
4. Next deploy check says "Already up to date" and does nothing
5. **The new code is on disk but NOT built and NOT served**

**Detection**: Deploy log shows "Rollback complete. Running at <sha>" but the deploy check never fires again for the same SHA.

**Fix**: Manually build and restart, or force a trivial empty commit to create a new SHA:
```bash
git commit --allow-empty -m "chore: force deploy" && git push origin main
```
