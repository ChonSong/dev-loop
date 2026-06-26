---
name: security/vuln-assessment
description: Use when assessing and prioritizing vulnerabilities. Covers CVE matching with SearchExploit, CVSS v3.1 scoring, false positive verification, vulnerability prioritization matrices, and structured finding documentation.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, vulnerability, cve, cvss, assessment, prioritization, searchsploit]
    related_skills:
      - security/workflow
      - security/network-recon
      - security/web-app-scan
      - security/exploit-basics
      - security/report-generator
---

# Vulnerability Assessment

## Overview

Vulnerability assessment is the process of identifying, classifying, and prioritizing security weaknesses discovered during reconnaissance and scanning. This skill covers CVE matching, CVSS scoring, false positive elimination, risk prioritization, and structured finding documentation.

## When to Use

- You've completed scanning and have a list of discovered services/versions
- You need to match discovered services against known CVEs
- You need to prioritize findings for the exploitation phase
- You need to document vulnerabilities with CVSS scores
- You're triaging scanner output (Nmap NSE, Nikto) for false positives

**Don't use for:** exploitation (use `security/exploit-basics`), report writing (use `security/report-generator`).

## Tool Availability Check

```bash
searchsploit --version 2>&1 | head -1
searchsploit --update
```

Install: `sudo apt install exploitdb` (searchsploit is included)

## Phase 1: CVE Matching with SearchExploit

```bash
# Search for a specific service/version
searchsploit apache 2.4.49
searchsploit openssh 8.2
searchsploit windows 10
searchsploit wordpress

# Search with exact match (slower but more precise)
searchsploit -t apache | grep 2.4.49

# Search by CVE
searchsploit CVE-2021-41773

# Search by Exploit-DB ID
searchsploit -m 50535

# Mirror exploit to current directory
searchsploit -m 50535          # Copy to cwd
searchsploit -m 50535 ./exploits/  # Copy to specific directory

# Mirror as HTML (for report inclusion)
searchsploit -w 50535          # Show URL instead of copying

# Export results
searchsploit apache 2.4.49 --json > exploits.json
searchsploit apache 2.4.49 -x   # Exclude DOS vulnerabilities

# Update the local database
searchsploit --update
```

### SearchExploit Categories
```bash
# List categories
searchsploit --categories

# Common categories:
# remote   — Remote exploits
# local    — Local privilege escalation
# webapps  — Web application exploits
# dos      — Denial of service (exclude for production assessments)

# Search by category
searchsploit -t remote apache 2.4.49
searchsploit -t webapps wordpress
```

## Phase 2: Online CVE Databases

### NVD (National Vulnerability Database)
```bash
# Search via API
curl -s "https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=apache+2.4.49" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data.get('vulnerabilities', []):
    cve = item['cve']
    print(f\"{cve['id']}: {cve['descriptions'][0]['value'][:100]}\")
"

# Search by CVE ID
curl -s "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2021-41773" | \
  python3 -m json.tool | head -50
```

### Vulners API
```bash
# Search (requires free API key)
curl -s "https://vulners.com/api/v3/search/search?query=apache+2.4.49&apiKey=YOUR_KEY" | \
  python3 -m json.tool
```

### Exploit-DB via URL
```
https://www.exploit-db.com/search?q=apache+2.4.49
https://nvd.nist.gov/vuln/search/results?form_type=1&results_type=overview&query=apache+2.4.49
```

## Phase 3: CVSS v3.1 Scoring

### CVSS v3.1 Vector String
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
```

### Metric Breakdown
| Metric | Options | Meaning |
|--------|---------|---------|
| **AV** (Attack Vector) | N/A/L/P | Network/Adjacent/Local/Physical |
| **AC** (Attack Complexity) | L/H | Low/High |
| **PR** (Privileges Required) | N/L/H | None/Low/High |
| **UI** (User Interaction) | N/R | None/Required |
| **S** (Scope) | U/C | Unchanged/Changed |
| **C** (Confidentiality) | N/L/H | None/Low/High |
| **I** (Integrity) | N/L/H | None/Low/High |
| **A** (Availability) | N/L/H | None/Low/High |

### Quick Reference: Common Scenarios
| Scenario | Vector | Score |
|----------|--------|-------|
| Remote code execution, no auth, no interaction | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` | 9.8 (Critical) |
| SQL injection, low priv, web app | `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N` | 8.1 (High) |
| XSS (stored), requires user interaction | `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` | 6.1 (Medium) |
| Information disclosure, no auth | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` | 5.3 (Medium) |
| Local privilege escalation | `CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H` | 7.8 (High) |
| DoS, no auth | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H` | 7.5 (High) |

### Calculate CVSS Score
```bash
# Use the NVD calculator
# https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator

# Use the FIRST CVSS calculator
# https://www.first.org/cvss/calculator/3.1

# Quick Python calculation (approximate)
python3 -c "
# Use cvss library: pip install cvss
from cvss import CVSS3
v = CVSS3('CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H')
print(f'Score: {v.scores()[0]}')
print(f'Severity: {v.severities()[0]}')
print(f'Vector: {v.vector}')
"
```

## Phase 4: Vulnerability Prioritization

### Risk Matrix

| Factor | Weight | Assessment |
|--------|--------|-----------|
| **Exploitability** | 40% | Exploit available? Network-adjacent? Auth required? |
| **Impact** | 35% | Data exposure? System compromise? Availability? |
| **Asset Criticality** | 25% | Production vs staging? Customer-facing? Contains sensitive data? |

### Prioritization Workflow
1. **Eliminate false positives** (see Phase 5 below)
2. **Score remaining findings** with CVSS v3.1
3. **Check for known exploits** (SearchExploit, Metasploit)
4. **Assess asset criticality** (is this the crown jewel or a test server?)
5. **Apply priority matrix:**

### Priority Matrix
| CVSS Score | Exploit Available | Asset Criticality | Priority |
|------------|-------------------|-------------------|----------|
| 9.0-10.0 | Yes | High | **P1 — Immediate** |
| 9.0-10.0 | No | High | **P2 — High** |
| 7.0-8.9 | Yes | High | **P2 — High** |
| 7.0-8.9 | No | High | **P3 — Medium** |
| 7.0-8.9 | Yes | Low | **P3 — Medium** |
| 4.0-6.9 | Any | Any | **P4 — Low** |
| 0.1-3.9 | Any | Any | **P5 — Informational** |

## Phase 5: False Positive Verification

### Verification Methodology

For each finding, ask:

1. **Is the version actually vulnerable?**
   - Scanner may report based on banner version
   - Patches may have been backported (especially RHEL/CentOS)
   - Check: `rpm -q --changelog openssl | head -20`

2. **Is the finding reproducible?**
   - Manually trigger the vulnerability
   - For SQL injection: `curl "http://target/page?id=1' OR 1=1--"`
   - For XSS: `<script>alert(1)</script>` in input fields

3. **Does the service actually run on that port?**
   - Virtual hosts may serve different content
   - Default pages may not indicate the actual application
   - Check: `curl -s http://target:port/ | head -20`

4. **Is it a configuration issue or a code vulnerability?**
   - Misconfigurations (default creds, open directories) are lower severity
   - Code vulnerabilities (RCE, SQLi) are higher severity

### False Positive Elimination Checklist
- [ ] Version verified against actual service (not just banner)
- [ ] CVE applies to the specific version/patch level
- [ ] Finding manually reproduced
- [ ] Not a virtual host default page
- [ ] Not a backported patch (check distro-specific advisories)

## Phase 6: Finding Documentation

### Finding Template
```markdown
## Finding: [Short Title]

**Severity:** Critical | High | Medium | Low | Informational
**CVSS v3.1 Score:** X.X ([Vector String](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector=AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H))
**CVE:** CVE-YYYY-NNNNN
**Affected Asset:** target.com:443 (198.51.100.1)
**Discovered:** 2026-07-08 by Nmap NSE

### Description
Brief description of the vulnerability and its impact.

### Reproduction Steps
1. Step one (exact command)
2. Step two (exact command)
3. Observe the result

### Evidence
```
[Paste relevant tool output, screenshots, or code]
```

### Impact
What an attacker could achieve by exploiting this vulnerability.

### Remediation
- **Short-term:** Immediate mitigation (WAF rule, firewall, disable feature)
- **Long-term:** Proper fix (patch, upgrade, reconfigure)

### References
- https://nvd.nist.gov/vuln/detail/CVE-YYYY-NNNNN
- https://www.exploit-db.com/exploits/XXXXX
```

## Common Pitfalls

1. **Trusting scanner version detection.** Service banners lie. Verify with multiple methods (`curl -I`, nmap `-sV`, manual testing).
2. **Not checking for backported patches.** Red Hat/CentOS often backport security fixes without changing the version number. Check distro advisories.
3. **CVSS without context.** A 9.8 on a non-production staging server is lower priority than a 7.5 on the production database. Always factor in asset criticality.
4. **Not verifying exploit availability.** A CVE with no public exploit is lower priority than one with a working Metasploit module. Check SearchExploit and Metasploit.
5. **Ignoring false positives.** Every false positive in the report wastes the client's time and hurts your credibility. Verify before documenting.
6. **Not documenting reproduction steps.** If the client can't reproduce the finding, they'll question its validity. Exact commands, exact output.

## Verification Checklist

- [ ] All discovered services/versions checked against SearchExploit
- [ ] All findings have CVSS v3.1 scores with vector strings
- [ ] False positives eliminated through manual verification
- [ ] Findings prioritized using the risk matrix
- ] Exploit availability verified (SearchExploit, Metasploit)
- [ ] Asset criticality assessed for all findings
- [ ] Each finding documented with the finding template
- [ ] All findings include reproduction steps and evidence
- [ ] References include CVE links and exploit references
