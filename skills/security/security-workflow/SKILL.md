---
name: security-workflow
description: Use when planning or executing any penetration test, security audit, or CTF challenge. Provides the master methodology framework, phase-gated workflow, and tool routing for all security testing tasks.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, pentest, methodology, workflow, audit, recon, exploit, reporting]
    related_skills:
      - security/network-recon
      - security/web-app-scan
      - security/directory-fuzz
      - security/password-attack
      - security/vuln-assessment
      - security/exploit-basics
      - security/report-generator
      - security/legal-checklist
      - security/tool-setup
---

# Security Workflow — Master Orchestrator

## Overview

This is the **entry point** for all security testing tasks. It provides a phase-gated methodology covering the full lifecycle: authorization → recon → enumeration → vulnerability assessment → exploitation → post-exploitation → reporting. Every other security skill plugs into this workflow.

Based on PTES (Penetration Testing Execution Standard) and OSSTMM frameworks, adapted for practical use with Kali Linux tools.

## When to Use

- Starting any penetration test, security audit, or CTF challenge
- User asks "how do I test X for security issues"
- You need to decide which security tools/skills to apply next
- You need to structure findings into a report

**Don't use for:** individual tool-specific tasks (use the dedicated skill for that tool).

## Phase 0: Authorization & Scope (MANDATORY FIRST STEP)

> **⚠️ Never skip this phase. Testing without authorization is illegal in most jurisdictions.**

### Authorization Checklist
- [ ] Written authorization obtained (signed by system owner)
- [ ] Scope document defines:
  - ✅ In-scope targets (IP ranges, domains, applications)
  - ❌ Out-of-scope targets (production systems, third-party services, etc.)
  - Testing window (dates, hours — e.g., weekends only)
  - Emergency contact (phone number for immediate stop)
  - Authorized techniques (or explicit exclusions like "no DoS")
- [ ] Rules of Engagement (RoE) document reviewed and agreed
- [ ] Data handling requirements defined (encryption, retention period, destruction)
- [ ] Legal jurisdiction considerations noted (CFAA, Computer Misuse Act, etc.)

### Scope Definition Template
```
Target:        example.com (198.51.100.0/24)
Excluded:      api.production.example.com, *.third-party.com
Window:        2026-07-10 00:00 to 2026-07-12 23:59 UTC
Contacts:      Jane Doe, +1-555-0123 (emergency stop)
Techniques:    All except DoS/DDoS
Data handling: Encrypt findings at rest, destroy after 30 days
```

## Phase 1: Reconnaissance

### 1A — Passive Reconnaissance (OSINT)
Use: `security/osint` skill
- WHOIS, DNS records, subdomain enumeration
- Certificate transparency logs (crt.sh)
- Search engine dorking, Wayback Machine
- GitHub/repository reconnaissance
- Shodan/Censys queries
- **Output:** Target profile document (domains, IPs, tech stack, employees)

### 1B — Active Reconnaissance
Use: `security/network-recon` skill
- Host discovery (Nmap ping sweeps)
- Port scanning (SYN, service version, OS detection)
- DNS zone transfer attempts
- **Output:** Live host list with open ports and services

### Recon Phase Gate
Before moving to enumeration, you should have:
- [ ] List of all live hosts and their IPs
- [ ] List of open ports per host
- [ ] Identified services and versions
- [ ] Network diagram (even rough)
- [ ] Technology stack inventory

## Phase 2: Enumeration

### 2A — Web Application Enumeration
Use: `security/web-app-scan` and `security/directory-fuzz` skills
- Web server fingerprinting (WhatWeb, httpx)
- Directory/file discovery (ffuf, gobuster)
- Technology-specific scanning (WPScan for WordPress, etc.)
- Manual browsing and form mapping
- Nikto vulnerability scanning

### 2B — Service Enumeration
- SMB enumeration (smbclient, enum4linux, nmap NSE)
- SNMP enumeration (snmpwalk, onesixtyone)
- NFS showmount (showmount -e target)
- LDAP enumeration (ldapsearch)
- SMTP user enumeration (smtp-user-enum)

### Enumeration Phase Gate
Before moving to vulnerability assessment, you should have:
- [ ] Complete attack surface map
- [ ] All web endpoints catalogued
- [ ] All network services and their banners
- [ ] Usernames/accounts discovered (if any)
- [ ] Potential entry points identified

## Phase 3: Vulnerability Assessment

Use: `security/vuln-assessment` skill

- Match discovered services/versions against known CVEs
- Run vulnerability scanners (Nmap NSE `--script vuln`, Nikto)
- Manual verification of findings (no blind trust in scanners)
- CVSS scoring for each finding
- Prioritize by: exploitability × impact × asset criticality
- **Output:** Prioritized vulnerability list with evidence

### Vuln Assessment Phase Gate
- [ ] All services checked against CVE databases
- [ ] False positives eliminated through manual verification
- [ ] Each finding has CVSS score and evidence
- [ ] Findings prioritized for exploitation phase

## Phase 4: Exploitation

Use: `security/exploit-basics` skill

- Attempt exploitation of prioritized vulnerabilities
- Start with highest-confidence, lowest-risk exploits
- Document every attempt (success and failure)
- Capture evidence: screenshots, shell access proof, data access proof
- **Never** run destructive exploits without explicit authorization

### Exploitation Techniques (in order of preference)
1. **Public exploit** (SearchSploit, Metasploit) — understand it before running
2. **Credential-based** (use `security/password-attack` skill)
3. **Configuration abuse** (default creds, misconfigurations)
4. **Manual exploitation** (SQL injection, command injection, etc.)

### Exploitation Phase Gate
- [ ] All high/critical findings have exploitation attempts documented
- [ ] Evidence captured for each successful exploit
- [ ] Post-exploitation assessment completed for compromised hosts

## Phase 5: Post-Exploitation

- Privilege escalation assessment (linPEAS, winPEAS, manual checks)
- Lateral movement potential assessment
- Data access evaluation (what data is accessible from compromised position)
- Persistence mechanism identification
- **Document everything** — this is the most evidence-sensitive phase

## Phase 6: Reporting

Use: `security/report-generator` skill

- Executive summary (non-technical, business impact focus)
- Technical findings (reproducible, evidence-backed)
- Risk ratings (Critical / High / Medium / Low / Informational)
- Remediation roadmap (prioritized by risk + effort)
- Appendices (tool versions, scope, methodology)

## Tool Routing Table

| Task | Skill |
|------|-------|
| Overall methodology | `security/workflow` (this skill) |
| Network scanning | `security/network-recon` |
| Web app scanning | `security/web-app-scan` |
| Directory fuzzing | `security/directory-fuzz` |
| Password attacks | `security/password-attack` |
| Packet analysis | `security/packet-analysis` |
| OSINT / passive recon | `security/osint` |
| Vulnerability assessment | `security/vuln-assessment` |
| Exploitation | `security/exploit-basics` |
| Wireless auditing | `security/wireless-audit` |
| Forensics | `security/forensics` |
| Report writing | `security/report-generator` |
| Tool installation | `security/tool-setup` |
| Legal/authorization | `security/legal-checklist` |
| Code security review | `security-review` |
| Static analysis | `trailofbits/static-analysis` |
| Audit context building | `trailofbits/audit-context-building` |

## Common Pitfalls

1. **Skipping authorization.** Even on your own lab, document your scope. It builds good habits and protects you legally.
2. **Jumping to exploitation without recon.** You'll miss attack surface and waste time on the wrong targets.
3. **Trusting scanner output blindly.** Every automated finding needs manual verification. False positives waste everyone's time.
4. **Not documenting as you go.** Memory is unreliable. Screenshot everything, save all tool output, timestamp your findings.
5. **Scanning too aggressively on production.** Use rate limiting, scan during maintenance windows, and always have the emergency contact ready.
6. **Forgetting UDP.** Nmap defaults to TCP. Run `-sU` separately — DNS, SNMP, and TFTP are common UDP attack vectors.
7. **Not saving output in multiple formats.** Always use `-oA` (all formats) with Nmap. XML for parsing, grepable for grep, normal for reading.

## Verification Checklist

- [ ] Authorization and scope documented before any testing
- [ ] All tool output saved with timestamps
- [ ] Screenshots captured for all significant findings
- [ ] Every vulnerability has manual verification (not just scanner output)
- [ ] All findings include CVSS scores
- [ ] Report includes both executive summary and technical details
- [ ] Remediation recommendations are actionable and prioritized
- [ ] Evidence package is organized and reproducible
