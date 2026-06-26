# Polytopia Clone Deployment Audit (June 2026)

## Context
Static game build served via `serve dist -p 3001 --cors` behind Cloudflare tunnel at `hex.codeovertcp.com`.

## Deployment details
- **Repo**: `/home/sc/repos/polytopia-clone`  
- **Build**: `npm run build` (dist/ directory)  
- **Server**: `npm exec serve dist -p 3001 --cors` (background PID 1041066)  
- **DNS**: CNAME `hex.codeovertcp.com` → Cloudflare tunnel  
- **Process path**: cwd = `/home/sc/repos/polytopia-clone/dist`  

## Verification checklist (from deployment-audit skill)
1. ✅ **Port 3001 active** – `curl localhost:3001` → 200  
2. ✅ **Title tag** – `<title>Polytopia Clone</title>` (customized from Vite default)  
3. ✅ **Public endpoint** – `curl https://hex.codeovertcp.com` → 200  
4. ✅ **Working directory** – matches project repo, not stale build elsewhere  
5. ✅ **No git changes** – clean working tree, nothing to redeploy  

## Common pitfalls encountered
- Port 3001 wasn't listening after prior session ended; required manual `serve` restart.  
- `npm run test` passes (228 tests) but doesn't verify live server health – add E2E smoke test to CI if needed.

## Quick restart script
```bash
#!/bin/bash
cd /home/sc/repos/polytopia-clone
npm run build
npm exec serve dist -p 3001 --cors &
sleep 2
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001
```