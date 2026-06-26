---
name: coding-standards
description: Baseline cross-project coding conventions for naming, readability, immutability, and code-quality review. Use domain-specific skills for framework patterns.
origin: ECC (adapted for Hermes)
---

# Coding Standards & Best Practices

Baseline conventions applicable across all projects. This is the shared floor, not the detailed framework playbook.

## When to Activate

- Starting a new project or module
- Reviewing code for quality and maintainability
- Refactoring existing code
- Setting up linting, formatting, or type-checking rules

## Core Principles

### 1. Readability First
- Code is read more than written
- Clear variable and function names — self-documenting > comments
- Consistent formatting

### 2. KISS
- Simplest solution that works
- Avoid over-engineering
- No premature optimization

### 3. DRY
- Extract common logic into functions/utilities
- Create reusable components
- Avoid copy-paste programming

### 4. YAGNI
- Don't build features before they're needed
- Avoid speculative generality
- Start simple, refactor when needed

## Naming Conventions

### TypeScript/JavaScript
```typescript
// GOOD: Descriptive names
const marketSearchQuery = 'election'
const isUserAuthenticated = true
const totalRevenue = 1000
const handleUserClick = () => {}

// BAD: Unclear names
const q = 'election'
const flag = true
const x = 1000
const fn = () => {}
```

### Python
```python
# GOOD
def calculate_monthly_revenue(orders: list[Order]) -> float:
    ...

# BAD
def calc(o):
    ...
```

### Go
```go
// GOOD
func CalculateMonthlyRevenue(orders []Order) float64 { ... }

// BAD
func Calc(o []Order) float64 { ... }
```

## Error Handling

- Handle errors at every level
- User-friendly messages in UI code
- Log detailed context server-side
- Never silently swallow errors
- Fail fast with clear messages

## Code Smells to Flag

| Smell | Fix |
|-------|-----|
| Functions > 50 lines | Extract into smaller functions |
| Files > 800 lines | Split by feature/domain |
| Nesting > 4 levels | Early returns, guard clauses |
| Hardcoded values | Constants, env vars, config |
| Deep inheritance | Composition over inheritance |
| Magic numbers/strings | Named constants |

## Immutability

- Default to immutable data structures
- Create new objects instead of mutating
- Use `const` in JS/TS, `frozen=True` in Python dataclasses
- Return new copies with changes applied

## Scope Boundary

This skill is the baseline. For framework-specific patterns:
- React/Svelte → load `react-agent` or `svelte-development` skill
- Backend/API → load `deployment-patterns` or project-specific skill
- Go → load `go` skill
- Python → load relevant project skill
