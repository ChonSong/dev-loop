# Skill Library — Full Inventory

> Discovered 2026-05-26. Canonical source: `skills_list` API + filesystem scan.

## Skills Registry

**167 skills** across 20 categories, registered in Hermes Agent skill index.

Skills live at: `~/.hermes/skills/` (canonical), `~/.hermes/home/.hermes/skills/` (nested duplicate — ignore).

## The skill-selector System

Installed 2026-05-24 (session `f49547b1e6e8`) but **not yet active**:

| Component | Status |
|---|---|
| `skill-selector` skill | ✅ Registered |
| `skill-selector-prep` skill | ✅ Registered |
| Scripts at `~/.hermes/scripts/skill-selector*.py` | ✅ Present |
| Weekly cron `65520f7d71f9` | ❌ Never fired |
| Cache at `~/.hermes/skill-selector-cache/` | ❌ Empty/stale |
| System prompt injection | ❌ Not applied in this session |
| Task classifier | ❌ Not built |
| Workflow-stage scoring | ❌ Designed but not implemented |

**Action needed**: Run `python3 /home/hermeswebui/.hermes/scripts/skill-selector-prep.py` once to populate the cache, then the weekly cron keeps it fresh.

## 5 Source Repos (for 1000+ skills target)

| Repo | Skills | Format |
|---|---|---|
| `VoltAgent/awesome-agent-skills` | ~1,117 | README bullet list |
| `0xNyk/awesome-hermes-agent` | ~120 | README mixed |
| `mattpocock/skills` | 28 | Per-SKILL.md subdirs |
| `vercel-labs/skills` | ~4 | README |
| `expo/skills` | ~4 | README |
| Local (`~/.hermes/skills/`) | 167 | SKILL.md files |

**Total catalog: 1,320+** (deduped, verified 2026-05-25)

## Optional Skills (not registered)

Bundled at `~/.hermes/hermes-agent/optional-skills/`:
`blackbox`, `openhands`, `honcho`, `evm`, `hyperliquid`, `solana`, `one-three-one-rule`, etc.

NOT installed into `~/.hermes/skills/` — copy to register.

## Key Paths (container)

```
~/.hermes/skills/                    # 167 registered skills
~/.hermes/scripts/skill-selector.py  # every-turn scorer
~/.hermes/scripts/skill-selector-prep.py  # weekly cache builder
~/.hermes/skill-selector-cache/      # cache (empty until prep runs)
```

## What Was Discussed This Session

- User asked about 1000+ skills (references Matt Pocock, awesome lists)
- skill-selector-prep cron `65520f7d71f9` has **never fired** — added fix section to skill
- 167 skills is the current count; 1000+ is achievable by running the prep script
- Having many skills does NOT harm performance (lazy loading, caching architecture)
- At 1000+ scale, `skill-selector-prep` weekly cron becomes critical
- System prompt injection was done in the May 24 session but may not be active in all contexts