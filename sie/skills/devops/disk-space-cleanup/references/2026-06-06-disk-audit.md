# Disk Audit — 2026-06-06

## Initial State
- **94% used** (409G/461G, 29G free)
- Mount: `/dev/sda2` on `/workspace` (ext4, rw, noatime)
- Container user: `hermeswebui` (uid 1000), no sudo, no SSH to host

## Disk Hogs Found

| Path | Size | Category | Action | Recovered |
|------|------|----------|--------|-----------|
| `/tmp/npm-cache` | 2.4G | Package cache | Deleted | 2.4G |
| `/tmp/gto-wizard-clone` | 893M | Stale clone | Deleted | 893M |
| `/tmp/playwright_browsers` | 641M | Duplicate browser cache | Deleted (kept `pw-browsers`) | 641M |
| `/tmp/test-clone2/3` + `/tmp/test-bearer` | ~177M | Test artifacts | Deleted | 177M |
| `/tmp/hermes-sync` | 159M | Config backup | Deleted | 159M |
| `/workspace/onetag.bak/` | 2.5G | SQL backup | **Pending** — owned by root, needs `sudo rm -rf` on host | — |
| `/workspace/.git` | 422M | Git history | `git gc --aggressive` | ~50–100M |
| `/workspace/forrest-plan-and-track/.git` | 108M | Git history | `git gc --aggressive` | ~20–30M |
| `/workspace/open-lovable/node_modules` | 1G | Dependencies | Rebuildable (lockfile exists) | — |
| `/workspace/gto-wizard-clone/node_modules` | 738M | Dependencies | Rebuildable (lockfile exists) | — |
| `/workspace/forrest-plan-and-track/node_modules` | 330M | Dependencies | Rebuildable (lockfile exists) | — |
| `/workspace/forrest-plan-and-track/streamlit_onetag` venv | 520M | Python venv | Rebuildable (requirements.txt) | — |
| `/tmp/libs` | 159M | Chrome/Puppeteer libs | **Kept** — needed for QA | — |

## After Phase 1+2
- **93% used** (405G/461G, 33G free) — recovered ~4G
- After `git gc`: **404G used, 33G free**

## Key Findings

### Duplicate Browser Caches
`/tmp/pw-browsers` and `/tmp/playwright_browsers` had identical contents:
```
chromium-1223
chromium_headless_shell-1223
ffmpeg-1011
```
Both 641M. Keep `pw-browsers` (the one the Puppeteer wrapper references).

### Root-Owned File Blocking
`/workspace/onetag.bak/OneTag_HMAS SYDNEY_ANON.bak` (2.5G) is owned by root.
- `truncate` failed: "Permission denied"
- `sudo` not available in container
- SSH to host not available (no key, port 22 closed)
- **Resolution:** User must run `sudo rm -rf /workspace/onetag.bak` on the host

### Forrest DB Status
`/workspace/forrest-plan-and-track/data/onetag.db` — 136M, last written Jun 2. The 2.5G `.bak` is a SQL Server backup that's no longer needed since the SQLite DB is loaded and current.

### Remaining Rebuild-able Space
If all `node_modules` + venv are deleted when not actively developing: ~1.6G additional recovery.

## Host Command Needed
```bash
sudo rm -rf /workspace/onetag.bak
```
This will bring usage to ~401G (~87%, ~37G free).
