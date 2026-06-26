# Datasets for AI Detection Bypass / Humanization

Found on Hugging Face — paired human/AI text for fine-tuning humanizer models.

## Primary: `dmitva/human_ai_generated_text`

**278K rows, 64MB CSV** — the best single source for training a humanizer.

### Schema

| Column | Contents |
|---|---|
| `id` | UUID |
| `human_text` | Human-written response to the prompt |
| `ai_text` | AI-generated response to the same prompt |
| `instructions` | The prompt given to both writer and AI |

### Why it's good for humanizer training

The human text has real imperfections — typos ("offter", "desicions"), lowercase starts, run-on sentences, varying grammar quality. The AI text is polished, formal, and predictable. This contrast is exactly what a fine-tuned model needs to learn the "human style" distribution.

### Sample

```
INSTRUCTIONS: Write a persuasive essay on whether classes from home should be offered
HUMAN: "Also they feel more comfortable at home. Some school have decreased bullying..."
AI:    "Therefore, when it comes to allowing students the option to attend classes from home,
       there are intricacies that need to be taken into consideration..."
```

### How to use for fine-tuning

```
from datasets import load_dataset
ds = load_dataset("dmitva/human_ai_generated_text", split="train")
```

For seq2seq fine-tuning (T5, Flan-T5, Qwen-2.5-Instruct):
- input = `ai_text` (the text to humanize)
- target = `human_text` (the target human style)

For LoRA fine-tuning on a decoder model:
- Format as chat template: user provides `ai_text`, assistant returns `human_text`

## Secondary: `Ateeqq/AI-and-Human-Generated-Text`

249 downloads, 22 likes. English. Similar paired structure.

## Detection-side datasets

| Dataset | Downloads | Notes |
|---|---|---|
| `artem9k/ai-text-detection-pile` | 812 | Pile-based evaluator training |
| `dmitva/human_ai_generated_text` | 677 | Dual-use: detection OR humanization |
| `Ateeqq/AI-and-Human-Generated-Text` | 249 | Alternative paired dataset |
| `ziq/ai-generated-text-classification` | 714 | Classification-ready |

## Workflow lesson

Before building a custom scraping pipeline (Scrapling, proxy rotation, multiple accounts):

1. **Search HF datasets first** — `huggingface.co/datasets?search=human_ai_generated_text`
2. Evaluate size and quality
3. Only scrape if no adequate dataset exists

`dmitva/human_ai_generated_text` (278K pairs) is sufficient for most humanizer fine-tuning needs.
