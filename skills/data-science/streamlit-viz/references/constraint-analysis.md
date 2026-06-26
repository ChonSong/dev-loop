# Constraint & Bottleneck Analysis Patterns

## Overview

Identify scheduling constraints by analyzing isolation point contention, gap windows between jobs, and area-level overcrowding. Uses SQL window functions (LAG) to calculate gaps between consecutive isolation events on the same point.

## Bottleneck Points (contention scoring)

Rank isolation points by how many distinct jobs have used them. High job count = more contention = less availability for new work.

```sql
SELECT
    i.Id, i.Name AS IsolationPoint,
    ia.Name AS Area,
    COUNT(DISTINCT rj.JobId) AS JobCount,
    COUNT(DISTINCT ri.Id) AS IsolationCount,
    AVG(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS AvgDurationDays,
    MIN(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS MinDurationDays,
    MAX(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS MaxDurationDays,
    SUM(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS TotalDays
FROM IsolationPoints i
INNER JOIN Areas ia ON i.AreaId = ia.Id
INNER JOIN RFIIsolations ri ON i.Id = ri.IsolationPointId AND ri.DeletedDate IS NULL
    AND ri.AppliedDate IS NOT NULL
    AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
INNER JOIN Jobs j ON rj.JobId = j.Id AND j.DeletedDate IS NULL
WHERE i.DeletedDate IS NULL
GROUP BY i.Id, i.Name, ia.Name
HAVING COUNT(DISTINCT rj.JobId) >= 2   -- only points used by 2+ jobs
ORDER BY JobCount DESC
```

**Key join note**: The bottleneck query joins through `RFIJobs → RFIs → RFIIsolations` — the full relationship chain from jobs to isolation points. Dropping any join in this chain produces wrong counts.

**Visualization**: Horizontal bar chart, y = IsolationPoint, x = JobCount, color = AvgDurationDays. Gives a quick read of which points are most contested.

## Gap Analysis (scheduling opportunity finder)

For a single isolation point, find gaps between consecutive job isolation periods using `LAG()`. Green highlighted periods on the timeline = free windows where another job could be scheduled without waiting for the point to become available.

```sql
WITH IsoJobs AS (
    SELECT ri.AppliedDate AS IsoStart,
           COALESCE(ri.RemovalDate, GETUTCDATE()) AS IsoEnd,
           ri.IsolationPointId,
           j.JobNumber, j.Description AS JobDescription,
           r.RFINumber
    FROM RFIIsolations ri
    INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
    INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
    INNER JOIN Jobs j ON rj.JobId = j.Id AND j.DeletedDate IS NULL
    WHERE ri.DeletedDate IS NULL
      AND ri.AppliedDate IS NOT NULL
      AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
)
SELECT *,
       LAG(IsoEnd) OVER (
           PARTITION BY IsolationPointId ORDER BY IsoStart
       ) AS PrevEnd,
       DATEDIFF(DAY, 
           LAG(IsoEnd) OVER (PARTITION BY IsolationPointId ORDER BY IsoStart), 
           IsoStart
       ) AS GapDays
FROM IsoJobs
WHERE IsolationPointId = %(point_id)s   -- parameterized filter
ORDER BY IsoStart
```

**How the gap chart works**:
1. Fetch all isolation events for a single point (ordered by applied date)
2. `LAG(IsoEnd)` gets the previous event's end date
3. `GapDays = DATEDIFF(DAY, PrevEnd, IsoStart)` → positive = free gap, negative or zero = overlap
4. Build a flat records list: each event is a blue bar, each positive gap is a green bar
5. The green bars represent scheduling opportunities — periods when this isolation point was available

**KPI cards to show**:
- Total jobs using this point
- Total isolation events
- Average gap in days
- Maximum gap in days

## Area Overcrowding

Group by area to find which physical zones have the most concurrent isolation activity. High isolation point count + high jobs affected = area where scheduling is tightest.

```sql
SELECT
    ia.Name AS Area,
    COUNT(DISTINCT i.Id) AS IsolationPoints,
    COUNT(DISTINCT ri.Id) AS IsolationEvents,
    COUNT(DISTINCT rj.JobId) AS JobsAffected,
    AVG(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS AvgDurationDays
FROM Areas ia
INNER JOIN IsolationPoints i ON ia.Id = i.AreaId AND i.DeletedDate IS NULL
INNER JOIN RFIIsolations ri ON i.Id = ri.IsolationPointId AND ri.DeletedDate IS NULL
    AND ri.AppliedDate IS NOT NULL
    AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
WHERE ia.DeletedDate IS NULL
GROUP BY ia.Name
ORDER BY JobsAffected DESC
```

**Visualization**: Scatter plot — x = IsolationPoints, y = JobsAffected, size = IsolationEvents, color = AvgDurationDays. Shows which areas have many isolation points affecting many jobs (top-right = most constrained).

## Interpretation Guide

- **Bottleneck points**: High job count + high avg duration = critical constraint. Look for gaps (green windows) on the gap timeline to find scheduling opportunities.
- **Large gaps** (> 30 days) on busy points = opportunity to batch smaller jobs during the idle period.
- **Areas** with many isolation points but few jobs = underutilized. Areas with few points but many jobs = the points in that area are reused heavily; contention is high despite low point count.
