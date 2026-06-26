# Streamlit App Debugging — Patterns & Case Studies

## Session: OneTag HMAS Sydney DB Explorer (June 2026)

### Pattern: "Not connected to any MS SQL server" / "DBPROCESS is dead"

**Symptom:** Streamlit pages show `Query error: Not connected to any MS SQL server` or `(20047, b'DBPROCESS is dead or not enabled')`.

**Root Cause:** `@st.cache_resource(ttl=300)` caches a single `pymssql` connection. After 5 min idle, SQL Server closes it. All subsequent queries fail.

**Fix:** Replace cached connection with fresh-per-query pattern:
```python
def _new_connection():
    for attempt in range(3):
        try:
            conn = pymssql.connect(**DB_CONFIG)
            conn.autocommit(True)
            return conn
        except pymssql.OperationalError:
            if attempt < 2:
                import time; time.sleep(2)
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
    finally:
        try: conn.close()
        except: pass
```

**Also add a "Reconnect DB" sidebar button:**
```python
if st.sidebar.button("🔄 Reconnect DB"):
    st.cache_data.clear()
    st.rerun()
```

---

### Pattern: Adaptive Server Connection Timeout on Heavy Queries

**Symptom:** `(20047, b'DB-Lib error message 20003, severity 6: Adaptive Server connection timed out')`.

**Root Cause:** Multi-table JOINs with CTEs exceed SQL Server timeout.

**Fix:** Simplify — drop non-critical JOINs, use `LEFT JOIN` for optional relations, remove CTEs computable in Python.

---

### Pattern: `KeyError: 'sum'` from `DataFrame.describe()`

**Root Cause:** `describe()` returns count, mean, std, min, 25%, 50%, 75%, max — **no `sum`**.

**Fix:** Use `df['col'].sum()` directly.

---

### Pattern: `SELECT DISTINCT TOP N` Syntax Error (MS SQL Server)

**Fix:** Use `SELECT DISTINCT TOP 10 ...` not `SELECT TOP 10 DISTINCT ...`.

---

### Pattern: `use_container_width` Deprecation in `st.plotly_chart()`

**Fix:** Replace with `width='stretch'`. Note: `st.dataframe(use_container_width=True)` is NOT deprecated.

---

### Pattern: Streamlit Log Shows Errors from Wrong Instance

**Root Cause:** Multiple instances — host (Python 3.13) and container (Python 3.12). Check which process is actually serving.

---

### General Streamlit Debugging Workflow

1. Check log file first: `cat streamlit.log | tail -40`
2. Test each page's SQL queries individually against the DB
3. Use `execute_code` with `pymssql` to test in container's env
4. Check for stale processes on different ports
5. Add error boundaries around the page router
6. Add "Reconnect DB" sidebar button
