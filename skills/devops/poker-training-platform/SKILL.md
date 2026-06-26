---
name: poker-training-platform
description: "Build a poker GTO training platform (GTO Wizard clone): equity calculator, MCCFR solver, training quizzes, hand history analysis, ICM calculator. Covers open-source library stack, CFR algorithm, HH formats, and tech stack selection."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [poker, gto, cfr, equity, icm, hand-history]
    track: infrastructure
---

# Poker Training Platform — GTO Wizard Clone Skill

Build a full-featured open-source GTO poker training platform clone of gto-wizard.com.

## Trigger Conditions

- User asks to build a poker training tool
- User asks about GTO solvers, poker equity calculators, ICM tools
- User mentions PokerStars hand history analysis, GTO strategy training
- Feature request involves poker ranges, hand evaluation, or CFR algorithms

## What GTO Wizard Is

**gto-wizard.com** — subscription SaaS poker training platform. Core features:

| Feature | Description | Technical approach |
|---------|-------------|-------------------|
| GTO Solver | Nash equilibrium strategy via CFR | MCCFR + Numba JIT |
| Equity Calculator | Hand vs range equity | Monte Carlo + exact enumeration |
| Training Quizzes | Random spots → user guesses GTO action | Quiz DB + spot randomization |
| Hand History Analysis | Upload HH → parse → leak detection | HH parsers + GTO comparison |
| ICM Calculator | Tournament chip equity | Malmoud-Harville formula |
| Range Builder | Visual 13x13 grid hand selector | React component |

## Open-Source Library Stack

### Poker Engine (equity + hand evaluation)
- `zekyll/OMPEval` (224⭐, C++) — fast 5-card hand evaluation, use via `ctypes` or rewrite in Python
- `siavashg87/poker-odds-calc` (99⭐, Node) — fast equity calc patterns
- `thotbreakerr/Texas-Hold'em-AI` (1⭐, Python) — **Reference MCCFR implementation** (use as starting point)
- `sweeterthancandy/CandyPoker` (13⭐) — equity + solver patterns

### ICM & Tournament
- `apcode/poker-mtt-icm` (12⭐, Python) — tournament ICM calculator
- `pwn2ooown/Simple-ICM-Calculator-Python` — DFS-based ICM

### Hand History Parsing
- `aneopsy/PokerStats` (18⭐, Python) — PokerStars HH parser
- `alexyz/poker` (140⭐, Java) — PokerStars + Full Tilt parser (reference for format)

### Range Equity
- `battermann/equiweb` (8⭐) — in-browser range equity (reference for React UI)
- `sol5000/gto` (14⭐) — Streamlit GUI + Monte Carlo equity

## MCCFR Algorithm — Core Implementation Notes

```
MCCFR (Monte Carlo Counterfactual Regret Minimization)

1. Initialize strategy for all information sets (player + game state)
2. Loop iterations:
   a. Sample game tree (chance sampling for card dealing)
   b. Play to terminal with current strategy
   c. Compute regrets: R += value_of_alternatives - value_of_current_action
   d. Update strategy: σ += R+ (positive regrets only)
   e. Normalize strategy
3. Result: Nash equilibrium strategy profile
```

**Performance targets (2-player, heads-up):**

| Street | Time | Notes |
|--------|------|-------|
| River | <1s | Fewest nodes |
| Turn | <10s | Moderate |
| Flop | <60s | Most complex |
| Pre-flop | <30s | Lookup table preferred |

**Multi-way (3+ players):** multiply times by 5-10x.

**Numba JIT optimization:** Decorate hot CFR functions with `@numba.jit(nopython=True)` for 10-50x speedup over pure Python.

## Hand History File Formats

### PokerStars Format
```
PokerStars Hand #123456789: Hold'em No Limit (0.01/0.02) - 2026-05-25
Table 'Asteria' 6-max Seat #1 is the button
Seat 1: player1 (150.00 in chips)
...
*** HOLE CARDS ***
Dealt to player1 [Ah Kh]
*** COMMUNITY CARDS ***
[As Qs Jh]
*** SHOWDOWN ***
player1: shows [Ah Kh] (two pair, Aces and Queens)
...
*** SUMMARY ***
Total pot 45.00 | Rake 0.45
Board: [As Qs Jh]
```

### Key Parser Fields
- `hand_id` — unique identifier
- `game_type` — Hold'em / PLO / etc.
- `limit_type` — No Limit / Pot Limit
- `stakes` — small blind / big blind amounts
- `table_name`, `max_seats`, `button_position`
- `players[]` — name, position, starting stack, hole cards
- `actions[]` — preflop/flop/turn/river betting rounds
- `board[]` — community cards
- `pot` — total pot at showdown
- `winners[]` — player + amount won

## Recommended Tech Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Frontend | Next.js 15 + React 19 + TypeScript | SSR + routing |
| UI Components | Tailwind CSS v4 + Shadcn UI | Pre-built components |
| Backend | FastAPI (Python 3.12) + Pydantic v2 | Async, WebSocket |
| Solver | Python 3.12 + NumPy + Numba | CPU-intensive CFR |
| IPC | gRPC (separate solver service) OR direct Python import | Offload CFR to dedicated process. **Direct import is preferred for real-time solves** (<200 iters, sub-second response). gRPC for batch/isolated solves. |
| Database | PostgreSQL (Neon serverless) | Free tier, JSONB for strategy storage |
| Cache | Redis | Equity result caching (key: hash of board+ranges) |
| Containers | Docker + Docker Compose | Solver isolation |

## Architecture

```
apps/
  web/              # Next.js 15 frontend
  api/              # FastAPI backend (REST + WebSocket)
  solver/           # Python gRPC service (CFR engine)
packages/
  poker-core/       # Shared: deck, hand eval, equity, range (Python + TS bindings)
  ui-components/    # Shared React components (range grid, board renderer)
  types/            # Shared TypeScript types
infra/
  docker/           # docker-compose.yml for all services
```

## Poker Range Notation → 169 Combos

The 169 preflop hands (13×13 grid):
- **Unpaired:** 78 combos (e.g., AKs = 4, AQs = 4, ..., 72o = 12)
- **Pairs:** 13 combos (AA = 6, KK = 6, ..., 22 = 6)
- **Suited total:** 78, **Offsuit total:** 78

Range strings:
- `AA-CC` → pairs AA, KK, QQ, JJ, TT, 99, ..., CC
- `AKs, AQs, AJs` → suited Broadway hands
- `T8o+` → T8o, T9o, J8o, ...

**Range → combos expansion:**
```python
def expand_range(range_str: str) -> list[tuple[str, str]]:
    """Parse 'AKs, TT+98s' → list of card tuples like ('A', 'K')"""
    hands = []
    for token in range_str.split(','):
        token = token.strip()
        if '-' in token and not '+' in token:
            # Range: 'JJ-TT' → all pairs from JJ to TT
            ...
        elif token.endswith('o'):
            # Offsuit: 'T8o' → T8 offsuit combos
            ...
        elif token.endswith('s'):
            # Suited: 'T8s' → T8 suited combos
            ...
    return hands
```

## ICM Formula (Malmoud-Harville)

```
For N players with stacks s_1, ..., s_N and prizes p_1 >= p_2 >= ... >= p_N:

Equity_i = Σ_{j=1}^{N} p_j × Pr(finish jth | stack s_i)

Pr(finish jth) computed via dynamic programming:
- Base: last place → prize N / chips_N
- Recursive: Pr(place k) = Σ_i (stack_i / total_chips) × Pr(previous_place k from remaining)
```

## Standalone / No-Docker Deployment

When deploying outside Docker (serverless, dev machines, containers without Docker socket), use fallback services to replace Redis and PostgreSQL:

### Redis → Fakeredis
```python
def init_redis(app: FastAPI):
    redis_url = os.environ.get("REDIS_URL", "")
    try:
        if redis_url:
            import redis; app.state.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            import fakeredis; app.state.redis = fakeredis.FakeRedis(decode_responses=True)
        app.state.redis.ping()
    except Exception as e:
        import fakeredis; app.state.redis = fakeredis.FakeRedis(decode_responses=True)
```
Install: `pip install fakeredis`

### PostgreSQL → SQLite (aiosqlite)
```python
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    _sqlite_path = "gto_wizard.db"
    DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath(_sqlite_path)}"
```
Install: `pip install aiosqlite`

**Caveats:** SQLite doesn't support `JSONB` column type — replace with `JSON` or `Text`. No connection pooling — set `pool_size=1` when SQLite detected. Fakeredis has no persistence — cache resets on restart.

### gto-poker Editable Install Trap

If `gto_poker` is installed via `pip install -e .` from `/tmp/`, all edits to the real `/workspace/` copy are **silently ignored**. Symptom: `gto_poker.__file__` shows `/tmp/...` path. **Fix:** `pip uninstall -y gto-poker && cd /workspace/packages/poker-core && pip install -e .` Check with `pip show gto-poker` → `Editable project location:`.

### PYTHONPATH for Mixed Backend Imports

The FastAPI backend uses two conflicting import styles:
- `from routers import equity` (relative to `apps/api/`)
- `from apps.api.websocket.manager import get_websocket_manager` (absolute from repo root)

**Fix:** Set `PYTHONPATH` to include BOTH directories:
```bash
PYTHONPATH="/workspace/gto-wizard-clone/apps/api:/workspace/gto-wizard-clone"
cd /workspace/gto-wizard-clone
uvicorn apps.api.main:app --host 0.0.0.0 --port 8002
```

Without this, either `ModuleNotFoundError: No module named 'routers'` (missing `apps/api`) or `No module named 'apps'` (missing repo root).

### equity_vs_range Monte Carlo Counting Bug

See `references/equity-vs-range-algorithm.md` for full trace of the bug, fix, and verification.

Bug: `villain_losses < len(villain_combos)` excludes the case where hero beats ALL combos (villain_losses == len), so wins are never counted. Fix: simplify to `if villain_wins == 0: if villain_losses > 0: wins += 1 else: ties += 1` — no len comparison needed. Verify: AA vs KdKh on QsJs2c → 0.839 (fixed) vs 0.0 (buggy).

### Next.js Monorepo Version Conflict

Root `package.json` Next.js version must match workspace `apps/web/package.json`. If root has `next: "^16.2.7"` but workspace has `next: "^15.2.4"`, turbopack loads root's Next.js 16 types which mismatch the app's Next.js 15 types. Fix: `"next": "^15.2.4"` in root, then `rm -rf node_modules/next && npm install`.

## Deployment Pitfall — Port 8002 Conflict

**Port 8002 is claimed by Chrome's network service** in the Hermes container. The Chrome browser's network.mojom.NetworkService binds to port 8002 internally, making it unavailable for the API server. Symptom: `ERROR: [Errno 98] address already in use` even after `fuser -k 8002/tcp`.

**Diagnosis:**
```bash
# Check what's holding port 8002
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  if cat /proc/$pid/net/tcp 2>/dev/null | grep -q "1F42"; then
    echo "PID $pid: $(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')"
  fi
done
# Chrome processes will show up — they're not killable (container-managed)
```

**Fix:** Use a different port (e.g., 8003) and set `NEXT_PUBLIC_API_URL` accordingly:
```bash
# Start API on alternate port
cd /workspace/gto-wizard-clone && PYTHONPATH="apps/api:packages/poker-core/src" \
  uvicorn main:app --host 0.0.0.0 --port 8003

# Start web app with alternate API URL
NEXT_PUBLIC_API_URL=http://localhost:8003 next start -p 3000
```

## Deployment Pitfall — Hermes Gateway Port Claim

The Hermes gateway (`hermes gateway run`) also claims port 8002. If you kill it to free the port, it may auto-restart. Using port 8003 avoids all conflicts.

## Deployment Architecture — Two Frontends Problem

**CRITICAL: There are TWO separate frontends. Do NOT deploy the open-lovable one.**

| Frontend | Path | Status | Notes |
|----------|------|--------|-------|
| **Open Lovable** | `/workspace/open-lovable/app/gto/` | ❌ Do NOT deploy | Template/base project. Title says "Open Lovable v3". Has proto pages but NOT the real app. |
| **GTO Wizard Web** | `/workspace/gto-wizard-clone/apps/web/` | ✅ This is the real frontend | Title says "GTO Wizard". Has PWA, proper API rewrites, shared component libs. |

The gto-wizard-clone web app (`apps/web/`) is the ONLY frontend that should be deployed. It proxies API requests via Next.js rewrites defined in `apps/web/next.config.ts`:

```
/api/*, /icm/*, /plo4/*, /double-board/*, /bomb-pot/*, /ws/* → NEXT_PUBLIC_API_URL (default: localhost:8002)
```

The tunnel must route:
- `wiz.codeovertcp.com` → container port (gto-wizard-clone web app frontend)
- `wiz.codeovertcp.com/api/*` → container port 8002 (FastAPI backend)

### Quick Diagnostic

If the deployed site title says "Open Lovable v3", you're serving the wrong frontend. Check:
```bash
curl -s https://wiz.codeovertcp.com/ | grep '<title>'
# Should say: <title>GTO Wizard</title>
# If it says "Open Lovable v3", the wrong app is deployed
```

## QA Strategy — Tests That Actually Matter

**Do NOT rely on the custom Puppeteer script at `/workspace/ui-qa-tool/ui-qa.js`.** It only checks element existence ("does this button appear?"), not functional correctness ("does this button produce the right result?").

The project has **real E2E tests** via Playwright:
- Location: `/workspace/gto-wizard-clone/apps/web/tests/`
- 74 Playwright E2E tests testing actual user flows
- Run with: `cd /workspace/gto-wizard-clone && npm run test:e2e` (from apps/web/)

### QA Hierarchy (best to worst)

1. **Playwright E2E tests** — test complete user flows with real API calls
2. **API contract tests** — verify request/response schemas
3. **Functional checks** — "does Calculate Equity return a number?" (not just "does the button exist?")
4. **Visual regression** — pixel-diff screenshots (only after functional correctness is verified)
5. **Element existence** — the ui-qa.js approach (least valuable, but fast)

### When QA Reports "All 127 Checks Passed"

This means nothing if the checks are all element-existence checks. A site can pass 100% of element checks and still have zero working functionality. Always verify:
- API responses are real data (not empty/mock)
- Interactive flows complete end-to-end
- Error states are handled (not just happy path)

## Deployment

### Port Conflicts

Port 8002 is claimed by Chrome's network service in the Hermes container — not killable. Use port 8003 instead. See `references/deployment-architecture-2026-08.md` for diagnosis and fix.

### cloudflared Tunnel Config Caching

The Cloudflare edge caches tunnel ingress config. Editing the local `config.yml` does NOT update the tunnel. You must kill ALL cloudflared processes and restart fresh. See `references/deployment-architecture-2026-08.md`.

### Hermes Init Auto-Starts open-lovable on Port 8564

The Hermes init system auto-starts `next dev -p 8564` in the open-lovable directory. Kill these processes before deploying the gto-wizard-clone web app. See `references/deployment-architecture-2026-08.md`.

### Correct Start Sequence

1. Kill port conflicts (stale next servers, cloudflared)
2. Start API on port 8003 (avoids Chrome's port 8002)
3. Build web app: `cd apps/web && next build`
4. Start web app: `NEXT_PUBLIC_API_URL=http://localhost:8003 next start -p 3000`
5. Start tunnel: `cloudflared --config /workspace/gto-wizard-config.yml tunnel run`
6. Verify: `curl -s https://wiz.codeovertcp.com/ | grep '<title>'` → "GTO Wizard"

### QA Strategy — Tests That Actually Matter

**Do NOT rely on the custom Puppeteer script at `/workspace/ui-qa-tool/ui-qa.js`.** It only checks element existence, not functional correctness.

The project has **real E2E tests** via Playwright:
- Location: `/workspace/gto-wizard-clone/apps/web/tests/`
- 74 Playwright E2E tests testing actual user flows
- Run with: `cd /workspace/gto-wizard-clone && npm run test:e2e` (from apps/web/)

### QA Hierarchy (best to worst)

1. **Playwright E2E tests** — test complete user flows with real API calls
2. **API contract tests** — verify request/response schemas
3. **Functional checks** — "does Calculate Equity return a number?"
4. **Visual regression** — pixel-diff screenshots
5. **Element existence** — the ui-qa.js approach (least valuable)

## Phase Engine Pattern for Large Builds

Use the `autonomous-cron-pipeline` skill with these phase names for a GTO Wizard clone:

| Phase | Name | Focus |
|-------|------|-------|
| 1 | Foundation | Monorepo, Docker Compose, Next.js, TypeScript types |
| 2 | Equity Engine | Range selector, Monte Carlo engine, Redis caching |
| 3 | GTO Solver | MCCFR algorithm, pre-flop tables, gRPC service |
| 4 | Training Mode | Quiz DB, spot randomization, leaderboards |
| 5 | Hand History | HH parsers (PokerStars, GGPoker, Winamax), leak analysis |
| 6 | ICM + Polish | ICM calculator, push/fold charts, PWA, E2E tests |

## Subagent Delegation Lessons (2026-08)

**Parallel subagents timing out:** When delegating large frontend modification tasks to 3 parallel subagents, all three timed out after 600s (10 min) each. The subagents were modifying many files across the codebase and couldn't complete in time.

**Better approach:** For large-scale mock-data-to-API migration across many files, it's more effective to:
1. Do the work directly in the main session
2. Focus on one page at a time
3. Use smaller, more targeted subagents (1-2 files max) if delegating
4. Equity page already had working API hooks — just needed the data to be present

**User preference:** User wants "high quality and complete" work, "it doesnt need to be done fast", and wants it done "without me" — autonomous completion. Don't rush or cut corners.

## Cron Troubleshooting

For general cron job debugging patterns (model:null, deliver:origin, /tmp persistence, cache dirs), see:
`references/cron-troubleshooting-patterns.md`

## GTO Wizard Design Spec — Training Page (2026-06-07)

The user provided a complete single-file HTML mockup as the canonical design spec. The training page at `/gto/training` uses a **two-view pattern** toggled by a `showTraining` state variable:

### Setup View (default, `!showTraining`)
- **Table oval** — 6 seats (CO, BTN, SB, BB, UTG, HJ) positioned via absolute `top`/`left` percentages in a CSS radial-gradient oval
- **Card backs** — 5 "W" back-of-card placeholders in the center
- **Solutions pill** — `Cash • 6max • NL25 • General` with badge "13", opens solutions modal
- **Starting spot** — Segmented control: Preflop / Flop / Custom
- **Preflop action** — Chip buttons: Any, SRP, 3-bet, 4-bet, 5-bet, Squeeze, Limp, Iso (singleton selection)
- **Footer** — ALL SETTINGS link (opens same modal) + START TRAINING button
- **Banner** — Fixed-bottom teal guide banner, closable

### Training View (`showTraining === true`)
- **Action strip** — Horizontal scroll of position chips with stack size + action text, flop mini-cards, active highlight (teal border + darker bg)
- **3-column layout** (`56px 1fr 320px`):
  - **Tool bar** — 9 SVG icon tools (Focus, Select, Play, Reset, Settings, Study, Mute, More, Chart), single-active
  - **Table area** — Oval with BB (orange border + glow) and CO (teal border + glow) seats, hero cards (♥♣), board cards (border-radius 11px), matchup/pot labels, action buttons (CHECK green, BET red)
  - **Info panel** — Strategy/Range tabs, 13×13 action-color matrix with diamond/highlight cells, overall frequency bar, hand strength/equity meters, hand breakdown by category

### Solutions Modal
- Filter groups: Solutions, Type, Players, Rake, Postflop bet sizes, Opening size, Effective stack
- Locked filters get lock SVG icon + reduced opacity (.45)
- NEW badge on "Single Size" postflop bet size
- Confirms with "13 selected from 13 situations" footer

### Design Tokens (from spec, confirmed working)
```css
--bg: #0e0e0f;  --panel: #1a1c1e;  --border: #2a2e32;
--text: #d7d7d7;  --muted: #8a8f98;  --teal: #00b894;
--green: #2ecc71;  --red: #e74c3c;  --orange: #e67e22;
```
Font: `Inter, system-ui, sans-serif`. Nav height: 48px. Sidebar width: 220px.
All components use inline React `style={{}}` (no Tailwind classes in the new layout).

### Implementation Notes
- Layout renders in `app/gto/layout.tsx` — the `<main>` wrapper sets flex:1 + overflow:auto
- Training page is `app/gto/training/page.tsx` — full page, no `<Link>` to sub-routes
- The 13×13 matrix uses a pre-computed `generateMatrixData()` function with `CELL_CLASSES` mapping
- Seat positions use absolute percentage positioning (responsive within the oval)
- The old Next.js server on port 8564 survived multiple `pkill` attempts and served stale layout for ~20 minutes — resolved with `kill -9 $(lsof -t -i :8564)`

## GTO Wizard-Specific Implementation (ChonSong/gto-wizard-clone)

> Absorbed from `domain/poker-gto-wizard-clone` skill — targets the specific repo at `github.com/ChonSong/gto-wizard-clone`.

### ChonSong Repo Structure

```
apps/web         — Next.js 15 (React 19, TypeScript, Tailwind v4, Shadcn UI)
apps/api        — FastAPI (Python 3.12) REST + WebSocket
apps/solver     — Python gRPC (CFR engine, Numba JIT, separate process)
packages/
  poker-core    — deck, hand eval, equity, range (Python + TypeScript)
  ui-components — shared React components
  types         — shared TypeScript types
```

### Omaha Variants (ChonSong Repo)

| Variant | Library | Notes |
|---------|---------|-------|
| PLO4 (primary) | `HenryRLee/PokerHandEvaluator` (501⭐, C++/Python) | `pip install poker-hand-evaluator` |
| PLO5 | Same evaluator, 5-card variant | |
| Omaha Hi/Lo 8-or-better | Same + hi/lo split logic | Low qualifier: 8-or-better |
| Shortdeck (6+ Hold'em) | Same + `DeckType.SHORTDECK` | Flush > full house reversed ranking |
| Double Board PLO — NOVEL | Two evaluator instances + merged ranking | See `references/double-board-plomd` |
| PLO Bomb Pot — NOVEL | Pre-flop circular betting, 4 community simultaneously | Custom betting handler |

### Phase Execution via Cron (ChonSong Repo)

Each phase runs as a cron job with inline skill loading:
- Model: `@opencode-go:deepseek-v4-flash` — use this for ALL GTO-related cron jobs (user preference). Do NOT use openrouter models for poker work unless explicitly overridden.
- Deliver: `local` (accept that delivery to chat is unreliable — see `autonomous-cron-pipeline` skill pitfall 20)
- Repeat: `100x` for active work; reduce to `1/1` for completion-check jobs
- Skills: **prefer empty (`skills: []`)** — inline instructions directly in the prompt. Only attach skills verified safe for cron context. See `autonomous-cron-pipeline` pitfall 25.

```bash
# Phase 1 example prompt (skills inlined, NOT attached):
"Phase 1: Implement Python equity engine with OMPEval.
Use test-driven-development: write tests first, then implementation.
Build hand evaluator, deck, and equity calculator.
All tests green before commit. Push to gto-wizard-clone main."
```

### Cron Stability Rules (2026-06-01 Lessons)

1. **Skill attachment is safe for workflow skills** — The blanket "Keep skill lists empty on cron jobs" is overly conservative. Skills that provide workflow/algorithm guidance ONLY (`test-driven-development`, `blueprint`, `repo-transmute`, `docker-patterns`, `e2e-testing`) work fine in cron context. Skills that access the local filesystem (`repo-init` reads `.env`) can fail with PermissionError. **Rule:** attach workflow skills; avoid skills that read filesystem paths.
2. **Avoid Monte Carlo tests in cron prompts** — Tests like `test_equity.py` (exact enumeration) and `test_icm.py` (prize extension) hang indefinitely, killing the cron job. Replace with fast checks: `python3 -c "from gto_poker.plo4 import PLO4Evaluator; print('OK')"`.
3. **Use `timeout` on all test commands** — `timeout 60 python3 -m pytest packages/poker-core/tests/test_plo4.py -v --tb=short`
4. **Check for secrets after amending cron commits** — Cron jobs may write `.env` or `*-creds.json` files into the repo. Always `git diff --cached` before pushing.
5. **Reduce repeat count when work is done** — Phase 2 completion check: `repeat: "1/1"` so it runs once then stops. Don't leave completed jobs running forever.
6. **Never store scripts or repos in `/tmp`** — tmpfs is wiped on container restart. Always use `/workspace/` for anything that must survive. This includes the Roadmap Autonomy Engine script (lost 1,126 lines) and any cloned repos.
7. **`verify_final.py` and similar smoke tests drift** — When refactoring class APIs (e.g., method → property, signature changes), update smoke test call sites too. Common pattern: `obj.method()` → `obj.method` (property), or positional args → keyword args.
8. **`model: null` silently kills cron jobs** — Always set `model` and `provider` explicitly. `null` causes API rejection with no clear error. Check all jobs with `last_run_at: null` and `last_error: null` — they may have never actually executed.
9. **`deliver: origin` fails without a delivery target** — Use `deliver: local` for cron jobs that don't need to push to chat. `origin` requires a resolved delivery target or fails with "no delivery target resolved".
10. **Cache dirs need explicit creation** — Scripts that write to `~/.hermes/*-cache/` dirs fail with PermissionError if the dir doesn't exist. Always `mkdir -p` + `chmod 755` before first run.

### Pydantic v2 Migration Patterns (2026-06-04)

When upgrading from Pydantic v1 to v2 (or writing new code in a v2 project), these patterns appear frequently:

1. **`class Config` → `model_config`** — Pydantic v2 replaces inner `class Config` with `model_config = ConfigDict(...)`:
   ```python
   # v1 (deprecated)
   class MyModel(BaseModel):
       class Config:
           from_attributes = True
   
   # v2 (correct)
   class MyModel(BaseModel):
       model_config = {"from_attributes": True}
   ```
   Quick fix: `grep -rn "class Config:" apps/ packages/ --include="*.py"` then replace.

2. **`max_items` → `max_length`** — `Field(max_items=N)` is deprecated in v2, use `Field(max_length=N)` for list fields.

3. **`dict()` → `model_dump()`** — `obj.dict()` is deprecated, use `obj.model_dump()`.

4. **Type mismatch in test data** — When a service signature changes (e.g., `strategy_data: List[Dict]` → `strategy_data: Dict[str, Any]`), tests passing the old type will fail with `Input should be a valid dictionary`. Check the actual service signature when tests fail with type errors.

### Protobuf Version Pinning (2026-06-04)

When using gRPC with protobuf in a Python project:

- **The error:** `Detected incompatible Protobuf Gencode/Runtime versions: gencode X.X.X runtime Y.Y.Y. Runtime version cannot be older than the linked gencode version.`
- **Cause:** `solver_pb2.py` was generated with a newer protoc than the installed `protobuf` runtime.
- **Fix:** Pin the runtime to match: `pip install "protobuf~=5.29"` (or whatever version the gencode was generated with). Check with: `python3 -c "import google.protobuf; print(google.protobuf.__version__)"`.
- **Prevention:** Add `protobuf` version constraint to `pyproject.toml` / `requirements.txt` that matches your protoc version.

### Solver Integration — Direct Path (2026-06-11)

The solver router (`apps/api/routers/solver.py`) now imports the MCCFR engine directly for synchronous solves, bypassing gRPC/Celery. This is the recommended approach for trainer-scale solves (single hand, <200 iterations):

```python
from cfr.engine import CFREngine
from games.texas_hold_em import TexasHoldEm, create_river_state
from gto_poker.deck import Deck

game = TexasHoldEm()
engine = CFREngine(game=game)
state = create_river_state(
    p0_cards=["Ah", "Kh"],
    p1_cards=["Kc", "Qc"],
    board=["Kd", "7h", "2c"],
    pot=100, stacks=[100, 100],
)
strategies = engine.solve(initial_state=state, iterations=200)
```

**Path requirements:** The FastAPI server needs `apps/solver/` on `sys.path` for `from cfr.engine import CFREngine`. From `apps/api/routers/`, this is `../../../apps/solver`. gto-poker must be pip-installed.

**Limitations:**
- `get_average_strategy()` returns action probabilities but NOT expected values (EVs are 0.0)
- The `create_river_state` function expects `List[str]` for cards, NOT `Card` objects
- Currently supports river streets only (flop/turn/preflop need more work)
- Multi-way support exists in the engine but tested separately (3-way river solve is computationally heavy)

See `devops/gto-wizard-deployment` skill's `references/solver-deployment-2026-06-11.md` for full deployment details.

### gRPC Integration Audit Findings (2026-06-14, updated 2026-06-11)

The GTO Wizard Clone has a **complete gRPC service that nobody calls**. Full integration gap analysis:

| Component | Status | Gap |
|-----------|--------|-----|
| Proto definition (`apps/solver/proto/solver.proto`) | ✅ Complete | 11 RPCs, 15 messages |
| Generated stubs (`solver_pb2.py`, `solver_pb2_grpc.py`) | ✅ Compiled | Imports work |
| gRPC server (`start_grpc_server.py`) | ✅ Runs | Health check passes |
| Service impl (`apps/solver/service.py`) | ✅ Full | All RPCs implemented |
| Celery tasks (`apps/worker/tasks.py`) | ✅ Runs | Solves without gRPC |
| Docker solver service | ⚠️ Broken | `CMD` references nonexistent `solver.service` module |
| API → gRPC client | ✅ Wired (June 11) | `/apps/api/services/solver_client.py` connects to gRPC solver server directly |
| API depends_on solver | ❌ Missing | `docker-compose.yml`: API doesn't depend on solver service |
| Frontend gRPC client | ❌ Missing | Browsers can't do native gRPC; `NEXT_PUBLIC_GRPC_URL` set but unused |
| Docker healthcheck | ❌ Missing | No healthcheck on solver container |
| `grpcio` in container | ❌ Missing | Not installed in base env; server won't start without it |

**Key Pitfall — dual solve paths:** The system has two completely separate paths for solving:
1. **REST/Celery path:** API → `submit_solve` Celery task → solver engine (works, tested)
2. **gRPC path:** gRPC server → `SolverServicer.SubmitSolve` → same engine (works standalone, never called)
3. **Direct import path (simplest for trainer):** FastAPI router imports solver directly, no Celery/gRPC overhead

For trainer-scale solves (single hand, 25-50 iterations), direct import is the fastest path — no serialization overhead, no worker queue. See `gto-wizard-clone` skill's `references/solver-trainer-integration.md` for the confirmed approach.

These paths should be consolidated. Options:
- **(a) Direct import for real-time, Celery for batch:** Trainer uses direct import for instant feedback; range views and complex solves use Celery
- **(b) gRPC-only:** API becomes gRPC client, drop Celery for solves
- **(c) Celery-only:** Remove gRPC server, Celery already handles async solves

**Key Pitfall — Dockerfile CMD vs actual entrypoint:** The Dockerfile says `CMD ["python", "-m", "solver.service"]` but there is no `solver/__main__.py`. The actual entrypoint is `apps/solver/start_grpc_server.py`. Docker Compose needs `command: python start_grpc_server.py --port 50051` to override. There's also a second `server.py` with hardcoded `/tmp/gto-wizard-clone` paths that shouldn't be used.

**Key Pitfall — grpcio not in base environment:** The `grpcio` pip package isn't installed in the default container/server environment. The gRPC server imports fail with `ModuleNotFoundError: No module named 'grpc'`. Must `pip install grpcio grpcio-tools` or add to `requirements.txt`.

**Verified working (2026-06-14):**
```python
# Direct import and instantiation works after pip install grpcio
import sys
sys.path.insert(0,'apps/solver')
sys.path.insert(0,'apps/solver/proto') 
sys.path.insert(0,'packages/poker-core/src')
from service import SolverServicer  # ✅ Works
# gRPC server starts on ephemeral port, health check returns healthy=True
# Redis unavailable (expected), strategy_storage works, celery imports OK
```

### Next.js / React 19 / Shadcn UI Build Pitfalls (2026-06-01)

These patterns emerge when building Next.js 15 + React 19 + Shadcn UI apps (like the GTO Wizard clone). Check for these when `next build` fails with type errors:

1. **`HeadingAttributes` removed in React 19** — shadcn/ui `card.tsx` imports it from `'react'`. If React 19 is used, remove the import (it was unused anyway). Check: `grep -rn "HeadingAttributes" src/`.
2. **`<Button ghost>` → `<Button variant="ghost">`** — Shadcn UI `Button` uses `variant` prop, not a boolean `ghost` prop. The `ghost` variant value exists but must be passed as `variant="ghost"`. Check: `grep -rn "ghost" src/ --include="*.tsx"`.
3. **`window.__HERMES_SESSION_TOKEN__` in non-Hermes apps** — Leftover from copying Hermes-Agent UI code. Replace with `process.env.NEXT_PUBLIC_API_TOKEN` or remove entirely. Check: `grep -rn "__HERMES" src/`.
4. **Strict TS cast: `SomeType as Record<string, unknown>`** — TypeScript 5.7+ rejects direct casts between non-overlapping types. Use `as unknown as Record<string, unknown>` as intermediate. Check: `grep -rn "as Record<string, unknown>" src/ --include="*.tsx"`.
5. **Barrel index duplicate type exports** — When two modules export the same type name (e.g., `HHCard` from both `HandViewer` and `HandPlayback`), the barrel `index.ts` must import from only one. Remove the duplicate `export type { X } from './Module2'` if `X` already exported from `Module1`.
6. **`QuizSocket` / socket type exports** — If a hook imports `QuizSocket` as a type from a socket module but the module only exports `quizSocket` (value), add an explicit type export: `export type QuizSocket = ReturnType<typeof SocketClient.getQuizSocket>`.
7. **`critters` missing for Next.js 15 `optimizeCss`** — `next build` fails with `Cannot find module 'critters'`. Fix: `npm install critters`. Already in `package.json` deps but may be missing from `node_modules` if install was incomplete. Add to `devDependencies` if not present: `npm install -D critters`.
8. **Data possibly undefined in comparison renderers** — When a variable is used conditionally (e.g., `{isComparisonMode && comparisonData && (<span data.action .../>)}`), ensure `data` is also guarded: `{isComparisonMode && comparisonData && data && (...)}`.
9. **`StrategyHeatmap.tsx` RANKS `as const` cast** — When using `indexOf` on a `const` array like `RANKS`, TypeScript narrows the return type. Cast the input: `RANKS.indexOf(currentHand[0] as typeof RANKS[number])` instead of `RANKS.indexOf(currentHand[0])`.
10. **`sw.js` build artifact mismatch** — Next.js generates `sw.js` with a build hash. If the working tree has a stale `sw.js` from a previous build, it causes a hash mismatch. Clean before rebuild: `rm -rf .next apps/web/.next apps/web/sw.js`.

**Quick diagnostic:** When `next build` fails, collect all unique errors first: `npx next build 2>&1 | grep "Type error:" | sort -u`. Fix all unique patterns, then rebuild once.

### References (ChonSong Repo)

- `references/double-board-plomd` — double board PLO rules and implementation notes
- `references/poker-platform-stackmd` — domain knowledge from repo-init skill
- `references/build-fixes-2026-06-04.md` — API test fixes, Pydantic v2 migration, protobuf pinning, package.json merge
- `references/database-seeding.md` — SQLite seeding: dual-Base problem, pitfalls, running seed_all.py

## Database Seeding

The GTO Wizard Clone uses SQLite (via `aiosqlite`) as the local dev database, with SQLAlchemy async ORM. The project has **two separate `declarative_base()` instances** that must both be handled when creating tables or seeding.

### Dual Base Problem

```python
# Base 1 — used by quiz_models.py, hh_models.py
from apps.api.services.database import Base as MainBase

# Base 2 — used by course_models.py, spots.py, services/models.py  
from apps.api.services.models import Base as StrategyBase
```

`MainBase.metadata.create_all()` only creates tables for models registered with `MainBase`. `StrategyBase` has its own metadata. **Both must be created.**

### DB Path

The SQLite DB path is computed in `database.py` relative to `__file__`:
```python
_sqlite_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "gto_wizard.db")
# Resolves to: /workspace/gto_wizard.db (NOT inside the clone dir)
```

### Seeding Script

A unified seeder exists at `/workspace/gto-wizard-clone/seed_all.py`. Run with:
```bash
cd /workspace/gto-wizard-clone && python3 seed_all.py
```

It seeds:
1. **Quiz spots** (60 spots across 25+ categories × 3 difficulties)
2. **Training courses** (3 courses × 8 lessons = 24 lessons)
3. **Push/fold strategy data** (18 entries: Nash charts for 5 positions × 5 stack depths + 3 ICM bubble ranges)

The seeder is idempotent — it checks existing counts and skips if already populated.

### Known Pitfalls

1. **`index=True` + explicit `Index()` on same column** — SQLAlchemy creates the auto-named index from `index=True`, then the explicit `Index()` tries to create again with the same name → `OperationalError: index already exists`. Fix: remove `index=True` from the column if an explicit `Index()` is defined. The `QuizSpot.street` column had this bug (fixed).

2. **`Base.metadata.drop_all` doesn't drop indexes in SQLite** — After `drop_all`, orphan indexes may persist. Use `checkfirst=True` on `create_all`, or delete the `.db` file entirely.

3. **Engine singleton caching** — `database.py` caches `_engine` globally. If you delete the `.db` file, reset the singleton:
   ```python
   import apps.api.services.database as db_mod
   db_mod._engine = None
   db_mod._session_factory = None
   ```

4. **`strategy_data` column type** — The `Strategy` model uses `JSON` column. When inserting, pass a dict (SQLAlchemy handles serialization). Querying returns a dict (or string if using raw SQL — use `json.loads()`).

### Schema Changes

When adding new models or columns:
1. Update the model file
2. Delete the old `.db` file (SQLite has limited `ALTER TABLE` support)
3. Re-run `seed_all.py` to recreate and re-seed

## Export Functionality

The platform provides export capabilities across multiple pages. All PNG exports use the Canvas API directly — no external dependencies (no html2canvas).

### Shared Utilities

- `apps/web/src/lib/exportUtils.ts` — Core export functions:
  - `renderGridToPNG(grid, filename, opts)` — Renders a 13×13 grid (strategy/equity heatmap) to PNG
  - `renderBarChartToPNG(data, filename, opts)` — Renders a bar chart (leak analysis) to PNG
  - `renderEquityChartToPNG(data, filename, opts)` — Renders stacked equity bars to PNG
  - `downloadBlob(blob, filename)` — Triggers a browser download from a Blob
  - `downloadFromApi(url, filename)` — Triggers download from an API endpoint
  - `timestampedFilename(prefix, ext)` — Generates `prefix_YYYY-MM-DD_HHMMSS.ext`

- `apps/web/src/components/ui/ExportButton.tsx` — Reusable dropdown export button:
  - Single option: direct click, no dropdown
  - Multiple options: dropdown menu with labels + descriptions
  - Props: `options`, `label`, `size`, `variant`, `className`

### Page-Specific Exports

| Page | PNG | CSV | Notes |
|------|-----|-----|-------|
| `/strategies` | ✅ Strategy heatmap (13×13 grid via `renderGridToPNG`) | ✅ Strategy data (hand, action, frequency, EV) | CSV uses poker hand ordering (pairs first, then suited, then offsuit) |
| `/equity` | ✅ Equity line chart (SVG→Canvas→PNG) | ✅ Equity by street | SVG element needs `id` attribute for export targeting |
| `/analyze/hands` | — | ✅ Via `GET /api/v1/hh/export` | Frontend calls backend API; falls back to client-side export if API unreachable |
| `/analyze/leaks` | ✅ Leak bar chart via `renderBarChartToPNG` | ✅ Leak data (category, amount, expected, delta) | Uses `LeakChartWithExport` wrapper |

### Backend CSV Export

`GET /api/v1/hh/export` in `apps/api/routers/hh.py`:
- Properly serializes JSONB columns: `stakes` → `sb/bb`, `winners` → `player: amount; ...`, `players` → `name (seat N: stack)`, `board` → space-joined cards
- Null-safe access on all columns with proper formatting (`pot` → 2 decimals, `ev_loss` → 4 decimals)
- Supports filters: `site`, `date_from`, `date_to`, `board_texture`, `spot_category`, `pot_min`, `pot_max`, `limit`
- Returns `Content-Disposition: attachment; filename=hand_history_export_YYYYMMDD_HHMMSS.csv`

### Pattern: Adding Export to a New Chart Component

1. Import `ExportButton` and the relevant `render*ToPNG` function
2. Create a wrapper component that wraps the chart with `<div>` and places `<ExportButton>` in the header area
3. For SVG-based charts (recharts): assign an `id` to the `<svg>` element, use `XMLSerializer` → `Image` → `canvas` → `toBlob`
4. For canvas-based exports: call `renderGridToPNG(grid, filename, opts)` with grid data derived from the component's data
5. For CSV: build header + rows array, join with commas, wrap in quotes, create Blob, trigger download

## Celery Worker Architecture (2026-07)

### shared_task vs app.task — Circular Import Pattern

When `celery_app.py` uses `include=["tasks"]` and `tasks.py` imports from `celery_app.py`, there's a circular dependency. The fix:

```python
# celery_app.py
celery_app = Celery("gto_solver", broker=..., backend=...)
app = celery_app  # alias

# tasks.py — use shared_task, NOT app.task
from celery import shared_task

@shared_task(bind=True, name="solver.solve_spot", queue="solver",
           max_retries=2, default_retry_delay=10)
def solve_spot(self, params):
    ...

# Only import celery_app lazily where send_task() is needed
def submit_solve(params):
    from apps.worker.celery_app import celery_app  # lazy import
    celery_app.send_task("solver.solve_spot", args=[params])
```

**Rule:** Use `@shared_task` for all task decorators. Never `from celery_app import app` at module level in tasks.py. Import `celery_app` lazily inside functions that need `send_task()`.

### Multi-Queue Task Routing

Route heavy solver jobs to dedicated queues:

```python
# celery_app.py
task_routes = {
    "solver.*": {"queue": "solver"},      # CFR solves (CPU-heavy)
    "analysis.*": {"queue": "analysis"},   # Batch HH import, leak detection
    "maintenance.*": {"queue": "default"}, # Cleanup, status checks
}
```

Worker command: `celery -A app worker -Q solver,analysis,default --concurrency=4`

### Redis → WebSocket Progress Bridge

Pattern for streaming Celery task progress to browser clients:

1. Worker publishes progress to Redis channel `solver:progress:{job_id}`
2. API subscribes via `RedisService.psubscribe("solver:progress:*")`
3. `ProgressBridge` forwards messages to `WebSocketManager.broadcast_to_job()`

```python
# progress_bridge.py
class ProgressBridge:
    _instance = None
    _lock = threading.Lock()  # MUST be class-level, not in __init__

    @classmethod
    def register(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            if not cls._instance._running:
                cls._instance.start()
            return cls._instance

    def start(self):
        self._redis_service.subscribe_to_progress(
            job_id="*",  # wildcard = pattern subscribe
            callback=self._on_progress,
        )

    def _on_progress(self, data):
        job_id = data.get("job_id")
        if not job_id:
            return
        if not self._loop:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                return
        asyncio.run_coroutine_threadsafe(
            self._ws_manager.handle_solver_progress(job_id, data),
            self._loop,
        )
```

**Key gotcha:** `subscribe_to_progress(job_id="*")` must use `psubscribe` (pattern subscribe), not `subscribe`. The listener must handle both `message` and `pmessage` types.

### RedisService Pattern Subscription

```python
# redis_service.py
def subscribe_to_progress(self, job_id, callback):
    if job_id == "*":
        channel = f"{self.PROGRESS_CHANNEL_PREFIX}*"  # pattern
    else:
        channel = self.get_progress_channel(job_id)  # exact
    self._subscriptions[channel] = callback
    if not self._running:
        self._start_listener()

def _listen_for_updates(self):
    pubsub = self.pubsub_client.pubsub()
    patterns = [ch for ch in self._subscriptions if ch.endswith("*")]
    exact = [ch for ch in self._subscriptions if not ch.endswith("*")]
    if exact:
        pubsub.subscribe(*exact)
    if patterns:
        pubsub.psubscribe(*patterns)
    for message in pubsub.listen():
        if message["type"] in ("message", "pmessage"):
            channel = message.get("channel") or message.get("pattern")
            # ... dispatch to callback
```

### Worker Dockerfile — Multi-Queue Setup

```dockerfile
FROM python:3.12-slim
# Install monorepo packages first
COPY packages/poker-core ./packages/poker-core
RUN pip install -e ./packages/poker-core
COPY apps/solver ./apps/solver
RUN pip install -e ./apps/solver
COPY apps/api ./apps/api
COPY apps/worker/ ./apps/worker/
# Worker listens on all queues
CMD ["celery", "-A", "apps.worker.celery_app", "worker",
     "--loglevel=info", "--concurrency=4",
     "-Q", "solver,analysis,default"]
```

### Beat Scheduler for Periodic Cleanup

```python
# celery_app.py
beat_schedule = {
    "cleanup-expired-jobs": {
        "task": "maintenance.cleanup_expired_jobs",
        "schedule": crontab(hour=3, minute=0),  # 3 AM UTC daily
    },
}
```

Run as separate service: `celery -A app beat --loglevel=info`

### Retry/Backoff Pattern for Long-Running Tasks

```python
@shared_task(bind=True, name="solver.solve_spot", queue="solver",
           max_retries=2, default_retry_delay=10)
def solve_spot(self, params):
    try:
        # ... do work ...
    except SoftTimeLimitExceeded:
        retry_params = dict(params)
        retry_params["iterations"] = max(100, iterations // 2)
        if self.request.retries < self.max_retries:
            raise self.retry(args=[retry_params])
        raise
```

On retry, halve the iteration count. After max retries, let it fail.

### Variant Task Registration Pattern

Each variant gets its own task name for explicit routing:

| Task | Queue | Purpose |
|------|-------|---------|
| `solver.solve_spot` | solver | NLH river/flop/turn CFR |
| `solver.solve_flop_spot` | solver | Explicit flop street |
| `solver.solve_turn_spot` | solver | Explicit turn street |
| `solver.solve_plo4_spot` | solver | PLO4 CFR with PLO4Evaluator |
| `solver.solve_omaha_spot` | solver | Omaha Hi/Lo |
| `solver.solve_shortdeck_spot` | solver | Shortdeck (6+ Hold'em) |
| `solver.solve_double_board_equity` | solver | Double Board PLO MC |
| `solver.solve_bomb_pot_equity` | solver | Bomb Pot MC equity |
| `solver.compute_push_fold_chart` | solver | Nash push/fold generation |
| `solver.submit_solve` | default | Task router/dispatcher |
| `solver.get_job_status` | default | Status polling |
| `analysis.batch_import_hands` | analysis | Batch HH import |
| `analysis.analyze_leaks` | analysis | Batch leak detection |
| `analysis.compute_icm_batch` | analysis | Batch ICM calculation |
| `maintenance.cleanup_expired_jobs` | default | Daily Redis cleanup |

### API Endpoints for Variant Solving

```
POST /api/v1/solver/solve              → NLH (auto-detect street)
POST /api/v1/solver/solve/double-board → Double Board PLO
POST /api/v1/solver/solve/bomb-pot     → Bomb Pot
POST /api/v1/solver/solve/plo4         → PLO4
POST /api/v1/solver/analysis/import-hands     → Batch HH import
POST /api/v1/solver/analysis/leaks            → Batch leak analysis
POST /api/v1/solver/analysis/push-fold-chart  → Push/fold chart gen
```

### Strategy Storage — Thread-Safe Async in Celery

Never create a new `asyncio.EventLoop()` in Celery's main thread (deadlocks with prefork). Use `ThreadPoolExecutor`:

```python
import concurrent.futures, asyncio

def store_strategy_if_available(...):
    def _store():
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(storage.store_strategy(...))
        finally:
            loop.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_store)
        future.result(timeout=30)
```

## General GTO Platform Knowledge

### Open-Source Library Stack

See `references/poker-platform-stack.md` in `repo-init` skill for full open-source library catalog.
> See `references/gto-wizard-clone.md` in `autonomous-cron-pipeline` skill for the actual GTO Wizard Clone execution log (2026-05-25, job IDs, repo structure).
> See `references/deployment-architecture-2026-08.md` for the two-frontends problem and correct deployment setup.
See `references/python-cpu-services.md` in `docker-patterns` skill for Numba JIT patterns and gRPC service structure.