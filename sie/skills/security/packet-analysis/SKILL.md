---
name: security/packet-analysis
description: Use when capturing and analyzing network traffic. Covers tcpdump and tshark for packet capture, protocol analysis, credential extraction from cleartext protocols, flow analysis, and forensic network investigation.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, packets, tcpdump, tshark, wireshark, network, forensics, capture]
    related_skills:
      - security/network-recon
      - security/workflow
      - security/forensics
      - security/tool-setup
---

# Packet Analysis

## Overview

Packet analysis is essential for network forensuds, detecting malicious traffic, extracting credentials from cleartext protocols, and understanding network behavior. This skill covers tcpdump for capture and tshark (CLI Wireshark) for analysis, with filters, field extraction, and investigative workflows.

## When to Use

- You need to capture network traffic for analysis
- You suspect cleartext credential transmission
- You need to analyze suspicious network behavior
- You're investigating a security incident
- You need to extract files or data from captured traffic
- You're performing network forensics

**Don't use for:** active network scanning (use `security/network-recon`), password attacks (use `security/password-attack`).

## Tool Availability Check

```bash
tcpdump --version
tshark --version 2>&1 | head -1
```

Install: `sudo apt install tcpdump tshark wireshark-common`

## Phase 1: Packet Capture with tcpdump

### Basic Capture
```bash
# Capture on default interface, save to file
tcpdump -i eth0 -w capture.pcap

# Capture on all interfaces
tcpdump -i any -w capture.pcap

# Capture with ring buffer (auto-rotate files)
tcpdump -i eth0 -C 100 -W 5 -w capture.pcap
# -C 100 = rotate at 100MB, -W 5 = keep 5 files

# Capture limited number of packets
tcpdump -i eth0 -c 1000 -w capture.pcap

# Capture with snap length (full packets)
tcpdump -i eth0 -s 0 -w capture.pcap

# Don't resolve hostnames or port names (faster, cleaner)
tcpdump -i eth0 -nn -w capture.pcap
```

### Capture Filters
```bash
# Host filter
tcpdump -i eth0 host 192.168.1.1 -w host.pcap

# Source/destination
tcpdump -i eth0 src host 192.168.1.1 -w src.pcap
tcpdump -i eth0 dst host 192.168.1.1 -w dst.pcap

# Port filter
tcpdump -i eth0 port 80 -w http.pcap
tcpdump -i eth0 portrange 8000-8080 -w web_ports.pcap

# Protocol filter
tcpdump -i eth0 tcp -w tcp_only.pcap
tcpdump -i eth0 udp -w udp_only.pcap
tcpdump -i eth0 icmp -w icmp.pcap
tcpdump -i eth0 arp -w arp.pcap

# Network range
tcpdump -i eth0 net 192.168.1.0/24 -w subnet.pcap

# Combined filters
tcpdump -i eth0 'host 192.168.1.1 and port 80' -w combined.pcap
tcpdump -i eth0 'host 192.168.1.1 and (port 80 or port 443)' -w web.pcap
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0' -w syn.pcap    # SYN packets only
tcpdump -i eth0 'tcp[tcpflags] & tcp-rst != 0' -w rst.pcap    # RST packets (port scans)

# Exclude noise (SSH to your management host)
tcpdump -i eth0 'not host 192.168.1.1 and not port 22' -w filtered.pcap
```

### Reading Captures
```bash
# Read pcap with ASCII output (see cleartext)
tcpdump -r capture.pcap -A

# Read with hex + ASCII
tcpdump -r capture.pcap -X

# Read with verbose output
tcpdump -r capture.pcap -vv

# Read with no DNS resolution (faster)
tcpdump -r capture.pcap -nn

# Read specific number of packets
tcpdump -r capture.pcap -c 100

# Apply display filter on read
tcpdump -r capture.pcap 'port 80'
```

## Phase 2: Analysis with tshark

### Basic Analysis
```bash
# Read pcap with default output
tshark -r capture.pcap

# Read with specific fields
tshark -r capture.pcap -T fields -e frame.number -e ip.src -e ip.dst -e tcp.port

# Summary statistics
tshark -r capture.pcap -q -z io,phs    # Protocol hierarchy statistics
tshark -r capture.pcap -q -z conv,tcp  # TCP conversations
tshark -r capture.pcap -q -z conv,udp  # UDP conversations
tshark -r capture.pcap -q -z endpoints,ip  # IP endpoints
tshark -r capture.pcap -q -z endpoints,tcp # TCP endpoints

# Top talkers
tshark -r capture.pcap -q -z endpoints,tcp | head -20
```

### HTTP Analysis
```bash
# Extract HTTP requests
tshark -r capture.pcap -Y http.request -T fields \
  -e ip.src -e http.host -e http.request.uri -e http.request.method

# Extract HTTP POST data (credentials!)
tshark -r capture.pcap -Y http.request.method==POST -T fields \
  -e ip.src -e http.host -e http.request.uri -e urlencoded-form.value

# Extract HTTP responses with status codes
tshark -r capture.pcap -Y http.response -T fields \
  -e ip.src -e http.response.code -e http.response.phrase

# Extract HTTP cookies
tshark -r capture.pcap -Y http.cookie -T fields \
  -e ip.src -e http.host -e http.cookie

# Extract User-Agent strings
tshark -r capture.pcap -Y http.request -T fields \
  -e http.user_agent | sort | uniq -c | sort -rn

# Extract all URLs from HTTP traffic
tshark -r capture.pcap -Y http.request -T fields -e http.host -e http.request.uri | \
  awk '{print "https://" $1 $2}'
```

### DNS Analysis
```bash
# Extract DNS queries
tshark -r capture.pcap -Y dns.qry.name -T fields \
  -e ip.src -e dns.qry.name | sort | uniq

# Extract DNS responses
tshark -r capture.pcap -Y dns.a -T fields \
  -e dns.qry.name -e dns.a

# Find DNS queries for suspicious domains
tshark -r capture.pcap -Y "dns.qry.name contains \"suspicious.com\"" -T fields \
  -e ip.src -e dns.qry.name -e frame.time

# Detect DNS tunneling (unusually long queries or high query volume)
tshark -r capture.pcap -Y dns.qry.name -T fields -e dns.qry.name | \
  awk '{print length($0), $0}' | sort -rn | head -20
```

### Credential Extraction
```bash
# Extract FTP credentials (cleartext)
tshark -r capture.pcap -Y "ftp.request.command==USER or ftp.request.command==PASS" -T fields \
  -e ip.src -e ftp.request.command -e ftp.request.arg

# Extract Telnet credentials (cleartext)
tshark -r capture.pcap -Y telnet -T fields \
  -e ip.src -e ip.dst -e telnet.data

# Extract SMTP credentials (AUTH LOGIN)
tshark -r capture.pcap -Y "smtp.req.command contains \"AUTH\"" -T fields \
  -e ip.src -e smtp.req.command

# Extract HTTP Basic Auth (Base64 encoded)
tshark -r capture.pcap -Y http.authorization -T fields \
  -e ip.src -e http.host -e http.authorization
```

### TLS/SSL Analysis
```bash
# Extract TLS handshakes (Client Hello)
tshark -r capture.pcap -Y tls.handshake.type==1 -T fields \
  -e ip.src -e ip.dst -e tls.handshake.extensions_server_name

# Extract TLS certificate information
tshark -r capture.pcap -Y tls.handshake.certificate -T fields \
  -e x509ce.subject -e x509ce.issuer -e x509ce.validity_not_before -e x509ce.validity_not_after

# Check TLS versions and cipher suites
tshark -r capture.pcap -Y tls.handshake -T fields \
  -e tls.handshake.version -e tls.handshake.ciphersuite

# Find weak TLS (SSLv3, TLS 1.0)
tshark -r capture.pcap -Y "tls.handshake.version == 0x0300 or tls.handshake.version == 0x0301" -T fields \
  -e ip.src -e ip.dst -e tls.handshake.version
```

### ARP Analysis
```bash
# ARP traffic analysis
tshark -r capture.pcap -Y arp -T fields \
  -e arp.src.hw_mac -e arp.src.proto_ipv4 -e arp.dst.hw_mac -e arp.dst.proto_ipv4

# Detect ARP spoofing (multiple IPs from one MAC)
tshark -r capture.pcap -Y arp -T fields -e arp.src.hw_mac -e arp.src.proto_ipv4 | \
  sort | uniq
```

### ICMP Analysis
```bash
# ICMP traffic (ping, traceroute, tunneling)
tshark -r capture.pcap -Y icmp -T fields \
  -e ip.src -e ip.dst -e icmp.type -e data.len -e data.data

# Large ICMP packets (potential tunneling)
tshark -r capture.pcap -Y "icmp and data.len > 64" -T fields \
  -e ip.src -e ip.dst -e data.len -e data.data
```

## Phase 3: Advanced Analysis

### Extract Files from Captures
```bash
# Extract all HTTP objects (files, images, etc.)
tshark -r capture.pcap --export-objects http,./extracted_files/

# Extract from SMB
tshark -r capture.pcap --export-objects smb,./extracted_smb/

# Using NetworkMiner CLI alternative
# (install NetworkMiner separately for GUI-based extraction)
```

### Flow Analysis
```bash
# Identify long-running connections (potential C2 beacons)
tshark -r capture.pcap -q -z conv,tcp | \
  awk '{if ($6 > 3600) print}'  # Connections over 1 hour

# Find port scans (many SYN packets to different ports)
tshark -r capture.pcap -Y "tcp.flags.syn==1 and tcp.flags.ack==0" \
  -T fields -e ip.src -e tcp.dstport | \
  sort | uniq -c | sort -rn | head -20

# Detect data exfiltration (large outbound transfers)
tshark -r capture.pcap -q -z conv,ip | \
  awk '{if ($10 > 1000000) print}'  # Transfers over 1MB
```

### Custom Output Format
```bash
# CSV output for spreadsheet analysis
tshark -r capture.pcap -T fields \
  -e frame.time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport \
  -e ip.proto -e frame.len -E header=y -E separator=, > capture.csv

# JSON output for programmatic analysis
tshark -r capture.pcap -T json > capture.json
tshark -r capture.pcap -T ek > capture_ek.json  # Elastic search format
```

## Phase 4: Live Analysis

```bash
# Live HTTP traffic on port 80
tcpdump -i eth0 -A 'port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'

# Live DNS queries
tcpdump -i eth0 -nn 'port 53'

# Live credentials on common cleartext ports
tcpdump -i eth0 -A -nn 'port 21 or port 23 or port 110 or port 143' | grep -iE 'user|pass|login|auth'

# Capture and analyze simultaneously with tshark
tshark -i eth0 -Y http.request -T fields -e http.host -e http.request.uri -l
```

## Display Filters Reference (tshark/Wireshark)

| Filter | Description |
|--------|-------------|
| `ip.addr == 10.0.0.1` | Source or dest IP |
| `ip.src == 10.0.0.1` | Source IP only |
| `ip.dst == 10.0.0.1` | Dest IP only |
| `tcp.port == 80` | TCP port (src or dst) |
| `tcp.dstport == 80` | TCP destination port |
| `http` | All HTTP traffic |
| `http.request` | HTTP requests only |
| `http.response` | HTTP responses only |
| `dns` | DNS traffic |
| `dns.qry.name` | DNS query name |
| `tls` | TLS/SSL traffic |
| `tls.handshake.extensions_server_name` | SNI (server name) |
| `icmp` | ICMP traffic |
| `arp` | ARP traffic |
| `tcp.flags.syn == 1` | SYN packets |
| `tcp.flags.rst == 1` | RST packets |
| `data` | Packets with payload |
| `frame.len > 1000` | Packets larger than 1000 bytes |

## Common Pitfalls

1. **Capturing without `-s 0`.** Default snap length truncates packets. Use `-s 0` for full packet capture.
2. **Not using `-nn`.** DNS resolution slows capture and adds noise. Always use `-nn` for captures.
3. **Running out of disk space.** Use ring buffer (`-C 100 -W 5`) for long captures. Monitor disk space.
4. **Capturing on wrong interface.** Check interfaces with `tcpdump -D` or `ip link show` before starting.
5. **Not capturing during the event.** Start capture before the activity you're investigating. You can't retroactively capture.
6. **Reading large pcaps without filters.** A 1GB pcap takes forever to read. Always apply display filters with `-Y`.
7. **Forgetting permissions.** tcpdump/tshark need root or `pcap` group membership. Use `sudo` or `setcap cap_net_raw+ep`.

## Verification Checklist

- [ ] Capture saved with full packet length (`-s 0`)
- [ ] Output saved to pcap file (not just terminal)
- [ ] Capture ring buffer configured for long-running captures
- [ ] Cleartext credentials extracted (FTP, Telnet, HTTP Basic)
- [ ] DNS queries analyzed for suspicious domains
- [ ] HTTP traffic analyzed for cookies, auth headers, POST data
- [ ] TLS versions and cipher suites checked
- [ ] ARP traffic checked for spoofing
- [ ] Large transfers and long connections identified
- [ ] Protocol hierarchy statistics reviewed
- [ ] Timeline of events documented
