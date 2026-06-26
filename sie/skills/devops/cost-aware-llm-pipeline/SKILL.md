---
name: cost-aware-llm-pipeline
description: Cost optimization for LLM API usage — model routing by task complexity, budget tracking, retry logic, and prompt caching. Extends multi-provider-llm-backoff.
origin: ECC (adapted for Hermes)
---

# Cost-Aware LLM Pipeline

Patterns for controlling LLM API costs while maintaining quality. Extends `multi-provider-llm-backoff` with cost tracking and model routing.

## When to Activate

- Building applications that call LLM APIs
- Processing batches of items with varying complexity
- Need to stay within a budget for API spend
- Optimizing cost without sacrificing quality on complex tasks

## Model Routing by Task Complexity

Automatically select cheaper models for simple tasks, reserving expensive models for complex ones.

```python
# Tier 1: Simple tasks (summarization, classification, formatting)
# Use: MiniMax-M2.7, Haiku, or cheapest available
# Cost: ~$0.01-0.10/1M tokens

# Tier 2: Medium tasks (code review, analysis, translation)
# Use: Claude Sonnet, GPT-4o-mini
# Cost: ~$0.10-1.00/1M tokens

# Tier 3: Complex tasks (architecture, reasoning, creative)
# Use: Claude Opus, GPT-4o, Qwen3.6-plus
# Cost: ~$1.00-15.00/1M tokens
```

### Routing Decision

| Signal | Route To |
|--------|----------|
| Task < 10K chars, simple transformation | Tier 1 (cheapest) |
| Task 10K-50K chars, analysis needed | Tier 2 (balanced) |
| Task > 50K chars, complex reasoning | Tier 3 (strongest) |
| Batch processing > 100 items | Tier 1 with quality sampling |
| Vision/image analysis | Tier 2+ with vision capability |
| Code generation | Tier 2+ (code-optimized models) |

## Budget Tracking

Track cumulative spend per task/session:
- Log model, input tokens, output tokens, cost per call
- Set budget limits per task type
- Alert when approaching budget threshold

## Retry Logic

- Narrow retry: same model, different prompt
- Model fallback: try cheaper model if expensive fails
- Budget guard: stop if cost exceeds threshold

## Prompt Caching

- Cache expensive prompt results by content hash
- Use SHA-256 of (model + prompt) as cache key
- TTL: 24h for docs, 1h for dynamic data
- Store in `/opt/data/cache/llm-responses/`

## Hermes Adaptation

- Use `multi-provider-api-calls` skill for actual API calls
- Current setup: MiniMax-M2.7 (default), Qwen3.6-plus (vision), OpenRouter fallback
- Budget awareness: track token usage per session
- For batch tasks (repo-transmite migrations): use cheapest model that meets quality bar
- For critical tasks (code review, architecture): use strongest available model
