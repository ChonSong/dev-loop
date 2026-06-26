# Streamlit Patterns for HMAS Sydney

## Duration Filter Checkbox Pattern

When a table has bad data (e.g. negative durations from clock skew), add a checkbox to filter it:

```python
filter_negative = st.checkbox("Filter out DurationMinutes < -1 (bad data)", value=True)
# ... after query ...
if filter_negative and "DurationMinutes" in df.columns:
    before = len(df)
    df = df[df["DurationMinutes"] >= -1]
    filtered = before - len(df)
    if filtered > 0:
        st.caption(f"⚠️ Filtered out {filtered} rows with DurationMinutes < -1")
```

## SQL Query Display Under Tables

Add a collapsible SQL display under every data table using a helper:

```python
def show_sql(sql, label="SQL Query"):
    with st.expander(f"📝 {label}", expanded=False):
        st.code(sql, language="sql")
```

Call it right after `st.dataframe()`:
```python
st.dataframe(df, use_container_width=True, height=500)
st.caption(f"{len(df):,} rows")
show_sql(sql, "Query Name")
```

For pages where SQL is embedded in a cached function, extract it as a module-level constant and reference from both the query function and the display.

## Error Boundary + Reconnect Button

Wrap the page router in try/except and add a sidebar reconnect button:

```python
# In sidebar
if st.sidebar.button("🔄 Reconnect DB"):
    st.cache_data.clear()
    st.rerun()

# Router with error boundary
try:
    pages[page](Filters)
except Exception as e:
    st.error(f"⚠️ Page error: {e}")
    st.info("Try clicking '🔄 Reconnect DB' in the sidebar.")
    if st.button("Clear Cache & Retry"):
        st.cache_data.clear()
        st.rerun()
```

## Connection Management: Fresh Per-Query Pattern

**Problem:** `@st.cache_resource` caches a single connection that dies after SQL Server timeout. All subsequent queries get `DBPROCESS is dead or not enabled`.

**Fix:** Open a fresh connection per query with retry logic:

```python
def _new_connection():
    for attempt in range(3):
        try:
            conn = pymssql.connect(**DB_CONFIG)
            conn.autocommit(True)
            return conn
        except pymssql.OperationalError:
            if attempt < 2:
                import time
                time.sleep(2)
    return None

@st.cache_data(ttl=60, show_spinner=False)
def query(sql, params=None):
    conn = _new_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params) if params else cur.execute(sql)
        return cur.fetchmany(50000)
    except pymssql.OperationalError:
        conn2 = _new_connection()
        if conn2 is None:
            return []
        cur = conn2.cursor(as_dict=True)
        cur.execute(sql, params) if params else cur.execute(sql)
        return cur.fetchmany(50000)
    except Exception as e:
        st.error(f"Query error: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass
```

## Pandas `describe()` Does Not Include `sum`

`df['col'].describe()` returns: `count, mean, std, min, 25%, 50%, 75%, max`. There is **no `sum`** key.

```python
# WRONG: KeyError
s = df["DurationMinutes"].describe()
st.metric("Total Hours", f"{s['sum'] / 60:,.0f}")

# CORRECT:
st.metric("Total Hours", f"{df['DurationMinutes'].sum() / 60:,.0f}")
```

## Multi-Pass Cached Functions

When a downstream cached function calls an upstream cached function, both may re-run the query.

**Fix:** Make the downstream function accept an optional DataFrame:

```python
def get_prediction_dataset(df=None):
    if df is None:
        df = get_job_timeframe_data()
    # ... filter ...

# In page:
training = get_prediction_dataset(df)  # reuse loaded df
```

## Function Body Leak During Patches

When using `patch` to edit a function near a function boundary, the replacement can absorb lines from the next function:

```python
# BROKEN — fmt_duration body merged into show_sql:
def show_sql(sql, label="SQL Query"):
    with st.expander(f"📝 {label}", expanded=False):
        st.code(sql, language="sql")
    if pd.isna(minutes): return "-"  # <-- leaked from fmt_duration!
```

**Prevention:** After every `patch`, run `ast.parse()` to verify syntax. Include the next `def` line in `old_string` for clean cuts.

## `with st.expander` Indentation Pitfall

`elif` must be at the **same indentation level** as `if`, not nested inside a `with` block:

```python
# BROKEN:
if sub_tab == "Overview":
    with st.expander("SQL"):
        st.code(sql)
    elif sub_tab == "Analysis":  # SYNTAX ERROR: elif inside with
        pass

# CORRECT:
if sub_tab == "Overview":
    with st.expander("SQL"):
        st.code(sql)
elif sub_tab == "Analysis":  # OK: same level as if
    pass
```

**Rule:** Always close `with` blocks before `elif`/`else` at the same level.

## Stubbing an Overloaded Page

When a page has too many heavy queries and overloads the system, replace it with a stub:

```python
def page_analysis(flt):
    st.title("📈 Analysis & Sankey Diagrams")
    st.warning("⚠️ This page is currently under development and has been disabled to prevent system overload.")
    st.markdown("""
    ### Planned Features
    **Sankey Diagrams** — RFI State Flow, Lock Chain, Vendor→Equipment
    **Pre-built Reports** — Isolation Point Frequency, Worker Lock Activity, etc.
    These features will be re-enabled once query performance is optimized.
    """)
```

After stubbing, remove unused functions that were only referenced by the stubbed page. Use `grep -n "def "` and cross-reference with call sites to find dead code.
