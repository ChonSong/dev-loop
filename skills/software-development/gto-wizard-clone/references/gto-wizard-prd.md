# GTO Wizard Clone — Product Requirements Document

**Location:** `/workspace/gto-wizard-prd.md` (840 lines, 40KB)

## Purpose

The single source of truth for all GTO Wizard Clone development. Documents every page, every gap, every acceptance criterion, and every bug. Consult this before writing any code and update it when you discover undocumented gaps.

## Key Sections

### Product Vision & Target Users (Section 1-2)
4 user personas with specific needs: Recreational Player, Serious Grinder, Coach/Content Creator, Tournament Player.

### Architecture (Section 3)
Tech stack, route structure, layout system diagram with exact dimensions (nav 48px, sidebar 280px, icon bar 30px).

### Design Tokens (Section 4)
Complete color palette (20 hex values), typography scale (8 sizes), spacing (7 values), borders/shadows.

### Feature Inventory per Page (Section 5)
Each of the 14 pages documented with:
- Current implementation (what works, component-level)
- Gaps vs real GTO Wizard (prioritized P0/P1/P2)
- Specific changes needed (file paths, line numbers, exact code)
- Acceptance criteria (checklist format)

### Cross-Cutting Gaps (Section 6)
Design system inconsistencies, auth integration, matrix sizing.

### Bug Inventory (Section 7)
All known bugs with severity, file path, and line number.

### API Endpoint Inventory (Section 8)
40+ endpoints mapped to their consuming frontend pages.

### Implementation Roadmap (Section 9)
3 phases across 3 weeks with dependency graph.

### Feature Prioritization Matrix (Section 10)
19 items with effort estimates, dependencies, and sequencing notes.
