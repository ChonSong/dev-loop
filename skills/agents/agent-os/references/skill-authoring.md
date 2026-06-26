# Skill Authoring — Cross-Container Filesystem Patterns

## SKILL.md Format: `<name>/SKILL.md` (Directory-Per-Skill)

The nanobot skill loader reads `<skill-dir>/SKILL.md` — it does NOT read `<name>.md` files at the top level.

```
custom-skills/
  greeting-skill/
    SKILL.md      ← CORRECT
  hello.md        ← WRONG — ignored
```

**Frontmatter required fields:**
```markdown
---
name: skill-name
description: One-line description for the agent.
---

# Skill Name
...
```

## Host-Backed Persistent Volume for Skill Creation

Backend (Go) → writes to host path → nanobot (Python) → reads from same host path via its own mount.

```
Host filesystem
  /home/sean/.nanobot/custom-skills/
    <name>/SKILL.md

Backend container mounts:  /home/sean/.nanobot  →  /root/.nanobot  (:rw)
Nanobot container mounts:  /home/sean/.nanobot/custom-skills  →  /app/packages/nanobot/nanobot/skills/custom  (:ro)
```

Backend path inside container: `/root/.nanobot/custom-skills/<name>/SKILL.md`
Nanobot path inside container: `/app/packages/nanobot/nanobot/skills/custom/<name>/SKILL.md`

**Critical: backend's `loadSkillsFromDisk()` must scan both roots:**
1. `/app/packages/nanobot/nanobot/skills` — built-in skills (inside nanobot image)
2. `/root/.nanobot/custom-skills` — custom skills (host-backed mount)

These are different filesystem namespaces inside the backend container — a single `readdir` cannot traverse both.

## execSync vs dockerode in Containerized Backends

**`execSync` runs on the host** — not inside the container. Paths in `execSync` commands are host paths.

**`execSync('docker exec ...')` CAN reach other containers** if both share the host's Docker socket:
```typescript
// This WORKS from agent-os-backend (has docker.sock) to agent-os-nanobot (also has docker.sock):
execSync('docker exec agent-os-nanobot sh -c "ls /app/packages/nanobot/nanobot/skills/"', { stdio: 'ignore' });
```

**dockerode's `Container.execSync()` does NOT exist** — only async `exec()`. For synchronous one-shot commands, use `child_process.execSync('docker exec ...')` directly.

## docker-compose: Mount Syntax for Custom Skills Volume

```yaml
nanobot:
  volumes:
    - /home/sean/.nanobot/custom-skills:/app/packages/nanobot/nanobot/skills/custom:ro  # read-only from nanobot side

backend:
  volumes:
    - /home/sean/.nanobot/custom-skills:/root/.nanobot/custom-skills:rw  # read-write from backend side
```

**`:ro` on nanobot** — prevents nanobot from modifying its own skills dir; custom skills come from host.
**`:rw` on backend** — allows backend to create new skill files via `fs.writeFileSync`.

## Verifying Skill Creation End-to-End

```bash
# 1. Create via API
curl -X POST http://localhost:3001/api/skills/create \
  -H 'Content-Type: application/json' \
  -d '{"name":"test-skill","description":"Test","content":"---\nname: test-skill\ndescription: Test.\n---\n\n# Test\n"}'

# 2. Verify file on host
ls /home/sean/.nanobot/custom-skills/test-skill/SKILL.md

# 3. Verify nanobot can see it
docker exec agent-os-nanobot ls /app/packages/nanobot/nanobot/skills/custom/test-skill/

# 4. Verify backend lists it
curl http://localhost:3001/api/skills | python3 -c 'import json,sys; [print(s["name"]) for s in json.load(sys.stdin)]'
```
