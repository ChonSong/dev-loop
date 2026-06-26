# Streamlit Database Explorer — Interactive Query App

Build a full-featured Streamlit app for exploring a SQL Server (or SQLite) database with filters, charts, and custom SQL. Runs inside the container and is exposed via socat alongside the simple data browser.

## Architecture

```
streamlit_explorer/
├── app.py       -- Main entry: 6 pages, sidebar filters, navigation router
├── connect.py   -- DB connection layer: cached pool, retry, error handling
├── queries.py   -- Parameterized SQL templates per report type
└── charts.py    -- Plotly figure builders with dark theme
```

Run on port 8766 (or whatever is free) and expose via socat alongside the browser on 8765.

## Connection Layer (connect.py)

```python
import pymssql
import streamlit as st

DB_CONFIG = {
    "server": "172.17.0.1",  # Host from container
    "port": 1433,
    "user": "SA",
    "password": "YourPassword!",
    "database": "DatabaseName",
    "timeout": 30,
    "login_timeout": 10,
}

@st.cache_resource(ttl=300)
def get_connection():
    """Cached connection reused across reruns for up to 5 minutes."""
    try:
        conn = pymssql.connect(**DB_CONFIG)
        conn.autocommit(True)
        return conn
    except pymssql.OperationalError as e:
        st.error(f"Connection failed: {e}")
        return None

def query(sql, params=None, max_rows=50000):
    """Execute with retry (3 attempts, 1s backoff). Returns list of dicts."""
    conn = get_connection()
    if conn is None:
        return []
    for attempt in range(3):
        try:
            cur = conn.cursor(as_dict=True)
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            return cur.fetchmany(max_rows)
        except pymssql.OperationalError as e:
            if attempt < 2:
                time.sleep(1)
                st.cache_resource.clear()
                conn = get_connection()
            else:
                st.error(f"Query failed after 3 attempts: {e}")
                return []
```

Key design choices:
- `as_dict=True` returns rows as dicts for easy column access
- `@st.cache_resource` keeps the TCP connection alive across reruns
- 3 retries handle transient network blips from container->host routing
- 50K row cap prevents OOM on large tables

## Pre-built Query Templates (queries.py)

Each report type is a function that accepts filter parameters and returns `(sql_string, params_dict)`:

```python
def rfi_jobs_vendors(date_from=None, date_to=None, company=None, 
                     rfi_state=None, active_only=True):
    conditions = []
    params = {}
    
    if date_from:
        conditions.append("r.CreatedDate >= @from")
        params["from"] = date_from
    if date_to:
        conditions.append("r.CreatedDate <= @to")
        params["to"] = date_to
    if company:
        conditions.append("c.Name LIKE @company")
        params["company"] = f"%{company}%"
    if active_only:
        conditions.append("r.DeletedDate IS NULL")
    
    sql = f"""
    SELECT r.RFINumber, r.Description, j.JobNumber, c.Name AS Vendor
    FROM RFIs r
    INNER JOIN RFIJobs rj ON rj.RFIId = r.Id
    INNER JOIN Jobs j ON rj.JobId = j.Id
    INNER JOIN Companies c ON j.CompanyId = c.Id
    WHERE {' AND '.join(conditions) if conditions else '1=1'}
    ORDER BY r.CreatedDate DESC
    """
    return sql, params
```

Pattern:
- Use named parameters (`@from`, `@to`, `@company`) not string interpolation — prevents SQL injection and handles type conversion
- Build conditions list dynamically, join with AND
- Default to `1=1` when no filters active
- Always ORDER BY DESC to show latest first

## Chart Builders (charts.py)

All charts use Plotly Express with a consistent dark theme:

```python
THEME = {
    "template": "plotly_dark",
    "plot_bgcolor": "#0d1117",
    "paper_bgcolor": "#0d1117",
    "font": {"color": "#c9d1d9"},
}

def apply_theme(fig):
    fig.update_layout(**THEME, margin=dict(l=40, r=40, t=40, b=40))
    return fig
```

Supported chart types:
- **Pie**: RFI state distribution (categorical breakdown)
- **Horizontal bar**: Top-N tables (isolation frequency, worker activity, vendor breakdown) — use `orientation="h"` with `categoryorder="total ascending"`
- **Histogram**: Lock duration distribution — `nbins=50`, clip outliers
- **Line**: Daily activity timeline — `EventDate` on x-axis, `EventCount` on y
- **Timeline/Gantt**: Lock on/off periods — `px.timeline()` with `x_start`, `x_end`, `y`
- **Heatmap**: Activity by day-of-week and hour — pivot table from `groupby`

All chart functions return `None` when the input DataFrame is empty, so callers can safely `if fig: st.plotly_chart(...)`.

## App Structure (app.py)

```
sidebar:
  - Connection status indicator (green/red)
  - Navigation radio: Dashboard, Report1, Report2, ..., Analysis
  - Global filter pane: date range, company, worker, RFI state, active-only toggle

pages:
  Dashboard: 4-column metric cards, 4 chart grid
  RFI -> Jobs -> Vendors: data table + vendor breakdown chart + heatmap
  Jobs -> Isolations -> Equipment: data table
  Lock History: data table + duration histogram + day/hour heatmap + lock timeline
  RFI Log Timeline: data table with log type filter
  Analysis: 
    - Pre-built reports dropdown (isolation frequency, worker activity, state dist, etc.)
    - Custom SQL mode (SELECT-only, CSV download button)
```

## Streamlit Startup Command

```bash
streamlit run app.py --server.port=8766 --server.address=0.0.0.0 \
  --server.headless=true --server.maxUploadSize=5
```

Note: `streamlit` is often installed to `/home/hermeswebui/.hermes/home/.local/bin/streamlit` in Hermes containers. Use the full path if `which streamlit` returns nothing.

## Connecting from Desktop Azure Data Studio / SSMS

| Field | Value |
|-------|-------|
| Server | `localhost,1433` |
| Authentication | SQL Login |
| User | `SA` |
| Password | `YourPassword!` |
| Trust server certificate | True |

The Streamlit app connects programmatically via pymssql using the same credentials but pointing to the Docker bridge IP (172.17.0.1) instead of localhost.

## Port Convention

| Service | Container Port | Socat Port | Purpose |
|---------|---------------|------------|---------|
| SQL Server | 1433 | 1433 | Direct DB connection |
| SQLite Browser | 8765 | 8765 | Simple data browser |
| Streamlit App | 8766 | 8766 | Interactive dashboard |
