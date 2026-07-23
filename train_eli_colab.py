"""
Colab Fine-Tuning Script for Eli (Qwen 2.5/3 Coder) using Unsloth
Run on Google Colab (T4 / L4 / A100 GPU)
"""

import os
# Disable XET fallback stall in Colab
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

import torch

# Apply monkeypatch to fix transformers/trl version mismatch for Trainer.__init__
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

from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

# Configuration
MODEL_NAME = "Qwen/Qwen2.5-Coder-3B-Instruct"
MAX_SEQ_LENGTH = 2048
DATASET_PATH = "./processed/eli-sft-train.jsonl"
OUTPUT_DIR = "./models/eli-tone-lora"
EPOCHS = 3
BATCH_SIZE = 2
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 2e-4

def main():
    print(f"=== INITIALIZING UNSLOTH FINE-TUNING ===")
    print(f"Loading Base Model: {MODEL_NAME}")
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto-detect float16 / bfloat16
        load_in_4bit=True,
    )

    # Setup LoRA Adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=2026,
    )

    # Format ChatML Dataset
    def format_prompts(examples):
        texts = []
        for messages in examples["messages"]:
            formatted = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False
            )
            texts.append(formatted)
        return {"text": texts}

    print(f"Loading dataset from {DATASET_PATH}...")
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")
    dataset = dataset.map(format_prompts, batched=True)

    print(f"Dataset loaded ({len(dataset)} items). Setting up SFTTrainer...")

    # Universal TRL / Transformers version compatibility for SFTTrainer
    try:
        from trl import SFTConfig
        sft_config = SFTConfig(
            dataset_text_field="text",
            max_seq_length=MAX_SEQ_LENGTH,
            dataset_num_proc=2,
            packing=False,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRADIENT_ACCUMULATION,
            warmup_steps=2,
            num_train_epochs=EPOCHS,
            learning_rate=LEARNING_RATE,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=5,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=2026,
            output_dir=OUTPUT_DIR,
            save_strategy="no",
            report_to="none",
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
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRADIENT_ACCUMULATION,
            warmup_steps=2,
            num_train_epochs=EPOCHS,
            learning_rate=LEARNING_RATE,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=5,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=2026,
            output_dir=OUTPUT_DIR,
            save_strategy="no",
            report_to="none",
        )
        trainer_kwargs = {
            "model": model,
            "train_dataset": dataset,
            "dataset_text_field": "text",
            "max_seq_length": MAX_SEQ_LENGTH,
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

    print("=== STARTING TRAINING ===")
    trainer_stats = trainer.train()

    print(f"\n=== TRAINING COMPLETE ===")
    print(f"Saving LoRA Adapter to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Saved successfully!")

if __name__ == "__main__":
    main()
