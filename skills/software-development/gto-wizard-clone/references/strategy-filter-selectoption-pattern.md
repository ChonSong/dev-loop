# Strategy Filter SelectOption Type Fix

The strategy page's filter options (positions, stack depths, streets, bet sizes) are loaded from API endpoints that return objects like:

```json
{"positions": [{"value": "BTN", "label": "Button"}, {"value": "SB", "label": "Small Blind"}]}
```

## Bug

The original code used `string[]` state and rendered `<option key={p}>{p}</option>`. When the API response was loaded as-is (an object array), `{p}` in JSX produced `[object Object]` → React error #31.

## Fix: Triple Pattern

### 1. State Type

```typescript
type SelectOption = { value: string; label: string };
const [positions, setPositions] = useState<SelectOption[]>([]);
const [stackDepths, setStackDepths] = useState<SelectOption[]>([]);
const [streets, setStreets] = useState<SelectOption[]>([]);
const [betSizes, setBetSizes] = useState<SelectOption[]>([]);
```

### 2. Loader Unwrapping

```typescript
if (posRes.ok) {
  const d = await posRes.json();
  setPositions(Array.isArray(d) ? d : d?.positions || []);
}
// Same pattern for stack_depths, streets, bet_sizes
```

### 3. Render Using .value / .label

```typescript
{options.map(o => (
  <option key={o.value} value={o.value}>{o.label}</option>
))}
```

## Quick Check

After fixing, verify no `typeof x === 'string' ? x : x.value` patterns remain — those were the temporary workaround before the type was corrected. They dead-end into TypeScript `never` when the state type is `SelectOption[]`.