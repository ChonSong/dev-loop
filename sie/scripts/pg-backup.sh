#!/bin/bash
# Agent-OS PostgreSQL backup script
BACKUP_DIR="$HOME/.hermes/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/agentos_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

# pg_dump via docker exec
docker exec agent-os-postgres pg_dump -U agentos -d agentos | gzip > "$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "agentos_*.sql.gz" -mtime +7 -delete

echo "[$(date)] Backup saved: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
