---
name: repo-catalog
description: Create a comprehensive repo catalog for ideation, discovery, and combinatorial application design. Indexes owned and starred repos with metadata, tags, query scripts, and auto-refresh.
category: devops
tags: [repository, catalog, github, ideation, metadata, automation]
---

## Overview

Create a searchable, tag-indexed catalog of owned and starred repositories for the purpose of ideation and combinatorial application design. Each repo gets a markdown file with YAML frontmatter containing structured metadata, and a main README with stats tables, language breakdown, tag index, and combinatorial pairing suggestions.

## Trigger Conditions

- User asks to create a catalog/index of their repos
- User wants to analyze repos for ideation/combinatorial design
- User wants to explore relationships between owned and starred repos

## Step-by-Step Workflow

### 1. Discover repos

Fetch owned repos:
```bash
gh repo list <owner> --limit 100 --json nameWithOwner,description,primaryLanguage,stargazerCount,forkCount,diskUsage,pushedAt,isFork,parent,licenseInfo,repositoryTopics
```

Fetch starred repos:
```bash
gh api user/starred --paginate
```

Filter starred repos: skip forks whose parent is already in owned repos.

### 2. Define frontmatter schema

Each repo gets a markdown file with YAML frontmatter:
```yaml
repo: owner/name
url: https://github.com/owner/name
description: "Brief description"
type: monorepo|library|cli|webapp|agent|service|infrastructure|fork|awesome-list|utility|unknown
status: active|scaffolded|suspended|archived|fork
language: Python|TypeScript|Go|Rust|etc
size_kb: 1234
stars: 567
last_pushed: '2026-05-10'
license: MIT|Apache-2.0|etc
tags: [agent, ai, api, dashboard, docker]
fork_of: parent/repo  # optional, only for forks
```

### 3. Auto-extract tags (two-layer: topics + text keywords)

**Layer 1: GitHub topics** — Map `repositoryTopics` (owned) and `topics` (starred) to canonical tags via a broad `TOPIC_TAG_MAP` (80+ entries covering tech, patterns, domains, ecosystem keywords). Use substring matching for fuzzy topic coverage.

**Layer 2: Text keywords** — Fallback scanning of description + README text via `TEXT_KEYWORD_MAP`. Merge both layers with `merge_tags()` for maximum tag accuracy.

```python
TOPIC_TAG_MAP = {
    'ai': 'ai', 'machine-learning': 'ai', 'large-language-model': 'llm',
    'agent': 'agent', 'multi-agent': 'multi-agent', 'mcp': 'mcp',
    'svelte': 'svelte', 'typescript': 'typescript', 'go': 'go', 'rust': 'rust',
    'browser-automation': 'browser-automation', 'scraping': 'browser-automation',
    'vector-db': 'vector-db', 'rag': 'rag', 'fine-tuning': 'fine-tuning',
    'roadmap': 'education', 'design-system': 'design-system',
    # ... 80+ entries covering tech, patterns, domains, ecosystem
}

def merge_tags(text_tags: list, topics: list) -> list:
    tags = set(text_tags)
    for t in topics:
        t_lower = t.lower().replace('_', '-')
        if t_lower in TOPIC_TAG_MAP:
            tags.add(TOPIC_TAG_MAP[t_lower])
        for key, tag in TOPIC_TAG_MAP.items():
            if key in t_lower or t_lower in key:
                tags.add(tag)
    return sorted(tags)
```

### 4. Generate per-repo markdown files

Frontmatter now includes `topics` (raw GitHub topics) and `refreshed_at` (UTC timestamp of generation).

### 4. Generate per-repo markdown files

Directory structure:
```
repo-catalog/
├── owned/           # Per-repo .md files for owned repos
│   ├── owner_repo1.md
│   └── owner_repo2.md
├── starred/         # Per-repo .md files for starred repos
│   ├── org1_repo1.md
│   └── org2_repo2.md
├── scripts/
│   ├── generate-catalog.py  # Main generation script
│   ├── refresh.sh           # Pull, generate, commit, push wrapper
│   └── query.py             # CLI query tool
└── README.md        # Index with stats, tables, tag index
```

### 5. Generate README.md and COMBINATORIAL.md

**README.md** includes:
- Quick stats table (repos count, total size, languages, tags)
- **Refresh timestamp** in header: `Last refreshed: 2026-05-11 02:10 UTC`
- Directory structure diagram
- Owned repos grouped by type with table (repo, language, size, stars, tags)
- Top 20 starred repos by stars
- Tag index with count and sample repos
- Language breakdown with count and total size
- Link to COMBINATORIAL.md (no longer inline — keeps README lean)

**COMBINATORIAL.md** (separate file) includes:
- Full tag overlap analysis between owned and starred repos
- For each bridging tag: owned repos with descriptions, starred repos with star counts
- Starred-only clusters (tags with ≥3 starred repos but no owned overlap — potential exploration areas)
- Sorted by total count descending (highest overlap first)

### 6. Create query script

Python CLI for querying the catalog:
```bash
python3 query.py --stats          # Show stats
python3 query.py tag agent        # Find repos with 'agent' tag
python3 query.py type monorepo    # Find repos of type 'monorepo'
python3 query.py language python  # Find Python repos
python3 query.py search docker    # Full-text search
```

### 7. Generate changelog (compare old vs new)

Before regenerating, parse existing frontmatter to capture old repo names and star counts. After generation, diff:
- **Added repos**: new entries with star counts if >0
- **Removed repos**: entries that no longer exist
- **Star count changes**: delta per repo (top 20 changes shown)

Print changelog at end of run so you see what changed at a glance.

### 8. Set up auto-refresh

Create a refresh script that:
1. Pulls latest changes
2. Fetches current owned/starred repos via `gh` CLI
3. Regenerates all markdown files
4. Commits and pushes if there are changes

Set up cron job for weekly auto-refresh (e.g., Monday 9 AM).

### 8. Create the GitHub repo

```bash
gh repo create <owner>/<repo-name> --public --description "Personal code catalog for ideation and combinatorial app design"
git remote add origin https://github.com/<owner>/<repo-name>.git
git push -u origin main
```

## Key Decisions

- **Scope**: Include all owned repos (including forks), all public starred repos, skip private repos
- **Format**: Markdown index + per-repo .md files with YAML frontmatter (not JSON/YAML only, for GitHub readability)
- **Tags**: Two-layer approach — GitHub topics (via `TOPIC_TAG_MAP` with 80+ entries and substring matching) merged with text keyword scanning. Much higher accuracy than keyword-only.
- **Combinatorial**: Extracted to separate `COMBINATORIAL.md` to keep README readable. README has link + count only.
- **Changelog**: Every run diffs old vs new state (parsed from existing frontmatter). Shows additions, removals, star count deltas.
- **Refresh**: Cron-based auto-refresh weekly, manual trigger available. `refreshed_at` timestamp in header and per-repo frontmatter.
Tiers 3 and 4 NEVER run autonomously — repo-transmute is expensive and produces code changes that need review.

## Using the Catalog for Gap Analysis & Actionable Recommendations

Beyond browsing, the catalog is a tool for structured opportunity discovery. Workflow:

### 1. Theme Clustering

Group starred repos by functional area (observability, eval/testing, agent frameworks, etc.). Capture star count, description, and relevance to owned repos.

### 2. Gap Identification

For each cluster determine: has owned repo? already integrated? true gap where starred tool does something no owned repo covers?

### 3. Opportunity Ranking (Effort/Impact)

| Tier | Criteria | Action |
|------|----------|--------|
| Tier 1 | Zero overhead — CLI, npx, single container | Integrate immediately |
| Tier 2 | Single Docker service, ~150MB RAM | Deploy alongside existing stack |
| Tier 3 | Multi-container, 2-3+ GB RAM | Use cloud free tier or lighter alt |
| Tier 4 | Needs custom build or new owned repo | Schedule into dev backlog |

### 4. Recommendation Format

Structured table with: resource (what), stars, what it does, maps to which owned repo, effort estimate, impact description. Action plan with numbered, independently deliverable steps, each with a clear "done" criterion.

### 5. Feed into Backlog

Winning candidates go into the master-development-loop backlog or get implemented immediately if Tier 1/2. Call out which projects should be added as new backlog entries vs which exist already.

### 6. Parallel Subagent Cluster Mining

For rapid, multi-angle catalog analysis, delegate parallel subagents to mine different tag clusters simultaneously:

```
delegate_task(tasks=[
  {"goal": "Mine monitoring/reliability cluster", "toolsets": ["terminal","file","web"]},
  {"goal": "Mine agent orchestration/context cluster", "toolsets": ["terminal","file","web"]},
  {"goal": "Mine voice/media/research cluster", "toolsets": ["terminal","file","web"]},
])
```

Each subagent:
1. Reads the full README.md for the tag index
2. Reads the relevant starred/ and owned/ .md files
3. Cross-references with existing infrastructure via terminal (check what's deployed, what's running)
4. Proposes ranked opportunities with effort estimates

Then the main session synthesizes the three cluster reports into a unified opportunity map ranked by value/effort, removing cross-cluster duplicates and identifying synergies.

**Best practiced when:** 3+ distinct functional clusters exist in the catalog (monitoring, orchestration, media, etc.) and you need a comprehensive survey without sequential serial analysis.

## Two Catalog Patterns

The user has two repo catalog repos serving different purposes:

### seans-reporepo (detailed catalog)
- Per-repo `.md` files with YAML frontmatter (owned + starred)
- `COMBINATORIAL.md` with full tag overlap analysis
- `scripts/query.py` CLI for filtering/searching
- Auto-refreshes weekly via cron
- **Purpose:** Detailed metadata, searchable index, repo-transmute pipeline input

### seans (summary catalog)
- Single `README.md` with summary table, categories, architecture map
- Cross-repo combination opportunities with detailed ideation entries
- ASCII architecture diagram showing ecosystem layers
- No per-repo files, no scripts, no query tool
- **Purpose:** Quick overview for ideation — "what do I have and how can I combine it?"
- **When to create:** User wants a lightweight catalog for brainstorming without per-repo overhead
- **Creation workflow:** `gh repo create`, fetch owned repos via `gh repo list`, write README with summary table + categories + combination opportunities + architecture map, commit and push

## Pitfalls

- `gh repo list` GraphQL API uses `diskUsage` not `size` for repo size. The `size` field was removed from the API — always use `diskUsage`.
- Starred repos API returns different field names (`stargazers_count` vs `stargazerCount`)
- Fork filtering: skip starred repos whose parent is already in owned repos to avoid duplicates
- README fetching: some repos return 404 (deleted/archived/private). Use `gh(cmd, silent=True)` — add a `silent` parameter to the `gh()` wrapper so README 404s don't spam stderr. The error is non-blocking, catalog continues normally.
- YAML frontmatter: use proper quoting for strings with special characters
- No PyYAML dependency: parse YAML frontmatter manually to avoid external dependencies in scripts
- `refresh.sh` paths: the script lives at `scripts/refresh.sh` but references the host repo path (`/home/sean/.hermes/cache/seans-reporepo`). If running from container, copy the script to host first via `scp`.

## Verification

- `python3 query.py --stats` shows correct counts
- Tag index has no empty tags
- All owned/starred repos have corresponding .md files
- README renders correctly on GitHub
- Cron job is set up and tested

## Related: Catalog → Transmute Pipeline

The catalog feeds repo-transmute as its candidate identification layer. See `references/transmute-pipeline.md` for the pipeline workflow: catalog identifies combinatorial overlaps → candidates/ profiles → repo-transmute migrates components into target stack (Go + Svelte 5 for agent-os ecosystem).

### candidates/ Directory

When the catalog identifies migration targets, generate a `candidates/` directory with per-repo profile files:

```
repo-catalog/
├── candidates/
│   ├── README.md              # Candidate index (table with repo, target tile, tier, effort, relevance)
│   ├── bytebot-ai_bytebot.md  # Per-candidate profile
│   └── trycua_cua.md          # Per-candidate profile
├── owned/
├── starred/
├── scripts/
├── COMBINATORIAL.md
└── README.md
```

Each candidate profile includes:
- Source analysis table (URL, stars, license, language, last pushed, relevance score)
- Relevance rationale (why this repo maps to a target tile)
- What to extract (specific files/components and their target location)
- What to SKIP (scope boundaries)
- repo-transmute plan (exact `v2 migrate` command)
- Tile spec integration (which Svelte components + Go handlers are affected)
- Effort estimate (phased: ingest → migrate → integrate → test)
- Risk register (repo-specific risks with mitigations)

**Relevance scoring:** 1-10 scale based on: (a) tag overlap with owned repos, (b) active maintenance, (c) solves real problem in target stack, (d) license compatibility.

### 4-Tier Cron Strategy

| Tier | Trigger | Action | Auto? |
|---|---|---|---|
| 1: Catalog Refresh | Weekly (Mon 9AM) | Pull stars, regenerate catalog, changelog | Yes |
| 2: Candidate Alert | New star matches combinatorial criteria | Generate candidate profile, notify | Yes |
| 3: Auto-Ingest | User says "ingest <repo>" | Run `repo-transmute v2 ingest` | No (manual gate) |
| 4: Auto-Migrate | User says "migrate <repo> to <tile>" | Full transmute pipeline + vision | No (manual gate) |

Tiers 3 and 4 NEVER run autonomously — repo-transmute is expensive and produces code changes that need review.