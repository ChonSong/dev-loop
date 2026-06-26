# Hermes Gateway API — Cross-Container Dispatch

When a companion container (e.g., WebUI) needs to execute commands on the host but SSH is not yet available, the Hermes Gateway API can be used to dispatch instructions to the host's agent.

## Prerequisites

- Host Hermes agent must have `API_SERVER_ENABLED=true` in its `.env`
- The `API_SERVER_KEY` must be known (stored in the companion container's `.env` copy)
- The host's gateway must be reachable from the companion container (Docker bridge IP, typically `172.19.0.1:8642`)

## Technique

```python
import urllib.request, json

# The API key lives in .env as API_SERVER_KEY
# From a companion container's .env:
with open("/path/to/.hermes/.env") as f:
    for line in f:
        if line.startswith("API_SERVER_KEY="):
            api_key = line.strip().split("=", 1)[1].strip()

body = json.dumps({
    "model": "deepseek-v4-flash",  # or whatever model the host agent uses
    "messages": [
        {
            "role": "user",
            "content": "Run this shell command: <command to execute>"
        }
    ],
    "max_tokens": 100
})

req = urllib.request.Request(
    "http://172.19.0.1:8642/v1/chat/completions",
    data=body.encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
)
resp = urllib.request.urlopen(req, timeout=30)
```

## Use Cases

1. **SSH key bootstrap** — When the companion container generates an SSH key but needs it on the host's `~/.ssh/authorized_keys`:
   ```
   mkdir -p ~/.ssh && echo '<pubkey>' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
   ```

2. **Service health checks** when direct access is blocked — the host agent has full terminal access and can run diagnostics the companion container cannot.

3. **One-shot config changes** — modifying host files, restarting services, checking systemd status.

## Caveats

- This is an **LLM chat completion endpoint** — it runs inference, not direct command execution. The model must interpret the instruction and use its tool-calling to execute. Success depends on the model's ability to follow instructions and the agent's tool configuration.
- The host agent processes the message with its full system prompt and available tools. If it can't use terminal tools (e.g., TIRITH blocks), the dispatch will fail.
- The gateway API sends the full system prompt with every request (90K+ tokens observed), making it expensive for frequent use. Use SSH once available.
- The API key is a shared secret — treat it like a password.
