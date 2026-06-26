# Windows .bak → Linux SQL Server Restore Pipeline

Full worked example from a real session: restoring a 2.5GB Windows SQL Server backup (OneTag) to a Linux SQL Server 2022 container, when the backup file lives in a different container than the SQL Server container.

## Prerequisites

| Item | Notes |
|------|-------|
| SSH key authorized on host | Key at `~/.ssh/id_ed25519`, host alias in `~/.ssh/config` |
| `sqlcmd` installed | v1.10+ at `~/.local/bin/sqlcmd` |
| SQL Server container running | On the host, not necessarily on host networking |
| ~10GB free disk | 2.5GB backup → ~5GB MDF + ~5GB LDF |

## Full Pipeline

### Step 1: Get the backup file into the SQL Server container

The `.bak` lives in a separate container (Hermes at `172.19.0.2`). The SQL Server container (`sqlserver-onetag`) is on a different Docker bridge (`172.17.0.2`). Bridge the gap via SSH:

```bash
# Copy from local container to host
scp /workspace/OneTag_HMAS\ SYDNEY_ANON.bak host:/tmp/onetag-backup.bak

# Copy from host into SQL Server container
ssh host "docker cp /tmp/onetag-backup.bak sqlserver-onetag:/var/opt/mssql/onetag-backup.bak"

# Verify
ssh host "docker exec sqlserver-onetag ls -lh /var/opt/mssql/onetag-backup.bak"

# Clean host temp
ssh host "rm /tmp/onetag-backup.bak"
```

### Step 2: Discover logical file names

Windows backups have hardcoded `C:\...` paths. Get the logical names:

```bash
ssh host "docker exec sqlserver-onetag /opt/mssql-tools18/bin/sqlcmd \
  -S localhost,1433 -U sa -P 'password' -C -d master \
  -Q \"RESTORE FILELISTONLY FROM DISK = N'/var/opt/mssql/onetag-backup.bak'\""
```

Typical output:
```
LogicalName  PhysicalName (Windows path)
-----------  -------------------------------------------------
OneTag       C:\...\OneTag_Sydney.mdf
OneTag_log   C:\...\OneTag_Sydney_log.ldf
```

### Step 3: Ensure data directory exists

```bash
ssh host "docker exec sqlserver-onetag mkdir -p /var/opt/mssql/data"
```

### Step 4: Restore WITH MOVE

```bash
# Write SQL to temp file to avoid quoting hell with T-SQL
ssh host "cat > /tmp/restore.sql << 'SQLEOF'
RESTORE DATABASE [OneTagDev]
FROM DISK = N'/var/opt/mssql/onetag-backup.bak'
WITH REPLACE, RECOVERY, STATS = 5,
MOVE N'OneTag' TO N'/var/opt/mssql/data/OneTag_Sydney.mdf',
MOVE N'OneTag_log' TO N'/var/opt/mssql/data/OneTag_Sydney_log.ldf';
GO
SQLEOF"

# Pipe through docker exec -i (avoids shell escaping issues)
ssh host "cat /tmp/restore.sql | docker exec -i sqlserver-onetag \
  /opt/mssql-tools18/bin/sqlcmd -S localhost,1433 -U sa -P 'password' \
  -C -d master -b -t 600"
```

**Important:** Use `docker exec -i` (stdin pipe) instead of `docker exec ... -i /tmp/restore.sql` to avoid having to copy the SQL file into the container too.

### Step 5: Verify

```bash
# From the local container (via Docker gateway)
sqlcmd -S "172.19.0.1,1433" -U sa -P 'password' -C -d OneTagDev \
  -Q "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
```

### Step 6: Clean up

```bash
ssh host "docker exec sqlserver-onetag rm /var/opt/mssql/onetag-backup.bak"
ssh host "rm /tmp/restore.sql"
```

## Pitfalls

### SA Password Mismatch
**Symptom:** `Login failed for user 'sa'. Reason: Password did not match.`
**Cause:** The env var `MSSQL_SA_PASSWORD` in the container is stale — the SA password was changed after initial setup.
**Fix:** Start the container in single-user mode and reset the password (see SKILL.md §SA Password Reset).

### Quoting Hell with T-SQL
T-SQL with `WITH MOVE` uses single quotes around path strings. Shell + SSH + docker exec nests 3-4 levels of quoting. **Solution:** Write SQL to a file on the host, then pipe via `docker exec -i` (or `cat file.docker exec -i`). This avoids needing to escape the SQL at all.

### Disk Space
A 2.5GB .bak can expand to ~11GB (5.3GB MDF + 5.5GB LDF). The SQL Server container's data directory needs enough free space. Check **inside the container**:
```bash
ssh host "docker exec sqlserver-onetag df -h /var/opt/mssql"
```

### Compatibility Upgrade
SQL Server 2019 backups (version 904) restored on SQL Server 2022 are auto-upgraded to version 957. This is normal and unavoidable for restore. The upgrade steps (~50 steps from 904→957) print during restore and add to the total time.

## Container Networking Notes

| Misconception | Reality | Evidence |
|---|---|---|
| `network_mode: host` | Docker bridge network | Container at `172.19.0.2`, not host IP |
| `localhost:1433` reachable | Port only accessible via Docker gateway `172.19.0.1:1433` | Direct TCP check fails on localhost |
| SSH key at `/home/hermes/.ssh/id_ed25519` | Key at `/home/hermeswebui/.ssh/id_ed25519` | Actual filesystem |
| Host is `localhost:22` | Host is `172.19.0.1:22` | SSH config: `Host host → HostName 172.19.0.1` |

Always verify with `ip addr`, `/etc/hosts`, and `cat ~/.ssh/config` before assuming networking topology.
