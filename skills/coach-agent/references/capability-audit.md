# Capability Audit & Toolset Minimalism

> **Source:** OWASP LLM Top 10 — LLM01:2025 Prompt Injection; Steward-OS Architecture — Separation of Concerns.  
> **Principle:** Each role gets only the tools it needs. A narrow allowlist beats a broad grant. The role that reads untrusted content must not have the same toolset as the role that acts on the world.

---

## Coach — Toolset Audit

### What Coach DOES
- Reads web pages (browser_navigate, web_extract, web_search) — **HIGH EXPOSURE to indirect injection**
- Runs terminal commands (test suites, build verification, structural gates)
- Reads/writes files (checkpoints, AGENTS.md, verdict JSON)
- Delegates subagents (RefQA tests, adversarial review)
- Searches past sessions (DevKnowledge, gotcha queries)
- Reads Discord/github (future Watcher consumption)

### Toolset: `coach-review` (canonical preset)

| Tool | Needed? | Reason |
|---|---|---|
| browser | ✅ YES | Reference comparison (Tier 1 — core differentiator) |
| terminal | ✅ YES | Structural gates 1-5, 6, 7 |
| file (read/write/search) | ✅ YES | Checkpoints, AGENTS.md, verdict JSON |
| delegation | ✅ YES | RefQA subagents, adversarial reviewer |
| web (search/extract) | ✅ YES | Fetching reference, DevKnowledge lookups |
| session_search | ✅ YES | Past session investigation |
| cronjob | ❌ NO | Coach doesn't schedule jobs |
| memory | ❌ NO | Coach doesn't persist facts |
| image_gen | ❌ NO | Not needed for review |
| tts | ❌ NO | Not needed for review |
| discord | ❌ NO | Coach doesn't post (would be Band C anyway) |
| skills | ❌ NO | Skills are pre-loaded, not dynamically loaded |
| vision | ✅ YES | Screenshot comparison |
| github (MCP) | ❌ NO | Future — when Watcher exists, Watcher handles GitHub |

**Hermes toolset name:** `coach-review`
**Hermes enabled_toolsets value:** `["browser", "terminal", "file", "web", "delegation", "session_search", "vision"]`

---

## Player — Toolset Audit

### What Player DOES
- Reads task descriptions from AGENTS.md (Coach-generated, semi-trusted)
- Reads web docs for implementation reference
- Runs terminal commands (build, test, git, npm)
- Reads/writes files (code, checkpoints)
- Delegates subagents (parallel implementation, test suites)
- Uses browser for live site verification

### Toolset: `player-implement` (canonical preset)

| Tool | Needed? | Reason |
|---|---|---|
| terminal | ✅ YES | Build, test, git, package management |
| file (read/write/search) | ✅ YES | Code editing, checkpoint updates |
| delegation | ✅ YES | Parallel subagents for implementation |
| web (search/extract) | ✅ YES | Docs lookup, API references |
| browser | ✅ YES | Live site verification, canvas testing |
| session_search | ❌ NO | Player doesn't investigate past sessions |
| cronjob | ❌ NO | Player doesn't schedule jobs |
| memory | ❌ NO | Player doesn't persist facts |
| image_gen | ❌ NO | Not needed |
| tts | ❌ NO | Not needed |
| discord | ❌ NO | Player doesn't post |
| skills | ❌ NO | Pre-loaded |
| vision | ✅ YES | Screenshot comparison for visual tasks |
| github (MCP) | ❌ NO | Player uses git via terminal, not MCP |

**Hermes toolset name:** `player-implement`
**Hermes enabled_toolsets value:** `["terminal", "file", "web", "browser", "delegation", "vision"]`

---

## Watcher (Future Phase 3) — Toolset Audit

### What Watcher DOES
- Polls GitHub issues, PRs, upstream repos
- Reads Discord messages
- Searches web for mentions
- Classifies signals (bug/feature/question/noise)
- Writes to watcher queue (local file only)

### Toolset: `watcher-intake` (future preset)

| Tool | Needed? | Reason |
|---|---|---|
| web (search/extract) | ✅ YES | Polling GitHub API, web mentions |
| terminal | ✅ YES | curl, jq for API responses |
| file (write) | ✅ YES | Write watcher-queue.json |
| browser | ❌ NO | Too heavy for API polling |
| delegation | ❌ NO | No need for subagents |
| memory | ❌ NO | No persistence needed |
| discord | ✅ YES | Read Discord messages |
| github (MCP) | ✅ YES | Read issues, PRs, comments |
| cronjob | ❌ NO | Watcher IS a cron, doesn't need to schedule |

**Hermes enabled_toolsets value:** `["web", "terminal", "file", "discord"]`

**CRITICAL:** Watcher has NO write access to the world. It captures to a local queue only. It cannot: close issues, post comments, merge PRs, or reply to Discord. This is the privilege separation that makes the Watcher safe.

---

## Steward (Future Phase 6) — Toolset Audit

### Toolset: `steward-health` (future preset)

| Tool | Needed? | Reason |
|---|---|---|
| terminal | ✅ YES | Disk usage, process checks, log analysis |
| file (read/write) | ✅ YES | Health digests, state tracking |
| session_search | ✅ YES | Session DB health, analytics |
| cronjob | ✅ YES | List/check cron job health |
| web | ✅ YES | Verify deployed URLs |
| discord | ⚠️ LIMITED | Only for RED alerts (Band A with watchdog) |
| delegation | ❌ NO | Single health check, no parallel work |

**Hermes enabled_toolsets value:** `["terminal", "file", "session_search", "cronjob", "web"]`

---

## Subagent Toolset Presets

Subagents should always run with the minimum toolset. Common presets:

| Preset | Toolsets | Use case |
|---|---|---|
| `code-only` | `["terminal", "file"]` | Implementation subagents (Player delegation) |
| `test-runner` | `["terminal", "file"]` | Running test suites in isolation |
| `web-research` | `["web"]` | Research probes, no file or code access |
| `browser-qa` | `["browser", "file"]` | Browser QA subagents (Coach RefQA) |
| `review-adversarial` | `["terminal", "file", "browser"]` | Adversarial reviewer (Phase 4) |

---

## Migration Plan

1. **Immediate (this phase):** Document presets. No enforcement yet — changing existing cron/agent toolset configs requires testing.
2. **Phase 2 (autonomy bands):** Apply `coach-review` and `player-implement` presets to respective cron jobs.
3. **Phase 3 (Watcher):** `watcher-intake` preset applied at creation.
4. **Phase 6 (Steward):** `steward-health` preset applied at creation.

### How to apply a toolset to a cron job

```python
cronjob(action='update', job_id='<id>', enabled_toolsets=["terminal", "file", "browser", "web", "delegation", "session_search", "vision"])
```

---

## Verification

After applying a toolset, verify the agent can still do its job:
- Coach: Can it run structural gates (terminal), load reference pages (browser), write verdicts (file)?
- Player: Can it build (terminal), write code (file), delegate subagents, verify live pages (browser)?
- If a missing tool causes a failure, add it back — but document why. Minimalism with documented exceptions beats unrestricted access.
