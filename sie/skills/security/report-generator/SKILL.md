---
name: security/report-generator
description: Use when writing penetration test reports. Provides templates for executive summaries, technical findings, risk ratings, remediation roadmaps, and appendices. Converts tool output into structured, professional pentest reports.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, report, pentest, template, findings, risk, remediation]
    related_skills:
      - security/workflow
      - security/vuln-assessment
      - security/tool-setup
---

# Report Generator

## Overview

A penetration test is only as good as its report. This skill provides structured templates for creating professional pentest reports, from executive summaries to technical findings to remediation roadmaps.

## When to Use

- You've completed testing and need to write the report
- You need to structure findings into a professional document
- You need to generate risk ratings and remediation priorities
- You need an executive summary for non-technical stakeholders
- You need to convert tool output (Nmap XML, Nikto, ffuf JSON) into report sections

## Report Structure

```
1. Executive Summary
2. Scope & Methodology
3. Findings Summary (Risk Matrix)
4. Detailed Technical Findings
5. Remediation Roadmap
6. Appendices
   A. Tool Versions
   B. Scan Data
   C. Raw Output References
   D. Glossary
```

## 1. Executive Summary Template

```markdown
# Executive Summary

**Client:** [Organization Name]
**Assessment Date:** [Start] – [End]
**Report Date:** [Date]
**Classification:** CONFIDENTIAL

## Overview

A penetration test was conducted against [scope] from [dates] to
identify security vulnerabilities and assess the overall security posture.

## Key Findings

| # | Finding | Severity | CVSS |
|---|---------|----------|------|
| 1 | [Title] | Critical | 9.8 |
| 2 | [Title] | High | 8.1 |
| 3 | [Title] | Medium | 6.5 |

## Risk Summary

- **Critical:** X findings requiring immediate remediation
- **High:** X findings requiring remediation within 30 days
- **Medium:** X findings requiring remediation within 90 days
- **Low:** X findings — address as resources permit
- **Informational:** X findings — best practice recommendations

## Overall Risk Rating: [CRITICAL | HIGH | MEDIUM | LOW]

[One-paragraph summary of the overall security posture and primary concerns.]

## Recommendations (Priority Order)

1. [Highest priority remediation]
2. [Second priority]
3. [Third priority]
```

## 2. Scope & Methodology Template

```markdown
# Scope & Methodology

## In-Scope Targets

| Target | Type | IP/URL | Notes |
|--------|------|--------|-------|
| Web App | Black box | https://target.com | Production |
| Network | Grey box | 198.51.100.0/24 | Internal range |

## Out-of-Scope

- Production API (api.production.target.com)
- Third-party services
- Denial of Service testing

## Methodology

The assessment followed the PTES (Penetration Testing Execution Standard)
framework:

1. **Pre-engagement** — Scope definition, authorization, rules of engagement
2. **Reconnaissance** — Passive OSINT, active network scanning
3. **Enumeration** — Service enumeration, web application mapping
4. **Vulnerability Assessment** — Automated scanning, manual verification
5. **Exploitation** — Controlled exploitation of discovered vulnerabilities
6. **Post-Exploitation** — Impact assessment, lateral movement evaluation
7. **Reporting** — This document

## Tools Used

| Tool | Version | Purpose |
|------|---------|---------|
| Nmap | 7.94 | Network scanning |
| ffuf | 2.1.0 | Directory fuzzing |
| Nikto | 2.5.0 | Web vulnerability scanning |
| SQLmap | 1.7.12 | SQL injection testing |
| Metasploit | 6.3.x | Exploitation |
```

## 3. Findings Summary

```markdown
# Findings Summary

## Risk Matrix

| Risk Level | Count | % of Total |
|------------|-------|------------|
| Critical   | X     | X% |
| High       | X     | X% |
| Medium     | X     | X% |
| Low        | X     | X% |
| Info       | X     | X% |
| **Total**  | **X** | **100%** |

## Risk Rating Methodology

Risk ratings follow CVSS v3.1 with contextual adjustments:

- **Critical (9.0-10.0):** Immediate threat to business operations or data
- **High (7.0-8.9):** Significant risk, may lead to system compromise
- **Medium (4.0-6.9):** Moderate risk, should be addressed in normal cycles
- **Low (0.1-3.9):** Minor risk, address as resources permit
- **Informational:** Best practice recommendations, no direct exploitability
```

## 4. Detailed Finding Template

```markdown
# Finding [N]: [Short Descriptive Title]

| Field | Value |
|-------|-------|
| **Severity** | 🔴 Critical / 🟠 High / 🟡 Medium / 🔵 Low / ⚪ Informational |
| **CVSS v3.1** | X.X ([AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector=AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)) |
| **CVE** | CVE-YYYY-NNNNN |
| **Affected Asset(s)** | target.com:443 (198.51.100.1) |
| **Discovered By** | Nmap NSE on 2024-01-15 |
| **Exploit Available** | Yes — Exploit-DB #XXXXX, Metasploit module: exploit/... |
| **Authentication Required** | No |

## Description

[2-3 paragraphs explaining the vulnerability, why it exists, and its
potential impact. Avoid excessive jargon — the technical audience will
read the reproduction steps.]

## Business Impact

[Describe the business impact: data exposure, financial loss, regulatory
compliance, reputation damage, etc.]

## Reproduction Steps

1. Run the following Nmap command:
   ```bash
   nmap -sV -sC -p 443 --script http-vuln-cve2021-41773 target.com
   ```
2. Observe the following output:
   ```
   [Paste relevant output]
   ```
3. Navigate to `http://target.com/cgi-bin/.%%32%65/.%%32%65/bin/sh`
4. Observe RCE response with `uid=33(www-data) gid=33(www-data)`

## Evidence

[Screenshot or tool output showing the vulnerability]

```
[Raw tool output or screenshot reference]
```

## Affected Components

- Apache 2.4.49 on target.com:443
- CGI-enabled endpoints under /cgi-bin/

## Remediation

### Short-term (Immediate)
1. Upgrade Apache to version 2.4.51 or later:
   ```bash
   sudo apt update && sudo apt upgrade apache2
   ```
2. If upgrade is not immediately possible, disable CGI:
   ```bash
   sudo a2dismod cgi
   sudo systemctl restart apache2
   ```

### Long-term (Structural)
1. Implement a Web Application Firewall (WAF) to filter exploitation attempts
2. Apply principle of least privilege to web server processes
3. Regular vulnerability scanning and patch management program

## References

- [NVD: CVE-2021-41773](https://nvd.nist.gov/vuln/detail/CVE-2021-41773)
- [Exploit-DB: 50383](https://www.exploit-db.com/exploits/50383)
- [Apache Security Advisory](https://httpd.apache.org/security/vulnerabilities_24.html)
```

## 5. Remediation Roadmap Template

```markdown
# Remediation Roadmap

## Priority 1: Critical (Fix Immediately)

| # | Finding | Action | Effort | Owner |
|---|---------|--------|--------|-------|
| 1 | Apache RCE | Upgrade to 2.4.51+ | 2 hours | Web Team |
| 2 | Default Admin Creds | Change passwords + MFA | 1 hour | IT Admin |

## Priority 2: High (Fix Within 30 Days)

| # | Finding | Action | Effort | Owner |
|---|---------|--------|--------|-------|
| 3 | SMB Signing Disabled | Enable via GPO | 4 hours | AD Team |
| 4 | Outdated OpenSSL | Upgrade to 3.0.x | 4 hours | DevOps |

## Priority 3: Medium (Fix Within 90 Days)

| # | Finding | Action | Effort | Owner |
|---|---------|--------|--------|-------|
| 5 | Information Disclosure | Update error handling | 8 hours | Dev Team |
| 6 | Missing Security Headers | Add HSTS, CSP, X-Frame-Options | 4 hours | Dev Team |

## Priority 4: Low (Address as Resources Permit)

| # | Finding | Action | Effort | Owner |
|---|---------|--------|--------|-------|
| 7 | SSH weak ciphers | Update sshd_config | 2 hours | IT Admin |

## Estimated Total Effort: XX hours over 90 days
```

## 6. Appendices Template

```markdown
# Appendices

## Appendix A: Tool Versions

| Tool | Version | License |
|------|---------|---------|
| Nmap | 7.94 | GPLv2 |
| ffuf | 2.1.0 | MIT |
| Nikto | 2.5.0 | GPL |
| SQLmap | 1.7.12 | GPLv2 |
| Metasploit Framework | 6.3.45 | BSD-3 |

## Appendix B: Scan Summary

| Scan Type | Date | Target | Tool |
|-----------|------|--------|------|
| Full TCP SYN | 2024-01-15 | 198.51.100.0/24 | Nmap |
| Web Scan | 2024-01-15 | https://target.com | Nikto |
| Directory Fuzz | 2024-01-15 | https://target.com | ffuf |
| SQL Injection | 2024-01-16 | https://target.com | SQLmap |

## Appendix C: Glossary

| Term | Definition |
|------|-----------|
| CVSS | Common Vulnerability Scoring System |
| CVE | Common Vulnerabilities and Exposures |
| RCE | Remote Code Execution |
| LFI/RFI | Local/Remote File Inclusion |
| PTES | Penetration Testing Execution Standard |
| NSE | Nmap Scripting Engine |
```

## Converting Tool Output to Findings

### Parse Nmap XML
```bash
# Extract open services
python3 -c "
import xml.etree.ElementTree as ET
tree = tree.parse('scan.xml')
for host in tree.findall('.//host'):
    ip = host.find('.//address[@addrtype=\"ipv4\"]').get('addr')
    for port in host.findall('.//port'):
        portid = port.get('portid')
        state = port.find('state').get('state')
        if state == 'open':
            svc = port.find('service')
            name = svc.get('name', 'unknown') if svc is not None else 'unknown'
            ver = svc.get('version', '') if svc is not None else ''
            print(f'{ip}:{portid} {name} {ver}')
"
```

### Parse ffuf JSON
```bash
python3 -c "
import json
with open('ffuf_results.json') as f:
    data = json.load(f)
for r in data['results']:
    if r['status'] in [200, 301, 302, 403]:
        print(f\"{r['status']:>5} {r['length']:>10} {r['url']}\")
"
```

### Generate Finding Count
```bash
# Count findings by severity from a structured list
echo "Critical: $(grep -c 'Severity.*Critical' findings.md)"
echo "High: $(grep -c 'Severity.*High' findings.md)"
echo "Medium: $(grep -c 'Severity.*Medium' findings.md)"
```

## Risk Rating Quick Reference

### Impact Assessment Questions
- **Confidentiality:** Can an attacker read sensitive data? (customer PII, credentials, trade secrets)
- **Integrity:** Can an attacker modify data? (database, configurations, files)
- **Availability:** Can an attacker disrupt services? (DoS, data destruction, lockout)

### Exploitability Assessment Questions
- Is there a public exploit? (SearchExploit, Metasploit)
- Can it be exploited remotely? (network vs local)
- Does it require authentication? (none vs valid creds vs admin)
- Does it require user interaction? (click, visit, open file)
- How complex is the attack? (script kiddie vs advanced)

## Common Report Pitfalls

1. **Too much tool output, not enough analysis.** Raw Nmap output doesn't explain risk. Every finding needs context and business impact.
2. **No executive summary.** Decision-makers read only the first page. Give them what they need.
3. **Vague remediation.** "Update software" is useless. Give exact commands, exact versions, exact configurations.
4. **No risk ratings.** Without severity ratings, the client can't prioritize. Always include CVSS.
5. **Missing evidence.** Screenshots, tool output, reproduction steps — without these, findings aren't credible.
6. **Not including positive findings.** Documenting what's GOOD builds trust. "SSH uses strong ciphers, no issues found" is valuable.
7. **Forgetting scope and methodology.** These sections protect you legally and give context to findings.

## Verification Checklist

- [ ] Executive summary completed
- [ ] Scope documented with in-scope and out-of-scope items
- [ ] Methodology described
- [ ] Each finding has: title, severity, CVSS, description, impact, reproduction steps, evidence, remediation, references
- [ ] Risk matrix with counts by severity
- [ ] Remediation roadmap with priorities and estimated effort
- [ ] Appendices with tool versions and scan dates
- [ ] All findings have evidence (screenshots, tool output)
- [ ] Report reviewed for consistency (severity ratings match CVSS scores)
- [ ] Report reviewed for actionable remediation (specific commands, not vague advice)
