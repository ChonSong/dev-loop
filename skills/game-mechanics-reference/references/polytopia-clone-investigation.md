# Polytopia Clone Investigation – 2026-06-17

## Context
Investigation of the Polytopia clone at `/home/sc/repos/polytopia-clone` revealed a discrepancy between passing tests and missing core gameplay mechanics.

## Findings

### Core Loop Status
- **Unit Spawn**: ❌ Missing – no code creates initial units when a city is founded.
- **First-Turn Immobility**: ❌ Missing – no flag prevents units from acting on turn of creation.
- **City-Border Enforcement**: ❌ Missing – no proximity check blocks unit placement within 1-tile radius of a city.
- **Building Placement**: ✅ Implemented – `City.canBuild()` and `Building.ts` handle resource-based placement.

### Evidence
- `grep -r "spawn" src/` → 0 matches
- `grep -r "border" src/` → 0 matches
- `grep -r "firstTurn"` → 0 matches
- Test suite: 228/228 passing (tests do not cover missing mechanics)

### GDD Reference
- `GDD.md:88` explicitly states: "❌ No city/village proximity constraint — resources spawn globally"
- `GDD.md:91` states: "❌ No unit spawn on turn 1"

## Action Plan
1. Add `spawnInitialUnits(city)` in `Tribe.ts` or `TurnManager.ts`
2. Implement `isFirstTurn` flag on `Unit`, reset at end of tribe's first turn
3. Add `isWithinCityBorder(coord, cities)` utility and call in `TurnManager.validateMove()`
4. Add tests for each mechanic