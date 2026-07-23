"""
Turnkey Unsloth QLoRA Fine-Tuning Script for Eli (Qwen-3-4B Base)
Epoch Model Suite 1

Usage:
    python train_eli.py --data_path ../processed/training-data-sharegpt.jsonl --output_dir ../models/eli-qwen3-4b-lora
"""

import os
import argparse
from pathlib import Path

# Apply monkeypatch to fix transformers/trl version mismatch for Trainer.__init__
try:
    import transformers
    import inspect
    original_init = transformers.Trainer.__init__
    def patched_trainer_init(self, *args, **kwargs):
        sig = inspect.signature(original_init)
        if 'tokenizer' in kwargs and 'tokenizer' not in sig.parameters and 'processing_class' in sig.parameters:
            kwargs['processing_class'] = kwargs.pop('tokenizer')
        elif 'processing_class' in kwargs and 'processing_class' not in sig.parameters and 'tokenizer' in sig.parameters:
            kwargs['tokenizer'] = kwargs.pop('processing_class')
        return original_init(self, *args, **kwargs)
    transformers.Trainer.__init__ = patched_trainer_init
    if hasattr(transformers, 'trainer') and hasattr(transformers.trainer, 'Trainer'):
        transformers.trainer.Trainer.__init__ = patched_trainer_init
except ImportError:
    pass

SYSTEM_PROMPT = (
    "You are Eli — a fast, casual, direct, senior developer model. "
    "You ship production-ready, clean, mergeable code on frontend and backend without corporate fluff. "
    "If a prompt is vague, ask directly. If code is requested, provide idiomatic, high-taste code."
)

def train(data_path: str, output_dir: str, max_seq_length: int = 50000, batch_size: int = 4, epochs: int = 3):
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
        model_name="Qwen/Qwen3-4B-Instruct",
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
        if "conversations" in examples:
            for convs in examples["conversations"]:
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for msg in convs:
                    role = "user" if msg.get("from") in ["human", "user"] else "assistant"
                    messages.append({"role": role, "content": msg.get("value", "")})
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                texts.append(text)
        elif "messages" in examples:
            for msgs in examples["messages"]:
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + msgs
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                texts.append(text)
        elif "instruction" in examples and "output" in examples:
            for inst, out in zip(examples["instruction"], examples["output"]):
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": inst},
                    {"role": "assistant", "content": out}
                ]
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                texts.append(text)
        elif "text" in examples:
            return {"text": examples["text"]}
        return {"text": texts}

    dataset = dataset.map(format_prompts, batched=True)

    print("=== Starting SFT Training ===")
    try:
        from trl import SFTConfig
        sft_config = SFTConfig(
            dataset_text_field="text",
            max_seq_length=max_seq_length,
            dataset_num_proc=2,
            packing=False,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            num_train_epochs=epochs,
            learning_rate=2e-4,
            fp16=False,
            bf16=True,
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.001,
            lr_scheduler_type="cosine",
            lr_scheduler_kwargs={"min_lr_rate": 0.1},
            seed=3407,
            output_dir=output_dir,
            save_strategy="epoch",
        )
        try:
            trainer = SFTTrainer(
                model=model,
                train_dataset=dataset,
                processing_class=tokenizer,
                args=sft_config,
            )
        except TypeError:
            try:
                trainer = SFTTrainer(
                    model=model,
                    train_dataset=dataset,
                    tokenizer=tokenizer,
                    args=sft_config,
                )
            except TypeError:
                trainer = SFTTrainer(
                    model=model,
                    train_dataset=dataset,
                    args=sft_config,
                )
    except (ImportError, TypeError):
        training_args = TrainingArguments(
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            num_train_epochs=epochs,
            learning_rate=2e-4,
            fp16=False,
            bf16=True,
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.001,
            lr_scheduler_type="cosine",
            lr_scheduler_kwargs={"min_lr_rate": 0.1},
            seed=3407,
            output_dir=output_dir,
            save_strategy="epoch",
        )
        trainer_kwargs = {
            "model": model,
            "train_dataset": dataset,
            "dataset_text_field": "text",
            "max_seq_length": max_seq_length,
            "dataset_num_proc": 2,
            "packing": False,
            "args": training_args,
        }
        try:
            trainer = SFTTrainer(processing_class=tokenizer, **trainer_kwargs)
        except TypeError:
            try:
                trainer = SFTTrainer(tokenizer=tokenizer, **trainer_kwargs)
            except TypeError:
                trainer = SFTTrainer(**trainer_kwargs)

    trainer_stats = trainer.train()
    print("=== Training Complete! Saving LoRA Adapter ===")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model adapter saved to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Eli Model using Unsloth")
    parser.add_argument("--data_path", type=str, default="../processed/training-data-sharegpt.jsonl")
    parser.add_argument("--output_dir", type=str, default="../models/eli-qwen3-4b-lora")
    parser.add_argument("--max_seq_length", type=int, default=50000)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=3)

    args = parser.parse_args()
    train(args.data_path, args.output_dir, args.max_seq_length, args.batch_size, args.epochs)
