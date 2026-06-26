---
name: trailofbits/static-analysis
description: Use when performing static application security testing (SAST). Covers Semgrep rule writing, language-specific scanning (Python/bandit, Node.js/njsscan, Go/gosec, Java/spotbugs), and CI/CD integration patterns for automated security scanning.
version: 2.0.0
author: Trail of Bits (original), OWL (expansion)
license: MIT
metadata:
  hermes:
    tags: [security, sast, static-analysis, semgrep, bandit, code-review, scanning, ci-cd]
    related_skills:
      - trailofbits/audit-context-building
      - security-review
      - security/tool-setup
---

# Static Application Security Testing (SAST)

## Overview

Static analysis examines source code for security vulnerabilities without executing the program. This skill covers language-specific scanners, Semgrep rule writing, and CI/CD integration for automated security scanning in development pipelines.

## When To Use

- Reviewing code for security vulnerabilities (manual or CI/CD)
- Writing custom detection rules for project-specific patterns
- Auditing a codebase before a penetration test
- Setting up automated security scanning in a CI/CD pipeline
- Performing a code review focused on security

## Phase 1: Language-Specific Scanners

### Python — Bandit
```bash
# Install
pip install bandit

# Basic scan
bandit -r ./src/

# With severity filter (only medium and above)
bandit -r ./src/ -ll

# Output formats
bandit -r ./src/ -f json -o bandit_results.json
bandit -r ./src/ -f html -o bandit_results.html
bandit -r ./src/ -f txt -o bandit_results.txt

# Exclude directories
bandit -r ./src/ --exclude ./src/tests,./src/vendor

# Specific tests only
bandit -r ./src/ -t B301,B302,B303    # Specific test IDs

# Skip specific tests
bandit -r ./src/ -s B301,B302

# Confidence levels
# HIGH   — high confidence the issue exists
# MEDIUM — might be a false positive
# LOW    — probably a false positive
bandit -r ./src/ -iii    # Show all including LOW confidence
```

**Common Bandit Test IDs:**
| ID | Test | Severity |
|----|------|----------|
| B301 | pickle deserialization | High |
| B302 | marshal deserialization | High |
| B303 | MD5/SHA1 usage | Medium |
| B304 | insecure cipher | High |
| B305 | insecure cipher mode | High |
| B310 | urllib open to file:// | Medium |
| B311 | random (not secrets) | Medium |
| B312 | telnet usage | High |
| B324 | hashlib with insecure hash | High |
| B404 | subprocess import | Low |
| B501 | requests without cert verification | High |
| B506 | yaml.load (unsafe) | Medium |
| B602 | subprocess with shell=True | High |
| B605 | subprocess with os.system | High |
| B608 | SQL injection (string formatting) | High |
| B609 | wildcard injection | High |

### JavaScript/TypeScript — npm audit + njsscan
```bash
# npm audit (built into npm)
npm audit
npm audit --audit-level=high
npm audit --json > npm_audit.json
npm audit fix                    # Auto-fix where possible
npm audit fix --force            # Force fix (may break things)

# njsscan (more thorough SAST)
pip install njsscan
njsscan ./src/
njsscan ./src/ --json -o njsscan_results.json
njsscan ./scan/ --sarif -o njsscan_results.sarif

# eslint security plugins
npm install --save-dev eslint-plugin-security
npm install --save-dev eslint-plugin-security-node
npm install --save-dev eslint-plugin-no-unsanitized
# Add to .eslintrc:
# "plugins": ["security", "no-unsanitized"]
# "extends": ["plugin:security/recommended"]
```

### Go — gosec
```bash
# Install
go install github.com/securego/gosec/v2/cmd/gosec@latest

# Basic scan
gosec ./...

# With confidence filter
gosec -confidence medium ./...

# Output formats
gosec -fmt json -out gosec_results.json ./...
gosec -fmt sarif -out gosec_results.sarif ./...
gosec -fmt html -out gosec_results.html ./...

# Include tests
gosec -tests ./...

# Exclude rules
gosec -exclude G101,G102 ./...    # Exclude hardcoded credentials, bind to all interfaces
```

### Java — SpotBugs + FindSecBugs
```bash
# SpotBugs with FindSecBugs plugin
# Download from: https://spotbugs.github.io/
# Download FindSecBugs from: https://find-sec-bugs.github.io/

# Run with FindSecBugs
spotbugs -textui -include spotbugs-include.xml \
  -pluginList findsecbugs-plugin.jar \
  -output spotbugs_results.xml \
  target/classes/

# Maven plugin approach
mvn spotbugs:check

# FindSecBugs categories:
# CRYPTO, INJECTION, XSS, SQL_INJECTION, COMMAND_INJECTION,
# PATH_TRAVERSAL, LDAP_INJECTION, XXE, SSRF, HEADER_INJECTION,
# SPRING, SCALA, WEAK_TRNG, WEAK_MESSAGE_DIGEST, JAVAEE,
# HARD_CODE_PASSWORD, HARD_CODE_KEY, DESERIALIZATION,
# JSP, TAPSTRIP, REDOS, LOG_FORGING, JACKSON, BAD_XML,
# SCALA_SENSITIVE_DATA_EXPOSURE, SCALA_PLAY_SSRF
```

### Ruby — Brakeman
```bash
# Install
gem install brakeman

# Basic scan
brakeman -o brakeman_results.html

# Output formats
bracheman -f json -o brakeman_results.json
brakeman -f csv -o brakeman_results.csv
brakeman -f tabs -o brakeman_results.txt

# Skip already confirmed/skipped warnings
brakeman --skip-files config/

# Run against a specific path
brakeman /app --assume-route-all
```

### Semgrep (Multi-Language)
```bash
# Install
pip install semgrep

# Run with built-in rulesets
semgrep --config=auto ./
semgrep --config=p/security-audit ./
semgrep --config=p/secrets ./
semgrep --config=p/python ./
semgrep --config=p/javascript ./
semgrep --config=p/node ./
semgrep --config=p/golang ./
semgrep --config=p/java ./
semgrep --config=p/golang .

# OWASP Top 10 rulesets
semgrep --config=p/owasp-top-ten ./

# Output formats
semgrep --config=auto --json -o semgrep_results.json ./
semgrep --config=auto --sarif -o semgrep_results.sarif ./
semgrep --config=auto --gitlab-sast -o semgrep_gitlab.json ./

# Specific rules
semgrep --config=r/python.lang.security.audit.dangerous-eval ./

# Exclude paths
semgrep --config=auto --exclude=tests --exclude=vendor ./

# Only show new findings (CI mode)
semgrep --config=auto --error ./    # Exit code 1 if findings
```

## Phase 2: Writing Custom Semgrep Rules

### Rule Structure
```yaml
rules:
  - id: my-custom-rule-id
    patterns:
      - pattern: |
          eval(...)
      - pattern-not: |
          ast.literal_eval(...)
    message: |
      Dangerous eval() detected. Use ast.literal_eval() for safe evaluation.
    languages:
      - python
    severity: ERROR
    metadata:
      category: security
      cwe: "CWE-95: Improper Validation of Syntactic Integrity of a Message"
      owasp: "A03:2021 - Injection"
      confidence: HIGH
      likelihood: HIGH
      impact: HIGH
      subcategory:
        - audit
      references:
        - https://cwe.mitre.org/data/definitions/95.html
```

### Pattern Types
```yaml
# Match exact code
pattern: os.system(request.GET['cmd'])

# Match any function call with specific argument
pattern: $FUNC(..., request.$ATTR, ...)

# Match multiple patterns (all must match)
patterns:
  - pattern: $DB.execute(...)
  - pattern: $DB.execute(... + ...)

# Match any of these patterns
pattern-either:
  - pattern: pickle.loads(...)
  - pattern: yaml.load(...)
  - pattern: marshal.loads(...)

# Match inside a context
pattern-inside: |
  def $FUNC(...):
    ...

# Match outside a context (exclude)
pattern-not-inside: |
  def test_$FUNC(...):
    ...

# Match a metavariable that appears elsewhere
pattern: |
  $X = request.$ATTR
  ...
  eval($X)
```

### Testing Rules
```bash
# Test a rule against a specific file
semgrep --config=my_rule.yaml target_file.py

# Test against a directory
semgrep --config=my_rule.yaml ./src/

# Use the Semgrep Playground for interactive testing
# https://semgrep.dev/playground
```

## Phase 3: CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
            p/owasp-top-ten
          generateSarif: true
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: semgrep.sarif

  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r ./src/ -f json -o bandit_results.json -ll
      - name: Upload results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: bandit-results
          path: bandit_results.json

  npm-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm audit --audit-level=high
```

### GitLab CI
```yaml
# .gitlab-ci.yml
semgrep:
  stage: test
  image: returntocorp/semgrep
  script:
    - semgrep --config=auto --json -o semgrep_results.json .
    - semgrep --config=auto --error .
  artifacts:
    reports:
      sast: semgrep_results.json
  allow_failure: true

bandit:
  stage: test
  image: python:3.11
  script:
    - pip install bandit
    - bandit -r ./src/ -f json -o bandit_results.json -ll
  artifacts:
    reports:
      sast: bandit_results.json
  allow_failure: true
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.50.0
    hooks:
      - id: semgrep
        args: ['--config', 'p/security-audit', '--error']

  - repo: https://github.com/PyCQA/bandit
    rev: '1.7.5'
    hooks:
      - id: bandit
        args: ['-ll', '-r', './src/']
```

## Phase 4: Interpreting Results

### Severity Classification
| Severity | Meaning | Action |
|----------|---------|--------|
| ERROR | High confidence vulnerability | Fix immediately |
| WARNING | Likely issue, may need context | Review and fix |
| INFO | Informational finding | Review, may be acceptable |

### False Positive Management
1. **Review each finding** — don't auto-dismiss
2. **Understand the context** — is the data actually user-controlled?
3. **Check for existing mitigations** — is there validation upstream?
4. **Document false positives** — add to a suppression list with justification
5. **Suppress with comments** — use inline suppression for known false positives

```python
# Python: Bandit suppression
eval(user_input)  # nosec B307 — justified: input is sanitized by validate()

# Semgrep suppression
eval(user_input)  # nosec — justified: input is sanitized by validate()
```

## Common Pitfalls

1. **Running scanners without reviewing results.** Automated tools produce false positives. Every finding needs human review.
2. **Only running SAST.** Static analysis misses runtime issues, configuration problems, and business logic flaws. Combine with DAST and manual testing.
3. **Not writing custom rules.** Built-in rules catch common issues. Custom rules catch project-specific patterns.
4. **Ignoring INFO-level findings.** Some of the most interesting vulnerabilities are classified as informational.
5. **Not integrating into CI/CD.** One-time scans are useless. Automated scanning on every commit catches issues early.
6. **Not updating rules.** Security rules evolve. Keep Semgrep, Bandit, and other tools updated.

## Verification Checklist

- [ ] Language-appropriate scanner run (Bandit for Python, gosec for Go, etc.)
- [ ] Semgrep run with security-audit and secrets rulesets
- [ ] npm audit / pip audit run for dependency vulnerabilities
- [ ] All findings reviewed (not just automated output)
- [ ] False positives documented and suppressed with justification
- [ ] Custom rules written for project-specific patterns
- [ ] CI/CD integration configured
- [ ] Results documented in findings tracker
