# Cron Job Host Access — Authenticated Tool Anti-Pattern

## The Failure

`seans-reporepo refresh` cron job (`e4d95660ab35`) failed with `last_status: error` for 7 days. The cron prompt told it to SSH to the host, but `generate-catalog.py`'s `gh()` function ran `gh` commands **locally** (in the container context) where `gh` is not authenticated.

```python
# generate-catalog.py — what was happening
def gh(cmd: str) -> str:
    result = subprocess.run(f"gh {cmd}", shell=True, ...)  # ← runs in container, NOT on host
```

The script was designed to run **on the host** (where `gh auth` is set up), but the cron job was executing it **in the container** where `gh` is not authenticated.

## Key Distinction: Container vs Host Tooling

| Tool | Host | Container | Cron job context |
|------|------|-----------|-------------------|
| `gh` CLI | ✅ authenticated | ❌ not authenticated | ❌ runs in container |
| `python3` scripts | ✅ run locally | ✅ run locally | ✅ runs in container |
| Host filesystem | ✅ full access | partial (volumes) | partial |

**Rule:** When a script relies on an authenticated CLI tool (like `gh`), it must run on the host, not the container. For cron jobs, this means the ENTIRE script must execute over SSH on the host.

## The Fix

Update the cron job prompt to wrap the entire script execution in SSH:

**Before (broken):**
```
Run: bash /home/sean/.hermes/scripts/refresh.sh
```
The script runs in the container where `gh` isn't authenticated.

**After (working):**
```
Execute: ssh -i /home/hermeswebui/.hermes/container_key -o StrictHostKeyChecking=accept-new sean@172.19.0.1 "bash /home/sean/.hermes/scripts/refresh.sh"
```
The entire script runs on the host where `gh` IS authenticated.

## Correct SSH Pattern for Cron Jobs

```bash
ssh -i /home/hermeswebui/.hermes/container_key \
     -o StrictHostKeyChecking=accept-new \
     -o ConnectTimeout=5 \
     sean@172.19.0.1 \
     "<full command to run on host>"
```

**Key components:**
- `-i /home/hermeswebui/.hermes/container_key` — Ed25519 key for `sean@172.19.0.1`
- `-o StrictHostKeyChecking=accept-new` — auto-accept new host keys (avoids interactive prompt)
- `-o ConnectTimeout=5` — fail fast if host unreachable
- `sean@172.19.0.1` — NOT `localhost` (port 22 not on container's localhost)
- Command in double-quotes — runs on the host shell

## General Rule for Cron Jobs Using Host-Only Tools

Before creating a cron job that calls a script on the host:
1. **Check if the script uses authenticated CLI tools** (`gh`, `gcloud`, `aws`, etc.)
2. **If yes, the entire script must run over SSH** — not just parts of it
3. **Never assume the cron job context is the host** — it's the container
4. **SSH key path in container:** `/home/hermeswebui/.hermes/container_key` (NOT `/opt/data/container_key`)
5. **Host IP:** `172.19.0.1` (Docker gateway, NOT `localhost`)

## Verification After Fix

```bash
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "git -C /home/sean/.hermes/cache/seans-reporepo log --oneline -1"
```
Should show the newest commit. Then check `cronjob action=list` → `last_status: ok` for the job.