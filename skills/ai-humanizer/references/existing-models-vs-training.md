# Existing Models vs Training — Findings (June 2026)

## The core question

User asked: "Is there not an existing model we can use?" — a smarter question than "let's train one." Existing instruction-tuned models CAN rewrite text. The question is whether they evade detection.

## Models tested locally (CPU, ~4GB RAM)

| Model | Size | Loads? | Output Quality | Fakespot Detection |
|-------|------|--------|---------------|-------------------|
| Qwen2.5-0.5B-Instruct | 0.5B | ✅ ~1GB | Childish/friendly tone | 99.99% AI |
| distilgpt2 (LoRA fine-tuned) | 82M | ✅ ~800MB | Gibberish (40 samples) | 99.99% AI |

## Why small models fail

- <1B models have a detectable "friendly chatbot" voice — exclamation marks, simple sentence structures, overly enthusiastic tone
- Detectors see through this immediately — it's a different set of tells but still tells
- The model's OWN training data (instruction tuning) gives it a style that detectors recognize

## What would actually work

- **1B+ model** (TinyLlama, Qwen-2.5-1.5B, Phi-3-mini) with LoRA fine-tune on 5000+ human-written samples
- **GPU required** — CPU training of 1B+ models takes hours
- **Colab free tier** (T4 GPU) is the practical path — notebook at `~/workspace/humanizer_colab.ipynb`

## The two viable paths

| Path | Hardware | Beats GPTZero? | Effort |
|------|----------|---------------|--------|
| Adversarial optimizer (rules + Fakespot loop) | CPU only | ❌ | Low — works now |
| Fine-tune 1B+ model on human text | GPU (Colab) | Probably, untested | Medium — needs Colab |

## Bottom line

Small existing models (<1B) don't work — they have their own detectable voice. Larger models (1B+) need GPU. Without GPU or API access, the adversarial optimizer is the best available option.
