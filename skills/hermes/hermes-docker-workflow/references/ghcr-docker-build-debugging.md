# GHCR + GitHub Actions Docker Build Debugging

## Key Lesson: You Cannot COPY --from an External Registry URL

**Do NOT do this:**
```dockerfile
FROM ghcr.io/astral-sh/uv:0.11.6-python3.13-trixie AS uv
COPY --from=ghcr.io/astral-sh/uv:0.11.6-python3.13-trixie /uv /usr/local/bin/uv
```

`COPY --from` only works with **named stages** (e.g., `COPY --from=uv`) or **image IDs** — not direct external registry URLs. The workaround: either `RUN pip install uv` directly, or use a proper multi-stage build where the external image is the stage's `FROM` and you `COPY` out of it.

## Debugging GHCR Image Builds via GitHub Actions

When a Docker build step fails in GitHub Actions, retrieve failure logs like this:

```python
import subprocess, json

gh_env = {**__import__('os').environ, 'GH_TOKEN': '<token>'}
gh = lambda cmd: subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=gh_env)

# Get run IDs and filter by workflow name + branch
r = gh(['gh', 'api', '-H', 'Accept: application/vnd.github+json',
        '/repos/{owner}/{repo}/actions/runs?per_page=10'])
data = json.loads(r.stdout)
for run in data['workflow_runs']:
    if run['head_sha'] == '<commit_sha>':
        print(run['id'], run['name'], run['conclusion'])

# Get job IDs for a specific run
r2 = gh(['gh', 'api', '-H', 'Accept: application/vnd.github+json',
         f'/repos/{owner}/{repo}/actions/runs/{run_id}/jobs'])
jobs = json.loads(r2.stdout)
for job in jobs['jobs']:
    print(f"  {job['name']} | {job['conclusion']}")
    if job['conclusion'] == 'failure':
        # Download and inspect failure logs
        lr = gh(['gh', 'api', job['logs_url']])
        log_text = lr.stdout.decode('utf-8', errors='ignore')
        for line in log_text.split('\n'):
            if any(x in line for x in ['ERROR', 'error:', 'FAILED', 'failed']):
                print(' ', line)
```

**Faster CLI shortcut** (when you already have the run ID):
```bash
gh run view <run_id> --repo <owner/repo>           # summary
gh run view <run_id> --job <job_id> --log-failed  # failure logs for specific job
```

## GHCR Image Naming: All-Lowercase Required

GitHub Container Registry (GHCR) repository names **must be lowercase**. Even if your GitHub account is `ChonSong`, `ghcr.io/ChonSong/repo` will **fail** with:
```
invalid tag "ghcr.io/ChonSong/repo:latest": repository name must be lowercase
```

**Fix**: Always hardcode the lowercase form in workflow YAML:
```yaml
# WRONG — Chonsong uppercase leaks into the tag:
ghcr.io/${{ github.repository_owner }}/agent-os-dashboard:latest
# → resolves to ghcr.io/ChonSong/agent-os-dashboard → FAILS

# CORRECT — hardcode lowercase:
ghcr.io/chonsong/agent-os-dashboard:latest
```

**Exception**: `docker/metadata-action` correctly produces lowercase tags automatically. The problem is manually specified tags in `docker/build-push-action`.

## GitHub Actions Workflow Image Tag Discovery

- `docker/metadata-action` tags from branches/sha are lowercase automatically
- `latest` tag is NOT added automatically — you must specify it explicitly if wanted
- The workflow run ID (e.g., `ghcr.io/chonsong/repo:sha-<sha>`) gives you full traceability

## Checking What Tags an Image Has

```bash
# Via GH API for user-scoped packages
gh api -H 'Accept: application/vnd.github+json' \
  '/users/{owner}/packages/container/{repo}/versions' | \
  python3 -c "import sys,json; [print(v['id'], v.get('metadata',{}).get('container',{}).get('tags',[])) for v in json.load(sys.stdin)[:5]]"
```

Common tags: `main`, `latest`, `sha-<short_sha>`. An image might exist but have no `latest` tag — use `main` or the sha tag instead.

## Common Dockerfile.nanobot Failures and Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| `/uv: not found` | COPY --from with external URL | Use `RUN pip install uv` directly |
| `pyproject.toml not found` | Source copied AFTER pip install | COPY source BEFORE `uv pip install` |
| `uv pip install -e .[api]` fails | pyproject.toml is in a subdirectory | Use `uv pip install --system -e "./nanobot[api]"` |
| `ghcr.io/ChonSong/repo:latest: not found` | Image has no `latest` tag | Use `main` or `sha-<sha>` tag instead |

## Dashboard FROM Base Image Pattern

When the dashboard image is built FROM `ghcr.io/chonsong/hermes-agent`, that base image must already exist in GHCR. Build order matters:
1. Build `hermes-agent` first → pushes to `ghcr.io/chonsong/hermes-agent:main`
2. Build `agent-os-dashboard` → uses `FROM ghcr.io/chonsong/hermes-agent:main`

If the dashboard build runs before hermes-agent is published, it fails with "not found". Handle this by ensuring the hermes-agent workflow runs first (or accept the first dashboard build will fail and re-run after hermes-agent is done).
