---
name: skill-selector-prep
description: Weekly cron (Sunday 06:00 UTC) that syncs 5 source skill repos, computes size/category/tag metadata for all local skills, pre-scores them against active workspaces, and writes skill_metadata.json + context_scores.json cache files consumed by skill-selector every turn. Run via cron only.
category: software-development
tags: [skills, cron, cache, prep, autonomous]
required_environment_variables: []
required_commands: ["git", "du", "python3"]
---

## Overview

Runs on the `skill-selector-prep.py` no-agent cron job. The skill says "weekly Sunday 06:00 UTC" but the actual cron job (`65520f7d71f9`) is configured as `0 6 * * 0` which IS weekly Sunday — this is consistent. The daily-vs-weekly discrepancy in older doc versions is resolved: it's weekly.

- `~/.hermes/skill-selector-cache/skill_metadata.json` — all local skills with size, category, tags
- `~/.hermes/skill-selector-cache/context_scores.json` — pre-computed relevance scores per active workspace

Also syncs new skills from 5 source repos into the local skill catalog.

## Source Repos

All 5 repos are cloned on the **host** machine (container has no outbound git), accessed via SSH. Each repo has a distinct format:

```python
SOURCE_REPOS = [
    {"org": "VoltAgent",          "name": "awesome-agent-skills",  "src_name": "voltagent",           "format": "readme"},
    {"org": "mattpocock",         "name": "skills",                "src_name": "mattpocock-skills",    "format": "claude"},
    {"org": "0xNyk",              "name": "awesome-hermes-agent",  "src_name": "0xNyk",               "format": "readme"},
    {"org": "vercel-labs",        "name": "skills",                "src_name": "vercel-labs-skills",   "format": "readme"},
    {"org": "expo",               "name": "skills",                "src_name": "expo-skills",          "format": "readme"},
]
TMP_DIR = "/tmp/skill-selector-prep"

def ssh(cmd: str) -> str:
    """Run command on host via SSH (container has no direct git access)."""
    r = subprocess.run(
        ["ssh", "-i", "/home/hermeswebui/.hermes/container_key",
         "-o", "StrictHostKeyChecking=no", "sean@172.19.0.1", cmd],
        capture_output=True, text=True, timeout=60
    )
    return r.stdout.strip() if r.returncode == 0 else ""
```

**Catalog sizes (as of 2026-05-25):**
| Source | Skills | Format |
|--------|--------|--------|
| voltagent | ~1,117 | README bullet list (`- **[name](url)** - desc`) |
| 0xNyk | ~120 | README mixed (bold links + plain links + maturity tags like `**[beta]**`) |
| local | 153 | Local SKILL.md files |
| mattpocock-skills | 28 | Per-skill SKILL.md in subdirs |
| vercel-labs-skills | ~4 | README |
| expo-skills | ~4 | README |

**Total: 1,441+ skills** (deduped unique, verified 2026-05-25), 481 with LLM summaries. Remaining ~960 score on description-only matching.

## Workflow

### 1. Setup (absolute paths required)

```python
import json, subprocess, time
from pathlib import Path

# HARDCODE paths — do NOT use Path.home() in this container
CACHE_DIR = Path("/home/hermeswebui/.hermes/skill-selector-cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SKILLS_DIR = Path("/home/hermeswebui/.hermes/skills")
TMP_DIR = Path("/tmp/skill-selector-prep")
TMP_DIR.mkdir(exist_ok=True)

def gh(cmd: list[str], **kwargs) -> str:
    # Run gh on the HOST (172.19.0.1) via SSH — gh not available in container
    result = subprocess.run(
        ["ssh", "-i", "/home/hermeswebui/.hermes/container_key",
         "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
         "sean@172.19.0.1", "gh"] + cmd,
        capture_output=True, text=True, **kwargs
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()
```

### 2. Sync Source Repos

```python
def sync_source_repos():
    """Clone/update 5 source repos to /tmp/skill-selector-prep/<name>"""
    for repo in SOURCE_REPOS:
        dest = TMP_DIR / repo["name"]
        if dest.exists():
            subprocess.run(["git", "-C", str(dest), "pull", "--ff-only"], capture_output=True)
        else:
            ssh_url = f"git@github.com:{repo['org']}/{repo['name']}.git"
            subprocess.run(
                ["git", "clone", "--depth", "1", ssh_url, str(dest)],
                capture_output=True,
                env={**__import__("os").environ, "GITHUB_TOKEN": ""}
            )
```

Extract skills from each repo format:

```python
def extract_skills_from_readme(repo_path: Path, repo_name: str) -> list[dict]:
    """Parse readme for skill entries (name + description + link)."""
    readme = (repo_path / "README.md").read_text()
    skills = []
    # VoltAgent/awesome-agent-skills uses ## Skill Name\nDescription format
    import re
    pattern = re.compile(r'##\s+\[([^\]]+)\]\([^\)]+\)\s*\n*([^\n#]+)', re.MULTILINE)
    for match in pattern.finditer(readme):
        name, desc = match.group(1).strip(), match.group(2).strip()[:200]
        skills.append({"name": name, "description": desc, "source": repo_name, "tags": []})
    return skills

def extract_skills_from_claude_dir(repo_path: Path, repo_name: str) -> list[dict]:
    """Parse .claude dirs with SKILL.md files."""
    skills = []
    for skill_file in repo_path.rglob("SKILL.md"):
        rel = skill_file.parent.relative_to(repo_path)
        frontmatter = skill_file.read_text().split("---")[1] if "---" in skill_file.read_text() else ""
        name = rel.parts[-1] if rel.parts else skill_file.stem
        skills.append({"name": name, "description": frontmatter[:200], "source": repo_name, "tags": []})
    return skills

def parse_skills_source(repo_path: Path, repo: dict) -> list[dict]:
    if repo["format"] == "readme":
        return extract_skills_from_readme(repo_path, repo["name"])
    elif repo["format"] == "claude":
        return extract_skills_from_claude_dir(repo_path, repo["name"])
    return []
```

### 3. Compute Local Skill Metadata

```python
def get_skill_size(skill_path: Path) -> float:
    """Get skill dir size in MB using du."""
    result = subprocess.run(
        ["du", "-sm", str(skill_path)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return float(result.stdout.split()[0])
    return 0.0

def load_local_skills() -> list[dict]:
    """Scan ~/.hermes/skills/ for all local SKILL.md files."""
    skills = []
    if not SKILLS_DIR.exists():
        return skills
    for category_dir in SKILLS_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        for skill_dir in category_dir.iterdir():
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            # Parse frontmatter
            text = skill_md.read_text()
            frontmatter = {}
            if text.startswith("---"):
                end = text.find("---", 3)
                if end > 0:
                    for line in text[3:end].strip().split("\n"):
                        if ":" in line:
                            k, v = line.split(":", 1)
                            frontmatter[k.strip()] = v.strip().strip('"')
            skills.append({
                "name": skill_dir.name,
                "path": str(skill_dir),
                "category": category_dir.name,
                "description": frontmatter.get("description", ""),
                "tags": frontmatter.get("tags", "").strip("[]").replace("'", "").split(",") if frontmatter.get("tags") else [],
                "size_mb": get_skill_size(skill_dir),
                "is_local": True,
            })
    return skills
```

### 4. Merge Remote Skills (dedup by name)

```python
def merge_remote_skills(local_skills: list[dict], remote_skills: list[dict]) -> list[dict]:
    """Merge remote skills, skipping if local version exists."""
    local_names = {s["name"] for s in local_skills}
    for rs in remote_skills:
        if rs["name"] not in local_names:
            rs["is_local"] = False
            rs["size_mb"] = 0.0
            local_skills.append(rs)
    return local_skills
```

### 5. Compute Context Scores

```python
WORKSPACE_CONTEXTS = {
    "hermes-web-computer": {
        "path": "/workspace/hermes-web-computer",
        "keywords": ["go", "svelte", "tile", "component", "backend", "docker", "hermes-computer", "dock", "panel", "layout"],
        "weight": 1.5,
    },
    "agent-os": {
        "path": "/workspace/agent-os",
        "keywords": ["node", "react", "express", "postgres", "api", "docker", "agent", "page", "spa", "backend"],
        "weight": 1.2,
    },
    "seans-reporepo": {
        "path": "/workspace/seans-reporepo",
        "keywords": ["repo", "catalog", "star", "github", "readme", "tag", "combinatorial"],
        "weight": 1.0,
    },
    "repo-transmute-v2": {
        "path": "/workspace/repo-transmute-v2",
        "keywords": ["migrate", "ast", "component", "vision", "llm", "screenshot", "transpile", "react", "svelte"],
        "weight": 1.3,
    },
}

def compute_context_scores(skills: list[dict]) -> dict[str, float]:
    """Pre-score every skill against each workspace context."""
    scores = {}
    for skill in skills:
        score = 0.0
        skill_text = f"{skill.get('name','')} {skill.get('description','')} {' '.join(skill.get('tags',[]))}".lower()
        for ws_name, ctx in WORKSPACE_CONTEXTS.items():
            if not ctx["path"]:
                continue
            matches = sum(1 for kw in ctx["keywords"] if kw in skill_text)
            if matches > 0:
                score += matches * ctx["weight"]
        scores[skill["name"]] = round(score, 3)
    return scores
```

### 6. Write Cache Files

```python
def write_cache(skills: list[dict], context_scores: dict):
    # skill_metadata.json — full list with size/category/tags
    metadata = [{
        "name": s["name"],
        "category": s.get("category", ""),
        "description": s.get("description", ""),
        "tags": s.get("tags", []),
        "size_mb": s.get("size_mb", 0.0),
        "is_local": s.get("is_local", False),
        "source": s.get("source", "local"),
    } for s in skills]
    
    with open(CACHE_DIR / "skill_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    # context_scores.json — pre-computed workspace relevance
    with open(CACHE_DIR / "context_scores.json", "w") as f:
        json.dump(context_scores, f, indent=2)
    
    # refresh timestamp
    with open(CACHE_DIR / "last_refresh.txt", "w") as f:
        from datetime import datetime
        f.write(datetime.utcnow().isoformat() + "Z\n")
```

### 7. Check Repo Updates (changed since last run)

```python
def check_source_updates() -> list[str]:
    """Return list of source repos that have new commits since last run."""
    changed = []
    state_file = CACHE_DIR / "source_state.json"
    prev_state = {}
    if state_file.exists():
        prev_state = json.loads(state_file.read_text())
    
    new_state = {}
    for repo in SOURCE_REPOS:
        # Check if repo local copy exists and has new commits
        dest = TMP_DIR / repo["name"]
        if dest.exists():
            result = subprocess.run(
                ["git", "-C", str(dest), "log", "-1", "--format=%ct", "HEAD"],
                capture_output=True, text=True
            )
            ts = result.stdout.strip()
            new_state[repo["name"]] = ts
            if prev_state.get(repo["name"]) != ts:
                changed.append(repo["name"])
    
    with open(state_file, "w") as f:
        json.dump(new_state, f)
    
    return changed
```

### 8. Notify

```python
def build_notify_message(changed_repos: list[str], total_skills: int, cache_age_h: float) -> str:
    parts = [f"skill-selector-prep done — {total_skills} skills indexed"]
    if changed_repos:
        parts.append(f"Updated sources: {', '.join(changed_repos)}")
    if cache_age_h > 24:
        parts.append(f"Cache was stale ({cache_age_h:.0f}h), refreshed")
    return " | ".join(parts)
```

## Cron Config

```yaml
name: skill-selector-prep (weekly)
schedule: "0 6 * * 0"   # 06:00 UTC every Sunday
action: create
script: skill-selector-prep.py   # no_agent=True, script runs directly
deliver: local   # save output only, don't spam user
```

## ⚠️ Initial Setup — Cron Has Never Fired

Job `65520f7d71f9` was created 2026-05-24 but **never executed** (`last_run_at: null`). The cache is empty or stale.

**To build the cache NOW** (one-time, before the weekly cron takes over):

```bash
# Run the prep script directly to populate the cache immediately
cd /home/hermeswebui/.hermes/scripts && python3 skill-selector-prep.py

# Then verify
ls -la /home/hermeswebui/.hermes/skill-selector-cache/
cat /home/hermeswebui/.hermes/skill-selector-cache/skill_metadata.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} skills indexed')"
```

After the initial run, the weekly cron (Sunday 06:00 UTC) keeps it fresh automatically.

## Pitfalls

- Path.home() resolves to `/home/hermeswebui/.hermes/home` in this container — **always use absolute paths** in the script (`/home/hermeswebui/.hermes/...`) rather than `Path.home()` or `~/.hermes/...`
- Three source repos share the name "skills" locally (mattpocock/skills, vercel-labs/skills, expo/skills). They are stored in TMP_DIR under distinct names (mattpocock-skills, vercel-skills, expo-skills) but all contribute a skill named "skills" — the first one found wins in the `merge_skills` dedup. Accept this limitation; exact deconfliction requires namespacing by source org.
- `du -sm` on skills with many reference files can be slow — skip if >5s, estimate from file count instead
Remote skill parsing — each format needs a distinct parser:

```python
# VoltAgent (voltagent): line-by-line bullet parser
# Lines: - **[name](url)** - description
#        - **[maturity]** [name](url)** - description  (maturity tag = 1st bold block)
# Use the LAST bold block containing a link as the skill name.
for line in text.split("\n"):
    bold_blocks = re.findall(r'\*\*([^*]+)\*\*', line)
    for bb in reversed(bold_blocks):  # reversed = skip maturity tags
        m = re.search(r'\[([^\]]+)\]\([^\)]+\)', bb)
        if m:
            name = m.group(1)
            break
    dash_parts = line.split(" - ")
    if len(dash_parts) >= 2:
        desc = " - ".join(dash_parts[1:]).strip()

# 0xNyk: plain links in some sections (no **)
# Line: - [name](url) by [author] - description
m = re.match(r'- \[([^\]]+)\]\([^\)]+\)\s+by\s+\[([^\]]+)\]\([^\)]+\)\s*-\s*([^\n]{10,300})', line)

# mattpocock-skills: SKILL.md per subdirectory
# find all SKILL.md files, extract frontmatter description:
for md_path in repo_path.rglob("SKILL.md"):
    content = ssh(f"cat \"{md_path}\"")
    # parse YAML frontmatter → description
```
- Empty `context_scores.json` (first run): `skill-selector` falls back to keyword-only scoring
- On first run, all 5 repos show as "updated" — this is expected, not an error
- If `skill_metadata.json` already exists, compare count before/after to detect repo deletions or additions
- **0xNyk README is NOT a simple bullet list** — it has mixed formatting with `**` bold links, plain `[name](url) by [author]` links, and maturity tags like `**[beta]**`. The original regex pattern `##\s+\[([^\]]+)\]\([^\)]+\)\s*\n*([^\n#]+)` was too strict and matched 0 skills. Fix: parse line-by-line with `re.findall(r'\*\*([^*]+)\*\*', line)` and use the last bold block containing a link as the skill name.
- **Unified README parsing** — All three README formats (VoltAgent `**[name](url)**`, 0xNyk/bold `**[maturity]** [name](url) by [author]**`, 0xNyk/plain `[name](url) by [author]`) parse with a single regex: split on the LAST ` - ` to separate name_block from description, then extract the first markdown link from name_block. This cleanly handles maturity tags without special-casing them.
- **OpenRouter LLM summarization — WORKING 2026-05-25** — The free tier works again via host SSH tunnel. Use `openrouter/free` which routes to free models (nvidia/nemotron-3-nano, poolside/laguna, liquid/lfm-2.5). Container has no outbound network — always call via `ssh sean@172.19.0.1` with `curl ... -d @-` piping JSON payload through stdin. **Critical: use `echo '{payload}' | curl ... -d @-`** (not `-d '{json}'`) because the JSON contains quotes that break `-d` flag embedding.
- **Working prompt format for `openrouter/free`** — JSON dict with empty values, LLM fills them:
  ```
  prompt = f'JSON: {json.dumps({n: "" for n in skills})}. Fill each value with short description (max 55 chars, start with USE WHEN).'
  ```
  Response comes in the `content` field (not `reasoning`). Strip markdown code fences (` ```json ... ``` `) before parsing JSON.
- **Parse response** — `re.search(r'\{[^{}]+\}', text, re.DOTALL)` then `json.loads(m.group())`. Some models embed JSON inside `reasoning` field instead — check both `content` and `reasoning`.
- **Batch summarizer script** — `/home/hermeswebui/.hermes/scripts/summarize-batches.py` — 2.5s sleep between batches, 5 consecutive failures = stop. Run in background with `notify_on_complete=True`.
- **OpenRouter 402 globally (resolved)** — Previously both `openrouter/free` and `openrouter/auto` returned 402 everywhere due to credits exhaustion. Resolved 2026-05-25 — free tier working again. If 402 returns, fall back to MiniMax API directly or find another free model.
- **When 402 fires during batch summary generation** — skills fall back to description-only scoring. Not fatal — summaries are additive, not required.
- **Always SSH to host for git operations** — The container has no outbound network. Git clones, pulls, and `gh` commands must run on `sean@172.19.0.1` via the container key at `/home/hermeswebui/.hermes/container_key`. Direct `git clone https://...` from the container will hang.
- **SSH tunnel: `echo payload | curl -d @-`** — Container routes to external APIs via host SSH. The `echo ... | curl ... -d @-` pattern (piping JSON through stdin) is critical because it avoids quote-escaping issues that break `-d '{json}'` flag embedding when the JSON contains nested quotes. Use absolute paths for the key: `/home/hermeswebui/.hermes/container_key`.

## Verification

```bash
# After running:
cat ~/.hermes/skill-selector-cache/skill_metadata.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} skills, {sum(s[\"size_mb\"] for s in d):.1f}MB total')"
cat ~/.hermes/skill-selector-cache/context_scores.json | python3 -c "import json,sys; d=json.load(sys.stdin); top=sorted(d.items(),key=lambda x:-x[1])[:5]; print('Top scores:',top)"
```

**Calibration notes, raw score data, and source deconfliction** → `references/calibration.md`

## Related

- `skill-selector`: the every-turn meta-skill that reads these cache files