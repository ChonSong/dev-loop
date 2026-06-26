"""
humanizer-ml.py — ML-powered humanizer using fine-tuned LoRA adapter.
Run TEMPERATURE=0.7 python3 scripts/humanizer-ml.py < input.txt > output.txt
"""

import os, sys
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

MODEL_NAME = "Qwen/Qwen2.5-0.5B"
LORA_PATH = "/home/sc/workspace/humanizer-lora"
MAX_NEW_TOKENS = 512
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.9"))
TOP_P = 0.9
TOP_K = 40
REPETITION_PENALTY = 1.15


def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.float32, trust_remote_code=True,
    )
    if os.path.exists(LORA_PATH):
        model = PeftModel.from_pretrained(base, LORA_PATH)
    else:
        model = base
    model.eval()
    return tokenizer, model


def humanize(text, tokenizer, model):
    prompt = f"Humanize: {text.strip()}\n"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P, top_k=TOP_K,
            repetition_penalty=REPETITION_PENALTY,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )
    generated = outputs[0][inputs.input_ids.shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


if __name__ == "__main__":
    tokenizer, model = load_model()
    print('\n\n'.join(
        humanize(p, tokenizer, model)
        for p in sys.stdin.read().split('\n\n') if p.strip()
    ))
