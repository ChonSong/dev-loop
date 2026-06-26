---
name: third-party-skill-install
description: |
  Install skills from third-party catalogs (browse.sh, skills.sh, etc.) when `npx skills add` fails due to GitHub auth. Covers the manual download pattern: inspect SKILL.md for safety, mkdir, curl from raw.githubusercontent.com, verify.
  Triggers: "install skill from browse.sh", "add browser automation skill", "install third-party skill", "skills add fails".
---

# Third-Party Skill Installation

When `npx skills add <slug>` fails with "Authentication failed" or hangs on cloning, fall back to manual download.

## Safety First

Before installing any third-party skill:

1. **Verify source** — check it's from a reputable org (e.g., `github.com/browserbase/skills`)
2. **Read SKILL.md** — scan for suspicious content, external URLs, encoded payloads
3. **Check metadata** — look for `license`, `allowed-tools`, `compatibility` fields
4. **Prefer verified skills** — `verified: true` in browse.sh catalog

## Manual Install Pattern

```bash
# 1. Inspect SKILL.md for safety
curl -sL "https://raw.githubusercontent.com/<org>/<repo>/main/skills/<path>/SKILL.md"

# 2. Create directory
mkdir -p ~/.hermes/skills/<skill-name>
mkdir -p ~/.hermes/skills/<skill-name>/scripts
mkdir -p ~/.hermes/skills/<skill-name>/references

# 3. Download SKILL.md
curl -sL "<raw-url>/SKILL.md" -o ~/.hermes/skills/<skill-name>/SKILL.md

# 4. Download supporting files (check SKILL.md for referenced scripts/references)
curl -sL "<raw-url>/scripts/<file>.mjs" -o ~/.hermes/skills/<skill-name>/scripts/<file>.mjs
curl -sL "<raw-url>/references/<file>.md" -o ~/.hermes/skills/<skill-name>/references/<file>.md

# 5. Verify
find ~/.hermes/skills/<skill-name>/ -type f | sort
```

## browse.sh Specifics

- Catalog URL: https://browse.sh
- Search: `npx browse skills find "<query>"`
- Slug format: `<hostname>/<task>-<id>`
- `browse skills add <slug>` tries to clone `github.com/browserbase/browse.sh.git` — fails without GitHub auth
- Manual download from: `https://raw.githubusercontent.com/browserbase/skills/main/skills/<path>/`
- Some skills are in `browserbase/skills` repo, others in `browserbase/browse.sh` repo — check `sourceUrl` in catalog output
- Daily notes: workspace/memory/2026-06-08.md

## Memory Management

- Memory is limited (~2200 chars). Prune proactively when >80% full.
- Remove oldest/least-relevant entry before adding new ones.
- Don't wait for repeated failures — check usage and trim first.

## Batch Install

Skills that need scripts/references (check directory listing on GitHub first):
- `company-research`: scripts/extract_page.mjs, scripts/compile_report.mjs, scripts/list_urls.mjs, references/example-research.md
- `event-prospecting`: scripts/extract_page.mjs, scripts/compile_report.mjs, references/example-research.md, references/workflow.md
- `browser-trace`: scripts/start-capture.mjs, scripts/stop-capture.mjs, scripts/bisect-cdp.mjs
- `cookie-sync`: scripts/cookie-sync.mjs
- `autobrowse`: references/example-task.md
- `browser-to-api`: scripts/discover.mjs
