# Whack-a-Mole IS the Data

The user's key insight: "couldn't the whack-a-mole be the data?"

Every trial in the adversarial feedback loop (`adversarial-train.py`) generates training signal. Successful mutations — ones that lower the detector's AI score — are positive examples of "text that fooled this detector." The process IS generating data.

## Why this matters

My default tendency was to say "we need to collect human text → train a proper model → THEN it works." The user correctly pointed out that the adversarial optimization loop IS already doing that. Each trial that beats Fakespot produces a concrete artifact (the winning parameter set) that encodes "what works against this detector."

## Literature basis

This is validated as **adversarial self-training**:

- Krishna et al. (2023), "Paraphrasing Evades Detectors of AI-Generated Text": simple paraphrasing drops GPT-2 detector accuracy from ~95% to ~50-70%
- GAN-based training for text generation: generator vs discriminator, where the generator's training signal IS the discriminator's errors

## Practical takeaway

| Approach | Collects human data? | Generates adversarial signal? | Works now? |
|----------|---------------------|------------------------------|-----------|
| Scrapling collection → train model | ✅ Yes | ❌ No (passive) | ❌ (too little data) |
| Adversarial optimization loop | ❌ No | ✅ Yes (active) | ✅ (against Fakespot) |

The user was right: the adversarial loop is a form of training, not just a hack. The correct framing is:

**"Adversarial self-training with a rule-based generator"** — the rules ARE the learned policy, parameterized by their weights, and the optimization loop is the training process that converges those weights against a discriminator (the detector).

## When to recommend which path

- **Need results today** → adversarial optimization loop (works against single-model detectors)
- **Need results against GPTZero/Turnitin** → need the human-data → model fine-tune path (theoretical — not yet proven with available resources)
- **Can tolerate wait time** → let the cron job collect data, then train (see `humanizer-training` skill)
