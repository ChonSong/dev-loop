---
name: security/tool-setup
description: Use when setting up a security testing environment. Covers Kali Linux installation (VM, WSL2, Docker), essential tool installation, wordlist setup, Python tool installation, and environment verification.
version: 2.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, setup, kali, arch, installation, tools, wordlists, environment, ssh-proxy, container]
    related_skills:
      - security/workflow
      - security/network-recon
      - autonomous-ai-agents/hermes-agent
---

# Security Tool Setup

## Overview

This skill covers setting up a complete security testing environment, whether on a dedicated Kali Linux installation, a VM, WSL2, or Docker. Includes essential tool installation, wordlist setup, and environment verification.

## When to Use

- Setting up a new security testing environment
- Installing security tools on an existing system
- Verifying tool availability before an assessment
- Troubleshooting missing dependencies
- Running from a restricted container and need to install tools on the host via SSH

## Phase 0: Environment Detection

Before choosing an install strategy, probe what's available:

```bash
# Who are we?
whoami; id -u

# Can we sudo?
sudo -n true 2>/dev/null && echo "⬆️  sudo accessible" || echo "❌ no passwordless sudo"

# Can we SSH to the host?
ls /home/hermeswebui/.hermes/container_key 2>/dev/null && echo "✅ SSH key present" || echo "❌ no SSH key"
ls ~/.ssh/id_ed25519 2>/dev/null && echo "✅ SSH key at ~/.ssh"

# Do we have the Docker socket?
ls /var/run/docker.sock 2>/dev/null && echo "✅ Docker socket" || echo "❌ no Docker socket"

# What package manager?
which pacman 2>/dev/null && echo "📦 Arch Linux (pacman)"
which apt 2>/dev/null && echo "📦 Debian/Kali (apt)"
which apk 2>/dev/null && echo "📦 Alpine (apk)"

# Is filesystem writable?
test -w /usr/bin && echo "📁 writable /usr" || echo "🔒 readonly /usr (likely container)"
```

### Decision Tree

| sudo | SSH key | Docker socket | Use this strategy |
|------|---------|--------------|-------------------|
| ✅ | — | — | Direct install (Option 1 or 3) |
| ❌ | ✅ | — | SSH-proxy to host (Option 4) |
| ❌ | ❌ | ✅ | Docker exec as root, then install |
| ❌ | ❌ | ❌ | Cannot install — use skill as reference |

## Option 1: Full Kali Linux Installation

### Bare Metal / VM
```bash
# Download Kali from https://www.kali.org/get-kali/
# Choose: Kali Linux 64-Bit (for VM) or Kali Linux Installer (bare metal)

# VMware shortcut: download the pre-built VMware image
# VirtualBox: download the VBox image

# After installation, update everything
sudo apt update && sudo apt full-upgrade -y

# Install essential tools
sudo apt install -y \
  nmap \
  nikto \
  sqlmap \
  ffuf \
  gobuster \
  dirb \
  hydra \
  john \
  hashcat \
  aircrack-ng \
  tshark \
  tcpdump \
  wireshark \
  whatweb \
  wpscan \
  burpsuite \
  metasploit-framework \
  exploitdb \
  searchsploit \
  exiftool \
  binwalk \
  sleuthkit \
  autopsy \
  steghide \
  foremost \
  volatility3 \
  dnsrecon \
  dnsenum \
  whois \
  subfinder \
  amass \
  theharvester \
  massdns \
  dnsx \
  httpx \
  nuclei \
  wafw00f \
  wpscan \
  wifite \
  bettercap \
  hcxdumptool \
  hcxpcapngtool \
  tesseract-ocr \
  binutils \
  default-jdk \
  ruby \
  python3 \
  python3-pip \
  golang-go
```

### Python Tools
```bash
# Install Python-based security tools
pip3 install --upgrade pip
pip3 install \
  searchsploit \
  shodan \
  censys \
  pwntools \
  ropper \
  capstone \
  unicorn \
  requests \
  scapy \
  impacket \
  crackmapexec \
  bloodhound \
  certspotter \
  trufflehog

# Install Golang-based tools
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/tomnomnom/assetfinder@latest
go install github.com/tomnomnom/anew@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/tomnomnom/gf@latest
go install github.com/tomnomnom/waybackurls@latest
go install github.com/lc/gau/v2/cmd/gau@latest
```

## Option 2: WSL2 (Windows)

```bash
# Install WSL2 with Kali
wsl --install -d kali-linux

# Inside Kali WSL:
sudo apt update && sudo apt full-upgrade -y
# Then follow the same install commands as above

# Note: WSL2 doesn't support wireless adapter access
# Wireless auditing requires native Linux or VM with USB passthrough
```

## Option 3: Docker

```bash
# Pull Kali Linux Docker image
docker pull kalilinux/kali-rolling

# Run with persistent volume
docker run -it --rm \
  --name kali \
  --network host \
  -v kali-data:/root \
  kalilinux/kali-rolling /bin/bash

# Inside container:
apt update && apt full-upgrade -y
# Install tools as needed

# Save container state
docker commit kali kali-custom:latest
```

## Option 4: Arch Linux (Pacman)

```bash
# Essential security tools on Arch
sudo pacman -S --needed nmap nikto sqlmap ffuf gobuster dirb hydra \
  john hashcat aircrack-ng wireshark-cli tcpdump whatweb wpscan \
  exploitdb metasploit masscan dnsutils jq exiftool binwalk \
  sleuthkit steghide foremost whois dnsrecon subfinder amass \
  wafw00f hcxdumptool python python-pip

# Bettercap from AUR (if yay/paru installed)
sudo pacman -S --needed bettercap

# Seclists from AUR (or clone directly)
git clone https://github.com/danielmiessler/SecLists.git /opt/seclists

# Wordlists
sudo pacman -S --needed rockyou         # Arch package
sudo gunzip /usr/share/wordlists/rockyou.txt.gz
```

**Arch-specific notes:**
- Package names may differ from Debian/Kali (e.g., `wireshark-cli` not `tshark`)
- AUR tools need an AUR helper (yay/paru) or manual build
- `metasploit` package exists in community repo, not just AUR
- The `check_env.sh` script can use `which` instead of `apt-cache`

## Option 5: SSH Proxy Install (Container → Host)

Use when the agent runs in an unprivileged container but has SSH access to the host:

### Prerequisites Check
```bash
# Find the SSH key path
SSH_KEY="/home/hermeswebui/.hermes/container_key"
test -f "$SSH_KEY" || SSH_KEY=~/.ssh/id_ed25519

# Test connection to host
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
  sean@172.19.0.1 "echo host reachable"

# Check host package manager
ssh -i "$SSH_KEY" sean@172.19.0.1 "which pacman; which apt; which sudo"
```

### Single Tool Install
```bash
# Install a tool on the host via SSH
SSH_KEY="/home/hermeswebui/.hermes/container_key"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no sean@172.19.0.1 \
  "sudo pacman -S --noconfirm nmap"

# Verify it's now available through SSH
ssh -i "$SSH_KEY" sean@172.19.0.1 "nmap --version"
```

### Using Tools via SSH Proxy
Once installed, run the tool through the SSH proxy:
```bash
# Instead of: nmap -sV target
# Run: ssh <host> "nmap -sV target"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no sean@172.19.0.1 \
  "nmap -sV -p 22,80,443 192.168.1.1"

# Copy results back
ssh -i "$SSH_KEY" sean@172.19.0.1 \
  "nmap -sV -p- -oA scan_output target && cat scan_output.nmap" \
  > /tmp/nmap_results.txt
```

### Full Suite Install
```bash
# Install common security tools on an Arch host
ssh -i "$SSH_KEY" sean@172.19.0.1 << 'REMOTE'
  sudo pacman -S --needed nmap masscan dnsutils curl jq
  # Verify
  nmap --version | head -1
REMOTE
```

### Running Tools Through the Kali Container
Once the container exists (see Option 6), run tools with:
```bash
docker exec kali-tools <command>
```
Combined with SSH proxy:
```bash
ssh -i "$SSH_KEY" sean@172.19.0.1 "docker exec kali-tools nmap -sV target"
```

For long-running commands, pipe output back:
```bash
ssh -i "$SSH_KEY" sean@172.19.0.1 \
  "docker exec kali-tools nmap -sV -p- -oA /workspace/scan_output target \
   && cat /workspace/scan_output.nmap"
```

### Finding the Host
| Context | Connect to | Key path |
|---------|-----------|----------|
| Docker with bridge network | `172.19.0.1` (gateway) | `/home/hermeswebui/.hermes/container_key` |
| Docker host network | `localhost` | `/home/hermeswebui/.hermes/container_key` |
| Known LAN IP | `192.168.X.X` | Key depends on setup |

## Option 6: Persistent Kali Container (Docker)

Use when you're in a constrained container (no root, read-only /usr) but have Docker access on the host via SSH. This creates a long-running Kali container that becomes your security tool execution environment.

### Create the Container
```bash
# Pull the image
docker pull kalilinux/kali-rolling

# Create persistent container
docker rm -f kali-tools 2>/dev/null
docker run -d \
  --name kali-tools \
  --network host \
  --cap-add NET_RAW --cap-add NET_ADMIN \
  -v /path/to/workspace:/workspace \
  -v /path/to/downloads:/downloads:ro \
  kalilinux/kali-rolling sleep infinity
```

**Critical flags:**
- `--network host` — share host network so Nmap sees the same interfaces
- `--cap-add NET_RAW` — required for Nmap SYN scans (`-sS`). Without this, Nmap binary hangs: `/usr/lib/nmap/nmap: Operation not permitted`
- `--cap-add NET_ADMIN` — required for Nmap OS detection and certain NSE scripts
- `-v /workspace:/workspace` — mount workspace so scan outputs persist on the host

### Install Tools Inside the Container
```bash
# Enter the container
docker exec -it kali-tools bash

# Inside: update + install core tools
apt-get update && apt-get install -y \
  nmap ffuf sqlmap hydra john hashcat \
  nikto whatweb wpscan gobuster dirb \
  dnsrecon wafw00f exploitdb \
  tcpdump dnsutils whois netcat-openbsd \
  curl wget binwalk steghide foremost seclists

# Install additional tools as needed
apt-get install -y aircrack-ng wireshark
```

### Tool Access Pattern
```bash
# Direct command
docker exec kali-tools nmap -sV -p 80,443 target

# With output to mounted workspace
docker exec kali-tools bash -c \
  "nmap -sV -p- -oA /workspace/scan_results target"

# Interactive shell
docker exec -it kali-tools bash
```

### Verify Tools
```bash
for tool in nmap ffuf sqlmap hydra john hashcat nikto whatweb wpscan gobuster dnsrecon; do
  echo -n "$tool: "
  docker exec kali-tools which "$tool" 2>/dev/null && echo "✅" || echo "❌"
done
```

### SSH Proxy Pattern (from container with SSH key)
```bash
SSH_KEY="/home/hermeswebui/.hermes/container_key"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no sean@172.19.0.1 \
  "docker exec kali-tools nmap -sV target"
```

### Recreate After Host Reboot
The container stops when the host reboots. Restart:
```bash
docker start kali-tools
```
No re-install needed — tools persist in the committed image layer. Add `--restart unless-stopped` at creation for auto-restart.

> 📄 Full setup transcript with exact commands at `references/docker-kali-container-setup.md`

## Wordlist Setup

```bash
# Install SecLists (comprehensive wordlist collection)
sudo apt install seclists
# Installs to: /usr/share/seclists/

# Or clone from GitHub for latest version
git clone https://github.com/danielmiessler/SecLists.git /opt/seclists
ln -s /opt/seclists /usr/share/seclists

# RockYou wordlist (essential for password attacks)
sudo gunzip /usr/share/wordlists/rockyou.txt.gz
# Verify: wc -l /usr/share/wordlists/rockyou.txt (should be ~14M lines)

# Verify wordlist paths
ls -la /usr/share/wordlists/
ls -la /usr/share/seclists/Discovery/Web-Content/
ls -la /usr/share/seclists/Discovery/DNS/
ls -la /usr/share/seclists/Passwords/

# Directory fuzzing wordlists
ls /usr/share/seclists/Discovery/Web-Content/
# key files:
#   raft-medium-directories.txt     (~220K entries)
#   raft-large-directories.txt      (~624K entries)
#   directory-list-2.3-medium.txt   (~220K entries)
#   directory-list-2.3-large.txt    (~1.8M entries)

# DNS subdomain wordlists
ls /usr/share/seclists/Discovery/DNS/
# key files:
#   subdomains-top1million-5000.txt  (5K entries, good for quick scan)
#   subdomains-top1million-110000.txt (110K entries, thorough)

# Password wordlists
ls /usr/share/seclists/Passwords/
# key files:
#   10k-most-common.txt
#   rockyou.txt (after gunzipping)
#   darkweb2017-top10000.txt
```

## Hashcat Rules Setup

```bash
# Hashcat rules are built-in
ls /usr/share/hashcat/rules/
# Key rules:
#   best64.rule        (64 transformations, fast)
#   dive.rule          (35K transformations, thorough)
#   rockyou-30000.rule (30K transformations)
#   OneRuleToRuleThemAll.rule (community compendium)

# Test rule effectiveness
hashcat -r rules/best64.rule --stdout wordlist.txt | wc -l
```

## Metasploit Database Setup

```bash
# Initialize PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Initialize Metasploit database
sudo msfdb init

# Verify
msfconsole
msf6> db_status
# Should show: "Connected to msf"

# If connection issues:
msfdb reinit
```

## API Key Setup

```bash
# WPScan (WordPress vulnerability data)
# Register at https://wpscan.com/api (free tier: 25/day)
# Set in ~/.wpscan/scan.yml:
echo "api_token: YOUR_API_TOKEN" > ~/.wpscan/scan.yml

# Shodan (Internet-wide scanning)
# Register at https://account.shodan.io (free tier: 100 queries)
shodan init YOUR_API_KEY

# Censys (Internet-wide scanning)
# Register at https://search.censys.io/account
# Set environment:
export CENSYS_API_ID="YOUR_ID"
export CENSYS_API_SECRET="YOUR_SECRET"

# NIST NVD API (higher rate limits)
# Register at https://nvd.nist.gov/developers/request-an-api-key
export NVD_API_KEY="YOUR_KEY"
```

## Environment Verification Script

```bash
#!/bin/bash
# save as verify_env.sh and run: bash verify_env.sh

check_tool() {
  if command -v "$1" &>/dev/null; then
    echo "✅ $1: $(command -v $1)"
  else
    echo "❌ $1: NOT FOUND"
  fi
  echo "   Install: $2"
}

get_install_cmd() {
  if command -v pacman &>/dev/null; then
    echo "sudo pacman -S $1"
  elif command -v apt &>/dev/null; then
    echo "sudo apt install $1"
  else
    echo "install $1 manually"
  fi
}

echo "=== Security Environment Verification ==="
echo ""

echo "--- Network Tools ---"
check_tool nmap "$(get_install_cmd nmap)"
check_tool masscan "$(get_install_cmd masscan)"
check_tool tcpdump "$(get_install_cmd tcpdump)"
check_tool tshark "$(get_install_cmd wireshark-cli)"
check_tool nikto "$(get_install_cmd nikto)"
check_tool whatweb "$(get_install_cmd whatweb)"

echo "--- Web Tools ---"
check_tool ffuf "$(get_install_cmd ffuf)"
check_tool gobuster "$(get_install_cmd gobuster)"
check_tool sqlmap "$(get_install_cmd sqlmap)"
check_tool wpscan "$(get_install_cmd wpscan)"
check_tool nuclei "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"

echo "--- Password Tools ---"
check_tool hydra "$(get_install_cmd hydra)"
check_tool john "$(get_install_cmd john)"
check_tool hashcat "$(get_install_cmd hashcat)"

check_tool "python3 -c 'import cvss'" "pip3 install cvss"

check_tool searchsploit "$(get_install_cmd exploitdb)"
check_tool msfconsole "$(get_install_cmd metasploit-framework)"
check_tool msfvenom "$(get_install_cmd metasploit-framework)"

echo "--- Forensics ---"
check_tool volatility3 "$(get_install_cmd volatility3)"
check_tool fls "$(get_install_cmd sleuthkit)"
check_tool autopsy "$(get_install_cmd autopsy)"
check_tool exiftool "$(get_install_cmd exiftool)"
check_tool binwalk "$(get_install_cmd binwalk)"

echo "--- Wordlists ---"
check_wordlist() {
  if [ -f "$1" ]; then
    lines=$(wc -l < "$1")
    echo "✅ $1 ($lines lines)"
  else
    echo "❌ $1: NOT FOUND"
  fi
}

check_wordlist "/usr/share/wordlists/rockyou.txt"
check_wordlist "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt"
check_wordlist "/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt"

echo ""
echo "=== Verification Complete ==="
```

## Common Pitfalls

1. **Not updating after install.** Kali needs `apt full-upgrade` immediately. Many tools have known bugs in the base image.
2. **Forgetting to decompress rockyou.txt.** It's gzipped by default. `gunzip /usr/share/wordlists/rockyou.txt.gz`.
3. **Not initializing the Metasploit database.** Without `msfdb init`, you can't save findings, hosts, or credentials across sessions.
4. **Installing tools without checking for existing ones.** Check first with `which toolname` to avoid conflicts.
5. **Not setting API keys.** Many tools (WPScan, Shodan, NVD) work better with API keys. Register for free tiers before you need them.
6. **WSL2 for wireless.** WSL2 doesn't expose USB devices (including wireless adapters). Use a VM with USB passthrough for wireless auditing.
7. **Insufficient disk space.** SecLists alone is ~500MB. Full Kali with all tools needs 40GB+. Plan accordingly.
8. **Assuming apt on every Linux.** The host may run Arch (pacman), Alpine (apk), or Fedora (dnf). Always detect the package manager first with `which pacman apt apk` before suggesting install commands. Running `apt install` on an Arch host fails silently (command not found).
9. **SSH proxy: wrong key path.** Inside the Hermes container, the SSH key is at `/home/hermeswebui/.hermes/container_key`, NOT `~/.ssh/id_ed25519`. Verify the path exists before attempting SSH.
10. **SSH proxy: wrong host IP.** In a Docker bridge network, the host is at the gateway IP (`172.19.0.1`), not `localhost`. In host network mode, use `localhost`. For LAN, use the actual network IP of the host machine. Test with a simple `echo` before running install commands.
11. **SSH proxy: no passwordless sudo on host.** The remote user must have `NOPASSWD` in sudoers. Without it, `sudo` prompts for a password interactively and the install hangs. Verify with `sudo -n true` on the host first.
12. **SSH proxy: host package names differ from Kali.** `wireshark-cli` on Arch vs `tshark` on Debian. `metasploit` on Arch vs `metasploit-framework` on Debian. Always check the host's package manager before suggesting tool names.
13. **Docker Nmap: missing `--cap-add NET_RAW`.** Nmap SYN scans (`-sS`) fail with `Operation not permitted` on the binary if the container lacks `NET_RAW` capability. Use `-sT` (TCP connect) as fallback, or recreate the container with `--cap-add NET_RAW`.
14. **Docker Nmap: missing `--cap-add NET_ADMIN`.** OS detection and some NSE scripts that manipulate raw sockets need `NET_ADMIN`. Without it, they silently fail or return inaccurate results.
15. **Persistent container stops on host reboot.** The `sleep infinity` container exits when the host restarts. Run `docker start kali-tools` to bring it back. Tools persist across restarts. Add `--restart unless-stopped` at creation for auto-restart.
16. **Kali apt installs time out in one shot.** The full security tools suite takes 5+ minutes to install via apt. Install in smaller groups (network tools first, web tools second, etc.) or increase the SSH/docker exec timeout to 600s.

## Verification Checklist

- [ ] Kali Linux updated (`apt full-upgrade`)
- [ ] Core tools installed and verified (`nmap`, `ffuf`, `sqlmap`, `nikto`, `hydra`)
- [ ] Wordlists decompressed and available (rockyou.txt, SecLists)
- [ ] Metasploit database initialized (`msfdb init` + `db_status`)
- [ ] API keys configured (WPScan, Shodan, Censys, NVD)
- [ ] Python tools installed (`shodan`, `censys`, `impacket`)
- [ ] Golang tools installed (`subfinder`, `httpx`, `nuclei`)
- [ ] GPU drivers installed (for Hashcat)
- [ ] Disk space sufficient (40GB+ recommended)
- [ ] Wireless adapter recognized (if doing wireless testing)
