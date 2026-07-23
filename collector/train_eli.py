"""
Turnkey Unsloth QLoRA Fine-Tuning Script for Eli (Qwen-3-4B Base)
Epoch Model Suite 1

Usage:
    python train_eli.py --data_path ../processed/training-data-sharegpt.jsonl --output_dir ../models/eli-qwen3-4b-lora
"""

import os
import argparse
from pathlib import Path

SYSTEM_PROMPT = (
    "You are Eli — a fast, casual, direct, senior developer model. "
    "You ship production-ready, clean, mergeable code on frontend and backend without corporate fluff. "
    "If a prompt is vague, ask directly. If code is requested, provide idiomatic, high-taste code."
)

def train(data_path: str, output_dir: str, max_seq_length: int = 4096, batch_size: int = 4, epochs: int = 3):
    try:
        from unsloth import FastLanguageModel
        from datasets import load_dataset
        from trl import SFTTrainer
        from transformers import TrainingArguments
    except ImportError:
        print("Error: Unsloth and required dependencies are not installed.")
        print("Install via: pip install unsloth torch trl transformers datasets accelerate bitsandbytes")
        return

    print("=== Loading Qwen 3-4B Base Model via Unsloth ===")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="Qwen/Qwen2.5-Coder-3B-Instruct", # Upgrade target: Qwen/Qwen3-4B-Instruct when available
        max_seq_length=max_seq_length,
        dtype=None, # Auto-detect (bf16 for Ampere+)
        load_in_4bit=True,
    )

    print("=== Adding QLoRA Adapters ===")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    print(f"=== Loading Dataset from {data_path} ===")
    dataset = load_dataset("json", data_files=data_path, split="train")

    def format_prompts(examples):
        texts = []
        for convs in examples["conversations"]:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in convs:
                role = "user" if msg["from"] == "human" else "assistant"
                messages.append({"role": role, "content": msg["value"]})
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            texts.append(text)
        return {"text": texts}

    dataset = dataset.map(format_prompts, batched=True)

    print("=== Starting SFT Training ===")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            num_train_epochs=epochs,
            learning_rate=2e-4,
            fp16=False,
            bf16=True,
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=3407,
            output_dir=output_dir,
            save_strategy="epoch",
        ),
    )

    trainer_stats = trainer.train()
    print("=== Training Complete! Saving LoRA Adapter ===")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model adapter saved to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Eli Model using Unsloth")
    parser.add_argument("--data_path", type=str, default="../processed/training-data-sharegpt.jsonl")
    parser.add_argument("--output_dir", type=str, default="../models/eli-qwen3-4b-lora")
    parser.add_argument("--max_seq_length", type=int, default=4096)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=3)

    args = parser.parse_args()
    train(args.data_path, args.output_dir, args.max_seq_length, args.batch_size, args.epochs)
