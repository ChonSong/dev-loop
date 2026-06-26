# Structure vs Surface Detection

## Core Finding

Modern AI detectors (Fakespot RoBERTa) detect **structural patterns** in text, not just surface-level features like vocabulary or contractions. This is why rule-based humanizers that only swap words and add fillers fail to move the needle.

## What Fakespot RoBERTa Sees

The model trained on GPT-4/Claude/Gemini output learns to recognize:

1. **The 5-paragraph essay template** — topic → supporting point A → supporting point B → counterpoint/nuance → conclusion
2. **Uniform sentence flow** — each sentence follows from the last with no tangents or asides
3. **Zero digression** — every clause serves the argument, unlike human writing which wanders
4. **Perfect topical coherence** — no "by the way" moments, no self-corrections, no "actually wait that reminds me"
5. **Formal register throughout** — no register mixing, no sudden colloquial turns
6. **Even information density** — every sentence carries roughly equal weight
7. **Predictable clause structure** — each sentence follows Subject-Verb-Object consistently

## Why Surface Changes Fail

The detector filters out noise from word swaps and contractions because it operates on *latent features* learned from millions of AI/human pairs. A sentence that reads "it's crucial to consider the ethical implications" still has the same *deep structure* as "it is crucial to consider the ethical implications" — the contraction is invisible to the model.

## What Humans Actually Do That AI Doesn't

Patterns in real human writing collected from HN and Reddit:

- **Topic drift** — start talking about X, then realize Y is more important mid-sentence
- **Self-correction** — "actually no, that's not quite right"
- **Register mixing** — formal statements followed by "yeah but who cares"
- **Rhetorical questions** — "but is that really true?"
- **Sentence fragments** — "Not really. It's more like..."
- **Discourse markers** — "look", "honestly", "the thing is", "here's the deal"
- **Tangential asides** — parentheticals that aren't strictly relevant
- **Varied coherence** — some jumps feel slightly disjointed
- **Inconsistent depth** — some points get 3 sentences, others get one

## Implications for Evasion

Rule-based humanizers can't generate these patterns because they require *understanding the content* to know where to inject tangents or break coherence. A regex engine can split sentences and swap words, but it can't decide that "now would be a good time to ask a rhetorical question about data privacy."

**The only path to structural evasion is a generative model** (fine-tuned LLM) that has internalized human writing patterns at the structural level and can reproduce them when rewriting.

## Test Data

See `detector-test-methodology.md` for the exact test text and full before/after.

## Failure Signatures

When a rule-based humanizer output is fed to Fakespot, the model produces:
- **99%+ AI confidence** even when perplexity is >50 (crossed into "Uncertain")
- No single sentence flagged — the whole text is flagged uniformly
- Suggests the feature vector driving the decision is *distributed across the entire text*, not localized

This distributed signal is the hallmark of structure-level detection — no single patch fixes it because the issue is the gestalt.
