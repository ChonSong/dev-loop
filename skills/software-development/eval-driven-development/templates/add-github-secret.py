#!/usr/bin/env python3
"""Add a secret to a GitHub repo via REST API with libsodium sealed-box encryption.

Usage:
    python3 add-github-secret.py <owner/repo> <SECRET_NAME> <secret_value>

Requires:
    - GITHUB_PAT environment variable or in ~/.hermes/.env
    - pynacl (pip install pynacl)
"""

import os, sys, json, base64, urllib.request
from nacl.public import PublicKey, SealedBox


def get_pat():
    for var in ["GITHUB_PAT", "GH_TOKEN", "GITHUB_TOKEN"]:
        val = os.environ.get(var)
        if val and len(val) > 20:
            return val
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_PAT="):
                    val = line.split("=", 1)[1]
                    if val and len(val) > 20:
                        return val
    return None


def add_secret(pat, repo, secret_name, secret_value):
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github.v3+json",
    }
    # Get public key
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req)
    key_data = json.loads(resp.read())
    key_id = key_data["key_id"]
    pub = PublicKey(base64.b64decode(key_data["key"]))
    sealed = SealedBox(pub)
    encrypted = base64.b64encode(sealed.encrypt(secret_value.encode())).decode()
    # PUT the secret
    payload = json.dumps({"encrypted_value": encrypted, "key_id": key_id}).encode()
    url = f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}"
    req = urllib.request.Request(
        url, data=payload, headers={**headers, "Content-Type": "application/json"}, method="PUT"
    )
    resp = urllib.request.urlopen(req)
    return resp.status


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <owner/repo> <SECRET_NAME> <secret_value>")
        sys.exit(1)
    pat = get_pat()
    if not pat:
        print("ERROR: GitHub PAT not found")
        sys.exit(1)
    repo, name, value = sys.argv[1], sys.argv[2], sys.argv[3]
    status = add_secret(pat, repo, name, value)
    print(f"✅ {name}: HTTP {status}")
