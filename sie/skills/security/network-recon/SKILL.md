---
name: security/network-recon
description: Use when performing network reconnaissance — host discovery, port scanning, service enumeration, OS fingerprinting, and DNS enumeration. Covers Nmap, masscan, and DNS tools with exact commands and output interpretation.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, nmap, recon, scanning, network, enumeration, dns, masscan]
    related_skills:
      - security/workflow
      - security/web-app-scan
      - security/vuln-assessment
      - security/tool-setup
---

# Network Reconnaissance

## Overview

Network recon is the first active phase of any penetration test. This skill covers host discovery, port scanning, service/version detection, OS fingerprinting, and DNS enumeration using Nmap, masscan, and DNS tools. Every command includes exact flags and output interpretation guidance.

## When to Use

- You have an authorized target range and need to discover live hosts
- You need to enumerate open ports and running services
- You need to identify operating systems and service versions
- You need to perform DNS enumeration (zone transfers, record enumeration)
- You're building an attack surface map

**Don't use for:** web application scanning (use `security/web-app-scan`), vulnerability assessment (use `security/vuln-assessment`).

## Tool Availability Check

```bash
nmap --version
dnsrecon --version 2>/dev/null || echo "dnsrecon not installed"
masscan --version 2>/dev/null || echo "masscan not installed"
```

Install missing tools: `sudo apt install nmap dnsrecon masscan dnsutils`

## Phase 1: Host Discovery

### Nmap Ping Sweep (ICMP + SYN)
```bash
# Fast ping sweep — ICMP echo, timestamp, and SYN to ports 80/443
nmap -sn -PE -PP -PS80,443 -PA80,443 -oA host_discovery 192.168.1.0/24

# Skip port scan, treat all hosts as online (useful when ICMP is blocked)
nmap -Pn -sn -oA host_discovery 192.168.1.0/24
```

**Output interpretation:**
- `Host is up` → live host
- `Host seems down` → may still be up but blocking probes (use `-Pn` to force scan)
- Extract live hosts: `grep "Host is up" host_discovery.gnmap | awk '{print $2}' > live_hosts.txt`

### Parse Live Hosts
```bash
# From grepable output
grep "Status: Up" host_discovery.gnmap | cut -d' ' -f2 > live_hosts.txt

# From XML
grep 'addrtype="ipv4"' host_discovery.xml | grep -oP 'addr="\K[^"]+' > live_hosts.txt
```

## Phase 2: Port Scanning

### SYN Scan (Stealth — default, requires root)
```bash
# Top 1000 ports (default)
nmap -sS -T4 -oA syn_default target

# All 65535 ports, fast rate
nmap -sS -p- --min-rate 10000 -oA syn_full target

# Specific ports
nmap -sS -p 21,22,23,25,53,80,110,135,139,443,445,993,995,1433,3306,3389,5432,8080,8443 -oA syn_common target
```

### TCP Connect Scan (no root required)
```bash
nmap -sT -p- --min-rate 5000 -oA tcp_full target
```

### UDP Scan (slow but essential)
```bash
# Top 100 UDP ports
nmap -sU --top-ports 100 -T4 -oA udp_scan target

# Specific UDP ports (DNS, SNMP, TFTP, NTP)
nmap -sU -p 53,161,162,69,123 -oA udp_common target
```

### Combined Scan (recommended for full assessment)
```bash
# SYN + version + scripts + OS on all ports
nmap -sS -sV -sC -O -p- --min-rate 10000 -T4 -oA full_scan target

# Without OS detection (less accurate but faster)
nmap -sS -sV -sC -p- --min-rate 10000 -T4 -oA full_scan target
```

### Masscan (large ranges, very fast)
```bash
# Scan entire /16 on common ports
masscan -p1-65535 10.0.0.0/16 --rate=10000 -oL masscan_results.txt

# Specific ports with banner grabbing
masscan -p22,80,443,8080 10.0.0.0/8 --rate=5000 --banners -oL masscan_results.txt
```

**⚠️ Masscan is aggressive. Use `--rate` to control packet rate. Start with 1000, increase carefully.**

## Phase 3: Service & Version Detection

```bash
# Version detection on discovered ports
nmap -sV --version-intensity 5 -p 22,80,443,3306 -oA service_scan target

# Version detection with default NSE scripts
nmap -sV -sC -p 22,80,443,3306 -oA service_scripts target

# Aggressive version detection (all probes, slower but thorough)
nmap -sV --version-all -p 22,80,443 -oA service_deep target
```

**Version intensity levels:**
| Level | Speed | Accuracy |
|-------|-------|----------|
| 0 | Fastest | Least accurate |
| 5 | Balanced | Good (default) |
| 9 | Slowest | Most accurate |

## Phase 4: OS Fingerprinting

```bash
# OS detection (requires root + at least 1 open + 1 closed port)
nmap -O --osscan-guess -oA os_scan target

# OS + version + scripts + traceroute (aggressive)
nmap -A -T4 -p- -oA aggressive target
```

**OS detection accuracy notes:**
- Requires root privileges
- Needs at least 1 open and 1 closed port on the target
- `--osscan-guess` forces a guess even with low confidence
- Virtual machines and containers may fingerprint as the hypervisor

## Phase 5: NSE Script Scanning

```bash
# Vulnerability scanning scripts
nmap --script vuln -p 22,80,443,3306 -oA vuln_scan target

# Specific useful scripts
nmap --script http-enum -p 80,443,8080 -oA http_enum target
nmap --script smb-enum-shares,smb-enum-users -p 445 -oA smb_enum target
nmap --script ssl-enum-ciphers,ssl-cert -p 443 -oA ssl_scan target
nmap --script dns-zone-transfer -p 53 -oA dns_axfr target
nmap --script ftp-anon -p 21 -oA ftp_anon target

# Safe scripts only (no crash/exploit)
nmap --script "safe" -p- -oA safe_scripts target

# All scripts in a category
nmap --script "default,safe" -p 22,80,443 -oA default_safe target
```

**Key NSE script categories:**
| Category | Use |
|----------|-----|
| `vuln` | Vulnerability detection |
| `exploit` | Active exploitation (use with caution) |
| `safe` | Won't crash services |
| `default` | Run with `-sC` flag |
| `auth` | Authentication/credential checks |
| `discovery` | Additional discovery |
| `brute` | Brute force (use with caution) |

## Phase 6: DNS Enumeration

```bash
# DNS record enumeration
dig any target.com
dig mx target.com
dig ns target.com
dig txt target.com

# Zone transfer attempt
dig axfr @ns1.target.com target.com

# Reverse DNS lookup
dig -x 198.51.100.1

# DNS enumeration with dnsrecon
dnsrecon -d target.com -t std,brt,axfr -c dnsrecon_results.csv

# Subdomain brute force
dnsrecon -d target.com -D /usr/share/wordlists/dnsmap.txt -t brt

# DNS enumeration with dnsenum
dnsenum target.com --dnsserver ns1.target.com -o dnsenum_results.xml
```

## Output Management

### Always Save in All Formats
```bash
nmap -sS -sV -sC -p- -oA scan_results target
# Creates: scan_results.nmap (human-readable)
#          scan_results.gnmap (grepable)
#          scan_results.xml (XML for tools)
```

### Convert Output
```bash
# XML to HTML
xsltproc scan_results.xml -o scan_results.html

# Grepable to CSV
nmaptocsv -i scan_results.gnmap -o scan_results.csv -f ip-fqdn-port-protocol-service-version-os

# Extract open ports
grep "open" scan_results.gnmap | awk -F'[/ ]' '{for(i=1;i<=NF;i++) if($i=="open") print $(i-1)}' | sort -u
```

## Port State Reference

| State | Meaning |
|-------|---------|
| `open` | Service is accepting connections |
| `closed` | Port accessible but no service listening |
| `filtered` | Firewall/probe blocked, can't determine |
| `unfiltered` | Port accessible but can't determine open/closed (ACK scan only) |
| `open\|filtered` | Could be open or filtered (no response) |
| `closed\|filtered` | Could be closed or filtered |

## Evasion Techniques

```bash
# Fragment packets
nmap -f -sS -p- target

# Decoy scan (hide among fake sources)
nmap -D RND:10 -sS -p- target

# Idle scan (zombie host, very stealthy)
nmap -sI zombie_host -p- target

# Slow scan (evade IDS rate-based detection)
nmap -sS -T2 --max-rate 10 -p- target

# Source port manipulation (bypass firewall rules)
nmap -g 53 -sS -p- target

# Randomize host order
nmap --randomize-hosts -sS -p- -iL target_list.txt
```

**Timing templates:**
| Template | Speed | Use Case |
|----------|-------|----------|
| `-T0` (Paranoid) | Very slow | IDS evasion, max stealth |
| `-T1` (Sneaky) | Slow | Evade rate-based IDS |
| `-T2` | Polite | Production, avoid detection |
| `-T3` (Normal) | Default | Balanced |
| `-T4` (Aggressive) | Fast | CTF, lab, authorized |
| `-T5` (Insane) | Fastest | Very fast networks only |

## Common Pitfalls

1. **Forgetting `-oA`.** Always save in all 3 formats. You'll need XML for tool integration and grepable for quick parsing.
2. **Not running UDP scans.** Nmap defaults to TCP only. DNS (53), SNMP (161), and TFTP (69) are common UDP attack vectors.
3. **Using `-T4`/`-T5` on production.** Triggers IDS/IPS. Use `-T2` or `-T1` for production assessments.
4. **Not using `-Pn` when ICMP is blocked.** Some hosts block ping but have open ports. If ping sweep shows nothing, try `-Pn`.
5. **Running OS detection without root.** `sudo` is required for SYN scans, OS detection, and most NSE scripts.
6. **Scanning from your own IP.** Use a VPS or VPN for real assessments. Your home IP will be logged.
7. **Not randomizing host order.** Firewalls detect sequential scans. Use `--randomize-hosts` for large ranges.

## Verification Checklist

- [ ] Host discovery completed (ping sweep + `-Pn` if needed)
- [ ] TCP scan completed on all 65535 ports (not just top 1000)
- [ ] UDP scan completed on top 100 ports minimum
- [ ] Service/version detection run on all open ports
- [ ] NSE scripts run on relevant services
- [ ] DNS enumeration attempted (zone transfer, subdomain brute force)
- [ ] All output saved in all 3 formats (`-oA`)
- [ ] Results parsed into a structured host/port/service inventory
