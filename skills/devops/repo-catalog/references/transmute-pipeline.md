# repo-catalog → repo-transmute Pipeline

## Concept

The catalog is not just a phonebook — it's the **input to repo-transmute**. Combinatorial overlaps between owned and starred repos identify concrete migration candidates.

## Pipeline Flow

```
seans-reporepo (catalog)  →  candidates/ (profiles)  →  repo-transmute (migration engine)  →  Target stack (Go+Svelte5)
       ↓                         ↓                            ↓
  COMBINATORIAL.md          Per-repo analysis             v2 migrate <src> <dst>
  identifies candidates     + repo-transmute commands     produces migrated code
```

## How to Use

1. Run `generate-catalog.py` → produces COMBINATORIAL.md with tag-bridged repos
2. Review COMBINATORIAL.md → identify high-value candidates
3. Generate `candidates/<repo>.md` profiles with extraction scope, transpile plan, effort estimates
4. For each candidate: use repo-transmute `v2 migrate` to migrate components into target stack
5. Verify with vision scoring (screenshot source vs migrated output)

## Candidate Prioritization Criteria

A starred repo is worth migrating into your stack if:
- **Overlap**: Shares ≥2 tags with an owned repo (visible in COMBINATORIAL.md)
- **Active**: Pushed within last 12 months, not archived
- **Solves a real problem**: Maps to a hermes-web-computer tile or agent-os feature gap
- **Right license**: MIT, Apache-2.0, BSD (not AGPL/proprietary)
- **Relevance score ≥6/10**: Based on overlap, activity, problem-fit, and license

## Known Mappings (as of 2026-05-11)

| Target Tile | Source Repo | Tier | Effort |
|---|---|---|---|
| Browser Tile | bytebot-ai/bytebot (11K⭐, Apache-2.0) | T1 | 3-5 days |
| Sandbox Tile | trycua/cua (15K⭐, MIT) | T1 | 3-4 days |
| Dashboard Tile | ChonSong/agent-os (owned, React→Svelte) | T1 | 2-3 days |
| AI Components | sveltejs/ai-tools | T2 | 1-2 days |
| Research Data | upstash/context7 | T2 | 1 day |
| Resource Index | sindresorhus/awesome | T2 | 0.5 days |

## Tile Architecture (hermes-web-computer)

Each tile is a Svelte 5 component backed by a Go handler, communicating through the JSON-RPC multiplexer over WebSocket.

### Core Tiles (v1.0)
- **Terminal** — built-in, already working (xterm.js + PTY)
- **Browser** — screenshot stream + URL bar + AI action button (from bytebot)
- **Voice Chat** — waveform display + transcript (from Fun-Audio-Chat)
- **Dashboard** — agent status, sessions, system metrics (from agent-os)

### Enhancement Tiles (v1.1)
- Code Editor (Monaco.svelte stub → full implementation)
- Research (context7 API integration)
- Sandbox (cua screen capture + input routing)
- Media (yt-dlp integration)

## repo-transmute Commands

```bash
# Ingest: clone + detect framework + extract AST blueprint
cd /opt/data/repo-transmute-v2
python3 -m src.cli v2 ingest https://github.com/bytebot-ai/bytebot --output data/bytebot

# Review blueprint
cat data/bytebot/blueprint.json | jq '.components[] | select(.name | contains("browser"))'

# Migrate: LLM-driven transpilation with vision verification
python3 -m src.cli v2 migrate data/bytebot /opt/data/hermes-web-computer \
  --extract "browser-capture,dom-analysis,input-routing" \
  --target svelte5+go \
  --style tailwind

# Verify: screenshot source vs migrated output
python3 -m src.cli v2 verify data/bytebot /opt/data/hermes-web-computer
```

## Refresh Strategy

- **Tier 1: Weekly cron** (Mon 9AM) — Star counts, new stars, changelog, COMBINATORIAL.md
- **Tier 2: On new star** — If new star matches combinatorial criteria, generate candidate profile
- **Tier 3: Gated ingest** — User says "ingest <repo>" → run repo-transmute v2 ingest
- **Tier 4: Gated migrate** — User says "migrate <repo> to <tile>" → full transmute pipeline

Tiers 3 and 4 are NEVER autonomous. repo-transmute is expensive (LLM calls, vision scoring) and produces code changes that need review.

## Risk Mitigations

| Risk | Mitigation |
|---|---|
| Source repo API changes during migration | Pin to specific commit, extract core only |
| Vision scoring fails on complex pages | Lower threshold, manual verification fallback |
| Svelte 5 rune migration breaks components | Incremental migration, test each component |
| User stars dead/archived repo | Catalog filters archived repos automatically |
| Wrong license (AGPL) | Filter candidates by license before migration |
