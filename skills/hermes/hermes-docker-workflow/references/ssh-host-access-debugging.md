# SSH Debugging: Host Access from Hermes Container

## Session Summary (2026-05-09)

**Problem**: SSH from hermes container to host (hpprobook/EndeavourOS) failed with `Permission denied` even with correct key.

**Root Cause**: Port 22 on host is occupied by something that isn't standard sshd. The port accepts connections (SSH banner `OpenSSH_10.3` responds) but authentication always fails.

**Working Solution**: Custom sshd on port 2229 using a copied binary.

---

## Key Findings

### Port 22 Ownership Mystery
- `cat /proc/net/tcp` shows inode 10825 listening on port 22 (0x0016)
- Process could NOT be found via `ps aux`, `/proc/*/cmdline`, or `/proc/*/fd` search
- PID 1 in container is `tini` (container init), not systemd
- The sshd that answers on port 22 is hidden from container process namespace

### Why `chroot /proc/1/root /usr/sbin/sshd` Fails on Port 22
```
Bind to port 22 on 0.0.0.0 failed: Address already in use.
Bind to port 22 on :: failed: Address already in use.
Cannot bind any address.
```
Something already owns the port — not searchable systemd unit, not visible process.

### Why the Copied sshd Binary Approach Works
1. Copy binary: `cp /proc/1/root/usr/sbin/sshd /tmp/sshd_host`
2. Use **absolute path** for `AuthorizedKeysFile` (not `%h/.ssh/authorized_keys`)
3. Run via `chroot /proc/1/root /tmp/sshd_host -f /path/to/config`

The copied binary resolves paths relative to its own filesystem view, not the chroot's `/proc/1/root`.

### Critical: `%h` Expansion Fails in Chroot Context
When `AuthorizedKeysFile` uses `%h` (home directory expansion), sshd tries to expand it relative to the running user's home from the chroot's `/etc/passwd`. This fails silently. Use absolute paths.

---

## Working SSH Commands

```bash
# SSH as root on port 2229 (works)
ssh -i /opt/data/home/.ssh/id_ed25519 -p 2229 root@localhost "hostname"
# Returns: hpprobook

# SSH as root on port 22 (fails — blocked)
ssh -i /opt/data/home/.ssh/id_ed25519 root@localhost "hostname"
# Returns: Permission denied (publickey,password)

# SSH via IPv6 (fails same way)
ssh -i /opt/data/home/.ssh/id_ed25519 -6 root@::1 "hostname"
```

---

## Host SSH Key Discovery

| Path | Description |
|------|-------------|
| `/proc/1/root/usr/sbin/sshd` | Host sshd binary (copied to `/tmp/sshd_host` for custom config) |
| `/proc/1/root/etc/ssh/sshd_config` | Host sshd config (port 22, UsePAM yes, PubkeyAuth commented out) |
| `/proc/1/root/etc/ssh/ssh_host_*` | Host SSH host keys (rsa, ecdsa, ed25519) |
| `/proc/1/root/root/.ssh/authorized_keys` | Root's authorized_keys on host |
| `/proc/1/root/home/sean/.ssh/authorized_keys` | Sean's authorized_keys on host |

---

## SSH Debugging Trace (Failure Path)

```
debug1: Offering public key: /opt/data/home/.ssh/id_ed25519 ED25519 SHA256:sue0wfFk9mnlVvsKYtYbzGPFBphUNnkgeRE+Ffw1e+0 explicit
debug1: Authentications that can continue: publickey,password
debug1: Next authentication method: password
```
Key is offered but server responds "authentications that can continue: publickey,password" then immediately jumps to password — indicates server isn't finding/reading the authorized_keys file properly.

---

## Authoritative Commands

```bash
# Check if port 22 is open (should show SSH banner)
curl --max-time 2 telnet://127.0.0.1:22

# Check port 2229 (custom sshd)
curl --max-time 2 telnet://127.0.0.1:2229

# View TCP connections
cat /proc/net/tcp | grep "0016"  # port 22 in hex

# List all sshd processes visible from container
for pid in $(ls /proc/1/root/proc/ 2>/dev/null | grep -E "^[0-9]+$"); do
  cmdline=$(cat /proc/1/root/proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
  if [[ "$cmdline" == *sshd* ]]; then echo "PID $pid: $cmdline"; fi
done

# Test key authentication (verbose)
ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no -o ConnectTimeout=5 -v root@localhost 2>&1 | grep -E "Offering|Authentications|authorized_keys"
```

---

## Temporary Fix for Port 22 (Run on Host Manually)

```bash
# Stop whatever is owning port 22
sudo fuser -k 22/tcp

# Start real sshd
sudo systemctl enable --now ssh

# Verify
ssh -i ~/.ssh/id_ed25519 sean@localhost "hostname"
```

This needs to be done on the host terminal — cannot be done from inside the hermes container reliably.

---

## Current Working SSH Configuration (May 2026)

**Host IP**: `172.19.0.1` (container gateway, not localhost)
**Key**: `/home/hermeswebui/.hermes/container_key` (Ed25519)
**User**: `sean`

```bash
# Primary working SSH command
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "hostname"

# With connection keepalive
ssh -i /home/hermeswebui/.hermes/container_key -o "ServerAliveInterval=15" -o "ServerAliveCountMax=3" sean@172.19.0.1 "hostname"
```

**Path correction:** The older `/opt/data/home/.ssh/id_ed25519` path (port 2229) is legacy. The current correct path is `/home/hermeswebui/.hermes/container_key` from inside the container.

### When SSH Commands Return Empty Output

If SSH returns exit code 0 with no output (instead of command output), the command is likely timing out or the server is slow. Add `ServerAliveInterval=15` to prevent premature connection closure. If output is truncated, the command completed but the pipe broke — check results directly on the host.

### Git Operations via SSH (hermes-sync)

```bash
# Verify files exist in git (no pull needed)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 'cd /home/sean/hermes-sync && git ls-files docker/'

# Check remote HEAD via GitHub API through SSH
ssh -i /home/hermeswebui/.hermes/container_key -o "ServerAliveInterval=15" sean@172.19.0.1 \
  'gh api repos/ChonSong/hermes-sync/git/trees/HEAD?recursive=1' | \
  python3 -c "import json,sys; t=json.load(sys.stdin); print([e['path'] for e in t['tree'] if 'docker' in e['path']])"

# When .git/FETCH_HEAD is root-owned (blocks git pull):
# Use gh api via SSH instead — bypasses git's fetch mechanism entirely
```

### When `.git/FETCH_HEAD` is Permission Denied

If `git pull` fails with `error: cannot open '.git/FETCH_HEAD': Permission denied`, the `.git` directory or `FETCH_HEAD` file is root-owned. Git operations that need to write to `.git/` (like fetch/pull) will fail. However:

- `git ls-files` works (read-only)
- `git add`/`git commit` work if the working tree files are owned by the user
- `git push` works if remote accepts the authentication

**Workaround**: Use `gh api` commands via SSH to check remote state, bypassing git's fetch entirely. The remote HEAD can be verified directly via GitHub API without pulling.