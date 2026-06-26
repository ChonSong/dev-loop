# Fine-Tuning a Humanizer Model

A more advanced approach: LoRA fine-tune a small language model (Qwen2.5-0.5B) on paired human/AI text to statistically learn human writing patterns instead of applying hand-coded rules.

## When to use this instead of the rule-based script

- Detectors are catching your rule-based output
- You have a GPU or can wait for CPU training
- You need to match a specific human voice at scale
- The rule-based script introduces artifacts that look predictable

## Dataset

**Primary:** [dmitva/human_ai_generated_text](https://huggingface.co/datasets/dmitva/human_ai_generated_text)
- 278,369 rows (CSV)
- Columns: `human_text`, `ai_text`, `instructions` (shared prompt for both)
- CC-BY-4.0 license
- Human text has natural imperfections: typos, grammar mistakes, informal structure, contractions, varied sentence lengths

**Secondary options:**
- [artem9k/ai-text-detection-pile](https://huggingface.co/datasets/artem9k/ai-text-detection-pile) — Pile-based detection corpus
- [Ateeqq/AI-and-Human-Generated-Text](https://huggingface.co/datasets/Ateeqq/AI-and-Human-Generated-Text) — similar paired structure
- [GOAT-AI/generated-novels](https://huggingface.co/datasets/GOAT-AI/generated-novels) — LLM-generated fiction

## Training approach

### Model choice
- **Qwen2.5-0.5B** — good balance of size vs quality. ~500M params, fits in 2GB RAM.
- **TinyLlama-1.1B** — better quality if you have 4GB+ RAM or a GPU.
- **Phi-3-mini (3.8B)** — best quality, needs GPU.

### Setup
```bash
pip install torch transformers datasets accelerate peft
```

### Training format

Teach the model to translate AI → human:
```
System: Rewrite this to sound human.
User: {ai_text}
Assistant: {human_text}
```

Loss mask everything except the assistant response. Use `-100` as the ignore index for labels.

### LoRA config
- `r=8, alpha=16, dropout=0.05`
- Target modules: `q_proj, k_proj, v_proj, o_proj`
- This adds ~1M trainable params out of 500M (0.2%)

### Training loop
- Batch size: 2 (CPU), grad_accum: 4 → effective 8
- Learning rate: 3e-4
- AdamW optimizer
- 1 epoch (3K-10K samples is enough for proof of concept)
- Full 278K rows would take ~hours on CPU, faster on GPU

### transformers 5.x API notes
In transformers >=5.0.0:
- `Trainer.__init__()` uses `processing_class=tok` instead of `tokenizer=tok`
- `from_pretrained()` uses `dtype=torch.float32` instead of `torch_dtype=torch.float32`
- TrainingArguments parameters are the same

## Inference

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B")
model = PeftModel.from_pretrained(model, "/path/to/adapter")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B")

messages = [
    {"role": "system", "content": "Rewrite this to sound human."},
    {"role": "user", "content": ai_text},
]
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tok(prompt, return_tensors="pt")
out = model.generate(**inputs, max_new_tokens=512, temperature=0.7, do_sample=True)
```

## Pitfalls

- **CPU training is slow:** 3K samples × 1 epoch on 2 cores takes ~15-30 min. Full 278K is hours.
- **Dataset quality:** Some human_text entries are still formal/essay-like. Filter to shorter, less grammatically perfect entries for best results.
- **Over-tuning:** The model might learn to add too many typos/errors. Temperature 0.7-0.9 at inference balances naturalness vs correctness.
- **Detector adaptation:** Detectors evolve. Periodically re-test and retrain.
- **Rule-based fallback:** Use the `scripts/humanize.py` as a second pass after model inference for patterns the model misses.
