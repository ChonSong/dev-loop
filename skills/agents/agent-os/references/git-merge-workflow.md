# agent-os Git Merge Workflow

## Scenario: Local uncommitted changes + remote has new commits

This happens when local frontend work is in progress while CI/other sessions push to origin.

### Steps

```bash
cd /opt/data/agent-os

# 1. Check state
git status --short          # local modifications
git log --oneline -5        # local HEAD
git fetch origin
git log --oneline origin/main -5  # remote HEAD

# 2. Check what remote added (usually safe new files)
git diff --stat HEAD..origin/main

# 3. Fast-forward merge (local changes stay as uncommitted)
git merge origin/main -m "Merge origin/main"
# If remote added only new files (no overlap), this is a clean fast-forward
# Local modifications are NEVER touched by a fast-forward

# 4. Verify
git log --oneline -5        # should show both local and remote history
git status --short          # local changes still present

# 5. Stage, commit, push local work
git add <files>
git commit -m "type(scope): description"
git push origin main
```

### Key Insight

`git merge origin/main` with uncommitted working changes does a **fast-forward** (no merge commit needed if no divergence). Your uncommitted files are untouched. This is safe when:

- Remote added new files only (e.g., docs, new pages)
- Remote didn't modify the same files you have local changes in

If there ARE overlapping changes, git will refuse the merge and tell you to commit/stash first.

### Common Pattern

Remote often adds docs (STATE_OF_AGENT_OS.md) or backend fixes while local has frontend work. These never conflict.

### Commit Message Convention

Follow conventional commits for agent-os:
- `feat(scope):` — new feature
- `fix(scope):` — bug fix
- `refactor(scope):` — code restructure
- `docs:` — documentation only

Scopes: `frontend`, `backend`, `FileExplorerPage`, `ContainerPage`, etc.
