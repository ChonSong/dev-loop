# Cron Error Catalog

Quick lookup for common Hermes cron error signatures.

## 401 — Missing Authentication Header

```
error: RuntimeError: Error code: 401 - {'error': {'message': 'Missing Authentication header', 'code': 401}}
```

**Pattern:** All agent-based jobs fail identically; no-agent/script-only jobs succeed.

**Root cause:** The LLM provider API key is missing, expired, or revoked.

**Diagnosis:**

1. Check which provider is configured:
   ```bash
   hermes config show           # look for provider: line (e.g., opencode-go, openrouter)
   ```
2. Identify the expected env var for that provider:
   - `opencode-go` → `OPENCODE_GO_API_KEY`
   - `openrouter` → `OPENROUTER_API_KEY`
   - `anthropic` → `ANTHROPIC_API_KEY`
   - `openai` → `OPENAI_API_KEY`
   - `gemini` → `GEMINI_API_KEY`
3. Verify the var is set and non-empty:
   ```bash
   grep -i "${PROVIDER}_API_KEY" /home/hermeswebui/.hermes/.env
   ```

**Fix:** Replace with a valid key in `.env` (at `/home/hermeswebui/.hermes/.env`), then restart the gateway:
```bash
hermes gateway run &
```

**Do NOT:** Edit individual job prompts — this is a single config fix that heals all jobs at once.

---

## 400 — Non-Retryable Client Error (Model Routing)

```
error: RuntimeError: Error code: 400 - {'error': {'message': 'non_retryable_client_error', 'code': 400}}
```

**Pattern:** One or a few jobs fail; others with different models succeed.

**Root cause:** The model name is wrong for the provider, or the provider can't serve that model right now.

**Fix:** Switch to a different model in the job config. Common swap: `owl-alpha` ↔ `anthropic/claude-sonnet-4`.

---

## Delivery Failure — No Target Resolved

```
⚠ Delivery failed: no delivery target resolved for deliver=origin
```

**Pattern:** Job runs successfully (`ok`) but the output doesn't arrive.

**Root cause:** `deliver=origin` — cron jobs have no originating conversation to deliver to.

**Fix:** Change `deliver` to `local`.

---

## Broken Pipe — Prompt Executes Against Missing Files/Paths

```
error: RuntimeError: [Errno 32] Broken pipe
```

**Pattern:** Job fails with Broken pipe, no other error context.

**Root cause:** The cron job's prompt instructs the agent to read files, list directories, or execute scripts at paths that don't exist. The file/terminal tool opens a pipe to the target, the target doesn't exist, and the pipe breaks.

**Common triggers:**
- Prompt references `/home/hermeswebui/.hermes/memories/` (doesn't exist — session data is in `state.db`)
- Prompt references `/opt/data/` paths after migration to `/home/hermeswebui/.hermes/`
- Prompt tries to run a script that was moved or deleted

**Diagnosis:**
1. Read the job's full prompt from `/home/hermeswebui/.hermes/cron/jobs.json`
2. Identify all file paths mentioned in the prompt
3. Verify each path exists in the container filesystem

**Fix:** Update the prompt to reference only paths that exist. Common corrections:
- Wrong: `/home/hermeswebui/.hermes/memories/` → use `session_search` tool instead
- Wrong: `/opt/data/` container paths → use `/home/hermeswebui/.hermes/` or `/workspace/`
- Wrong: old project paths from workspace reorg → check current paths first

**Do NOT:** Restart the gateway or change the provider — this is a prompt/content issue, not an infrastructure issue.

---

## Broken Pipe — LLM Provider Connection Drop

```
error: RuntimeError: [Errno 32] Broken pipe
```

**Pattern:** Job fails with Broken pipe. Prompt references no file paths (or all paths exist). Other jobs succeeded recently.

**Root cause:** Transient LLM provider connection drop. The agent session was mid-response when the provider stream cut out. This is NOT a script or path issue — it's a network/connection blip between the gateway and the model provider.

**How to distinguish from file-path Broken pipe:**
- **File-path version:** Job consistently fails. Other file-reading jobs also fail. Prompt references paths that may not exist.
- **Connection-drop version:** Job fails intermittently (runs ok, then fails, then ok again). Other jobs succeed at the same time. No path issues in the prompt.

**Diagnosis:**
1. Check the job's recent history — do successful runs exist between failures? If yes → connection drop.
2. Check sibling jobs — did other agent-driven jobs around the same time also fail? Cluster = provider issue.
3. Count consecutive failures from output files — 1-2 intermittent failures is noise; 5+ consecutive is a real problem.

**Fix:** No action needed for a single occurrence. The job auto-recovers on its next scheduled tick.

**When to escalate:**
- 5+ consecutive failures with zero successes between them
- ALL agent-based jobs fail identically (cluster of Broken pipe across jobs)
- Error persists for more than 24 hours

**Do NOT:**
- Restart the gateway — this doesn't fix a provider-side connection drop
- Edit the job prompt — the content is fine
- Change the provider — one intermittent failure is normal

**Known affected jobs (as of June 2026):**
- `GTO Wizard QA Sweep` — ~1 failure every 2-3 days
- `Daily QA Audit — wiz.codeovertcp.com` — ~1 failure/week
- `Hermes Full Backup — Docker Image` — ~1 failure/2 weeks

All self-recover on next tick without intervention.

---


## Script Exit Code 255 (SSH Failure)

```
error: Script exited with code 255
stdout:
[timestamp] <job name> (via SSH to host)
Permission denied, please try again.
Permission denied, please try again.
user@host: Permission denied (publickey,password).
Host QA script exited with code 255
```

**Pattern:** Jobs that SSH into the host from the container fail.

**Root cause:** SSH key mismatch, missing key, or wrong user. The container's SSH key (`~/.ssh/id_ed25519`) may not be authorized on the host, or the `known_hosts` entry is stale.

**Fix:** Verify `ssh -i ~/.ssh/id_ed25519 user@host` works from the container. Re-run `ssh-copy-id` or update `known_hosts`.

---

## HTTP 530 / Cloudflare Error 1033 — Argo Tunnel Origin Unreachable

```
**GTO Wizard — All Checks Failed**
| Main page               | ❌ HTTP 530 | Response time: 0.058s |
| API health              | ❌ HTTP 530 | Response time: 0.360s |
| Page title              | ❌ Not found | No `<title>` tag in response |
```

**Pattern:** All curl-based checks to a Cloudflare-tunneled service return HTTP 530. Response time is fast (~50ms) — Cloudflare edge is responding, but the tunnel has no origin to connect to.

**Root cause:** Cloudflare error 1033 means `cloudflared` (the Argo Tunnel daemon) on the origin server cannot reach the upstream application. The app or the tunnel daemon has stopped on the host.

**Diagnosis:**

1. Check if `cloudflared` is running on the host:
   ```bash
   ssh user@host "systemctl status cloudflared 2>/dev/null"
   ```
2. Check if the application service is running:
   ```bash
   ssh user@host "systemctl status <app-service> 2>/dev/null"
   ```
3. If you can't SSH (blocked, no key), the 530 + 1033 combo is diagnostic enough — it's a tunnel/origin issue, not a DNS or routing problem.

**Fix:** Restart both services on the host:
```bash
systemctl restart <app-service> cloudflared
```

**Do NOT:** Change DNS settings, retry from container, or restart the gateway. The issue is on the host side where `cloudflared` runs.

---

---

## Tirith + Cron Mode — All Commands Blocked (Silent Failure)

```
Every terminal command blocked — even `echo test`, `pwd`, `id`.
All fail with: status: pending_approval, pattern_key: tirith:unknown
last_status may still show "ok" because the agent didn't crash — it just got nothing done.
```

**Pattern:** Every terminal command — even trivial ones (`echo test`, `pwd`, `id`) — is rejected with `status: pending_approval` and `pattern_key: tirith:unknown`. The agent cannot run curl, SSH, git, or any shell command. The job's `last_status` may show `ok` because the agent completed without crashing — but functionally it did nothing.

**Critical: `last_status: "ok"` is misleading.** The cron engine sets `ok` when the agent finishes without crashing. A job that does nothing because every command was blocked still returns `ok`. Always verify by checking output content, not just status.

**Root cause:** `approvals.cron_mode: deny` in `config.yaml`. When Tirith (security scanner) flags a command as `unknown`, it demands manual approval. In cron mode there is no user present to approve, so every command sits at `pending_approval` indefinitely. The agent finishes its loop having accomplished nothing, and returns `last_status: ok` because no crash occurred.

This is NOT a Tirith scanner misconfiguration — Tirith is working as designed. The issue is that cron-mode jobs have no way to approve flagged commands.

**Distinguishing from other failures:**
- Trivial commands (`echo test`) fail — rules out per-command issues
- All terminal-reliant cron jobs fail identically — systemic block
- No output or error from the tools — just the approval pending message
- Non-terminal jobs (web_search, web_extract, no_agent scripts) may still work
- `last_status: ok` despite zero functional output — the real signal is in the output content, not the status field

**Diagnosis:**

1. Check the `approvals.cron_mode` setting in `config.yaml`:
   ```bash
   grep -A 3 'approvals:' ~/.hermes/config.yaml | grep cron_mode
   ```
   If it says `deny`, this is the root cause.

2. Confirm by checking whether a cron job that used terminal produced any actual output. Read the job's output log to see if commands actually ran or just returned pending_approval messages.

3. Check if no_agent script-based jobs (which bypass both Tirith and terminal) still execute — if yes, it confirms the issue is specifically with terminal approval in cron mode.

**Fix (not nuclear):**

Set `approvals.cron_mode: auto_approve` in `config.yaml`. This allows cron-mode agents to auto-approve commands that Tirith flags — preserving Tirith's scanning for interactive sessions while letting cron jobs run.

```bash
# Using hermes CLI (if available):
hermes config set approvals.cron_mode auto_approve

# Direct YAML edit (if hermes CLI is broken — missing deps, bad venv shebang):
python3 -c "
import yaml
with open('$HOME/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
cfg['approvals']['cron_mode'] = 'auto_approve'
with open('$HOME/.hermes/config.yaml', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False)
"
```

If `pyyaml` is not installed:
```bash
pip3 install pyyaml
```

No gateway restart needed — the config change takes effect on the next cron tick. The next time the cron job runs, terminal commands auto-approve and execute normally.

**What NOT to do:**
- **Do NOT** disable Tirith entirely (`security.tirith_enabled: false`) — this removes security scanning for interactive sessions too
- **Do NOT** reinstall Tirith — it's working correctly
- **Do NOT** convert all cron jobs to `no_agent: true` — that strips LLM reasoning from jobs that benefit from it (trend analysis, anomaly detection, content verification)
- **Do NOT** edit individual job prompts — all cron jobs share the same `cron_mode` setting
- **Do NOT** restart the gateway hoping it fixes the approval issue — the `cron_mode` setting is read fresh each tick

---

## Gateway Not Running

```
⚠ Gateway is not running — jobs won't fire automatically.
```

**Pattern:** Jobs don't fire at all. No errors logged — just nothing happens.

**Root cause:** Gateway process died or was never started (common after container restart).

**Fix:**
```bash
hermes gateway run &    # starts in background (use nohup for persistence)
```
Or install as a service:
```bash
hermes gateway install           # user service
sudo hermes gateway install --system  # boot-time system service
```
