# Data-driven patterns from 278K paired human/AI text analysis

Source dataset: [dmitva/human_ai_generated_text](https://huggingface.co/datasets/dmitva/human_ai_generated_text)
- 278,369 rows, 3 columns: human_text, ai_text, instructions
- Same prompt given to both a human and GPT
- Human text has natural imperfections (typos, fragments, informal grammar)
- AI text is polished, formal, structured

Analysis: 10,000-row sample. Key findings below.

## Sentence structure

| Metric | Human | AI | Implication |
|---|---|---|---|
| Mean sentence length | 23.9 words | 21.2 words | AI ≈ human mean |
| Std Dev | 20.4 | 7.4 | **AI is 2.8x more uniform** |
| CV (burstiness) | **0.85** | **0.35** | Humans mix short & long |
| Min | 1 word | 1 word | |
| Max | 200+ words | 80 words | |

**How to exploit:** Intentionally create 2-6 word sentences alongside 35+ word sentences. Target CV ≥ 0.7.

## Contractions / 10K words

| Contractions | Human | AI |
|---|---|---|
| Total | **85.3 / 10K** | **14.2 / 10K** |

Humans use 6x more contractions. Every contraction type is underused by AI. Target: 70-85% of eligible pairs should be contracted.

## Sentence starters

**AI loves (replace these):**
- Ultimately (183x more common in AI)
- Additionally (42x)
- Furthermore (9.2x)
- Despite (31x)
- Through (44x)
- Overall (8.4x)
- Moreover (4.1x)

**Humans love (use these instead):**
- Because (59.7x more common in humans)
- Like (30x)
- Sometimes (19.7x)
- Also (16.4x)
- And (12.9x)
- So (12.5x)
- Then (14.6x)
- But (8.6x)

## Lowercase sentence starts

| | Human | AI |
|---|---|---|
| Lowercase starts | **7.7%** | **0.1%** |

AI almost never starts a sentence with lowercase. Target: ~8% of sentences.

## Word usage: AI overuses

These words appear more in AI text than human text on the SAME topic:

| Word | AI/Human ratio | Category |
|---|---|---|
| particularly | **84.8x** | adverb |
| essential | **81.8x** | adjective |
| additionally | **46.6x** | transition |
| relationships | **59.0x** | noun |
| potential | **46.9x** | noun |
| providing | **41.7x** | verb |
| academic | **39.8x** | adjective |
| performance | **32.1x** | noun |
| solutions | **29.4x** | noun |
| perspectives | **27.4x** | noun |
| strive | **23.0x** | verb |
| provide/provides | **22.7x** | verb |
| valuable | **21.6x** | adjective |
| significant | **21.5x** | adjective |
| growth | **19.5x** | noun |
| various | **18.7x** | adjective |

## Word usage: humans favor

| Word | Human/AI ratio | Note |
|---|---|---|
| because | **29.1x** | #1 human marker |
| thing | **26.4x** | vague but very human |
| really | **19.0x** | intensifier |
| kids | **18.4x** | informal register |
| don't | **16.7x** | contraction |
| want | **16.3x** | desire verb |
| everything | **15.5x** | absolute |
| you | **8.8x** | 2nd person |
| think | **8.9x** | epistemic verb |
| know | **8.2x** | epistemic verb |
| bad | **9.6x** | simple adjective |

## Punctuation / 1000 chars

| Mark | Human | AI | AI/Human |
|---|---|---|---|
| Periods (.) | 7.7 | 7.7 | 1.0x — equal |
| Commas (,) | 6.1 | 8.7 | **1.4x** — AI overuses |
| Semicolons (;) | 0.15 | 0.09 | 0.6x — humans use more |
| Exclamation (!) | 0.05 | 0.02 | 0.3x |
| Question (?) | 0.19 | 0.02 | **0.1x** — hardly any in AI |
| Quotes (")| 0.35 | 0.11 | 0.3x |
| Hyphens (-) | 0.15 | 1.05 | **6.9x** — AI loves hyphens |
| Em-dashes (—) | 0.00 | 0.04 | **39x** |

## Transition words / 10K

| Word | Human | AI | AI/Human |
|---|---|---|---|
| however | 6.3 | 12.2 | 1.9x |
| therefore | 2.4 | 3.4 | 1.4x |
| furthermore | 1.0 | 8.7 | **8.8x** |
| moreover | 0.6 | 2.7 | **4.5x** |
| consequently | 0.1 | 0.4 | 2.5x |
| additionally | 0.3 | 14.0 | **46.6x** |
| thus | 0.2 | 1.6 | **8.1x** |
| notably | 0.0 | 0.1 | 15.8x |
| particularly | 0.0 | 1.8 | **84.8x** |
| similarly | 0.1 | 1.9 | 24.7x |
| conversely | 0.0 | 0.5 | 19.1x |

## Personal pronouns / 10K

| Category | Human | AI | Human/AI |
|---|---|---|---|
| First-person (I, me, we, etc.) | 341.0 | 225.7 | **1.5x** |
| Second-person (you, your) | 301.7 | 45.9 | **6.6x** |
| Third-person (he, she, it, they) | 324.0 | 160.9 | **2.0x** |
