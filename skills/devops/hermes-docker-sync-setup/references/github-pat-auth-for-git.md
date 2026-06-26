# GitHub PAT Authentication for Git Operations

## TL;DR

For `git clone`, `git push`, `git fetch` — use **credential helper**, NOT URL-embedded tokens.

```bash
# ✅ Correct: credential helper
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials
git config --global credential.helper store

# ❌ Wrong: Bearer token in URL (deprecated by GitHub)
git clone "https://Bearer ${GITHUB_TOKEN}@github.com/repo.git"

# ❌ Wrong: raw token in URL (works but leaks in logs/process lists)
git clone "https://${GITHUB_TOKEN}@github.com/repo.git"
```

## Why URL Embedding Fails

GitHub deprecated Bearer-token URL patterns (`https://Bearer TOKEN@github.com/...`) in 2023. The `Bearer ` prefix in a git URL causes authentication failures.

Raw token embedding (`https://TOKEN@github.com/...`) works but is **unsafe** — the token appears in:
- `ps aux` output
- shell history
- git log output (if `GIT_TRACE=1`)
- error messages

Credential helper stores the token in `~/.git-credentials` (mode 0600) and git sends it only during the actual authentication handshake — never in URLs or process listings.

## Credential Helper Setup

```bash
# Write credentials file (mode 0600 — git refuses if world-readable)
mkdir -p "$(dirname ~/.git-credentials)"
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials
chmod 0600 ~/.git-credentials

# Enable the helper globally
git config --global credential.helper store
```

This applies to **all** git operations for the current user, not just a single clone.

## Fine-Grained PATs Don't Work with Git

Fine-grained PATs (prefix `NZ-...`, generated at https://github.com/settings/tokens?type=beta) are **API-only**. Git's HTTP/HTTPS protocol does not support them:

```
fatal: could not read Password for 'https://NZ-XXXX@github.com': No such device or address
```

**Only classic PATs** (`ghp_...`) work with git protocol.

| PAT type | Prefix | Git clone/push | GitHub API |
|----------|--------|----------------|------------|
| Classic | `ghp_` | ✅ | ✅ |
| Fine-grained | `NZ-...` | ❌ | ✅ |

## Bootstrap Script Pattern

In `hermes-bootstrap/setup.sh`:

```bash
# Exit fast if token missing — no interactive prompt
if [ -z "${GITHUB_TOKEN}" ]; then
    echo "ERROR: GITHUB_TOKEN env var required" >&2
    echo "Usage: GITHUB_TOKEN=ghp_xxx curl -fsSL ... | bash" >&2
    exit 1
fi

# Set up credential helper BEFORE any git operation
mkdir -p ~/.git-credentials
echo "https://${GITHUB_TOKEN}@github.com" > ~/.git-credentials
chmod 0600 ~/.git-credentials
git config --global credential.helper store

# Now clone private repos without token in URLs
git clone https://github.com/ChonSong/hermes-sync.git
git clone https://github.com/ChonSong/hermes-webui.git
# hermes-agent is public — no auth needed
git clone https://github.com/NousResearch/hermes-agent.git
```

This approach works:
- In containers (no TTY for interactive prompt)
- In CI/CD pipelines
- On headless machines
- In Codespaces (where git auth behaves differently than local)

## Codespace-Specific Behavior

In GitHub Codespaces, token-in-URL may fail with `403 Write access to repository not granted` even when the token has `repo` scope. The Codespace git network configuration handles authentication differently than standard environments.

**Root cause:** Codespace injects its own git credential helper which may conflict with URL-embedded tokens.

**Fix:** Always use the credential helper approach above — it works in Codespaces because git uses the standard credential protocol rather than URL parsing.