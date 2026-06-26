# Prisma Schema → SQLite SQL Conversion

Full technique for converting a Prisma schema (`.prisma` file) into runnable SQLite CREATE TABLE statements.

## The Problem

Prisma schemas contain:
- Type annotations (`@db.Uuid`, `@db.VarChar`) that don't apply to SQLite
- Virtual relation fields (camelCase references to other models with `@relation`) that have no column representation
- Composite primary keys (`@@id([A, B])`)
- Table naming via `@@map("ActualName")`
- Complex field attributes (`@default(uuid())`, `@default(now())`)

These must all be handled to produce valid SQLite DDL.

## Python Conversion Script

```python
import re

with open('schema.prisma') as f:
    content = f.read()

# Remove Prisma comments
content = re.sub(r'//.*', '', content)

# Extract model names (for identifying relation fields)
model_names = set()
for m in re.finditer(r'model\s+(\w+)\s*{', content):
    model_names.add(m.group(1))

# Extract model blocks
models = {}
current_model = None
current_lines = []
for line in content.split('\n'):
    m = re.match(r'model\s+(\w+)\s*{', line)
    if m:
        current_model = m.group(1)
        current_lines = []
    elif current_model is not None:
        if line.strip() == '}':
            models[current_model] = current_lines
            current_model = None
        else:
            current_lines.append(line)

# Type map
type_map = {
    'String': 'TEXT', 'Int': 'INTEGER', 'Float': 'REAL',
    'Boolean': 'INTEGER', 'DateTime': 'TEXT', 'BigInt': 'INTEGER',
    'Decimal': 'REAL', 'Bytes': 'BLOB',
}

for model_name in models:
    lines = models[model_name]
    
    # Find table name
    table_name = model_name
    for line in lines:
        m = re.search(r'@@map\("([^"]+)"\)', line)
        if m:
            table_name = m.group(1)
            break
    
    # Find composite PK
    composite_pk = None
    for line in lines:
        m = re.search(r'@@id\(\[([^\]]+)\]\)', line)
        if m:
            composite_pk = [x.strip() for x in m.group(1).split(',')]
            break
    
    cols = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('@') or line.startswith('@@'):
            continue
        
        parts = line.split()
        if len(parts) < 2:
            continue
        
        col_name = parts[0]
        prisma_type_raw = parts[1]
        
        # Detect relation field: type is another model name AND no @attribute
        type_clean = prisma_type_raw.replace('?', '')
        has_at = any(p.startswith('@') for p in parts[2:])
        is_relation = (type_clean in model_names and not has_at) or \
                      any(p.startswith('@relation') for p in parts[2:])
        
        if is_relation:
            continue  # Skip — not a real column
        
        nullable = '?' in prisma_type_raw
        prisma_type_clean = prisma_type_raw.replace('?', '')
        sql_type = type_map.get(prisma_type_clean, 'TEXT')
        
        attributes = ' '.join(parts[2:])
        is_pk = '@id' in attributes
        has_default_uuid = '@default(uuid())' in attributes
        
        col_def = f'"{col_name}" {sql_type}'
        if is_pk and not composite_pk:
            col_def += ' PRIMARY KEY'
        if has_default_uuid:
            col_def += ' DEFAULT (lower(hex(randomblob(16))))'
        if nullable and not is_pk:
            col_def += ' NULL'
        elif not nullable and not is_pk:
            col_def += ' NOT NULL'
        
        cols.append(col_def)
    
    if not cols:
        continue
    
    sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n'
    sql += ',\n'.join(cols)
    if composite_pk:
        pk_cols = ', '.join(f'"{c}"' for c in composite_pk)
        sql += f',\nPRIMARY KEY ({pk_cols})'
    sql += '\n);'
```

## Key Decisions

| Decision | Reason |
|----------|--------|
| Use `CREATE TABLE IF NOT EXISTS` | Safe for re-runs — won't error if table exists |
| UUID default via `lower(hex(randomblob(16)))` | SQLite doesn't have native UUID; this produces a valid UUID-like hex string |
| Double-quote ALL column names | Prisma schemas frequently use SQL reserved words (`Index`, `Order`, `Group`, `State`, `Key`, `Value`) |
| Relation field detection via model name + absence of `@` | A field like `groups Groups? @relation(...)` has `Groups` as its type (another model) and `@relation` attribute — filter it out |
| Keep `NOT NULL` from Prisma | Prisma doesn't add `?` to required fields — preserve this so seeding catches missing values |

## What NOT to do

- **Don't try to create FK constraints in SQLite** — SQLite parses them but doesn't enforce them by default unless `PRAGMA foreign_keys = ON`. The ORM handles referential integrity.
- **Don't preserve `@db.Uuid`** — In SQLite, all UUIDs are just TEXT. The `@db.Uuid` annotation is SQL Server-specific.
- **Don't preserve relation field names** — They're virtual. The actual FK columns are the ones referenced in `@relation(fields: [ActualFkColumn])`.
