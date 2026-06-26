# Repo Catalog Frontmatter Schema

Used when building a catalog/index of owned and starred repos for ideation and recombination.

## Directory Structure

```
repo-catalog/
├── README.md              # Human-readable index
├── owned/
│   ├── agent-os.md
│   ├── repo-transmute.md
│   └── ...
└── starred/
    ├── repomix.md
    ├── opencode.md
    └── ...
```

## YAML Frontmatter Fields

```yaml
repo: ChonSong/agent-os           # owner/name (required)
url: https://github.com/ChonSong/agent-os  # full URL
description: "Self-hosted AI agent dashboard"  # one-liner
type: monorepo                    # monorepo | library | cli | webapp | agent | service | infrastructure | docs | other
status: active                    # active | scaffolded | suspended | archived
language: Python                  # primary language
languages: [Python, TypeScript, Shell]  # all languages (monorepos)
size_kb: 45000
stars: 12
forks: 3
last_pushed: 2026-05-10
created_at: 2025-11-15
license: MIT
visibility: public                # public | private
topics: [agent, dashboard, react, postgresql]
architecture: Express backend + React SPA + Hermes Agent + PostgreSQL
key_dependencies: [Hermes Agent, PostgreSQL, Cloudflare Tunnel, React]
provides: [REST API, Web UI, Agent CLI]  # what it exposes/consumes
fork_of: openclaw/hermes-agent             # upstream, if forked
combinable_with: [claw-aie, casaos-webhook-emitter]  # repos that pair well
notes: ""  # manual curation, free-text
```

## Auto-Extractable Fields (from GitHub API + README parsing)

- `repo`, `url`, `description`, `language`, `languages`, `size_kb`, `stars`, `forks`, `last_pushed`, `created_at`, `license`, `topics` → GitHub API
- `type`, `architecture`, `key_dependencies`, `provides` → Parse README (look for architecture diagrams, dependency lists, feature sections)
- `status` → Check README "Status:" badge, `pushed_at` recency, or explicit markers like "Development suspended"

## Manual Fields

- `combinable_with` — curated suggestions based on tech stack overlap and purpose alignment
- `notes` — anything that doesn't fit the structured fields

## Filtering Rules

- **Owned repos:** Include all (including forks). Exclude private repos unless explicitly requested.
- **Starred repos:** Include all public. Skip forks that are pure mirrors (no custom commits).
- **Forks:** If a fork's upstream is already cataloged as an owned repo, skip the fork entry unless it has significant custom work.
