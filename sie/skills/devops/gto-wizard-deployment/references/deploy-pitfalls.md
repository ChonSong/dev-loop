# GTO Wizard Deploy Script Pitfalls

## Deploy Script Skips Rebuild on Local Pushes

**Symptom:** You push code to GitHub from the local machine, the deploy timer fires, logs show "Already up to date" but the live site doesn't change.

**Cause:** `deploy.sh` does `git fetch origin main` then compares `git rev-parse HEAD` (local) vs `git rev-parse origin/main` (remote). If you pushed from the same machine, local HEAD already equals remote, so the script exits before building.

**Fix:** After pushing from local, manually trigger a rebuild:
```bash
cd /home/sc/repos/gto-wizard-clone
npx turbo build --force
systemctl --user restart gto-wizard-web.service
```

**Prevention:** The deploy script should always build when the working tree has uncommitted changes or when explicitly triggered. Consider adding a `--force` flag to the deploy script.

## Service Restart Timing

After restarting `gto-wizard-web.service`, wait 3-5 seconds before testing. Next.js needs time to start up. The service uses `Restart=always` with `RestartSec=5`, so it will auto-restart if the build produced a broken bundle.

## Build Cache Issues

If the build seems to use stale output:
```bash
cd /home/sc/repos/gto-wizard-clone
rm -rf apps/web/.next apps/web/.turbo
npx turbo build --force
systemctl --user restart gto-wizard-web.service
```
