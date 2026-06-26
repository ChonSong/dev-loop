# Container-SSH Failure — 2026-08

## What happened

The `seans-reporepo refresh` cron job was configured to SSH from the container to the host:
```
ssh -i /home/hermes/.ssh/id_ed25519 sean@localhost "cd /workspace/seans-reporepo && ..."
```

This failed because:
1. `/home/hermes/.ssh/id_ed25519` does not exist in the container
2. Host port 22 refuses connections from the container
3. The `ssh host` config alias also fails

## Fix applied

Redesigned the job to run directly from the container — the repo is at `/workspace/seans-reporepo/`:
```
cd /workspace/seans-reporepo
git pull origin main
python3 scripts/generate-catalog.py
git add -A && (git diff --cached --quiet || git commit -m "..." && git push)
```

## Lesson

**Never assume SSH works from container to host.** Test first with `ssh host "echo ok"`. If it fails, redesign the job to run from the container directly, or pause it if host-only resources are truly needed.

## Jobs affected and fixed

| Job | Old approach | New approach |
|-----|-------------|-------------|
| seans-reporepo refresh | SSH to host | Direct from container |
| context-budget-audit | `deliver: origin` (broken) | `deliver: local` |
| html-in-canvas-api-monitor | `research` skill (missing) | Direct GitHub API + web search |
| Morning Briefing | Paused after error | Simplified prompt, re-enabled |
