# Zero Console Error Finale — June 2026

All 14 pages pass Puppeteer QA with zero console errors. Here are all fixes.

## Strategy Page: `e.map is not a function`

**Root cause:** API returns `{positions: [{value, label}]}` but frontend expected `["BTN", "SB", ...]`.

**Fix (4 occurrences):**
```typescript
// Before:
setPositions(await posRes.json());

// After:
const d = await posRes.json();
setPositions(Array.isArray(d) ? d : d?.positions || []);
```
Also: state type `string[]` → `SelectOption[]` (`{value: string; label: string}[]`).
Render uses `p.value` / `p.label` not raw `p`.

## Courses Page: `e.map is not a function`

**Root cause:** `setCategories(await r.json())` — API returns `{categories: [...]}`.

**Fix (3 occurrences — categories, courses, featured):**
```typescript
const d = await r.json();
setCategories(Array.isArray(d) ? d : d?.categories || []);
```

## Spots Page: `e.map is not a function`

**Root cause:** `setSpots(await r.json())` — API returns `{spots: [...]}`.

**Fix (2 occurrences — spots, comments):**
```typescript
const d = await r.json();
setSpots(Array.isArray(d) ? d : d?.spots || d?.data || []);
```

## Quiz Leaderboard: 500 Internal Server Error

**Root cause:** `func.cast(expr, func.Float)` — `func.Float` is a `Function`, not a `TypeEngine`.

**Fix:**
```python
from sqlalchemy import cast, Float
accuracy_expr = cast(subquery.c.correct_count, Float) / cast(subquery.c.total_solves, Float) * 100
```

## Quiz Stats: 500 Internal Server Error

**Root cause:** `default=uuid.uuid4` returns a `uuid.UUID` object. SQLite column is `String(36)`, cannot bind UUID objects.

**Fix (4 model classes: QuizSpot, QuizSubmission, UserStats, ReviewSpot):**
```python
# Before:
id: Mapped[uuid.UUID] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)

# After:
id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
```

## Strategy React Error #31 (Objects not valid as children)

**Root cause:** Filter values are objects `{value, label}` but `<option key={p}>` tries to render the object.

**Fix:** Access `.value` / `.label` properties:
```typescript
{positions.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
```

## Universal Pattern: API Response Unwrapping

Every list endpoint in this API returns an object wrapper `{items: [...]}` or `{categories: [...], courses: [...]}`, NOT a raw array. The frontend must always unwrap:

```typescript
const data = await r.json();
if (Array.isArray(data)) setItems(data);
else if (data?.items) setItems(data.items);
else if (data?.data) setItems(data.data);
else setItems([]);
```

## Strategy Lookup Filter Types

The `strategy-lookup/*` endpoints return arrays of objects `{value, label}`, not strings:
- `/api/v1/strategy-lookup/positions` → `{positions: [{value:"BTN", label:"Button"}, ...]}`
- `/api/v1/strategy-lookup/stack-depths` → `{stack_depths: [{value:100, label:"100bb"}, ...]}`
- `/api/v1/strategy-lookup/streets` → `{streets: [{value:"flop", label:"Flop"}, ...]}`
- `/api/v1/strategy-lookup/bet-sizes` → `{bet_sizes: [{value:0.5, label:"50% pot"}, ...]}`

State type must be `{value: string; label: string}[]` not `string[]`.
