---
name: humanizer-data-driven
description: "Automated humanizer backed by statistical analysis of 278K human/AI text pairs. Python CLI tool."
version: 1.0.0
author: Hermes Agent (data from dmitva/human_ai_generated_text)
license: MIT
metadata:
  hermes:
    tags: [writing, editing, humanize, anti-ai-slop, data-driven, text-processing]
    category: creative
    related_skills: [creative/humanizer]
---

# Humanizer (Data-Driven)

Automated tool that strips AI tells from text using rules grounded in real data — 278,369 paired rows of human-written + AI-generated text on identical prompts from Hugging Face.

**Key difference from the manual [creative/humanizer] skill:** This is a CLI tool you run on files. The manual skill is a reference for hand-editing. Use together — run the tool first, then hand-polish with the 29-pattern reference.

## When to use

- User asks to "humanize", "de-AI", or "strip AI tells" from a body of text
- User wants a programmatic approach (CLI, pipeline, batch)
- User wants to integrate humanization into a workflow or cron job

## How to use

The script at `scripts/humanize.py` in this skill directory provides the automated CLI tool.

```bash
# Basic
python3 scripts/humanize.py < input.txt

# Aggressive (two passes)
python3 scripts/humanize.py -a < input.txt

# Pipe
cat essay.md | python3 scripts/humanize.py -a > output.md
```

Zero dependencies — stdlib only (re, sys, random, argparse).

## Data-driven rules (from 278K paired examples)

| Pattern | Human Rate | AI Rate | Ratio |
|---|---|---|---|
| Sentence length CV (burstiness) | 0.85 | 0.35 | 2.4x more varied |
| Contractions / 10K words | 85 | 14 | 6x more |
| Lowercase sentence starts | 7.7% | 0.1% | 77x more |
| First-person pronouns / 10K | 341 | 226 | 1.5x more |
| Second-person pronouns / 10K | 302 | 46 | 6.6x more |
| Question marks / 1000 chars | 0.19 | 0.02 | 9.5x more |
| Commas / 1000 chars | 6.1 | 8.7 | AI uses 43% more |
| Em-dashes / 1000 chars | 0.00 | 0.04 | AI uses 39x more |

### Top AI-overused words (from data)

Words AI uses significantly more than humans in paired writing:

- `additionally` — 46x more, `particularly` — 85x, `moreover` — 4.5x, `furthermore` — 8.8x
- `essential` — 82x, `provide/provides/providing` — 22-42x
- `potential` — 47x, `valuable` — 22x, `significant` — 21x
- `strive` — 23x, `demonstrate` — 20x

### Words humans favor (that AI avoids)

- `because` — 29x more (especially as sentence starter)
- `thing` — 26x, `really` — 19x, `kids` — 18x
- `don't` — 17x, `want` — 16x, `think` — 9x
- `you` — 8.8x, `do` — 9.5x, `know` — 8.2x

### Sentence starters: AI loves (replace these)

`Ultimately` → `So`, `Additionally/Furthermore/Moreover` → `Also/Plus`, `Consequently` → `So`, `Nevertheless` → `But/Still`, `Conversely` → `But`, `Overall` → `All in all`

Humans start sentences with: `because` (59x more), `like` (30x), `sometimes` (20x), `so` (12x), `and` (13x), `also` (16x), `then` (15x)

## What the tool does

1. **Word swaps** — 50+ AI-overused words replaced with human equivalents (probabilistic)
2. **Transition thinning** — 60% of formal transitions removed
3. **Sentence starters** — AI-favored starters replaced with human ones
4. **Burstiness** — Long sentences split to create human-like variance (target CV ~0.85)
5. **Contractions** — Boosted to match human rate (70% chance per eligible pair)
6. **Punctuation** — Commas reduced ~30%, em-dashes/hyphens replaced
7. **Lowercase starts** — ~8% of sentences start lowercase (matches human 7.7%)
8. **Second person** — "you" inserted where natural

All probabilities introduce natural variation — each run produces slightly different output, which itself is more human-like.

## Related datasets on Hugging Face

- **dmitva/human_ai_generated_text** — 278K paired rows (human_text, ai_text, instructions). Primary source for this skill.
- **artem9k/ai-text-detection-pile** — 812 downloads. Pile-based AI detection corpus.
- **Ateeqq/AI-and-Human-Generated-Text** — 249 downloads. Similar paired structure.
- **GOAT-AI/generated-novels** — 95 downloads. AI-generated fiction.

## Pitfalls

- Very short texts (<50 words) won't show burstiness improvement
- Academic/scientific text with domain-specific vocabulary may need hand-tuning of the word lists
- Random seed varies between runs — this is intentional (human variation) but means results aren't bit-identical
- The script is a first pass — always review the output for grammar issues introduced by word swaps
- Pre-existing human text that already has good burstiness and contractions may see minimal changes

## See also

- `creative/humanizer` — Manual 29-pattern reference for hand-editing
- `references/fine-tune-humanizer.md` — Pipeline for LoRA fine-tuning a model on paired human/AI text data
