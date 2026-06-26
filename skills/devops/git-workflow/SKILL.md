---
name: git-workflow
description: Git workflow patterns — branching strategies, conventional commits, merge vs rebase, conflict resolution, PR summaries, and clean history.
origin: ECC (adapted for Hermes)
---

# Git Workflow

Git conventions for clean, traceable, professional repositories.

## When to Activate

- Starting a new feature or fix
- Writing commit messages
- Resolving merge conflicts
- Preparing a PR
- Cleaning up messy history

## Branch Strategy

```
main ──────────────────────────────────── (production)
  ├── feat/feature-name                  (new features)
  ├── fix/bug-description                (bug fixes)
  ├── refactor/description               (code cleanup)
  └── chore/description                  (maintenance)
```

## Conventional Commits

```
<type>: <description>

feat: add user authentication
fix: resolve race condition in webhook handler
refactor: extract payment logic into service
docs: update API documentation
test: add integration tests for checkout flow
chore: update dependencies
perf: optimize image loading
ci: add deployment pipeline
```

### Breaking Changes

```
feat: change authentication method

BREAKING CHANGE: Switch from session-based to JWT auth.
All clients must update to include Authorization header.
```

## PR Best Practices

- **Title**: Conventional commit format
- **Description**: What changed, why, how to test
- **Small PRs**: One logical change per PR
- **Link issues**: `Closes #123`
- **Review checklist**: Tests pass, no security issues, docs updated

## Rebase vs Merge

| Scenario | Use |
|----------|-----|
| Feature branch → main | Squash merge (clean history) |
| Sync main into feature | Rebase (linear history) |
| Hotfix to main | Direct commit + cherry-pick |
| Multiple PRs in sequence | Rebase each onto main |

## Conflict Resolution

1. `git fetch origin`
2. `git rebase origin/main`
3. Resolve conflicts in each file
4. `git add <resolved-files>`
5. `git rebase --continue`
6. `git push --force-with-lease` (if rebasing pushed branch)

### Unmerged (Conflicted) Files with Staged Changes

When you have **both** staged changes (`Changes to be committed`) **and** an unmerged conflicted file, `git checkout .` silently fails on the conflicted file — it cannot discard an unmerged path without first choosing a side (`--ours` or `--theirs`).

**Scenario:** You staged debug logging in `cron/scheduler.py`. Meanwhile `run_agent.py` has merge conflicts. You want to keep your staging but discard the conflicting local version.

```bash
# Step 1: Resolve the conflicted file using upstream version
git checkout --theirs run_agent.py     # Takes upstream's version of the conflicting file
git add run_agent.py                   # Marks conflict as resolved

# Step 2: Now pull — working tree is clean except your staged changes
git pull --ff-only
```

**What `git checkout .` does on an unmerged file:** exits with error, does nothing. Does NOT unstage anything.

**What `git checkout --theirs <file>` does:** replaces the conflicting local version with the upstream version from the merge-base. Safe to `add` and proceed.

**Key invariant:** `git pull --ff-only` only succeeds when the working tree is clean (no unmerged paths). `git status` should show only staged changes before pulling.

### Divergent Branch Recovery

When local and remote have diverged (possibly with unrelated histories), and normal `git pull --rebase` fails:

```bash
# Scenario: local has commits, remote has different commits, git pull fails
git fetch origin
git reset --hard origin/main   # Discard local commits that conflict
# Re-apply your changes:
git add -A
git commit -m "your changes"
git push                       # Normal push now works

# If that's too destructive and you want to keep local work:
git stash
git pull origin main --no-rebase --allow-unrelated-histories
git stash pop
git add -A && git commit --amend --no-edit
git push --force-with-lease    # Requires approval
```

**Key insight:** When `git pull --rebase` fails with "unrelated histories" and `git merge` also fails, `git push --force-with-lease` is the fastest path forward — it overwrites the remote with your version while protecting against concurrent pushes by other collaborators.

## Clean History

- Squash WIP commits before merging
- Use `git commit --amend` for typos in last commit
- `git log --oneline --graph` to review history
- Never rewrite public/main branch history

## Hermes Adaptation

- All commits from Hermes use conventional commits
- PR summaries include: changes, testing notes, screenshots (if UI)
- When pushing from container: `ssh -i /opt/data/container_key sean@localhost "cd /path && git ..."`
- For agent-os: commits go to `ChonSong/agent-os` main branch

### Diagnosing "Missing" Files in Git

When a bootstrap fails because a file is "missing" from a remote clone, verify the file actually exists in git before building complex workarounds:

```bash
# Wrong approach: assume file is missing and try to add it via API
# Correct approach: check git ls-files on the remote HEAD
git ls-files <path>                    # checks LOCAL index — misleading if index stale
gh api repos/OWNER/REPO/git/trees/HEAD?recursive=1 | python3 -c "
  import json,sys; tree=json.load(sys.stdin)
  print([e['path'] for e in tree['tree'] if e['path'].startswith('docker/')])
"                                     # checks ACTUAL remote HEAD — authoritative

# Alternative: git ls-remote (doesn't need fetch)
git ls-remote origin <path>
```

**Real case:** `docker/` directory was assumed missing from hermes-sync because `git status` on the host showed it untracked. However, `gh api .../git/trees/HEAD?recursive=1` confirmed docker/ WAS already committed at remote HEAD. The local host had `git reset --hard origin/master` applied, which pulled the remote state — and remote already had docker/. The file was never actually missing.

**Rule:** When a remote file appears absent, always verify against `origin/HEAD` via GitHub API or `git ls-remote`, not the local working tree or index. Local and remote can diverge.

### SSH Git Operations Through Container

When git operations on the host fail due to permission issues (e.g., `.git/FETCH_HEAD` root-owned):

```bash
# Verify files exist in git via SSH without needing to pull
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'cd /home/sean/hermes-sync && git ls-files docker/'

# Check remote HEAD contents via API through SSH
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  'gh api repos/ChonSong/hermes-sync/git/trees/HEAD?recursive=1' | \
  python3 -c "import json,sys; t=json.load(sys.stdin); print([e['path'] for e in t['tree'] if 'docker' in e['path']])"
```

**When `.git/FETCH_HEAD` is root-owned:** this blocks `git pull`. Use `gh api` via SSH to verify remote state directly, bypassing git's fetch mechanism entirely.
