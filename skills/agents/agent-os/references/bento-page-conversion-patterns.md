# Bento Page Conversion: Patterns & Pitfalls

## When to Use

When converting a React page from shadcn `<Card>` components to Bento `bento-card` divs.

## Standard Card → Bento Transformations

### Pattern A: Card with Header + Content
```tsx
// BEFORE
<Card>
  <CardHeader>
    <div className="flex items-center gap-2">
      <Icon className="h-5 w-5 text-muted-foreground" />
      <CardTitle className="text-base">{title}</CardTitle>
    </div>
  </CardHeader>
  <CardContent>
    {content}
  </CardContent>
</Card>

// AFTER
<div className="bento-card bg-[#FFFBF5] border border-[#F0E6D8] rounded-2xl p-5 shadow-bento-sm hover:shadow-bento-md transition-shadow">
  <div className="flex items-center gap-2 pb-3">
    <Icon className="h-5 w-5 text-muted-foreground" />
    <span className="text-base font-semibold">{title}</span>
  </div>
  <div>
    {content}
  </div>
</div>
```

### Pattern B: Card with Subheader
```tsx
// BEFORE
<CardHeader>
  <div className="flex items-center gap-2">
    <Icon className="h-5 w-5" />
    <CardTitle>{title}</CardTitle>
  </div>
  <div className="flex items-center gap-4 text-xs text-muted-foreground">
    {/* legend items */}
  </div>
</CardHeader>
<CardContent>

// AFTER
<div className="bento-card ...">
  <div className="flex flex-col gap-3 pb-3">
    <div className="flex items-center gap-2">
      <Icon className="h-5 w-5" />
      <span className="text-base font-semibold">{title}</span>
    </div>
    <div className="flex items-center gap-4 text-xs text-muted-foreground">
      {/* legend items */}
    </div>
  </div>
  <div>
```

### Pattern C: Error Card
```tsx
// BEFORE
<Card>
  <CardContent className="py-6">
    <p className="text-sm text-destructive text-center">{error}</p>
  </CardContent>
</Card>

// AFTER
<div className="bento-card bg-[#FFFBF5] border border-[#F0E6D8] rounded-2xl p-5 shadow-bento-sm">
  <p className="text-sm text-[#DC2626] text-center">{error}</p>
</div>
```

### Pattern D: Empty State Card
```tsx
// BEFORE
<Card>
  <CardContent className="py-12">
    <div className="flex flex-col items-center text-muted-foreground">
      <Icon className="h-8 w-8 mb-3 opacity-40" />
      <p className="text-sm font-medium">{title}</p>
      <p className="text-xs mt-1 text-muted-foreground/60">{subtitle}</p>
    </div>
  </CardContent>
</Card>

// AFTER
<div className="bento-card bg-[#FFFBF5] border border-[#F0E6D8] rounded-2xl p-5 shadow-bento-sm">
  <div className="flex flex-col items-center text-muted-foreground py-12">
    <Icon className="h-8 w-8 mb-3 opacity-40" />
    <p className="text-sm font-medium">{title}</p>
    <p className="text-xs mt-1 text-muted-foreground/60">{subtitle}</p>
  </div>
</div>
```

## Critical Pitfall: SSH Heredoc Escaping

When writing Python scripts via SSH, **heredoc (`<<'EOF'`) fails silently** for strings containing backslashes, quotes, or JSX. Python indentation errors (`IndentationError: unexpected indent`) appear even when the script looks correct.

**Working approaches (in order of reliability):**

1. **`scp` from within hermes** — Write file locally with `write_file` tool (lands in `/tmp/` of hermes), then `scp` to host:
   ```bash
   scp -i /opt/data/home/.hermes/home/.ssh/id_ed25519 /tmp/script.py sean@localhost:/tmp/
   ssh -i /opt/data/home/.hermes/home/.ssh/id_ed25519 sean@localhost "python3 /tmp/script.py"
   ```

2. **Base64 encoding** — Encode and pipe through SSH:
   ```bash
   B64=$(base64 -w0 /tmp/script.py)
   ssh ... "echo '$B64' | base64 -d > /tmp/script.py && echo Written"
   ```

3. **`python3 -c` inline** — Only for very short scripts with no complex quoting

**When ALL approaches fail**: Use `git checkout HEAD --` to restore the file to clean state, then write a fresh Python script via `write_file` → `scp`.

## Critical Pitfall: Duplicate Close Patterns

### The Problem

When TWO components in the same file have IDENTICAL close patterns:
```
      </CardContent>
    </Card>
  );
}

function NextComponent
```

String replacement matches the FIRST occurrence, silently consuming the second component's close tag. This puts the second `export` or function inside a malformed JSX block.

**AnalyticsPage actual failure**: ModelTable and SkillTable both close with the same pattern. The ModelTable close replacement consumed the `export default` statement, producing `"Unexpected export"` at build time. The script reported 11/11 successful replacements but the nesting was broken.

### The Fix: Unique Anchor Context

For close patterns appearing more than once, include a UNIQUE identifier AFTER the closing tag:
- Use `}\n\nexport default function PageName` as the anchor for the last component
- Use `}\n\nfunction NextComponentName` as the anchor for intermediate components
- Never rely on the close tag alone as the search string

### Better Approach: Line-Number-Based Python Script

For complex multi-component files, use exact line indices:

1. `grep -n '<Card>\|</Card>\|</CardContent>\|</CardHeader>' file.tsx` — get all Card tag line numbers
2. `sed -n 'N,Mp'` or Python `readlines()` to view exact content around each boundary
3. Write Python with exact line indices (0-based from `readlines()`)
4. Operate on indices in REVERSE order to avoid offset shifting

```python
# Example: line-based fix in reverse order
with open(path) as f:
    lines = f.readlines()

# Fix close first (higher line number), then open (lower)
lines[close_idx] = '      </div>\n    </div>\n'
lines[open_idx] = '    <div className="bento-card ...>\n'

with open(path, 'w') as f:
    f.writelines(lines)
```

### Verify After Patch

Always run after patching:
```bash
grep -c '</Card>' file.tsx   # Must be 0
grep -c '<Card>' file.tsx    # Must be 0
grep -c 'bento-card' file.tsx  # Should be >= number of converted components
```

Then immediately build to catch nesting errors:
```bash
docker exec -e NODE_PATH=/app/node_modules agent-os-backend \
  /app/node_modules/.bin/vite build \
  /home/sean/.hermes/agent-os/apps/dashboard/frontend
```

## Common Nesting Bug: Extra Div

When converting `<CardContent>` to `<div>`, you must remove BOTH `</CardContent>` AND `</Card>` — replacing them with `</div>\n    </div>`.

Wrong — creates extra div, breaks parent nesting:
```tsx
// Search: "      </CardContent>\n    </Card>"
// Replace with: "      </div>\n    </div>"  ← adds one extra div
```

Correct — CardContent div closes, bento-card div closes:
```tsx
// The bento-card open is: <div className="bento-card">...<div>
// Inner content div needs closing: </div>
// Outer bento-card div needs closing: </div>
```

## Sessions Page: Dot Separator Spacing

The dot separator `&#183;` (·) needs surrounding whitespace in the HTML source for proper browser spacing. Replace bare `&#183;` with ` · ` (with spaces):
```tsx
// BEFORE
<span className="text-border">&#183;</span>

// AFTER
<span className="text-border"> · </span>
```

## Sessions Page: Truncation with `min-w-0`

The session title row uses `min-w-0` on the parent flex container to allow `truncate` to work on child spans:
```tsx
<div className="flex items-center gap-3 min-w-0 flex-1">
  <div className="flex flex-col gap-0.5 min-w-0">
    <span className="text-sm truncate pr-2">...</span>
  </div>
</div>
```

## Critical Pitfall: CronPage schedule_display + formatTime Concatenation

`job.schedule_display` contains the time with AM/PM suffix (e.g. `"At 8:00 AM"`). `formatTime(job.last_run_at)` outputs `"May 7, 2026 8:00 AM"`. Without a newline separator between JSX expressions, adjacent text concatenates as `"At 8:00 AMLast: May 7..."`. Always wrap `formatTime()` calls in their own `<span>` block — never put `formatTime()` output on the same line as another text expression:
```tsx
// CORRECT — each time piece in its own span
<div className="flex items-center gap-4 text-xs text-muted-foreground">
  <span className="font-mono">{job.schedule_display}</span>
  <span>
    {t.cron.last}:{" "}{formatTime(job.last_run_at)}
  </span>
  <span>
    {t.cron.next}:{" "}{formatTime(job.next_run_at)}
  </span>
</div>
```

## Critical Pitfall: Date Formatting — formatDate vs formatTime vs formatAge

Three different date formatters exist across pages:
- `formatDate(str)` — date-only strings `"2026-05-01"` via regex; returns `"Invalid Date"` for full ISO datetimes
- `formatTime(ts)` — Unix timestamps and full ISO datetimes
- `formatAge(iso)` — relative time from ISO-8601 string (ObservabilityPage, SessionsPage); returns `NaNd ago` if input is invalid/empty

**`formatAge` NaN bug**: When `new Date(iso).getTime()` returns `NaN` (invalid ISO string), `Math.floor(NaN / 1000)` = `NaN`, producing `NaNd ago`. Fix:

```tsx
// BEFORE
function formatAge(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const s = Math.floor(ms / 1000);

// AFTER
function formatAge(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  if (Number.isNaN(ms)) return "—";
  const s = Math.floor(ms / 1000);
```

This appears in `ObservabilityPage.tsx` and can silently produce `NaNd ago` in Recent Sessions tables.

Two different date formatters exist. `formatDate(str)` handles date-only `"2026-05-01"` via regex. `formatTime(ts)` handles Unix timestamps and full ISO datetimes. Calling `formatDate("2026-05-07T14:30:00Z")` returns "Invalid Date" — use `formatTime()` for API timestamps.

## Critical Pitfall: Floating Point Precision in Settings Inputs

When loading `ag.temperature` (a JSON number like `0.30000001192092896`) into a React `useState` string, naive `String(ag.temperature)` preserves the float imprecision. Use `Math.round()` to clean it:

```tsx
// WRONG — preserves float encoding
setTemperature(ag.temperature != null ? String(ag.temperature) : "");

// CORRECT — rounds to 2 decimal places before string conversion
setTemperature(ag.temperature != null ? Math.round(Number(ag.temperature) * 100) / 100).toString() : "");
```

The issue manifests in `<input type="number">` spinbuttons which display the raw float value even when the user sees `0.3` in the UI (the browser_snapshot shows the imprecision; `inputEl.value` confirms the actual value is clean).

## CSS Switch Override for Bento Theme

The shadcn `<Switch>` component uses dark CSS variables (`--background`, `--muted-foreground`) that don't match the bento warm cream theme. Add this to `index.css` to override:

```css
/* ============================================================
   BENTO SWITCH (override shadcn dark defaults)
   ============================================================ */
[role="switch"] {
  background-color: #FAD4C0 !important;
  cursor: pointer;
}
[role="switch"][aria-checked="true"] {
  background-color: #16A34A !important;
}
[role="switch"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

Without this, the switch OFF state shows as dark gray (`#1f2937`) instead of warm peach (`#FAD4C0`).

## Pages Status

| Page | Cards | Status | Notes |
|------|-------|--------|-------|
| ContainerPage | many | ✅ Done | Stat cards, human-readable ports |
| ModelsPage | 5+ | ✅ Done | TokenBar + model cards |
| CronPage | 2 | ✅ Done | Bento grid + formatTime spacing |
| ProfilesPage | 2 | ✅ Done | Bento grid |
| ObservabilityPage | 4 | ✅ Done | MetricCard warm styling |
| AnalyticsPage | 7 | ✅ Done | All bento-card, formatDate fix |
| LogsPage | 1 | ✅ Done | Simple wrapper Card |
| SessionsPage | 1 | ✅ Done | bento-card, dot separator spacing |
| ConfigPage | 3 | ✅ Done | yaml view + search/active category cards |
| EnvPage | 6 | ✅ Done | LLN Providers card + Category Cards |
| SkillsPage | 4 | ✅ Done | Search + skills list + empty state + toolset card

## Build + Deploy Workflow

```bash
# 1. Restore from git first (clean baseline)
git -C /home/sean/.hermes/agent-os checkout HEAD -- apps/dashboard/frontend/src/pages/TargetPage.tsx

# 2. Apply patches
python3 /tmp/bento_script.py /path/to/TargetPage.tsx

# 3. Verify no Card tags remain
grep -c '</Card>' /path/to/TargetPage.tsx  # must be 0

# 4. Build
docker exec -e NODE_PATH=/app/node_modules agent-os-backend \
  /app/node_modules/.bin/vite build \
  /home/sean/.hermes/agent-os/apps/dashboard/frontend 2>&1 | tail -10

# 5. Deploy on success
# Copy dist/assets/* to /home/sean/.hermes/agent-os-patched/frontend-dist/assets/
# Copy dist/index.html to /home/sean/.hermes/agent-os-patched/frontend-dist/
# docker restart agent-os-backend
```
