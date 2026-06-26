---
name: security/directory-fuzz
description: Use when discovering hidden files, directories, parameters, and virtual hosts on web applications. Covers ffuf, gobuster, and dirb with complete recipes for directory brute-forcing, extension fuzzing, parameter discovery, and vhost enumeration.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, fuzzing, ffuf, gobuster, dirb, web, enumeration, directories, parameters]
    related_skills:
      - security/web-app-scan
      - security/workflow
      - security/osint
      - security/tool-setup
---

# Directory & Content Fuzzing

## Overview

Web servers hide content. This skill covers systematic discovery of hidden files, directories, parameters, and virtual hosts using ffuf (primary), gobuster, and dirb. Includes wordlist selection, filtering strategies, and result triage.

## When to Use

- You've identified a web server and need to discover its attack surface
- You need to find hidden admin panels, backup files, or API endpoints
- You need to enumerate subdomains or virtual hosts
- You need to discover URL parameters for further testing
- You're mapping a web application's full content tree

**Don't use for:** vulnerability scanning (use `security/web-app-scan`), password attacks (use `security/password-attack`).

## Tool Selection

| Tool | Speed | Features | Best For |
|------|-------|----------|----------|
| **ffuf** | Fastest | Recursion, filtering, multi-position | Primary choice |
| **gobuster** | Fast | DNS mode, vhost mode | Simple scans, vhost enum |
| **dirb** | Slow | Basic, legacy | When others unavailable |

**Recommendation:** Use ffuf as primary. Fall back to gobuster for simple vhost enumeration.

## Tool Availability Check

```bash
ffuf -V
gobuster version
dirb 2>&1 | head -1
```

Install: `sudo apt install ffuf gobuster dirb`

## Wordlist Selection

### Standard Wordlists (Kali)
| Wordlist | Path | Use |
|----------|------|-----|
| dirb common | `/usr/share/wordlists/dirb/common.txt` | Quick scan (~4.6K entries) |
| dirb big | `/usr/share/wordlists/dirb/big.txt` | Thorough (~20K entries) |
| dirbuster medium | `/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt` | Balanced (~220K entries) |
| dirbuster large | `/usr/share/wordlists/dirbuster/directory-list-2.3-large.txt` | Exhaustive (~1.8M entries) |
| SecLists Discovery | `/usr/share/seclists/Discovery/Web-Content/` | Comprehensive collection |
| raft-medium | `/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt` | Good balance |
| raft-large | `/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt` | Thorough |

### Technology-Specific Wordlists
```bash
# WordPress
/usr/share/seclists/Discovery/Web-Content/CMS/wordpress.fuzz.txt

# Apache
/usr/share/seclists/Discovery/Web-Content/apache.fuzz.txt

# IIS / ASP.NET
/usr/share/seclists/Discovery/Web-Content/IIS.fuzz.txt

# API endpoints
/usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt

# Common parameters
/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt
```

### Custom Wordlist Generation
```bash
# CeWL — spider a site and build a wordlist from its content
cewl -d 2 -m 5 -w custom_wordlist.txt http://target.com

# Crunch — pattern-based generation
crunch 4 6 abc123 -o pattern_wordlist.txt

# Combine wordlists
cat wordlist1.txt wordlist2.txt | sort -u > combined.txt
```

## ffuf Recipes

### Basic Directory Fuzzing
```bash
# Standard directory scan
ffuf -w /usr/share/wordlists/dirb/common.txt -u http://target.com/FUZZ -mc all -fc 404

# With extensions
ffuf -w /usr/share/wordlists/dirb/common.txt -u http://target.com/FUZZ -e .php,.html,.asp,.aspx,.jsp,.txt,.bak,.old,.zip -mc all -fc 404

# Larger wordlist, output to JSON
ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
  -u http://target.com/FUZZ \
  -mc all -fc 404 \
  -of json -o ffuf_results.json
```

### Recursive Scanning
```bash
# Recurse into discovered directories (depth 2)
ffuf -w /usr/share/wordlists/dirb/common.txt \
  -u http://target.com/FUZZ \
  -recursion -recursion-depth 2 \
  -mc all -fc 404

# Specify recursion only on certain status codes
ffuf -w /usr/share/wordlists/dirb/common.txt \
  -u http://target.com/FUZZ \
  -recursion -recursion-strategy greedy \
  -recursion-depth 3 \
  -mc 200,301,302,403
```

### Virtual Host Discovery
```bash
# Vhost fuzzing via Host header
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -u http://target.com \
  -H "Host: FUZZ.target.com" \
  -fs 0 -mc all

# Filter by response size (find vhosts with different content)
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -u http://target.com \
  -H "Host: FUZZ.target.com" \
  -fs 150  # Filter responses of size 150 (default vhost size)
```

### Parameter Fuzzing
```bash
# GET parameter discovery
ffuf -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -u http://target.com/page?FUZZ=value \
  -fs 0

# Multiple parameter positions
ffuf -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt:W1 \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt:W2 \
  -u http://target.com/page?W1=value1&W2=value2 \
  -fs 0

# POST parameter fuzzing
ffuf -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -u http://target.com/login \
  -X POST -d "FUZZ=value&password=test" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -fs 0
```

### Advanced Filtering
```bash
# Filter by status code, size, words, lines
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -fc 404,403,401 \     # Filter status codes
  -fs 0 \                # Filter response size (0 = empty)
  -fw 0 \                # Filter word count
  -fl 0                  # Filter line count

# Match only specific status codes
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -mc 200,301,302,403

# Filter by regex in response body
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -fr "Not Found"        # Filter responses containing "Not Found"
```

### Rate Limiting (Production Targets)
```bash
# Add delay between requests (0.1 to 0.5 seconds)
ffuf -w wordlist.txt -u http://target.com/FUZZ -p 0.1-0.5 -mc all -fc 404

# Limit concurrent threads
ffuf -w wordlist.txt -u http://target.com/FUZZ -t 5 -mc all -fc 404

# Combined: slow and steady
ffuf -w wordlist.txt -u http://target.com/FUZZ -t 3 -p 0.5 -mc all -fc 404
```

### Authentication / Session Fuzzing
```bash
# With cookies
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -b "session=abc123; token=xyz789" \
  -mc all -fc 404

# With custom headers
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -H "Authorization: Bearer TOKEN" \
  -H "X-Custom-Header: value" \
  -mc all -fc 404

# With basic auth
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)" \
  -mc all -fc 404
```

## gobuster Recipes

```bash
# Directory scan
gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt -o gobuster_dirs.txt

# With extensions
gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt -x php,html,asp,txt -o gobuster_ext.txt

# Vhost enumeration
gobuster vhost -u http://target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -o gobuster_vhosts.txt

# DNS subdomain enumeration
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -o gobuster_dns.txt

# With proxy
gobuster dir -u http://target.com -w wordlist.txt -p http://127.0.0.1:8080

# With authentication
gobuster dir -u http://target.com -w wordlist.txt -c "session=abc123"
```

## dirb Recipes (Legacy)

```bash
# Basic scan
dirb http://target.com /usr/share/wordlists/dirb/common.txt

# With extensions
dirb http://target.com /usr/share/wordlists/dirb/common.txt -X .php,.html

# With authentication
dirb http://target.com -u admin:password

# Output to file
dirb http://target.com /usr/share/wordlists/dirb/common.txt -o dirb_results.txt
```

## Result Triage

### Parse ffuf JSON Output
```bash
# Extract discovered paths
cat ffuf_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data['results']:
    print(f\"{r['status']:>5} {r['length']:>10} {r['url']}\")
"

# Filter by status code
cat ffuf_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data['results']:
    if r['status'] in [200, 301, 302, 403]:
        print(f\"{r['status']} {r['url']}\")
"
```

### Parse gobuster Output
```bash
# Extract found paths
grep "Status: 200" gobuster_dirs.txt | awk '{print $1}'
grep "Status: 301\|Status: 302" gobuster_dirs.txt | awk '{print $1}'
```

### Priority Triage Order
1. **200 OK** — directly accessible content (investigate immediately)
2. **403 Forbidden** — exists but access denied (try bypass techniques)
3. **301/302 Redirect** — may reveal internal paths in redirect target
4. **401 Unauthorized** — authentication required (credential attack candidate)
5. **500 Internal Server Error** — may indicate injection vulnerability

## Common Pitfalls

1. **Not filtering by size.** Without `-fs`/`-fc`, you'll get thousands of false positives from soft 404s (pages that return 200 but show "not found" content).
2. **Recursive fuzzing without depth limit.** `-recursion-depth 10` on a large site = millions of requests = DoS. Start with depth 1-2.
3. **Using on production without rate limiting.** `-p 0.1-0.5` adds random delays. Always use on production targets.
4. **Missing the `-mc all` flag.** Without it, ffuf only shows 200 responses by default, missing 301/302/403/401.
5. **Not checking for WAF.** If all responses are the same size, you may be hitting a WAF. Try with `-p 0.5` and different User-Agent.
6. **Forgetting extensions.** `/admin` might 404 but `/admin.php` returns 200. Always fuzz with common extensions.
7. **Using a tiny wordlist.** `dirb/common.txt` has ~4,600 entries. For real assessments, use at least `raft-medium` (~220K).

## Verification Checklist

- [ ] Directory fuzzing completed with at least `raft-medium` wordlist
- [ ] Extension fuzzing completed (.php, .html, .asp, .txt, .bak, .zip)
- [ ] Recursive scanning completed (depth 2+)
- [ ] Vhost enumeration attempted
- [ ] Parameter fuzzing attempted on key endpoints
- [ ] Results filtered and triaged by status code
- [ ] Interesting findings documented with full URLs
- [ ] Output saved in JSON format for report integration
