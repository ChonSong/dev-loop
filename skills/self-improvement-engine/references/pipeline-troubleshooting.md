# Pipeline Troubleshooting Record

Bugs found and fixed during the June 22 restoration from git commit `9e5982d`.

## Bug 1: Bold-Colon Regex Mistmatch (learnings_scanner.py)

**Symptom:** Scanner ran but found 0 entries even though `.learnings/LEARNINGS.md` existed with valid data. All entries showed `area=backend priority=medium recurrence=1` (defaults).

**Root cause:** The regex patterns expected the colon OUTSIDE the bold markers (`**Field**:\s*`) but the markdown format had the colon INSIDE (`**Field:**`). For example:
- File: `**Priority:** high`
- Regex: `\*\*Priority\*\*:\s*(\w+)` — expected `**Priority**: high`

**Fix:** Changed patterns to `\*\*Field[:\*]+\s*(\w+)` — matches either `**Field:**` or `**Field**:`.

**Pattern:** Always check regex against actual file content. Markdown bold can have the colon inside or outside the markers depending on author preference or text editor auto-formatting.

## Bug 2: Timezone-Naive Datetime (learnings_scanner.py)

**Symptom:** Scanner crashed with `TypeError: can't subtract offset-naive and offset-aware datetimes`.

**Root cause:** `parse_iso_timestamp()` returned timezone-aware datetimes (when the input had Z/+HH:MM), but the fallback `datetime.now(timezone(timedelta(hours=10)))` returned timezone-aware. However, if the input timestamp was a bare date string without timezone info, `parse_iso_timestamp()` returned a naive datetime.

**Fix:** Added `if ts.tzinfo is None: ts = ts.replace(tzinfo=...)` after parsing.

**Pattern:** Always normalize timezone awareness before arithmetic. One-off `replace()` is simpler than making both sides aware conditionally.

## Bug 3: AUTHOR Path Assignment (self_improvement.py)

**Symptom:** `self_improvement.py` had `AUTHOR=*** / "scripts" / "skill_author.py"` — syntax error. The `***` was visible in the git show output but was actually a terminal rendering artifact of the original file's content being somehow corrupted or a copy-paste artifact.

**Fix:** Rewrote as `AUTHOR = HERMES_SYNC / "scripts" / "skill_author.py"` consistent with `SCANNER` on the line above.

## Restoration Command

```bash
cd /home/sc/repos/archive/hermes-sync
for f in self_improvement.py learnings_scanner.py skill_author.py; do
  git show 9e5982d:scripts/$f > /home/sc/repos/hermes-sync/scripts/$f
done
```

Then fix the three bugs above before running.
