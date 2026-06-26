---
name: repo-discovery
description: "Locate, identify, and assess a user's code repositories across filesystem and GitHub. Triggered when user mentions a repo name, asks what's on their GitHub, or says 'do you have access to X'."
version: 1.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [github, filesystem, investigation, repo-locating, discovery]
    category: github
---

# Repo Catalog Building

Build a structured catalog/index of GitHub owned and starred repos for ideation, discovery, and combinatorial application design.

## When to Use

- User wants to audit/summarize their GitHub repos
- User wants to explore what they own/star for app ideas
- User asks "what repos do I have?" or wants a searchable index
- Combining existing repos into new applications

## Quick Start

1. Create a new repo (e.g., `ChonSong/seans-reporepo`)
2. Clone it locally
3. Run: `python3 scripts/generate-catalog.py <repo-dir>`
4. Commit and push

The script auto-fetches via `gh` CLI (must be authenticated).

## Directory Structure

```
repo-catalog/
├── README.md              # Human-readable index
├── owned/
│   ├── agent-os.md
│   ├── repo-transmute.md
│   └── ...
├── starred/
│   ├── repomix.md
│   ├── opencode.md
│   └── ...
└── scripts/
    └── query-repo-catalog.py  # Search/filter utility
```

## YAML Frontmatter Fields

```yaml
repo: ChonSong/agent-os           # owner/name (required)
url: https://github.com/ChonSong/agent-os  # full URL
description: "Self-hosted AI agent dashboard"  # one-liner
type: monorepo                    # monorepo | library | cli | webapp | agent | service | infrastructure | docs | other
status: active                    # active | scaffolded | suspended | archived
language: Python                  # primary language
size_kb: 45000
stars: 12
last_pushed: 2026-05-10
license: MIT
tags: [agent, dashboard, react, postgresql]
fork_of: openclaw/hermes-agent             # upstream, if forked
```

## Auto-Extractable Fields (from GitHub API + README parsing)

- `repo`, `url`, `description`, `language`, `size_kb`, `stars`, `last_pushed`, `license` → GitHub API
- `tags` → Auto-extracted from description/README via keyword matching
- `type`, `status` → Heuristic detection from description keywords and push recency

## Manual Fields

- `fork_of` — upstream repo name, only for forked repos
- `tags` — can be manually curated after auto-generation

## Filtering Rules

- **Owned repos:** Include all (including forks). Exclude private repos unless explicitly requested.
- **Starred repos:** Include all public. Skip forks whose parent is already in owned (avoids duplication).
- **Forks:** If a fork's upstream is already cataloged as an owned repo, skip the fork entry unless it has significant custom work.
- **Private repos:** Skip by default — they won't appear in starred API results anyway. Include owned private repos only if user explicitly requests.

## Scripts

- `scripts/generate-catalog.py` — Full catalog generator. Run: `python3 generate-catalog.py /path/to/catalog-repo-dir`
- `scripts/query-repo-catalog.py` — Search/filter utility: `query.py tag agent`, `query.py type monorepo`, `query.py --stats`

## Auto-Refresh Cron Setup

To keep the catalog current, set up a cron job that:
1. Pulls latest
2. Runs `scripts/generate-catalog.py <repo-dir>`
3. Commits and pushes if changes

```bash
#!/bin/bash
cd /path/to/seans-reporepo
git pull origin main 2>/dev/null || true
python3 scripts/generate-catalog.py .
git add -A
if ! git diff --cached --quiet; then
    git commit -m "Auto-refresh: $(date '+%Y-%m-%d %H:%M UTC')"
    git push
fi
```

Run weekly (e.g., Monday 9 AM): schedule `0 9 * * 1`.

## Pitfalls

- **`gh repo list --json` uses `diskUsage` NOT `size`** — `size` is not a valid field, returns "Unknown JSON field" error
- **Complex `jq` filters break in nested SSH contexts** — write to temp file and use `jq -f` or pipe script via `bash -s`
- **No PyYAML in container** — the generate-catalog.py script uses a manual frontmatter formatter (no yaml import)
- **Starred API returns parent object differently** — owned repos use `parent.nameWithOwner`, starred use `parent.full_name`
- **Stale file cleanup** — always remove `.md` files for repos that no longer appear in the API results
