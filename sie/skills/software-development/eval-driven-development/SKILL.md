---
name: eval-driven-development
description: "Add promptfoo-based eval gates to a project's CI pipeline — LLM evaluation as a quality gate on every PR. Covers config creation, provider wiring, GitHub Actions integration, red-team security scanning, and regression tracking."
version: 1.0.0
tags:
  - eval
  - testing
  - ci
  - promptfoo
  - llm
  - quality-gate
related_skills:
  - test-driven-development
  - ci-cd
  - e2e-testing
  - multi-provider-api-calls
  - repo-init
---

# Eval-Driven Development (promptfoo CI Integration)

Add automated LLM evaluation as a CI quality gate using promptfoo — a CLI framework for testing prompts, models, and assertions. Runs alongside the project's existing test suite but tests LLM output quality rather than code correctness.

## When to Use

- A project has LLM-dependent features (prompts, agents, RAG pipelines)
- You need to track model quality regressions across PRs
- You want side-by-side model comparisons (deepseek-v4-flash vs alternatives)
- You need scheduled security scanning (prompt injection, PII leakage)
- The project already has a CI pipeline or is about to get one
- You're iterating on prompts and want to know when a change regresses

## Architecture

```
GitHub PR → promptfoo eval → quality gate (fail CI on assertions) → PR comment with results
              ↕
         LLM API(s)
         (deepseek, openai, anthropic, etc.)
```

promptfoo is a Node.js CLI tool that:
- Accepts a YAML config with prompts, providers, and test cases
- Runs every prompt × every provider × every test case as a matrix
- Checks assertions (contains, regex, llm-rubric, cost, latency)
- Outputs JSON, HTML, JUnit XML for CI consumption

## Setup Steps

### 1. Create the Config Files

**Minimal config** (`promptfooconfig.yaml`):

```yaml
prompts:
  - id: code-gen
    label: Code Generation
    raw: |
      You are an expert developer.
      {{prompt}}

providers:
  - id: openai:chat:deepseek-v4-flash
    label: deepseek-v4-flash
    config:
      apiBaseUrl: https://opencode.ai/zen/go/v1
      apiKeyEnvar: OPENCODE_GO_API_KEY

tests:
  - description: "Task A — Rate Limiter"
    vars:
      prompt: "Implement a token bucket rate limiter..."
    assert:
      - type: contains
        value: "class TokenBucketLimiter"
      - type: llm-rubric
        value: "Code must use time.monotonic() and threading.Lock"
      - type: cost
        threshold: 0.01
      - type: latency
        threshold: 30000
```

**Provider configuration** — OpenAI-compatible endpoints work with just `apiBaseUrl` + `apiKeyEnvar`:

```yaml
providers:
  # Direct provider (DeepSeek via OpenCode Go)
  - id: openai:chat:deepseek-v4-flash
    label: deepseek-v4-flash
    config:
      apiBaseUrl: https://opencode.ai/zen/go/v1
      apiKeyEnvar: OPENCODE_GO_API_KEY
      temperature: 0.3

  # OpenAI
  - id: openai:chat:gpt-5.4
    label: gpt-5.4
    config:
      apiKeyEnvar: OPENAI_API_KEY
      temperature: 0.3

  # Anthropic (native format)
  - id: anthropic:messages:claude-sonnet-4-20250514
    label: claude-sonnet-4
    config:
      apiKeyEnvar: ANTHROPIC_API_KEY
```

### 2. Create the CI Workflow

`.github/workflows/promptfoo-eval.yml`:

```yaml
name: promptfoo Eval

on:
  pull_request:
    paths:
      - 'promptfooconfig.yaml'
      - 'prompts/**'
  push:
    branches: [main]
    paths:
      - 'promptfooconfig.yaml'
      - 'prompts/**'
  schedule:
    - cron: '0 6 * * 1'   # Weekly Monday 6AM UTC
  workflow_dispatch:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - name: Cache LLM responses
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/promptfoo
            .promptfoo-cache
          key: promptfoo-${{ hashFiles('promptfooconfig.yaml') }}-${{ github.sha }}
          restore-keys: promptfoo-${{ hashFiles('promptfooconfig.yaml') }}-
      - name: Run promptfoo eval
        id: eval
        continue-on-error: true
        env:
          OPENCODE_GO_API_KEY: ${{ secrets.OPENCODE_GO_API_KEY }}
        run: |
          npx promptfoo@latest eval \
            -c promptfooconfig.yaml \
            --share \
            --output results.json \
            --output report.html \
            --output results.junit.xml
      - name: Quality Gate
        run: |
          FAILURES=$(jq '.results.stats.failures // 0' results.json)
          if [ "$FAILURES" -gt 0 ]; then
            echo "❌ Quality gate FAILED: $FAILURES test(s) failed"
            exit 1
          fi
          echo "✅ All tests passed!"
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: promptfoo-results
          path: |
            results.json
            report.html
            results.junit.xml
```

### 3. Add GitHub Secrets

The repo needs API key secrets corresponding to the `apiKeyEnvar` values in the config:

| Secret | Config Envar | Source |
|--------|-------------|--------|
| `OPENCODE_GO_API_KEY` | `OPENCODE_GO_API_KEY` | OpenCode Go, from ~/.hermes/.env |
| `OPENAI_API_KEY` | `OPENAI_API_KEY` | OpenAI dashboard |
| `DEEPSEEK_API_KEY` | `DEEPSEEK_API_KEY` | DeepSeek platform |
| `ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY` | Anthropic console |

Add via REST API (libsodium sealed box encryption, see template `templates/add-github-secret.py`) or GitHub UI.

### 4. Configure Red-Team Security Scanning

`redteam.yaml` — standalone config for scheduled security scans:

```yaml
prompts:
  - "You are a helpful assistant. Respond to the user's request."

targets:
  - id: openai:chat:deepseek-v4-flash
    label: DeepSeek V4 Flash
    config:
      apiBaseUrl: https://opencode.ai/zen/go/v1
      apiKeyEnvar: OPENCODE_GO_API_KEY

redteam:
  plugins:
    - owasp:llm:01        # Prompt injection
    - owasp:llm:02        # Sensitive info disclosure
    - jailbreak
    - harmful:privacy
    - pii:direct
    - excessive-agency
    - hallucination
  strategies:
    - basic
    - base64
    - jailbreak
    - leetspeak
  numTests: 5
  passThreshold: 0.8
```

Run: `npx promptfoo@latest redteam run -c redteam.yaml`

### 5. Verify Locally

```bash
# One-shot run (auto-downloads promptfoo)
npx promptfoo@latest eval -c promptfooconfig.yaml

# View results in browser
npx promptfoo@latest view

# Run security scan
npx promptfoo@latest redteam run -c redteam.yaml
```

No global install needed — `npx` handles it.

## Promptfoo vs a Custom Benchmark Platform

| Aspect | promptfoo | Custom Platform (e.g. llm-benchmark-platform) |
|--------|-----------|----------------------------------------------|
| Purpose | Fast iteration, CI gating, model comparison | Deep scoring, persistent history, custom dashboards |
| Test storage | YAML configs, git-tracked | Database (SQLite, Postgres) |
| CI integration | First-class (GitHub Action, JUnit) | None (would need building) |
| Scoring | Assertion system (contains, llm-rubric, cost, latency) | Proprietary scoring engine, code analysis |
| Red teaming | 50+ attack plugins | None built-in |
| Overhead | Runs on npx, no Docker needed | Docker + backend + database |

**Sweet spot:** promptfoo as the fast-iteration/CI layer + custom platform as the persistent backend. They are complementary, not overlapping.

## Pitfalls

- **API key availability** — promptfoo needs access to LLM APIs. If the key isn't available in CI, all tests fail. Use `continue-on-error: true` on the eval step to keep the CI green even when the eval can't run (e.g., fork PRs without secrets).
- **Caching is critical** — Without caching, every CI run re-queries the LLM, costing money and taking minutes. Always cache `~/.cache/promptfoo` and `.promptfoo-cache`.
- **Cost management** — A typical run with 3 test cases × 1 model × 1 prompt × 3 assertions = ~$0.02-0.03. Large suites with red-teaming can cost much more. Use caching and limit to essential tests.
- **Provider compatibility** — Only OpenAI-compatible endpoints work with `openai:chat:` prefix. For Anthropic, use `anthropic:messages:`. For anything else, check promptfoo docs for the correct provider ID.
- **Test stability** — LLM outputs are non-deterministic. Use `llm-rubric` assertions for qualitative checks (they re-query the LLM to judge) and `contains`/`cost`/`latency` for quantitative checks. Avoid overly strict exact-match assertions.
- **Red-teaming is slow** — Each plugin × strategy combination makes an API call. A full red-team run with 7 plugins × 5 strategies × 5 tests = 175+ API calls. Run it on a schedule (weekly), not on every PR.
