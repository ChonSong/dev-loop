#!/usr/bin/env bash
# Restore a SQL Server .bak backup file directly via sqlcmd (no Docker needed)
#
# Usage:
#   ./restore-direct.sh [backup_file_path]
#
# Environment:
#   DB_HOST          — SQL Server host (default: localhost)
#   DB_PORT          — SQL Server port (default: 1433)
#   DB_NAME          — Target database name (default: OneTagDev)
#   DB_USER          — SQL Server user (default: sa)
#   DB_PASS          — SA password (REQUIRED: ONETAG_SQL_SA_PASSWORD)
#   BACKUP_FILE      — Default backup file name if no arg given

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
DB_HOST="${ONETAG_SQL_HOST:-${DB_HOST:-localhost}}"
DB_PORT="${ONETAG_SQL_PORT:-${DB_PORT:-1433}}"
DB_NAME="${ONETAG_SQL_DB:-${DB_NAME:-OneTagDev}}"
DB_USER="${ONETAG_SQL_USER:-${DB_USER:-sa}}"
DB_PASS="${ONETAG_SQL_SA_PASSWORD:?ONETAG_SQL_SA_PASSWORD is not set}"

BACKUP_FILE="${1:-${BACKUP_FILE:-}}"

# MOVE paths — for Windows→Linux restores. Set these when the backup was from Windows SQL Server.
#   get logical names: sqlcmd -S ... -Q "RESTORE FILELISTONLY FROM DISK = N'/path/to/backup.bak'"
DATA_LOGICAL_NAME="${DATA_LOGICAL_NAME:-}"
DATA_PHYSICAL_PATH="${DATA_PHYSICAL_PATH:-/var/opt/mssql/data/${DB_NAME}.mdf}"
LOG_LOGICAL_NAME="${LOG_LOGICAL_NAME:-}"
LOG_PHYSICAL_PATH="${LOG_PHYSICAL_PATH:-/var/opt/mssql/data/${DB_NAME}_log.ldf}"
MOVE_CLAUSE=""
if [[ -n "$DATA_LOGICAL_NAME" ]]; then
  MOVE_CLAUSE="MOVE N'${DATA_LOGICAL_NAME}' TO N'${DATA_PHYSICAL_PATH}',
  MOVE N'${LOG_LOGICAL_NAME}' TO N'${LOG_PHYSICAL_PATH}',"
fi

if [[ -z "$BACKUP_FILE" ]]; then
  echo "ERROR: No backup file specified. Pass path as argument or set BACKUP_FILE."
  exit 1
fi

# ── Prerequisites ───────────────────────────────────────────────────────────
if ! command -v sqlcmd &>/dev/null; then
  echo "ERROR: sqlcmd not found. Install:"
  echo "  curl -sSLo /tmp/sqlcmd.tar.gz https://github.com/microsoft/go-sqlcmd/releases/download/v1.10.0/sqlcmd-linux-amd64.tar.gz"
  echo "  tar -xzf /tmp/sqlcmd.tar.gz -C /usr/local/bin sqlcmd"
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "ERROR: Backup file not found: $BACKUP_FILE"
  exit 1
fi

if [[ ! -s "$BACKUP_FILE" ]]; then
  echo "ERROR: Backup file is empty: $BACKUP_FILE"
  exit 1
fi

# Check for Git LFS pointer
if head -n 1 "$BACKUP_FILE" 2>/dev/null | grep -q "^version https://git-lfs.github.com/spec/v1$"; then
  echo "ERROR: Backup file is a Git LFS pointer. Run 'git lfs pull' first."
  exit 1
fi

# ── SQL Server connectivity check ──────────────────────────────────────────
echo "Checking connection to ${DB_HOST}:${DB_PORT}..."
if ! timeout 5 sqlcmd -S "${DB_HOST},${DB_PORT}" -U "${DB_USER}" -P "${DB_PASS}" \
  -C -d master -Q "SELECT 1 AS ping" -b -W 2>/dev/null | grep -q "ping"; then
  echo "FATAL: SQL Server unreachable at ${DB_HOST}:${DB_PORT}"
  echo ""
  echo "Troubleshooting:"
  echo "  • Verify server is running"
  echo "  • Check port: nc -zv ${DB_HOST} ${DB_PORT}"  
  echo "  • Test credentials: sqlcmd -S ${DB_HOST},${DB_PORT} -U sa -P '<pass>' -C -Q 'SELECT 1'"
  exit 1
fi
echo "Connected successfully."

# ── Disk space check ────────────────────────────────────────────────────────
BACKUP_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || echo 0)
MIN_REQUIRED=$((BACKUP_SIZE * 3))  # backup + MDF + LDF
echo "Backup size: $((BACKUP_SIZE / 1073741824))GB"
echo "Recommended: at least $((MIN_REQUIRED / 1073741824))GB free"

# ── Run restore ────────────────────────────────────────────────────────────
echo ""
echo "Restoring ${DB_NAME} from ${BACKUP_FILE}..."
sqlcmd -S "${DB_HOST},${DB_PORT}" -U "${DB_USER}" -P "${DB_PASS}" -C -d master -b -W -t 600 <<EOF
-- Kill existing connections, set single-user mode
IF DB_ID(N'${DB_NAME}') IS NOT NULL
BEGIN
    ALTER DATABASE [${DB_NAME}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    PRINT 'DB set to single-user mode';
END;

RESTORE DATABASE [${DB_NAME}]
FROM DISK = N'${BACKUP_FILE}'
WITH REPLACE, RECOVERY, STATS = 5,
${MOVE_CLAUSE}
;

ALTER DATABASE [${DB_NAME}] SET MULTI_USER;
PRINT 'DB restored and set to multi-user mode';
GO

-- Verify
SELECT name, state_desc FROM sys.databases WHERE name = N'${DB_NAME}';
GO
EOF

echo ""
echo "Restore complete for ${DB_NAME}"
echo "Verify: sqlcmd -S ${DB_HOST},${DB_PORT} -U ${DB_USER} -P '***' -C -d ${DB_NAME} -Q 'SELECT COUNT(*) AS [Tables] FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = '\''BASE TABLE'\'''"
