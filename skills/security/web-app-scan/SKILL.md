---
name: security/web-app-scan
description: Use when scanning web applications for vulnerabilities. Covers Nikto, WhatWeb, WPScan, and SQLmap with complete recipes for technology fingerprinting, CMS scanning, SQL injection testing, and WAF detection.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, web, nikto, sqlmap, wpscan, whatweb, waf, injection, cms]
    related_skills:
      - security/directory-fuzz
      - security/workflow
      - security/vuln-assessment
      - security/exploit-basics
      - security/tool-setup
---

# Web Application Scanning

## Overview

Web application scanning covers technology fingerprinting, CMS-specific scanning, general vulnerability scanning, and SQL injection testing. This skill provides exact commands for Nikto, WhatWeb, WPScan, and SQLmap with output interpretation and WAF-aware testing strategies.

## When to Use

- You've discovered a web application during recon
- You need to identify the technology stack (CMS, framework, server)
- You need to scan for known web vulnerabilities
- You need to test for SQL injection
- You need to assess a WordPress/Joomla/Drupal site

**Don't use for:** directory discovery (use `security/directory-fuzz`), network scanning (use `security/network-recon`).

## Tool Availability Check

```bash
nikto -Version 2>&1 | head -1
whatweb --version
wpscan --version 2>&1 | head -1
sqlmap --version 2>&1 | head -1
```

Install: `sudo apt install nikto whatweb wpscan sqlmap`

## Phase 1: Technology Fingerprinting

### WhatWeb
```bash
# Basic fingerprinting (aggression level 1-4)
whatweb -a 1 http://target.com          # Stealthy
whatweb -a 3 http://target.com          # Aggressive (recommended)
whatweb -a 4 http://target.com          # Heavy (most thorough)

# Multiple targets
whatweb -a 3 -i targets.txt --log-json=whatweb.json

# Verbose output with plugin details
whatweb -a 3 -v http://target.com

# Aggressive with proxy (route through Burp)
whatweb -a 3 --proxy 127.0.0.1:8080 http://target.com
```

**Aggression levels:**
| Level | Speed | Stealth | Detail |
|-------|-------|---------|--------|
| 1 | Fast | Stealthy | Basic |
| 3 | Medium | Normal | Detailed (recommended) |
| 4 | Slow | Noisy | Maximum |

**Interpreting output:**
- `HTTPServer[Apache/2.4.41]` → web server and version
- `X-Powered-By[PHP/7.4.3]` → backend language
- `WordPress[5.8]` → CMS and version
- `JQuery[3.5.1]` → JavaScript framework
- `Country[US]` → server location

### httpx (alternative, fast)
```bash
# Technology detection with httpx
echo "http://target.com" | httpx -tech-detect -status-code -title -silent

# Batch mode
cat urls.txt | httpx -tech-detect -status-code -title -o httpx_results.txt
```

## Phase 2: General Vulnerability Scanning

### Nikto
```bash
# Basic scan
nikto -h http://target.com -output nikto_results.html -Format htm

# Scan with tuning options
nikto -h http://target.com -Tuning x 6 -output nikto_tuned.txt

# Scan specific port
nikto -h http://target.com -p 8080 -output nikto_8080.txt

# With authentication
nikto -h http://target.com -id admin:password -output nikto_auth.txt

# With proxy (route through Burp for manual verification)
nikto -h http://target.com -useproxy http://127.0.0.1:8080

# Scan multiple hosts
nikto -h hosts.txt -output nikto_batch.csv -Format csv
```

**Tuning options (combine with `-Tuning`):**
| Code | Scan Type |
|------|-----------|
| 0 | File uploads |
| 1 | Interesting files / logs |
| 2 | Misconfigurations / default files |
| 3 | Information disclosure |
| 4 | Injection (XSS/Script/HTML) |
| 5 | Remote file retrieval (web root) |
| 6 | Denial of service (use with caution) |
| 7 | Remote file retrieval (server) |
| 8 | Code execution / remote shell |
| 9 | SQL injection |
| a | Authentication bypass |
| b | Software identification |
| c | Remote source inclusion |
| x | Reverse tuning (exclude these) |

**Recommended:** `-Tuning x 6` excludes DoS tests. For production, use `-Tuning 12345789abc` (everything except DoS and remote file retrieval).

**Output interpretation:**
- `+ OSVDB-XXXXX: /path` → known vulnerability reference
- `+ /path: Apache default file` → default configuration
- `+ /path: Admin login page found` → potential entry point
- Cross-reference OSVDB IDs with current CVE databases (OSVDB is archived)

## Phase 3: CMS-Specific Scanning

### WPScan (WordPress)
```bash
# Basic WordPress scan
wpscan --url http://target.com --enumerate ap,at,u --format json -o wpscan.json

# With API token (unlimited scans + vulnerability data)
wpscan --url http://target.com --api-token YOUR_TOKEN --enumerate ap,at,u,cb,dbe

# Enumerate all plugins, themes, users, and timthumbs
wpscan --url http://target.com --enumerate ap,at,u,tt,cb,dbe --format json -o wpscan_full.json

# Brute force login (use with caution on production)
wpscan --url http://target.com --passwords /usr/share/wordlists/rockyou.txt --usernames admin

# Scan with proxy
wpscan --url http://target.com --proxy 127.0.0.1:8080

# Aggressive plugin detection
wpscan --url http://target.com --enumerate ap --plugins-detection aggressive
```

**Enumerate flags:**
| Flag | What it enumerates |
|------|-------------------|
| `u` | Users |
| `ap` | All plugins |
| `at` | All themes |
| `tt` | Timthumb files |
| `cb` | Config backups |
| `dbe` | Database exports |
| `p` | Popular plugins |
| `t` | Popular themes |

**Get free API token:** Register at https://wpscan.com/api (free tier: 25 requests/day)

### Droopescan (Drupal/Joomla/Moodle)
```bash
# Drupal scan
droopescan scan drupal -u http://target.com -t 30 -o droopescan_drupal.json

# Joomla scan
droopescan scan joomla -u http://target.com -t 30 -o droopescan_joomla.json
```

## Phase 4: SQL Injection Testing

### SQLmap
```bash
# Basic GET parameter test
sqlmap -u "http://target.com/page?id=1" --batch --risk=1 --level=2

# POST parameter test
sqlmap -u "http://target.com/login" --data="user=admin&pass=test" --method POST --batch

# Test all parameters on a page
sqlmap -u "http://target.com/page?id=1&cat=2" --batch --risk=1 --level=2

# Crawl and test everything
sqlmap -u http://target.com --crawl=3 --batch --risk=1 --level=2

# Specify DBMS (faster if you know it)
sqlmap -u "http://target.com/page?id=1" --dbms=mysql --batch

# Specify injection technique
sqlmap -u "http://target.com/page?id=1" --technique=BEUSTQ --batch

# Dump specific table
sqlmap -u "http://target.com/page?id=1" --dump -T users --batch

# Dump all databases
sqlmap -u "http://target.com/page?id=1" --dbs --batch

# Get OS shell (DESTRUCTIVE — last resort, authorized targets only)
sqlmap -u "http://target.com/page?id=1" --os-shell --batch

# Get SQL shell
sqlmap -u "http://target.com/page?id=1" --sql-shell --batch

# With cookie for authenticated testing
sqlmap -u "http://target.com/page?id=1" --cookie="session=abc123" --batch

# With proxy (route through Burp)
sqlmap -u "http://target.com/page?id=1" --proxy="http://127.0.0.1:8080" --batch

# Tamper scripts for WAF evasion
sqlmap -u "http://target.com/page?id=1" --tamper=space2comment,between --batch

# Output directory
sqlmap -u "http://target.com/page?id=1" --batch --output-dir=./sqlmap_results/
```

**Risk levels:**
| Risk | What it tests |
|------|--------------|
| 1 | Safe (default) — standard tests |
| 2 | + OR-based tests |
| 3 | + stacked queries, time-based blind |

**Level values:**
| Level | Tests |
|-------|-------|
| 1 | GET/POST parameters (default) |
| 2 | + Cookies |
| 3 | + User-Agent, Referer |
| 4 | + All headers |
| 5 | + Everything |

**⚠️ Production guidance:** Use `--risk=1 --level=2` on production. Higher levels send more requests and may cause locks/timeouts.

**Technique flags:**
| Flag | Technique |
|------|-----------|
| `B` | Boolean-based blind |
| `E` | Error-based |
| `U` | UNION query |
| `S` | Stacked queries |
| `T` | Time-based blind |
| `Q` | Inline queries |

### Common Tamper Scripts for WAF Evasion
```bash
# Space replacement
--tamper=space2comment    # ' ' → /**/
--tamper=space2plus       # ' ' → +
--tamper=space2dash       # ' ' → --

# Keyword obfuscation
--tamper=between          # AND → BETWEEN
--tamper=randomcase       # SeLeCt
--tamper=charunicodeencode # URL-encode

# Combined
--tamper=space2comment,between,randomcase
```

## Phase 5: WAF Detection

### WAF Detection with wafw00f
```bash
# Detect WAF
wafw00f http://target.com

# Multiple targets
wafw00f -i targets.txt -o waf_results.txt
```

### WAF Detection with Nmap
```bash
nmap -p 80,443 --script http-waf-detect target.com
nmap -p 80,443 --script http-waf-fingerprint target.com
```

### WAF Bypass Strategies
1. **Encoding:** URL-encode, double-encode, Unicode
2. **Case variation:** `SeLeCt`, `UNIOn`
3. **Comments:** `UN/**/ION SEL/**/ECT`
4. **Whitespace:** Tabs, newlines, comments instead of spaces
5. **Parameter pollution:** `?id=1&id=2&id=3`
6. **Content-Type manipulation:** Switch between `application/x-www-form-urlencoded`, `multipart/form-data`, `application/json`
7. **HTTP method variation:** GET → POST → PUT

## Common Pitfalls

1. **SQLmap `--os-shell` on production.** This is destructive and leaves traces. Only use on authorized targets with explicit permission.
2. **Nikto without tuning.** Default scan includes DoS tests. Use `-Tuning x 6` to exclude them.
3. **Not checking for WAF before aggressive scanning.** WAF will block you and you'll get false negatives. Detect first, then adapt.
4. **SQLmap risk/level too high on production.** `--risk=3` sends stacked queries that can cause database locks. Stick to `--risk=1 --level=2`.
5. **WPScan without API token.** Without a token, you miss vulnerability data for discovered plugins. Register for free at wpscan.com.
6. **Not routing through Burp.** Manual verification catches what automated scanners miss. Use `--proxy` to route through Burp Suite.
7. **Trusting scanner output.** Every finding needs manual verification. Nikto especially has false positives.

## Verification Checklist

- [ ] Technology fingerprinting completed (WhatWeb or httpx)
- [ ] General vulnerability scan completed (Nikto with safe tuning)
- [ ] CMS-specific scan completed if applicable (WPScan/Droopescan)
- [ ] SQL injection testing completed on all input parameters
- [ ] WAF detected and bypass strategy adapted if present
- [ ] All findings manually verified (not just scanner output)
- [ ] Evidence captured (screenshots, request/response pairs)
- [ ] Output saved in structured format (JSON/CSV) for reporting
