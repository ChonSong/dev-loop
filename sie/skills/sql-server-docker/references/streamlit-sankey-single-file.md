# Single-File Streamlit App with Sankey Diagrams

Merge the modular Streamlit pattern (connect + queries + charts) into a single deployable `app.py` while adding Sankey flow visualization. Useful when you want a self-contained interactive dashboard that deploys as one file.

## Architecture

```
app.py (~400-500 lines)
├── Constants & Imports        — LOG_TYPE_NAMES, theme palette, DB config
├── Database Layer              — get_connection(), query(), query_df()
├── Query Templates (8-10)     — parameterized SQL functions returning (sql, params)
├── Chart Builders (8-12)      — Plotly functions returning go.Figure or None
│   ├── Standard charts        — pie, bar, histogram, heatmap, Gantt, line
│   └── Sankey diagrams (3)    — state flow, lock chain, vendor→equipment
├── UI Pages (6)               — each renders a section with filters + charts
├── Sidebar                    — navigation + global filters (date, text, state)
└── Router                     — dict mapping page label → page function
```

## Sankey Diagram Construction

Sankey diagrams use `plotly.graph_objects.Sankey` with `node` and `link` properties:

```python
import plotly.graph_objects as go

fig = go.Figure(go.Sankey(
    node=dict(
        label=["Node A", "Node B", "Node C"],
        pad=15, thickness=20,
        color="#3498db"
    ),
    link=dict(
        source=[0, 1],    # indices into node list
        target=[1, 2],
        value=[10, 5]
    )
))
```

### Sankey Variant 1: State Transition Flow

Purpose: Show how records move through a state machine over their lifecycle.

**SQL pattern:**
```sql
-- For each RFI, order log entries chronologically, pair consecutive states
WITH numbered AS (
    SELECT RFIId, RFILogType,
           ROW_NUMBER() OVER (PARTITION BY RFIId ORDER BY CreatedDate) AS Seq
    FROM RFILogs
)
SELECT l1.RFILogType AS FromType, l2.RFILogType AS ToType, COUNT(*) AS Weight
FROM numbered l1
JOIN numbered l2 ON l1.RFIId = l2.RFIId AND l1.Seq = l2.Seq - 1
WHERE l1.RFILogType != l2.RFILogType
GROUP BY l1.RFILogType, l2.RFILogType
```

**Python:**
```python
def sankey_state_flow():
    rows = query(sql_above)
    if not rows: return None
    df = pd.DataFrame(rows)
    agg = df.groupby(["FromType", "ToType"], as_index=False)["Weight"].sum()
    agg = agg[agg["Weight"] >= 3]  # filter noise
    nodes = sorted(set(agg["FromType"].tolist() + agg["ToType"].tolist()))
    idx = {v: i for i, v in enumerate(nodes)}
    fig = go.Figure(go.Sankey(
        node=dict(label=[f"{n}: {LOG_TYPE_NAMES[n]}" for n in nodes],
                  color=["green" if n in active_states else "red" for n in nodes]),
        link=dict(source=[idx[r.FromType] for _, r in agg.iterrows()],
                  target=[idx[r.ToType] for _, r in agg.iterrows()],
                  value=[r.Weight for _, r in agg.iterrows()])))
    return fig
```

### Sankey Variant 2: Asset Chain Flow

Purpose: Show physical asset chains (Worker → Padlock → LockBox → RFI).

```sql
SELECT CONCAT(u.FirstName, ' ', u.LastName) AS Worker,
       p.SerialNumber AS Padlock,
       rlb.SerialNumber AS LockBox,
       r.RFINumber
FROM RFILocksRFIJobs rlrj
JOIN RFILocks rl ON rlrj.RFILockId = rl.Id
JOIN PadLocks p ON rl.PadLockId = p.Id
JOIN Users u ON rl.UserId = u.Id
JOIN RFIJobs rj ON rlrj.RFIJobId = rj.Id
JOIN RFIs r ON rj.RFIId = r.Id
LEFT JOIN RFILockBoxes rlb ON r.Id = rlb.RFIId
WHERE rlrj.LockOffDate IS NULL AND rlrj.DeletedDate IS NULL
```

Build links by creating three edges per row: `Worker→Padlock`, `Padlock→LockBox`, `LockBox→RFI`. Aggregate by `(source, target)` pairs. Use emoji prefixes in labels (`🧑 Worker`, `🔒 Padlock`, `📦 LockBox`, `📋 RFI-123`) to visually distinguish node categories.

### Sankey Variant 3: Vendor → Equipment Flow

Purpose: Map business relationships — which vendors work on which equipment.

```sql
SELECT c.Name AS Vendor, j.JobNumber, e.Name AS Equipment
FROM Jobs j
JOIN Companies c ON j.CompanyId = c.Id
JOIN RFIJobs rj ON rj.JobId = j.Id
JOIN RFIs r ON rj.RFIId = r.Id
JOIN RFIIsolations ri ON r.Id = ri.RFIId
JOIN Equipment e ON ri.EquipmentId = e.Id
WHERE j.DeletedDate IS NULL
```

Build links as `Vendor→Job` and `Job→Equipment`. Prefix labels with emoji: `🏢 Vendor`, `📄 J-123`, `⚙️ Equipment`.

## Converting Existing SQL Exports into Parameterized Templates

When the user has pre-existing SQL queries (from Azure Data Studio, SSMS, etc.):

1. **Copy verbatim** — start with the original as a comment, then refactor below
2. **Replace literals with parameters** — convert `WHERE Col = 'foo'` into `WHERE Col = %(param)s`
3. **Build WHERE conditionally** — collect conditions in a list and `" AND ".join()` at query time
4. **Fix bugs found in exports:**
   - `GROUP BY` all columns with no aggregates → remove GROUP BY entirely (or add `COUNT(*)`)
   - Joins on wrong columns (e.g. `ON u.UserRoleId = r.Id` where `r` is RFIs) → remove or fix
   - Missing soft-delete filters → add `AND DeletedDate IS NULL`
   - Hardcoded timezone conversions → document them, make configurable
5. **Add chart companions** — for each export query that produces aggregatable data, write a chart function that takes the query result DataFrame and returns a Plotly figure
6. **Cache aggressively** — wrap with `@st.cache_data(ttl=60)` to avoid re-querying on UI interactions

## Filters (sidebar)

All pages use a shared set of global filters instantiated as a simple type:

```python
Filters = type("Filters", (), {})()
Filters.dfrom = st.sidebar.date_input("From", default_from)
Filters.dto = st.sidebar.date_input("To", default_to)
# ... more filters
```

The `Filters` object is passed to each page function.

## Shared Theme

```python
THEME = {
    "template": "plotly_dark",
    "color_continuous_scale": "Viridis",
    "font": {"color": "#c9d1d9"},
    "plot_bgcolor": "#0d1117",
    "paper_bgcolor": "#0d1117",
}

def apply_theme(fig):
    fig.update_layout(**THEME)
    return fig
```

## Page Structure (6 Pages)

| Page | Purpose | Charts | Key Query |
|------|---------|--------|-----------|
| 📊 Dashboard | Summary KPIs + 4 overview charts | Pie, bar, histogram, worker activity | `dashboard_summary()` UNION ALL queries |
| 📋 RFI→Jobs→Vendors | Work request mapping | Vendor breakdown bar, activity heatmap | 5-table join RFIs→RFIJobs→Jobs→Companies |
| 🔗 Jobs→Isolations→Equipment | Full asset hierarchy | (dataframe only) | 10-table join through Equipment |
| 🔒 Lock History | Padlock tracking | Heatmap, histogram, Gantt timeline, stats | 9-table lock chain join |
| 📜 RFI Log Timeline | Lifecycle events | (dataframe + type filter) | RFILogs→RFIs→Users→Companies |
| 📈 Analysis | Sankey + reports + custom SQL | State flow, lock chain, vendor Sankey | CTE windowed for state transitions |

## Custom SQL Mode

Allows ad-hoc SELECT queries with CSV download. Displayed as read-only dataframe with row count. Guard against non-SELECT statements with a simple `.upper().startswith("SELECT")` check.

## Key Reliability Patterns

| Pattern | Implementation |
|---------|---------------|
| Connection caching | `@st.cache_resource(ttl=300)` — reuses pymssql connection for 5 min |
| Query caching | `@st.cache_data(ttl=60)` — avoids re-execution on widget interaction |
| Retry logic | 3 attempts, 1s backoff, `st.cache_resource.clear()` on failure |
| Row limit | `fetchmany(50000)` — prevents OOM |
| Empty state | `if df.empty: st.warning(...); return` — no crashes on empty results |
| Duration formatting | `fmt_duration()` — converts minutes to `"2h 13m"` human format |
