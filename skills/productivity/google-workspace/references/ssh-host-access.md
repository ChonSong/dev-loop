# SSH Host Access for Google Workspace Operations

When Google Drive upload or other host-side operations are needed, SSH connects via the Docker bridge gateway — NOT `localhost` unless sshd is running inside the container. The host is always at `172.19.0.1` for this Docker setup.

## Quick Reference

| Path/Command | Value |
|---|---|
| SSH key | `/home/hermeswebui/.hermes/container_key` |
| Host IP | `172.19.0.1` (Docker bridge gateway — fixed for this setup) |
| Host home | `/home/sean/` (Linux host) |
| Downloads on host | `/home/sean/Downloads/` |
| OAuth client secret | Copied to `/home/hermeswebui/.hermes/google_client_secret.json` |
| SSH command | `ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 <command>` |

## Standard SSH Pattern

```bash
# Always use the bridge gateway IP, not localhost
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "echo connected"

# Copy file from host to container via cat redirect
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "cat /path/on/host/file.zip" > local_file.zip

# List Downloads on host
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "ls ~/Downloads/"

# Copy large files: use cat on host + redirect in container (faster than scp for large zips)
ssh -i ... sean@172.19.0.1 "cat /home/sean/Downloads/bigfile.zip" > /workspace/bigfile.zip
```

## SSH Key Note

The container key at `/home/hermeswebui/.hermes/container_key` is the forwarded agent key — SSH agent forwarding is active, so keys configured on the host are available without storing them in the container. No password needed.

## Starting sshd on the Host

If the host SSH daemon is not running:

```bash
# Linux (on host)
sudo systemctl start sshd

# macOS (on host)
# System Settings → Sharing → Remote Login (enable)
```

## Google OAuth Workflow (this setup — already done, token at ~/.hermes/google_token.json)

1. Client secret JSON found on host at `/home/sean/Downloads/client_secret_*.json`
2. Copy to container: `ssh ... "cat /home/sean/Downloads/client_secret_*.json" > /home/hermeswebui/.hermes/google_client_secret.json`
3. Run setup: `python3 ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --client-secret ~/.hermes/google_client_secret.json`
4. Get auth URL: `python3 ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --auth-url`
5. User pastes redirected URL from browser → `--auth-code` exchange completes
6. Token saved to `/home/hermeswebui/.hermes/google_token.json`

## Crossref API (academic references)

Use `urllib.request` directly — no `google-auth` or browser tools needed:

```python
import urllib.request, json
req = urllib.request.Request(
    "https://api.crossref.org/works?query-title=understanding+by+design&rows=5",
    headers={"Accept": "application/json", "User-Agent": "research-bot/1.0"}
)
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
```

## Large File Transfer via SSH Cat

The `unzip` command is not available in the container. For zip files:
- Use Python's `zipfile` module: `python3 -c "import zipfile; zipfile.ZipFile('file.zip').extractall('out_dir')"`
- For large files from host, redirect stdin: `ssh ... "cat file.zip" > file.zip`
- For node_modules/docx: use `python-docx` (already installed), not the Node.js `docx` package