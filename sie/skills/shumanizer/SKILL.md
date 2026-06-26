---
name: shumanizer
description: CLI AI text humanizer — anti-detection prompts + post-processing + 12-metric detector. Built from StealthHumanizer pipeline.
category: writing
---

# SHumanizer

CLI tool at `/home/sc/workspace/shumanizer.py`. Rewrites AI text to bypass detection using StealthHumanizer's anti-detection prompts + post-processing rules + 12-metric detector.

## Usage

```bash
# Source Hermes env for API keys first
set -a && . ~/.hermes/.env

# Detect-only (no API key needed)
python3 /home/sc/workspace/shumanizer.py -f input.txt --detect-only
python3 /home/sc/workspace/shumanizer.py --text "AI text..." --detect-only

# Full pipeline (rewrite + detect)
python3 /home/sc/workspace/shumanizer.py --level ninja --style academic -f input.txt
python3 /home/sc/workspace/shumanizer.py --level aggressive --style humanize --text "AI text here..."
python3 /home/sc/workspace/shumanizer.py -f input.txt -o output.txt

# JSON output
python3 /home/sc/workspace/shumanizer.py -f input.txt --json
```

## Levels

- `light` — minimal changes, swap 2-3 words
- `medium` — moderate rewrite, 30-40% rearranged
- `aggressive` (default) — strong rewrite, personal voice
- `ninja` — full rewrite, blog-post style, rhetorical questions

## Styles: humanize, academic, casual, professional, creative, technical

## Providers tried in order

1. **OpenRouter** — `openai/gpt-oss-120b:free` (requires OPENROUTER_API_KEY env var)
2. **OpenCode Zen** — `gemini-3.5-flash` (requires OPENCODE_ZEN_API_KEY)
3. **Gemini** — `gemini-1.5-flash` (requires GEMINI_API_KEY)

## Pipeline

1. Anti-detection system prompt instructs LLM to vary burstiness, avoid AI phrases, use contractions
2. LLM rewrites text through provider
3. Post-processing swaps 50+ AI-typical phrases ("furthermore" → "plus", "demonstrates" → "shows")
4. 12-metric detector scores output (burstiness, AI phrase density, contraction ratio, etc.)

## Location

`/home/sc/workspace/shumanizer.py` — single-file Python3 script, no deps beyond stdlib.
