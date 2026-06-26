# Container-to-Host Connectivity Troubleshooting for SQL Server

When you need to restore a `.bak` file but the SQL Server container is unreachable, use this investigation pattern to find the host and enable access.

## The Investigation Pattern

### 1. Verify the network topology

The system prompt may claim `network_mode: host`, but the actual Docker networking may differ. Verify:

```bash
# Check which network the container is on
ip addr 2>/dev/null | grep inet

# Check /etc/hosts for container IP vs host gateway
cat /etc/hosts

# The host gateway is typically the .1 address of the container's subnet
# e.g., container=172.19.0.2 → host gateway=172.19.0.1
```

**Evidence from a real session:** Container had IP `172.19.0.2` and host `0fa2ab323c3e` in `/etc/hosts`, with `127.0.0.1` as the only lo entry. This means the container was on a Docker bridge network (`172.19.0.0/16`), NOT host networking — contradicting the system prompt claim.

### 2. Check SSH accessibility

The container may have an SSH config pointing to the host:

```bash
cat ~/.ssh/config
# Typical: Host host → HostName 172.19.0.1, User sean
```

Test connectivity:

```bash
# Check if SSH is reachable
ssh -o ConnectTimeout=5 host "echo connected" 2>&1

# Verbose for debugging
ssh -v host "echo connected" 2>&1 | tail -20
```

**Diagnostic clues:**
- `Connection refused` → SSH server not running on the host (or wrong IP)
- `Permission denied (publickey)` → SSH works but key not authorized
- Success → can manage Docker remotely

### 3. Try SQL Server directly

```bash
# Test port with bash built-in (no nc needed)
timeout 3 bash -c 'echo > /dev/tcp/localhost/1433' 2>/dev/null && echo "OPEN" || echo "CLOSED"

# Scan common SQL ports
for port in 1433 1434 1401 1533 11433 13433 14433; do
  timeout 1 bash -c "echo > /dev/tcp/localhost/$port" 2>/dev/null && echo "Port $port OPEN" || true
done
```

### 4. Check Docker availability from inside container

```bash
# Check if Docker socket is mounted
ls -la /var/run/docker.sock 2>/dev/null

# Check if Docker CLI exists
command -v docker 2>/dev/null

# Check if Docker daemon listens on TCP (unusual, but possible)
for port in 2375 2376 4243; do
  timeout 2 bash -c "echo > /dev/tcp/localhost/$port" 2>/dev/null && echo "Docker API at $port" || true
done

# Check for any container runtime
command -v podman nerdctl containerd 2>/dev/null || echo "no container runtime"

# Check /proc/mounts for Docker socket mounts
grep docker /proc/mounts 2>/dev/null || echo ""
```

### 5. Identify what you CAN do

| If you have... | You can... |
|---|---|
| SSH to host (key authorized) | `ssh host "docker start sqlserver-onetag"` then restore |
| Docker socket mounted | Run Docker commands directly |
| Docker API via TCP | Remote Docker control |
| Neither | Ask user to start the container on the host |

## Unblocking Options

### Option A: Authorize SSH key

The container's public key needs to be added to the host user's `~/.ssh/authorized_keys`:

```
# On the host:
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB6IYsMQWQqO79S3BECiD3+QTHcg+h+3040W94DdDqwx hermes-container@0fa2ab323c3e" >> ~/.ssh/authorized_keys
```

After authorization, the agent can SSH in and start/manage Docker containers.

### Option B: Manual container start

```bash
docker start sqlserver-onetag
```

### Option C: Mount Docker socket into container

Restart the container with `-v /var/run/docker.sock:/var/run/docker.sock` and the Docker CLI will work.

## Key Learnings

- **System prompt invariants lie.** `network_mode: host`, SSH key paths, and user home directories all may be stale. Verify everything.
- **`/proc/net/tcp` gives clean port lists** even when `ss`/`netstat` aren't available.
- **Bash built-in `/dev/tcp`** is the most portable port checker — no `nc` needed.
- **SSH config may define host aliases** that point to the Docker gateway IP, not `localhost`.
- **No root ≠ no options.** Static binaries in `~/.local/bin` can add tools like `sqlcmd`, `docker` CLI, etc.
- **Known_hosts reveals previous connections** — it shows which hosts the container has talked to and their key fingerprints, which helps identify how the container was previously connected.
