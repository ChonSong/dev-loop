# Google Drive rclone OAuth Reference

## OAuth Credentials (Sean's account)

| Field | Value |
|-------|-------|
| Client ID | `596071327960-9be70fpnvvq8mlr5349epc1ur2r17hhn.apps.googleusercontent.com` |
| Client Secret | `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` |
| Account | `seanos1a@gmail.com` |
| Scope | `drive` (full read/write) |

> ⚠️ There were two different client secrets in old configs: `GOCSPX-IvbZ` (wrong) and `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` (correct). Always use the Xwwk version.

## Embedding rclone Config into secrets.age

The rclone config is stored as `RCLONE_CONFIG_BASE64` inside the Fernet-encrypted `secrets.age`. This enables seamless migration — any new machine running `setup.sh` automatically gets Drive access without manual OAuth.

**Encryption (run after any token refresh):**

```python
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PASSHRASE = "dawnofdoyle"
SALT = b"hermes-sync-salt-v1"

# Read current rclone config
with open('/opt/data/rclone_config/rclone.conf') as f:
    rclone_conf = f.read()

# Decrypt existing secrets.age
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=480000)
key = base64.urlsafe_b64encode(kdf.derive(PASSHRASE.encode()))
with open('/opt/data/hermes-sync/secrets.age', 'rb') as f:
    encrypted = f.read()
f2 = Fernet(key)
decrypted = f2.decrypt(encrypted).decode()

# Append rclone config as base64 env var
new_line = f"RCLONE_CONFIG_BASE64={base64.b64encode(rclone_conf.encode()).decode()}"
new_env = decrypted.rstrip() + "\n" + new_line + "\n"

# Re-encrypt
re_encrypted = Fernet(key).encrypt(new_env.encode())
with open('/opt/data/hermes-sync/secrets.age', 'wb') as f:
    f.write(re_encrypted)
print("Updated secrets.age with rclone config")
```

**Decryption (in setup.sh):**

```bash
python3 - <<'PYEOF'
import base64, os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

passphrase = os.environ.get('PASSPHRASE', 'dawnofdoyle')
salt = b'hermes-sync-salt-v1'
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

with open('secrets.age', 'rb') as f:
    token = f.read()
f2 = Fernet(key)
decrypted = f2.decrypt(token)

# Write .env
with open('.env', 'wb') as out:
    out.write(decrypted)

# Restore rclone config if present
for line in decrypted.decode().splitlines():
    if line.startswith('RCLONE_CONFIG_BASE64='):
        b64 = line.split('=', 1)[1].strip()
        rclone_conf = base64.b64decode(b64).decode()
        os.makedirs('.hermes/rclone_config', exist_ok=True)
        with open('.hermes/rclone_config/rclone.conf', 'w') as f:
            f.write(rclone_conf)
        print("Rclone config restored.")
        break
print("Secrets restored.")
PYEOF
```

## Token Behavior

- Access tokens expire in 1 hour; refresh tokens last ~7 days
- rclone auto-refreshes on each invocation — no manual re-auth needed
- If `rclone ls` fails with 401, the refresh token may have expired — regenerate via OAuth flow above
- The refresh token itself is stored inside the `token = {...}` JSON in rclone.conf — it does NOT expire like the access token

## Alternative: google-drive-ocamlfuse (Ubuntu desktop)

See `references/google-drive-ocamlfuse.md`. Use `setup-google-drive.sh` on Ubuntu machines with FUSE kernel support.
