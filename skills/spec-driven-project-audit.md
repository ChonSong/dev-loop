# Spec-Driven Project Audit (Playwright-First)

A runtime-first audit protocol that verifies project claims by driving a real browser — not by counting tests or reading source.

See `~/.hermes/skills/quality/spec-driven-project-audit/SKILL.md` for the full skill definition.

## Why This Exists

The Polytopia clone failure: told "core gameplay loop" was functional because `Unit.ts` and `City.ts` existed and 228 tests passed — but **3 of 4 stages had zero runtime code**. Source reading + test count = lies. The only honest check is "I launched the app, clicked around, and watched what happened."

## Mandatory Protocol

| Step | Action |
|------|--------|
| 0 | Build and serve the app (`npm run build`, `serve dist`) |
| 1 | Read the authoritative spec (GDD.md → AGENTS.md → README) |
| 2 | For each claimed feature, write and run a Playwright script |
| 3 | Report pass/fail per spec item |
| 4 | Only read source to **diagnose** failures — never to claim success |

## Key Principles

- **Code-read fallacy**: seeing a class/function in source ≠ runtime behaviour
- **Test-count fallacy**: green suite ≠ features work
- **Spec-neglect fallacy**: open the spec before any source file
- **Server-forget fallacy**: rebuild before running checks

## When to Use

- Reporting on project status or verifying claims
- Before claiming a feature is implemented
- Deployment verification
