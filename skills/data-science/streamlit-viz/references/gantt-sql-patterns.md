# Gantt Chart SQL Patterns for OneTag DB

## Jobs with Actual Lock Dates

```sql
SELECT
    j.Id AS JobId, j.JobNumber, j.Description AS JobDescription,
    j.JobState, j.OnHold, j.ControlledJob,
    c.Name AS Vendor, sa.StandardActivityNumber,
    MIN(rlrj.LockOnDate) AS JobStart,
    MAX(rlrj.LockOffDate) AS JobEnd,
    DATEDIFF(DAY, MIN(rlrj.LockOnDate), MAX(rlrj.LockOffDate)) AS DurationDays,
    COUNT(DISTINCT rlrj.Id) AS LockEventCount,
    COUNT(DISTINCT rj.RFIId) AS RFICount
FROM Jobs j
INNER JOIN Companies c ON j.CompanyId = c.Id
LEFT JOIN StandardActivities sa ON j.StandardActivityId = sa.Id
LEFT JOIN RFIJobs rj ON rj.JobId = j.Id AND rj.DeletedDate IS NULL
LEFT JOIN RFILocksRFIJobs rlrj ON rlrj.RFIJobId = rj.Id AND rlrj.DeletedDate IS NULL
WHERE j.DeletedDate IS NULL
GROUP BY j.Id, j.JobNumber, j.Description, j.JobState,
         j.OnHold, j.ControlledJob, c.Name, sa.StandardActivityNumber
HAVING MIN(rlrj.LockOnDate) IS NOT NULL
    AND MAX(rlrj.LockOffDate) > '2000-01-01'
    AND MIN(rlrj.LockOnDate) <= MAX(rlrj.LockOffDate)
```

## Isolations with Applied/Removal Dates

```sql
SELECT
    rj.JobId,
    j.JobNumber,
    r.RFINumber,
    i.Name AS IsolationPoint,
    ia.Name AS IsolationArea,
    e.Name AS Equipment,
    ri.AppliedDate AS IsoStart,
    ri.RemovalDate AS IsoEnd,
    ri.RFIIsolationState,
    CASE WHEN ri.RemovalDate IS NULL THEN 'Active' ELSE 'Removed' END AS IsoStatus
FROM RFIIsolations ri
INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
INNER JOIN IsolationPoints i ON ri.IsolationPointId = i.Id AND i.DeletedDate IS NULL
LEFT JOIN Equipment e ON ri.EquipmentId = e.Id AND e.DeletedDate IS NULL
INNER JOIN Areas ia ON i.AreaId = ia.Id
INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
INNER JOIN Jobs j ON rj.JobId = j.Id AND j.DeletedDate IS NULL
WHERE ri.DeletedDate IS NULL
    AND ri.AppliedDate IS NOT NULL
    AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
```

## Key Data Quality Filters

- `MAX(rlrj.LockOffDate) > '2000-01-01'` — filters out SQL Server default `0001-01-01` dates
- `MIN(rlrj.LockOnDate) <= MAX(rlrj.LockOffDate)` — filters out bad data where end < start
- `ri.AppliedDate IS NOT NULL` — isolations must have an applied date to be meaningful on a timeline
- `ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01'` — active isolations have NULL removal; filter bad dates

## Left Join Gotcha: EquipmentId Can Be NULL

`RFIIsolations.EquipmentId` is **nullable**. An isolation can be applied to an isolation point without being tied to specific equipment. Using `INNER JOIN Equipment` silently drops every isolation row where `EquipmentId` is NULL.

**Always use `LEFT JOIN`** for Equipment in isolation queries:

```sql
LEFT JOIN Equipment e ON ri.EquipmentId = e.Id AND e.DeletedDate IS NULL
```

Then handle NULL in Python chart labels:

```python
equip = iso["Equipment"] if pd.notna(iso["Equipment"]) else ""
equip_str = f" ({equip})" if equip else ""
label = f"{iso['IsolationPoint']}{equip_str}"
```

## Cross-Section Pattern (preferred over parent-child nesting for multi-job context)

When most isolations span multiple jobs (96% in the OneTag dataset), nesting isolations under a single job as "children" is misleading. Use a **cross-section** pattern instead:

1. Let the user select one or more jobs from a picker
2. Show each job as a blue bar (lock start → lock end)
3. For each job, find *all* isolations linked via the DB relationship (`iso_df["JobNumber"] == job["JobNumber"]`)
4. Indent isolation bars under their job
5. Color isolations by their timing relationship to the job window
6. Generate a summary sentence per job with duration + isolation counts by relationship

## Join Key Gotcha

The isolation query returns **both** `rj.JobId` (UUID) and `j.JobNumber` (string). When matching isolations to jobs in Python:

- Jobs DataFrame has `JobId` (UUID) and `JobNumber` (string)
- Isolations DataFrame has `JobId` (UUID) and `JobNumber` (string)
- **Match on `JobNumber` (string)** for chart display purposes — UUID comparison can fail silently if types don't match exactly
- If you need to match on UUID, cast both sides explicitly

## JobState Mapping

| Value | Label |
|-------|-------|
| 0 | Cancelled |
| 1 | Active |
| 2 | Completed |

## RFIIsolationState Values

| Value | Meaning |
|-------|---------|
| 0 | (rare) |
| 1 | (rare) |
| 2 | Pending? |
| 3 | Applied (most common — 13518 of 14123) |
| 4 | (rare — 6 records) |

## Data Volume Notes

- ~9700 jobs total, ~5200 with actual lock dates
- ~14000 isolations total
- Up to 123 isolations per job (e.g., WO-SYD-00004869-11)
- Use `px.timeline` with a unified DataFrame + `categoryorder="array"` for combined parent-child views — NOT `go.Bar` with `base` + duration (which breaks the time axis)

## Overlap Query (for Multi-Job Cross-Section)

**PREFER filtering by the DB relationship column (`JobNumber`/`JobId`) rather than date overlap alone.** The isolation query above already links isolations to their specific job through `RFIJobs`. Use `iso_df["JobNumber"] == job["JobNumber"]` in Python to get only the isolations actually related to that job.

Use date-overlap-only filtering ONLY when there's no direct relationship column (e.g., the child items are from a different system or log table):

```sql
-- Overlap: AppliedDate <= JobEnd AND (RemovalDate >= JobStart OR RemovalDate IS NULL)
SELECT ...
FROM RFIIsolations ri
INNER JOIN ...
WHERE ri.AppliedDate <= %(job_end)s
  AND (ri.RemovalDate >= %(job_start)s OR ri.RemovalDate IS NULL)
  AND ri.DeletedDate IS NULL
  AND ri.AppliedDate IS NOT NULL
  AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
```

## Relationship Classification (Python)

Classify each overlapping isolation's relationship to the job window:

```python
def classify_overlap(iso_start, iso_end, job_start, job_end):
    if iso_start < job_start and (pd.isna(iso_end) or iso_end > job_end):
        return "Throughout"       # isolation covers entire job period
    elif iso_start < job_start:
        return "Started earlier"  # began before the job, ended during it
    elif pd.isna(iso_end) or iso_end > job_end:
        return "Ends later"       # began during the job, extends past it
    else:
        return "Fits within"      # applied and removed inside job window
```

## Relationship Crosscheck (Jobs ↔ Isolations Overlap)

**Always run this before deciding to nest isolations under jobs in a parent-child Gantt.** If most isolations span multiple jobs, nesting is misleading.

### Isolation Timing vs Job Lock Dates

```sql
SELECT cat, COUNT(*) AS cnt FROM (
    SELECT CASE 
        WHEN ri.AppliedDate >= jdr.LockStart 
             AND (ri.RemovalDate IS NULL OR ri.RemovalDate <= jdr.LockEnd) 
        THEN 'Inside job window'
        WHEN ri.AppliedDate < jdr.LockStart THEN 'Applied before lock start'
        WHEN ri.AppliedDate > jdr.LockEnd THEN 'Applied after job ended'
        WHEN ri.AppliedDate >= jdr.LockStart AND ri.RemovalDate > jdr.LockEnd 
        THEN 'Removed after job ended'
        ELSE 'Other/uncertain' END AS cat
    FROM RFIIsolations ri
    INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
    INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
    INNER JOIN (
        SELECT rj2.JobId, MIN(rlrj.LockOnDate) AS LockStart, MAX(rlrj.LockOffDate) AS LockEnd
        FROM RFIJobs rj2
        LEFT JOIN RFILocksRFIJobs rlrj ON rlrj.RFIJobId = rj2.Id AND rlrj.DeletedDate IS NULL
        WHERE rj2.DeletedDate IS NULL
        GROUP BY rj2.JobId
        HAVING MIN(rlrj.LockOnDate) IS NOT NULL AND MAX(rlrj.LockOffDate) > '2000-01-01'
    ) jdr ON jdr.JobId = rj.JobId
    WHERE ri.DeletedDate IS NULL AND ri.AppliedDate IS NOT NULL
) sub
GROUP BY cat
ORDER BY COUNT(*) DESC;
```

### Isolation Distribution per Job

```sql
SELECT bucket, COUNT(*) AS NumJobs FROM (
    SELECT CASE 
        WHEN cnt = 1 THEN '1'
        WHEN cnt BETWEEN 2 AND 3 THEN '2-3'
        WHEN cnt BETWEEN 4 AND 6 THEN '4-6'
        WHEN cnt BETWEEN 7 AND 10 THEN '7-10'
        WHEN cnt BETWEEN 11 AND 20 THEN '11-20'
        ELSE '21+' END AS bucket
    FROM (
        SELECT COUNT(DISTINCT ri.Id) AS cnt
        FROM RFIJobs rj
        INNER JOIN RFIs r ON rj.RFIId = r.Id AND r.DeletedDate IS NULL
        INNER JOIN RFIIsolations ri ON r.Id = ri.RFIId AND ri.DeletedDate IS NULL AND ri.AppliedDate IS NOT NULL
        WHERE rj.DeletedDate IS NULL
        GROUP BY rj.JobId
    ) sub
) grouped
GROUP BY bucket
ORDER BY CASE bucket WHEN '1' THEN 1 WHEN '2-3' THEN 2 WHEN '4-6' THEN 3 WHEN '7-10' THEN 4 WHEN '11-20' THEN 5 WHEN '21+' THEN 6 END;
```

### Real-World Reference: OneTag DB Stats

| Metric | Value |
|--------|-------|
| Jobs with lock dates | 5,178 |
| Jobs with isolations | 7,004 |
| Jobs with both | 5,178 |
| Avg isolations per job | 13 |
| Max isolations per job | 123 |
| Isolations "Inside job window" | 3,651 (4%) |
| Isolations "Applied before lock start" | 71,221 (96%) |
| Avg isolation duration | 23 days |
| Max isolation duration | 673 days |
| Isolations with removal dates | 100% |

**Rule of thumb**: if < 20% of children fit inside parent windows, use the Cross-Section Pattern instead of nesting.
