---
name: test-data-generation
description: "Generate realistic test/fixture data for database schemas — Prisma/ORM-to-SQL conversion, schema-aware seeding with NOT NULL auto-fill, FK-aware insertion with captured reference IDs."
version: 1.0.0
author: Hermes Agent (curated)
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [database, seeding, fixtures, test-data, prisma, sqlite, orm]
    related_skills: []
---

# Test Data Generation

Generate realistic seed/fixture data for complex database schemas, especially when converting from ORM schemas (Prisma, TypeORM, etc.) to a runnable local database.

## Core Pattern

### 1. Schema Conversion (ORM → SQLite SQL)

When the target database engine differs from the ORM's source, convert rather than replicate.

**Key steps:**
1. Parse the ORM schema file to extract model definitions
2. Map ORM types to SQLite types (`String→TEXT`, `Int→INTEGER`, `Float→REAL`, `Boolean→INTEGER`, `DateTime→TEXT`, `Bytes→BLOB`)
3. **Exclude relation fields** — ORMs often embed virtual relation references (camelCase fields referencing other models with `@relation`). These are not real columns. Detect them by checking if the field type is another model name OR the field has an `@relation` attribute.
4. Handle `@id` (primary key), `@default(uuid())` (UUID default), `@@id([A, B])` (composite PK), and `@@map("TableName")` (actual table name)
5. Handle `?` suffix for nullable columns in Prisma

**Common pitfalls:**
- ORM model names are often PascalCase but the `@@map` directive gives the real table name — use that
- `@db.Uuid` in Prisma is just a TEXT column in SQLite — no special type needed
- Relation fields (e.g., `groups Groups? @relation(fields: [GroupVesselId], ...)`) must be excluded — they have no database column representation

### 2. Schema-Aware Seeding

Use `PRAGMA table_info` to dynamically discover column structure at runtime:

```python
_cache = {}
def table_columns(table):
    if table not in _cache:
        cur.execute(f'PRAGMA table_info("{table}")')
        _cache[table] = {row[1] for row in cur.fetchall()}
    return _cache[table]
```

**NOT NULL auto-fill:** Prisma schemas often leave audit columns NOT NULL without defaults. Seed scripts MUST fill these or inserts fail silently.

Detect NOT NULL columns (excluding PKs and already-auto-filled ones) and fill type-appropriate defaults:

```python
def not_null_cols(table):
    cur.execute(f'PRAGMA table_info("{table}")')
    for row in cur.fetchall():
        name, typ, not_null, is_pk = row[1], row[2], row[3], row[5]
        if not_null and not is_pk and name not in AUTO_FILLED_COLS:
            yield name, typ

# Auto-fill rules:
if nn_type == 'INTEGER':  vals[nn_col] = 0
if nn_type == 'REAL':     vals[nn_col] = 0.0
if nn_type == 'BLOB':     vals[nn_col] = b''
else:                     vals[nn_col] = ''  # TEXT
```

**Quote column names with double-quotes** — many ORM schemas use SQL reserved words as column names (`Index`, `Order`, `Group`, etc.). Always emit `INSERT INTO "table" ("col1", "col2")` with quoted columns.

### 3. FK-Aware Insertion

For schemas with foreign key constraints, you MUST capture inserted IDs and reuse them:

```python
# Step 1: Seed reference tables and capture IDs
depts = {name: smart_insert('Departments', Name=name)
         for name in ['Ops', 'Maint', 'Safety']}

# Step 2: Use captured IDs in dependent tables
smart_insert('Users', Name='Alice', DepartmentId=depts['Ops'])

# Step 3: For M:N bridges, sample from captured ID sets
for entity in random.sample(entity_ids, n):
    smart_insert('BridgeTable', EntityId=entity, ...)
```

### 4. INSERT OR IGNORE + Error Handling

- Use `INSERT OR IGNORE` to skip duplicate-safe inserts
- Wrap in try/except with logging to catch schema mismatches
- Always commit at the end, not per-row (performance)

## Seed Script Structure

A seed script should follow this order:

```
1. Connect to database
2. Create schema if empty (executescript)
3. Seed reference tables (static dimensions) → capture IDs
4. Seed hierarchy (Groups → Systems → Areas → Equipment → Points) → capture IDs
5. Seed transaction tables (Users, RFIs, Jobs) → capture IDs
6. Seed bridge tables (RFIJobs, RFIIsolations, RFILocks)
7. Seed audit/log tables (RFILogs, EventLogs, AuditChecks)
8. Commit
```

## Verification Checklist

- [ ] All seeded tables have >0 rows
- [ ] Dashboard/N+1 queries return non-empty results
- [ ] No SQL errors during insert (check for reserved words as column names)
- [ ] FK reference chains are complete (parent rows exist before child inserts)
- [ ] Database file is non-zero size

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| NOT NULL column missed | `INSERT OR IGNORE` silently inserts 0 rows | Use PRAGMA to discover all NOT NULL cols and auto-fill. **Debug first:** temporarily use `INSERT INTO` (without `OR IGNORE`) to surface constraint errors, then add it back |
| Reserved word as column name | `near "Index": syntax error` | Always double-quote column names in INSERT. Common culprits: `Index`, `Order`, `Group`, `State`, `Key`, `Value` |
| Relation fields treated as columns | Extra meaningless columns in SQLite | Filter out fields whose type name matches another model AND has no `@` attributes |
| Missing FK reference | `FOREIGN KEY constraint failed` | Seed parent tables first, capture IDs in dict |
| Cursor isolation after executescript | `PRAGMA` returns empty | `executescript()` may commit and leave the cursor in a new state — reconnect or use a fresh connection for seeding |
| Schema scale (>400 NOT NULL columns) | Seed script grows complex fast with many required FKs | Auto-fill via PRAGMA is essential — don't try to manually enumerate all NOT NULL columns. Seeding 50+ entity rows with 5+ FK refs each will expose gaps quickly; verify with app queries after each seeding pass |

## Support Files

- **`references/prisma-to-sqlite.md`** — Complete Python script + technique for converting Prisma schema to SQLite DDL, including relation field filtering, type mapping, and composite PK handling.
- **`references/schema-aware-seeding.md`** — The `smart_insert()` pattern with PRAGMA-based column discovery, NOT NULL auto-fill, FK-aware insertion, and dashboard verification.
- **`references/production-scale-seed.md`** — Real-world example: seeding a 103-table HMAS database with 400+ NOT NULL columns, including seed order, FK insertion pattern, debug trap, and dashboard verification checklist.
- **`templates/seed-script-template.py`** — Ready-to-customize seed script skeleton with schema creation, smart_insert, and the reference→entity→bridge→log seeding order.
