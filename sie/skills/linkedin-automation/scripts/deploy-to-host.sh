#!/bin/bash
# Deploy LinkedIn automation scripts from container to host
# Run from inside the container

set -e

SCRIPTS=(
  "linkedin-login.py"
  "linkedin-browser.py"
  "linkedin-queue-post.sh"
  "linkedin-post-runner.py"
)

echo "Copying LinkedIn automation scripts to host..."
for script in "${SCRIPTS[@]}"; do
  if [ -f "/workspace/${script}" ]; then
    scp -i /home/hermeswebui/.hermes/container_key \
        -o StrictHostKeyChecking=no \
        "/workspace/${script}" \
        sean@172.19.0.1:/tmp/
    echo "  [OK] ${script} -> /tmp/"
  else
    echo "  [SKIP] ${script} not found in /workspace/"
  fi
done

echo "Done. Scripts are in /tmp/ on the host."
echo "Install Playwright on host if not already:"
echo "  pip3 install playwright --break-system-packages"
echo "  python3 -m playwright install chromium"
