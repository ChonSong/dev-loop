---
name: tandem-browser-start
description: "Start Tandem Browser with shared session for Hermes AI viewer integration. Enables seamless connection between Tandem Electron app and Hermes viewer via CDP (Chrome DevTools Protocol)."
category: devops
tags:
  - tandem
  - browser
  - cdp
  - viewer
---

## Purpose
Start Tandem Browser with shared session for Hermes AI viewer integration. This skill enables seamless connection between Tandem Electron app and Hermes viewer via CDP (Chrome DevTools Protocol).

## Reference Files
- How to start Tandem Browser: references/how-to-start-tandem.md
- Tandem Browser troubleshooting: references/tandem-troubleshooting.md

## When to Use
- When needing to view or interact with Tandem Electron app pages through Hermes viewer
- When Tandem needs to be running for SEEK Quick Apply roles or other browser-based workflows
- When initial setup is required after system restart or session reset

## Prerequisites
- Node.js 18+ installed (system or virtualenv)
- Python 3.8+ for script execution
- Tandem repository cloned at `/home/sc/repos/tandem-browser`
- Required npm dependencies installed (`npm install` in tandem-browser directory)

## Steps to Execute
1. Navigate to Tandem Browser directory:
   ```bash
   cd /home/sc/repos/tandem-browser
   ```

2. Run the start script:
   ```bash
   bash /home/sc/.hermes/scripts/start-tandem.sh
   ```

3. Wait for confirmation:
   ```
   Tandem starting with remote debugging on port 9222...
   CDP ready after 4s
   Electron viewer starting at http://localhost:3099
   ```

4. Open the viewer in your browser:
   ```
   http://localhost:3099
   ```

## Common Issues & Solutions
- **Port conflict**: If port 9222 or 3099 is already in use, kill existing processes first:
  ```bash
  lsof -ti :9222 | xargs -r kill 2>/dev/null || true
  lsof -ti :3099 | xargs -r kill 2>/dev/null || true
  ```
- **Node not found**: Ensure Node.js is installed and in PATH:
  ```bash
  which node || echo "Node.js not found in PATH"
  ```
- **Script not executable**: Make sure the script has execute permissions:
  ```bash
  chmod +x /home/sc/.hermes/scripts/start-tandem.sh
  ```

## Notes
- Tandem runs as a background process (PID will be shown in logs)
- The viewer automatically refreshes every 2 seconds to show updated page content
- The script kills any existing Tandem processes on ports 9222 and 3099 before starting new ones
- CDP (Chrome DevTools Protocol) is used for communication between Tandem and viewer
- Viewer shows live page content from Tandem Electron app without navigating away