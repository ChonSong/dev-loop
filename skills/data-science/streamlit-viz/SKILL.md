---
name: streamlit-viz
description: Streamlit + Plotly visualization patterns — Gantt charts, timelines, and interactive charts that actually work. Load when building Streamlit dashboards with Plotly charts, especially Gantt/timeline views.
---

# Streamlit + Plotly Visualization Patterns

> **Reference**: `references/gantt-sql-patterns.md` — complete SQL queries for Jobs + Isolations Gantt data, including data quality filters and state mappings.
> **Reference**: `references/constraint-analysis.md` — bottleneck point scoring, gap analysis with LAG window function, area overcrowding patterns.
> **Reference**: `references/hermes-state-db-sessions.md` — Hermes state.db schema, session analytics queries, gap computation, and derived columns for pipeline dashboards.

## Gantt Charts

### The Right Approach: `px.timeline` for Everything

**Always use `px.timeline` for Gantt charts.** It handles datetime axes correctly — bars are positioned and sized by actual timestamps.

```python
import plotly.express as px

fig = px.timeline(
    df,
    x_start="StartDate",    # column name (string), not values
    x_end="EndDate",        # column name (string), not values
    y="Label",
    color="StatusColumn",
    color_discrete_map={
        "Completed": "#2ecc71",
        "Active": "#3498db",
        "Cancelled": "#e74c3c",
    },
    title="Gantt Chart Title",
    labels={"Label": "", "StatusColumn": "Status"},
    hover_data={
        "ExtraCol1": True,
        "ExtraCol2": True,
        "StartDate": "|%Y-%m-%d %H:%M",
        "EndDate": "|%Y-%m-%d %H:%M",
    },
)
fig.update_yaxes(autorange="reversed")
fig.update_layout(height=max(400, len(df) * 28))
```

### Parent-Child Grouping (e.g., Jobs → Isolations)

> **⚠️ CRITICAL: Verify data relationships before nesting.** Query the overlap ratio first. If most "child" items span multiple "parent" periods (e.g., 96% of isolations are applied before the job's lock period starts), nesting them under a single parent is factually misleading. Always run the crosscheck query (see `references/gantt-sql-patterns.md` → "Relationship Crosscheck") before deciding to nest.

Use `px.timeline` with a **unified DataFrame** containing both parents and children, with `categoryorder="array"` to enforce ordering:

```python
# Build ordered records: each job followed by its isolations
records = []
for _, job in jobs_df.iterrows():
    records.append({
        "Task": f"📋 {job['JobNumber']}: {job['Description'][:45]}",
        "Start": job["JobStart"],
        "End": job["JobEnd"],
        "Color": job["JobStateLabel"],       # e.g. "Completed"
        "Type": "Job",
        "Detail": f"{job['Vendor']} | {job['DurationDays']}d",
    })
    for _, iso in job_isolations.iterrows():
        records.append({
            "Task": f"  └─ {iso['IsolationPoint']} ({iso['Equipment']})",
            "Start": iso["IsoStart"],
            "End": iso["IsoEnd"],
            "Color": f"Iso: {iso['Status']}",  # e.g. "Iso: Active"
            "Type": "Isolation",
            "Detail": f"{iso['Area']} | {iso['RFINumber']}",
        })

plot_df = pd.DataFrame(records)

# Combined color map — job states + isolation states
color_map = {
    "Completed": "#2ecc71",
    "Active": "#3498db",
    "Cancelled": "#e74c3c",
    "Iso: Active": "#e74c3c",
    "Iso: Removed": "#27ae60",
}

fig = px.timeline(
    plot_df,
    x_start="Start",
    x_end="End",
    y="Task",
    color="Color",
    color_discrete_map=color_map,
    hover_data={"Type": True, "Detail": True, "Start": "|%Y-%m-%d %H:%M", "End": "|%Y-%m-%d %H:%M"},
)
fig.update_yaxes(
    autorange="reversed",
    categoryorder="array",
    categoryarray=[r["Task"] for r in records],  # enforces job→isolation ordering
)
fig.update_layout(height=max(500, len(records) * 18))
```

Key points:
- **Use `px.timeline`, NOT `go.Bar` with `base` + duration** — `go.Bar` with `base` doesn't create a proper datetime x-axis; all bars appear to start at the same point
- **`categoryorder="array"` + `categoryarray`** enforces exact y-axis ordering (job, then its isolations)
- **Prefix isolation labels** with `└─` and indent for visual hierarchy
- **Use distinct color values** for jobs vs isolations (e.g., `"Active"` vs `"Iso: Active"`) so the legend doesn't merge them
- **`color_discrete_map`** gives one legend entry per unique value — no duplicates

### Key Parameters

- **`x_start`, `x_end`**: Column names (strings), not values — `px.timeline` resolves them from the DataFrame
- **`color`**: Categorical column for color-coding. Use `color_discrete_map` for explicit colors, NOT `color_continuous_scale`
- **`hover_data`**: Dict of `{col: True}` for extra columns, or `col: "|%Y-%m-%d %H:%M"` for formatted dates
- **`autorange="reversed"`**: Essential — without this, the first row appears at the bottom
- **Height**: Scale with `len(df) * 18-28` pixels per row. Use `max(400, ...)` for a minimum

### Cross-Section Pattern (Alternative to Parent-Child Nesting)

When the data doesn't support nesting (child items span multiple parents), use a **cross-section** instead. The user picks one or more parent items, and the chart shows all overlapping child items within each parent's window, color-coded by their relationship.

**CRITICAL: filter by DB relationship, not just date overlap.** If the child table has a foreign-key path back to the parent table (e.g., isolations → RFIs → RFIJobs → Jobs), use that relationship column (`JobNumber` or `JobId`) as the primary filter. Date overlap alone shows unrelated child items that happen to share the same calendar period (e.g., isolations from a different compartment on the same ship).

```python
# Correct: filter by DB relationship first
related = children_df[children_df["ParentId"] == parent["Id"]].copy()

# Wrong: showing unrelated items that just happen to overlap in time
related = children_df[
    (children_df["Start"] <= parent_end) &
    (children_df["End"] >= parent_start)
].copy()
```

Once the DB relationship filter is applied, the date overlap becomes redundant — every child linked to the parent is relevant. The relationship labels (Throughout, Started earlier, etc.) still provide the timing context.

**Single-parent** (simplest):

plot_df = pd.DataFrame(records)
color_map = {
    "Job": "#3498db",
    "Fits within": "#2ecc71",
    "Started earlier": "#e67e22",
    "Ends later": "#e74c3c",
    "Throughout": "#9b59b6",
}

fig = px.timeline(plot_df, x_start="Start", x_end="End", y="Task",
                  color="Color", color_discrete_map=color_map,
                  category_orders={"Color": ["Job", "Fits within", "Started earlier",
                                              "Ends later", "Throughout"]})
fig.update_yaxes(autorange="reversed")
```

**Multi-parent with per-item sentence generation** (user selects N parents, each shown with its children + a text summary):

```python
all_records = []
sentences = []
for _, parent in selected_parents.iterrows():
    children = find_overlapping(children_df, parent["Start"], parent["End"])
    rel_counts = {"Fits within": 0, "Started earlier": 0, "Ends later": 0, "Throughout": 0}

    # Parent bar
    all_records.append({
        "Task": f"📋 {parent['Number']}: {parent['Description'][:45]}",
        "Start": parent["Start"], "End": parent["End"],
        "Color": "Job", "Detail": f"{parent.get('Vendor','')}",
    })

    # Child bars
    for _, child in children.iterrows():
        rel = classify_overlap(child["Start"], child["End"], parent["Start"], parent["End"])
        rel_counts[rel] += 1
        all_records.append({
            "Task": f"  {child['Name']} ({child['Equipment']})",
            "Start": child["Start"], "End": child["End"],
            "Color": rel,
            "Detail": f"{child.get('Area','')} | {child.get('RFI','')} | {rel}",
        })

    # Per-parent sentence
    dur = int(parent.get("DurationDays", 0) or 0)
    total_children = sum(rel_counts.values())
    bits = [f"**{parent['Number']}** — {parent['Description'][:60]}"]
    bits.append(f"Lasted **{dur} days**")
    if total_children > 0:
        detail = [f"{c} {r.lower()}" for r in ["Fits within","Started earlier","Ends later","Throughout"]
                  if (c := rel_counts[r]) > 0]
        bits.append(f"{total_children} overlapping: {', '.join(detail)}")
    sentences.append(" — ".join(bits))

for s in sentences:
    st.markdown(f"• {s}")

plot_df = pd.DataFrame(all_records)
fig = px.timeline(plot_df, ..., categoryarray=[r["Task"] for r in all_records])
st.plotly_chart(fig, width='stretch')
```

**Relationship classification function:**

```python
def classify_overlap(child_start, child_end, parent_start, parent_end):
    """Classify how a child period relates to a parent period.
    Returns one of: 'Throughout', 'Started earlier', 'Ends later', 'Fits within'"""
    if child_start < parent_start and (pd.isna(child_end) or child_end > parent_end):
        return "Throughout"      # child fully contains parent
    elif child_start < parent_start:
        return "Started earlier" # child began before parent, ended during it
    elif pd.isna(child_end) or child_end > parent_end:
        return "Ends later"      # child began during parent, extends past it
    else:
        return "Fits within"     # child entirely inside parent window
```

Relationship meanings:
- **Throughout** (purple) — child was active for the parent's *entire* duration; parent window fits inside child window
- **Started earlier** (orange) — child began before the parent, but ended during it
- **Ends later** (red) — child began during the parent, extends beyond it
- **Fits within** (green) — child started and ended inside the parent's window

The same child can have different relationships to different parents (e.g., "Started earlier" for Parent A, "Throughout" for Parent B) — correct, because the overlap is relative to each parent's specific window.

Advantages over nesting:
- **Honest display** — doesn't imply a hierarchy that doesn't exist
- **Scalable** — one parent at a time, so no data truncation
- **Informative** — color instantly shows containment vs spanning

### SQL Server Date Gotchas for Gantt

SQL Server's `datetimeoffset` type can contain `0001-01-01` as a default/unset value. Always filter:

```sql
HAVING MIN(date_col) IS NOT NULL
    AND MAX(date_col) > '2000-01-01'
    AND MIN(date_col) <= MAX(date_col)
```

Also filter in WHERE for nullable end-date columns:
```sql
WHERE (end_date IS NULL OR end_date > '2000-01-01')
```

### Streamlit Integration

```python
import streamlit as st

# Search & filter panel (collapsible)
with st.expander("🔍 Search & Filters", expanded=True):
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        search_term = st.text_input("Search", placeholder="e.g. keyword")
    with fcol2:
        filter_vendor = st.text_input("Vendor")
    with fcol3:
        filter_state = st.multiselect("State", options=["A", "B", "C"], default=["A", "B", "C"])
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        date_from = st.date_input("From", value=None)
    with dcol2:
        date_to = st.date_input("To", value=None)

# Apply filters to DataFrame BEFORE passing to chart
filtered = df.copy()
if search_term:
    mask = filtered["Col1"].str.contains(search_term, case=False, na=False)
    filtered = filtered[mask]
# ... etc for other filters

# Date filtering with timezone-aware comparison
if date_from:
    filtered = filtered[filtered["StartDate"] >= pd.Timestamp(date_from, tz="UTC")]
if date_to:
    filtered = filtered[filtered["EndDate"] <= pd.Timestamp(date_to, tz="UTC")]

# Slider for max items
max_items = st.slider("Max items", 1, 50, 25)
fig = chart_function(filtered, max_items)
st.plotly_chart(fig, width='stretch')
```

#### Cross-Section Pattern (Jobs + Isolations)

When the user asks for a combined Jobs + Isolations Gantt, check the data relationship FIRST before deciding the approach:

1. **Run the overlap crosscheck** (`references/gantt-sql-patterns.md` has the SQL) to see what % of isolations fall "inside" job windows
2. If < 20% fit inside (OneTag: 4%), **don't nest** — use the cross-section pattern instead:
   - Filter by DB relationship (`JobNumber`), not date overlap
   - Build records per-job, each with isolation bars indented underneath
   - Classify timing: Throughout / Started earlier / Ends later / Fits within
   - Generate a plain-English sentence for each selected job
3. If > 60% fit inside, parent-child nesting via unified DataFrame + `categoryorder="array"` is fine

**EquipmentId can be NULL** — always LEFT JOIN Equipment in isolation queries. Handle NULL in labels.

## Inter-Session Gap Analysis (for Pipeline Throughput)

When building a session-timeline or pipeline dashboard that needs to answer "should we increase frequency?", include gap analysis:

```python
# Compute gaps between consecutive sessions
s = df.sort_values("started_at")
s["gap_s"] = s["started_at"] - s["ended_at"].shift(1)
s["gap_min"] = s["gap_s"] / 60.0

# Gap histogram (capped at 360min = 6hrs)
fig = go.Figure()
fig.add_trace(go.Histogram(
    x=s["gap_min"].clip(0, 360),
    nbinsx=40, marker_color="#AB63FA", opacity=0.7
))
fig.update_layout(height=350, bargap=0.05)

# Gap percentiles (insight summary)
import numpy as np
pcts = [10, 25, 50, 75, 90, 95, 99]
vals = s["gap_min"].dropna()
summary = {p: f"{np.percentile(vals, p):.1f}" for p in pcts}
```

**Interpreting the verdict:**
- **Median gap < 15 min**: pipeline is well-packed. Increasing frequency adds overhead without throughput gain.
- **Median gap 15-30 min**: moderate idle time. Marginal gains from tightening.
- **Median gap 30-120 min**: significant idle windows. Increase frequency.
- **Median gap > 120 min**: pipeline is under-scheduled. Double automated job frequency.

The gap histogram shows the *distribution* (right-skewed is normal; a second peak at high values = stalled periods). The per-hour gap breakdown reveals when dead time concentrates (e.g., overnight, lunch hours).

Key metrics for the verdict panel:
```python
tot_active = df["dur_min"].sum()
tot_gap = s["gap_min"].sum()
utilization = tot_active / (tot_active + tot_gap) * 100
med_gap = s["gap_min"].median()
p90_gap = np.percentile(s["gap_min"].dropna(), 90)
```

## Streamlit Render Performance

### First Load Takes 60-90s (Acceptable for Data-Intensive Dashboards)

Streamlit re-runs the entire script on first load. With SQL queries + git log across 41 repos + 6-8 Plotly charts, the first render can take 60-90s. This is normal and each subsequent load is faster due to `@st.cache_data`.

**Mitigations:**
- Use `@st.cache_data(ttl=60)` on expensive data-loading functions. The first load is still slow, but every load within the TTL is instant.
- Set `day_range = st.sidebar.slider("Days back", 1, 60, 7)` — default to 7 days, let user expand if needed.
- For `load_git()` with many repos, use a shorter default period (7 days) — most repos have 0 recent commits anyway.
- **CRITICAL**: avoid creating one trace per item in Plotly. Use grouped traces (scatter markers, `px.timeline`) instead. A `for` loop with `fig.add_trace(go.Bar(...))` for 100+ items creates a JSON spec that takes 30-60s+ to serialize and can crash orjson.

### Process Management

When running `streamlit run` as a background Hermes process:
- The shell forks: one `bash` wrapper + one `python3.11` server + the Python script child process. `process(action="log")` may show 0 lines because stderr goes to the forked server, not the original watcher. Redirect to a file: `2>/tmp/streamlit.log`.
- The Streamlit `_stcore/health` endpoint returns "ok" as soon as the server starts — even before the Python script finishes its first run. The "Running..." spinner is the true indicator.
- If `@st.cache_data` fails, the error appears in the browser (Streamlit shows it as an alert), NOT in the terminal log. Check the browser output for traceback.

For throughput/volume dashboards where you want bars (tokens, commits) with an overlaid line (sessions, users):

```python
from plotly.subplots import make_subplots
import plotly.graph_objects as go

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Bar(x=df["date"], y=df["tokens"] / 1e3,
           name="Tokens (K)", marker_color="#636EFA", opacity=0.7),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=df["date"], y=df["sessions"],
               name="Sessions", mode="lines+markers",
               line=dict(color="#EF553B", width=2)),
    secondary_y=True,
)

fig.update_layout(
    height=350, hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig.update_yaxes(title_text="Tokens (K)", secondary_y=False)
fig.update_yaxes(title_text="Sessions", secondary_y=True)
```

This is the standard pattern for every "throughput vs activity" chart. The dual-axis avoids one metric dominating the other visually.

## Large Dataset Timelines (Scatter Markers Instead of Individual Bar Traces)

When you have 50-200+ sessions/items to show on a timeline, **DO NOT create one `go.Bar` trace per item** — each trace becomes a separate JSON node. With 100+ traces plus annotations and vrects, the figure JSON balloons and `orjson.dumps` in Plotly's `to_json` will either hang (>60s) or crash with `TypeError: Type is not JSON serializable`.

**Use `go.Scatter` with markers instead** — one trace per category (source), not one per item:

```python
import plotly.graph_objects as go

source_colors = {
    "cron": "#AB63FA", "webui": "#00CC96", "subagent": "#FFA15A",
    "cli": "#19D3F3", "api_server": "#FF6692",
}

fig = go.Figure()

for src, grp in df.groupby("source"):
    # y_pos is a row-number for ordering; compute before grouping
    fig.add_trace(go.Scatter(
        x=grp["started_dt"],
        y=grp["y_pos"],
        mode="markers",
        marker=dict(
            size=grp["dur_min"].clip(2, 18),  # size = duration
            color=source_colors.get(src, "#636EFA"),
            line=dict(width=0.5, color="white"),
            symbol="square",
        ),
        name=src.title(),
        hovertemplate=(
            f"<b>{src}</b><br>"
            f"Model: %{{customdata[0]}}<br>"
            f"Duration: %{{customdata[1]:.0f}} min<br>"
            f"Messages: %{{customdata[2]}}<br>"
            f"Tokens: %{{customdata[3]:,}}<br>"
            f"Gap: %{{customdata[4]:.0f}} min<extra></extra>"
        ),
        customdata=grp[["model_short", "dur_min", "message_count",
                        "tokens", "gap_min"]].values,
        showlegend=True,
    ))

fig.update_layout(
    height=400,
    hovermode="closest",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(
        title="",
        rangeselector=dict(buttons=[
            dict(count=1, label="24h", step="hour", stepmode="backward"),
            dict(count=3, label="3d", step="day", stepmode="backward"),
            dict(count=7, label="7d", step="day", stepmode="todate"),
        ]),
    ),
    yaxis=dict(title="", showticklabels=False, showgrid=False),
    plot_bgcolor="rgba(0,0,0,0)",
)
```

Advantages:
- **Fast rendering** — one trace per category (e.g. 4 traces for 200 items instead of 200 traces)
- **Marker size encodes duration** — visual density at a glance
- **Color by source** — legend is readable and compact
- **`rangeselector`** lets user zoom 24h/3d/7d without re-querying

## Gantt from SQLite Sessions — ⚠️ DON'T Use go.Bar + pd.Timedelta in Streamlit

**Do NOT use this pattern in Streamlit:**

```python
# BROKEN with Streamlit's st.plotly_chart:
x=[pd.Timedelta(seconds=dur)]
```

**Why:** Plotly's `to_json` uses `orjson`, which cannot serialize `pd.Timedelta`. You get:
```
TypeError: Type is not JSON serializable: Timedelta
```
This also makes the figure construction itself hang (>60s) because orjson keeps retrying non-serializable types during `st.plotly_chart` serialization.

**If you must use `go.Bar` with `base`** (small datasets, <30 items), pass duration in **milliseconds** as a plain number:
```python
x=[dur * 1000],  # ms plain int/float — orjson-safe
```

**Better alternative for any dataset over 30 items:** use the scatter-marker timeline pattern above (one trace per category, sized markers).

**Best alternative for small hierarchical datasets:** `px.timeline` (see the main Gantt section above).
- Scale height to data: `max(300, min(1200, len(df) * 12))`

## Pitfalls (Cross-Domain)

### Pandas Mixed Timezones with Git Log Output

**Symptom:** `pd.to_datetime(df["timestamp"])` raises `ValueError: Mixed timezones detected`.

**Root cause:** Git's `%ai` format includes per-commit timezone offsets (e.g., `+1000`, `+0000`). A single repo may have commits from different timezones, producing a column with mixed-offset datetimes. Pandas `to_datetime` refuses mixed timezones by default.

**Fix:** Always pass `utc=True`:
```python
df["date"] = pd.to_datetime(df["timestamp"], utc=True).dt.date
```

This normalizes everything to UTC before comparison. Applies to any source producing mixed-offset timestamps (git log, API responses, distributed systems logs).

## Color Conventions (consistent across the app)

| Meaning | Color | Hex |
|---------|-------|-----|
| Completed/Removed | Green | `#2ecc71` |
| Active/In Progress | Blue | `#3498db` |
| Cancelled/Error | Red | `#e74c3c` |
| Unknown/Other | Grey | `#95a5a6` |

## Timeline X-Axis: Auto-Range Pitfall

**`px.timeline`'s auto-range does NOT reliably show all bars.** It clips bars at the edges, especially when data spans a wide range or has partial bars at the boundaries. Always compute explicit range from data:

```python
min_d = df["StartDate"].min()
max_d = df["EndDate"].max()
if pd.notna(min_d) and pd.notna(max_d) and max_d > min_d:
    pad = (max_d - min_d) * 0.03
    fig.update_xaxes(range=[min_d - pad, max_d + pad])
```

For long timelines, add a range slider for interactive zoom:
```python
fig.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.05)
```

Without explicit range, bars at the start/end of the dataset may be clipped or invisible.

## Data Validation Before Timeline Charts

Sanitize data before passing to `px.timeline`:

```python
df = df.dropna(subset=["StartDate", "EndDate"])
if df.empty: return None
df = df[df["StartDate"] <= df["EndDate"]]
if df.empty: return None
```

One bad row (NaT, reversed dates, SQL Server defaults) breaks the entire timeline.

## Controlling Legend Order

Use `category_orders` to control legend entry order:

```python
fig = px.timeline(..., category_orders={"Color": ["Completed", "Active", "Removed", "Cancelled"]})
```

Pairs with `color_discrete_map` for full control.

## Common Pitfalls

1. **Don't use `go.Bar` with `base` + `x` (duration) for Gantt** — it doesn't create a proper datetime x-axis. All bars appear to start at the same point. Use `px.timeline` instead.
2. **Don't forget `update_yaxes(autorange="reversed")`** — without it, your most recent items are at the bottom
3. **Don't pass datetime values to `x_start`/`x_end`** — pass column names as strings; `px.timeline` resolves them
4. **Scale height with data** — fixed height cuts off bars when data grows; use `max(400, len(df) * 28)`
5. **Match join keys correctly** — when joining Jobs (UUID `JobId`) with other tables, check whether the other table has `JobId` (UUID) or `JobNumber` (string). Don't compare UUID to string.
6. **Filter `0001-01-01` dates** — SQL Server's default datetime shows up as `0001-01-01+00:00` in Python. Always filter with `> '2000-01-01'` in SQL or `pd.Timestamp('2000-01-01', tz='UTC')` in Python.
7. **Legend deduplication** — use `color_discrete_map` with a small set of unique color values. Each unique value = one legend entry. Don't set `name` per-trace.
8. **Always set explicit x-axis range on px.timeline** — auto-range clips bars at edges. Compute min/max from data, add 3% padding, call `fig.update_xaxes(range=[...])`. See section above for the full pattern.
9. **Validate dates before plotting** — filter NaT, filter start > end, filter SQL Server defaults (0001-01-01). One bad row breaks the entire timeline. See "Data Validation" section above.
10. **Verify hierarchy cardinality before nesting in parent-child Gantt** — run a crosscheck query to see if child items actually fit inside parent windows. If most children span multiple parents (e.g., 96% of isolations applied before the job starts), DO NOT nest them. Use the Cross-Section Pattern instead. The query pattern in `references/gantt-sql-patterns.md` → "Relationship Crosscheck" shows how to measure this.
11. **Cross-section: filter by DB relationship, not just date overlap** — filter child items by their relationship column (e.g., `iso_df["JobNumber"] == job["JobNumber"]`), not just by date overlap. Date-overlap-only shows unrelated items that share the same calendar period. The DB relationship is the correct primary filter.
12. **LEFT JOIN nullable FK columns in child queries** — e.g., `RFIIsolations.EquipmentId` is nullable. `INNER JOIN Equipment` silently drops every isolation row where `EquipmentId` is NULL. Always check nullable FK constraints before writing joins.
13. **Module-level SQL strings don't invalidate st.cache_data** — when a `@st.cache_data` function references a module-level string constant, changing the string doesn't change the function bytecode hash. The cache key stays the same, so stale results persist after editing SQL. To force re-query: add a nonce/version parameter, or hard-refresh the browser (Ctrl+F5).
14. **CTE outer query cannot reference inner table aliases** — in a `WITH cte AS (SELECT ri.Col FROM ...) SELECT * FROM cte WHERE ri.Col = %(x)s`, the `ri.` prefix fails because `ri` only exists inside the CTE. The outer WHERE must use bare column names: `WHERE Col = %(x)s`. This catches everyone at least once — especially when parameterizing a WHERE clause appended to a CTE string.