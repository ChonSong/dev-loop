# Fine-tune Pipeline — Status & Lessons (June 2026)

## Pipeline scripts

| Script | Purpose | Location |
|--------|---------|----------|
| `train-human-model.py` | LoRA fine-tune a model on human-written text | `~/workspace/train-human-model.py` |
| `build-dataset.py` | Bootstrap + merge scraped data into training JSONL | `~/workspace/build-dataset.py` |

## Usage

```bash
source .venv/bin/activate
python3 build-dataset.py /tmp/human-data*.jsonl -o /tmp/human-training.jsonl
python3 train-human-model.py --data /tmp/human-training.jsonl --model-name distilgpt2 --output ./human-model
python3 train-human-model.py --rewrite "AI text..." --model ./human-model
```

## Models tested against Fakespot

| Model | Params | Train time (40 samples, CPU) | Fakespot score |
|-------|--------|------------------------------|----------------|
| distilgpt2 | 82M | 16s | 99.99% AI |
| Qwen2.5-0.5B-Instruct (prompted, not fine-tuned) | 0.5B | N/A (inference only) | 99.99% AI |
| Qwen2.5-1.5B-Instruct (prompted) | 1.5B | N/A | Not tested (RAM) |

**Takeaway**: Tiny models (<1B) produce garbage. Qwen 0.5B defaults to a childish "friendly chatbot" voice; distilgpt2 generates incoherent continuations. Neither fools any detector.

## Requirements for meaningful training

Data: ~500-2000 samples (40 bootstrapped → growing via cron). RAM: ~6GB+ for 1B model in 4-bit.

## Auto-collection

Cron job `human-text-collector` runs every 6h, appends to /tmp/human-training.jsonl.
