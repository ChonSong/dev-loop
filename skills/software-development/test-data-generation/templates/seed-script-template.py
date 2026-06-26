"""
Schema-Aware Database Seeder Template
Copy this as a starting point for seeding any ORM-sourced SQLite database.

Customize:
  1. DB_PATH → your database path
  2. SCHEMA_PATH → your schema SQL file path  
  3. The reference data dicts (departments, user_roles, types, etc.)
  4. MAIN_ENTITIES dicts with your domain data
  5. BRIDGE_TABLES to link entities

See references/schema-aware-seeding.md for the technique.
See references/prisma-to-sqlite.md for schema conversion.
"""

import sqlite3, os, uuid, random
from datetime import datetime, timedelta, timezone

DB_PATH = 'data/app.db'
SCHEMA_PATH = 'prisma/schema.sqlite.sql'

def uid():
    return str(uuid.uuid4()).upper()

def d(days=0, hours=0):
    return (datetime.now(timezone.utc) - timedelta(days=days, hours=hours)).isoformat()

random.seed(42)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Create schema if empty
cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
if cur.fetchone()[0] == 0:
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()

# ── Schema-Aware Helpers ────────────────────────────────────────────────

_col_cache = {}
_null_cache = {}

def table_columns(table):
    if table not in _col_cache:
        cur.execute(f'PRAGMA table_info("{table}")')
        _col_cache[table] = {row[1] for row in cur.fetchall()}
    return _col_cache[table]

def not_null_cols(table):
    if table not in _null_cache:
        cur.execute(f'PRAGMA table_info("{table}")')
        result = {}
        for row in cur.fetchall():
            name, typ, nn, pk = row[1], row[2], row[3], row[5]
            if nn and not pk and name not in ('Id','CreatedDate','CreatedBy','ModifiedBy','DeletedBy'):
                result[name] = typ
        _null_cache[table] = result
    return _null_cache[table]

def smart_insert(table, **values):
    cols = table_columns(table)
    vals = dict(values)
    
    if 'Id' not in vals and 'Id' in cols:
        vals['Id'] = uid()
    if 'CreatedDate' not in vals and 'CreatedDate' in cols:
        vals['CreatedDate'] = d(days=random.randint(1, 365))
    for ac in ['CreatedBy', 'ModifiedBy', 'DeletedBy']:
        if ac in cols and ac not in vals:
            vals[ac] = uid()
    
    for nn_col, nn_type in not_null_cols(table).items():
        if nn_col not in vals:
            if nn_type == 'INTEGER': vals[nn_col] = 0
            elif nn_type == 'REAL':  vals[nn_col] = 0.0
            elif nn_type == 'BLOB':  vals[nn_col] = b''
            else:                    vals[nn_col] = ''
    
    valid = {k: v for k, v in vals.items() if k in cols}
    if not valid:
        return None
    
    quoted = [f'"{c}"' for c in valid.keys()]
    stmt = f'INSERT OR IGNORE INTO "{table}" ({", ".join(quoted)}) VALUES ({", ".join(["?" for _ in valid])})'
    try:
        cur.execute(stmt, list(valid.values()))
        return vals.get('Id')
    except Exception as e:
        print(f'  ⚠️  {table}: {e}')
        return None

# ═══════════════════════════════════════════════════════════════════════
#  SEED DATA — Customize below
# ═══════════════════════════════════════════════════════════════════════

print('🌱 Seeding database...')

# 1. Reference tables (static dimensions) → capture IDs
ref_a = {name: smart_insert('ReferenceTableA', Name=name) 
         for name in ['Value1', 'Value2', 'Value3']}

# 2. Entity hierarchy → capture IDs
entities = {}
for name in ['Entity Alpha', 'Entity Beta']:
    entities[name] = smart_insert('EntityTable', Name=name, RefId=ref_a['Value1'])

# 3. Transaction tables → capture IDs
txns = []
for i in range(10):
    tid = smart_insert('TransactionTable', Name=f'TXN-{i:04d}')
    txns.append(tid)

# 4. Bridge tables (M:N)
for eid in random.sample(list(entities.values()), min(3, len(entities))):
    smart_insert('BridgeTable', EntityId=eid, TransactionId=random.choice(txns))

# 5. Log/audit tables
for tid in txns:
    for _ in range(random.randint(1, 5)):
        smart_insert('LogTable', TransactionId=tid, Event=f'Event {_}')

conn.commit()
conn.close()
print('✅ Seed complete!')
