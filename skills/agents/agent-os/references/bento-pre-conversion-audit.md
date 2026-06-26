# Bento Pre-Conversion Audit: Bugs to Fix First

Before converting any page from shadcn `<Card>` to bento-card divs, run these audits. Bugs in shared utility functions and component prop overrides will persist through the conversion and ruin the visual result.

---

## 1. `timeAgo()` in `src/lib/utils.ts` — NaN for null/undefined

**Symptom:** Sessions list shows "NaNd ago" for sessions with `null` or `undefined` `last_active` timestamps.

**Root cause:** `Date.now() / 1000 - ts` where `ts` is `null`/`undefined` produces `NaN`.

**Fix:**
```typescript
export function timeAgo(ts: number | undefined | null): string {
  if (ts == null || Number.isNaN(ts)) return "—";
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return `${Math.floor(diff)}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}
```

**Audit command:**
```bash
grep -rn 'timeAgo' /home/sean/.hermes/agent-os/apps/dashboard/frontend/src/pages/
# Then grep for all call sites to confirm NaN display issues
```

---

## 2. `formatDate()` in `AnalyticsPage.tsx` — Invalid Date

**Symptom:** Analytics page shows "Invalid Date" in the date range display.

**Root cause:** `new Date("2026-05-01")` in some JS environments interprets this as UTC midnight, but `.toLocaleDateString()` uses local timezone, causing off-by-one or Invalid Date for dates near midnight UTC.

**Fix:**
```typescript
const formatDate = (day: string | undefined | null): string => {
  if (!day) return "—";
  // Handle ISO date-only format (YYYY-MM-DD) explicitly
  const d = /^\d{4}-\d{2}-\d{2}$/.test(day);
  if (d) {
    const [y, m, mo, da] = day.match(/\d+/g)!.map(Number);
    return new Date(y, mo - 1, da).toLocaleDateString("en-US", {
      year: "numeric", month: "short", day: "numeric",
    });
  }
  const parsed = new Date(day);
  if (Number.isNaN(parsed.getTime())) return "—";
  return parsed.toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric",
  });
};
```

**Audit command:**
```bash
grep -rn 'Invalid Date\|formatDate\|new Date(' /home/sean/.hermes/agent-os/apps/dashboard/frontend/src/pages/AnalyticsPage.tsx
```

---

## 3. Cron `formatTime()` — JSX Text Node Spacing

**Symptom:** "AMNext" or "AMLast" — text runs together without spaces.

**Root cause:** JSX expressions next to plain text need explicit `{" "}` separators:
```tsx
// BROKEN — text runs together
{t.cron.last}:{formatTime(job.last_run_at)}
{t.cron.next}:{formatTime(job.next_run_at)}

// FIXED
{t.cron.last}:{" "}{formatTime(job.last_run_at)}
{t.cron.next}:{" "}{formatTime(job.next_run_at)}
```

**Also:** Use locale-independent formatting to avoid `Intl` discrepancies:
```typescript
function formatTime(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const dateStr = d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  const timeStr = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
  return `${dateStr} ${timeStr}`;
}
```

---

## 4. NouiTypography `H2` — className Override Ignored

**Symptom:** After conversion, heading text still appears dark or wrong color despite setting `className="text-[#111827]"`.

**Root cause:** `H2` (from `@/components/NouiTypography`) applies its own CSS classes (`text-[#e8e6e3]` or similar) that have higher specificity than the passed `className`. The prop is not truly overridable — it gets merged but its values win.

**Fix:** Use plain HTML elements (`<h2>`, `<p>`, `<span>`) with inline classes for headings inside bento cards:
```tsx
// BROKEN — className ignored
<H2 variant="xl" className="text-[#111827]">Settings</H2>

// FIXED — plain element with explicit class
<h2 className="text-lg font-semibold text-[#111827]">Settings</h2>
```

**Audit command:**
```bash
grep -rn 'H2 variant=\|H2 className=' /home/sean/.hermes/agent-os/apps/dashboard/frontend/src/pages/
```

---

## Pre-Conversion Checklist

Run before starting any page conversion:

1. [ ] `grep -rn 'timeAgo\|formatDate\|formatTime' src/lib/utils.ts src/pages/*.tsx` — check for NaN/Invalid handling
2. [ ] `grep -rn 'H2 variant=' src/pages/` — identify NouiTypography overrides that need plain HTML replacement
3. [ ] `grep -rn 'new Date(' src/pages/ | grep -v 'localeDateString\|toLocale' ` — find raw Date constructors that may fail
4. [ ] `grep -rn '{".*"}\|{" "}{' src/pages/` — find JSX text expression patterns that may be missing explicit space separators
5. [ ] Build and verify baseline renders correctly before starting conversion
