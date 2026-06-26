---
name: trailofbits/audit-context-building
description: Use when building deep architectural context for a security audit. Covers codebase mapping, trust boundary identification, data flow analysis, threat modeling integration (STRIDE/DREAD), and architecture review checklists.
version: 2.0.0
author: Trail of Bits (original), OWL (expansion)
license: MIT
metadata:
  hermes:
    tags: [security, audit, architecture, threat-modeling, code-review, trust-boundaries]
    related_skills:
      - trailofbits/static-analysis
      - security-review
      - security/vuln-assessment
      - security/workflow
---

# Audit Context Building

## Overview

Before you can effectively audit code for security vulnerabilities, you need to understand the system's architecture, trust boundaries, data flows, and threat surface. This skill provides a structured approach to building deep architectural context — the foundation that makes all subsequent security analysis more effective and targeted.

## When to Use

- Starting a security audit of an unfamiliar codebase
- Preparing for a penetration test of a web application
- Building a threat model for a new system
- Reviewing architecture for security weaknesses
- Understanding trust boundaries before testing

## Phase 1: Codebase Mapping

### Initial Survey
```bash
# Clone the repo (if not already)
git clone <repo_url> /tmp/audit_target
cd /tmp/audit_target

# Get an overview of the codebase structure
find . -maxdepth 2 -type f -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" | head -20

# Count files by language
find . -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20

# Find entry points
ls -la | grep -E 'main|app|server|index|router|handler|controller'

# Find configuration files
find . -name "*.config.*" -o -name "*.env*" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" | grep -v node_modules | grep -v .git

# Find database models/schemas
find . -type f \( -name "*model*" -o -name "*schema*" -o -name "*entity*" \) | grep -v node_modules

# Find authentication/authorization code
grep -r "auth\|login\|session\|token\|permission\|role" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" --include="*.java" -l | grep -v node_modules | grep -v .git
```

### Architecture Discovery
```bash
# Identify the tech stack
cat package.json 2>/dev/null | grep -E '"dependencies"|"devDependencies"' -A 50 | head -30
cat requirements.txt 2>/dev/null
cat go.mod 2>/dev/null | head -20
cat pom.xml 2>/dev/null | grep -E '<artifactId>|<version>' | head -30
cat Gemfile 2>/dev/null

# Find API endpoints/routes
grep -r "route\|@app\|@router\|@GetMapping\|@PostMapping\|app.get\|app.post\|router\|fastapi\|flask\|express" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules

# Find database queries
grep -r "SELECT\|INSERT\|UPDATE\|DELETE\|query\|execute\|db\.\|connection\|pool\|ORM\|sequelize\|sqlalchemy\|gorm\|jdbc" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules

# Find crypto usage
grep -r "crypto\|encrypt\|decrypt\|hash\|bcrypt\|scrypt\|argon2\|aes\|rsa\|hmac\|signature\|certificate\|tls\|ssl" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules
```

## Phase 2: Trust Boundary Identification

### What Are Trust Boundaries?

Trust boundaries are points where data crosses from one trust level to another:
- **User input → Application** (untrusted → trusted)
- **Application → Database** (trusted → trusted, but different privilege)
- **Application → External API** (trusted → external)
- **Frontend → Backend** (client → server)
- **Service A → Service B** (internal microservices)
- **Application → File System** (application → OS)

### Mapping Trust Boundaries
```bash
# Find all input sources
echo "=== HTTP Input ==="
grep -r "req\.body\|req\.query\|req\.params\|request\.GET\|request\.POST\|@RequestBody\|@RequestParam\|ctx\.Request\|r\.Form" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules

echo "=== File Upload ==="
grep -r "upload\|multer\|formidable\|multipart\|FileUpload\|file\.content" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules

echo "=== External API Calls ==="
grep -r "fetch\|axios\|http\.get\|http\.post\|requests\.get\|requests\.post\|restTemplate\|HttpClient" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules

echo "=== Database ==="
grep -r "SELECT\|INSERT\|UPDATE\|DELETE\|query\|execute\|createQueryBuilder\|findBy\|save\|create" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules

echo "=== File System ==="
grep -r "fs\.\|open(\|readFile\|writeFile\|os\.ReadFile\|os\.WriteFile\|ioutil\|FileInputStream\|FileOutputStream" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules
```

### Trust Boundary Checklist
For each boundary identified, document:
- [ ] **What data crosses the boundary?** (user input, API response, file content)
- [ ] **How is the data validated?** (input validation, sanitization, type checking)
- [ ] **What happens if validation fails?** (error handling, default values, rejection)
- [ ] **What's the privilege level on each side?** (user, application, admin, system)
- [ ] **How does data flow downstream?** (is validated data used safely?)

## Phase 3: Data Flow Analysis

### Identify Sensitive Data Flows

Track these types of data through the codebase:

```bash
# PII (Personally Identifiable Information)
grep -r "email\|ssn\|social_security\|credit_card\|passport\|dob\|date_of_birth\|phone\|address\|name" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules

# Credentials
grep -r "password\|secret\|api_key\|apikey\|token\|private_key\|credential" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules

# Financial Data
grep -r "payment\|transaction\|balance\|amount\|invoice\|billing\|charge" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" -l | grep -v node_modules
```

### Data Flow Documentation Template

For each sensitive data type:

```
=== Data Flow: User Email ===

Source:         req.body.email (POST /register)
Validation:     Joi.string().email() (auth.js:42)
Storage:        db.users.insert({ email }) (auth.js:58)
Encryption:     None in transit (HTTPS handled by reverse proxy)
                None at rest (stored plaintext in PostgreSQL)
Logging:        logger.info({ email }) (auth.js:60) ⚠️ LOGGED IN PLAINTEXT
Output:         Email rendered in profile page (profile.js:112)
                Email sent to third-party analytics (analytics.js:33)

Risk Assessment:
- Email logged in plaintext → PII in logs
- No encryption at rest → DB breach exposes emails
- Third-party sharing → No consent mechanism visible
```

## Phase 4: Threat Modeling (STRIDE)

### STRIDE Categories

| Category | Threat | Code-Level Indicators |
|----------|--------|----------------------|
| **S**poofing | Impersonating a user/service | Weak auth, predictable tokens, no MFA |
| **T**ampering | Modifying data/code | Missing integrity checks, no signatures |
| **R**epudiation | Denying actions occurred | Missing audit logs, no non-repudiation |
| **I**nformation Disclosure | Exposing sensitive data | Verbose errors, missing access controls, logs with secrets |
| **D**enial of Service | Making system unavailable | No rate limiting, resource exhaustion vectors |
| **E**levation of Privilege | Gaining unauthorized access | Missing authz checks, IDOR, broken access control |

### STRIDE Analysis Checklist

For each component/module:

**Spoofing:**
- [ ] How is authentication implemented?
- [ ] Are sessions/tokens properly generated and validated?
- [ ] Is there MFA?
- [ ] Are API keys/secrets properly managed?

**Tampering:**
- [ ] Is input validated on the server side?
- [ ] Are database queries parameterized?
- [ ] Are file uploads validated (type, size, content)?
- [ ] Is there integrity verification for updates/downloads?

**Repudiation:**
- [ ] Are sensitive actions logged (login, admin actions, data changes)?
- [ ] Do logs include who, what, when?
- [ ] Are logs protected from tampering?

**Information Disclosure:**
- [ ] Do error messages leak internal details? (stack traces, DB errors)
- [ ] Are sensitive fields exposed in API responses? (passwords, tokens, PII)
- [ ] Are logs free of sensitive data?
- [ ] Is sensitive data encrypted at rest and in transit?

**Denial of Service:**
- [ ] Is there rate limiting on API endpoints?
- [ ] Are there resource limits (file upload size, query result limits)?
- [ ] Are there timeout configurations?

**Elevation of Privilege:**
- [ ] Is authorization checked on every endpoint?
- [ ] Are there horizontal privilege escalation vectors? (IDOR)
- [ ] Are there vertical privilege escalation vectors? (user → admin)
- [ ] Are admin functions properly protected?

## Phase 5: Architecture Review Checklist

### High-Level Architecture
- [ ] What is the deployment model? (monolith, microservices, serverless)
- [ ] What are the trust zones? (DMZ, internal, external)
- [ ] What's the network architecture? (load balancer, reverse proxy, CDN)
- [ ] What databases are used? (SQL, NoSQL, in-memory)
- [ ] What external services are integrated? (APIs, SaaS, cloud)

### Security Architecture
- [ ] Is TLS used for all external communication?
- [ ] Is there a WAF? (Web Application Firewall)
- [ ] Are there security headers? (CSP, HSTS, X-Frame-Options)
- [ ] Is there logging and monitoring? (SIEM, alerting)
- [ ] Is there an incident response plan?
- [ ] How is secret management handled? (vault, env vars, config files)

### Code Security
- [ ] Are dependencies up to date? (check for known CVEs)
- [ ] Is there a dependency audit process? (npm audit, pip audit, etc.)
- [ ] Is there input validation? (on all input sources)
- [ ] Is there output encoding? (XSS prevention)
- [ ] Is parameterized queries used? (SQL injection prevention)
- [ ] Are there hardcoded secrets in code?

## Common Pitfalls

1. **Starting code review without understanding the codebase.** You'll miss context-specific vulnerabilities that require understanding the architecture.
2. **Ignoring trust boundaries.** Most vulnerabilities exist at trust boundaries — that's where untrusted data enters the system.
3. **Only looking at code, not configuration.** Security issues often live in config files, deployment scripts, and infrastructure setup.
4. **Not documenting data flow.** Without tracking sensitive data, you miss information disclosure risks.
5. **Threat modeling only once.** Threat models should be updated as the system evolves.

## Verification Checklist

- [ ] Codebase structure mapped (languages, frameworks, entry points)
- [ ] Architecture diagram created (components, data stores, external services)
- [ ] Trust boundaries identified and documented
- [ ] Sensitive data flows tracked end-to-end
- [ ] STRIDE analysis completed for each component
- [ ] Architecture review checklist completed
- [ ] Threat model documented with identified risks prioritized
