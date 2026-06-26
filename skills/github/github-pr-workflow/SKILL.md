---
name: github-pr-workflow
description: "GitHub PR lifecycle: branch, commit, open, CI, merge."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Auth Methods (in priority order)

**Preferred: SSH agent forwarding** (no tokens in prompts)

On hpprobook (Ubuntu host), the hermes container has SSH agent forwarding enabled. From inside the container, `ssh sean@localhost` works without a password because the agent socket is mounted. The host's `gh` CLI is already authenticated via keyring.

```bash
# All gh/git operations via SSH to host — no tokens needed in prompts
ssh -o StrictHostKeyChecking=no sean@localhost "gh run list --repo ChonSong/agent-os --limit 3"
ssh -o StrictHostKeyChecking=no sean@localhost "cd /path/to/repo && git pull origin main"
```

This pattern should be used whenever the host has gh authenticated, which is the case for Sean's setup.

**Alternative: Encrypted token store**

If gh is NOT available on the host but you need a GitHub token, encrypt it with a passphrase using OpenSSL:

```bash
# Encrypt a token
echo 'ghp_YOUR_TOKEN' | openssl enc -aes-256-cbc -salt -pass pass:'dawn of dooyle' -a > ~/.credentials/github_token.enc

# Decrypt when needed
TOKEN=$(ssh -o StrictHostKeyChecking=no sean@localhost "openssl enc -aes-256-cbc -d -a -pass pass:'dawn of dooyle' -in ~/.credentials/github_token.enc")
```

The passphrase "dawn of dooyle" is a memorable phrase — encode it in the skill, not in memory. The encrypted file lives at `~/.credentials/` on the host and is gitignored.

**Fallback: Direct token in environment**

```bash
# Determine which method to use
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHTHON_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
```

**Rule: Never put raw GitHub tokens in cron prompts.** If a cron needs gh, it SSHs to the host. If it absolutely must have the token directly, use the encrypted store.

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

### List Recent Runs (git + curl)

```bash
# List recent workflow runs (per_page goes as a query param)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?per_page=5" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for run in data['workflow_runs'][:5]:
    print(run['id'], run['name'][:50], run['status'], run['conclusion'] or 'null', run['head_sha'][:7])
"
```

### Get Jobs for a Run (git + curl)

```bash
# Get job IDs and conclusions for a specific run
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/jobs" \
  | python3 -c "
import sys, json
for job in json.load(sys.stdin)['jobs']:
    print(f'  {job[\"name\"]} | {job[\"status\"]} | {job[\"conclusion\"]}')
    if job['conclusion'] == 'failure':
        print(f'    → logs_url: {job[\"logs_url\"]}')
"
```

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### GitHub API Debugging (no gh needed)

When `gh` is unavailable on the machine, use the GitHub REST API directly with a token. This is more reliable than `gh` in containerized environments where `gh` may not be installed.

```python
import urllib.request, json

GH = "https://api.github.com/repos/ChonSong/agent-os"
TOKEN = "ghp_YOUR_TOKEN_HERE"  # or use GH_TOKEN from env

def api(path):
    req = urllib.request.Request(f"{GH}{path}",
        headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

# List recent workflow runs
runs = api("/actions/runs?per_page=5")
for r in runs['workflow_runs']:
    print(r['head_sha'][:7], r['conclusion'] or r['status'], r['name'])

# Get jobs for a failing run
jobs = api(f"/actions/runs/{RUN_ID}/jobs")
for j in jobs['jobs']:
    print(f"  {j['name']}: {j.get('conclusion', 'pending')}")
    if j.get('conclusion') == 'failure':
        # Fetch logs via the redirect URL
        print(f"    → logs: {j.get('logs_url', '')[:80]}...")
```

### Git Accidental Commit Recovery

When `git add -A` accidentally stages unrelated files (binaries, generated files, new directories) alongside your intended changes:

```bash
# Undo the bad commit but KEEP all staged changes
git reset --soft HEAD~1

# Unstage only the unwanted files (keeps them on disk)
git rm --cached unwanted_file.bin
git rm --cached path/to/unwanted_directory/

# Commit just the intended changes
git commit -m "your correct message"

# Force push to fix the remote
git push --force-with-lease
```

**Never use `git reset --hard`** — it discards your working tree changes too.

This situation happens when: `git add -A` picks up compiled artifacts (Go binaries in `infra/CasaOS/agent/agent`, TypeScript build output in `.nx/`, Python `.pyc` files) that weren't gitignored before a commit.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

## 6. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

### Handling Diverged Remote (Single Local Commit + Unstaged Changes)

When `git push` fails with `! [rejected] main -> main (fetch first)` and you have **1 committed change + unstaged changes**, use `git stash -u`:

```bash
# 1. Stash unstaged changes
git stash -u

# 2. Pull with rebase (your commit moves to top of origin/main)
git pull --rebase origin main

# 3. Pop your unstaged changes
git stash pop

# 4. Push
git push origin main
```

This handles the case where remote has new commits but your local working tree has both committed and uncommitted work. The stash preserves uncommitted changes across the rebase.

**Step 1: Save your uncommitted work as a patch**
```bash
# Save the full diff between your HEAD and origin/main (works even after reset)
git diff HEAD origin/main > /tmp/my-changes.patch
wc -l /tmp/my-changes.patch  # verify it has content
```

**Step 2: Fetch and reset to clean origin/main**
```bash
git fetch origin main
git reset --hard origin/main
```

**Step 3: Try `--3way` apply first (handles partial conflicts)**
```bash
git apply --3way /tmp/my-changes.patch 2>&1
```
This performs a three-way merge using the patch's index lines as the base. Files that changed only on your side apply cleanly. Files that also changed upstream show as conflicts you can resolve manually.

**Step 4: If --3way leaves files that don't exist in the index** (common for genuinely new files from your commits):
```bash
# Extract genuinely new files from the patch
python3 << 'EOF'
import re
with open('/tmp/my-changes.patch') as f:
    content = f.read()
parts = re.split(r'^(diff --git .+)$', content, flags=re.MULTILINE)
for i in range(1, len(parts)-1, 2):
    header = parts[i]
    body = parts[i+1]
    m = re.match(r'^diff --git a/(.+) b/(.+)$', header)
    if m and body.startswith('new file mode'):
        path = m.group(1)
        print(f"NEW FILE: {path}")
EOF
```

**Step 5: Recover from reflog if commits were wiped** (alternative to patch approach):
```bash
# Find the dangling commits
git reflog | head -10
# Example output:
#   4f6a760 HEAD@{1}: commit: feat(dashboard): CasaOS-style shell + agent-core + full pages
#   2b461ce HEAD@{2}: commit: feat(observability): add AIEAgentHook...
#   44c9bcd HEAD@{3}: reset: moving to origin/main

# Restore a commit's files onto current HEAD without moving HEAD
git checkout 4f6a760 -- .
git status --short  # see what was restored
```

Combine: use reflog to get individual commits, then `git checkout <sha> -- .` to bring their files into the current index, then commit as a single new commit.

**Step 6: Resolve conflicts from --3way if any remain**
```bash
# For each file with conflicts:
# 1. Edit the file to resolve
# 2. git add <file>
git add <resolved-files>
git commit -m "feat: <description> (merged from divergent branch)"
git push origin main
```

## 7. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
