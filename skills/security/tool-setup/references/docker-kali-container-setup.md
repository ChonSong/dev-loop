# Docker Kali Container — Setup Transcript (2026-06-09)

## Context

Running inside a Hermes WebUI container (Docker, unprivileged, read-only `/usr`).
Docker socket not available inside the container, but Docker exists on the host
and is accessible via SSH proxy with the container's SSH key.

## Host Environment

| Property | Value |
|----------|-------|
| Host distro | Arch Linux |
| Host package manager | `pacman` |
| Host user | `sean` (uid 1000, has sudo + docker group) |
| Host LAN IP | `192.168.1.130` |
| Container → Host IP | `172.19.0.1` (Docker bridge gateway) |
| SSH key path (container) | `/home/hermeswebui/.hermes/container_key` |
| SSH key owner | `hermeswebui` inside container |

## Exact Setup Sequence

### 1. Pull the Image
```bash
docker pull kalilinux/kali-rolling
```

### 2. Create the Container
```bash
docker rm -f kali-tools 2>/dev/null
docker run -d \
  --name kali-tools \
  --network host \
  --cap-add NET_RAW \
  --cap-add NET_ADMIN \
  -v /home/sean/workspace:/workspace \
  -v /home/sean/Downloads:/downloads:ro \
  kalilinux/kali-rolling \
  sleep infinity
```

**Critical flags:**
- `--network host` — container shares host networking; Nmap sees host interfaces
- `--cap-add NET_RAW` — **required** for Nmap SYN scans (`-sS`). Without it, the
  Nmap binary has capabilities set (`setcap cap_net_raw+ep`) but Docker blocks
  them at the container level → `/usr/lib/nmap/nmap: Operation not permitted`
- `--cap-add NET_ADMIN` — required for OS detection and some NSE scripts
- `-v /workspace:/workspace` — scan outputs persist on the host filesystem

### 3. Install Core Tools
```bash
docker exec kali-tools bash -c \
  'apt-get update && apt-get install -y \
    nmap ffuf sqlmap hydra john hashcat \
    nikto whatweb wpscan gobuster dirb \
    dnsrecon wafw00f exploitdb \
    tcpdump dnsutils whois netcat-openbsd \
    curl wget binwalk steghide foremost seclists'
```

**Pitfall:** Don't install everything in one shot — `apt-get install` of all tools
at once times out (takes 5+ min). If you hit a timeout, check progress with:
```bash
docker exec kali-tools bash -c 'while ps aux | grep -q "[a]pt-get"; do sleep 10; done; echo DONE'
```

Then verify what was actually installed:
```bash
docker exec kali-tools bash -c 'for t in nmap ffuf sqlmap hydra john hashcat nikto whatweb wpscan gobuster tcpdump dig whois nc; do which $t 2>/dev/null && echo "$t: OK" || echo "$t: MISSING"; done'
```

Install missing tools in smaller batches targeting only what's missing:
```bash
docker exec kali-tools apt-get install -y <tool1> <tool2> ...
```

### 4. Verify Nmap Works
```bash
docker exec kali-tools nmap --version
# Expected: Nmap version 7.99 ( https://nmap.org )
# NOT:      /usr/lib/nmap/nmap: Operation not permitted
```

If Nmap gives `Operation not permitted`:
1. **Check container capabilities:** `docker inspect kali-tools | grep CapAdd`
2. **Fix:** recreate container with `--cap-add NET_RAW`
3. **Alternative (no raw sockets):** use `-sT` (TCP connect) instead of `-sS` (SYN)

### 5. Verification — All Tools
```bash
# Network
docker exec kali-tools nmap --version | head -1
docker exec kali-tools nc -h 2>&1 | head -1
docker exec kali-tools dig -h 2>&1 | head -1
docker exec kali-tools tcpdump --version | head -1

# Web
docker exec kali-tools ffuf -V
docker exec kali-tools gobuster version
docker exec kali-tools sqlmap --version | head -1
docker exec kali-tools nikto -Version | head -1
docker exec kali-tools whatweb --version | head -1

# Password
docker exec kali-tools hydra --version | head -1
docker exec kali-tools john --version | head -1
docker exec kali-tools hashcat --version | head -1

# Forensics
docker exec kali-tools binwalk --version | head -1
docker exec kali-tools steghide version | head -1

# Wordlists
docker exec kali-tools ls /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt
```

## Usage Patterns

### SSH Proxy (from Hermes container)
```bash
SSH_KEY="/home/hermeswebui/.hermes/container_key"
HOST="sean@172.19.0.1"

# Single command
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$HOST" \
  "docker exec kali-tools nmap -sV -p 22,80,443 192.168.1.1"

# Scan with output to workspace (persists on host)
ssh -i "$SSH_KEY" "$HOST" \
  "docker exec kali-tools bash -c \
    'nmap -sV -p- -oA /workspace/scan_results 192.168.1.1'"

# Live interactive shell
ssh -t -i "$SSH_KEY" "$HOST" \
  "docker exec -it kali-tools bash"
```

### Inside Kali Container Directly
```bash
# Attach to container
docker exec -it kali-tools bash

# Run a quick scan
docker exec kali-tools nmap -sn 192.168.1.0/24

# Long full-port scan on host
docker exec kali-tools nmap -sS -p- --min-rate 5000 -oA /workspace/host_full_scan 192.168.1.130
```

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| `Operation not permitted` on Nmap | Missing `NET_RAW` capability | Recreate with `--cap-add NET_RAW` |
| `apt-get` locked / timed out | Previous install still running inside container | Wait: `while ps aux | grep -q "[a]pt"; do sleep 10; done` |
| Container gone after reboot | `sleep infinity` exits on host restart | `docker start kali-tools` or add `--restart unless-stopped` |
| `command not found` on tool | Install didn't complete | Check with `which`, install missing ones in small batches |
| SecLists not at /usr/share/seclists/ | Missing from install | Install `seclists` package or clone from GitHub |
| SSH key not found | Wrong path | Key is at `/home/hermeswebui/.hermes/container_key` NOT `~/.ssh/` or `/opt/data/` |
| Host not reachable | Wrong IP | Docker bridge = `172.19.0.1`. Host network = `localhost`. LAN = actual IP |
| Nmap UDP scans silent | UDP needs root + raw sockets | Container has both (with capabilities). Slow scans are normal |

## Committed State

Tools installed and verified (2026-06-09):

| Category | Tools |
|----------|-------|
| Network | nmap 7.99, tcpdump 4.99.6, dig, whois 5.6.6, nc |
| Web | ffuf 2.1.0, sqlmap 1.10.5, nikto 2.6.0, whatweb 0.6.4, wpscan, gobuster 3.8.2, dirb 2.22, wafw00f |
| Password | hydra 9.7, john, hashcat 7.1.2 |
| Recon | dnsrecon 1.3.1, searchsploit |
| Forensics | binwalk, steghide 0.5.1, foremost 1.5.7 |
| Wordlists | SecLists 1.9G at /usr/share/seclists/ |
| Container image | `kalilinux/kali-rolling:latest` |
| Host package manager | pacman (Arch) — not apt |
