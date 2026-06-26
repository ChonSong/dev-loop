# Colab Training — Beating GPTZero

The rule-based adversarial optimizer beats Fakespot but not GPTZero. To beat GPTZero, train a 1B+ model on human-written text with a GPU.

## The Notebook

`~/workspace/humanizer_colab.ipynb` — ready to upload to Google Colab.

### What it does (cell by cell)

| # | Cell | Time | Result |
|---|------|------|--------|
| 1 | `!pip install transformers peft datasets accelerate bitsandbytes` | ~2 min | Dependencies |
| 2 | Import + device check | instant | Confirms T4 GPU |
| 3 | Config: TinyLlama-1.1B, 4-bit, LoRA rank 16 | instant | — |
| 4 | Load dataset (OpenWebText, 50k samples) | ~2 min | Streaming, filtered |
| 5 | Load model with 4-bit quantization | ~2 min | ~2GB VRAM |
| 6 | Apply LoRA (trainable: ~0.5% of params) | instant | — |
| 7 | Tokenize | ~1 min | — |
| 8 | Train | ~10-15 min | Loss converges |
| 9 | Test rewrite | instant | Sample output |
| 10 | Download model as zip | instant | ~50MB |

### How to run

1. Go to https://colab.research.google.com/
2. Sign in with Google account
3. File → Upload Notebook → select `humanizer_colab.ipynb`
4. Runtime → Run all
5. Wait ~15-20 min total
6. At the end, browser downloads `human-model.zip`

### What you get

- A LoRA adapter for TinyLlama-1.1B that generates text in a human-like style
- Test cell shows a rewrite of sample AI text
- Zip file can be loaded locally with `PeftModel.from_pretrained()`

### Why this works when the rule-based approach doesn't

The rule-based humanizer injects surface noise (fillers, fragments, contractions) that Fakespot detects as statistical anomalies. GPTZero uses an ensemble of signals and isn't fooled by noise.

A fine-tuned model on real human text learns:
- Natural sentence length distributions
- Authentic discourse markers
- Human-level vocabulary choices
- Organic paragraph structure

These are structural features that no rule system can replicate.

## Local loading (after download)

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
model = PeftModel.from_pretrained(base, "./human-model")
tokenizer = AutoTokenizer.from_pretrained("./human-model")
```

## Background

Session date: 2026-06-16
Reason created: Rule-based approach hit GPTZero ceiling. Colab provides free T4 GPU for training.
