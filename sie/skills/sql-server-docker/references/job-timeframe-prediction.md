# Job Timeframe Comparison & Completion Prediction

## Feature Overview

A Streamlit page that compares planned vs actual job durations and predicts completion dates for active/cancelled jobs. Built for the OneTag HMAS Sydney database but applicable to any SQL Server job-tracking system.

## Data Sources

Planned dates come from `Jobs.PlannedStartDate` and `Jobs.PlannedEndDate` (populated for ~8% of jobs). Actual dates come from lock activity: `MIN(RFILocksRFIJobs.LockOnDate)` and `MAX(RFILocksRFIJobs.LockOffDate)` per job — available for ~54% of jobs.

## Query Design — CTE Pre-aggregation

When joining `RFIIsolations` (many rows per RFI) with `RFILocksRFIJobs` (47K rows), the result set explodes. **Pre-aggregate in a CTE**:

```sql
WITH IsoCounts AS (
    SELECT ri.RFIId, COUNT(DISTINCT ri.IsolationPointId) AS IsolationPointCount
    FROM RFIIsolations ri
    WHERE ri.DeletedDate IS NULL
    GROUP BY ri.RFIId
)
SELECT j.*, SUM(ic.IsolationPointCount) AS IsolationPointCount
FROM Jobs j
INNER JOIN RFIs r ON ...
LEFT JOIN IsoCounts ic ON r.Id = ic.RFIId
GROUP BY j.Id, ...
```

## Charts

| Chart | Type | Purpose |
|-------|------|---------|
| Gantt comparison | Grouped horizontal bar | Planned (blue) vs actual (red) per job |
| Variance histogram | Histogram | Distribution of schedule variance days |
| Planned vs actual scatter | Scatter with diagonal | On-time line reference |
| Vendor performance | Horizontal bar | Avg variance by vendor (green/red) |

## Prediction Model

Simple weighted blend (no ML library needed):

1. Vendor historical mean (weight 0.4): avg actual duration for vendor's completed jobs (if >=3)
2. Planned regression (weight 0.4): planned_days * vendor_ratio where vendor_ratio = avg_actual / avg_planned
3. Activity extrapolation (weight 0.2): elapsed days since first lock + rate-based remaining estimate

Validation: Run the same model on completed jobs, compute MAE (mean absolute error). Display predicted-vs-actual scatter.

```python
vendor_stats = training.groupby("Vendor").agg(
    VendorAvgActual=("ActualDurationDays", "mean"),
    VendorAvgPlanned=("PlannedDurationDays", "mean"),
    VendorCount=("JobNumber", "count"),
).reset_index()
vendor_stats["VendorRatio"] = vendor_stats["VendorAvgActual"] / vendor_stats["VendorAvgPlanned"].clip(lower=1)
global_ratio = training["ActualDurationDays"].sum() / training["PlannedDurationDays"].clip(lower=1).sum()
```

The model intentionally avoids sklearn/xgboost dependencies — works with stdlib + pandas only.

## Page Layout

Three sub-tabs:
1. Overview & Comparison — KPI cards, filterable Gantt, data table with CSV download
2. Detailed Analysis — Variance histogram, scatter plot, vendor performance, vendor stats table
3. Predict Future Jobs — Training data summary, prediction output table, overdue count, MAE validation

## Schema Mapping — OneTag HMAS Sydney

- Jobs.JobState: 0=Cancelled, 1=Active, 2=Complete
- Jobs.PlannedStartDate / PlannedEndDate: only populated for ~8% of jobs
- RFILocksRFIJobs.LockOnDate / LockOffDate: actual activity timestamps (~54% of jobs)
- Companies.Name: vendor/contractor name
- RFIIsolations.IsolationPointId: many per RFI (N:M with RFIs)
- Equipment.AreaId: the correct source for equipment compartment area (NOT RFIIsolations.AreaId which doesn't exist)