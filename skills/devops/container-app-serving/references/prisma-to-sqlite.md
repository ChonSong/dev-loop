# Prisma Schema → SQLite Conversion

When you have a Prisma schema (designed for SQL Server/PostgreSQL) but need a SQLite database, use this two-step approach.

## Step 1: Parse Prisma to SQLite DDL

Key translation rules:
- `String` → `TEXT`, `Int` → `INTEGER`, `Float` → `REAL`, `Boolean` → `INTEGER`, `DateTime` → `TEXT`, `BigInt` → `INTEGER`, `Bytes` → `BLOB`
- `@id` → `PRIMARY KEY` (unless composite)
- `@default(uuid())` → `DEFAULT (lower(hex(randomblob(16))))`
- `@map("TableName")` → use the mapped name as the actual table name
- `@@id([A, B])` → composite `PRIMARY KEY (A, B)`
- `?` after type → `NULL`, otherwise → `NOT NULL`
- `@db.Uuid` → just `TEXT` (ignore the db-specific annotation)

**CRITICAL: Filter out relation fields.** Prisma models have virtual fields that reference other models (e.g., `groups Groups? @relation(fields: [GroupId], references: [Id])`). These are NOT real database columns — they're Prisma-level relation navigators. Detect them by checking if the field's type matches another model name AND has no `@attribute` markers. Skip these entirely.

## Step 2: Schema-Aware Seeding

When the resulting SQLite schema has 100+ tables with 400+ NOT NULL columns, hand-writing seed INSERTs for every column is impractical. Use a **schema-aware** approach:

```python
def table_columns(table):
    """Return set of actual column names for a table via PRAGMA."""
    cur.execute(f'PRAGMA table_info("{table}")')
    return {row[1] for row in cur.fetchall()}

def smart_insert(table, **values):
    """Insert into table, auto-filling Id, CreatedDate, audit cols, 
    and ANY remaining NOT NULL columns with type-appropriate defaults."""
    cols = table_columns(table)
    vals = dict(values)

    # Auto-fill Id
    if 'Id' not in vals and 'Id' in cols:
        vals['Id'] = str(uuid.uuid4()).upper()
    # Auto-fill CreatedDate
    if 'CreatedDate' not in vals and 'CreatedDate' in cols:
        vals['CreatedDate'] = datetime.now().isoformat()
    # Auto-fill audit columns
    for ac in ['CreatedBy', 'ModifiedBy', 'DeletedBy']:
        if ac in cols and ac not in vals:
            vals[ac] = str(uuid.uuid4()).upper()
    # Auto-fill ALL remaining NOT NULL columns by type
    for nn_col, nn_type in not_null_cols(table).items():
        if nn_col not in vals:
            if nn_type == 'INTEGER': vals[nn_col] = 0
            elif nn_type == 'REAL':  vals[nn_col] = 0.0
            elif nn_type == 'BLOB':  vals[nn_col] = b''
            else:                    vals[nn_col] = ''

    # Filter to only existing columns
    valid = {k: v for k, v in vals.items() if k in cols}

    # Build quoted column names to handle SQL reserved words (e.g., "Index")
    quoted = [f'"{c}"' for c in valid.keys()]
    placeholders = ', '.join(['?' for _ in valid])
    stmt = f'INSERT OR IGNORE INTO "{table}" ({", ".join(quoted)}) VALUES ({placeholders})'
    cur.execute(stmt, list(valid.values()))
```

## Key Pitfalls

- **Relation fields**: The most common mistake — Prisma's virtual relation fields (e.g., `groups Groups?`) are NOT database columns. Filter them out during DDL generation.
- **Reserved words**: `Index` is a reserved word in SQLite. Always double-quote column names in INSERT statements: `INSERT INTO "Table" ("Index") VALUES (?)`.
- **NOT NULL cascade**: In Prisma-to-SQLite conversion, columns that had defaults in SQL Server (like `CreatedBy`, `Permissions`) become NOT NULL without defaults. The schema-aware seed script must detect and fill these.
- **Composite PKs**: Prisma `@@id([A, B])` → SQLite `PRIMARY KEY (A, B)`. The individual columns are NOT marked as PK in PRAGMA.
- **INSERT OR IGNORE**: Use this for reference data seeding. It silently skips duplicates instead of erroring.
