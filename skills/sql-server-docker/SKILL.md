---
name: sql-server-docker
description: Restore and query SQL Server .bak backup files using Docker or direct sqlcmd — for when you need to browse or export a SQL Server database backup. Covers Docker container setup, direct sqlcmd restore, backup restoration, data export to SQLite, container-to-host connectivity troubleshooting, and common pitfalls (memory, permissions, sqlcmd path, CSV parsing, SSH key location).
triggers:
  - SQL Server backup
  - .bak file
  - restore database
  - sqlserver docker
  - sqlcmd
  - export SQL Server to SQLite
  - browse SQL Server database
  - sql server connectivity
  - container cannot reach host
  - docker socket not available
  - network_mode host mismatch
---

# SQL Server in Docker — Restore & Query .bak Files

## Overview

Restore a SQL Server `.bak` backup file using the official `mcr.microsoft.com/mssql/server` Docker image, then query or export the data. Use this when you need to browse/extract data from a SQL Server backup without native SQL Server.

## Prerequisites

- Docker available on the host (check: `docker --version`)
- Sufficient disk space (backup file + 2× for MDF/LDF)
- At least 2GB free RAM for SQL Server container

## Real-World Example

See `references/onetag-hmas-profile.md` — a 2.45 GB HMAS safety management database (104 tables, 426K rows) was restored and is running as `sqlserver-onetag` on the host at port 1433.

## Step-by-Step

### 0. Inspect the backup header (optional, no restore needed)

SQL Server `.bak` files contain UTF-16LE metadata in their headers. Extract schema without restoring:

```python
import re
with open('backup.bak', 'rb') as f:
    data = f.read(5 * 1024 * 1024)
utf16 = re.compile(b'(?:[\\x21-\\x7e]\\x00){3,}')
for m in utf16.findall(data):
    try:
        s = m.decode('utf-16-le').strip()
        if len(s) >= 4: print(s)
    except: pass
```

This reveals database name, table names, column names, PKs, and relationships. See `references/bak-header-analysis.md` for the full scanning implementation including table name extraction from schema metadata.

### 1. Prepare the backup file

If the `.bak` filename has spaces, copy to a clean path first:

```bash
cp '/path/with spaces.bak' /data/backup.bak
```

### 2. Create data directory with correct ownership

SQL Server container runs as uid 10001 inside the container:

```bash
mkdir -p /data/mssql-data
chown 10001:10001 /data/mssql-data
```

**Common failure:** `Access is denied` on master.mdf means wrong ownership.

### 3. Start SQL Server container

```bash
docker run -d \
  --name sqlserver-restore \
  -e 'ACCEPT_EULA=Y' \
  -e 'MSSQL_SA_PASSWORD=YourStrongPassword!' \
  -e 'MSSQL_PID=Developer' \
  -p 1433:1433 \
  -v /data/backup.bak:/var/opt/mssql/backup/backup.bak:ro \
  -v /data/mssql-data:/var/opt/mssql/data \
  --memory 2.5g \
  --cpus 3 \
  mcr.microsoft.com/mssql/server:2022-latest
```

**Memory note:** SQL Server needs at least 1.5–2.5 GB. If the host is tight, use `--memory 1.5g --memory-swap 3g`. Check available RAM first: `free -h`.

**Wait for startup:** ~30–60 seconds. Check with `docker logs sqlserver-restore` — wait for "SQL Server is now ready for client connections."

### 4. Restore the backup

```bash
# Get file list
docker exec -u root sqlserver-restore /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'password' -N -C \
  -Q "RESTORE FILELISTONLY FROM DISK = N'/var/opt/mssql/backup/backup.bak'"

# Restore with MOVE — use a SQL file for proper batch execution
cat > /tmp/restore.sql << 'EOF'
USE [master];
GO
RESTORE DATABASE [MyDB]
FROM DISK = N'/var/opt/mssql/backup/backup.bak'
WITH
  MOVE N'DataFile' TO N'/var/opt/mssql/data/MyDB.mdf',
  MOVE N'LogFile' TO N'/var/opt/mssql/data/MyDB_log.ldf',
  REPLACE,
  STATS = 10;
EOF

scp /tmp/restore.sql host:/tmp/ && ssh host "docker cp /tmp/restore.sql sqlserver-restore:/tmp/restore.sql"
docker exec -u root sqlserver-restore /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'password' -N -C -i /tmp/restore.sql
```

**Important:** Run as `-u root` — the default `mssql` user lacks permissions.

### 5. Query data

sqlcmd is at `/opt/mssql-tools18/bin/sqlcmd` in the 2022 image (NOT `/opt/mssql-tools/bin/sqlcmd`).

**Gotcha:** `USE [db]; SELECT * FROM table` with `-Q` may not respect the database context. Use a SQL file with `GO` separator and `-i` flag instead.

### 6. Export to SQLite (for browsing)

Use sqlcmd CSV output with `-N -C -W -s ','` flags. **Critical parsing note:** sqlcmd CSV output has a separator line between headers and data:

```
ColumnName1,ColumnName2
------------,------------
value1,value2
```

Skip line 2 (the dashes) when parsing. Python parser:

```python
lines = [l.strip() for l in output.split('\n') if l.strip()]
headers = [h.strip() for h in lines[0].split(',')]
# lines[1] is separator — skip it
for line in lines[2:]:
    values = line.split(',')
    row = dict(zip(headers, [v.strip() for v in values]))
```

**Gotcha:** Table names from sqlcmd CSV may have surrounding single quotes. Strip them: `clean = name.strip("'")`

## Browsing the SQLite database

Prisma 7.8+ requires `prisma.config.ts` with SQLite adapter — complex setup for unknown schemas. For quick browsing, use the provided `scripts/sqlite_browser.py`:

```bash
python3 scripts/sqlite_browser.py /path/to/exported.db 8765
```

Serves the SQLite DB as a web UI with table list, pagination, search, and dark theme. See source for customization.

## Alternative: sqlcmd-Only Restore (No Docker)

When Docker is unavailable (no socket, no daemon) or SQL Server is already running on the network, use sqlcmd directly. This is the fallback when you can't run Docker inside the container.

```bash
# sqlcmd must be installed locally
sqlcmd --version  # v1.10+ recommended

# Then run the adapted restore script
chmod +x templates/restore-direct.sh
BACKUP_FILE=/path/to/backup.bak ONETAG_SQL_SA_PASSWORD='...' ./templates/restore-direct.sh
```

The template at `templates/restore-direct.sh` handles:
- Pre-flight SQL Server connectivity check (fails fast with troubleshooting tips)
- Disk space estimation (warns if < 3× backup size free)
- LFS pointer detection
- Heredoc-based restore T-SQL (handles `GO` batches cleanly)
- Configurable host/port via env vars (`DB_HOST`, `DB_PORT`)

See `references/sqlcmd-direct-restore.md` for full comparison vs Docker-based approach and when to use each.

## When SQL Server Cannot Be Reached

If sqlcmd can't connect (port 1433 closed), use the investigation pattern in `references/connectivity-troubleshooting.md`:

1. **Verify network topology** — `ip addr` + `/etc/hosts` to find container IP and host gateway
2. **Check SSH access** — `cat ~/.ssh/config` and `ssh host "echo connected"` to see if host management is possible
3. **Test SQL directly** — `bash -c 'echo > /dev/tcp/localhost/1433'` to check port
4. **Check Docker availability** — socket, CLI, or TCP API
5. **Ask user for access** — SSH key authorization or Docker socket mount

**Key insight: system prompt invariants lie.** The claim `network_mode: host` may be stale — always verify with `ip addr` and `/etc/hosts`. The container may be on a Docker bridge (e.g., `172.19.0.0/16`) with the host at the gateway IP (`172.19.0.1`).

## Windows .bak → Linux SQL Server (WITH MOVE)

SQL Server `.bak` files created on Windows have hardcoded Windows filesystem paths (e.g., `C:\Program Files\Microsoft SQL Server\...\*.mdf`). On Linux SQL Server, you **must** use `WITH MOVE` to relocate the data/log files.

### Discover logical file names first

```bash
sqlcmd -S host,port -U sa -P 'password' -C -d master \
  -Q "RESTORE FILELISTONLY FROM DISK = N'/path/to/backup.bak'"
```

Look for the `LogicalName` column — typically one for data (`.mdf`) and one for log (`.ldf`).

### Restore WITH MOVE

```sql
RESTORE DATABASE [MyDB]
FROM DISK = N'/var/opt/mssql/backup/backup.bak'
WITH
  MOVE N'LogicalDataName' TO N'/var/opt/mssql/data/MyDB.mdf',
  MOVE N'LogicalLogName' TO N'/var/opt/mssql/data/MyDB_log.ldf',
  REPLACE, RECOVERY, STATS = 5;
```

The data directory inside the container is `/var/opt/mssql/data/`. Ensure it exists: `mkdir -p /var/opt/mssql/data`.

## SA Password Stale After Container Recreate

**Root cause:** SQL Server writes the `SA` password hash to `master.mdf` on **first** startup of a fresh data directory. On subsequent container starts reusing the same volume, `MSSQL_SA_PASSWORD` env var is **ignored** — the stored hash is authoritative. Recreating the container with a different password env var will silently fail: the container starts, `docker inspect` shows the new env, but SA login still uses the old password.

### Fix A: Nuke System DBs + Reattach User DBs (Faster)

Use when you have user database files you want to keep but need a fresh SA password:

```bash
# 1. Stop/remove container
docker stop sqlserver-onetag && docker rm sqlserver-onetag

# 2. Remove ONLY system DB files (keep user MDF/LDF)
cd /host/path/mssql-data
find . -maxdepth 1 ! -name 'OneTag*' ! -name '.' -delete

# 3. Restart container — fresh system DBs get the NEW password
docker run -d \
  --name sqlserver-onetag \
  -e 'ACCEPT_EULA=Y' \
  -e 'MSSQL_SA_PASSWORD=NewPassword!' \
  -e 'MSSQL_PID=Developer' \
  -p 1433:1433 \
  -v /host/path/mssql-data:/var/opt/mssql/data \
  mcr.microsoft.com/mssql/server:2022-latest

# 4. Wait for ready, then ATTACH (not restore) user databases
cat > /tmp/attach.sql << 'ENDSQL'
CREATE DATABASE [UserDb]
ON (FILENAME = '/var/opt/mssql/data/UserDb.mdf'),
   (FILENAME = '/var/opt/mssql/data/UserDb_log.ldf')
FOR ATTACH;
GO
ENDSQL
docker cp /tmp/attach.sql sqlserver-onetag:/tmp/attach.sql
docker exec -u root sqlserver-onetag /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'NewPassword!' -N -C -i /tmp/attach.sql
```

Systems databases to remove: `master.mdf`, `mastlog.ldf`, `model.mdf`, `modellog.ldf`, `msdbdata.mdf`, `msdblog.ldf`, `tempdb.mdf`, `templog.ldf`, `Entropy.bin`. Keep user DB MDF/LDF files.

### Fix B: Single-User Mode Password Reset

Use when you CANNOT lose system databases (server-level configs, logins, jobs):

```bash
docker stop sqlserver-onetag
docker run -d --name sqlserver-reset \
  -v /host/path/mssql-data:/var/opt/mssql/data \
  -e "ACCEPT_EULA=Y" \
  mcr.microsoft.com/mssql/server:2022-latest \
  /opt/mssql/bin/sqlservr -m

for i in $(seq 1 30); do sleep 2; docker logs sqlserver-reset 2>&1 | grep -q "Server is listening on" && break; done

# Use the CURRENT password (the one stored in master.mdf)
docker exec sqlserver-reset /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "CurrentPassword!" -C \
  -Q 'ALTER LOGIN sa WITH PASSWORD = N"NewPassword!"; ALTER LOGIN sa ENABLE;'

docker stop sqlserver-reset && docker rm sqlserver-reset
docker start sqlserver-onetag
```

**Key insight:** Single-user mode still requires the old SA password — it authenticates against the same master.mdf. This changes it to a new value for subsequent normal starts.

## Copy Backup to SQL Server Container (Remote Pipeline)

When the `.bak` file lives in a different container than the SQL Server container (common with multi-container setups), use SSH to bridge:

```bash
# 1. Copy from local container to host
scp /workspace/backup.bak host:/tmp/onetag-backup.bak

# 2. Copy from host into SQL Server container
ssh host "docker cp /tmp/onetag-backup.bak sqlserver-onetag:/var/opt/mssql/backup.bak"

# 3. Clean up host temp
ssh host "rm /tmp/onetag-backup.bak"

# 4. Now restore FROM DISK pointing at the container-internal path
ssh host "docker exec sqlserver-onetag /opt/mssql-tools18/bin/sqlcmd ..."
```

See `references/windows-bak-to-linux.md` for a worked example with the full pipeline.

## Interactive Streamlit Explorers

After exporting to SQLite, two Streamlit exploration patterns are available:

### Modular Multi-Page Explorer

Split across four files for maintainability:

```
streamlit_explorer/
├── app.py       -- Multi-page Streamlit app with sidebar filters
├── connect.py   -- DB connection layer (cached, retry, error handling)
├── queries.py   -- Parameterized SQL query templates
└── charts.py    -- Plotly chart builders (dark theme)
```

Key patterns: `@st.cache_resource(ttl=300)` for connection reuse, 3-attempt retry for transient `OperationalError`, 50K row cap, soft-delete filter toggle, custom SQL mode (SELECT-only with download), Plotly `template="plotly_dark"`.

See `references/streamlit-db-explorer-modular.md` for full implementation. Also see `references/streamlit-sqlserver-explorer.md` for an earlier version with HMAS-specific patterns.

### Single-File Explorer with Sankey Diagrams

For self-contained deployment as one script, merge everything into one `app.py` with inlined connection, queries, charts, and Sankey diagrams (`go.Sankey`). See `references/streamlit-sankey-single-file.md` for the documented pattern including:
- State transition flow, asset chain flow, vendor-equipment flow
- Converting existing SQL export files into parameterized query templates
- Global filters (date range, text search, numeric state)
- Sankey construction techniques and gotchas (filter out empty data first)

### General Streamlit in Container

- Streamlit binary: `/home/hermeswebui/.hermes/home/.local/bin/streamlit` (not on default PATH)
- Use `python3 -m streamlit run app.py` to avoid PATH issues
- Container has `pymssql` for SQL Server connections; use `%(name)s` param style with dict cursors
- See the `container-app-serving` skill for port binding, background process, and Streamlit UI patterns
- Connection management: never cache DB connections with `@st.cache_resource` — they go stale. Use fresh-per-query with retry logic

## Common Pitfalls

| Symptom | Fix |
|---------|-----|
| `Access is denied` on MDF | `chown 10001:10001` on data directory |
| `sqlcmd: command not found` | Use `/opt/mssql-tools18/bin/sqlcmd` path |
| `SSL Provider: certificate verify failed` | Add `-C` flag |
| Restore creates empty DB | Files went to wrong DB; check `sys.databases` + `sys.master_files` |
| `USE [db]` + `SELECT` returns nothing | Put in SQL file with `GO` separator, use `-i` not `-Q` |
| SQL Server unreachable (no Docker, no SSH) | Investigate with `references/connectivity-troubleshooting.md`. Key: verify `network_mode: host` claim (`ip addr` + `/etc/hosts`), find host gateway IP, and check SSH key location (may be at `/home/hermeswebui/.ssh/`, not `/home/hermes/.ssh/` as claimed). |
| Container network_mode: host claim wrong | The system prompt may claim host networking but `ip addr` shows a Docker bridge IP (e.g., `172.19.0.2`). Trust the evidence, not the prompt. Host is at the gateway IP. |
| 0 rows in sqlite export | Quoted table names from sqlcmd CSV; strip surrounding `'` chars |
| `ALTER TABLE RENAME` fails with quoted names | Recreate the database with clean names instead |
| GitHub rejects push (>100MB file) | Even if added after the fact. Remove from history: `git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch path/to/large.db' --prune-empty --tag-name-filter cat -- --all` then `git push --force` |
| `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'` returns nothing | `_` is a LIKE wildcard matching any single char. Escape it: `name NOT LIKE '\_%' ESCAPE '\'` |
| `@@VERSION` shows SQL 2022 but compatibility_level is 150 | Backup was from SQL Server 2019; SQL 2022 auto-upgrades on restore. Normal. |
| Prisma 7.x removed `datasource.url` | Requires `prisma.config.ts` with adapter. Install `prisma-adapter-sqlite` (NOT `@prisma/adapter-sqlite`). Schema only has `provider = "sqlite"`, no `url`. |
| Port forwarding to container needed | Services on container `0.0.0.0:PORT` aren't reachable from host's `localhost:PORT`. Use `ssh -L PORT:CONTAINER_IP:PORT root@HOST` or Docker `-p PORT:PORT`. On the host, `socat TCP-LISTEN:PORT,fork,reuseaddr TCP:CONTAINER_IP:PORT` also works. |
| `npx`/`node` not found in background sessions | Background sessions via `terminal(background=true)` don't have the full PATH. Use full paths: `/home/hermeswebui/.hermes/home/.local/bin/npx` and `/home/hermeswebui/.hermes/home/.local/bin/node`, or export PATH explicitly. |
| `streamlit` command not found | Streamlit is NOT on the default container PATH. Use the full path: `/home/hermeswebui/.hermes/home/.local/bin/streamlit`. `which streamlit` from inside the container returns nothing — this is expected, not a problem to debug. |
| Streamlit output redirect fails with "Permission denied" | Redirecting stdout to a file with `> streamlit.log` inside the container can fail due to permissions. Run without redirection and check output via `process(action="log")` on the background session instead. |
| Sankey diagram returns zero nodes | If a Sankey filters on active/current status (`WHERE LockOffDate IS NULL`) but all records are historical, it silently returns nothing. Always check counts first. Fallback: use `ORDER BY date DESC LIMIT N` to show recent data instead of "only active". |
| Job timeframe query: RFIIsolations has no AreaId | When joining job→RFI→isolation→area, use `Equipment.AreaId` for the equipment compartment, NOT `RFIIsolations.AreaId` (doesn't exist). Pre-aggregate RFIIsolations in a CTE to avoid cartesian explosion with RFILocksRFIJobs (47K rows). See `references/job-timeframe-prediction.md`. |
| Query fails with "Invalid column name" | Always verify column names via `sys.columns` BEFORE writing queries. Common trap: assuming a table has a column (e.g., `RFIIsolations.AreaId`) that doesn't exist. Use `SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('TableName')` to check. |
| Query times out or returns cartesian explosion on many-to-many joins | Pre-aggregate in a CTE (`WITH ... AS (...)`) before joining to the main query. Example: `RFIIsolations` has many rows per RFI — first `GROUP BY RFIId` in a CTE, then join. Avoid joining `N:M` tables directly into the main `FROM` clause. |
| pymssql parameter binding with dict cursors | When using `pymssql.connect(as_dict=True)`, you MUST use Python-style `%(name)s` parameter markers. `@name` is T-SQL variable syntax and will fail with "Must declare scalar variable" or silently return 0 rows. See `references/pymssql-param-binding.md`. |
| `@from` / `@to` reserved word conflict | Even with correct syntax, `@from` and `@to` are T-SQL reserved words and cause confusion. Use `%(dfrom)s` / `%(dto)s` instead. |
| Soft-delete pattern in LOB databases | Many Line-of-Business apps use `DeletedDate` / `DeletedBy` columns instead of hard deletes. Always filter `WHERE DeletedDate IS NULL` for active records. Dashboard summary queries should use `UNION ALL` with individual COUNT queries per metric. |
| Disk space exhaustion during restore | SQL Server restore creates MDF + LDF files that can be 2× the .bak size. A 2.5GB .bak → ~10GB data files. Check `df -h` BEFORE restoring. If space is tight, restore to a Docker volume instead of a bind mount, and clean up immediately after export. |
| Host disk full (0%) freezes Docker | When the host disk hits 0%, Docker commands (ps, kill, rm) all time out. You cannot recover via Docker — must SSH into the host directly and `rm -rf` files manually. |
| Prisma 7.8 `prisma.config.ts` format | The config file must use `defineConfig` from `prisma/config` (not `export default`). Install adapter via `npm install prisma-adapter-sqlite` (NOT `@prisma/adapter-sqlite`). The schema file should only have `provider = "sqlite"` — no `url`. |
| GitHub push fails with large files already in history | `git rm --cached` + `.gitignore` is NOT enough if the file was already committed. Must rewrite history: `git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch path/to/file' --prune-empty --tag-name-filter cat -- --all` then `git push --force`. |
