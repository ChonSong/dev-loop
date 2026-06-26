# Docker Gateway Access from WebUI Container

When the Hermes WebUI is running in Docker (user `hermeswebui`, container `8b2c33b1562f`), the host is at the Docker bridge gateway IP `172.19.0.1`.

## Detecting the Gateway

```bash
ip route | grep default | awk '{print $3}'  # e.g. 172.19.0.1
```

## Host Services

| Service | Host Port | Container Access | Notes |
|---|---|---|---|
| GTO Wizard | 3000 | http://172.19.0.1:3000 | Health: `/api/v1/health` |
| Hermes gateway | 8642 | http://172.19.0.1:8642 | Use `API_SERVER_KEY` from `.env` for auth |
| WebUI (self) | 8787 | http://172.19.0.1:8787 | Loops back to this container |
| Benchmark | 8000 | http://172.19.0.1:8000 | |
| Energy router | 8009 | http://172.19.0.1:8009 | When deployed |

## SSH from Container to Host

Generate a key in the container and install on the host:

```bash
# In container
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "hermes-webui@container"
cat ~/.ssh/id_ed25519.pub
# Copy the public key

# On host (run from host or via Hermes gateway API)
echo "<public-key>" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test from container
ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 sc@172.19.0.1 "hostname"
```

## Via Hermes Gateway API

The host's Hermes gateway at `172.19.0.1:8642` accepts OpenAI-compatible requests with the API key from `.env` (`API_SERVER_KEY`). This can be used to dispatch messages to the host's Hermes agent for command execution:

```python
import urllib.request, json

with open("/home/hermeswebui/.hermes/.env") as f:
    for line in f:
        if line.startswith("API_SERVER_KEY="):
            api_key = line.strip().split("=", 1)[1].strip()

body = json.dumps({
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "your command here"}],
    "max_tokens": 100
}).encode()

req = urllib.request.Request(
    "http://172.19.0.1:8642/v1/chat/completions",
    data=body,
    headers={"Content-Type": "application/json",
             "Authorization": f"Bearer {api_key}"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=30)
```
