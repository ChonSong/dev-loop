# Work Discovery Investigation Cycle

How to find real, safe work when starting an autonomous continuation cycle with no predefined task. This is the Phase 0 of any auto-continue session.

## Step 1: Browse Recent Sessions

```python
session_search()  # no query = browse mode, shows last 3 sessions + previews
```

Extract: what projects were active, what was left incomplete, what decisions were made. Then drill into specific topics:

```python
session_search(query="HWC gto-wizard linkedin", limit=3)
```

Sessions already searched are cached — you'll get them faster on subsequent queries.

## Step 2: Map the Workspace

**Critical pitfall:** The auto-continue instructions say workspace is at `/workspace` — it is NOT. The actual layout is:

| Location | Content |
|----------|---------|
| `/opt/data/<project>` | Persistent git repos (hermes-web-computer, everything-dashboard, etc.) |
| `/tmp/<project>` | Ephemeral repos (gto-wizard-clone, PokerHandEvaluator — wiped on container restart) |
| `/opt/data/.hermes/` | Hermes config, cron, plugins, skills |
| `/opt/data/skills/` | Agent skills library (what you're editing now) |

Always find repos first:
```bash
find / -maxdepth 4 -name ".git" -type d 2>/dev/null | grep -v node_modules | grep -v ".cache" | grep -v ".local" | sort
```

## Step 3: Assess Each Active Repo

For each repo that had recent activity (from Step 1 or from git log):

```bash
cd /path/to/repo && git log --oneline -15 && git status --short
```

Check:
- **Recent commits** — what was last worked on
- **Uncommitted changes** — work in progress that needs finishing or cleaning up
- **Branch** — are you on main/HEAD or a feature branch
- **Tags** — `git tag -l | sort -V` for release boundaries

## Step 4: Check GitHub for Open Work

```bash
# Check open issues (no pipe-to-interpreter)
curl -sL "https://api.github.com/search/issues?q=repo:ChonSong/<repo>+is:open+is:issue" | head -50
# Check open PRs
curl -sL "https://api.github.com/search/issues?q=repo:ChonSong/<repo>+is:open+is:pr" | head -50
```

**Security scanner constraint:** Pipe-to-interpreter patterns (`curl | python3`) are blocked. Use `execute_code` with `urllib.request` instead for automated processing.

```python
import urllib.request, json
url = "https://api.github.com/search/issues?q=repo:ChonSong/<repo>+is:open"
resp = urllib.request.urlopen(url)
data = json.loads(resp.read())
print(f"Open: {data['total_count']}")
```

## Step 5: Search for TODO/FIXME/HACK Markers

```bash
grep -r "FIXME\|TODO\|HACK" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.go" -l 2>/dev/null | grep -v node_modules | grep -v ".next" | grep -v ".venv" | grep -v ".turbo"
```

## Step 6: Check Plans and Trackers

```
/opt/data/<project>/plans/              — HWC-style plan documents
/opt/data/<project>/DEVELOPMENT_PLAN.md  — GTO-style development plan
/opt/data/<project>/docs/ROADMAP.md      — Roadmap docs
/opt/data/<project>-state/PHASE_TRACKER.json  — Phase engine trackers
/opt/data/project-state/<project>/PHASE_TRACKER.json  — Alternative path
```

Look for:
- Phases marked "pending" or "in_progress"
- Sections that say "remaining work" or "next"
- Steps that have acceptance criteria but no commit evidence

## Step 7: Check Uncommitted Changes Closely

Not all uncommitted changes are meaningful, but some are:

| Pattern | Meaning | Action |
|---------|---------|--------|
| `M app/file.ts` | Modified tracked file | Check diff — could be work in progress |
| `?? new_file.py` | Untracked file | Could be new work, verify scripts, or temp artifacts |
| `M sw.js` | Service worker rebuild | Auto-generated, skip |
| `?? node_modules/` or `.turbo/` | Build artifacts | Skip (already in gitignore) |
| `M verify_*.py` | Verification script | Content changed — check if it reveals test state |

## Decision: Does Work Exist?

**A clear safe path requires ALL of:**
1. Exact next step identifiable (from plan, issue, session log, or uncommitted diff)
2. Change is well-understood and low-risk
3. You have the context to implement correctly
4. It hasn't been done already (git log check)

**Hard NOs:** credentials, auth/billing, production deployments, user-design decisions, guessing intent.

**If no clear path after 3 consecutive cycles:** Report findings and reduce to read-only cycle (skip execution).

## Repo Scan Template

```bash
for dir in /opt/data/repo1 /opt/data/repo2 /tmp/repo3; do
  if [ -d "$dir/.git" ]; then
    echo "=== $dir ==="
    cd "$dir" && echo "Recent commits:" && git log --oneline -5 2>/dev/null && echo ""
    echo "Status:" && git status --short 2>/dev/null | head -10 && echo ""
  fi
done
```
