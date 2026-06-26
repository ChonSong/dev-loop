# Skill Permission Errors — hermes-agent

**Source:** Session 2026-05-08 cron job analysis  
**Date:** 2026-05-08

---

## Symptom

Cron jobs (and any hermes-agent session) fail to load a skill with:

```
WARNING [...] agent.prompt_builder: Failed to parse skill file /home/sean/.hermes/skills/agents/agent-os/SKILL.md: [Errno 13] Permission denied: '/home/sean/.hermes/skills/agents/agent-os/SKILL.md'
```

The skill is silently skipped. The agent runs without the skill's context, which can cause:
- Missing workflow steps
- Broken conditional logic that depends on skill content
- Cron jobs that "run" but produce no useful output

---

## Root Cause

The skill file (or its parent directory) is owned by a different UID than the hermes-agent process runs as:

| Context | UID | Can read 0o600 file? |
|---------|-----|----------------------|
| hermes container (hermes-agent) | 1000 | No |
| Inside container (root entrypoint ran chown) | 1000 after entrypoint | Yes |
| Cron job (host context?) | varies | varies |
| Skills bundled in Docker image | 0 (root) | No if mode is 0o600 |

Common cause: a skill was created or modified inside the Docker container with `root` ownership (e.g., `SKILL.md` created by an earlier run that used root inside the container, before the entrypoint remapped to uid 1000).

The skill at `/home/sean/.hermes/skills/agents/agent-os/` is owned by uid=0 inside the container, making it unreadable to the hermes-agent process running as uid=1000.

---

## Detection

```bash
# Check ownership of a skill
stat /home/sean/.hermes/skills/agents/agent-os/SKILL.md

# Should show uid=1000 for hermes-agent to read it
# If uid=0 and mode is 0o600 → unreadable

# Check all skills for ownership issues
find ~/.hermes/skills -name "SKILL.md" -exec stat {} \; 2>/dev/null | grep -B4 "Uid: (0"

# Or in one command
find ~/.hermes/skills -name "SKILL.md" -exec stat --format="%u %a %n" {} \; 2>/dev/null | awk '$1 != 1000 {print}'
```

---

## Fix

**On the host** (preferred — persists across container restarts):

```bash
# Fix a single skill
sudo chown -R 1000:1000 /home/sean/.hermes/skills/agents/agent-os/

# Fix all skills
sudo chown -R 1000:1000 /home/sean/.hermes/skills/
```

**Inside the container** (temporary, resets on container restart):

```bash
# If already running as uid 1000
chown -R 1000:1000 /home/sean/.hermes/skills/

# If running as root inside container
# The entrypoint should have already done this — if not, the entrypoint may be bypassed
```

---

## Prevention

- Never create or modify skills from inside the Docker container while running as root
- When using `skill_manage` or `write_file` inside the container, verify the file is created with uid 1000
- The entrypoint script (`entrypoint.sh`) runs `chown -R` on `/opt/data` (which is `~/.hermes` mapped). If skills are created before the entrypoint completes (e.g., via `sleep infinity` bypass), ownership stays root
