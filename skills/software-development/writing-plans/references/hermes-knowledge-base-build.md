# Hermes Ecosystem Knowledge Base — Build Pattern

## Context

Building user-facing knowledge bases (guides, docs sites, slideshows) for the Hermes ecosystem requires upfront interrogation BEFORE generation. Failure to do this produces technically-complete but substantively-empty deliverables — slides that exist but miss workflows, fullscreen modes, images, and external links the user explicitly wanted.

## The Relentless Questioning Protocol

Before writing ANY documentation deliverable, establish these 6 dimensions:

### 1. Scope — What's In, What's Out
- Which subsystems are in-scope? (Agent, WebUI, Workspace, Skills, Integrations, External platforms)
- Is this for Hermes stock only, or include peer systems (Claude Code agents, agent-os)?
- Is there a relationship to clarify between systems (e.g., HWC vs agent-os)?

### 2. Audience — Who Reads This
- **New users** (friendly intro, no jargon)
- **Existing users** (advanced features, efficiency)
- **Operators/devs** (config, troubleshooting)
- **All three** (progressive disclosure: intro → advanced → reference)

### 3. Format — Where It Lives
- GitHub Pages? (needs `/docs/` subdirectory, `.nojekyll`, clean URLs)
- Obsidian vault? (native links, graph view)
- Workspace Markdown? (chat context rendering)
- Standalone HTML? (slideshow with D3 graph)
- Custom domain? (Cloudflare Pages vs GitHub Pages CNAME — DNS must point to correct target)

### 4. Images — Source Strategy
- **Real screenshots** (capture from actual UI via SSH + screenshot tool)
- **Generated graphics** (SVG/Mermaid/ASCII art — self-contained, always current)
- **ASCII art** (box-drawing chars, emoji — zero dependencies)
- **External links** (logos, architecture from upstream sources)
- **Decision affects scope significantly** — real screenshots require browser/OS access, timing, and are fragile to UI changes. Generated graphics are stable.

### 5. Features — Explicit List
Ask about each:
- [ ] Example workflows (real use-cases, not just feature descriptions)
- [ ] Fullscreen/ presentation mode (F key to hide UI chrome)
- [ ] Interactive graph (D3 skills network — test on target browser before committing)
- [ ] External links (official docs, GitHub repos, upstream sources)
- [ ] Inline editing (content editable in browser)
- [ ] Mobile/responsive behavior
- [ ] Cheat sheet / quick reference

### 6. Maintenance — Living or Snapshot
- **Snapshot** (versioned, dated, update on releases)
- **Living doc** (cron/heartbeat checks feature parity quarterly)
- **Contributing guide** (PR-based corrections)
- **Auto-generated** (pull from skill manifests, command help)

## D3 Skills Graph — Specific Gotchas

The skills graph (`skills-graph.html`) has specific failure modes:

1. **D3 CDN** — use `https://d3js.org/d3.v7.min.js` (HTTP 200), NOT `unpkg` (302 redirect that can fail in some iframe contexts)
2. **embedSrc path** — must be `./skills-graph.html` (relative), not `/skills-graph.html`, because GitHub Pages serves from a subdirectory
3. **Test in iframe context** — works in standalone tab but may fail when embedded via `<iframe>` in slideshow
4. **GitHub Pages path** — if Pages source is `/docs`, the relative path from `docs/index.html` to `docs/skills-graph.html` is `./skills-graph.html`
5. **CORS** — GitHub Pages sets `access-control-allow-origin: *` so cross-origin iframe embedding should work
6. **404 on `/`** — GitHub Pages with source=`/docs` serves `index.html` from `/docs/` at the root URL, but direct access to `/` may return a different file if no `404.html` exists at root

## Build Sequence

1. **Investigate first** — read actual skill manifests, check file paths in container, read AGENTS.md and MEMORY.md
2. **Confirm scope** — answer the 6 questions above with user input
3. **Design structure** — propose outline, get approval
4. **Build incrementally** — slideshow → MD files → graph → images
5. **Test on target** — verify all paths, graph, and interactive elements work on actual GitHub Pages before declaring done

## Anti-Patterns

- ❌ Generating MD files from template without reading actual codebase
- ❌ Assuming "highly detailed without technical weeds" without defining what that means operationally
- ❌ Building fullscreen mode as an afterthought — it must be in the original feature list
- ❌ Testing graph only in localhost — must test in iframe context on target deployment
- ❌ Missing example workflows — a guide without real use-cases is just a feature list

## Real Source Paths (Current Setup)

```
Container: /workspace/hermes-guide/  →  GitHub: ChonSong/hermes-guide (master:/docs)
Host:      /tmp/hermes-guide/         →  GitHub Pages: https://chonsong.github.io/hermes-guide/
SSH:       sean@172.19.0.1           →  GitHub auth via: gh auth token (on host)
```
