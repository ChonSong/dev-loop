# HWC Subagent Verification Patterns (May 2026)

## The Core Insight

**Subagent timeout ≠ work lost.** A subagent that times out may have successfully committed its work. Always check `git log --oneline -10` before assuming work is lost and re-delegating.

**BUT**: File existence ≠ work done. A subagent reporting "wrote file X" may have written it to a different path than expected. Always `git status --short` to verify.

## Pattern 1: Code Subagent (600s timeout)

Code subagents (Svelte, Go, TypeScript) almost always complete despite timeout warnings. The timeout fires at 600s but the work finishes around 580-590s. Check:

```bash
# After ANY code subagent timeout:
cd /path/to/project && git log --oneline -10 && git status --short
```

If commits appear in log but not in your expected sequence, the subagent likely committed out-of-order or with a non-standard message. Check `git diff --stat HEAD` to see actual changes.

**Example from this session (HWC Phase 3):**
- Subagent timed out after 600s with summary "completed, 48 API calls"
- `git log --oneline -10` showed `c6cacb9 feat(phase3): Docker containers CRUD...` — work was done and committed
- No re-delegation needed

**Example from HWC Phase 5:**
- Subagent timed out after 600s 
- `git log --oneline -10` showed `01c1fec feat(phase5): Xpra integration...` — work done
- No re-delegation needed

## Pattern 2: The Uncommitted Working Tree

`git diff --stat HEAD` shows files modified but `git diff` shows nothing. This means the blob hash differs from HEAD but content is identical (timestamp or permission change). Check:

```bash
git ls-files -s path/to/file   # staged/HEAD blob hash
git ls-files -s --stage path/to/file  # current index blob
```

If hashes match, there is NO actual change — `git add -A && git commit` will be a no-op for that file.

**This is NOT a problem.** It means the subagent's changes produced the same result as what was already committed (likely a trivial formatting or ordering difference that the Go formatter normalized).

## Pattern 3: Documentation Subagent — Different Failure Mode

Documentation subagents complete in <60s and report success. But the files may NOT exist at the expected path. The subagent's working directory is different from the controller's.

**Always verify with `git status --short` after documentation subagents.**

If the file doesn't appear, create it directly in the controller session via `write_file`. Do NOT re-delegate.

## Pattern 4: Subagent Working Directory Confusion

The HWC path differs between container and host:

| Environment | Path |
|-------------|------|
| Container (this runtime) | `/home/hermeswebui/.hermes/hermes-web-computer` |
| Host (sean@172.19.0.1) | `/home/sean/.hermes/hermes-web-computer` |

Subagents running code on the host may use absolute paths from the goal string. If the goal says `/home/hermeswebui/.hermes/hermes-web-computer` and the subagent runs on the host, the path doesn't exist and the subagent silently fails or writes to a different location.

**Prevention**: When delegating to subagents that will run on the host, always include the correct host path in the goal string AND verify the subagent used it.

## Pattern 5: Build Verification After Subagent

Subagents should NOT run build verification (it times them out). After code subagent completion:
1. Verify with `git status --short` 
2. SSH to host: `ssh -i container_key sean@172.19.0.1 'cd /home/sean/.hermes/hermes-web-computer && go build ./... && cd frontend && npm run build'`
3. Commit if build passes

## Pattern 6: Screenshot Capture via Playwright

When `grim`/`import` fail with "failed to create display" on the host (no X11), use Playwright:

```bash
# One-time install on host
cd /home/sean/.hermes/hermes-web-computer && npx playwright install chromium

# Screenshot
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://localhost:3005', { waitUntil: 'networkidle', timeout: 15000 });
  await page.screenshot({ path: '/tmp/hwc-screenshot.png', fullPage: false });
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
"

# Transfer to container
scp -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1:/tmp/hwc-screenshot.png /workspace/
```

## HWC Session State (2026-05-25)

### Paths
- Container: `/home/hermeswebui/.hermes/hermes-web-computer`
- Host: `/home/sean/.hermes/hermes-web-computer`

### Running Processes
- HWC Go server: PID 682891, port 3005, working dir `/opt/data/hermes-web-computer/backend`
- agent-os: PID 626151, port 3113
- Frontend dev: served from Go backend (embedded dist), not separate Vite

### Key SSH Commands
```bash
# SSH to host
ssh -i /home/hermeswebui/.hermes/container_key -o StrictHostKeyChecking=no sean@172.19.0.1

# Build Go backend on host
cd /home/sean/.hermes/hermes-web-computer/backend && go build -o server ./cmd/server/

# Build frontend on host
cd /home/sean/.hermes/hermes-web-computer/frontend && npm run build

# Restart HWC server
kill 682891; cd /opt/data/hermes-web-computer/backend && nohup ./server > /tmp/hwc.log 2>&1 &
```

### Port Mappings
- `:3005` — HWC Go backend (the one to use)
- `:3113` — agent-os (legacy, being replaced)
- `:3001` — agent-os alternate port

### Go Toolchain
On the host: `/home/sean/.hermes/hermes-web-computer/backend` has `go.mod` at `module hermes-web-computer/backend`. Build with `cd /home/sean/.hermes/hermes-web-computer/backend && go build ./...`