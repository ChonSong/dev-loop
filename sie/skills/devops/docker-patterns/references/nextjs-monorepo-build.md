# Next.js Production Build in Monorepo — Patterns & Pitfalls

## Context

npm workspace monorepo at `/workspace/gto-wizard-clone`:
```
workspace/
  apps/web/          ← Next.js 15 app
  apps/api/          ← FastAPI backend
  node_modules/      ← hoisted from root package.json
  .next/             ← build output (inside apps/web/)
```

PATH issue: The node/npm binaries are installed as Hermes deps at `/home/hermeswebui/.hermes/home/.local/bin/`, not in the default container PATH.

## Commands

```bash
# Always set PATH first
export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"

# Production build (from apps/web)
cd /workspace/gto-wizard-clone/apps/web
NODE_ENV=production node ../../node_modules/next/dist/bin/next build

# Verify build
cat .next/BUILD_ID          # must exist and be non-empty
ls .next/static/css/        # must contain hashed CSS files

# Start production server
NODE_PATH="/workspace/gto-wizard-clone/node_modules" \
  node ../../node_modules/next/dist/bin/next start -p 3002

# Test locally
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002/
curl -s http://localhost:3002/ | grep -oP '<title>[^<]+</title>'
```

## Verification Checklist

1. **BUILD_ID exists:** `cat .next/BUILD_ID` — non-empty string
2. **CSS files exist:** `ls .next/static/css/*.css` — at least one file
3. **CSS hash matches HTML:** `curl -s http://localhost:3002/ | grep css` → filename must match a file on disk
4. **JS chunks exist:** `ls .next/static/chunks/*.js` — multiple files
5. **Local HTTP 200:** `curl -s -o /dev/null -w "%{http_code}" http://localhost:3002/` → 200

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `npx: command not found` | PATH missing Hermes bin dir | `export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"` |
| `Could not find a production build in '.next'` | `.next` was deleted or build was dev mode | `rm -rf .next && NODE_ENV=production next build` |
| CSS URLs return 404 | HTML references stale hash | Check `BUILD_ID`, rebuild, verify CSS filenames match |
| `next start` exits immediately | No BUILD_ID in `.next` | Verify build completed without errors |
| `000` exit code from curl | Connection refused or timeout | Check server is actually running on that port |
| Assets serve locally (200) but not through tunnel | tunnel points to wrong port | Verify `localhost:PORT` inside the container |

## Zombie Next.js Server Pattern

Old Next.js processes survive across tool sessions and serve stale code on various ports (3000, 8555-8565).

Finding zombies: `grep -r "next" /proc/*/cmdline 2>/dev/null`
Kill: `kill -9 <PID>` for each stale PID.
Fix: Always kill old processes before starting new ones.
