# SQL Server Docker Restoration — Full Reference

End-to-end restoration of a 2.45 GB SQL Server .bak file from Docker, extraction to SQLite, and browser UI.

## Container Setup

**Host OS:** EndeavourOS (Arch-based), Docker 29.1.3, 7.6 GB RAM, 4 CPUs

**Image:** `mcr.microsoft.com/mssql/server:2022-latest` (RTM-CU25-GDR, version 16.0.4260.1)

**Memory tuning:** SQL Server needs ~1.5 GB minimum. When host RAM is tight, use `-m 1.5g --memory-swap 3g` to allow swap overflow.

**Volume strategy (two mounts):**
- Data: `/home/sean/mssql-data` -> `/var/opt/mssql/data` (persistent)
- Backup: `/home/sean/mssql-backup` -> `/var/opt/mssql/backup` (read-only)

**Permissions:** The `mssql` user runs as UID 10001 inside the container. The data directory on the host must be writable by that UID (`chown 10001:10001`).

## SA Password Reset

The `MSSQL_SA_PASSWORD` env var **only applies during fresh initialization** of the system databases. If `master.mdf` already exists (from a previous failed start, or a container restart with persistent data), the old password is baked in and the env var is ignored.

**Symptoms:** `sqlcmd: Login failed for user 'SA'` despite correct password.

**Fix:**
1. `docker stop sqlserver && docker rm sqlserver`
2. `rm -f /home/sean/mssql-data/master.mdf /home/sean/mssql-data/mastlog.ldf`  (remove ONLY system DB files)
3. Keep your restored MDF/LDF files (e.g. `OneTag_Sydney.mdf`)
4. `docker run ...` (the SA password env var works on the fresh system DBs)
5. Wait for startup, then `CREATE DATABASE [Name] ON (FILENAME = ...) FOR ATTACH`

This avoids having to re-restore the multi-gigabyte backup.

## sqlcmd Flags Reference

| Flag | Purpose | Required? |
|------|---------|-----------|
| `-S localhost` | Server address | Yes |
| `-U SA` | User | Yes |
| `-P password` | Password | Yes |
| `-N` | Encrypt connection | Yes (SQL Server 2022 defaults to encrypted) |
| `-C` | Trust server certificate | Yes (self-signed Docker cert) |
| `-W` | Trim trailing whitespace | For CSV export |
| `-s ','` | Column separator | For CSV export |
| `-Q "query"` | Run and exit | Single-query mode only |
| `-i file.sql` | Run from file | Multi-batch mode (needed for `USE` + `GO`) |

**Critical quirk:** `-Q` exits after the first batch. `USE [DB]; GO; SELECT ...` requires `-i` or separate connections.

## Multi-Batch Export Pattern

When you need to `USE [Database]` before a `SELECT`, use the `-i` file approach:

```bash
cat > /tmp/export.sql << 'ENDSQL'
USE [DatabaseName];
GO
SELECT TOP 100 * FROM Users;
ENDSQL

# Copy to host, then to container
scp /tmp/export.sql root@172.17.0.1:/tmp/
ssh root@172.17.0.1 "docker cp /tmp/export.sql sqlserver:/tmp/"

# Execute
ssh root@172.17.0.1 "docker exec -u root sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P Password123! -N -C -W -s ',' -i /tmp/export.sql"
```

## CSV Export Format

sqlcmd with `-W -s ','` produces:

```
Column1,Column2
--------,--------
value1,value2
value3,value4

(2 rows affected)
```

**Parser recipe (Python):**
1. Split output on newlines
2. Skip any `Changed database context` lines
3. Line 0 = headers (split on comma, strip)
4. Line 1 = separator line (dashes) -- discard
5. Lines 2+ until a line matching `(N rows affected)` or end = data rows
6. Each data row: split on comma, zip with headers, produce dict

## Database Re-attachment After Container Recreate

If the container was recreated but the MDF/LDF files survive on the host mount:

```sql
CREATE DATABASE [DatabaseName]
ON (FILENAME = '/var/opt/mssql/data/DatabaseName.mdf'),
   (FILENAME = '/var/opt/mssql/data/DatabaseName_log.ldf')
FOR ATTACH;
```

The database must be in `ONLINE` state and `sys.databases` must show it before querying.

## Row Count Results (66 tables)

| Table | Rows | Notes |
|-------|------|-------|
| Messages | 1,584,643 | Skipped (too large for 100MB GitHub) |
| RFILogs | 123,698 | Event log |
| Resources | 62,830 | File attachments |
| Users | 3,884 | All anonymized (First####/Last####) |
| Systems | 2,067 | Asset systems |
| Areas | 561 | Location hierarchy |
| IsolationPoints | 10,025 | LOTO points |
| Jobs | 9,750 | Work orders |
| Total exported | 426,153 (66 tables) | 135.5 MB SQLite |

## Performance

**Restore:** 320,682 pages in ~34 seconds (73 MB/sec) on SSD. Includes version upgrade from 904 to 957 (53 steps, ~20 seconds).

**CSV export:** ~2-5 seconds per medium table (up to 100K rows). Large tables (Messages at 1.58M) should use `SELECT TOP N` to limit output.

## SQLite `_` Prefix Pitfall

When querying `sqlite_master` to list tables:

```sql
-- This returns 0 rows because _ is a single-char wildcard:
SELECT name FROM sqlite_master WHERE name NOT LIKE '_%'

-- Correct version with ESCAPE:
SELECT name FROM sqlite_master WHERE name NOT LIKE '\_%' ESCAPE '\'
```

The `_` wildcard in SQL LIKE matches any single character, so `NOT LIKE '_%'` excludes everything. Always escape with `ESCAPE '\'` when matching literal underscores.
