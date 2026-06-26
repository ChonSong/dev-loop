# Docker Build Context Resolution — Key Findings

## The Fix (2026-04-30)

**Wrong:**
```yaml
build:
  context: ../hermes-agent
  dockerfile: ../docker/Dockerfile   # ❌ resolves relative to compose file dir
```

**Correct:**
```yaml
build:
  context: ${HERMES_AGENT_DIR:-../hermes-agent}
  dockerfile: Dockerfile            # ✅ resolved relative to context
```

When `context` is set to `../hermes-agent` (relative to compose file at `hermes-sync/docker/docker-compose.yml`), the `dockerfile` field is resolved relative to the **build context root** (`hermes-agent/`), NOT the compose file location. So `dockerfile: Dockerfile` correctly points to `hermes-agent/Dockerfile`.

The original `../docker/Dockerfile` was treated by Docker as relative to the compose file dir, resolving to `hermes-sync/docker/Dockerfile`. Coincidentally this worked because `setup.sh` had copied the identical file there — but this was fragile and not guaranteed.

## Verified File Identity

`hermes-sync/docker/Dockerfile` and `hermes-agent/Dockerfile` are byte-identical (both 3321 bytes). The compose no longer uses the hermes-sync copy, so it should be removed from the repo (done: `git rm docker/Dockerfile`).

## Entrypoint Same Pattern

`hermes-sync/docker/entrypoint.sh` and `hermes-agent/docker/entrypoint.sh` are identical. Removed from hermes-sync (done: `git rm docker/entrypoint.sh`). Compose uses the one copied into the image from `hermes-agent/`.

## Cleanup Summary

After 2026-04-30 commit `bfd471c`, `hermes-sync/docker/` contains only:
- `docker-compose.yml` — compose definition
- `SOUL.md` — custom container soul (different from hermes-agent/docker/SOUL.md)
- `.dockerignore` — build exclusion list

No more duplicate files.
