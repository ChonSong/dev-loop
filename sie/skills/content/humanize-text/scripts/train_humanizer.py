#!/usr/bin/env python3
"""
train_humanizer.py — LoRA fine-tune Qwen2.5-0.5B on human/AI text pairs.
Trains the model to rewrite AI-sounding text into human-sounding text.

Usage:
  source ml-env/bin/activate
  python3 scripts/train_humanizer.py

Requirements (install once):
  uv pip install torch --index-url https://download.pytorch.org/whl/cpu
  uv pip install transformers datasets peft accelerate

Dataset: expects /tmp/human_ai_pairs.csv with columns:
  id, human_text, ai_text, instructions
(from dmitva/human_ai_generated_text on HuggingFace, 278K rows)
"""

import os, csv
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    get_linear_schedule_with_warmup, set_seed
)
from peft import LoraConfig, get_peft_model, TaskType
from accelerate import Accelerator

# ── Config ────────────────────────────────────────────────────
MODEL_NAME = "Qwen/Qwen2.5-0.5B"
DATA_PATH = "/tmp/human_ai_pairs.csv"
OUTPUT_DIR = "/home/sc/workspace/humanizer-lora"
MAX_LENGTH = 512
BATCH_SIZE = 4
GRAD_ACCUM = 4
LR = 3e-4
EPOCHS = 1
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
MAX_SAMPLES = 50000
SEED = 42

set_seed(SEED)
accelerator = Accelerator()


class HumanizeDataset(Dataset):
    def __init__(self, data_path, tokenizer, max_len, max_samples=None):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.pairs = []
        with open(data_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if row is None:
                    continue
                if max_samples and i >= max_samples:
                    break
                ai = (row.get('ai_text') or '').strip()
                human = (row.get('human_text') or '').strip()
                if ai and human and len(ai) > 10 and len(human) > 10:
                    self.pairs.append((ai, human))
        print(f"Loaded {len(self.pairs)} pairs")

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        ai, human = self.pairs[idx]
        prompt = f"Humanize: {ai.strip()}\n"
        full = prompt + f"{human.strip()}"

        prompt_tokens = self.tokenizer(prompt, truncation=True,
                                       max_length=self.max_len)
        full_tokens = self.tokenizer(full, truncation=True,
                                     max_length=self.max_len)

        input_ids = full_tokens["input_ids"]
        attn_mask = full_tokens.get("attention_mask", [1] * len(input_ids))
        prompt_len = len(prompt_tokens["input_ids"])
        labels = [-100] * prompt_len + input_ids[prompt_len:]

        if len(input_ids) > self.max_len:
            input_ids = input_ids[:self.max_len]
            attn_mask = attn_mask[:self.max_len]
            labels = labels[:self.max_len]

        pad_len = self.max_len - len(input_ids)
        input_ids += [self.tokenizer.pad_token_id] * pad_len
        attn_mask += [0] * pad_len
        labels += [-100] * pad_len

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attn_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def main():
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading model {MODEL_NAME}...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.float32, trust_remote_code=True,
    )
    model.gradient_checkpointing_enable()

    lora_config = LoraConfig(
        r=LORA_R, lora_alpha=LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_dropout=LORA_DROPOUT, bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("Loading dataset...")
    dataset = HumanizeDataset(DATA_PATH, tokenizer, MAX_LENGTH, MAX_SAMPLES)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True,
                            num_workers=0, drop_last=False)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    total_steps = len(dataloader) * EPOCHS // GRAD_ACCUM
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=100, num_training_steps=total_steps
    )

    model, optimizer, dataloader, scheduler = accelerator.prepare(
        model, optimizer, dataloader, scheduler
    )

    print(f"\nTraining: {len(dataset)} samples, {total_steps} steps\n")
    model.train()
    global_step = 0
    for epoch in range(EPOCHS):
        total_loss = 0
        for step, batch in enumerate(dataloader):
            with accelerator.accumulate(model):
                outputs = model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["labels"],
                )
                loss = outputs.loss
                accelerator.backward(loss)
                total_loss += loss.detach().float()
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
            global_step += 1
            if global_step % 50 == 0:
                print(f"  Step {global_step}/{total_steps}  loss={total_loss/(step+1):.4f}")
            if global_step >= total_steps:
                break

    print(f"\nSaving to {OUTPUT_DIR}...")
    accelerator.wait_for_everyone()
    unwrapped = accelerator.unwrap_model(model)
    unwrapped.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Done!")


if __name__ == "__main__":
    main()
