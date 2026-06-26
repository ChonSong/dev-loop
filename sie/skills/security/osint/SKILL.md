---
name: security/osint
description: Use when performing passive reconnaissance and OSINT gathering — WHOIS, DNS enumeration, subdomain discovery, certificate transparency, search engine dorking, Shodan queries, GitHub recon, and Wayback Machine investigation.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, osint, recon, passive, subdomain, dns, whois, shodan, dorking, github]
    related_skills:
      - security/workflow
      - security/network-recon
      - security/directory-fuzz
      - security/tool-setup
---

# OSINT — Passive Reconnaissance

## Overview

Passive reconnaissance gathers information about a target without directly interacting with their systems. This skill covers WHOIS, DNS enumeration, subdomain discovery, certificate transparency logs, search engine dorking, Shodan/Censys queries, GitHub reconnaissance, and Wayback Machine investigation. Everything here is passive — no packets sent to the target.

## When to Use

- You're in the early recon phase of an assessment
- You need to build a target profile before active scanning
- You need to discover subdomains, IP ranges, or technology stack
- You need to find exposed credentials or data leaks
- You need historical information about the target
- You want to understand the organization's footprint

**Don't use for:** active scanning (use `security/network-recon`), web app testing (use `security/web-app-scan`).

## Tool Availability Check

```bash
whois --version
dig -v 2>&1 | head -1
subfinder -v 2>&1 | head -1
amass --version 2>&1 | head -1
theHarvester --version 2>&1 | head -1
```

Install: `sudo apt install whois dnsutils` + see tool setup for others.

## Phase 1: WHOIS & Domain Intelligence

```bash
# WHOIS lookup
whois target.com

# WHOIS for IP range
whois 198.51.100.1

# WHOIS with specific server
whois -h whois.arin.net 198.51.100.1

# Extract key information
whois target.com | grep -iE 'registrar|creation|expiration|name server|dnssec|orgname|address'

# Reverse WHOIS (find other domains registered by same entity)
# Use online tools: viewdns.info/reversewhois/ or whoisxmlapi.com
```

## Phase 2: DNS Enumeration

### DNS Records
```bash
# All records
dig any target.com +noall +answer

# Specific record types
dig a target.com +short                  # A record
dig aaaa target.com +short               # AAAA (IPv6)
dig mx target.com +short                 # Mail servers
dig ns target.com +short                 # Name servers
dig txt target.com +short                # TXT records (SPF, DKIM, verification)
dig soa target.com +short                # Start of Authority
dig cname target.com +short              # CNAME records

# Trace DNS resolution path
dig target.com +trace

# Check DNSSEC
dig target.com +dnssec

# Find authoritative nameserver and query directly
dig ns target.com +short | head -1 | xargs -I{} dig @{}. target.com any
```

### Zone Transfer
```bash
# Attempt zone transfer (rarely works but always try)
dig axfr @ns1.target.com target.com

# Try all nameservers
for ns in $(dig ns target.com +short); do
  echo "Trying zone transfer from $ns..."
  dig axfr @$ns target.com
done
```

### Reverse DNS
```bash
# Reverse lookup
dig -x 198.51.100.1 +short

# Reverse lookup for entire range
for ip in $(seq 1 254); do
  dig -x 198.51.100.$ip +short
done | grep -v '^$'

# Using dnsrecon for reverse lookup
dnsrecon -r 198.51.100.0/24 -n ns1.target.com
```

## Phase 3: Subdomain Enumeration

### Subfinder
```bash
# Basic subdomain enumeration
subfinder -d target.com -o subdomains.txt

# Silent mode with all sources
subfinder -d target.com -silent -all -o subdomains_all.txt

# With specific sources
subfinder -d target.com -sources crtsh,virustotal,shodan -o subdomains_sources.txt

# Multiple domains
subfinder -dL domains.txt -o all_subdomains.txt

# Include IP addresses
subfinder -d target.com -o subdomains.txt && \
  cat subdomains.txt | dnsx -silent -a -resp
```

### Amass
```bash
# Passive enumeration
amass enum -passive -d target.com -o amass_passive.txt

# Active enumeration (brute force + recursive)
amass enum -active -d target.com -o amass_active.txt

# With brute force and wordlist
amass enum -active -brute -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -d target.com -o amass_brute.txt

# Input from certificate transparency
amass enum -passive -d target.com -o amass_ct.txt

# Track changes over time
amass track -d target.com -last 2
```

### dnsrecon
```bash
# Standard enumeration
dnsrecon -d target.com -t std,brt -c dnsrecon_results.csv

# With zone transfer and SRV records
dnsrecon -d target.com -t std,brt,axfr,srv -D /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -c dnsrecon_full.csv

# Range enumeration for reverse lookups
dnsrecon -r 198.51.100.0/24 -n ns1.target.com
```

### theHarvester
```bash
# Comprehensive OSINT gathering
theHarvester -d target.com -b all -l 500 -f harvester_results

# Specific sources
theHarvester -d target.com -b google,bing,linkedin,shodan,censys -l 500

# With DNS brute force
theHarvester -d target.com -b all -c -f harvester_full
```

### Subdomain Brute Force
```bash
# Using dnsx for fast resolution
cat subdomains.txt | dnsx -silent -a -resp -o resolved.txt

# Using massdns (fastest for large lists)
massdns -r /usr/share/wordlists/dns-resolvers.txt -t A -o S \
  subdomains.txt -o massdns_results.txt
```

### Consolidate Results
```bash
# Combine all subdomain results, deduplicate, sort
cat subfinder.txt amass.txt dnsrecon.txt theHarvester.txt | \
  grep -oP '[\w.-]+\.target\.com' | sort -u > all_subdomains.txt

# Resolve all discovered subdomains
cat all_subdomains.txt | while read domain; do
  dig +short a "$domain" | head -1 | xargs -I{} echo "{} $domain"
done > resolved_subdomains.txt
```

## Phase 4: Certificate Transparency

### crt.sh
```bash
# Query via curl
curl -s "https://crt.sh/?q=%.target.com&output=json" | \
  python3 -m json.tool | grep -i name_value

# Extract unique subdomains
curl -s "https://crt.sh/?q=%.target.com&output=json" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
names = set()
for entry in data:
    for name in entry.get('name_value', '').split('\n'):
        if 'target.com' in name:
            names.add(name.strip())
for n in sorted(names):
    print(n)
" | sort -u > cert_subdomains.txt
```

### SSL/TLS Certificate Inspection
```bash
# Get certificate details
echo | openssl s_client -connect target.com:443 -servername target.com 2>/dev/null | \
  openssl x509 -noout -text | grep -E 'Subject:|Issuer:|DNS:|Not Before|Not After'

# Certificate transparency with sslscan
sslscan target.com:443 | grep -E 'Subject:|DNS:|Issuer'
```

## Phase 5: Search Engine Dorking

### Google Dorks
```
# Find subdomains
site:target.com -www

# Find login pages
site:target.com inurl:login
site:target.com inurl:admin
site:target.com inurl:signin
site:target.com intitle:"login"

# Find exposed files
site:target.com filetype:pdf
site:target.com filetype:xlsx
site:target.com filetype:doc
site:target.com filetype:sql
site:target.com filetype:log
site:target.com filetype:bak
site:target.com filetype:env
site:target.com filetype:conf
site:target.com filetype:config
site:target.com filetype:xml

# Find sensitive information
site:target.com inurl:wp-config
site:target.com "password" OR "passwd" OR "pwd"
site:target.com "api key" OR "api_key" OR "apikey"
site:target.com inurl:phpinfo
site:target.com inurl:git
site:target.com inurl:.env
site:target.com inurl:backup
site:target.com intitle:"index of"

# Find exposed panels
site:target.com inurl:phpmyadmin
site:target.com inurl:admin panel
site:target.com inurl:dashboard
site:target.com inurl:cpanel

# Find error messages
site:target.com "sql syntax" OR "mysql error" OR "ORA-"
site:target.com "Warning:" OR "Fatal error:" OR "Parse error:"
site:target.com "stack trace" OR "exception"

# Combine techniques
site:target.com filetype:pdf | filetype:xlsx | filetype:doc confidential
site:target.com intitle:"index of" "parent directory"
```

### Bing Dorks
```
same patterns as google but append site:target.com
Use Bing for results Google may miss
```

## Phase 6: Shodan & Censys

### Shodan CLI
```bash
# Search for target
shodan search target.com
shodan search "org:Target Organization"
shodan search "hostname:target.com"
shodan search "ssl.cert.subject.cn:target.com"
shodan search "net:198.51.100.0/24"

# Host information
shodan host 198.51.100.1

# Count results
shodan count target.com

# Download results
shodan download shodan_results target.com
shodan parse --fields ip_str,port,hostnames,org,os shodan_results.json.gz

# Specific service search
shodan search "http.title:\"Target Admin\""
shodan search "http.html:\"target.com\" port:8080"
```

### Shodan Web Queries (Free)
```
https://www.shodan.io/search?query=target.com
https://www.shodan.io/search?query=hostname%3Atarget.com
https://www.shodan.io/search?query=org%3A%22Target+Organization%22
```

### Censys
```
https://search.censys.io/domains/target.com
https://search.censys.io/hosts?q=target.com
https://search.censys.io/certificates?q=target.com
```

## Phase 7: GitHub Reconnaissance

```bash
# Search for exposed credentials
# Use GitHub search: https://github.com/search?q=target.com+password&type=code
# Use GitHub search: https://github.com/search?q=target.com+api_key&type=code
# Use GitHub search: https://github.com/search?q=target.com+secret&type=code

# Common GitHub dorks for target
# filename:.env target
# filename:wp-config target
# filename:config target password
# target.com api_key
# target.com password
# target.com aws_access_key_id
# filename:.htpasswd target
# filename:id_rsa target
# filename:.npmrc target
# filename:.dockercfg target

# Using GitHub CLI (gh)
gh search code "target.com password" --limit 100
gh search code "target.com api_key" --limit 100
gh search repos target.com --limit 50
```

### GitHub Org Reconnaissance
```bash
# List organization repositories
gh api orgs/target-org/repos --paginate | jq -r '.[].full_name'

# Search for secrets in org
gh search code --owner target-org "password" --limit 100
gh search code --owner target-org "api_key" --limit 100
```

## Phase 8: Wayback Machine

```bash
# List all URLs archived for a domain
curl -s "http://web.archive.org/cdx/search/cdx?url=target.com*&output=text&fl=original" | \
  sort -u > wayback_urls.txt

# Filter for specific file types
curl -s "http://web.archive.org/cdx/search/cdx?url=target.com*&output=text&fl=original" | \
  grep -E '\.(sql|bak|conf|env|zip|tar|gz|log|txt)$' > wayback_sensitive.txt

# Get archived page
curl -s "https://web.archive.org/web/20230101000000*/target.com/page" > archived_page.html

# Using waybackurls (gau)
gau target.com --o gau_urls.txt
gau target.com --subs --o gau_subs.txt  # Include subdomains

# Filter gau results
cat gau_urls.txt | grep -E '\.(js|json|xml|config|env|sql|bak)$' | sort -u
```

## Phase 9: Social Media & Employee Intelligence

```bash
# LinkedIn — understand org structure, technologies from job posts
# Search: site:linkedin.com "target.com" "engineer" OR "developer"
# Job postings reveal tech stack (look for required skills)

# Twitter — check for security posts, leaks
# Search: from:target username password
# Search: from:target site:twitter.com leak

# Paste sites — check for data leaks
# Search: site:pastebin.com target.com
# Search: site:pastebin.com "target.com password"

# Have I Been Pwned — check for breached emails
curl -s "https://haveibeenpwned.com/api/v3/breachedaccount/user@target.com" \
  -H "hibp-api-key: YOUR_API_KEY"
```

## Output: Target Profile Template

Consolidate all OSINT findings into a structured document:

```
TARGET PROFILE: target.com
Generated: <timestamp>

DOMAINS:
- target.com (primary)
- admin.target.com (discovered via subfinder)
- api.target.com (discovered via crt.sh)

IP RANGES:
- 198.51.100.0/24 (WHOIS)
- 203.0.113.0/24 (Shodan)

TECHNOLOGY STACK:
- Web server: Nginx 1.18 (WhatWeb)
- Backend: PHP 7.4 (X-Powered-By header)
- CMS: WordPress 5.8 (WPScan)
- Cloud: AWS (Shodan)
- Mail: Google Workspace (MX records)

EMPLOYEES (LinkedIn):
- John Smith, DevOps Engineer → Docker, AWS, Kubernetes
- Jane Doe, Backend Developer → Python, Django, PostgreSQL

EXPOSED CREDENTIALS:
- github.com/target-org/config (AWS keys in commit history)
- pastebin.com/xyz (database credentials from 2023)

EXPOSED SERVICES:
- admin.target.com:8080 → Jenkins (Shodan)
- git.target.com → GitLab (subdomain enum)
- phpmyadmin.target.com → phpMyAdmin (directory fuzz)

HISTORICAL DATA:
- 2022: Old WordPress plugin (vulnerable) still present in archive
- 2021: /backup.sql available via Wayback Machine
```

## Common Pitfalls

1. **Active scanning during passive phase.** OSINT is passive. Don't send packets to the target during this phase.
2. **Not documenting sources.** Every finding needs a source reference (URL, tool, timestamp). Without it, findings aren't reproducible.
3. **Ignoring certificate transparency.** crt.sh is one of the best subdomain discovery sources and is often overlooked.
4. **Not checking paste sites.** Credentials, config files, and database dumps regularly appear on pastebin and similar sites.
5. **Scope creep in OSINT.** It's easy to find interesting data outside scope. Document everything but clearly mark in-scope vs out-of-scope.
6. **Forgetting the Wayback Machine.** Old backup files, config files, and vulnerable plugins are often archived.
7. **Not using multiple subdomain tools.** Each tool uses different sources. Subfinder + Amass + crt.sh together give the most complete picture.

## Verification Checklist

- [ ] WHOIS lookup completed for all domains and IPs
- [ ] All DNS record types enumerated (A, AAAA, MX, NS, TXF, SOA, CNAME)
- [ ] Zone transfer attempted against all nameservers
- [ ] Subdomain enumeration completed with at least 3 tools/sources
- [ ] Certificate transparency logs queried (crt.sh)
- [ ] Search engine dorking completed for sensitive files and information
- [ ] Shodan/Censys queried for exposed services
- [ ] GitHub searched for exposed credentials and config
- [ ] Wayback Machine queried for historical exposed content
- [ ] Social media and paste sites checked
- [ ] Target profile document created with all findings
- [ ] All findings documented with source and timestamp
