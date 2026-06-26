# Deploy Workaround — Manual Build When Pushing From Local

## Problem
The deploy script (`deploy.sh`) used by the systemd timer does:
```bash
CURRENT_HASH=$(git rev-parse HEAD)
git fetch origin main
REMOTE_HASH=$(git rev-parse origin/main)
if [ "$CURRENT_HASH" = "$REMOTE_HASH" ]; then
    echo "Already up to date at $CURRENT_HASH."
    exit 0  # <-- SKIPS BUILD ENTIRELY
fi
```

When the Player pushes from the local repo, both hashes already match. The script exits before building. The live site stays on the old build.

## Solution
After pushing from local, manually trigger a build + restart:

```bash
cd /home/sc/repos/<project>
npx turbo build --force
systemctl --user restart <project>-web.service
```

## For GTO Wizard specifically:
```bash
cd /home/sc/repos/gto-wizard-clone
npx turbo build --force
systemctl --user restart gto-wizard-web.service
```
