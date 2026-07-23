"""
Colab / Kaggle Fine-Tuning Script for Eli using Unsloth
Run on Google Colab or Kaggle (T4 / L4 / P100 / A100 GPU)

Production Step-Based Checkpointing & Hardware Benchmarking Guard:
- Base Model: Qwen/Qwen3-4B-Instruct
- Quantization: 4-bit NF4 via Unsloth
- Context Window: 49,152 tokens (48k context for long Fable-5 CoT traces)
- Checkpointing: Step-based every 250 steps (save_strategy="steps", save_steps=250)
  Resilient against Colab/Kaggle session disconnects (max loss = 15 mins).
- Benchmark Hook: Logs step wall-clock time across first 50 steps to print accurate ETA.
"""

import os
import sys
import time
import torch
from pathlib import Path

# Disable HF hub transfer stalls in Colab/Kaggle
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# Import Unsloth FIRST before transformers/trl for optimizations
from unsloth import FastLanguageModel

# Monkeypatch transformers/trl Trainer compatibility
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
from trl import SFTTrainer, SFTConfig
from transformers import TrainerCallback

# Configuration
MODEL_NAME = "unsloth/Qwen3-4B-Instruct-2507"
MAX_SEQ_LENGTH = 49152  # 48k context window
DATASET_PATH = "./processed/eli-sft-train-formatted.jsonl"
OUTPUT_DIR = "./models/eli-tone-lora"

# Custom Callback for Step Throughput & ETA Benchmarking
class ThroughputBenchmarkCallback(TrainerCallback):
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.step_start_time = None
        self.step_durations = []

    def on_step_begin(self, args, state, control, **kwargs):
        self.step_start_time = time.time()

    def on_step_end(self, args, state, control, **kwargs):
        if self.step_start_time:
            duration = time.time() - self.step_start_time
            self.step_durations.append(duration)
            if state.global_step <= 50 and state.global_step % 10 == 0:
                avg_step_time = sum(self.step_durations[-10:]) / len(self.step_durations[-10:])
                remaining_steps = self.total_steps - state.global_step
                eta_hours = (avg_step_time * remaining_steps) / 3600.0
                print(f"[BENCHMARK Step {state.global_step}/{self.total_steps}] "
                      f"Avg Step Time: {avg_step_time:.2f}s | "
                      f"Estimated Remaining Time: {eta_hours:.2f} hours")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train Eli using Unsloth on Colab/Kaggle")
    parser.add_argument("--batch-size", type=int, default=8, help="Total effective batch size (micro_batch * grad_accum * gpus)")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Initial learning rate")
    args = parser.parse_args()

    total_batch_size = args.batch_size
    # Auto-split total batch size into safe micro-batch size and gradient accumulation steps
    if total_batch_size % 2 == 0:
        micro_batch_size = 2
    else:
        micro_batch_size = 1
    gradient_accumulation = max(1, total_batch_size // micro_batch_size)

    print(f"=== INITIALIZING UNSLOTH FINE-TUNING ===")
    print(f"Base Model: {MODEL_NAME}")
    print(f"Context Length: {MAX_SEQ_LENGTH:,} tokens (48k)")
    print(f"Dataset Path: {DATASET_PATH}")
    print(f"Output Checkpoints: {OUTPUT_DIR}")
    print(f"Total Batch Size: {total_batch_size} (Micro-batch: {micro_batch_size}, Grad Accumulation: {gradient_accumulation})")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto float16 / bfloat16
        load_in_4bit=True,
    )

    # Configure LoRA Adapters
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

    def format_prompts(examples):
        texts = []
        if "conversations" in examples:
            for convs in examples["conversations"]:
                messages = []
                for msg in convs:
                    role = "user" if msg.get("from") in ["human", "user"] else "assistant"
                    messages.append({"role": role, "content": msg.get("value", "")})
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                texts.append(text)
        elif "instruction" in examples and "output" in examples:
            for inst, out in zip(examples["instruction"], examples["output"]):
                messages = [
                    {"role": "user", "content": inst},
                    {"role": "assistant", "content": out}
                ]
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                texts.append(text)
        return {"text": texts}

    dataset_path = DATASET_PATH
    if not Path(dataset_path).exists():
        for fallback in [
            "./processed/eli-sft-train-formatted.jsonl",
            "./processed/eli-sft-train.jsonl",
        ]:
            if Path(fallback).exists():
                dataset_path = fallback
                break

    print(f"Loading dataset from {dataset_path}...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")
    dataset = dataset.map(format_prompts, batched=True)
    total_samples = len(dataset)
    effective_batch_size = micro_batch_size * gradient_accumulation
    total_steps = (total_samples // effective_batch_size) * args.epochs
    print(f"Dataset loaded: {total_samples:,} training samples ({total_steps:,} total training steps).")

    # Step-Based Checkpointing Config (Resilient against disconnects)
    sft_config = SFTConfig(
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=True,
        per_device_train_batch_size=micro_batch_size,
        gradient_accumulation_steps=gradient_accumulation,
        warmup_steps=100,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=25,
        optim="adamw_8bit",
        weight_decay=0.001,
        lr_scheduler_type="cosine_with_min_lr",
        lr_scheduler_kwargs={"min_lr_rate": 0.1},
        seed=2026,
        output_dir=OUTPUT_DIR,
        save_strategy="steps",
        save_steps=50,
        save_total_limit=3,
        report_to="none",
    )

    benchmark_cb = ThroughputBenchmarkCallback(total_steps=total_steps)

    try:
        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            processing_class=tokenizer,
            args=sft_config,
            callbacks=[benchmark_cb],
        )
    except TypeError:
        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            tokenizer=tokenizer,
            args=sft_config,
            callbacks=[benchmark_cb],
        )

    # Auto-resume from last step checkpoint if available
    last_checkpoint = None
    if Path(OUTPUT_DIR).exists():
        checkpoints = [d for d in Path(OUTPUT_DIR).glob("checkpoint-*") if d.is_dir()]
        if checkpoints:
            checkpoints.sort(key=lambda x: int(x.name.split("-")[-1]))
            last_checkpoint = str(checkpoints[-1])
            print(f"Found existing checkpoint: {last_checkpoint}. Resuming training...")

    print("\n=== STARTING UNSLOTH SFT TRAINING ===")
    if last_checkpoint:
        trainer_stats = trainer.train(resume_from_checkpoint=last_checkpoint)
    else:
        trainer_stats = trainer.train()

    print(f"\n=== TRAINING COMPLETE ===")
    print(f"Saving final LoRA Adapter to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Saved successfully!")

if __name__ == "__main__":
    main()
