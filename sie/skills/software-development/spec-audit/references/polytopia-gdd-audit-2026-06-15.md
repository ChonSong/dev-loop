# Polytopia Clone GDD Audit — 2026-06-15

## Session Context

User asked to "review GDD.md" for the Polytopia Clone project (`/home/sc/repos/polytopia-clone`), then provided a comprehensive real-Polytopia reference document (full game manual) and asked for a thorough audit against the codebase.

## What Was Done

1. Read GDD.md (286 lines) — found internal contradictions between spec claims and gap list
2. Audited every GDD section against actual codebase:
   - `CombatSystem.ts` — damage formula, defense bonuses, retaliation
   - `City.ts` / `CityData.ts` — income, leveling, buildings
   - `Unit.ts` — unit types, stats, costs
   - `TechTree.ts` — tech definitions, costs, unlocks
   - `Tribe.ts` — starting stars, income
   - `TurnManager.ts` — phase structure, win conditions
   - `BasicAI.ts` — build/move/attack priorities
   - `MapGenerator.ts` — terrain generation, resource placement
   - `GameScene.ts` — scoring, city menu, combat execution
   - `SelectScene.ts` — map type / game mode enums
   - `Building.ts` — building definitions
3. Cross-referenced against the full real-Polytopia reference document (9 sections of game manual)
4. Rewrote GDD.md from 286 lines → 506 lines with:
   - Every claim verified against code with file/line citations
   - Implemented/not-implemented markers on each section
   - Full real-Polytopia mechanics as target spec
   - 45+ specific gaps organized by system category

## Key Findings

### Contradictions Found (spec vs code vs gap list)
- GDD §4.1 claimed "REAL — verified" damage formula but gap list said "approximation" — code had the real formula all along
- GDD §5.1 said "base 2 stars" but code uses biome yields + level bonus (no flat base)
- GDD §8 scoring had duplicate "city level" rows (50/level AND 20/level) — code uses only 20/level
- GDD §9.1 said AI gets different base income — code gives all tribes 5⭐/turn
- GDD §6.2 listed 7 tech series (11 techs) — code only has 3 series (9 techs)

### Major Features in Reference Doc But Not in Code
- Naval system (Raft → Scout → Rammer → Bomber with embark/disembark)
- Cloak infiltration / Dagger spawning
- Mind Bender (Convert, Heal Others)
- Veteran system (+5 max HP after 3 kills)
- Siege mechanics (economic blockade)
- Border expansion (3×3 → 5×5)
- Trade routes / City Connections / Grand Bazaar
- Explorer autonomous pathfinding
- Special tribes (Polaris, Cymanti, Elyrion)
- 4 additional tech series (Climbing, Organization, Farming, Smithery, Aquaculture)

## Files Modified
- `/home/sc/repos/polytopia-clone/GDD.md` — complete rewrite

## Commit
- `f8f0573` — "rewrite GDD.md: integrate full real-Polytopia spec with implemented/not-implemented audit"
- Push failed: no GitHub credentials (SSH key not authorized, no HTTPS token)

## User Preferences Observed
- Wants thorough integration of reference docs, not surface-level comparison
- Expects specific file/line citations for every claim verification
- Wants the updated spec document itself, not a separate audit report
- Gaps should be organized by system, not as a flat brainstorm list
- Direct, no-filler communication style
