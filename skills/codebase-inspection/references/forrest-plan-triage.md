# Triage Example: Forrest Plan & Track

> **Repo:** `ChonSong/forrest-plan-and-track`
> **Session:** 2026-06-09
> **Context:** User asked to "review forrest-plan-and-track repo and advise next steps"

## The Multi-Source Discovery in Practice

Here's exactly how the triage protocol played out step by step.

### 1. Check Local Clone

```bash
find /home /workspace -maxdepth 4 -name ".git" -path "*/forrest*" 2>/dev/null
# → NOT FOUND
```

Correction: the original session had found this at `/home/sean/workspace/forrest-plan-and-track/` but subsequent workspace reorganization had moved/archived it. The repo no longer had a local clone accessible in the container.

### 2. Check Archived Copies

```bash
# Found at /workspace/archive/forrest-plan-and-track/
# But only contained streamlit_onetag/ (git remote pointed to hermes-knowledge-graph, not this repo)
```

Lesson: archived copies may be partial or belong to a different repo. The git remote told the real story.

### 3. Fetch GitHub API

```bash
curl -sL "https://api.github.com/repos/ChonSong/forrest-plan-and-track/contents"
# → Returns full directory listing: 10 root files, 7 directories
```

The repo was alive on GitHub even though not cloned locally. Contents:
- Root: README.md, PLAN.md, FORREST-MODEL.md, SCENARIO.md, DEMO.md, PROGRESS.md, package.json, prisma.config.ts, .gitignore
- Dirs: daily-logs, diagrams, experiments, notes, prisma, scripts, streamlit_onetag

### 4. Search Session History

```bash
session_search(query="forrest plan track repo")
# → 3 sessions found:
```

Key discoveries from past sessions:
- Session 1 (June 1): Repo created, Day 0 logged, 2 blockers identified (repo URL + API key)
- Session 2 (June 8): Streamlit dashboard restored, auth proxy configured, but SQL Server password wrong and Cloudflare tunnel broken
- Session 3 (June 2): SQL Server container `sqlserver-onetag` started, .bak file being restored, schema extracted

### 5. Check Running Services

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8502/
# → Both return 000 (not responding)
```

None of the previously-running services (Streamlit dashboard, auth proxy, SQL Server) were still up.

### 6. Compare Against Original Plan

From `PROGRESS.md`: All phases beyond Day 0 marked "⬜ Not started."
From `PLAN.md`: Mission timeline was June 1-14. Current date: June 9.
**Slippage:** 9 days into a 14-day sprint, 0 experiments run.

### 7. Check External Dependencies

From `PROGRESS.md` blockers:
- Forrest repo URL (`<org>`) — 🔴 Blocking Day 1
- Anthropic API key — 🔴 Blocking Day 1

Neither was ever resolved. The original engine design (Claude proposing mutations) couldn't execute.

## The Capability-Constrained Reframe

**Original design:** Forrest = autonomous Claude-driven Monte Carlo loop over synthetic project scheduling scenario. Requires API key + external engine repo.

**What was actually available:**
- Full OneTag HMAS schema (80+ tables, 248 FK, in Prisma format)
- Functional Streamlit dashboard (2K lines, plotly viz, auth wrapper)
- Detailed schema analysis from .bak binary extraction
- The repo's experiment-tracking framework (Scenario → Run → Experiment → Finding)

**Reframed design:** Forrest = deterministic data analysis engine over OneTag HMAS data. Replace "Propose→Simulate→Score" with "Query→Analyze→Rank." The dashboard becomes the findings output surface.

**Files changed by the reframe:**
- `FORREST-MODEL.md` — Rewrite to describe data analysis engine
- `SCENARIO.md` — Replace project scheduling with OneTag HMAS domain
- `PLAN.md` / `PROGRESS.md` — Reset timeline, update phases
- `engine/` — New Python analysis modules (new directory)
- `streamlit_onetag/app.py` — Add findings page

## Key Lesson

When a plan assumes resources that don't exist, the first question isn't "can we get those resources?" — it's "what core methodology is the plan trying to execute, and can we execute it with what we actually have?" In this case, the methodology (structured experimentation → scored findings) was intact; only the Claude-driven simulation implementation was blocked.
