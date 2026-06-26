---
name: ai-humanizer
description: Free AI-detection bypass using data-driven rule-based rewriting. Strips AI phrases, swaps formal words, adds human markers (contractions, hedges, personal openers). No API calls, runs locally.
trigger: rewrite this to pass ai detection | humanize this text | bypass AI detector
---

# AI Humanizer

Rewrite AI-generated text to bypass detection. Three-part pipeline: humanizer (rewrite), detector (benchmark), collector (training data).

## Location

Scripts: `~/workspace/humanizer.py`, `~/workspace/ai_detector.py`, `~/workspace/human-train-collector.py`

## Architecture

The humanizer runs a multi-phase pipeline with escalating aggression:

```
Phase 1 — Marker phrase slaughter  (kill_markers)
Phase 2 — Vocabulary swap           (swap_vocab)
Phase 3 — Heavy contraction         (contract)
Phase 4 — Sentence-level carnage    (rip_sentences, pass_num escalates)
Phase 5 — Polish & cleanup          (polish)
```

Aggressive mode (`-a`) runs 3 passes with increasing `pass_num` (0→1→2), which scales:
- Sentence split threshold: 20 → 17 → 14 words
- Split chance: 55% → 70% → 85%
- Vary sentence opening: 50% → 65% → 80%
- Fragment injection: 5% → 15% → 25%

## Usage

```bash
# Standard pass (1x)
python3 ~/workspace/humanizer.py -f input.txt -o output.txt

# Aggressive (3 passes, escalating)
python3 ~/workspace/humanizer.py -f input.txt -a -o output.txt

# Side-by-side diff
python3 ~/workspace/humanizer.py -f input.txt --compare

# Perplexity benchmark
python3 ~/workspace/humanizer.py -f input.txt --benchmark

# Combined: benchmark + diff
python3 ~/workspace/humanizer.py -f input.txt -ab

# Compare before/after with detector
python3 ~/workspace/ai_detector.py -f input.txt -f humanized.txt
```

## Detector

`ai_detector.py` runs two methods side-by-side:

1. **Fakespot RoBERTa** — fine-tuned for modern LLMs (GPT-4, Claude, Gemini). Most reliable open-source detector as of mid-2026.
2. **GPT-2 Perplexity** — measures text predictability. Ranges: `<30 Strong AI`, `30-50 Likely AI`, `50-70 Uncertain`, `70-100 Likely Human`, `>100 Strong Human`.

Requires `transformers` + `torch` (~800MB). Install: `source .venv/bin/activate && pip install transformers torch`

**Detector landscape note**: Older open-source detectors like `Hello-SimpleAI/chatgpt-detector-roberta` classify ALL modern LLM output as "Human" with 99%+ confidence — useless for detection. Fakespot is the only reliable open option. GPTZero doesn't publish model weights, so programmatic testing against it isn't possible.

## Adversarial Training Loop

`adversarial-train.py` runs a feedback loop that optimizes humanizer parameters against a live detector:

```bash
source .venv/bin/activate
python3 adversarial-train.py -f input.txt -n 100 --evolve
```

The loop:
1. Humanizes text with current best parameters
2. Runs output through Fakespot detector
3. Mutates parameters (simulated annealing — temperature decays over iterations)
4. Keeps mutations that lower the AI score
6. Saves winning params back to `humanizer.py`

See `references/adversarial-feedback-loop.md` for full methodology, literature citations, and measured results.
See `references/gptzero-test-results.md` for actual GPTZero benchmark data (100% AI, all versions).
See `references/whack-a-mole-is-data.md` for the user's insight that adversarial self-training IS collecting useful data.
See `references/fine-tune-pipeline.md` for training pipeline scripts and status.

**Proven**: Drove Fakespot detection from 100% AI → **<1% AI** in as few as 3 trials. Key transformations: sentence fragments, mid-sentence fillers, broken clause structure — features that disrupt the "too perfect" AI pattern.

**Trade-off**: Effectiveness at the cost of readability. The parameters that best fool the detector also garble the text. This is inherent — the detector's signal IS the text's coherence, so defeating it requires injecting incoherence.

**The "whack-a-mole IS the data" insight**: Every trial in the adversarial loop generates training signal. Successful mutations are positive examples of "text that fooled the detector." This is a validated adversarial self-training approach (Krishna et al., "Paraphrasing Evades Detectors of AI-Generated Text" — paraphrasing drops detection from ~95% to ~50-70%).

## Best Workflow

### Option A: Quick pass (moderate quality)
```
python3 humanizer.py -f input.txt -a -o output.txt
python3 ai_detector.py -f input.txt -f output.txt   # check score
```

### Option B: Adversarial optimization (highest evasion, degraded quality)
```
source .venv/bin/activate
python3 adversarial-train.py -f input.txt -n 50          # optimize
python3 adversarial-train.py -f input.txt -n 50 --evolve # save params
python3 humanizer.py -f input.txt -a -o output.txt       # use evolved params
```

### Option C: Compare and benchmark
```
python3 humanizer.py -f input.txt -a --compare       # see what changed
python3 humanizer.py -f input.txt --benchmark         # perplexity delta
```

## Pitfalls

- **Modern detectors (Fakespot) see structure, not just style.** Rule-based humanizers work but need enough aggression — subtle synonym replacement alone does nothing. Sentence fragmentation, filler injection, and structural disruption are required.
- **The adversarial optimizer overfits to Fakespot.** Parameters evolved against Fakespot may not transfer to GPTZero or Originality.ai. Each detector has a different signal model.
- **`humanizer.py` uses `random.seed()`** — results vary between runs. Run multiple times or use the adversarial trainer to converge.
- **Word swaps can break collocations.** Exclude "learning" from swap dict to avoid "machine lesson." Always verify with `--compare`.
- **Aggressive mode will garble text.** Three passes of sentence splitting produce fragments. Acceptable for evasion but verify with `--compare`.
- **Adversarial iteration converges fast.** The loop typically finds effective params in ~3-5 trials, not 100. Use `-n 20` for quick results.
- **For sustained evasion, automate the feedback loop.** Run `adversarial-train.py --batch` on a growing corpus. Re-run when detectors update.

## User Preferences (this project)

- **Effectiveness over elegance.** User prefers tools that *work* even if brute-force. Explicitly rejected the fine-tune path in favor of aggressive rule-based approaches. Don't recommend replacing working rules with a model unless the rules demonstrably fail. "Doesn't have to be efficient but it should work."
- **Verify claims before asserting.** User challenged "are you sure" on the fine-tune approach and was right — the small model didn't work. When the user questions whether something is proven, check before asserting. Bring evidence or admit uncertainty.
- **Give direct text inline.** When the user asks for text content (test data, output samples, etc.), paste it directly in the response — don't say "see the file at /tmp/..." or "it's in the workspace." They want to read it now, not look it up. Exception: files >50 lines.
- **Check existing solutions first.** Before building a custom model, training pipeline, or data collector, check if an existing one already solves the problem. User asked "is there not an existing model we can use" and "do we need the cron isn't datasets enough" — both were valid: existing HF datasets and models exist and beat custom-built approaches. Search HuggingFace, check installed tools, look at config — then build. 
- **Action over discussion.** "> Both", "> start", "yes" — terse agreement markers. Move, don't explain.
- **Present options with real trade-offs.** Show costs (readability, complexity, setup time) and let the user choose. Don't sell one path.

## Data-Driven Profile Training (New Approach)

Instead of applying fixed rules, **learn a human writing profile from real text samples**. This approach adapts to any source domain (HN comments, Reddit, blog posts, product reviews) by extracting statistical signatures.

### Workflow

```bash
# 1. Collect human text samples
python3 collect-human-text.py    # uses HN API + other free sources
→ Outputs human-text-samples.jsonl

# 2. Analyse patterns and generate a profile
python3 analyse-human-text.py
→ Shows sentence starter distribution, sentence variance, contraction rate, filler frequency
→ Outputs a JSON profile config

# 3. Humanize using the trained profile
python3 humanizer.py --file input.txt --eval
→ Uses the learned profile for rewriting

# 4. Train from custom data
python3 humanizer.py --train my-samples.jsonl --output my-profile.json
```

### What Real Human Text Looks Like (from 162 HN comment samples)

| Metric | Human | AI (typical) |
|--------|-------|-------------|
| Sentence starts | "i" (37x), "the" (33x), "and" (13x), "we" (13x), "but" (10x), "so" (9x) | "in conclusion", "furthermore", "moreover", "additionally" |
| Sentence length variance | 318 (very varied, 1–148 words) | <50 (uniform) |
| Transitions | "and" 61%, "but" 16%, "so" 8%, "because" 6% | "furthermore", "moreover", "however" all rare |
| Fillers | "like", "just", "really", "actually" occur naturally | Almost absent |
| Contractions | "it's", "i'm", "don't", "can't" — heavy usage | Avoided |

### Key Findings

- **Low sentence-length variance (<50) is a strong AI signal.** Human writing naturally mixes 5-word sentences with 40-word ones.
- **Human sentence starters are boring.** "I", "The", "And", "We", "But", "So" — never the AI markers.
- **Fillers are human markers.** "like", "just", "really", "actually" appear naturally and their absence is detectable.
- **Small models (<1B) can't rewrite.** Even TinyLlama-1.1B outputs templated formal prose when asked to rephrase. The rule-based + data-driven approach beats any local model at this task for CPU.
- **The profile is portable.** Train once on your target domain (HN, Reddit, blog comments), reuse for all rewriting in that domain. Different domains need different profiles.

### Files

- `collect-human-text.py` — Scrapling/requests-based collector from HN API and Reddit (free, no keys)
- `analyse-human-text.py` — Statistical analyser: sentence lengths, starts, contraction rate, filler prevalence, transition words, AI tell counters
- `human-text-samples.jsonl` — Curated sample set (format: `{"source": "hn", "text": "..."}` per line)
- `humanizer.py` — Full pipeline: `--train` to learn from JSONL, `--profile` to apply custom profile, `--variants N` to pick best of N

## Data: Use Existing Datasets, Don't Scrape

Don't bother scraping your own human text data. Massive high-quality datasets already exist on HuggingFace:

| Dataset | Size | Best For |
|---------|------|----------|
| `openwebtext` | 8M docs | General human-like web writing |
| `wikitext-103-v1` | 100M tokens | Clean formal writing |
| `tiny_shakespeare` | 40K lines | Creative/literary style |

Load directly via `datasets.load_dataset()` — no scraping needed.

The `human-train-collector.py` script exists but only useful when you need domain-specific data not in existing datasets. Scrapling 0.4.x quirks:
- `resp.text()` → `resp.text`
- No `stealth=` keyword on `fetcher.get()`
- Run from `.venv/`

## Advanced: Google Colab Training

The rule-based approach hits a ceiling against GPTZero. To beat GPTZero-grade detectors, train a 1B+ model on human text with GPU. Google Colab free tier (T4 GPU) is the practical path.

Notebook at `~/workspace/humanizer_colab.ipynb`. It:
1. Loads TinyLlama-1.1B with 4-bit quantization
2. Loads OpenWebText (50k samples)
3. LoRA fine-tunes (rank 16, ~15 min on T4)
4. Tests rewriting AI text
5. Downloads the trained model

See `references/colab-training.md` for the full notebook walkthrough.
See `references/existing-models-vs-training.md` for model selection findings.

**Local model experiment results (June 2026)**:
| Approach | Fakespot | GPTZero | Notes |
|----------|----------|---------|-------|
| distilgpt2 (82M, CPU fine-tune) | 99.99% AI | 100% AI | Too small, too little data |
| Qwen2.5-0.5B-Instruct (via HF) | 99.99% AI | — | Output has childish "friendly chatbot" voice |
| Rule-based adversarial (our optimizer) | <1% AI | 100% AI | Beats Fakespot, degraded readability |
| TinyLlama-1.1B (Colab, 4-bit LoRA) | — | — | Untested — requires GPU |

**Key insight**: Small models (<1B) have their own detectable stylistic voice. You need 1B+ with GPU training for output that actually sounds human. Without GPU or API access, the adversarial optimizer is the best local option.
