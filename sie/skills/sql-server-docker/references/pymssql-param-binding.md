# pymssql Parameter Binding

## The Core Rule

When using `as_dict=True` cursors, use `%(name)s` format — NOT `@name` format.

```python
# WRONG — errors with "Must declare scalar variable '@name'":
cur = conn.cursor(as_dict=True)
cur.execute("SELECT * FROM Users WHERE Name = @name", {"name": "Bob"})

# RIGHT:
cur.execute("SELECT * FROM Users WHERE Name = %(name)s", {"name": "Bob"})
```

`@name` is T-SQL variable declaration syntax. pymssql's dict cursor only understands Python `%`-style formatting. The `@name` form works with positional cursors but NOT with dict cursors.

## Dynamic WHERE Clause Pattern

Build conditions dynamically and pass parameters as a dict:

```python
def get_users(company=None, department=None, active_only=True):
    conditions = []
    params = {}
    
    if company:
        conditions.append("c.Name LIKE %(company)s")
        params["company"] = f"%{company}%"
    if department:
        conditions.append("u.DepartmentId = %(dept)s")
        params["dept"] = department
    if active_only:
        conditions.append("u.DeletedDate IS NULL")
    
    where = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
    SELECT u.FirstName, u.LastName, c.Name AS Company
    FROM Users u
    LEFT JOIN Companies c ON u.CompanyId = c.Id
    WHERE {where}
    ORDER BY u.LastName
    """
    
    cur.execute(sql, params)
    return cur.fetchall()
```

## Reserved Words to Avoid as Parameter Names

These T-SQL reserved words cause silent failures or confusing errors when used as pymssql parameter names:

| Bad Name | Good Name |
|----------|-----------|
| `%(from)s` | `%(dfrom)s` or `%(date_from)s` |
| `%(to)s` | `%(dto)s` or `%(date_to)s` |
| `%(state)s` | `%(rfi_state)s` |
| `%(order)s` | `%(sort_order)s` |
| `%(group)s` | `%(group_name)s` |

## IN Clause with Tuple Parameters

For `WHERE col IN (...)` with a variable number of values:

```python
# Python tuple works directly:
cur.execute(
    "SELECT * FROM RFILogs WHERE RFILogType IN %(types)s",
    {"types": (1, 2, 4, 5)}
)
```

## Debugging Empty Results

When a parameterized query returns 0 rows unexpectedly:

1. Verify the parameter name matches exactly (case-sensitive in the dict key)
2. Check for reserved word conflicts in parameter names
3. Test with literal values first to confirm the query logic is correct
4. Compare date format expectations — pymssql passes strings directly, SQL Server does implicit conversion from ISO format to datetime

## Connection Module Template

The minimal reliable connection layer for a data app:

```python
import pymssql
import streamlit as st

@st.cache_resource(ttl=300)
def get_connection():
    return pymssql.connect(
        server="172.17.0.1", port=1433,
        user="SA", password="...",
        database="DatabaseName",
        timeout=30, login_timeout=10,
    )

def query_df(sql, params=None, max_rows=50000):
    import pandas as pd
    conn = get_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params)
        rows = cur.fetchmany(max_rows)
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()
```
