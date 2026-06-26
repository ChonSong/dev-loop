# OpenCode Zen Model Selection for Structured JSON Output

Tested 2026-06-26 against the `https://opencode.ai/zen/v1` endpoint.
All models require a valid OpenCode Zen API key from `~/.hermes/.env`.

## Summary

| Tier | Model | Speed | JSON Quality | Verdict |
|------|-------|-------|-------------|---------|
| ✅ Best | `nemotron-3-ultra-free` | 15-22s | ✓ correct aria-labels, handles complex prompts | Recommended default |
| ✅ Fast | `north-mini-code-free` | 2-6s | ~ simple clicks only, fails on complex JSON | Use for simple actions only |
| ❌ | `mimo-v2.5-free` (old default) | varies | ✗ returns `{}` ~30-40% of calls | Replaced by nemotron |
| ❌ | `deepseek-v4-flash-free` | 12s | ✗ thinking mode, returns empty string | Won't work |
| ❌ | `big-pickle` / `deepseek-v4-flash` | — | ✗ thinking mode, no tool_choice | Won't work |
| ❌ | `qwen3.6-plus-free` | — | ✗ API error | Not available |
| ❌ | `minimax-m3-free` | — | ✗ API error | Not available |
| ❌ | All GPT/Claude/Gemini paid models | — | ✗ "Insufficient balance" on this account | Not available |

## Why Nemotron Wins

`nemotron-3-ultra-free` (NVIDIA's Nemotron 3 Ultra) consistently produces:
- Full aria-label selectors: `[aria-label="UTG position, 100bb stack, active"]`
- Structured JSON with valid actions array on every call that succeeds
- Handles complex compound prompts (verify cells, wait for elements, frequency checks)

## Hybrid Strategy (Optional)

For speed on simple steps, use `north-mini-code-free` for:
- `click` actions — produces `[aria-label="UTG position"]` (3x faster)
- `navigate` actions
- `wait` actions

Fall back to `nemotron-3-ultra-free` for:
- `verify_text` — needs complex selectors
- `verify_element` — compound assertions
- Any step with a `reference:` key

## What NOT to Use

- **Thinking-mode models** (`deepseek-v4-flash`, `deepseek-v4-flash-free`, `big-pickle`):
  Their CoT reasoning breaks structured JSON output. They return empty or malformed content
  because the thinking tokens interfere with the JSON format constraint.
- **Models with no balance**: `gpt-5.4-mini`, `gpt-5.4-nano`, `claude-haiku-4-5`, `gemini-3.5-flash`
  all return non-standard responses without `choices[0].message.content`.
