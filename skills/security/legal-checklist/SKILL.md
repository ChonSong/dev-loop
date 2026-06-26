---
name: security/legal-checklist
description: Use before any security testing begins. Covers authorization requirements, scope definition, rules of engagement, responsible disclosure, data handling, and jurisdiction considerations. Legal protection for testers.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, legal, authorization, scope, compliance, disclosure, ethics]
    related_skills:
      - security/workflow
      - security/tool-setup
---

# Legal Checklist & Compliance

## Overview

This skill covers the legal and compliance requirements for penetration testing, bug bounty hunting, and security research. **Do not begin any security testing without completing the relevant sections of this checklist.**

## When to Use

- Before starting any penetration test or security assessment
- Before submitting a bug bounty report
- When defining the scope of an engagement
- When handling discovered data (credentials, PII, etc.)
- When you're unsure whether a technique is legal

## Phase 1: Authorization

### Written Authorization Requirements

A valid authorization letter/MUST include:

```markdown
# PENETRATION TEST AUTHORIZATION LETTER

**Date:** [YYYY-MM-DD]
**Authorization Number:** [If applicable]

## Authorizing Party
- **Name:** [Full legal name]
- **Title:** [Job title]
- **Organization:** [Company name]
- **Address:** [Physical address]
- **Phone:** [Direct phone]
- **Email:** [Direct email]

## Testing Party
- **Name:** [Tester name or company]
- **Title:** [If applicable]
- **Organization:** [If applicable]
- **Phone:** [Contact number]
- **Email:** [Contact email]

## Scope of Authorization
- **Authorized Targets:** [IP ranges, domains, applications]
- **Authorized Techniques:** [All except DoS | Specific list]
- **Testing Window:** [Start date/time to end date/time, timezone]
- **Emergency Contact:** [Name, phone — for immediate stop]

## Signature

___________________________     ___________
Authorizing Party                 Date

___________________________     ___________
Testing Party                     Date
```

### Authorization Checklist
- [ ] Written authorization signed by someone with authority to grant it
- [ ] Scope explicitly defined (in-scope AND out-of-scope)
- [ ] Testing window defined with timezone
- [ ] Emergency contact identified with direct phone number
- [ ] Authorized techniques listed (or explicitly excluded)
- [ ] Data handling requirements defined
- [ ] Retainer/contract signed (if commercial engagement)

## Phase 2: Scope Definition

### Scope Document Template
```markdown
# PENETRATION TEST SCOPE DOCUMENT

## In-Scope Assets

| Asset | Type | IP/URL | Environment | Notes |
|-------|------|--------|-------------|-------|
| Web App | Black box | https://app.example.com | Production | Customer-facing |
| API | Grey box | https://api.example.com | Staging | Internal API |
| Network | Grey box | 10.0.0.0/24 | Internal | Corporate LAN |

## Out-of-Scope Assets

| Asset | Reason |
|-------|--------|
| api.production.example.com | Third-party hosted |
| *.vendor.com | External services |
| Customer data stores | Regulatory restriction |

## Authorized Techniques

### Allowed
- Network scanning (Nmap, masscan)
- Web application testing (Nikto, SQLmap, ffuf)
- Password testing (hydra, john — with lockout awareness)
- Social engineering (if separately authorized)
- Physical testing (if separately authorized)

### Prohibited
- Denial of Service (DoS/DDoS)
- Phishing of customers
- Testing of third-party services
- Destructive exploitation (data deletion, ransomware)
- Testing outside the defined window

## Communication Plan

- [ ] Daily status updates to: [Contact name]
- [ ] Critical findings reported immediately to: [Phone number]
- [ ] All findings reported to: [Email]
- [ ] 24/7 emergency stop number: [Phone]
```

## Phase 3: Jurisdiction & Legal Framework

### United States
| Law | Relevance |
|-----|-----------|
| **Computer Fraud and Abuse Act (CFAA)** 18 U.S.C. § 1030 | Main federal anti-hacking law. Unauthorized access to computers is a felony. Authorization is your shield. |
| **Electronic Communications Privacy Act (ECPA)** | Governs interception of electronic communications. Relevant for packet capture. |
| **Wiretap Act** 18 U.S.C. § 2511 | Intercepting communications without authorization is illegal. Exceptions for system operators. |
| **State Laws** | Many states have additional computer crime laws (e.g., California Penal Code 502). Check your state. |

### European Union
| Law | Relevance |
|-----|-----------|
| **GDPR** | If you discover personal data (PII), you have handling obligations. Report to client immediately. |
| **Computer Misuse Directive (2013/40/EU)** | EU-wide framework. Member states implement locally. |
| **NIS2 Directive** | Affects critical infrastructure operators. Relevant for scope of assessments. |

### United Kingdom
| Law | Relevance |
|-----|-----------|
| **Computer Misuse Act 1990** (amended 2006) | Unauthorized access (S.1), unauthorized acts with intent to impair (S.3), making/supplying articles for use in offences (S.3A). |
| **Investigatory Powers Act 2016** | Governs interception and equipment interference. Requires warrant for some activities. |

### Other Jurisdictions
- **Canada:** Criminal Code sections 342.1, 430(1.1) — Unauthorized use of computer, mischief in relation to data
- **Australia:** Criminal Code Act 1995 Part 10.7 — Computer offences
- **Germany:** Strafgesetzbuch § 202a, 202b, 202c — Data espionage, interception, preparation

### Key Principle
**"Authorization is everything."** If you don't have written permission for the specific target, specific techniques, and specific time window, you risk criminal prosecution regardless of intent.

## Phase 4: Responsible Disclosure

### When You Find Vulnerability Outside Authorized Scope

1. **Stop immediately.** Do not exploit further.
2. **Document what you found** without accessing additional data.
3. **Report to the organization:**
   - Look for a security contact (security@domain.com, /security.txt)
   - Check for a bug bounty program (HackerOne, Bugcrowd, Intigriti)
   - Use CERT/CC as intermediary if no response
4. **Give reasonable time to respond:**
   - Industry standard: 90 days before public disclosure
   - Critical vulnerabilities (active exploitation): 48-72 hours
5. **Do not access, copy, or modify data** beyond what's needed to demonstrate the vulnerability

### Responsible Disclosure Template
```markdown
# Security Vulnerability Report

**Reported to:** security@example.com
**Date:** 2024-01-15
**Reporter:** [Your name/contact]

## Summary
[Brief description — one paragraph]

## Affected Component
[URL, IP, service]

## Severity Estimate
[High/Medium/Low — with brief justification]

## Reproduction Steps
1. Step one
2. Step two
3. Observe: [result]

## Impact
[What an attacker could do]

## Remediation Suggestion
[Optional — how to fix]

## Disclosure Timeline
- 2024-01-15: Reported to vendor
- 2024-01-22: Acknowledged (if applicable)
- 2024-04-15: Planned public disclosure (if no response)

**PGP Key:** [If encrypting]
```

## Phase 5: Data Handling

### If You Discover Sensitive Data During Testing

1. **Stop accessing the data immediately**
2. **Document the exposure** (what type, how much, how accessible)
3. **Report to the client immediately** (phone, not just email)
4. **Do not copy, download, or retain** sensitive data beyond minimal evidence
5. **Encrypt all evidence** containing sensitive data (use GPG)
6. **Destroy sensitive data** after the engagement (as per contract)

### Evidence Handling
```bash
# Encrypt evidence files
gpg --encrypt --recipient client@example.com evidence_file.txt
# Creates: evidence_file.txt.gpg

# Secure deletion
shred -vfz -n 3 sensitive_file.txt

# Verify secure deletion
# (file should be unrecoverable)
```

### Data Classification Handling
| Data Type | Handling |
|-----------|----------|
| **Passwords/Hashes** | Encrypt at rest, do not include plaintext in reports, hash only |
| **PII (names, emails, SSNs)** | Minimize in report (show pattern, not full data), encrypt |
| **Financial data** | Minimal evidence, encrypted storage, immediate client notification |
| **Health data (HIPAA)** | Same as PII + regulatory breach notification requirements |
| **Source code** | Mark as confidential, encrypted, limited distribution |

## Common Pitfalls

1. **Testing without authorization.** Even if your intent is good, unauthorized testing is illegal. Always get written permission.
2. **Scope creep.** You find an interesting system near the target. It's not in scope. Don't test it — report it as a recommendation.
3. **Accessing more data than needed.** Seeing PII during a test doesn't mean you can read it all. Minimize access.
4. **Not reporting immediately.** If you accidentally compromise a production system, call the emergency contact NOW. Don't wait.
5. **Keeping sensitive data.** After the engagement, destroy all copies of sensitive data. Retain only sanitized report evidence.
6. **Not knowing jurisdiction laws.** If you're testing across borders, research the laws in both your location and the target's location.
7. **Public disclosure without coordination.** Disclosing a vulnerability before the vendor can patch puts users at risk and may expose you to legal liability.

## Verification Checklist

- [ ] Written authorization obtained and signed
- [ ] Scope clearly defined (in-scope AND out-of-scope)
- [ ] Testing window defined with timezone
- [ ] Emergency contact identified (direct phone number)
- [ ] Authorized and prohibited techniques documented
- [ ] Jurisdiction laws researched (yours + target's)
- [ ] Data handling procedures defined
- [ ] NDA signed (if required)
- [ ] Insurance/professional liability coverage verified (commercial testing)
- [ ] Responsible disclosure policy understood
- [ ] Evidence handling procedures defined (encryption, retention, destruction)
