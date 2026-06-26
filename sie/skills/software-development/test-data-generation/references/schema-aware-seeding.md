# Schema-Aware Seeding Technique

Pattern for inserting test data into tables with unknown or dynamic column structures — using PRAGMA table_info to discover columns at runtime.

## Core Insert Function

```python
_cache = {}
_null_cache = {}

def table_columns(table):
    """Return set of column names for a table (cached)."""
    if table not in _cache:
        cur.execute(f'PRAGMA table_info("{table}")')
        _cache[table] = {row[1] for row in cur.fetchall()}
    return _cache[table]

def not_null_cols(table):
    """Return dict of NOT NULL column -> type, excluding PKs and auto-filled cols."""
    if table not in _null_cache:
        cur.execute(f'PRAGMA table_info("{table}")')
        result = {}
        for row in cur.fetchall():
            name, typ, not_null, is_pk = row[1], row[2], row[3], row[5]
            if not_null and not is_pk and name not in AUTO_FILLED:
                result[name] = typ
        _null_cache[table] = result
    return _null_cache[table]

def smart_insert(table, **values):
    """
    Insert into table, auto-filling:
    - Id (UUID if not provided)
    - CreatedDate (past date if not provided)
    - CreatedBy/ModifiedBy/DeletedBy (UUIDs if NOT NULL and not provided)
    - Any other NOT NULL column with a type-appropriate default
    """
    cols = table_columns(table)
    vals = dict(values)
    
    # Auto-fill common columns
    if 'Id' not in vals and 'Id' in cols:
        vals['Id'] = str(uuid.uuid4()).upper()
    if 'CreatedDate' not in vals and 'CreatedDate' in cols:
        vals['CreatedDate'] = iso_timestamp(days_ago=random.randint(1, 365))
    for ac in ['CreatedBy', 'ModifiedBy', 'DeletedBy']:
        if ac in cols and ac not in vals:
            vals[ac] = str(uuid.uuid4()).upper()
    
    # Auto-fill remaining NOT NULL cols
    for nn_col, nn_type in not_null_cols(table).items():
        if nn_col not in vals:
            if nn_type == 'INTEGER': vals[nn_col] = 0
            elif nn_type == 'REAL':  vals[nn_col] = 0.0
            elif nn_type == 'BLOB':  vals[nn_col] = b''
            else:                    vals[nn_col] = ''
    
    # Filter to existing columns only
    valid = {k: v for k, v in vals.items() if k in cols}
    if not valid:
        return None
    
    col_names = list(valid.keys())
    quoted = [f'"{c}"' for c in col_names]
    ph = ', '.join(['?' for _ in col_names])
    stmt = f'INSERT OR IGNORE INTO "{table}" ({", ".join(quoted)}) VALUES ({ph})'
    cur.execute(stmt, list(valid.values()))
    return vals.get('Id')
```

## Seeding with FK Awareness

```python
# Seed reference tables first, capture IDs
depts = {}
for name in ['Operations', 'Maintenance', 'Safety']:
    depts[name] = smart_insert('Departments', Name=name, Description=f'{name} dept')

# Use captured IDs in dependent tables
for name, role in [('Alice', 'Operator'), ('Bob', 'Supervisor')]:
    smart_insert('Users', 
        FirstName=name.split()[0],
        LastName=name.split()[1],
        UserName=name.lower(),
        DepartmentId=depts['Operations'],
        Position=role)
```

## Dashboard Query Verification

After seeding, run the actual queries the dashboard/application will use to verify data is meaningful:

```python
for q in [
    'SELECT COUNT(*) FROM RFIs',
    'SELECT COUNT(*) FROM Users WHERE AccountLocked = 0',
    # ... app-specific queries
]:
    result = conn.execute(q).fetchone()[0]
    assert result > 0, f"Empty result for: {q[:60]}"
```

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `INSERT OR IGNORE` won't complain about NOT NULL | 0 rows inserted silently | Use 'INSERT INTO' without OR IGNORE during debugging, or check rowcount |
| `executescript()` changes cursor state | PRAGMA returns stale results | Re-connect or use separate cursor for PRAGMA vs inserts |
| Real columns in the ORM `executescript()` changes cursor state PRAGMA returns stale results don't match assumptions | `sqlite3.OperationalError` | Always discover via PRAGMA, don't hardcode column lists |
| INT vs INTEGER vs REAL | Type mismatch for empty defaults | Match default type to PRAGMA-reported type |
| Column exists but wrong case | No error, silently skipped | SQLite column names are case-insensitive, but `in` checks are case-sensitive in Python |
