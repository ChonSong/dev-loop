#!/bin/bash
set -e

HERMES_SYNC_DIR="${HOME}/hermes-sync"
HERMES_DIR="${HOME}/.hermes"
WORKSPACE_DIR="${HOME}/workspace"
PASSPHRASE="${PASSPHRASE:-dawnofdoyle}"

echo "==> Hermes sync bootstrap"

# Detect package manager
if command -v apt-get &>/dev/null; then PKG_MGR="apt-get"
elif command -v dnf &>/dev/null; then PKG_MGR="dnf"
elif command -v pacman &>/dev/null; then PKG_MGR="pacman"
else echo "Unsupported distro"; exit 1; fi

echo "==> Installing dependencies..."
case "$PKG_MGR" in
    apt-get) sudo apt-get update && sudo apt-get install -y docker.io docker-compose git python3-cryptography curl ;;
    dnf)     sudo dnf install -y docker docker-compose git python3-cryptography curl ;;
    pacman)  sudo pacman -Syu --noconfirm docker docker-compose git python3-cryptography curl ;;
esac

# Clone / update hermes-sync
if [[ -d "$HERMES_SYNC_DIR/.git" ]]; then
    echo "==> Updating hermes-sync..."
    git -C "$HERMES_SYNC_DIR" pull
else
    echo "==> Cloning hermes-sync..."
    git clone https://github.com/ChonSong/hermes-sync.git "$HERMES_SYNC_DIR"
fi

# Clone / update hermes-agent (required for docker build)
HERMES_AGENT_DIR="$(dirname "$HERMES_SYNC_DIR")/hermes-agent"
if [[ -d "$HERMES_AGENT_DIR/.git" ]]; then
    echo "==> Updating hermes-agent..."
    git -C "$HERMES_AGENT_DIR" pull
else
    echo "==> Cloning hermes-agent..."
    git clone https://github.com/NousResearch/hermes-agent.git "$HERMES_AGENT_DIR"
fi

# Clone / update hermes-webui
HERMES_WEBUI_DIR="$(dirname "$HERMES_SYNC_DIR")/hermes-webui"
if [[ -d "$HERMES_WEBUI_DIR/.git" ]]; then
    echo "==> Updating hermes-webui..."
    git -C "$HERMES_WEBUI_DIR" pull
else
    echo "==> Cloning hermes-webui..."
    git clone https://github.com/ChonSong/hermes-webui.git "$HERMES_WEBUI_DIR"
fi

# Init git in hermes dir (for backup cron job)
if [[ ! -d "$HERMES_DIR/.git" ]]; then
    echo "==> Initializing $HERMES_DIR as git repo..."
    mkdir -p "$HERMES_DIR"
    git init
    git remote add origin https://github.com/ChonSong/hermes-sync.git
fi

# Configure git credential helper so pulls/pushes work non-interactively
if [[ -f "${HERMES_SYNC_DIR}/netrc" ]]; then
    echo "==> Configuring git credentials..."
    cp "${HERMES_SYNC_DIR}/netrc" "${HOME}/.netrc"
    chmod 600 "${HOME}/.netrc"
    git config --global credential.helper "store"
fi

# Restore secrets (if secrets.age exists in the sync repo)
if [[ -f "${HERMES_SYNC_DIR}/secrets.age" ]]; then
    echo "==> Restoring secrets..."
    mkdir -p "$HERMES_DIR"
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
with open('.env', 'wb') as out:
    out.write(decrypted)
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
fi

# Sync files
echo "==> Syncing files..."
mkdir -p "${HERMES_DIR}/skills" "${WORKSPACE_DIR}"
rsync -av --delete "${HERMES_SYNC_DIR}/config/"   "${HERMES_DIR}/"
rsync -av --delete "${HERMES_SYNC_DIR}/skills/"   "${HERMES_DIR}/skills/"
rsync -av "${HERMES_SYNC_DIR}/memory/"            "${HERMES_DIR}/memories/"
rsync -av "${HERMES_SYNC_DIR}/SOUL.md"            "${HERMES_DIR}/"
rsync -av --delete "${HERMES_SYNC_DIR}/workspace/" "${WORKSPACE_DIR}/"

# Build & start gateway + dashboard (from hermes-sync docker compose)
echo "==> Building & starting Hermes gateway + dashboard..."
export HERMES_AGENT_DIR
docker compose -f "${HERMES_SYNC_DIR}/docker/docker-compose.yml" up -d --build

# Build & start hermes-webui (separate compose)
echo "==> Building & starting hermes-webui..."
docker compose -f "${HERMES_WEBUI_DIR}/docker-compose.yml" up -d --build

# Wait for gateway to be healthy (max 120s)
echo "==> Waiting for gateway to be healthy..."
max_wait=120
elapsed=0
interval=5
while true; do
    status=$(docker inspect --format='{{.State.Health.Status}}' hermes 2>/dev/null || echo "none")
    if [[ "$status" == "healthy" ]]; then
        echo "Gateway is healthy!"
        break
    fi
    sleep $interval
    elapsed=$((elapsed + interval))
    if [[ $elapsed -ge $max_wait ]]; then
        echo "Warning: gateway health check timed out after ${max_wait}s (status: $status)"
        echo "Container may still be starting. Check with: docker inspect --format='{{.State}}' hermes"
        break
    fi
    echo "  Waiting... ${elapsed}s (status: $status)"
done

echo ""
echo "Done!"
echo "  WebUI:  http://localhost:8787"
echo "  TUI:    docker exec hermes /opt/hermes/.venv/bin/hermes --tui"
echo "  Logs:   docker logs hermes -f"
