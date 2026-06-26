# CI Troubleshooting Quick Reference

Common CI failure patterns and how to diagnose them from the logs.

## Reading CI Logs

```bash
# With gh
gh run view <RUN_ID> --log-failed

# With curl — download and extract
curl -sL -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/actions/runs/<RUN_ID>/logs \
  -o /tmp/ci-logs.zip && unzip -o /tmp/ci-logs.zip -d /tmp/ci-logs
```

## Common Failure Patterns

### Test Failures

**Signatures in logs:**
```
FAILED tests/test_foo.py::test_bar - AssertionError
E       assert 42 == 43
ERROR tests/test_foo.py - ModuleNotFoundError
```

**Diagnosis:**
1. Find the test file and line number from the traceback
2. Use `read_file` to read the failing test
3. Check if it's a logic error in the code or a stale test assertion
4. Look for `ModuleNotFoundError` — usually a missing dependency in CI

**Common fixes:**
- Update assertion to match new expected behavior
- Add missing dependency to requirements.txt / pyproject.toml
- Fix flaky test (add retry, mock external service, fix race condition)

---

### Lint / Formatting Failures

**Signatures in logs:**
```
src/auth.py:45:1: E302 expected 2 blank lines, got 1
src/models.py:12:80: E501 line too long (95 > 88 characters)
error: would reformat src/utils.py
```

**Diagnosis:**
1. Read the specific file:line numbers mentioned
2. Check which linter is complaining (flake8, ruff, black, isort, mypy)

**Common fixes:**
- Run the formatter locally: `black .`, `isort .`, `ruff check --fix .`
- Fix the specific style violation by editing the file
- If using `patch`, make sure to match existing indentation style

---

### Type Check Failures (mypy / pyright)

**Signatures in logs:**
```
src/api.py:23: error: Argument 1 to "process" has incompatible type "str"; expected "int"
src/models.py:45: error: Missing return statement
```

**Diagnosis:**
1. Read the file at the mentioned line
2. Check the function signature and what's being passed

**Common fixes:**
- Add type cast or conversion
- Fix the function signature
- Add `# type: ignore` comment as last resort (with explanation)

---

### Build / Compilation Failures

**Signatures in logs:**
```
ModuleNotFoundError: No module named 'some_package'
ERROR: Could not find a version that satisfies the requirement foo==1.2.3
npm ERR! Could not resolve dependency
```

**Diagnosis:**
1. Check requirements.txt / package.json for the missing or incompatible dependency
2. Compare local vs CI Python/Node version

**Common fixes:**
- Add missing dependency to requirements file
- Pin compatible version
- Update lockfile (`pip freeze`, `npm install`)

---

### Permission / Auth Failures

**Signatures in logs:**
```
fatal: could not read Username for 'https://github.com': No such device or address
Error: Resource not accessible by integration
403 Forbidden
```

**Diagnosis:**
1. Check if the workflow needs special permissions (token scopes)
2. Check if secrets are configured (missing `GITHUB_TOKEN` or custom secrets)

**Common fixes:**
- Add `permissions:` block to workflow YAML
- Verify secrets exist: `gh secret list` or check repo settings
- For fork PRs: some secrets aren't available by design

---

### Timeout Failures

**Signatures in logs:**
```
Error: The operation was canceled.
The job running on runner ... has exceeded the maximum execution time
```

**Diagnosis:**
1. Check which step timed out
2. Look for infinite loops, hung processes, or slow network calls

**Common fixes:**
- Add timeout to the specific step: `timeout-minutes: 10`
- Fix the underlying performance issue
- Split into parallel jobs

---

### Docker / Container Failures

**Signatures in logs:**
```
docker: Error response from daemon
failed to solve: ... not found
COPY failed: file not found in build context
```

**Diagnosis:**
1. Check Dockerfile for the failing step
2. Verify the referenced files exist in the repo

**Common fixes:**
- Fix path in COPY/ADD command
- Update base image tag
- Add missing file to `.dockerignore` exclusion or remove from it

---

## Auto-Fix Decision Tree

```
CI Failed
├── Test failure
│   ├── Assertion mismatch → update test or fix logic
│   └── Import/module error → add dependency
├── Lint failure → run formatter, fix style
├── Type error → fix types
├── Build failure
│   ├── Missing dep → add to requirements
│   └── Version conflict → update pins
├── Permission error → update workflow permissions (needs user)
└── Timeout → investigate perf (may need user input)
```

## Re-running After Fix

```bash
git add <fixed_files> && git commit -m "fix: resolve CI failure" && git push

# Then monitor
gh pr checks --watch 2>/dev/null || \
  echo "Poll with: curl -s -H 'Authorization: token ...' https://api.github.com/repos/.../commits/$(git rev-parse HEAD)/status"
```

---

## Docker Build Failures in GitHub Actions

These require checking the specific job logs. Common patterns:

### `COPY --from` External Registry URL
```
ERROR: failed to compute cache key: failed to calculate checksum of ref ...: "/uv": not found
```
**Cause**: `COPY --from=ghcr.io/external/image` is invalid — COPY --from only works with named stages or image IDs.
**Fix**: Use `RUN pip install uv` directly, or a proper multi-stage build with `FROM external-image AS stage`.

### Layer Order: Source Copied After Install
```
error: /app does not appear to be a Python project, as neither `pyproject.toml` nor `setup.py` are present
```
**Cause**: `uv pip install -e .` runs before `COPY packages/nanobot/ .` — install step can't find pyproject.toml.
**Fix**: Always `COPY` source first, then run the install.

### Wrong pyproject.toml Path for uv
```
error: /app does not appear to be a Python project
```
**Cause**: pyproject.toml is at `./nanobot/pyproject.toml` not `./pyproject.toml`.
**Fix**: Use `uv pip install --system -e "./nanobot[api]"` (include the subdirectory path).

### GHCR Uppercase Repo Name
```
ERROR: invalid tag "ghcr.io/ChonSong/repo:latest": repository name must be lowercase
```
**Cause**: `github.repository_owner` resolves to mixed-case `ChonSong`, which GHCR rejects.
**Fix**: Hardcode the lowercase form, or use bash `${var,,}` lowercasing with `shell: bash`:
```yaml
# WRONG:
ghcr.io/${{ github.repository_owner }}/repo:latest
# CORRECT (hardcoded):
ghcr.io/chonsong/repo:latest
# CORRECT (bash lowercasing — must set shell: bash):
ghcr.io/${GITHUB_REPOSITORY_OWNER,,}/repo:latest
```
> ⚠️ Jinja/GitHub expression filters like `|lower`, `toLowerCase()`, and `lower()` do not work in workflow YAML. Only bash parameter expansion `${var,,}` works, and only with `shell: bash` (YAML defaults to `sh`).

### GHCR Does Not Auto-Tag `latest`
GHCR does not automatically apply a `latest` tag when you push. You must explicitly push with both tags:
```yaml
- run: |
    docker buildx build \
      --tag "ghcr.io/chonsong/repo:${{ github.sha }}" \
      --tag "ghcr.io/chonsong/repo:latest" \
      --push \
      .
```
**Verification**: After a successful push, check the Packages page — if `latest` isn't listed, it wasn't pushed. Use `docker manifest inspect` locally or query the GHCR API to confirm all tags are present.

### `web_extract` Cannot Read CI Build stdout
When GitHub Actions step logs exceed a certain size, GitHub offloads them to S3. The `Authorization: token $GITHUB_TOKEN` header follows the redirect to S3 but GH Actions blocks automated/token-based access to build stdout via the web UI. This means `web_extract` on the workflow run page only shows run metadata (duration, conclusion, step names) — **not the actual error messages from the failed step**.

**Workaround**: Use the API to get job/step details:
```bash
# Get the workflow run and its jobs
gh api repos/$OWNER/$REPO/actions/runs?per_page=3
gh api repos/$OWNER/$REPO/actions/runs/$RUN_ID/jobs

# Download logs directly
gh api repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs | python3 -c "
import sys, json, urllib.request, zipfile, io
data = json.load(sys.stdin)
# logs_url is a temporary S3 URL — follow it
req = urllib.request.Request(data['logs_url'])
with urllib.request.urlopen(req) as r:
    z = zipfile.ZipFile(io.BytesIO(r.read()))
    for name in z.namelist():
        print(f'--- {name} ---')
        print(z.read(name).decode(errors='replace'))
"
```

### Shell Pipe Exit Code Trap
When debugging CI steps, avoid piping to `head` or `tee` — they mask the real exit code:
```yaml
# BAD: 'head' closes the pipe after N lines, docker buildx exits non-zero
# but the shell's exit code reflects 'head', not 'docker'
run: |
  set -x
  docker info 2>&1 | head -20
  docker buildx build ... 2>&1 | tee /dev/stderr

# GOOD: run the command directly, let the exit code propagate
run: |
  docker buildx build \
    --platform linux/amd64 \
    --tag "ghcr.io/chonsong/repo:${{ github.sha }}" \
    --file ./Dockerfile \
    --push \
    .
```

If you need diagnostics, run them as separate steps without piping:
```yaml
- run: docker buildx version
- run: docker buildx ls
- run: docker info
```

### Base Image Tag Not Found
```
ERROR: ghcr.io/chonsong/hermes-agent:latest: not found
```
**Cause**: The base image exists but has no `latest` tag — it's tagged `main` or `sha-<hash>`.
**Fix**: Use the correct tag. Check via:
```bash
gh api -H 'Accept: application/vnd.github+json' \
  '/users/{owner}/packages/container/{repo}/versions' | \
  python3 -c "import sys,json; [print(v['id'], v.get('metadata',{}).get('container',{}).get('tags',[])) for v in json.load(sys.stdin)[:5]]"
```

### Workflow Path Filter Missing a File
```
This run likely failed because of a workflow file issue.
```
**Cause**: A Dockerfile or config file used in the workflow was updated, but it's not listed in `on.push.paths` — so the workflow didn't run.
**Fix**: Add the file to the path filter in the workflow YAML:
```yaml
on:
  push:
    paths:
      - 'Dockerfile.nanobot'
      - 'Dockerfile.dashboard'   # ← must be listed
      - 'docker-compose.yml'
      - '.github/workflows/agent-os.yml'
```

### Getting Job IDs for a Failed Run
```bash
# List all runs with workflow name + branch
gh api -H 'Accept: application/vnd.github+json' \
  '/repos/{owner}/{repo}/actions/runs?per_page=5' | \
  python3 -c "
import sys,json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs[:5]:
    print(r['id'], r['name'], r['status'], r['conclusion'], r['head_sha'][:7])
"

# Then get jobs for a run
gh api -H 'Accept: application/vnd.github+json' \
  '/repos/{owner}/{repo}/actions/runs/{run_id}/jobs' | \
  python3 -c "
import sys,json
for job in json.load(sys.stdin)['jobs']:
    print(f'  {job[\"name\"]} | {job[\"status\"]} | {job[\"conclusion\"]}')
"
```
