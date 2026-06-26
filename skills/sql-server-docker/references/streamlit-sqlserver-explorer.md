# Streamlit + SQL Server — Interactive Database Explorer

Build a browser-based SQL Server query app with Streamlit, pymssql, and Plotly. Alternative to Prisma Studio for exploring databases with custom filters, charts, and Sankey diagrams.

## When to Use

- You've restored a SQL Server database and need to explore it interactively
- You need filtered views, aggregations, and charts — not just raw table browsing
- Prisma Studio is too complex or doesn't support SQL Server
- You need to present findings to a non-technical audience

## Architecture: Single-File vs Modular

### Single-File (Recommended for simplicity)

All code in one `app.py` — database layer, query builders, chart builders, and UI pages. Good for:
- Quick prototypes
- Sharing as a single artifact
- Easy deployment (one file to copy)

Structure:
```python
# === 1. Imports + Constants ===
# === 2. Database Layer ===
#   get_connection() @st.cache_resource
#   query() → list[dict]
#   query_df() → pandas DataFrame
#   check_connection() → (bool, str)
# === 3. Query Builders ===
#   Each returns (sql_string, params_dict)
#   Use build_where() helper for filter logic
# === 4. Chart Builders ===
#   Each accepts DataFrame, returns plotly Figure or None
#   apply_theme() for dark GitHub-style theme
# === 5. UI Pages ===
#   One function per page, receives Filters namespace
# === 6. Main App ===
#   Sidebar nav + global filters + page router
```

### Modular (Better for maintenance)

Split into `connect.py`, `queries.py`, `charts.py`, `app.py`. Use when the app has 10+ queries or 8+ pages.

## Database Connection Layer

```python
import pymssql
import streamlit as st

DB_CONFIG = {
    "server": "172.17.0.1",  # Docker host gateway
    "port": 1433,
    "user": "SA",
    "password": "password",
    "database": "DatabaseName",
    "timeout": 30,
    "login_timeout": 10,
}

@st.cache_resource(ttl=300)
def get_connection():
    try:
        conn = pymssql.connect(**DB_CONFIG)
        conn.autocommit(True)
        return conn
    except pymssql.OperationalError as e:
        st.error(f"Connection failed: {e}")
        return None

def query_df(sql, params=None, max_rows=50000):
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params or {})
        rows = cur.fetchmany(max_rows)
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()
```

**Note:** pymssql uses Python-style `%(name)s` parameter markers, NOT `@name` which is T-SQL variable syntax.

## Query Builders — Parameterized Pattern

Each function returns a `(sql_string, params_dict)` tuple. Use `build_where()` to compose filters:

```python
def build_where(conditions, base="1=1"):
    where = " AND ".join(conditions) if conditions else base
    return f"WHERE {where}"

def users_by_department(department=None, min_logins=None, active_only=True):
    cond, params = [], {}
    if department:
        cond.append("d.Name LIKE %(dept)s"); params["dept"] = f"%{department}%"
    if min_logins is not None:
        cond.append("u.LoginAttempts >= %(min)s"); params["min"] = min_logins
    if active_only:
        cond.append("u.DeletedDate IS NULL")
    where = build_where(cond)
    return f"""SELECT u.FirstName, u.LastName, d.Name AS Department, u.LoginAttempts
               FROM Users u
               LEFT JOIN Departments d ON u.DepartmentId = d.Id
               {where} ORDER BY u.LastName""", params
```

### Lessons from Real SQL Export Files

When porting existing SQL queries into the app:

1. **Verify column existence before assuming joins work.** The `RFIIsolations` table has NO `AreaId` column. The original export query joined `INNER JOIN Areas ea ON i.AreaId = ea.Id` — reusing the isolation point's area. Equipment has its own `AreaId`. Always check `sys.columns` for the actual table schema.

2. **`GROUP BY` with no aggregate functions is an anti-pattern.** The original Lock History query had `GROUP BY col1, col2, ...` but no `SUM()`/`COUNT()`/`AVG()`. This works in SQL Server but is fragile and won't port to other databases. Replace with simple `SELECT ... ORDER BY`.

3. **Check for broken LEFT JOINs.** The original log timeline query had `LEFT OUTER JOIN UserRoles ur ON u.UserRoleId = r.Id` which compares a user role ID to an RFI ID — two different domains. This produces either zero rows or garbage. Drop broken joins entirely.

4. **Timezone conversions.** Original queries may have `SWITCHOFFSET(... 'AUS Eastern Standard Time')` conversions. If the database stores UTC, leave timestamps raw. Add timezone display as a UI label if needed.

## Chart Types

All charts use a dark theme (GitHub-dark, `plotly_dark` template, Viridis color scale):

| Chart | Plotly Function | Data Pattern | When to Use |
|-------|----------------|--------------|-------------|
| **Pie** | `px.pie()` | Category + count | Distribution (states, types) |
| **Horizontal bar** | `px.bar(orientation='h')` | Category + value + optional color | Rankings (top N) |
| **Histogram** | `px.histogram()` | Single numeric column | Duration distribution |
| **Line** | `px.line(color=...)` | Date + value + category | Time series by type |
| **Gantt** | `px.timeline()` | Start + end + row key | Lock on/off periods |
| **Heatmap** | `px.imshow()` | Pivot table (day × hour) | Activity patterns |
| **Sankey** | `go.Sankey()` | Source → target → weight | Flow/chain visualization |

### Sankey Diagrams — Implementation

Sankey diagrams show flow between entities. Three common patterns:

#### 1. State Transition Flow

Use `ROW_NUMBER()` window function to find consecutive log entries for each entity, then count transitions:

```sql
SELECT l1.RFIId, l1.RFILogType AS FromType, l2.RFILogType AS ToType, COUNT(*) AS Weight
FROM (
    SELECT RFIId, RFILogType, CreatedDate,
           ROW_NUMBER() OVER (PARTITION BY RFIId ORDER BY CreatedDate) AS Seq
    FROM RFILogs
) l1
INNER JOIN (
    SELECT RFIId, RFILogType, CreatedDate,
           ROW_NUMBER() OVER (PARTITION BY RFIId ORDER BY CreatedDate) AS Seq
    FROM RFILogs
) l2 ON l1.RFIId = l2.RFIId AND l1.Seq = l2.Seq - 1
WHERE l1.RFILogType != l2.RFILogType
GROUP BY l1.RFIId, l1.RFILogType, l2.RFILogType
```

Plotly code:
```python
nodes = sorted(set(agg["FromType"].tolist() + agg["ToType"].tolist()))
idx_map = {v: i for i, v in enumerate(nodes)}
fig = go.Figure(go.Sankey(
    node=dict(label=[type_names[n] for n in nodes], pad=15, thickness=20, color="color_scale"),
    link=dict(source=[idx_map[r["FromType"]] for _, r in agg.iterrows()],
              target=[idx_map[r["ToType"]] for _, r in agg.iterrows()],
              value=[r["Weight"] for _, r in agg.iterrows()])))
```

#### 2. Entity Chain (Worker → Device → Location)

Build links as a flat list of (source, target, value=1) tuples, then aggregate:

```python
links = []
for _, r in df.iterrows():
    links.append({"source": f"🧑 {r['Worker']}", "target": f"🔒 {r['Device']}", "value": 1})
    links.append({"source": f"🔒 {r['Device']}", "target": f"📦 {r['Location']}", "value": 1))
    links.append({"source": f"📦 {r['Location']}", "target": f"📋 {r['Document']}", "value": 1))
ldf = pd.DataFrame(links)
agg = ldf.groupby(["source", "target"], as_index=False)["value"].sum()
```

#### 3. Vendor → Item Flow

Same as entity chain but using vendor/category/item categories. Prefix labels with emoji to distinguish node types at a glance: `🏢 Vendor`, `📄 JobNumber`, `⚙️ Equipment`.

## Global Sidebar Filters Pattern

Use a simple namespace object to pass filters to all page functions:

```python
Filters = type("Filters", (), {})()
Filters.dfrom = filter_date_from
Filters.dto = filter_date_to
Filters.company = filter_company if filter_company else None
Filters.active_only = filter_active

def page_dashboard(flt):
    with st.spinner("Loading…"):
        df = query_df(rfi_jobs_vendors(flt.dfrom, flt.dto, flt.company, active_only=flt.active_only))

pages[page](Filters)
```

## Port Forwarding for Browser Access

Streamlit binds to `0.0.0.0:PORT` inside the container. To access from the host:

```bash
# On the host — socat forwards host:PORT to container:PORT
socat TCP-LISTEN:PORT,fork,reuseaddr TCP:CONTAINER_IP:PORT

# Or SSH tunnel
ssh -L PORT:CONTAINER_IP:PORT user@host
```

Common container IPs: `172.17.0.2` (Docker bridge), `172.19.0.2` (custom bridge). Check with `hostname -I`.

## Sankey Query Pitfalls

1. **Zero active records.** If a Sankey filters on `WHERE status = 'active'` and the DB has no active records (all completed/historical), it silently returns nothing. Always check counts first, then fall back to "most recent N" instead of "only active".

2. **Too many nodes overload the diagram.** When building entity-chain Sankeys, TOP 500 raw records can produce dozens of unique nodes. The diagram becomes unreadable. Apply a sensible LIMIT to the underlying query.

3. **Aggregate before building links.** Building links as individual rows then grouping in pandas is simpler than trying to write a single SQL GROUP BY for chain flows. Accept the temporary DataFrame overhead.

## Query Performance — CTE Pre-aggregation

When a query joins a table with a 1:N or N:M relationship (e.g., `RFIIsolations` has many rows per RFI), the result set explodes. **Pre-aggregate in a CTE** before joining:

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

This avoids the cartesian product that occurs when joining `RFIIsolations` directly into a query that also joins `RFILocksRFIJobs` (47K rows).

## Schema Verification — Always Check sys.columns First

Before writing any query against an unfamiliar SQL Server database, verify column names exist:

```sql
SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('TableName') ORDER BY column_id
```

**Real example:** `RFIIsolations` has NO `AreaId` column. The original export query and my first app version both assumed it did. The correct join for equipment area is `INNER JOIN Areas ea ON e.AreaId = ea.Id` (via Equipment), not `ON ri.AreaId` (via RFIIsolations).
