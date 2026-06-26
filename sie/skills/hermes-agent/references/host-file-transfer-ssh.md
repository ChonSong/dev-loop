# Host File Transfer via SSH Pipe

When a file exists on the host machine but not in the container, and no volume mount is available, transfer via SSH pipe.

## When to Use

- File is on host in `/home/sean/Downloads/` or similar
- Container has no `unzip` command
- Downloads directory not mounted to container

## Pattern

```bash
ssh -i /home/hermeswebui/.ssh/id_ed25519 sean@172.19.0.1 "cat /path/to/file" > /workspace/file
```

## SSH Access Summary

| Item | Value |
|------|-------|
| SSH key | `/home/hermeswebui/.ssh/id_ed25519` |
| Host IP | `172.19.0.1` |
| User | `sean` |
| Auth | SSH key (ed25519) |

## SSH Key Generation (when no key exists)

If no SSH key exists anywhere in the container:

```bash
mkdir -p /home/hermeswebui/.ssh
ssh-keygen -t ed25519 -f /home/hermeswebui/.ssh/id_ed25519 -N "" -C "hermes-container@$(hostname)"
ssh-keyscan -t ed25519 172.19.0.1 >> /home/hermeswebui/.ssh/known_hosts
# Copy public key to host
ssh-copy-id -i /home/hermeswebui/.ssh/id_ed25519 sean@172.19.0.1
```

## Key Points

- `cp` from host to container via SSH fails with "No such file or directory" because destination path doesn't exist inside container
- `cat ... > /workspace/file` works because the redirect runs in container local filesystem
- `unzip` is often not available; Python `zipfile` module is always available
- Verify size after transfer: `ls -la /workspace/file.zip`

## Writable Directories

- `/home/hermes/` — NOT writable from container
- `/home/hermeswebui/` — writable, use for SSH keys
- `/workspace/` — writable, general purpose

---

## Direct Root SSH (No Key Required) — hermes-webui Container

As of 2026-07-09, the `hermes-webui` container can reach the host directly **without any key flag**:

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@172.17.0.1 "whoami"
```

| Item | Value |
|------|-------|
| Host IP | `172.17.0.1` (Docker default gateway) |
| User | `root` |
| Auth | Default SSH config (no key flag needed) |
| Works from | `hermes-web-ui` / `hermeswebui` containers |

**Common operations:**

```bash
# Run a command on host
ssh root@172.17.0.1 "pacman -S --noconfirm cairo"

# Check if a Python package is installed on host
ssh root@172.17.0.1 "pip show somepackage"

# Install a Python package on host (Arch managed env)
ssh root@172.17.0.1 "pip install --break-system-packages <package>"
```

> **⚠️ System-prompt path does NOT work:** `ssh -i /home/hermes/.ssh/id_ed25519 sean@localhost` — the key doesn't exist at that path and `localhost` is unreachable from this container. Use `root@172.17.0.1` instead.

> **Arch pip caveat:** The host runs Arch Linux with an externally-managed Python environment. For system packages use `pacman -S python-xyz`. For pip-only packages use `pip install --break-system-packages xyz`.
