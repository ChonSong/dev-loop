---
name: jthack/ffuf-claude-skill
description: Use when performing web content discovery and fuzzing with ffuf. Covers directory brute-forcing, file extension fuzzing, parameter discovery, virtual host enumeration, recursive scanning, and result triage. This is the definitive ffuf reference.
version: 2.0.0
author: jthack (original), OWL (expansion)
license: MIT
metadata:
  hermes:
    tags: [security, ffuf, fuzzing, web, directories, parameters, vhost, enumeration]
    related_skills:
      - security/directory-fuzz
      - security/web-app-scan
      - security/osint
      - security/tool-setup
---

# ffuf — Web Fuzzer

## Overview

ffuf (Fuzz Faster U Fool) is a fast web fuzzer for discovering hidden content, parameters, and virtual hosts. This skill is a complete reference for ffuf usage — directory fuzzing, extension fuzzing, parameter discovery, vhost enumeration, recursive scanning, and result parsing.

> **Note:** This skill is a superset of `security/directory-fuzz`. Use that skill for the broader fuzzing workflow; use this skill when you need the complete ffuf reference.

## When to Use

- Discovering hidden directories and files on a web server
- Finding URL parameters for further testing
- Enumerating virtual hosts / subdomains
- Fuzzing for specific file types (.php, .bak, .sql)
- Recursive content discovery
- Rate-limited fuzzing on production targets

## Installation & Verification

```bash
# Install
sudo apt install ffuf
# or
go install github.com/ffuf/ffuf/v2@latest

# Verify
ffuf -V
```

## Core Concepts

### Fuzzing Positions (FUZZ keyword)
```bash
# URL path fuzzing
ffuf -w wordlist.txt -u http://target.com/FUZZ

# Extension fuzzing
ffuf -w wordlist.txt -u http://target.com/index.FUZZ

# Host header fuzzing (vhost discovery)
ffuf -w wordlist.txt -u http://target.com -H "Host: FUZZ.target.com"

# Parameter name fuzzing
ffuf -w wordlist.txt -u http://target.com/page?FUZZ=value

# Parameter value fuzzing
ffuf -w wordlist.txt -u http://target.com/page?id=FUZZ

# Multi-position fuzzing
ffuf -w users.txt:W1 -w passwords.txt:W2 -u http://target.com/W1/W2
```

### Wordlists
```bash
# Kali standard wordlists
/usr/share/wordlists/dirb/common.txt           # ~4.6K entries
/usr/share/wordlists/dirb/big.txt              # ~20K entries
/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt  # ~220K
/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt   # ~624K
/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt
/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt
```

## Recipes

### Directory Discovery
```bash
# Basic
ffuf -w /usr/share/wordlists/dirb/common.txt -u http://target.com/FUZZ -mc all -fc 404

# With extensions
ffuf -w /usr/share/wordlists/dirb/common.txt -u http://target.com/FUZZ \
  -e .php,.html,.asp,.aspx,.jsp,.txt,.bak,.old,.zip,.tar,.gz -mc all -fc 404

# Large wordlist with JSON output
ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
  -u http://target.com/FUZZ -mc all -fc 404 -of json -o dirs.json
```

### Recursive Scanning
```bash
# Recurse into discovered directories
ffuf -w /usr/share/wordlists/dirb/common.txt -u http://target.com/FUZZ \
  -recursion -recursion-depth 2 -mc all -fc 404

# Recurse only on 200/301/302/403
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -recursion -recursion-strategy greedy -recursion-depth 3 -mc 200,301,302,403
```

### Virtual Host Discovery
```bash
# Vhost enumeration
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -u http://target.com -H "Host: FUZZ.target.com" -fs 0 -mc all

# Filter by size (find vhosts with different content)
ffuf -w wordlist.txt -u http://target.com -H "Host: FUZZ.target.com" -fs 150
```

### Parameter Discovery
```bash
# GET parameter names
ffuf -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -u http://target.com/page?FUZZ=value -fs 0

# POST parameters
ffuf -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -u http://target.com/login -X POST -d "FUZZ=value&password=test" \
  -H "Content-Type: application/x-www-form-urlencoded" -fs 0

# Multi-parameter
ffuf -w params.txt:W1 -w params.txt:W2 \
  -u http://target.com/page?W1=val1&W2=val2 -fs 0
```

### Filtering
```bash
# Filter status codes
ffuf -w wordlist.txt -u http://target.com/FUZZ -fc 404,403,401

# Filter response size
ffuf -w wordlist.txt -u http://target.com/FUZZ -fs 0

# Filter word count
ffuf -w wordlist.txt -u http://target.com/FUZZ -fw 0

# Filter line count
ffuf -w wordlist.txt -u http://target.com/FUZZ -fl 0

# Match specific status codes
ffuf -w wordlist.txt -u http://target.com/FUZZ -mc 200,301,302,403

# Regex filter
ffuf -w wordlist.txt -u http://target.com/FUZZ -fr "Not Found"
```

### Rate Limiting (Production)
```bash
# Add delay between requests
ffuf -w wordlist.txt -u http://target.com/FUZZ -p 0.1-0.5 -mc all -fc 404

# Limit concurrent threads
ffuf -w wordlist.txt -u http://target.com/FUZZ -t 5 -mc all -fc 404

# Combined slow scan
ffuf -w wordlist.txt -u http://target.com/FUZZ -t 3 -p 0.5 -mc all -fc 404
```

### Authentication
```bash
# Cookie-based
ffuf -w wordlist.txt -u http://target.com/FUZZ -b "session=abc123; token=xyz" -mc all -fc 404

# Custom headers
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -H "Authorization: Bearer TOKEN" -H "X-Custom: value" -mc all -fc 404

# Basic auth
ffuf -w wordlist.txt -u http://target.com/FUZZ \
  -H "Authorization: Basic $(echo -n 'admin:pass' | base64)" -mc all -fc 404
```

### POST Body Fuzzing
```bash
# JSON body
ffuf -w wordlist.txt -u http://target.com/api/login -X POST \
  -d '{"username":"admin","password":"FUZZ"}' \
  -H "Content-Type: application/json" -fr "Invalid credentials"

# Form data
ffuf -w wordlist.txt -u http://target.com/login -X POST \
  -d "username=admin&password=FUZZ" \
  -H "Content-Type: application/x-www-form-urlencoded" -fr "Invalid"
```

### Output Formats
```bash
# JSON (best for parsing)
ffuf -w wordlist.txt -u http://target.com/FUZZ -of json -o results.json

# CSV
ffuf -w wordlist.txt -u http://target.com/FUZZ -of csv -o results.csv

# HTML report
ffuf -w wordlist.txt -u http://target.com/FUZZ -of html -o results.html

# All formats
ffuf -w wordlist.txt -u http://target.com/FUZZ -of all -o results
```

## Result Parsing

### JSON Output
```bash
# Extract discovered paths
python3 -c "
import json
with open('results.json') as f:
    data = json.load(f)
for r in data['results']:
    print(f\"{r['status']:>5} {r['length']:>10} {r['url']}\")
"

# Filter by status
python3 -c "
import json
with open('results.json') as f:
    data = json.load(f)
for r in data['results']:
    if r['status'] in [200, 301, 302, 403]:
        print(f\"{r['status']} {r['url']}\")
"

# Extract just URLs
python3 -c "
import json
with open('results.json') as f:
    data = json.load(f)
for r in data['results']:
    print(r['url'])
" > discovered_urls.txt
```

### CSV Output
```bash
# Parse CSV
python3 -c "
import csv
with open('results.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f\"{row['status']} {row['url']}\")
"
```

## Common Pitfalls

1. **Not filtering size.** Without `-fs`/`-fc`, you'll get thousands of false positives from soft 404s.
2. **Recursive fuzzing without depth limit.** Start with depth 1-2. Monitor request count.
3. **Using on production without rate limiting.** Always use `-p 0.1-0.5` on production.
4. **Missing `-mc all`.** Default only shows 200. You need 301/302/403/401 too.
5. **Forgetting extensions.** `/admin` might 404 but `/admin.php` returns 200.
6. **Not checking for WAF.** If all responses are the same size, you may be hitting a WAF.
7. **Using a tiny wordlist.** `dirb/common.txt` has ~4,600 entries. Use at least `raft-medium` (~220K) for real assessments.

## Verification Checklist

- [ ] Directory fuzzing completed with appropriate wordlist
- [ ] Extension fuzzing completed (.php, .html, .asp, .txt, .bak, .zip)
- [ ] Recursive scanning completed (depth 2+)
- [ ] Vhost enumeration attempted
- [ ] Parameter fuzzing attempted on key endpoints
- [ ] Results filtered and triaged by status code
- [ ] Output saved in JSON format
- [ ] Interesting findings documented with full URLs
