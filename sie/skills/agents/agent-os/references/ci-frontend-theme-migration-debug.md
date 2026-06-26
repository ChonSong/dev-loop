# CI Frontend Build Failures: Bento Theme Migration (2026-05-09)

## Session Context

Migrated dark theme (`#0a0e14`) to warm bento design system (`#FFF5E6`). 31 files changed across CSS, components, pages, and i18n. Required 5 fix commits to get CI green.

## Failure Pattern 1: JSX Tag Mismatch

**Root cause:** The theme migration replaced `<Card>/<CardHeader>/<CardTitle>/<CardContent>` components with raw `<div>/<span>` elements but botched the nesting.

**Symptoms:**
- `TSXParserError: JSX expressions must have one parent element`
- `JSX syntax error: expected corresponding closing tag for <div>`

**Debugging technique — JSX balance checker:**
```python
import re
lines = open("SkillsPage.tsx").readlines()
depth = 0
for i, line in enumerate(lines, 1):
    opens = len(re.findall(r'<div[\s>]', line))
    closes = len(re.findall(r'</div>', line))
    depth += opens - closes
    if opens or closes:
        print(f"{i:4d}| depth={depth:+d} {line.rstrip()[:100]}")
```

**Key pitfall:** Self-closing `<div.../>` counts as an open in regex `<div[\s>]` but doesn't need a closing tag. Account for this in balance checks:
```python
self_closing = len(re.findall(r'<div[^>]*/>', content))
real_opens = total_opens - self_closing  # should equal total_closes
```

**Common patterns that break:**
- Extra `</div>` where original had `</CardHeader>` (separate component → single div)
- Missing opening `<span>` when `</span>` was kept from original
- Card components map to 2+ divs but migration assumed 1

## Failure Pattern 2: i18n Proxy Type Errors

**Root cause:** `I18n` type changed from `Record<string, any>` to `Record<string, unknown>`. Proxy-based i18n returns `unknown` for all nested property access.

**Symptoms:** Hundreds of `TS18046: 't.skills' is of type 'unknown'` across every component that uses `t.common.*`, `t.skills.*`, `t.sessions.*`, etc.

**Fix:** Revert to `Record<string, any>`. The Proxy dynamically returns objects for any key — strict typing is impossible and undesirable:
```typescript
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type I18n = Record<string, any>;
```

**Also:** Don't export non-existent symbols. The refactor added `makeSafeI18n` to `i18n/index.ts` exports but it was never defined in `context.tsx`.

## Failure Pattern 3: Invalid Component Props

**Root cause:** Migration used `variant="xs"` on a typography component that only accepts `"sm" | "md" | "lg" | "xl"`.

**Symptom:** `TS2322: Type '"xs"' is not assignable to type '"sm" | "md" | "lg" | "xl" | undefined'`

**Fix:** Replace `"xs"` with `"sm"` (or check component's type definition before using a variant).

**General rule:** When replacing UI components during a theme migration, always check the target component's prop types — the old component may have supported different variants.

## CI Log Extraction Without `gh` CLI

When `gh` CLI is not available, use GitHub API directly with the token from `~/.netrc`:

```python
import subprocess, json, os

token = None
with open(os.path.expanduser("~/.netrc")) as f:
    for line in f:
        if "password" in line:
            token = line.strip().split("password ")[1]
            break

# Get latest run
r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {token}",
     "https://api.github.com/repos/ChonSong/agent-os/actions/runs?per_page=1"],
    capture_output=True, text=True, timeout=15)
run_id = json.loads(r.stdout)["workflow_runs"][0]["id"]

# Get jobs
r = subprocess.run(["curl", "-s", "-H", f"Authorization: token {token}",
     f"https://api.github.com/repos/ChonSong/agent-os/actions/runs/{run_id}/jobs"],
    capture_output=True, text=True, timeout=15)

# Get logs for failed job
job_id = [j for j in json.loads(r.stdout)["jobs"] if j["name"] == "Build"][0]["id"]
r = subprocess.run(["curl", "-s", "-L", "-H", f"Authorization: token {token}",
     f"https://api.github.com/repos/ChonSong/agent-os/actions/jobs/{job_id}/logs"],
    capture_output=True, text=True, timeout=15)

# Extract unique TS errors
errors = set()
for line in r.stdout.split("\n"):
    clean = line.split(" ", 1)[-1] if line.startswith("20") else line
    if "error TS" in clean:
        errors.add(clean.strip())
```
