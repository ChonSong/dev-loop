# Production-Scale Seeding Example — OneTag HMAS

This reference documents the seed script built for the OneTag HMAS database (103 tables, 400+ NOT NULL columns) as a concrete example of the schema-aware seeding pattern.

## Scale

| Metric | Value |
|--------|-------|
| Tables | 103 |
| NOT NULL columns without defaults | 431 |
| Reference tables seeded | 15+ |
| Entity rows (RFIs, Jobs, Users) | 50 + 40 + 12 |
| Bridge/link rows | 250+ |
| Log entries | 750+ |
| Database size | 1.4 MB |

## Seed Order (Critical Path)

The exact order matters for FK integrity:

1. **Reference tables** (static dimensions) — GroupTypes, SystemTypes, SystemCategories, AreaTypes, Departments, UserRoles, IsolationPointTypes, WorkPermitTypes, ReasonCodes, LockoutDeviceTypes, Permissions
2. **Hierarchy** — Groups → Systems → Areas → Equipment → IsolationPoints (+ link table)
3. **Companies**
4. **Users** (+ UserLogins)
5. **RFIs** (50)
6. **Jobs** (40)
7. **Bridge tables** — RFIJobs, RFIIsolations, RFILocks, RFILocksRFIJobs
8. **Log tables** — RFILogs, IsolationPointLogs
9. **Secondary entities** — WorkPermits, Audits, AuditChecks, TemporaryTags
10. **System audit trail** — EventLogs

## FK-Aware Insertion Pattern

```python
# Step 1: Capture reference IDs
depts = {name: smart_insert('Departments', Id=uid(), Name=name, Description=desc)
         for name, desc in [('Operations','Ops'),('Maintenance','Maint')]}

# Step 2: Use them in next level
for name in ['Entity A', 'Entity B']:
    smart_insert('Systems', Id=uid(), Name=name,
                 DepartmentId=depts['Operations'])  # ← captured ref

# Step 3: Use at transaction level
smart_insert('RFIs', Id=rid,
             RFINumber=f'RFI-{n:04d}',
             GroupId=random.choice(list(groups.values())),  # ← captured ref
             DeveloperUserId=random.choice(list(user_ids.values())))  # ← captured ref
```

## The `INSERT OR IGNORE` Debug Trap

During development, `INSERT OR IGNORE` will silently fail on NOT NULL constraint violations. The debug pattern:

**Phase 1 — Schema discovery:** Run `INSERT INTO` (without `OR IGNORE`) on a single row to discover all constraint violations:

```sql
INSERT INTO "UserRoles" ("Id","Name","RoleLevel","ReadOnly") VALUES ('test','Test',1,0);
-- Error: NOT NULL constraint failed: UserRoles.Permissions
```

**Phase 2 — Auto-fill:** Add the missing column to the `not_null_cols()` auto-fill rules or to the explicit insert.

**Phase 3 — Production:** Add `OR IGNORE` back once all constraints are handled.

## Dashboard Verification

Run the actual SQL queries used by the dashboard/application to validate data:

```python
checks = [
    ('RFIs', 'SELECT COUNT(*) FROM RFIs WHERE DeletedDate IS NULL AND RFIState > 1 AND RFIState <= 11'),
    ('IsolationPoints', 'SELECT COUNT(*) FROM IsolationPoints WHERE DeletedDate IS NULL'),
    ('Jobs', 'SELECT COUNT(*) FROM Jobs WHERE DeletedDate IS NULL'),
    ('Users', 'SELECT COUNT(*) FROM Users WHERE DeletedDate IS NULL AND AccountLocked = 0'),
]
for name, query in checks:
    result = conn.execute(query).fetchone()[0]
    print(f'  {name}: {result}', '✅' if result > 0 else '❌')
```

## Full Working Script

The complete seed script is at `/workspace/forrest-plan-and-track/scripts/seed_data.py` (20KB, 200+ lines). It demonstrates:

- Schema creation on first run
- Schema-aware helpers (`col_cache`, `null_cache`, `smart_insert`)  
- 15+ reference tables with captured IDs
- FK-aware entity insertion at 3 hierarchy levels
- Bridge table seeding with random sampling
- Log/event table bulk inserts
- Dashboard query validation

## Key Quote Column Names

These columns in the OneTag schema are SQLite reserved words and require quoting:

| Column | Table | Issue |
|--------|-------|-------|
| `Index` | RFIIsolations, StandardActivityItems, SwMAChecks, etc. | Reserved word for index creation |
| `Order` | IsolationPointChecks | Reserved word for ORDER BY |
| `Group` | Multiple | Reserved word for GROUP BY |
| `Key` | Permissions | Reserved word for PRIMARY KEY |
| `State` | Multiple | Reserved word |
| `Value` | Multiple | Reserved word |
