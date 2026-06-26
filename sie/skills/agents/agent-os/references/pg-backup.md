# PostgreSQL Backup

## Setup
- Script: `/home/sean/.hermes/scripts/pg-backup.sh`
- Backup dir: `/home/sean/.hermes/backups/postgres/`
- Cron: daily at 3am (`0 3 * * *`)
- Log: `/home/sean/.hermes/backups/postgres/backup.log`

## What it does
1. `docker exec agent-os-postgres pg_dump -U agentos -d agentos | gzip > backup_file.sql.gz`
2. Filename: `agentos_YYYYMMDD_HHMMSS.sql.gz`
3. Prunes backups older than 7 days

## Restore
```bash
gunzip < /home/sean/.hermes/backups/postgres/agentos_TIMESTAMP.sql.gz | \
  docker exec -i agent-os-postgres psql -U agentos -d agentos
```

## Manual run
```bash
bash /home/sean/.hermes/scripts/pg-backup.sh
```
