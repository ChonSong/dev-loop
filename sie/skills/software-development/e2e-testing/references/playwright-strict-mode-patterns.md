# Playwright Strict-Mode Violation Patterns

Strict-mode violations happen when a locator resolves to multiple elements and
Playwright refuses to guess which one you meant. This is by design — ambiguous
locators hide bugs.

## Common Patterns

### Pattern: Text matches multiple elements

```
Error: strict mode violation: locator('text=Stack') resolved to 2 elements:
  1) <label>Stack Depth</label>
  2) <span>Stack</span>
```

**Fix** — use exact text match or pick a more specific container:

```typescript
// Exact match
page.getByText("Stack", { exact: true })

// More specific parent
page.locator(".board-section").getByText("Stack")

// Nth element (last resort — brittle)
page.locator("text=Stack").last()
```

### Pattern: Anchor href resolves to nav + content links

```
Error: strict mode violation: locator('a[href=\'/study\']') resolved to 2 elements:
  1) <a href="/study">W</a> (logo)
  2) <a href="/study">🎓 Study</a> (nav link)
```

**Fix** — constrain by position or content:

```typescript
page.locator("a[href='/study']").first()     // logo
page.getByRole("link", { name: "Study" })    // nav link by accessible name
```

### Pattern: Board card text matches description text

```
Error: strict mode violation: locator('text=Q♥') resolved to 2 elements:
  1) <span>BTN vs BB · Q♥J♦4♠</span>
  2) <div>Q♥</div> (card)
```

**Fix** — use `.last()` to target the rendered card, or scope to a container:

```typescript
page.locator("text=Q♥").last()
page.locator(".board-cards").getByText("Q♥")
```

## Prevention

1. Use `getByRole()` or `getByTestId()` instead of `text=` when possible
2. Anchor locators in a section container when the page layout has repeated content patterns (grids, cards, sidebars)
3. When you must use `.first()` or `.last()`, add a comment explaining WHY there are multiple matches
4. `data-testid` attributes are the gold standard — push for them in component code
