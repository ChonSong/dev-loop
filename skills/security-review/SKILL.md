---
name: security-review
description: Use when performing a security code review or application security assessment. Provides the OWASP Top 10 (2021) checklist with testing procedures, severity ratings, and remediation templates for each vulnerability category.
version: 2.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, code-review, owasp, audit, checklist, web-security]
    related_skills:
      - trailofbits/static-analysis
      - trailofbits/audit-context-building
      - security/web-app-scan
      - security/vuln-assessment
---

# Security Code Review — OWASP Top 10

## Overview

This skill provides a structured checklist for reviewing applications for security vulnerabilities, organized by the OWASP Top 10 (2021). Each category includes what to look for, how to test, severity guidance, and remediation recommendations.

## When to Use

- Performing a manual security code review
- Reviewing pull requests for security issues
- Assessing an application before deployment
- Preparing for a penetration test (understanding what to look for)
- Training developers on secure coding

## OWASP Top 10 (2021) Categories

### A01:2021 — Broken Access Control

**What to look for:**
- Insecure Direct Object References (IDOR): `/api/user/123` — can I access `/api/user/124`?
- Missing authorization checks on endpoints
- Privilege escalation (user → admin)
- CORS misconfiguration (wildcard `*` origins)
- Directory traversal: `../../../etc/passwd`
- Forced browsing to admin pages
- JWT/token manipulation

**Testing checklist:**
```bash
# IDOR testing — change IDs in URLs
curl http://target.com/api/user/123/profile  # Your profile
curl http://target.com/api/user/124/profile  # Someone else's?

# Method tampering
curl -X DELETE http://target.com/api/user/123  # Can a user delete?
curl -X PUT http://target.com/api/user/123/role -d '{"role":"admin"}'  # Priv escalation?

# CORS testing
curl -H "Origin: https://evil.com" http://target.com/api/data
# Check response for: Access-Control-Allow-Origin: https://evil.com

# Path traversal
curl http://target.com/download?file=../../../etc/passwd
curl http://target.com/download?file=....//....//etc/passwd
```

**Code patterns to flag:**
```python
# BAD: No authorization check
@app.route('/api/user/<id>')
def get_user(id):
    return User.query.get(id)  # Any user can access any profile

# GOOD: Authorization check
@app.route('/api/user/<id>')
def get_user(id):
    if current_user.id != int(id) and not current_user.is_admin:
        abort(403)
    return User.query.get(id)
```

**Remediation:**
- Implement authorization checks on every endpoint
- Use indirect object references (UUIDs instead of sequential IDs)
- Deny by default — whitelist allowed actions
- Implement proper CORS policies (specific origins, not `*`)
- Use a centralized authorization framework

---

### A02:2021 — Cryptographic Failures

**What to look for:**
- Passwords stored in plaintext or with weak hashing (MD5, SHA1)
- Sensitive data transmitted over HTTP (not HTTPS)
- Weak TLS configuration (SSLv3, TLS 1.0, weak ciphers)
- Hardcoded encryption keys in source code
- Predictable random number generation (`Math.random()`, `rand()`)
- Missing encryption at rest for sensitive data

**Testing checklist:**
```bash
# Check TLS configuration
nmap --script ssl-enum-ciphers -p 443 target.com
sslscan target.com
testssl.sh target.com

# Check for HTTP (non-HTTPS) endpoints
curl -I http://target.com/login  # Should redirect to HTTPS

# Check for sensitive data in URLs
grep -r "password\|token\|secret\|key" --include="*.js" --include="*.py" ./src/

# Check for hardcoded secrets
grep -r "API_KEY\|SECRET\|PASSWORD\|PRIVATE_KEY" --include="*.py" --include="*.js" --include="*.go" ./src/
```

**Code patterns to flag:**
```python
# BAD: Weak hashing
import hashlib
hash = hashlib.md5(password.encode()).hexdigest()

# GOOD: Strong hashing
import bcrypt
hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# BAD: Hardcoded key
SECRET_KEY = "my-secret-key-12345"

# GOOD: Environment variable
SECRET_KEY = os.environ.get('SECRET_KEY')
```

**Remediation:**
- Use bcrypt, scrypt, or argon2 for password hashing
- Enforce TLS 1.2+ everywhere
- Use strong cipher suites (AES-256-GCM, ChaCha20)
- Store secrets in a vault (HashiCorp Vault, AWS Secrets Manager)
- Use `secrets` module (Python) or `crypto/rand` (Go) for random generation

---

### A03:2021 — Injection

**What to look for:**
- SQL injection (string concatenation in queries)
- Command injection (`os.system`, `subprocess` with user input)
- LDAP injection
- XML injection (XXE)
- Template injection (SSTI)
- NoSQL injection
- Header injection

**Testing checklist:**
```bash
# SQL injection
curl "http://target.com/page?id=1' OR '1'='1"
curl "http://target.com/page?id=1; DROP TABLE users--"
curl "http://target.com/page?id=1 UNION SELECT 1,2,3--"

# Command injection
curl "http://target.com/ping?host=127.0.0.1;id"
curl "http://target.com/ping?host=127.0.0.1|cat /etc/passwd"
curl "http://target.com/ping?host=$(whoami)"

# XXE (XML External Entity)
curl -X POST http://target.com/api/xml \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>'

# SSTI (Server-Side Template Injection)
curl "http://target.com/page?name={{7*7}}"
curl "http://target.com/page?name=${7*7}"
```

**Code patterns to flag:**
```python
# BAD: SQL injection
query = "SELECT * FROM users WHERE id = " + user_input
cursor.execute(query)

# GOOD: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_input,))

# BAD: Command injection
os.system("ping " + user_input)

# GOOD: Safe command execution
subprocess.run(["ping", "-c", "4", user_input], capture_output=True)
```

**Remedification:**
- Use parameterized queries / prepared statements for ALL database access
- Use ORM (SQLAlchemy, Django ORM, GORM) instead of raw SQL
- Validate and sanitize all input
- Use allowlists for input validation
- Avoid `eval()`, `exec()`, `os.system()` with user input
- Disable external entity processing in XML parsers

---

### A04:2021 — Insecure Design

**What to look for:**
- Missing rate limiting on authentication endpoints
- No account lockout mechanism
- Business logic flaws (negative quantities, price manipulation)
- Missing CAPTCHA on sensitive operations
- Weak password policy
- No session timeout
- Missing audit logging for sensitive actions

**Testing checklist:**
```bash
# Rate limiting test — send 100 login requests rapidly
for i in $(seq 1 100); do
  curl -X POST http://target.com/login -d "user=admin&pass=wrong"
done
# If no lockout after 100 attempts = missing rate limiting

# Business logic — negative quantity
curl -X POST http://target.com/cart/add -d "item=123&qty=-1&price=100"

# Business logic — price manipulation
curl -X POST http://target.com/checkout -d "item=123&price=0.01"

# Session timeout — wait and retry
curl -b "session=old_token" http://target.com/dashboard
# If still valid after hours = no session timeout
```

**Remediation:**
- Implement rate limiting (e.g., 5 attempts per 15 minutes)
- Implement account lockout (temporary, not permanent)
- Validate business logic server-side (never trust client-side validation)
- Implement session timeout (30 minutes idle, 8 hours absolute)
- Log all sensitive actions (login, admin, data changes)
- Use CAPTCHA for sensitive operations

---

### A05:2021 — Security Misconfiguration

**What to look for:**
- Default credentials (admin/admin, root/root)
- Verbose error messages (stack traces, debug info)
- Unnecessary features enabled (debug mode, directory listing)
- Missing security headers
- Outdated software versions
- Exposed configuration files (.env, .git, .svn)
- Open cloud storage (S3 buckets, Azure blobs)

**Testing checklist:**
```bash
# Check for default credentials
curl -X POST http://target.com/admin -d "user=admin&pass=admin"
curl -X POST http://target.com/admin -d "user=admin&pass=password"

# Check for debug mode
curl http://target.com/debug
curl http://target.com/__debug__/
curl -X DEBUG http://target.com/

# Check security headers
curl -I http://target.com | grep -iE "x-frame|x-content|strict-transport|content-security|x-xss"

# Check for exposed files
curl http://target.com/.env
curl http://target.com/.git/HEAD
curl http://target.com/.svn/entries
curl http://target.com/robots.txt
curl http://target.com/sitemap.xml
curl http://target.com/crossdomain.xml
curl http://target.com/security.txt

# Check for directory listing
curl http://target.com/images/
curl http://target.com/assets/

# Check for open S3 buckets
aws s3 ls s3://target-bucket --no-sign-request 2>/dev/null
```

**Security headers to check:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

**Remediation:**
- Change all default credentials
- Disable debug mode in production
- Implement all security headers
- Disable directory listing
- Remove unnecessary files from web root
- Regular dependency updates
- Use a configuration management tool

---

### A06:2021 — Vulnerable and Outdated Components

**What to look for:**
- Outdated frameworks/libraries with known CVEs
- Unpatched software versions
- End-of-life components
- Missing security patches
- Unmanaged dependencies

**Testing checklist:**
```bash
# Check versions from HTTP headers
curl -I http://target.com | grep -iE "server|x-powered-by|x-aspnet-version"

# Check for known JavaScript libraries
grep -r "jquery\|angular\|react\|vue\|bootstrap" --include="*.html" --include="*.js" ./ | grep -oE '[0-9]+\.[0-9]+\.[0-9]+'

# Python dependency audit
pip audit
safety check

# Node.js dependency audit
npm audit
npm audit --audit-level=high

# Java dependency audit
mvn org.owasp:dependency-check-maven:check

# Ruby dependency audit
bundle-audit check --update
```

**Remediation:**
- Maintain a software bill of materials (SBOM)
- Automate dependency scanning in CI/CD
- Subscribe to security advisories for used components
- Have a patch management process
- Remove unused dependencies

---

### A07:2021 — Identification and Authentication Failures

**What to look for:**
- Weak password policy
- No multi-factor authentication
- Session fixation
- Session IDs in URLs
- Credential stuffing vulnerability
- Brute force vulnerability (no rate limiting)
- Weak password reset flow
- "Remember me" implementation flaws

**Testing checklist:**
```bash
# Test password policy
curl -X POST http://target.com/register -d "user=test&pass=a"  # Single char password?

# Test for credential stuffing
for pass in password123 admin123 welcome1; do
  curl -X POST http://target.com/login -d "user=admin&pass=$pass"
done

# Check session ID in URL
curl -I http://target.com/login | grep -i location
# If URL contains session ID = bad practice

# Test password reset
curl -X POST http://target.com/reset -d "email=target@example.com"
# Check if token is predictable, if it expires, if it's single-use

# Test session fixation
curl -c cookies.txt http://target.com/login
SESSION_ID=$(grep session cookies.txt | awk '{print $7}')
curl -b "session=$SESSION_ID" -X POST http://target.com/login -d "user=admin&pass=pass"
# If session ID doesn't change after login = session fixation
```

**Remediation:**
- Enforce strong password policy (12+ chars, complexity)
- Implement MFA (TOTP, WebAuthn)
- Regenerate session ID after login
- Implement rate limiting on authentication
- Use secure password reset (time-limited, single-use tokens)
- Never put session IDs in URLs

---

### A08:2021 — Software and Data Integrity Failures

**What to look for:**
- Unsigned software updates
- Insecure deserialization
- CI/CD pipeline vulnerabilities
- Missing integrity verification for dependencies
- Auto-update without signature verification

**Testing checklist:**
```bash
# Check for insecure deserialization (Python)
# Look for: pickle.loads(), yaml.load(), marshal.loads()

grep -r "pickle.loads\|yaml.load\|marshal.loads\|unserialize" --include="*.py" --include="*.php" ./src/

# Check for unsigned updates
# Look at update mechanism — does it verify signatures?

# Check CI/CD secrets
grep -r "AWS_ACCESS\|DOCKER_PASSWORD\|NPM_TOKEN" --include="*.yml" --include="*.yaml" ./.github/
```

**Remediation:**
- Sign all software updates
- Use safe deserialization (JSON instead of pickle)
- Verify dependency integrity (checksums, signatures)
- Secure CI/CD pipelines (secret management, branch protection)
- Implement Content Security Policy

---

### A09:2021 — Security Logging and Monitoring Failures

**What to look for:**
- No logging of authentication events
- No logging of failed login attempts
- No logging of sensitive operations
- Logs not monitored or alerted on
- Logs stored insecurely
- Sensitive data in logs (passwords, tokens, PII)

**Testing checklist:**
```bash
# Trigger events and check if they're logged
curl -X POST http://target.com/login -d "user=admin&pass=wrong"  # Should log failed login
curl http://target.com/admin  # Should log admin access
curl -X DELETE http://target.com/api/user/1  # Should log deletion

# Check for sensitive data in logs
grep -r "password\|token\|secret\|credit_card" --include="*.log" ./logs/

# Check log file permissions
ls -la ./logs/
# Logs should not be world-readable
```

**Remediation:**
- Log all authentication events (success and failure)
- Log all sensitive operations (admin, data changes, deletions)
- Never log sensitive data (passwords, tokens, PII)
- Implement log monitoring and alerting
- Protect log files (encryption, access controls)
- Implement a SIEM solution

---

### A10:2021 — Server-Side Request Forgery (SSRF)

**What to look for:**
- URL parameters that fetch external resources
- Webhook URLs
- PDF generators that accept URLs
- Image resizers that accept URLs
- Import from URL features

**Testing checklist:**
```bash
# Basic SSRF
curl "http://target.com/fetch?url=http://127.0.0.1:8080"
curl "http://target.com/fetch?url=http://169.254.169.254/latest/meta-data/"  # AWS metadata
curl "http://target.com/fetch?url=http://localhost:5432"  # Internal services

# SSRF via file://
curl "http://target.com/fetch?url=file:///etc/passwd"

# SSRF via DNS rebinding
curl "http://target.com/fetch?url=http://attacker-controlled.com"

# Cloud metadata endpoints
curl "http://target.com/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/"
curl "http://target.com/fetch?url=http://metadata.google.internal/computeMetadata/v1/"
```

**Code patterns to flag:**
```python
# BAD: Direct URL fetch
import requests
response = requests.get(request.GET['url'])

# GOOD: URL validation
from urllib.parse import urlparse
parsed = urlparse(url)
if parsed.hostname in ALLOWED_HOSTS and parsed.scheme in ('http', 'https'):
    response = requests.get(url)
else:
    raise ValueError("URL not allowed")
```

**Remediation:**
- Validate and whitelist allowed URLs/destrictions
- Block internal IP ranges (10.x, 172.16.x, 192.168.x, 127.x, 169.254.x)
- Disable unnecessary URL schemes (file://, gopher://, dict://)
- Implement network segmentation (app servers can't reach metadata endpoints)
- Use a dedicated service for external requests with restricted network access

## Severity Rating Guide

| Severity | Criteria | Examples |
|----------|----------|----------|
| **Critical** | Direct system compromise, data breach | RCE, SQL injection with data access, auth bypass |
| **High** | Significant data exposure, privilege escalation | IDOR, SSRF to metadata, stored XSS in admin |
| **Medium** | Limited impact, requires conditions | Reflected XSS, CSRF, information disclosure |
| **Low** | Minimal impact, defense in depth | Missing security headers, verbose errors |
| **Info** | Best practice, no direct exploitability | Missing HSTS, weak cipher preference |

## Verification Checklist

- [ ] A01: Access control tested (IDOR, privilege escalation, CORS)
- [ ] A02: Cryptography reviewed (hashing, TLS, secrets management)
- [ ] A03: Injection tested (SQL, command, XXE, SSTI)
- [ ] A04: Business logic reviewed (rate limiting, validation)
- [ ] A05: Configuration reviewed (defaults, headers, exposed files)
- [ ] A06: Dependencies audited (known CVEs, outdated versions)
- [ ] A07: Authentication reviewed (password policy, MFA, sessions)
- [ ] A08: Integrity reviewed (deserialization, update signing)
- [ ] A09: Logging reviewed (event coverage, sensitive data in logs)
- [ ] A10: SSRF tested (URL parameters, cloud metadata)
- [ ] All findings documented with severity and remediation
