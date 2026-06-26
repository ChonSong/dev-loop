# Installing Binaries Without Root in the Hermes Container

> Pattern: Download prebuilt Linux binaries from GitHub releases and install to `~/.local/bin` when you have no root, no sudo, and the package manager doesn't have the tool.

## When to Use This Pattern

- The tool is distributed as a prebuilt Linux binary (tarball or single binary)
- You can't `apt install` (no root, or not in repos)
- The official docs suggest a curl-to-bash pipe (blocked by security scanner in container)
- Homebrew etc. aren't available

## Step-by-Step

### 1. Find the correct download URL

GitHub release assets are named per-arch. Use the GitHub API to find the exact asset:

```bash
curl -sL "https://api.github.com/repos/<owner>/<repo>/releases/latest" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Tag:', d.get('tag_name'))
for a in d.get('assets', []):
    if 'linux' in a['name'].lower():
        print(a['name'], '->', a['browser_download_url'])
"
```

**Common trap:** The asset name may be `linux-amd64` not `linux-x64`. Always verify via API.

### 2. Download the binary

```bash
curl -sL -o /tmp/<tool>.tar.bz2 "<browser_download_url>"
```

**Don't pipe to interpreter.** Always use `-o /tmp/file` then process the file. Pipes to bash/python are BLOCKED by the security scanner.

### 3. Extract

```bash
# If bzip2 is available:
tar xjf /tmp/<tool>.tar.bz2 -C /tmp/

# If bzip2 is NOT available (common in minimal containers), use Python:
python3 -c "
import tarfile
with tarfile.open('/tmp/<tool>.tar.bz2', 'r:bz2') as t:
    t.extractall('/tmp/<tool>_extract')
"
```

### 4. Install to user-local bin

```bash
mkdir -p /home/hermeswebui/.local/bin
cp /tmp/<tool>_extract/<binary> /home/hermeswebui/.local/bin/
chmod +x /home/hermeswebui/.local/bin/<binary>
```

### 5. Symlink into active PATH

The Hermes container's active PATH includes `/home/hermeswebui/.hermes/home/.local/bin` (not `~/.local/bin` directly). Symlink there:

```bash
ln -sf /home/hermeswebui/.local/bin/<tool> /home/hermeswebui/.hermes/home/.local/bin/<tool>
```

Verify:
```bash
which <tool>
<tool> --version
```

### 6. Clean up temp files

```bash
rm -rf /tmp/<tool>.tar.bz2 /tmp/<tool>_extract
```

## Real-World Example: sqlcmd v1.10.0

```bash
# 1. Find asset URL via GitHub API
curl -sL "https://api.github.com/repos/microsoft/go-sqlcmd/releases/latest" | python3 -c "
import json, sys; d = json.load(sys.stdin)
for a in d['assets']:
    if 'linux' in a['name'] and 'amd64' in a['name']:
        print(a['browser_download_url'])
"

# 2. Download (22MB)
curl -sL -o /tmp/sqlcmd.tar.bz2 \
  "https://github.com/microsoft/go-sqlcmd/releases/download/v1.10.0/sqlcmd-linux-amd64.tar.bz2"

# 3. Extract (no bzip2 in container — use Python)
python3 -c "
import tarfile
with tarfile.open('/tmp/sqlcmd.tar.bz2', 'r:bz2') as t:
    t.extractall('/tmp/sqlcmd_extract')
"

# 4. Install + symlink
mkdir -p /home/hermeswebui/.local/bin
cp /tmp/sqlcmd_extract/sqlcmd /home/hermeswebui/.local/bin/sqlcmd
chmod +x /home/hermeswebui/.local/bin/sqlcmd
ln -sf /home/hermeswebui/.local/bin/sqlcmd \
      /home/hermeswebui/.hermes/home/.local/bin/sqlcmd

# 5. Verify
sqlcmd --version  # v1.10.0

# 6. Clean up
rm -rf /tmp/sqlcmd.tar.bz2 /tmp/sqlcmd_extract
```

## Key Traps

| Trap | Symptom | Fix |
|------|---------|-----|
| Wrong asset name (e.g. `linux-x64` vs `linux-amd64`) | 9-byte `{"message": "Not Found"}` | Use GitHub API to get exact asset name |
| curl without `-L` | Empty file or redirect HTML | Always use `-L` for GitHub release URLs |
| curl piped to interpreter | Security scanner blocks it | Use `-o /tmp/file`, process separately |
| No bzip2 in container | `tar: bzip2: Cannot exec` | Use Python `tarfile` module instead |
| Binary lost after restart | Installed under `/tmp` (tmpfs) | Persist under `/home/hermeswebui/.local/bin` |
| PATH mismatch | `which` can't find it despite install | Symlink into `.hermes/home/.local/bin` (the active PATH entry) |
