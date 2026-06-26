# Scrapling-based training data pipeline

Collect real human writing at scale for training a custom humanizer model.

## Key insight

You don't need multiple accounts — you need **browser fingerprint rotation**.
Scrapling uses `camoufox` under the hood for `StealthyFetcher`, which
randomizes canvas fingerprint, WebGL, fonts, user-agent, screen resolution,
timezone, and locale on every launch. This is what evades bot detection, not
account management.

## Collection targets

Best sources of natural human writing (low anti-bot, high signal):

| Source | Why | Caveat |
|---|---|---|
| Reddit (old.reddit.com) | Dense comment threads, casual tone | Rate limit ~60 req/min |
| GitHub issues/PRs | Technical but human, high signal | Public API, generous limits |
| Stack Overflow comments | Technical Q&A, natural speech | Requires API key |
| Blog comments (Disqus) | Varied styles, easy to scrape | Many are Disqus-embedded |
| Wikipedia talk pages | Discussion, not article text | Parse wiki markup |

## Scrapling setup

```bash
pip install scrapling
playwright install chromium    # StealthyFetcher needs this
```

## Stealth collection pattern

```python
from scrapling.fetchers import StealthyFetcher
from scrapling import Fetcher
import json, time, random

StealthyFetcher.adaptive = True

targets = [
    "https://old.reddit.com/r/programming/comments/",
    "https://github.com/rust-lang/rust/issues/",
]

results = []
for url in targets:
    try:
        page = StealthyFetcher.fetch(
            url, headless=True, network_idle=True, timeout=30
        )
        text_blocks = page.css('p, li, .comment, .discussion')
        results.extend([b.text_content() for b in text_blocks if
                       len(b.text_content().split()) > 15])
    except Exception as e:
        print(f"Failed {url}: {e}")
    time.sleep(random.uniform(2, 5))

with open("human_samples.json", "w") as f:
    json.dump(results, f, indent=2)
```

## Why this beats rule-based

Rule-based humanizers play pattern-matching — detectors learn the patterns.
A fine-tuned model on actual human writing learns the *distribution* of human
language: sentence-length variance (burstiness), vocabulary entropy, discourse
marker placement, and the subtle grammatical "mistakes" that are actually just
human speech. These are much harder for static detectors to flag because
they're sampling from the same distribution as the training data.

## Fine-tuning stack

- **Model**: Qwen-2.5-1.5B or Llama-3.2-3B (runs on CPU with Q4)
- **Adapter**: LoRA (rank=16, alpha=32)
- **Training**: unsloth or axolotl
- **Loss**: Next-token prediction on "human rewrite" task
- **Data format**: `{"instruction": "Humanize this AI text", "input": "...", "output": "..."}`
