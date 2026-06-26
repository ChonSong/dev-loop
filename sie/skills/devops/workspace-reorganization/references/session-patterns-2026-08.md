# Workspace Reorganization — Session Patterns (2026-08)

## Large Directory Gotchas

### `cp -r` hanging on node_modules
When merging `knowledge-graph/` (9MB) into `hermes-guide/`, `cp -r` hung indefinitely because of `node_modules/`. Fix: move files selectively excluding heavy dirs:
```bash
for f in source/*; do
  [ "$f" != "source/node_modules" ] && [ "$f" != "source/screenshots" ] && cp -r "$f" dest/
done
```

### Root-owned files from container
`forrest-plan-and-track/` (957MB) had root-owned venv files. `chown` and `rm` both failed with "Operation not privileged" from the container. These must be cleaned up from the host via SSH or manually.

### `git add -A` over-staging
Running `git add -A` after moving files stages ALL subdirectories including embedded git repos (skills/, memory/, docs/, etc.). The workspace repo (hermes-knowledge-graph) should NOT track these. Fix:
```bash
git reset HEAD  # unstage everything
git add .gitignore AGENTS.md SOUL.md ...  # stage only root files
# Add embedded repos to .gitignore BEFORE committing
```

## Permission Denied Patterns
- `sudo` not available in container
- SSH to host broken (port 22 refused, identity file missing)
- Root-owned files can only be cleaned from host
- Workaround: note manual action items, don't fight permissions

## Merge Collision Detection
Before merging dir A into dir B:
```bash
ls A/ | sort > /tmp/a.txt
ls B/ | sort > /tmp/b.txt
comm -12 /tmp/a.txt /tmp/b.txt  # shows filename conflicts
```

## Audit Depth: Reading README/Plan Files

When auditing a directory, always read at minimum:
- `README.md` — what is this?
- `PLAN.md` or `PROGRESS.md` — is it active?
- Check `git log --oneline -3` — last commit date
- Check `git status` — any uncommitted work?

A directory with a detailed plan but zero commits and a "Day 0 — Not started" progress board is a dead project. Archive it, don't leave it cluttering the root.

## Moving Projects Out of Workspace

Projects with their own GitHub remote should NOT live inside the workspace repo. Move them:
```bash
# From workspace
mv /workspace/project-name ~/project-name

# Verify the remote still works
cd ~/project-name && git remote -v && git status
```

The workspace repo is for workspace-level files only. Projects with `git remote -v` showing github.com should be at `~/project-name/`, not `/workspace/project-name/`.

## `rm -rf` Hanging on Git Objects (2026-09)

When deleting a directory that was a git repo (has `.git/objects/` with thousands of files), `rm -rf` can hang indefinitely.

**Fix:** Delete files and directories in separate passes:
```bash
find /path/to/dir -type f -delete     # delete all files first (fast)
find /path/to/dir -type d -delete     # then delete empty directories (bottom-up)
```

## Subagent Directory Auditing Blind Spots (2026-09)

When delegating a directory audit to a subagent, it may report directories as "empty" when they have content in subdirectories. Always verify "empty" claims:
```bash
du -sh /path/to/dir                    # check actual size
find /path/to/dir -type f | wc -l      # count files recursively
```

In this session: subagent reported `agent-ops/` and `presentations/` as empty. Both had real content in subdirectories.
