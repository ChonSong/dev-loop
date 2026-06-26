---
name: hermes-webui-development
description: Frontend development patterns for the hermes-webui codebase (Python server + vanilla JS). Covers architecture, script loading, session model, SSE streaming integration, UI conventions, and common pitfalls when adding features to the Hermes WebUI.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes-webui, frontend, vanilla-js, sse, sessions, contribution]
    track: development
---

# Hermes WebUI Development Guide

How to add frontend features to the hermes-webui codebase. This covers the
server architecture, JS module patterns, session/streaming model, and CSS
conventions used throughout the project.

## Project Root

`/home/hermeswebui/.hermes/hermes-webui/`

Remotes:
- `origin` → `https://github.com/ChonSong/hermes-webui.git` (your fork / push target)
- `upstream` → `https://github.com/nesquena/hermes-webui.git` (original / PR target)

**PRs target `upstream` (nesquena), NOT origin (the ChonSong fork).**

## Architecture Overview

```
server.py              Thin routing shell (~446 lines). Delegates to api/routes.py.
api/updates.py         Self-update engine (~1469 lines). Git-based check/apply/force
                       plus restart-safety, LLM-generated release summaries.
                       Routes: /api/updates/check, /api/updates/apply, /api/updates/force,
                       /api/updates/summary.
api/routes.py          All GET/POST route handlers (~9700 lines). Reads index.html from disk,
                       replaces __WEBUI_VERSION__, runs inject_extension_tags(), serves.
static/index.html      HTML template (~1323 lines). All UI markup, modal overlays, script tags.
static/style.css       All CSS (~3950+ lines). Themes, mobile responsive, component styles.
static/*.js            13 vanilla JS modules loaded with defer at end of body.
```

**No build step. No bundler. No frontend framework.** Python + vanilla JS only.

## File Inventory (Key Files)

```
static/
  index.html           HTML template — all markup, script tags at end of body
  style.css            All CSS — themes, components, responsive
  ui.js                DOM helpers, renderMd, renderMessages, tool cards, model dropdown (~7300 lines)
  sessions.js          Session CRUD, list rendering, loadSession() (~3600 lines)
  messages.js          send(), SSE handlers, approval, transcript (~2300 lines)
  panels.js            Cron, skills, memory, workspace, profiles, todo, settings (~6500 lines)
  commands.js          Slash command registry, parser, autocomplete (~1300 lines)
  boot.js              Event wiring, keyboard shortcuts, resize handles, boot IIFE (~1600 lines)
  workspace.js         File preview, file ops, loadDir (~370 lines)
  terminal.js          XTerm.js terminal panel
  i18n.js              Internationalization / locale strings
  icons.js             SVG icon constants
  login.js             Login page logic
  onboarding.js        First-run wizard
  tiles.js             Tiling chat interface — multi-session tiles, minimize/focus/close (~850 lines)
```

## How Scripts Are Loaded

Script tags are at the **end of `<body>`** in `index.html` (around line 1229+), all
with `defer`. Order matters:

```html
<script src="static/i18n.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/icons.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/ui.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/workspace.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/terminal.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/sessions.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/commands.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/messages.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/panels.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/onboarding.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/boot.js?v=__WEBUI_VERSION__" defer></script>
<script src="static/tiles.js?v=__WEBUI_VERSION__" defer></script>
```

The `__WEBUI_VERSION__` token is replaced by `api/routes.py` at serve time.
To add a new module: add a `<script>` tag after the last existing one (currently
`tiles.js`), create the file in `static/`, and ensure all functions are global
(no ES module pattern except the streaming-markdown import at the top of the HTML).

## The Global State Object (`S`)

A single global object in `ui.js` holds all application state:

```javascript
const S = {
  session: null,       // Current session object (or null)
  messages: [],        // Current session messages array
  entries: [],         // Transcript entries
  busy: false,         // Is a stream in progress?
  pendingFiles: [],    // Files queued for upload
  toolCalls: [],       // Active tool calls
  activeStreamId: null, // SSE stream ID
  currentDir: '.',     // Current workspace directory
  activeProfile: 'default',
  showHiddenWorkspaceFiles: false,
};
```

Plus `INFLIGHT = {}` — keyed by session_id, tracks in-flight SSE requests.
`SESSION_QUEUES = {}` — keyed by session_id, message queues.

**Pattern**: All JS modules read/write `S` directly. There is no reactivity
system — functions like `syncTopbar()`, `renderMessages()`, `renderSessionList()`
are called explicitly after state changes.

## Session Model (Server Side)

Sessions are stored as JSON files at `~/.hermes/webui/sessions/{session_id}.json`.

Key fields:
```
session_id       hex string, 12 chars (uuid4().hex[:12])
title            string, auto-set from first user message
workspace        absolute path, resolved at creation
model            model ID string
messages         list of OpenAI-format message dicts
created_at       float Unix timestamp
updated_at       float Unix timestamp
pinned           bool
archived         bool
project_id       string or null
message_count    int (denormalized)
last_message_at  float (denormalized)
active_stream_id string or null (set by streaming.py)
is_streaming     bool (denormalized, from active_streams count)
```

## Key Integration Points

### Opening a Session (Sidebar Click)

`sessions.js` → `loadSession(sid)`:
1. Fetches metadata only: `GET /api/session?session_id={sid}&messages=0&resolve_model=0`
2. Sets `S.session` to the session object
3. Clears `S.messages` and shows "Loading conversation..."
4. For streaming sessions: restores from INFLIGHT cache, reattaches SSE
5. For idle sessions: calls `_ensureMessagesLoaded(sid)` to fetch full messages
6. Calls `syncTopbar()`, `renderMessages()`, `loadDir('.')`

**To intercept sidebar clicks**: Add logic at the top of `loadSession()` to
redirect to custom handling before the existing code runs.

### Sending a Message

`messages.js` → `send()`:
1. Reads `$('msg').value` (the single global textarea)
2. Checks `S.busy` — if busy, queues or steers based on `_busyInputMode`
3. Forwards to `/api/chat` with session_id, message, model, profile
4. Returns `stream_id` → attaches SSE via `attachLiveStream()`
5. SSE events update `S.messages` in real-time via `window.smd` parser

**Per-tile sending**: Cannot reuse `send()` directly — it reads the global
`#msg` textarea. Create a tile-scoped version that POSTs to `/api/chat` and
manages its own INFLIGHT entry.

### SSE Streaming

`messages.js` handles SSE via `attachLiveStream(sid, streamId, attachments, options)`:
- Opens `GET /api/chat/stream?stream_id={streamId}`
- Parses SSE events → updates `S.messages` → calls `renderMessages()`
- On done/error: sets `S.busy = false`, updates header

**Server-side cancellation**: `POST /api/chat/cancel?stream_id={streamId}`

## Self-Update System (`api/updates.py`)

The WebUI can self-update via git operations from the frontend.
Two repos are tracked independently: the WebUI checkout and the Hermes Agent checkout.

### Key Files

| File | Role |
|------|------|
| `api/updates.py` | All server-side: check, apply, force-reset, summary generation |
| `static/ui.js` (~lines 5400-5830) | Frontend: update banner, `applyUpdates()`, `forceUpdate()`, "What's New" panel |
| `static/boot.js` (~line 1927) | Non-blocking boot-time update check (fire-and-forget, once per tab) |

### Check Flow

Boot / "Check for Updates" → `POST /api/updates/check`:
- `git fetch origin --tags --force` (15s timeout)
- Check release tags first (HEAD behind latest tag?)
- Fallback: count commits behind `@{upstream}`
- Cache result for 30 minutes (git fetch runs at most 2x/hour)

Frontend: `_showUpdateBanner(data)` → gold `#updateBanner` with "⬆ N updates" + "What's new?" links.

### Apply Flow

User clicks "Update Now" → `POST /api/updates/apply (target: 'webui'|'agent')`:

**Restart safety** (`_restart_blocker_snapshot()`):
- Checks `STREAMS` (active SSE) and `ACTIVE_RUNS` (detached workers)
- Returns `restart_blocked: True` if work is in-flight
- `_wait_until_restart_safe()` polls every 2s up to 300s, then proceeds anyway
- `_apply_lock` prevents concurrent updates on both repos

**Git operations** (`_apply_update_inner()`):
1. `git fetch origin --tags --force`
2. Select target ref via `_select_apply_compare_ref()` (prefers release tag, falls back to `@{upstream}`)
3. Dirty tree? → `git stash push -m 'hermes-update-autostash'`
4. `git pull --ff-only <remote> <branch>` (30s timeout)
5. On success: re-apply stash, `reset --hard HEAD` if stash conflicts
6. On failure: restore stash, return `diverged: True` or `conflict: True`

**Self-restart** (`_schedule_restart(delay=2.0)`):
- Waits for active runs to finish (300s max)
- Purges `__pycache__` dirs under both repos (avoids stale-bytecode crashes)
- `os.execv(sys.executable, [sys.executable] + sys.argv)` replaces process in-place
- On Windows: `subprocess.Popen(DETACHED_PROCESS) + os._exit(0)` instead
- Browser: `setTimeout(() => location.reload(), 1500)` — lands just after restart

**Force path** (`apply_force_update()`):
- `git checkout .` (discard all local changes) + `git reset --hard <compare_ref>`
- Requires user confirmation via `showConfirmDialog({danger: true})`
- Only offered when `apply_update()` returned `conflict` or `diverged`

### "What's New" Summary

`POST /api/updates/summary`:
1. Fetches commit subjects via `git log <current>..<latest>`
2. Optionally passes through LLM callback for natural-language summary
3. Deterministic fallback: lists commit subjects directly
4. Cached per update range (SHA signature)
5. Frontend caches in `sessionStorage` across reloads

### Pitfalls

- **Update refused during active chat**: By design — `os.execv()` kills everything. Wait for agent to finish.
- **Docker deployments**: Self-update only works in git-checkout installs. Docker images lack `.git`. Update by pulling new image.
- **Fork tracking**: Update check compares against `origin`. If `origin` is a personal fork, upstream releases are not detected. Use `git remote add upstream` + tracking.
- **Stash conflicts**: If re-apply fails, changes are preserved in `git stash` but lost from working tree. User gets recovery instructions.
- **Force update is destructive**: `git checkout .` discards ALL uncommitted changes in that repo.
- **Version detection**: `git describe --tags --always --dirty` — Docker builds use baked `api/_version.py` fallback.
- **Secret scrubbing**: Git diagnostics redact credentials from URLs, GitHub tokens, and query params before reaching the API.
- **sessionStorage flag**: `hermes-update-checked` prevents banner re-fire within the same tab session. Close and reopen tab to re-check.

## CSS Conventions

- All CSS is in `static/style.css` (~3950+ lines)
- CSS custom properties on `:root` and `:root.dark` for theming
- Mobile responsive via `@media(max-width:640px)` breakpoints
- New component styles should follow existing patterns:
  - `.component-name` for the container
  - `.component-name-element` for children
  - `.component-name--modifier` for state variants
- For new features: append styles at end of file

## Adding a New Feature (Checklist)

1. Create `static/feature.js` with IIFE or global functions
2. Add `<script src="static/feature.js?v=__WEBUI_VERSION__" defer></script>` after the last module in `index.html`
3. Add CSS to end of `static/style.css`
4. If modifying existing behavior: edit the target file at the **top** of the
   relevant function (not at the end) so intercepts don't break existing logic
5. Update `ARCHITECTURE.md` if adding new files or changing architecture
6. Update `CHANGELOG.md` under `[Unreleased]` with feature/fix entry
7. `pytest tests/ -x -q` to verify no regressions (full suite takes >2min; use search-specific tests for quick iteration)

## Submitting a PR

When the user asks to open a PR on the **upstream** (original) repo:

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes, commit with a descriptive message including `Co-Authored-By: OWL <owl@hermes>`
3. Push to your fork: `git push origin feature/my-feature`
4. Open the PR against `nesquena/hermes-webui` (the upstream remote)

**IMPORTANT**: The `gh` command on this system is NOT the GitHub CLI — it's a
browser-opener tool. To create PRs via API, use Python `urllib.request` or
`curl` with a token. The token may be in `~/.git-credentials` (old) or in the
`.env` file as `GITHUB_PAT` (new). Read `.env` with Python `open()` since the
shell masks the value:

```python
with open('/workspace/.env', 'rb') as f:
    for line in f.read().decode().split('\n'):
        if 'GITHUB_PAT' in line:
            token = line.strip().split('=', 1)[1].strip().strip('"').strip("'")
```

Then use `urllib.request` to POST to `https://api.github.com/repos/nesquena/hermes-webui/pulls`.

**Be aware**: Fine-grained PATs need explicit `Pull requests: Write` scope on the
target repo. If API returns 403 (not 401), the token is valid but scoped too
narrowly — ask the user to update the PAT's repository permissions. Fall back to
giving the user the direct PR creation URL:
```
https://github.com/nesquena/hermes-webui/compare/master...ChonSong:branch-name
```

## Common Pitfalls

- **Don't use ES modules** for new JS files (except for streaming-markdown which already uses `type="module"`). All other code uses global functions.
- **Don't put script tags in `<head>`** — they go at end of `<body>` with `defer`.
- **Don't add `async`** to script tags — `defer` preserves execution order.
- **Don't break `S` global structure** — all modules depend on it.
- **Don't forget `credentials: 'include'`** on fetch calls (auth cookies).
- **Use `document.baseURI`** instead of `location.href` for URL construction (the app supports subpath mounting via `<base>` tag).
- **`loadSession()` is the sidebar click handler** — put intercepts there for multi-session/tile patterns.
- **`__WEBUI_VERSION__` token** is replaced server-side. Always use this in script src URLs, not hardcoded versions.
- **CSS specificity**: Existing CSS uses low-specificity selectors. Keep new CSS at the same level to avoid specificity wars.
- **Check upstream before implementing**: The ChonSong fork and the nesquena upstream diverge (often by 200+ commits). Always check `git show upstream/master:<path>` to see if a feature already exists upstream before spending time re-implementing.
- **When the user says "it's not working" for a feature that should exist**: Check versions FIRST.
  1. `git describe --tags --always` — local version
  2. `git describe --tags upstream/master` — upstream version
  3. If local is behind, the feature may simply not be installed yet — offer to rebase to upstream rather than re-implementing.
- **Don't implement features that already exist in the codebase**: Before writing code, search for the feature (`search_files`, `grep`). Confirm it's truly missing before implementing.
- **When the user says "add a PR to hermes-webui for feature X"**: They likely want the feature to work in their installation, not necessarily a net-new contribution. Follow this order:
  1. Check if the installed version already has it (`search_files`, `grep`)
  2. If not, check if upstream has it (`git show upstream/master:<path>`)
  3. If upstream has it but local doesn't, rebase rather than implementing from scratch
  4. Only implement from scratch if the feature truly doesn't exist anywhere
- **Clarify the target repo**: When the user says "hermes-webui", they could mean the ChonSong fork (this install, `origin`) or the upstream (`nesquena/hermes-webui`). If ambiguous, ask — or check both. The fork can be significantly behind upstream (200+ commits is common).
- **`gh` is NOT the GitHub CLI**: The `gh` binary on this system is a custom browser-opener tool. Do NOT use it for API calls, PR creation, or authentication.
- **Verify push success immediately**: After `git push`, always verify the remote branch has the correct commit (`git log origin/branch-name --oneline -3`). Repos can be reset/rebased by external processes (CI, other agents, manual resets), wiping commits. If the push reports success but the commit is missing, the branch was reset server-side — you'll need to force-push or re-apply changes.
- **Fine-grained PATs need explicit scopes**: A fine-grained GitHub PAT with only `Contents: Read` cannot create PRs. It needs `Pull requests: Write` on the target repo. If API returns 403, check token scopes. Classic tokens with `repo` scope work for everything.
- **Git credentials / env tokens may be stale**: The token in `~/.git-credentials` can expire — `git push` will fail with auth errors. The `.env` file may contain a `GITHUB_PAT` key — read it with Python `open()` + string parsing since the shell masks `echo $GITHUB_PAT` output. If push auth fails, ask for a fresh PAT.
- **Working tree can be reset without warning**: If `git status` shows clean but your commits are gone, the repo was likely hard-reset. Check `git reflog` for lost commits. If the reflog is also clean, the commits are unrecoverable and work must be redone. |
- **Files you didn't modify can disappear too**: A git reset/rebase doesn't just affect your branch — it can revert the entire working tree to an older state, destroying uncommitted changes across ALL files. Always commit or stash your work before any git operations that rewrite history.
- **Session tab leak from boot/reconnect loops**: `boot.js:1176` calls `await newSession()` when no session is restored on page load. If the soft recovery path (`ui.js:123-131`) fails, it falls back to `window.location.reload()` — which creates infinite reload loops that generate hundreds of 0-message sessions. `messages.js:694,768,789,797,812,828` all call `newSession()` when `S.session` is null, compounding the problem. When adding features that interact with session creation, take care not to trigger session creation as a side effect of page initialization.
- **Session lifecycle memory leak (`session_lifecycle.py`)**: The `_sessions` dict in `api/session_lifecycle.py` is process-global and grows monotonically. Every call to `register_agent()` or `mark_turn_completed()` inserts a key, but `discard_session()` is the only removal path — and historically, no runtime code called it for tab-close or session-delete events. Documented in a code comment: *"The `_sessions` dict is process-global and historically only ever grew: `register_agent` / `mark_turn_completed` insert keys but no runtime path ever removed them, so every unique session_id the WebUI touched leaked a"*.

  **Impact**: Every session the webui ever touches adds a permanent in-memory entry. Combined with the tab-leak loop, this can grow unbounded. Fix would be wiring `discard_session()` into session-close or sidebar-delete paths.

  **Detection**: Monitor the length of `_sessions` under `api/session_lifecycle._lock`. If it exceeds the count of distinct active sessions in the sidebar, there's a leak.

## Credential Pool System

The WebUI has a credential pool system for managing multiple API key credentials per provider. The pool breakdown UI already exists in the frontend but only renders for providers in `_ACCOUNT_USAGE_PROVIDERS` (Codex, Anthropic). For all other providers (opencode-zen, opencode-go, etc.), the pool data is in `auth.json` but the UI never shows it.

**Full architecture details, code locations, and auth.json schema:** See [`references/credential-pools.md`](references/credential-pools.md)