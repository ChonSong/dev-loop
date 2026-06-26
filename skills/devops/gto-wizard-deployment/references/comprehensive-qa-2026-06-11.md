# Comprehensive QA Script (2026-06-11)

Run this when deploying changes or before setting up overnight maintenance crons.
All commands via SSH to the host:

```bash
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "command"
```

## 1. Port Inventory
```bash
ss -tlnp | grep -E '8564|8003|50051'
# Expected: 8564 (next-server), 8003 (uvicorn), 50051 (solver gRPC)
```

## 2. Title Tag (most important — identifies the correct app)
```bash
curl -sL http://localhost:8564/ | grep -o '<title>[^<]*</title>'
# Must be: <title>GTO Wizard</title>
# Wrong: <title>Open Lovable v3</title>
```

## 3. Frontend BUILD_ID vs git HEAD
```bash
cat /home/sean/gto-wizard-clone/apps/web/.next/BUILD_ID
cd /home/sean/gto-wizard-clone && git rev-parse HEAD
# If the frontend returns 502 on some pages, the build is stale
```

## 4. All 14 Pages
```bash
for p in / /equity /icm /train /courses /spots /strategies /analyze /study /play /practice /plo /double-board /bomb-pot; do
  echo -n "$p → "
  curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "https://wiz.codeovertcp.com${p}"
  echo
done
```

## 5. API Endpoints
```bash
echo "Health: $(curl -s http://localhost:8003/api/v1/health)"
echo "Solver: $(curl -s http://localhost:8003/api/v1/solver/health)"
echo "Quiz: $(curl -s http://localhost:8003/api/v1/quiz/random | head -c 100)"
echo "Courses: $(curl -s http://localhost:8003/api/v1/courses | head -c 100)"
echo "Solve: $(curl -s -X POST http://localhost:8003/api/v1/solver/solve -H 'Content-Type: application/json' -d '{\"board\":\"Kd7h2c\",\"iterations\":100}' | head -c 100)"
echo "Preflop: $(curl -s -X POST http://localhost:8003/api/v1/solver/preflop-range -H 'Content-Type: application/json' -d '{\"position\":\"BTN\"}' | python3 -c 'import sys,json;print(len(json.load(sys.stdin).get(\"hands\",[])))' 2>/dev/null || echo 'FAIL')"
```

## 6. Solver Engine
```bash
python3 -c "import sys; sys.path.insert(0,'/home/sean/gto-wizard-clone/apps/solver'); from cfr.engine import CFREngine; print('CFR engine OK')"
```

## 7. Database
```bash
python3 -c "
import sqlite3
c = sqlite3.connect('/home/sean/gto-wizard-clone/gto_wizard.db')
tables = c.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\"').fetchall()
for t in tables:
    if t[0] != 'sqlite_sequence':
        cnt = c.execute(f'SELECT COUNT(*) FROM [{t[0]}]').fetchone()[0]
        print(f'  {t[0]}: {cnt} rows')
"
```

## 8. Live Site
```bash
curl -s -o /dev/null -w '%{http_code}' --connect-timeout 10 https://wiz.codeovertcp.com/
curl -sL https://wiz.codeovertcp.com/ | grep -o '<title>[^<]*</title>'
```

## Known Failure Modes Detected

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **Partial 502** | Some pages 200, some 502. Title correct. | Rebuild frontend: `npx next build && pkill -9 next-server` |
| **Stale build** | BUILD_ID doesn't match git HEAD | `git pull && rm -rf .next && npx next build` |
| **Empty quiz** | `quiz/random` returns `"No spots found"` | Run seed script. DB tables exist but empty. |
| **Courses 500** | `courses` endpoint returns Internal Server Error | Missing course_models tables. Create tables. |
| **gRPC duplicate** | Two `python3 -m solver.server` processes on port 50051 | `pkill -f solver.server` and restart fresh. Harmless but wasteful. |
| **gRPC dead** | Port 50051 missing from `ss -tlnp` | Start solver server. Direct solve path still works (bypasses gRPC). |
| **Auto-restart conflict** | Frontend respawns with new PID after pkill | Host has auto-restart. Accept it — rebuild then kill; it auto-restarts with new code. |
