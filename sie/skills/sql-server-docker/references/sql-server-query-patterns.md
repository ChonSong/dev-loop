# SQL Server Query Patterns for HMAS Sydney

## DISTINCT + TOP Syntax

In SQL Server, `DISTINCT` must come **immediately after SELECT**, before `TOP`:

```sql
-- CORRECT:
SELECT DISTINCT TOP 50 col1, col2 FROM Table WHERE ...

-- WRONG (syntax error 156):
SELECT TOP 10 DISTINCT col1, col2 FROM Table WHERE ...
```

Always add `TOP N` to queries with many joins to prevent unbounded result sets.

## Dynamic WHERE Clause Builder (Python/SQL Server)

When building parameterized queries with optional filters in Streamlit:

```python
def build_where(conditions, base="1=1"):
    where = " AND ".join(conditions) if conditions else base
    return f"WHERE {where}"

def my_query(date_from=None, company=None, active_only=True):
    cond, params = [], {}
    if date_from:
        cond.append("r.CreatedDate >= %(dfrom)s"); params["dfrom"] = date_from
    if company:
        cond.append("c.Name LIKE %(company)s"); params["company"] = f"%{company}%"
    if active_only:
        cond.append("r.DeletedDate IS NULL")
    where = build_where(cond)
    sql = f"SELECT ... FROM ... {where} ORDER BY ..."
    return sql, params

# Usage with pymssql:
cur.execute(sql, params)
```

Key: never interpolate user input — always use `%(key)s` parameter markers with a dict.

## Pre-Aggregation CTEs for Many-to-Many Joins

When joining a table with a many-to-many relationship (e.g. RFIs ↔ RFIIsolations), the row count explodes. Pre-aggregate in a CTE:

```sql
WITH IsoCounts AS (
    SELECT ri.RFIId, COUNT(DISTINCT ri.IsolationPointId) AS IsolationPointCount
    FROM RFIIsolations ri
    WHERE ri.DeletedDate IS NULL
    GROUP BY ri.RFIId
)
SELECT
    j.JobNumber,
    SUM(ic.IsolationPointCount) AS IsolationPointCount
FROM Jobs j
INNER JOIN RFIJobs rj ON rj.JobId = j.Id
INNER JOIN RFIs r ON rj.RFIId = r.Id
LEFT JOIN IsoCounts ic ON r.Id = ic.RFIId
WHERE j.DeletedDate IS NULL
GROUP BY j.JobNumber
```

## Column Existence Check

Before referencing any column, verify it exists:

```sql
SELECT name FROM sys.columns
WHERE object_id = OBJECT_ID('TableName')
ORDER BY column_id
```

Common gotcha: `RFIIsolations` has **no** `AreaId` column — `Equipment` has it instead. The BC export query reused the isolation point's area for equipment by mistake.

## Date Derivation from Activity Tables

Many entity tables only have `PlannedStartDate`/`PlannedEndDate` (sparse coverage ~8%). Derive actual dates from activity:

```sql
MIN(rlrj.LockOnDate) AS ActualStart,
MAX(rlrj.LockOffDate) AS ActualEnd,
DATEDIFF(DAY, MIN(rlrj.LockOnDate), MAX(rlrj.LockOffDate)) AS ActualDurationDays
```

## Null-Safe Comparisons in Pandas

When computing derived columns after SQL aggregation:

```python
df["HasActualDates"] = df["ActualStart"].notna() & df["ActualEnd"].notna()
df["OnTime"] = df.apply(
    lambda r: r["ActualDurationDays"] <= r["PlannedDurationDays"]
    if (pd.notna(r["ActualDurationDays"]) and pd.notna(r["PlannedDurationDays"]))
    else None, axis=1
)
```

Never compare NaT/NaN with `<=` directly — always guard with `pd.notna()`.

## Chart Builder Defensive Patterns

Always guard chart functions against empty/null data:

```python
def chart_lock_histogram(df, max_min=480):
    if df.empty: return None
    if "DurationMinutes" not in df.columns: return None
    df = df.dropna(subset=["DurationMinutes"])
    df = df[df["DurationMinutes"] <= max_min]
    if df.empty: return None
    fig = px.histogram(df, x="DurationMinutes", nbins=50, ...)
    return apply_theme(fig)
```

## RFILogType Enum Reference

| ID | Name |
|----|------|
| 1 | AuthorityToIsolateSignOff |
| 2 | IsolationsActive |
| 3 | IsolationsActiveVerified |
| 4 | RFIComplete |
| 5 | RFICompleteVerified |
| 6 | RFIRejected |
| 7 | AlterationsNotes |
| 8 | LockOffComplete |
| 9 | LockOnComplete |
| 10 | LockAudit |
| 11 | RFIRemove |
| 12 | RFIUnlock |
| 13 | RFIPrint |
| 14 | RFIOnHold |
