# TrueNAS MCP Server Setup

## Overview

[truenas-mcp](https://github.com/truenas/truenas-mcp) is a Go binary implementing an MCP server that connects to TrueNAS via secure WebSocket (`wss://`). It exposes 48+ tools for monitoring, storage, apps, VMs, shares, and maintenance.

## Binary

- **Release:** v0.2.0 (Linux amd64)
- **Source:** https://github.com/truenas/truenas-mcp/releases
- **Local path:** `/home/hermeswebui/.local/bin/truenas-mcp`
- **Test:** `truenas-mcp --version`

## MCP Server Config

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  truenas:
    command: /home/hermeswebui/.local/bin/truenas-mcp
    args: ["--truenas-url", "192.168.1.102", "--api-key", "your-api-key"]
    timeout: 120
    connect_timeout: 30
```

## API Key

Generate at System Settings → API Keys in the TrueNAS web UI. The key is passed directly in `args` or via the `TRUENAS_API_KEY` env var.

## Connection Details

- **Protocol:** `wss://` on port 443 (enforced — ws:// will revoke the key)
- **Self-signed certs:** Accepted by default (no `--insecure` flag needed for most TrueNAS setups)
- **Auth method:** `auth.login_with_api_key` over WebSocket

## Registered Tools (48 total)

Monitoring: `system_info`, `system_health`, `get_system_metrics`, `get_network_metrics`, `get_disk_metrics`, `get_arc_metrics`, `get_ups_metrics`, `list_alerts`, `dismiss_alert`, `restore_alert`

Storage: `query_pools`, `query_datasets`, `query_snapshots`, `query_shares`, `create_dataset`, `create_smb_share`, `create_nfs_share`, `get_pool_capacity_details`, `analyze_capacity`, `get_scrub_status`, `run_scrub`, `query_scrub_schedules`, `create_scrub_schedule`, `delete_scrub_schedule`

Apps: `query_apps`, `search_app_catalog`, `get_app_catalog_details`, `install_app`, `start_app`, `stop_app`, `upgrade_app`, `delete_app`

Maintenance: `check_updates`, `download_update`, `apply_update`, `update_status`, `query_boot_environments`, `get_current_boot_environment`, `delete_boot_environment`, `system_reboot`

Directory: `query_directory_services`, `get_directory_service_status`, `configure_directory_service`, `leave_directory_service`, `refresh_directory_cache`, `list_directory_certificates`

Other: `query_vms`, `query_jobs`, `tasks_list`, `tasks_get`

## Known Issues

- Running inside an SSH tunnel or container with filtered environment: resolved path needed for the binary
- If `get_hermes_home()` resolves to a path different from `~/.hermes`, add config to the canonical `config.yaml`
- WebUI sessions need manual `discover_mcp_tools()` call — doesn't auto-discover at startup
