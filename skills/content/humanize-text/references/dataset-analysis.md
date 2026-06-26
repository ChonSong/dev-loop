# Dataset Analysis: dmitva/human_ai_generated_text

**Source**: https://huggingface.co/datasets/dmitva/human_ai_generated_text
**License**: CC-BY-4.0
**Rows**: 278,369
**Columns**: id, human_text, ai_text, instructions
**Language**: English

## What it is

Paired dataset where both a human and an AI (GPT-3.5/4 era) responded to the
same instruction prompt. The human text contains natural imperfections —
typos, grammar errors, run-on sentences, informal structure. The AI text is
polished, formal, and structurally uniform.

## Key Statistical Findings (from 10K-row sample)

### Sentence Structure

| Metric | Human | AI |
|---|---|---|
| Mean length | 23.9 words | 21.2 words |
| Median length | 19 | 21 |
| Std Dev | 20.4 | 7.4 |
| CV (burstiness) | **0.85** | **0.35** |
| Min length | 1 word | 1 word |
| Max length (sample) | 200+ words | ~80 words |
| Q1 | 13 | 16 |
| Q3 | 28 | 26 |

Key insight: **Humans write with 2.4× more sentence-length variance than AI.**
The CV of 0.85 means the standard deviation nearly equals the mean — some
sentences are 3 words, others 40+, with no pattern.

### Word Usage

**Top words AI overuses vs humans** (ratio AI freq / human freq):

| Word | AI/Human Ratio |
|---|---|
| essential | 81.8× |
| relationships | 59.0× |
| additionally | 48.2× |
| particularly | 84.8× |
| potential | 46.9× |
| providing | 41.7× |
| academic | 39.8× |
| leading | 26.5× |
| variety | 25.7× |
| access | 25.5× |
| provide | 22.7× |
| valuable | 21.6× |
| significant | 21.5× |
| various | 18.7× |
| specifically | 1.3× |

**Top words humans overuse vs AI** (ratio human freq / AI freq):

| Word | Human/AI Ratio |
|---|---|
| because | 29.1× |
| thing | 26.4× |
| really | 19.0× |
| kids | 18.4× |
| don't | 16.7× |
| want | 16.3× |
| everything | 15.5× |
| say | 15.4× |
| lot | 13.6× |
| got | 11.9× |
| think | 8.9× |
| know | 8.2× |
| you | **8.8×** |

### Sentence Starters

**AI-favored starters** (AI uses much more frequently):

| Starter | Human% | AI% | AI/Human |
|---|---|---|---|
| ultimately | 0.01 | 1.83 | 183× |
| additionally | 0.07 | 2.97 | 42× |
| moreover | 0.14 | 0.58 | 4× |
| furthermore | 0.20 | 1.84 | 9× |
| overall | 0.13 | 1.09 | 8× |
| in conclusion | ~0.5 | ~1.5 | ~3× |

**Human-favored starters**:

| Starter | Human% | AI% | Human/AI |
|---|---|---|---|
| because | 1.09 | 0.01 | **109×** |
| so | 1.64 | 0.12 | 14× |
| and | 1.71 | 0.12 | 14× |
| also | 1.86 | 0.10 | 19× |
| now | 0.41 | 0.04 | 10× |
| sometimes | 0.60 | 0.02 | 30× |
| well | 0.23 | 0.00 | 17× |

### Contractions

| Metric | Human | AI |
|---|---|---|
| Per 10K words | **85.3** | **14.2** |
| Total in sample | 37,060 | 2,865 |
| Rate ratio | 6.0× more | — |

Humans use 6× more contractions. The killer: `don't`, `can't`, `it's`, etc.
are almost absent in AI text.

### Transition Words (per 10K words)

| Word | Human | AI | AI/Human |
|---|---|---|---|
| however | 6.3 | 12.2 | 1.9× |
| therefore | 2.4 | 3.4 | 1.4× |
| furthermore | 1.0 | 8.7 | **8.8×** |
| moreover | 0.6 | 2.7 | **4.5×** |
| consequently | 0.1 | 0.4 | 2.5× |
| additionally | 0.3 | 14.0 | **46.6×** |
| thus | 0.2 | 1.6 | 8.1× |
| similarly | 0.1 | 1.9 | **24.7×** |
| notably | 0.0 | 0.1 | 15.8× |
| particularly | 0.0 | 1.8 | **84.8×** |
| conversely | 0.0 | 0.5 | **19.1×** |
| increasingly | — | — | ~11× |
| finally | 3.1 | 5.8 | 1.9× |
| overall | ~2 | ~8 | ~4× |

### Pronouns (per 10K words)

| Category | Human | AI | Human/AI |
|---|---|---|---|
| First-person (I, we, my, our) | 341.0 | 225.7 | 1.5× |
| **Second-person (you, your)** | **301.7** | **45.9** | **6.6×** |
| Third-person (he, she, they, it) | 324.0 | 160.9 | 2.0× |

### Punctuation (per 1K characters)

| Mark | Human | AI | AI/Human |
|---|---|---|---|
| . (period) | 7.70 | 7.66 | ~1.0× |
| , (comma) | 6.07 | 8.70 | **1.4×** |
| ; (semicolon) | 0.15 | 0.09 | 0.6× |
| ! (exclamation) | 0.05 | 0.02 | 0.3× |
| ? (question) | 0.19 | 0.02 | **0.1×** |
| — (em-dash) | 0.00 | 0.04 | **39×** |
| ... (ellipsis) | 0.02 | 0.00 | 0.1× |
| " (quotes) | 0.35 | 0.11 | **0.3×** |
| - (hyphen) | 0.15 | 1.05 | **6.9×** |

### Lowercase Sentence Starts

**Humans: 7.7% of sentences start with lowercase** (no capitalization).
**AI: 0.1%** (essentially zero).

Humans often start sentences mid-thought: "but I think...", "so then we...",
"because the thing is..."

## How to Use for Fine-Tuning

The paired structure (human_text ↔ ai_text on same instruction) is ideal for:

- **Style transfer training**: Train a model to rewrite AI text as human text.
  Task: Given `ai_text`, produce `human_text`.
- **Detection training**: Binary classifier (human vs AI).
- **Rewrite scoring**: Train a reward model to score how "human-like" a rewrite
  is, using `human_text` as the reference.

### Download

```bash
curl -sL "https://huggingface.co/datasets/dmitva/human_ai_generated_text/resolve/main/model_training_dataset.csv"
```

278K rows, 64MB CSV. Columns: id, human_text, ai_text, instructions.

### Recommended Split

- 250K train / 15K val / 13K test
- Shuffle by instruction type to avoid prompt leakage
