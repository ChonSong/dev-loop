# GPTZero Detection Test — June 16, 2026

Tested three versions of the same AI-generated paragraph against GPTZero's free web detector (gptzero.me). All three returned **100% AI-generated**.

## Test text

Original topic: AI integration in educational frameworks. ~180 words across ~7 sentences.

## Results

| Version | GPTZero | Fakespot RoBERTa | Notes |
|---------|---------|-----------------|-------|
| Original (untouched) | **100% AI** | 99.99% AI | Baseline — clean GPT-4 style output |
| Humanized v3 (3-pass aggressive) | **100% AI** | 71-99% AI (seed-dependent) | Fillers, contractions, vocab swaps, sentence fragments |
| Adversarial optimized (vs Fakespot) | **100% AI** | <1% AI | Heavy noise injection, broken clause structure, poor readability |

## What GPTZero caught

Even with aggressive structural changes (fragments, misplaced fillers, broken sentences), GPTZero still scored 100% AI. This suggests GPTZero uses multiple detection signals beyond what we disrupted:

1. **Structural coherence** — even with fragments, the underlying argument flow (topic→detail→counterpoint→conclusion) remained intact
2. **Register consistency** — the formal-to-casual register mixing was detectable as artificial
3. **Perplexity + burstiness + classifier ensemble** — GPTZero uses multiple models, not one

## Practical implication

Against GPTZero specifically, the rule-based and adversarial approaches **do not work**. The gap isn't in the transformation quality — it's that GPTZero's ensemble catches patterns that single-model detectors miss. The only tested approach that could plausibly beat GPTZero is training a generator on real human writing at scale (see `humanizer-training` skill).

## Detector summary (mid-2026)

| Detector | Open model? | API cost | Effectiveness vs rule-based humanizer |
|----------|------------|----------|--------------------------------------|
| Fakespot RoBERTa | ✅ Yes (HF) | Free | Beatable via adversarial optimization |
| Hello-SimpleAI | ✅ Yes (HF) | Free | Useless — classifies all modern LLM as "Human" |
| GPTZero | ❌ No | Free tier | Invulnerable to rule-based approaches |
| Originality.ai | ❌ No | Paid | Not tested |
| Turnitin | ❌ No | Institutional | Not tested |
