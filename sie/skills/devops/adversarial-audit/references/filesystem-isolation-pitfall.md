# Filesystem Isolation Pitfall — Real Example

## What Happened

During session `b18535bafe8a` (2026-06-08), the adversarial audit system was built:
1. `/workspace/commitments.md` was created with 3 active commitments
2. `/workspace/scripts/commitment_auditor.py` was written
3. A cron job (ID: `35dfd98f75e8`) was created to run the auditor Mon/Thu at 10:00 UTC
4. The cron job prompt referenced `/workspace/commitments.md`

**Problem**: The session ran in the webui container context. The cron job runs in a different container context. `/workspace/` is NOT shared between them.

**Result**: The auditor cron job will fail on its first scheduled run (2026-06-11) because it cannot find `/workspace/commitments.md`.

## How to Detect

Before creating any cron job that references files:
```bash
# Check if the path exists from the current context
ls -la /workspace/commitments.md 2>/dev/null || echo "NOT FOUND"

# Check if /workspace is even writable
mkdir -p /workspace/test 2>/dev/null || echo "NOT WRITABLE"
```

## Shared Paths

Paths that are typically shared across containers:
- `/opt/data/` — usually a volume mount, shared between webui and cron containers
- `/home/hermes/` — home directory, usually shared
- `/tmp/` — shared but ephemeral (lost on container restart)

Paths that are typically NOT shared:
- `/workspace/` — container-local in many Hermes deployments
- `/app/` — container-local
- `/home/hermeswebui/` — may be webui-container-specific

## Fix

1. Move `commitments.md` to `/opt/data/commitments.md`
2. Update the auditor cron job prompt to reference the new path
3. Update `AGENTS.md` to reference the new path
4. Verify: `ls -la /opt/data/commitments.md` from both webui and cron contexts

## Lesson

**Always verify filesystem paths are accessible from the execution context that will use them.** The webui session context and the cron job context are different containers with different filesystem views. What exists in one may not exist in the other.
