---
name: humanize-text
description: >-
  Strip AI tells from generated text to evade AI detectors. Rule-based
  humanizer script + Scrapling-based training data collection pipeline for
  custom fine-tuning. Free, local, zero API costs.
category: content
tags: [ai-detection, humanizer, text-rewriting, scrapling, stealth]
---

# humanize-text

Bypass AI text detectors (ZeroGPT, Originality, GPTZero, Turnitin) by
stripping the statistical tells that give AI-written text away. Two modes:

1. **Rule-based** — `humanizer.py` template applies ~60+ data-driven rewrites
   (marker phrases, vocabulary swaps, contraction injection, sentence-length
   burstiness, paragraph variance). Deterministic, instant, no model needed.
2. **Data-driven** — Scrapling + camoufox for stealth collection of real human
   writing at scale, for building a custom fine-tune.

## Quick start

```bash
python3 templates/humanizer.py < input.txt > output.txt
python3 templates/humanizer.py --aggressive < input.txt > output.txt
```

## Data-driven improvements (v2)

This skill was rebuilt using **278,369 paired rows** from
`dmitva/human_ai_generated_text` on HuggingFace — human-written text paired
with AI-generated text on the same prompt. Key statistical findings embedded
in the template:

| Pattern | Human | AI | Ratio |
|---|---|---|---|
| Sentence CV (burstiness) | 0.85 | 0.35 | 2.4× |
| Contractions / 10K words | 85.3 | 14.2 | 6.0× |
| Second-person pronouns / 10K | 301.7 | 45.9 | 6.6× |
| Lowercase sentence starts | 7.7% | 0.1% | 77× |
| Comma density / 1K chars | 6.07 | 8.70 | 0.70× |
| "additionally" frequency | 0.3/10K | 14.0/10K | 46.6× |
| "particularly" frequency | 0.0/10K | 1.8/10K | 84.8× |
| "because" as sentence starter | 1.09% | 0.01% | 109× |
| First-person pronouns / 10K | 341.0 | 225.7 | 1.5× |

The template bakes in these ratios so your output matches the statistical
profile of real human writing, not a guess-based pattern list.

## What it fixes

| AI Tell | Fix |
|---|---|
| Marker phrases ("in today's digital landscape", "it is crucial to") | Pattern-matched replacement |
| Overused vocab (leverage, utilize, unprecedented, demonstrate) | 60+ synonym swaps with probability-based application |
| Uniform sentence length (low burstiness, CV 0.35 vs human 0.85) | Splits at introductory phrases, comma+conjunction, or first comma |
| No contractions | ~70% chance per pair (matching human rate of 85/10K) |
| Formal transitions (furthermore, moreover, consequently) | ~60% random drop; "additionally"→"also" at 95% rate |
| AI-favored sentence starters (Additionally, Furthermore, Moreover) | Replaced with human equivalents: "Also", "Plus", "So", "But" |
| Perfect lowercase-start rate (0.1% vs human 7.7%) | 8% random chance per sentence |
| Missing "you" address (humans use 6.6× more) | "You" inserted at verb-friendly sentence start |
| Perfect parallelism (not only X but also Y) | Flattened to "X and Y" |
| Oxford comma overuse | Random removal |
| Missing "because" as sentence starter (109× ratio) | "because" in human starter pool |
| Over-punctuation (em-dashes, hyphens, commas) | Em-dash→period, comma reduction, hyphen reduction |
| Perfect paragraph structure | Splits paragraphs >150 words |
| "an" before consonant after word swap | Bidirectional a/an fix |
| Collocation breaks ("paradigm shift", "machine learning") | Context-aware skip in word swaps |

## Pipeline for custom training data

The rule-based approach is a cat-and-mouse game. For lasting evasion:

1. **Scrape real human writing** using Scrapling's `StealthyFetcher` (bypasses
   Cloudflare, uses camoufox for browser fingerprint randomization):
   ```python
   from scrapling.fetchers import StealthyFetcher
   StealthyFetcher.adaptive = True
   page = StealthyFetcher.fetch('https://forum.example.com',
       headless=True, network_idle=True)
   posts = page.css('.post-content')
   ```
2. **Build a paired corpus**: human text ↔ AI-rewritten version. For an
   existing paired dataset, use `dmitva/human_ai_generated_text` (278K rows,
   English, CC-BY-4.0) — download and split for fine-tuning directly.
3. **Fine-tune a small model** (Llama-3B, Phi-3, Qwen-2.5-1.5B) via LoRA on
   the task: "Rewrite this AI text to sound like the human samples."
4. **Run locally** — Ollama or llama.cpp on CPU with Q4 quantization. No API
   costs.

## ML fine-tuning pipeline (v3)

Rule-based evasion is cat-and-mouse. For durable evasion, fine-tune a small model
on the paired dataset:

1. **Dataset**: `dmitva/human_ai_generated_text` (278K rows, English, CC-BY-4.0).
   Columns: `id`, `human_text`, `ai_text`, `instructions`.
   Download: `curl -sL "https://huggingface.co/datasets/dmitva/human_ai_generated_text/resolve/main/model_training_dataset.csv" > /tmp/human_ai_pairs.csv`

2. **Install ML stack** (CPU-friendly):
   ```bash
   uv venv ml-env --python 3.11
   source ml-env/bin/activate
   uv pip install torch --index-url https://download.pytorch.org/whl/cpu
   uv pip install transformers datasets peft accelerate
   ```

3. **Train** (50K samples, ~30-60 min on 2-core CPU, 8GB RAM):
   ```bash
   source ml-env/bin/activate
   python3 scripts/train_humanizer.py
   ```
   This fine-tunes Qwen2.5-0.5B (350M params) with LoRA (rank=8, ~4M trainable
   params). Output adapter at `humanizer-lora/`.

4. **Inference**:
   ```bash
   source ml-env/bin/activate
   TEMPERATURE=0.9 python3 scripts/humanizer-ml.py < input.txt > output.txt
   ```

**Training note**: The kernel on this host is 5.4.0 (below recommended 5.5.0),
which Accelerate warns about. It still works but slower. For GPU training,
increase `MAX_SAMPLES` to the full 278K and use `torch_dtype=torch.bfloat16`.

## Pitfalls

- **"Learning"** collides with "machine learning" — never swap it in WORD_SWAPS.
- **"Paradigm shift"** collocation — replacing "paradigm" alone breaks the
   phrase. Context check in `replace_overused_words()` handles this.
- **Per-word swap rate** should stay under ~60% probability or the text starts
   sounding unnatural. Many swaps use 30-50% probability.
- **Scrapling browser deps** need `playwright install chromium` first.
- **Playwright dep version pin**: Scrapling pins `playwright==1.48` which may
   conflict with other tools. Use a venv.
- **Sentence starter insertion** can produce "And however" when both
   `fix_ai_sentence_starts` and `add_human_sentence_starts` fire on the same
   sentence. Both functions now skip sentences that already start with a
   transition or human word.
- **"Look" as a starter** causes "Look however" artifacts. Removed from
   HUMAN_STARTERS — avoided in favor of "So", "But", "And" which read
   naturally.
- **"You" insertion before preposition** ("You in the landscape", "You by using")
   produces ungrammatical text. The `_HUMAN_START_BLOCK` set prevents insertion
   before prepositions, articles, and helping verbs.
- **A/an mismatch after word swap** ("an new", "a important"). The `_fix_a_an()`
   function handles both directions: "a"→"an" before vowels and "an"→"a" before
   consonants.
- **"additionally" has 46.6× higher frequency in AI text** — it's the #1
   transition tell. Gets replaced with "also" at 95% rate by `AI_OVERUSED` but
   also caught by `PHRASE_REPLACEMENTS` and `fix_ai_sentence_starts`.
- **Detectors evolve** — what passes today may not pass next month. The
   ML fine-tune approach (v3) is more durable than rule-based.
- **Probability-based swaps give different output each run** — this is
   intentional and human-like, but makes debugging harder. Set `random.seed()`
   for reproducible outputs during development.
- **CSV dataset loading**: the 278K CSV has inconsistent quoting and some empty
   cells. Always use `errors='replace'` and `(row.get('key') or '').strip()` in
   the CSV reader.

## Templates

- `templates/humanizer.py` — The data-driven humanizer script (v3, ~470 lines).
  Run from the skill directory or copy anywhere:
  ```
  cd ~/.hermes/skills/content/humanize-text
  python3 templates/humanizer.py < input.txt > output.txt
  ```

## Scripts

- `scripts/train_humanizer.py` — LoRA fine-tune script for Qwen2.5-0.5B.
  Trains on 50K paired samples (~30-60 min on 2-core CPU, 8GB RAM). Requires
  ml-env with torch, transformers, peft, datasets, accelerate.
- `scripts/humanizer-ml.py` — Inference script for the trained LoRA adapter.
  Run after training: `TEMPERATURE=0.9 python3 scripts/humanizer-ml.py < input.txt`

## References

- `references/dataset-analysis.md` — Full statistical breakdown of the 278K-row
  analysis: sentence length distributions, word frequency tables, transition
  word weights, punctuation ratios, per-category pronoun usage.
- `references/scrapling-data-pipeline.md` — Scrapling MCP setup, StealthyFetcher
  config, camoufox fingerprinting, and scraping at scale.
- `blader/humanizer` (hub skill) — alternate approach, may have different phrase
  lists worth merging.
- `MohamedAbdallah-14/unslop` (hub skill) — focuses on structural tells
  (tricolons, em-dash pileups, hedging stacks). Consider running both.
