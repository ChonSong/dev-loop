# agent-qa (vostride/agent-qa) Comparison

## What agent-qa IS

An npm package (`npm install -D agent-qa`) — a **self-improving test harness** that runs YAML-based natural-language tests via an LLM-powered agent. Tests are written as declarative steps in plain English; the agent resolves selectors and execution paths at runtime.

Repo: https://github.com/vostride/agent-qa  
Docs: https://vostride.com/docs/agent-qa  
Latest: v0.1.21 (June 2026), ~50 packages (core, cli, web, mobile, android, ios, dashboard, mcp, cache, memory, hooks, parser, id generation, auth, provider connectors)

**Architecture:** pnpm monorepo, Node.js >= 24, Turbo build. Core engine has:
- `packages/core/src/agent/` — LLM agent that plans and executes test steps
- `packages/core/src/memory/` — SQLite-backed execution memory
- `packages/core/src/cache/` — action plan cache (reuses validated plans)
- `packages/core/src/parser/` — YAML test parser
- `packages/core/src/hooks/` — sandboxed Docker hook runner
- `packages/core/src/suite/` — test suite orchestration
- `packages/mcp/` — MCP server for coding agent integration
- `packages/dashboard-server/` + `packages/dashboard-ui/` — web dashboard

## Key Differentiators

| Feature | agent-qa | Our Setup |
|---|---|---|
| Test format | Natural-language YAML | TypeScript Playwright specs |
| Execution | LLM agent resolves selectors/actions at runtime | Static `page.click()` selectors |
| Healing | Re-observes UI on failure, tries alternative path | Fails hard on selector drift |
| Memory | SQLite — past executions inform future runs | Checkpoint spec_gaps (bug tracking only) |
| Cache | Reuses validated action plans | Runs fresh every cycle |
| Sandboxed hooks | Docker-contained setup/teardown scripts | Not present |
| Dashboard | Web UI for results | Terminal output |

## What Each Catches That The Other Misses

### agent-qa catches (we miss):
- **UI drift** — a button's aria-label changed? agent-qa re-discovers it; our Playwright test fails
- **Flaky timing** — page loads slow? agent-qa waits and retries; our test times out
- **Session-specific state** — logged-in vs anonymous differences? agent-qa adapts

### We catch (agent-qa misses):
- **Semantic correctness** — frequencies sum to 325% instead of 100%? Our POM asserts the sum; agent-qa validates the YAML says "clicked button" not "math is right"
- **Reference drift** — clone diverged from the original? Our Coach compares side-by-side; agent-qa has no concept of a reference app
- **Methodology failures** — test was written in the same session as the feature? Our Step 2.5 classifies this; agent-qa has no such gate
- **Console errors** — JS exceptions and unhandled rejections? Our audit spec catches them; agent-qa's healing can mask the underlying error
- **Canvas/Phaser rendering** — wrong tribe starts, units render incorrectly? DOM-based tools can't see inside canvas

## Hybrid Architecture Proposal

```
[Deploy] → agent-qa YAML smoke tests (self-healing regression)
     ↓
[CI] → Playwright POM specs (deep semantic assertions, console audit)
     ↓
[Review] → Coach (reference-based browser comparison + methodology gate)
```

- **agent-qa** for regression detection (survives UI drift, low maintenance)
- **POM specs** for gated assertions (frequencies, range comparison, error-free console)
- **Coach** as the final source of truth (reference comparison, methodology classification, backlog generation)

When considering adding agent-qa, the friction points are:
- Node >= 24 requirement (check host version)
- Docker required for hooks (already have Docker)
- It's an additional test system to maintain alongside Playwright
- agent-qa's test results are only as good as the YAML expectation — garbage in, garbage out
