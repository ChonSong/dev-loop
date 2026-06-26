# CI First-Try Green & TypeScript Patterns

## TypeScript: Hardcoded Array Literals vs Interface Gaps

**Pattern:** Adding a new optional field to an interface that has hardcoded initializers.
The TypeScript compiler error only surfaces when initializers DON'T include the new field.

**Real example:** `SkillRecord` interface was extended with `is_custom?: boolean`. Four hardcoded
`skills: [{ name: ..., description: ..., category: ..., enabled: true }, ...]` initializers existed
in the store seed data. Error: `TS2741: Property 'is_custom' is required in 'SkillRecord'
but not present in type '{ name: string; ... }'`.

**Fix:** Search for hardcoded array literals matching the interface:
```bash
grep -n "skills:\s*\[" backend/src/index.ts
# Add is_custom: false to each literal
```

**Lesson:** Always search for hardcoded initializers when adding fields to shared interfaces.
Local `tsc --noEmit` catches this — run it before committing.

## CI First-Try Green — Conditions and Failure Modes

After 8+ consecutive CI fix commits, achieved first-try green on `570c9e0`. Key conditions:
1. `tsc --noEmit` passes on every modified file (run individually per package)
2. GitHub Actions cache restores `node_modules` via `npm ci`
3. No interface/hardcoded-literal mismatches

**Failure modes that break first-try:**
- Missing `is_custom` on hardcoded literals (only caught in full project tsc)
- Optional chain (`?.`) on non-optional property → TS2741
- Frontend change not included in backend `tsc` pass (type errors only surface where types are used)

**Post-commit workflow:**
1. `git commit && git push`
2. `sleep 300 && curl GitHub API for run status` (non-blocking poll)
3. If failure → inspect, fix, commit, push
4. If success → deploy via SSH

## Theme Optional Chain Guard

**Pattern:** `ThemeSwatch` component accesses `preset.palette.background.hex` but `palette` is optional.

**Error:** `TS2741: 'palette' is optional — required in 'ThemeSwatch' but not in 'preset' type.`
Also manifested as `Cannot read properties of undefined (reading 'background')`.

**Fix — always use `??` fallback when destructuring optional:**
```tsx
// WRONG:
const { background, midground, warmGlow } = preset.palette;

// RIGHT:
const palette = preset.palette ?? {
  background: { hex: '#08090a' },
  midground: { hex: '#111115' },
  warmGlow: '#7170ff'
};
const { background, midground, warmGlow } = palette;
```

## ObservabilityPage Container History Pattern

Container stats use a time-series approach:
```tsx
type ContainerSnapshot = DockerContainerStats & { ts: number };
const [containerHistory, setContainerHistory] = useState<Record<string, ContainerSnapshot[]>>({});

// Polling every 15s appends to history, trims to last 20 entries:
setContainerHistory(prev => {
  const next = { ...prev };
  for (const c of stats) {
    const arr = [...(next[c.id] ?? []), { ...c, ts: Date.now() }];
    next[c.id] = arr.slice(-20);
  }
  return next;
});
```

**Sparkline from last 10 CPU readings:**
```tsx
const cpuHistory = containerHistory[container.id]?.slice(-10) ?? [];
const sparkMax = Math.max(...cpuHistory.map(s => parseFloat(s.cpu_percent)), 1);
const sparkline = cpuHistory.map(s => {
  const h = Math.round((parseFloat(s.cpu_percent) / sparkMax) * 7);
  return '▁▂▃▄▅▆▇'[h];
}).join('');
```

## ChatPanel Token Counter Pattern

Nanobot streams SSE with token metadata in each chunk:
```typescript
// Session-level cumulative:
const [sessionTokens, setSessionTokens] = useState({ input: 0, output: 0 });

// Parse from SSE chunks:
const usage = chunk.usage ?? chunk.tokens;
if (usage?.prompt_tokens) setSessionTokens(p => ({
  input: p.input + usage.prompt_tokens,
  output: p.output + (usage.completion_tokens ?? 0)
}));

// Per-message:
interface Message {
  content: string;
  tokens_used?: number;
}
```

**Display:**
```tsx
// Session total (header):
{sessionTokens.input + sessionTokens.output > 0 && (
  <span className="text-[10px] text-[#8a8f98] shrink-0">
    {sessionTokens.input + sessionTokens.output} tokens
  </span>
)}

// Per-message (below bubble content):
{msg.tokens_used != null && (
  <span className="text-[10px] text-[#8a8f98] ml-2 shrink-0">{msg.tokens_used} tokens</span>
)}
```
