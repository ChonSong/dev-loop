# Host File Transfer via SSH Pipe

When a file exists on the host machine but not in the container, and no volume mount is available, transfer via SSH pipe.

## When to Use

- File is on host in `/home/sean/Downloads/` or similar
- Container has no `unzip` command
- Downloads directory not mounted to container

## Pattern

```bash
# 1. Verify file exists on host
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 find /home/sean/Downloads -name "*TEAC5019*" -type f

# 2. Transfer via SSH pipe (stdin → file)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "cat /path/to/file.zip" > /workspace/file.zip

# 3. Extract with Python zipfile (no unzip binary in container)
python3 -c "
import zipfile
with zipfile.ZipFile('/workspace/file.zip', 'r') as z:
    z.extractall('/workspace/extracted_folder')
print('Done')
"
```

## Key Points

- `cp` from host to container via SSH fails with "No such file or directory" because destination path doesn't exist inside container
- `cat ... > /workspace/file` works because the redirect runs in container local filesystem
- `unzip` is often not available; Python `zipfile` module is always available
- Verify size after transfer: `ls -la /workspace/file.zip`

## SSH Access Summary

| Item | Value |
|------|-------|
| SSH key | `/home/hermeswebui/.hermes/container_key` |
| Host IP | `172.19.0.1` (not localhost) |
| User | `sean` |
| Auth | SSH agent forwarded (no password) |

## If SSH Key Not Found

Check both paths:
- `/home/hermeswebui/.hermes/container_key` (container-side)
- `~/.ssh/id_ed25519` (host-side, if agent not forwarded)

## Alternative: SCP with Inline Cat

```bash
# If cat redirect doesn't work (permission issues), use scp
scp -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1:/home/sean/Downloads/file.zip /workspace/
```