---
name: search-first
description: Research-before-coding workflow. Search for existing tools, libraries, and patterns before writing custom code. Use web_search, search_files, and skill_view before implementing.
category: software-development
tags: []
source: local
is_imported: true
---

# Search First — Research Before You Code

Systematizes "search for existing solutions before implementing" — already part of the Soul of the System ("Be resourceful before asking"), this skill makes it a structured workflow.

## When to Activate

- Starting a new feature that likely has existing solutions
- Adding a dependency or integration
- Before creating a new utility, helper, or abstraction
- User asks "add X functionality" and you're about to write code from scratch
- **User mentions something that could be a website, service, or public resource** (e.g., `browse.sh`, `npmjs.com`, a GitHub repo) — check the web before searching the filesystem

## Workflow

0. **Disambiguate: web resource or local file?** — Before searching, check if the thing the user mentioned could be a website, service, or public resource. If it looks like a domain name or known service, search the web FIRST. Don't exhaustively scan the filesystem for something that's clearly a URL.

   **Heuristics for "this is probably a website":**
   - Ends in `.sh`, `.com`, `.io`, `.dev`, `.app` AND the user didn't say "script" or "file"
   - Matches a known service name (browse.sh, npm, pypi, crates.io)
   - User says "search X" or "look up X" (not "find X on this machine")
   - No file exists at the obvious local path after a quick 1-level check

   **Quick check:** `curl -sL https://<name>` or `web_search` before `find / -name`.

1. **Repo scan** — `search_files` in the project for existing implementations
2. **Skills check** — `skills_list` to see if a skill already covers this
3. **Web search** — `web_search` for libraries, packages, or patterns
4. **Evaluate** — Score candidates (functionality, maintenance, community, license, deps)
5. **Decide** — Adopt existing > Extend/wrap > Build custom (informed by research)

## Decision Matrix

| Signal | Action |
|--------|--------|
| Exact match, well-maintained, permissive license | **Adopt** — install and use |
| Partial match, good foundation | **Extend** — install + thin wrapper |
| Multiple weak matches | **Compose** — combine 2-3 small packages |
| Nothing suitable | **Build** — write custom, but informed |

## Hermes-Specific Adaptation

- Use `skills_list` and `skill_view` to check existing skills before building
- Use `search_files` to scan project codebase
- Use `web_search` with operators (`site:npmjs.com`, `site:pypi.org`, `site:github.com`)
- Use `web_extract` to read docs of candidate libraries
- For MCP tools: check `native-mcp` skill for available servers

## Anti-Pattern

**Never write a utility from scratch without checking:** (1) project codebase, (2) existing skills, (3) npm/PyPI, (4) GitHub. The most common waste is building something that already exists.

**Never exhaustively scan the filesystem for something that's clearly a website.** If the user mentions `browse.sh` or similar domain-like names, try `web_search` or `curl https://<name>` first. Filesystem search is the last resort for ambiguous cases.
