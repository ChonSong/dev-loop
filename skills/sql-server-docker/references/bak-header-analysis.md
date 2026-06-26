# Backup Header Analysis — SQL Server .bak Reconnaissance

Extract database identity, schema structure, and table inventory from a `.bak` file without needing SQL Server. Works on any SQL Server backup format (SQL 2005 through 2022).

## TAPE Header

Every SQL Server `.bak` file starts with a 512-byte TAPE header:

| Offset | Size | Field | Meaning |
|--------|------|-------|---------|
| 0 | 4 | Signature | `b'TAPE'` — validates this is a SQL Server backup |
| 4 | 2 | Version | Minor format version |
| 8 | 4 | MediaFamilyId | Backup set identifier |
| 28 | 4 | BackupSetId | Sequential backup set number |

## UTF-16LE String Extraction

Database identity metadata is stored as UTF-16LE encoded strings in the first 1-5 MB of the file. Scan with:

```python
import re

with open('file.bak', 'rb') as f:
    data = f.read(5 * 1024 * 1024)  # 5 MB is usually sufficient

# Find UTF-16LE strings (any 3+ printable ASCII characters)
pattern = re.compile(b'(?:[\\x21-\\x7e]\\x00){3,}')
matches = pattern.findall(data)

strings = set()
for m in matches:
    try:
        decoded = m.decode('utf-16-le').strip()
        if len(decoded) >= 4:
            strings.add(decoded)
    except:
        pass
```

### What the strings reveal

| Information | Example | Location |
|-------------|---------|----------|
| **Database name** | `OneTag_Sydney` | First few MB |
| **Server name** | `BC-DIRELAND-MB\\MSSQLSERVER2019` | Near DB name |
| **Backup type** | `Full Database Backup` | Backup header |
| **Data file path** | `C:\\...\\OneTag_Sydney.mdf` | File list metadata |
| **Log file path** | `C:\\...\\OneTag_Sydney_log.ldf` | File list metadata |
| **Admin user** | `AzureAD\\DarrenIreland` | Backup user identity |
| **Table names** | `Users`, `Systems`, `RFIs`, etc. | Schema dump in backup |
| **Column check constraints** | Patterns like `tDF__Users__AccountLo` | Default constraint names |
| **Foreign key names** | `FK_Users_Departments_DepartmentId` | FK definitions |
| **Migration history** | Version numbers, timestamps | EF Core MigrationId values |

## Table Inventory Extraction

Table names appear as UTF-16LE strings throughout the backup. Filter systematically:

```python
# Extract all strings then filter for table-like names
table_keywords = ['table', 'index', 'column', 'pk_', 'fk_', 'ix_']
tables = set()
for s in strings:
    s_lower = s.lower()
    if s_lower.startswith('dbo.') or any(kw in s_lower for kw in table_keywords):
        # Strip prefix/suffix markers like leading numbers or & characters
        clean = s.strip('0123456789&$()*+,.-/:;<=>?@[]^`{|}~')
        if clean and not clean.startswith('Microsoft') and 'schema' not in clean:
            tables.add(clean)
```

More reliably, look for **collation strings** in the file header and scan for patterns like `PK_Tablename` (primary key constraint names) which always include the table name.

## Domain Classification from Table Names

Once you have a table list, group by domain area using naming patterns:

| Domain prefix | Example tables | System type |
|--------------|----------------|-------------|
| `IsolationPoint*` | IsolationPoints, IsolationPointChecks, IsolationPointLogs | LOTO / Safety |
| `RFI*` | RFIs, RFIJobs, RFIIsolations, RFILocks | Request For Isolation |
| `PadLock*`, `Lockout*` | PadLocks, PadLockTypes, LockoutDevices | Physical lock hardware |
| `Audit*`, `CheckList*` | Audits, AuditChecks, CheckListTemplates | Safety inspections |
| `SwMA*` | SwMAs, SwMATemplates, SwMAChecks | Safe Work Method Assessment |
| `WorkPermit*`, `Job*` | WorkPermits, Jobs, JobLogs | Work authorization |
| `BoundaryTemplate*` | BoundaryTemplates, BoundaryTemplateItems | Isolation boundary defs |
| `User*`, `Role*`, `Permission*` | Users, UserLogins, UserRoles, Permissions | Access control |
| `Asset*`, `Equipment*` | Assets, Equipment, AssetLogs | Asset registry |
| `Message*` | Messages, MessageTemplates | Communication |
| `System*`, `Area*`, `Department*` | Systems, Areas, Departments | Core hierarchy |

## Table Relationships from Constraints

Backup files contain constraint definitions that reveal foreign key relationships. Look for patterns like:

- `FK_Users_Departments_DepartmentId` — Users belongs to Departments
- `FK_RFIIsolations_RFIs_RFIId` — RFIIsolations depends on RFIs
- `IX_Systems_ParentId` — Systems has a self-referencing parent hierarchy

Scan for all strings containing `FK_` to build the relationship graph:

```python
foreign_keys = [s for s in strings if 'FK_' in s]
for fk in foreign_keys:
    parts = fk.split('_')
    if len(parts) >= 3:
        child_table = parts[1]
        parent_table = parts[2]
```

## Best Practices

1. **Always scan the first 1 MB first** — this is usually enough for DB identity
2. **Scan up to 10 MB for table inventory** — table metadata can be deeper in the backup
3. **Cross-reference with `RESTORE HEADERONLY`** once SQL Server is available for backup metadata
4. **Pre-export table list** speeds up the SQL Server restore by letting you plan which tables to export first
5. **Strings are unordered** — relationship inference requires name pattern matching and later verification against `INFORMATION_SCHEMA`
