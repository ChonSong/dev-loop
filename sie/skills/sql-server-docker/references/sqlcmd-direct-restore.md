# sqlcmd-Only Restore (No Docker)

When sqlcmd is installed directly (not inside a Docker container) and SQL Server is running somewhere accessible, restore scripts work differently than the Docker-based approach:

## Key Differences from Docker-Based Restore

| Aspect | Docker-Based | sqlcmd-Only |
|--------|-------------|-------------|
| Path mapping | Volume mount needed (`/host/path:/container/path`) | Same path on both ends |
| Backup file location | Must be bind-mounted into container | Any path sqlcmd can read |
| sqlcmd | Inside container (`docker exec`) | Installed on the system |
| Connectivity | Always `localhost` (same container) | Can target any host/port |
| Pre-flight checks | Docker status + container logs | TCP connectivity + credentials |

## The Adapted Script

The script at `templates/restore-direct.sh` is adapted from a devcontainer script that assumed Docker volume mounts. Key adaptations:

1. **Replaced container-specific paths** — `/workspaces/bluecats-onetag/.devcontainer/...` → direct `/workspace/...` paths
2. **Added SQL Server connectivity check** — probes the target host:port before attempting restore, fails fast with troubleshooting tips
3. **Disk space warning** — warns if available space < 3× backup size (saves restore from silent OOM/disk-full death)
4. **Configurable host/port** — via `ONETAG_SQL_HOST` and `ONETAG_SQL_PORT` env vars, defaults to localhost:1433
5. **sqlcmd heredoc** — T-SQL in a heredoc instead of `-Q` flag, handles multi-line GO-separated batches cleanly

## When to Use Each Approach

- **Docker-based**: When you don't have sqlcmd installed, or need a throwaway SQL Server instance
- **sqlcmd-only**: When SQL Server is already running on the network, or when Docker is unavailable (no socket, no daemon)
