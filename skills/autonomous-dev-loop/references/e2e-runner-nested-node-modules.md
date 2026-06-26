# E2E Runner — Nested node_modules Version Conflict

## Symptom

```
Error: Requiring @playwright/test second time,
First:
Error:
   at ../playwright.config.ts:1
> 1 | import { defineConfig, devices } from '@playwright/test';
```

`npx playwright test --list` fails with this error. `npx playwright test` also fails.

## Root cause

A monorepo (npm/yarn workspaces) has `@playwright/test` at TWO different node_modules locations:

1. **Root `node_modules/@playwright/test`** — installed as a transitive dependency of another package (e.g., `next@^15` bundles `@playwright/test@1.61.0`)
2. **Subdirectory `node_modules/@playwright/test`** — independently installed via the subdirectory's own `package.json`

When you run `npx playwright test` from the subdirectory context, Node loads `@playwright/test` from the FIRST resolved path, sets a process-global singleton flag (`process["__pw_initiator__"]`), then hits the SECOND path during test file resolution and the singleton guard throws.

## Diagnosis

```bash
# 1. List ALL node_modules directories (max depth 3)
find . -name "node_modules" -maxdepth 3 -type d | while read d; do
    echo "=== $d ==="
    [ -d "$d/@playwright" ] && echo "  HAS @playwright" || echo "  no @playwright"
done

# 2. Check if root has @playwright/test (likely from next.js)
ls root_node_modules/@playwright/test/package.json 2>/dev/null && cat $_ | grep '"version"'

# 3. Check if e2e has its own @playwright/test
ls apps/web/e2e/node_modules/@playwright/test/package.json 2>/dev/null

# 4. Check for stale .bak directories
find . -name "node_modules.bak*" -maxdepth 3 -type d
```

## Fix

```bash
# 1. Remove all duplicate node_modules under e2e/
rm -rf apps/web/e2e/node_modules
rm -rf apps/web/e2e/node_modules.bak
rm -rf apps/web/e2e/node_modules.bak2

# 2. Remove @playwright/test from e2e/package.json devDependencies
#    (the root already has it via next.js transitive dep)

# 3. Rewrite the test runner script to use npx (resolves from root)
#    Instead of: e2e/node_modules/.bin/playwright test --config=...
#    Use:        npx playwright test --config=e2e/playwright.config.ts

# 4. Verify
npx playwright test --list     # should list all tests without error
npx playwright test --list | wc -l   # count them
```

## Verification

```bash
npx playwright test --list 2>&1 | head -5
# Should show: "Listing tests:" followed by test names
# Should NOT show: "Requiring @playwright/test second time"
```

## Applied example

Applied to `/home/sc/repos/gto-wizard-clone` on 2026-06-25. Root cause: `next@15.5.19` hoisted `@playwright/test@1.61.0` to root, while `apps/web/e2e/package.json` independently declared `"@playwright/test": "^1.40.0"` and had its own `node_modules` from a prior `npm install` in that directory. Removed 3 directories (`node_modules`, `node_modules.bak`, `node_modules.bak2`), stripped `@playwright/test` from `e2e/package.json`, updated `playwright-test.sh` to use `npx playwright`.
