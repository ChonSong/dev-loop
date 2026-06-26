# CI Debugging Patterns (2026-05-06)

## Root Cause: GHCR Repository Name Must Be Lowercase

**Symptom:** 29 consecutive CI build failures. `docker build` succeeds but `docker push` silently fails.
The actual error from the push step:
```
ERROR: failed to build: invalid tag "ghcr.io/ChonSong/agent-os:...": repository name must be lowercase
```

**Root cause:** `${{ github.repository }}` = `ChonSong/agent-os` — the uppercase `S` in `ChonSong` is rejected by GHCR.

**Important:** `${{ github.repository.toLowerCase() }}` is **NOT valid** in GitHub Actions YAML. JavaScript `.toLowerCase()` cannot be called on template expressions.

**Correct fix — use shell `tr` in each build/push step:**
```yaml
- name: Build
  run: |
    repo_lower=$(echo '${{ github.repository }}' | tr '[:upper:]' '[:lower:]')
    docker build --load -t ghcr.io/${repo_lower}:${{ github.sha }} .

- name: Push
  run: |
    repo_lower=$(echo '${{ github.repository }}' | tr '[:upper:]' '[:lower:]')
    echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
    docker push ghcr.io/${repo_lower}:${{ github.sha }}
```

**Test-build workflow proof:** A minimal test workflow (`test-build.yml`) with plain `docker build --load -t ghcr.io/chonsong/agent-os:latest .` succeeded on first run. This confirmed the Docker infrastructure works — the problem was purely the uppercase repository name in the tag.

## Jobs API Returning Empty (`total_count: 0`)

**Symptom:** `GET /repos/{repo}/actions/runs/{id}/jobs` returns `{"total_count": 0, "jobs": []}` for a run that clearly has jobs (it's failing).

**When this happens:** GitHub's jobs API returns empty for runs where the log files have expired or are otherwise unavailable. The API is unreliable for recently-completed runs.

**Workaround:**
1. Use `gh run view {run_id} --json jobs` from the server (where `gh` is authenticated)
2. Or use GraphQL: `query { repository(owner:"ChonSong",name:"agent-os") { workflowRun(id:"...") { jobs { nodes { name conclusion } } } } }`
3. The run's `conclusion` and `status` are still reliably reported — only per-job/step details may be hidden

## Workflow-Level Failure with 0 Jobs (0-second completion)

**Symptom:** A workflow run completes in 0 seconds with `conclusion: failure` but `jobs: []` from the API.

**Root cause:** The workflow YAML has a structural error — a job reference in `needs:` that doesn't exist, or a YAML parse error at the workflow level.

**This session:** The old `agent-os.yml` had been corrupted through ~30 iterative patches. Replacing it with a clean file (copying the exact same logic but writing fresh) made it work. The accumulated diffs had introduced invisible corruption.

**Fix:** When a workflow run shows 0 jobs + instant completion, rewrite the YAML file from scratch rather than patching further.

## Immediate Failure Pattern (CI Completes in 0 Seconds)

**Symptom:** `gh run list` shows a run completed in 0 seconds — immediately after being triggered.

**Diagnosis:** Check `gh run view {id} --json event,conclusion,headSha,number` to confirm. If `conclusion: failure` with 0s duration, it's a workflow-level parse error.

**Note:** `workflow_dispatch` trigger was configured in YAML but GitHub's API didn't show it as available — the YAML was corrupted but still parseable by git, just not by GitHub Actions.

## Why the Artifact Approach Was Abandoned

The original plan: CI saves image as artifact → notifies server endpoint → server downloads → pushes to GHCR.

**What actually happened:** `docker build-push-action` was failing because of the uppercase GHCR tag. Once that was fixed, CI could push directly to GHCR. The artifact pipeline was unnecessary complexity — the direct push is simpler and faster.

**Current architecture:**
1. CI builds → pushes SHA tag + `latest` tag directly to GHCR (via `docker login` + `docker push`)
2. Server cron (`/home/sean/scripts/agent-deploy.sh`) polls GHCR every 60s
3. New digest detected → `docker pull ghcr.io/chonsong/agent-os:latest` → `docker-compose rm -sf backend && docker-compose up -d backend --pull always`

## CI Run Log Access

**From the server** (where `gh` CLI is authenticated):
```bash
gh api /repos/ChonSong/agent-os/actions/jobs/{job_id}/logs  # raw text
gh run view {run_id} --log-failed   # may return "log not found" for recent runs
gh run view {run_id} --json jobs    # reliable — job names + conclusions
```

**Key job IDs from 2026-05-06 successful run (25438589641):**
- Test (python): 74622336666
- Test (node): 74622336617
- Test (go): 74622336668
- Build: 74623336650
- Deploy: 74622573983

**Last successful SHA before fix:** `cb76b17` (run 25432022463). That run used `load: false, push: true` in the buildx action, which avoided the uppercase tag problem entirely — but the workflow was later overwritten with broken YAML.

## Docker Info from GHA (for reference)

```
Docker version: 28.0.4
BuildKit version: github.com/docker/buildx v0.33.0 f7897eba028583e0071642db3c011e860444f8cf
Builder driver: docker-container
Multi-platform build: true
OCI exporter: true
```
