---
name: project-decommissioning
description: "Safely remove a project from the system — containers, images, GitHub repo, local clone, config, skill references, and repo catalog. Counterpart to repo-portfolio-audit: audit tells you WHAT to delete, this tells you HOW."
version: 1.0.0
---

# Project Decommissioning

Execute a safe, thorough teardown of a project after the user has decided to remove it. Follow the steps in order — skipping verification or backup can lose data permanently.

## When to Use

- User says "delete X from the system" / "scrap project Y"
- User says "yes" to a deletion recommendation from `repo-portfolio-audit`
- A project is being replaced and no longer needs its old repo, containers, or config

## Process

### Phase 1 — Inventory What's Worth Keeping

Before deleting anything, scan for custom code that isn't replicated elsewhere:

```bash
# Check what the project is
cd /home/sc/repos/<project>
ls -la
du -sh .

# Check for custom source code (not vendored deps)
find . -name '*.py' -o -name '*.ts' -o -name '*.js' -o -name '*.go' -o -name '*.rs' | grep -v node_modules | grep -v '.git/' | head -30

# Check docker-compose, Dockerfile, configs
head -50 docker-compose.yml 2>/dev/null
head -50 Dockerfile 2>/dev/null

# Check for custom skills or workspace content
ls -la ~/.<project>/ 2>/dev/null
ls -la <project>-workspace*/ 2>/dev/null

# Check git log and branches
git log --oneline -5
git branch -a

# Check what runs on the host
docker ps --format '{{.Names}} {{.Status}}' | grep <project>
systemctl --user list-units --type=service --all | grep <project>
```

**Key question:** Is the custom code something you wrote, or is it an unmodified upstream fork? Unmodified upstream = no backup needed. Custom code = backup.

### Phase 2 — Backup Assets Worth Keeping

Archive to a dated directory in the workspace:

```bash
mkdir -p /home/sc/workspace/archived-<project>/
# Custom source files
cp -r <path> /home/sc/workspace/archived-<project>/
# Config/soul docs
cp <path> /home/sc/workspace/archived-<project>/
# Custom workspace skills
cp -r <workspace-dir>/skills /home/sc/workspace/archived-<project>/
```

Target: <1MB for pure text backups. If >5MB, you're backing up too much (vendored deps).

### Phase 3 — Stop Containers

```bash
docker rm -f <container1> <container2>
docker images --filter=reference='*<project>*' --format '{{.Repository}}:{{.Tag}} ({{.ID}} {{.Size}})'
docker rmi <image1> <image2>
```

### Phase 4 — Delete GitHub Repo

Check if the repo still exists on GitHub first:

```bash
# Extract token from git remote
python3 -c "import re; content=open('.git/config').read(); m=re.search(r'url = https://[^:]+:([^@]+)@', content); print(m.group(1) if m else '')"
```

Then delete via API (token in Authorization header):

```python
import re, urllib.request
content = open('/home/sc/repos/<project>/.git/config').read()
m = re.search(r'url = https://[^:]+:([^@]+)@', content)
token = m.group(1) if m else ''
# Extract org/repo from remote
remote = [l for l in open('/home/sc/repos/<project>/.git/config') if 'url =' in l][0]
org_repo = remote.split('github.com/')[1].split('.git')[0]
req = urllib.request.Request(
    f'https://api.github.com/repos/{org_repo}',
    method='DELETE',
    headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'})
# Check first (GET), then delete
urllib.request.urlopen(req)  # DELETE
```

**Note:** The token in git remote URLs is a fine-grained GitHub token. It only grants access to repos the user specifically granted it to. If `GET /repos/org/repo` returns 404, the token lacks access or the repo is already deleted — skip the delete.

### Phase 5 — Delete Local Clone

```bash
rm -rf /home/sc/repos/<project>
```

### Phase 6 — Clean Config Directories

```bash
rm -rf ~/.<project>/ ~/.config/<project>/
```

### Phase 7 — Remove Stale Skill References

Check for related skills:

```bash
find ~/.hermes/skills -name '*<project>*' -o -name '*<shortname>*' 2>/dev/null
find ~/.hermes/cache -path '*/skills/*' -name '*<project>*' 2>/dev/null
```

Delete them:

```bash
rm -rf ~/.hermes/skills/<path> ~/.hermes/cache/sync-work/hermes-sync/skills/<path>
```

### Phase 8 — Update Repo Catalog

```bash
cd /home/sc/repos/seans-reporepo
rm -f starred/<org>_<project>.md owned/<org>_<project>.md
# Commit if git tracked
git add -A && git commit -m "remove <project> from catalog" || true
```

### Phase 9 — Verify

- Confirm the backup archive is non-empty and contains expected files
- Confirm containers are stopped: `docker ps | grep <project>` → empty
- Confirm no stale config remains
- Report total disk reclaimed

## Pitfalls

- **Don't delete forks of active upstream projects** — user loses ability to pull from upstream. If upstream is active, consider archiving the local clone but keeping the GitHub fork.
- **Don't delete without backing up custom code first** — WhatsApp bridge, custom skills, soul docs, config templates are one-of-a-kind. The 30 seconds it takes to backup saves hours of regret.
- **Don't delete config from projects that still reference it** — `agent-os/packages/nanobot/` is a facade layer in another project. Leave it — it's part of that project's architecture, not this one's cleanup.
- **The GitHub API token is fine-grained** — it may 404 on repos it doesn't have access to. That doesn't mean the repo is gone — use `git remote show origin` to check.
- **seans-reporepo entries** are just catalog metadata. Delete them to keep the catalog clean, but they're non-critical.

## Related Skills

- `repo-portfolio-audit` — analysis/recommendation phase (run before this)
- `repo-catalog` — catalog management (run this after to update)
- `repo-init` — the inverse operation (creating new projects)
