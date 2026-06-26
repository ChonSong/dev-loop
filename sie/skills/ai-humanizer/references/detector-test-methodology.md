# AI Detector Test Methodology

## Detector Used

**Fakespot RoBERTa** (`fakespot-ai/roberta-base-ai-text-detection-v1`)
- Fine-tuned RoBERTa for modern LLM detection (GPT-4, Claude, Gemini, Llama)
- Outputs: Human vs AI with confidence percentage
- Source: HuggingFace (free, no API key needed for download)

**GPT-2 Perplexity** (secondary metric)
- Measures how predictable the text is to GPT-2
- Lower perplexity = more predictable = more AI-like
- Ranges: <30 Strong AI, 30-50 Likely AI, 50-70 Uncertain, 70-100 Likely Human, >100 Strong Human

## Test Procedure

1. Generate purely AI text on a common topic ("AI in education") — formal register, typical structure
2. Humanize with `python3 humanizer.py -f input.txt -a -o humanized.txt` (aggressive mode)
3. Compare side-by-side: `python3 humanizer.py -f input.txt --compare`
4. Run both through detector: `python3 ai_detector.py -f input.txt -f humanized.txt`

## Sample Text (original)

```
The integration of artificial intelligence into modern educational frameworks represents a paradigm shift in how students engage with learning materials. By leveraging adaptive algorithms, educational platforms can now personalize content delivery based on individual student performance metrics, thereby optimizing the learning trajectory for each user. It is important to note that this technological advancement not only enhances student engagement but also provides educators with granular insights into classroom dynamics. Furthermore, the implementation of AI-driven assessment tools facilitates real-time feedback loops, enabling instructors to identify knowledge gaps and adjust their pedagogical strategies accordingly. However, it is crucial to consider the ethical implications surrounding data privacy and algorithmic bias, which must be addressed through robust regulatory frameworks to ensure equitable access to these transformative technologies across all socioeconomic backgrounds.
```

## Results (June 16, 2026)

| Metric | Original AI | After Humanizer | Delta |
|--------|-------------|-----------------|-------|
| Fakespot RoBERTa | 99.99% AI | 99.99% AI | 0 |
| Perplexity | 24.29 | 28.76 | +4.47 |
| Sentences changed | — | 2 of 5 | 40% |

## What Changed

- Sentence 3: "not only enhances student engagement but also provides" → "enhances student engagement and provides"
- Sentence 4: "Furthermore, the implementation" → "the implementation" (lowercased)
- No changes to sentences 1, 2, or 5

## Why It Failed

The detector didn't care about surface-level fixes. It reads:
- **Formal register** — "it is important", "it is crucial", "must be addressed"
- **Predictable sentence structure** — all 5 sentences follow the same Subject-Verb-Object pattern
- **Zero personal voice** — no "I think", "honestly", "but actually"
- **Perfect grammar** — no natural imperfections at all
- **Heavy formal vocabulary** — "paradigm shift", "robust regulatory frameworks", "algorithmic bias", "socioeconomic backgrounds"
