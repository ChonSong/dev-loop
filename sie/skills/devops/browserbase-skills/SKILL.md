---
name: browserbase-skills
description: Install, update, and use Browserbase browse.sh browser automation skills. Covers the browse CLI, skill catalog discovery, manual installation (when browse skills add fails), env var management, and composing multiple skills for prospecting, API discovery, UI testing, and authenticated browsing workflows.
---

# Browserbase browse.sh Skills

Browserbase provides an open catalog of browser automation skills at [browse.sh](https://browse.sh). Each skill is a SKILL.md + supporting scripts that teaches an AI agent to complete specific tasks on particular websites using the `browse` CLI.

## Skill Categories

| Category | Key Skills | Use Case |
|----------|-----------|----------|
| **Research** | company-research, event-prospecting | Lead gen, ICP scoring, conference prospecting |
| **Automation** | autobrowser, fetch, search | Self-improving browsing, lightweight fetching |
| **Debugging** | browser-trace, browser-to-api | CDP traces, OpenAPI spec generation from traffic |
| **Infrastructure** | cookie-sync, ui-test | Auth sync, adversarial UI testing |

## Prerequisites

```bash
# CLI already installed on this system (v0.8.3) via npm global
which browse || npm install -g browse

# API key required — stored in /workspace/.env
export BROWSERBASE_API_KEY=$(grep BROWSERBASE_API_KEY /workspace/.env | head -1 | cut -d= -f2)
```

**IMPORTANT:** The key is in `/workspace/.env`, NOT in the container's default env. Always load it explicitly or add to `~/.bashrc`.

## Discovery

```bash
# Search the catalog
npx browse skills find "company-research"

# List all available skills
npx browse skills list

# Get full details on a skill
npx browse skills find "slug-name" | python3 -m json.tool
```

## Installation

### Preferred: `browse skills add` (requires GitHub auth)

```bash
npx browser skills add browserbase.com/company-research
```

**This often fails** with "Authentication failed" because it tries to clone the GitHub repo and the container lacks credentials.

### Fallback: Manual download (works without auth)

```bash
# 1. Create skill directory
mkdir -p ~/.hermes/skills/browserbase-{name}/{scripts,references}

# 2. Download SKILL.md
curl -sL "https://raw.githubusercontent.com/browserbase/skills/main/skills/{name}/SKILL.md" \
  -o ~/.hermes/skills/browserbase-{name}/SKILL.md

# 3. Download supporting files (check sourceUrl in catalog for what exists)
curl -sL "https://raw.githubusercontent.com/browserbase/skills/main/skills/{name}/scripts/*.mjs" \
  -o ~/.hermes/skills/browserbase-{name}/scripts/
```

Skills from `browserbase/skills` repo use path: `skills/{name}/SKILL.md`
Skills from `browserbase/browse.sh` repo use path: `skills/{hostname}/{task-slug}/SKILL.md`

## Verification

```bash
# Check API works
curl -s -X POST "https://api.browserbase.com/v1/search" \
  -H "Content-Type: application/json" \
  -H "X-BB-API-Key: $BROWSERBASE_API_KEY" \
  -d '{"query":"test","numResults":1}'

# Verify skill installed
ls ~/.hermes/skills/browserbase-*/
```

## Installed Skills (as of 2026-06-08)

All at `~/.hermes/skills/browserbase-*/`:

1. **company-research** — (5 files) Prospect discovery + ICP scoring, outputs CSV
2. **browser-to-api** — (2 files) Reverse-engineer APIs from browser traces → OpenAPI spec
3. **autobrowse** — (2 files) Self-improving browser automation via iterative loop
4. **event-prospecting** — (5 files) Conference lead scraping, person-first HTML reports
5. **fetch** — (1 file) Lightweight URL fetching without full browser
6. **cookie-sync** — (2 files) Chrome → Browserbase cookie sync for auth
7. **search** — (1 file) Web search without browser session
8. **ui-test** — (1 file) AI-powered adversarial UI testing (diff-driven or exploratory)
9. **browser-trace** — (4 files) CDP firehose capture + bisect for debugging

All MIT-licensed, verified, no proxies required.

## Skill Composition Patterns

**Full research pipeline:**
```
company-research → (discovers targets)
event-prospecting → (finds people at conferences)
browser-trace → (debugs failures)
```

**API discovery pipeline:**
```
browser-trace capture → browser-to-api → OpenAPI spec
```

**QA pipeline:**
```
autobrowse (build skill) → ui-test (verify) → browser-trace (debug failures)
```

## Pitfalls

- `browse skills add` fails without GitHub SSH/token — use manual curl download
- Skills require `BROWSERBASE_API_KEY` in env, not just `.env` file
- The `browse` CLI must be invoked via `npx browse` (v0.8.3, not globally in PATH)
- Fetch API can time out — use generous timeouts or fall back to search first
- `source .env` doesn't work with duplicate keys; use `grep KEY .env | head -1 | cut -d= -f2`
