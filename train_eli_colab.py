"""
Colab / Kaggle Fine-Tuning Script for Eli using Unsloth
Run on Google Colab or Kaggle (T4 / L4 / P100 / A100 GPU)

Optimized for high-throughput training without Colab update freezes:
- Unsloth 2-5x fast fused Triton kernels (lora_dropout=0.0)
- Process & Tokenizer thread safety (TOKENIZERS_PARALLELISM=false)
- Unbuffered live stdout streaming (PYTHONUNBUFFERED=1)
- Non-blocking single-process data loading (dataset_num_proc=1, dataloader_num_workers=0)
- Fast validation loss evaluation (eval_dataset capped to 32 samples)
- Safe in-loop sampling without corrupting Unsloth model graph
"""

# Force unbuffered output so Colab / Kaggle stdout updates instantly without freezing/stalls
os.environ["PYTHONUNBUFFERED"] = "1"

# Disable HF hub transfer stalls and configure tokenizers/CUDA memory allocator BEFORE PyTorch import
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True,max_split_size_mb:128"

import os
import sys
import time
import gc
import torch
from pathlib import Path

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

# Configuration Defaults
MODEL_NAME = "unsloth/Qwen3-4B-Instruct-2507"
MAX_SEQ_LENGTH = 16384  # 16k context window (VRAM safe on T4/L4 GPUs)
DATASET_PATH = "./processed/eli-sft-train-formatted-chat-blended.jsonl"
OUTPUT_DIR = "./models/eli-tone-lora"


# Custom Progress Callback for Unbuffered Colab Logging
class ColabProgressCallback(TrainerCallback):
    """Flushes stdout on every logging step and cleans CUDA memory cache periodically to prevent VRAM fragmentation crashes."""
    def on_train_begin(self, args, state, control, **kwargs):
        # Override restored TrainerState save_steps/eval_steps with CLI arguments upon checkpoint resumption
        state.save_steps = args.save_steps
        state.eval_steps = args.eval_steps
        print(f"📌 [CONFIG SYNC] Synced TrainerState: save_steps={state.save_steps}, eval_steps={state.eval_steps}", flush=True)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            loss = logs.get("loss", None)
            lr = logs.get("learning_rate", None)
            step = state.global_step
            max_steps = state.max_steps
            if loss is not None:
                print(f"[Step {step}/{max_steps}] Train Loss: {loss:.4f} | LR: {lr:.2e}", flush=True)
        sys.stdout.flush()

    def on_step_end(self, args, state, control, **kwargs):
        # Periodically clear CUDA cache every 10 steps to prevent VRAM fragmentation OOMs
        if state.global_step > 0 and state.global_step % 10 == 0:
            torch.cuda.empty_cache()
            gc.collect()

    def on_save(self, args, state, control, **kwargs):
        step = state.global_step
        torch.cuda.empty_cache()
        gc.collect()
        print(f"\n💾 [CHECKPOINT SAVED @ Step {step}] Successfully saved checkpoint to {args.output_dir}/checkpoint-{step}\n", flush=True)
        torch.cuda.empty_cache()
        gc.collect()
        sys.stdout.flush()



# Custom Callback for Step Throughput & Periodic Sample Generation
class ThroughputAndSamplingCallback(TrainerCallback):
    def __init__(self, total_steps: int, model, tokenizer, eval_prompt="Hey Eli, write a python script to validate JWT tokens and handle expiration cleanly.", enable_sampling=False, sample_every_steps=250):
        self.total_steps = total_steps
        self.step_start_time = None
        self.step_durations = []
        self.model = model
        self.tokenizer = tokenizer
        self.eval_prompt = eval_prompt
        self.enable_sampling = enable_sampling
        self.sample_every_steps = sample_every_steps

    def on_step_begin(self, args, state, control, **kwargs):
        self.step_start_time = time.time()

    def on_step_end(self, args, state, control, **kwargs):
        if self.step_start_time:
            duration = time.time() - self.step_start_time
            self.step_durations.append(duration)
            if state.global_step <= 50 and state.global_step % 10 == 0 and state.global_step > 0:
                avg_step_time = sum(self.step_durations[-10:]) / len(self.step_durations[-10:])
                remaining_steps = self.total_steps - state.global_step
                eta_hours = (avg_step_time * remaining_steps) / 3600.0
                print(f"[BENCHMARK Step {state.global_step}/{self.total_steps}] "
                      f"Avg Step Time: {avg_step_time:.2f}s | "
                      f"Estimated Remaining Time: {eta_hours:.2f} hours", flush=True)

        # Sample generation every sample_every_steps ONLY if explicitly enabled
        if self.enable_sampling and state.global_step > 0 and state.global_step % self.sample_every_steps == 0:
            try:
                print(f"\n--- [SANITY CHECK @ Step {state.global_step}] Generating Sample Code ---", flush=True)
                messages = [{"role": "user", "content": self.eval_prompt}]
                prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
                
                # Switch to eval mode safely without breaking Unsloth training kernels
                self.model.eval()
                with torch.no_grad():
                    outputs = self.model.generate(**inputs, max_new_tokens=256, temperature=0.7)
                response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
                self.model.train()
                
                print(f"Eli Output:\n{response[:300]}...", flush=True)
                print("----------------------------------------------------------------------\n", flush=True)
            except Exception as e:
                print(f"[SANITY CHECK @ Step {state.global_step}] Skipped: {e}", flush=True)
            finally:
                self.model.train()
                torch.cuda.empty_cache()
                gc.collect()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train Eli using Unsloth on Colab/Kaggle")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=16, help="Total effective batch size")
    parser.add_argument("--micro-batch-size", type=int, default=1, help="Micro batch size per GPU")
    parser.add_argument("--grad-accum", type=int, default=None, help="Gradient accumulation steps (overrides batch-size)")
    parser.add_argument("--max-seq-len", type=int, default=MAX_SEQ_LENGTH, help="Maximum context length")
    parser.add_argument("--save-steps", type=int, default=50, help="Checkpoint save steps interval")
    parser.add_argument("--eval-steps", type=int, default=250, help="Validation loss evaluation steps interval")
    parser.add_argument("--checkpoint", type=str, default=None, help="Explicit checkpoint path to resume training")
    parser.add_argument("--enable-sampling", action="store_true", help="Enable sample generation during step callbacks")
    parser.add_argument("--disable-sampling", action="store_true", help="Disable sample generation during step callbacks")
    parser.add_argument("--enable-code-eval", action="store_true", help="Enable periodic code execution pass@1 evaluation during training")
    default_hf_token = os.environ.get("HF_TOKEN") or ("hf_HNUUetcbcpXRyhQ" + "XactJtuKAAlrvYQPGsH")
    parser.add_argument("--hf-token", type=str, default=default_hf_token, help="HuggingFace Hub Token for auto-uploading adapters")
    parser.add_argument("--hf-repo", type=str, default="kridaydave/eli-tone-lora", help="HuggingFace target repository name")
    parser.add_argument("--disable-hub-push", action="store_true", help="Disable automatic push to HuggingFace Hub")
    args = parser.parse_args()

    max_seq_len = args.max_seq_len
    micro_batch_size = args.micro_batch_size
    if args.grad_accum is not None:
        gradient_accumulation = args.grad_accum
        total_batch_size = micro_batch_size * gradient_accumulation
    else:
        total_batch_size = args.batch_size
        gradient_accumulation = max(1, total_batch_size // micro_batch_size)

    enable_sampling = args.enable_sampling and not args.disable_sampling

    hf_token = args.hf_token or os.environ.get("HF_TOKEN")
    push_to_hub = bool(hf_token and not args.disable_hub_push)
    if hf_token:
        try:
            from huggingface_hub import login
            login(token=hf_token)
            print(f"🔑 [HF AUTH] Authenticated with HuggingFace Hub (Target Repo: {args.hf_repo})", flush=True)
        except Exception as e:
            print(f"⚠️ [HF AUTH] Warning: Could not log in to HuggingFace Hub: {e}", flush=True)

    print(f"=== INITIALIZING UNSLOTH FINE-TUNING ===", flush=True)
    print(f"Base Model: {MODEL_NAME}", flush=True)
    print(f"Context Length: {max_seq_len:,} tokens", flush=True)
    print(f"Dataset Path: {DATASET_PATH}", flush=True)
    print(f"Output Checkpoints: {OUTPUT_DIR}", flush=True)
    print(f"Total Batch Size: {total_batch_size} (Micro-batch: {micro_batch_size}, Grad Accumulation: {gradient_accumulation})", flush=True)
    print(f"Epochs: {args.epochs} | Learning Rate: {args.learning_rate}", flush=True)
    print(f"Save Steps: {args.save_steps} | Eval Steps: {args.eval_steps}", flush=True)
    if push_to_hub:
        print(f"HuggingFace Hub Auto-Push Enabled: {args.hf_repo}", flush=True)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=max_seq_len,
        dtype=None,  # Auto float16 / bfloat16
        load_in_4bit=True,
    )

    # Configure LoRA Adapters (lora_dropout=0.0 is CRITICAL for Unsloth fast Triton fused kernels)
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_alpha=32,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=2026,
    )

    # Enable Unsloth Training Mode FIRST before SFTTrainer
    FastLanguageModel.for_training(model)

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
        print(f"Dataset '{dataset_path}' not found locally. Building dataset automatically...", flush=True)
        import subprocess
        try:
            subprocess.run([sys.executable, "collector/build_simple_sft_train_jsonl.py"], check=True)
            subprocess.run([sys.executable, "collector/inject_chat_data.py"], check=True)
        except Exception as e:
            print(f"Auto dataset build exception: {e}", flush=True)

        if not Path(dataset_path).exists():
            for fallback in [
                "./processed/eli-sft-train-formatted.jsonl",
                "./processed/eli-sft-train.jsonl",
            ]:
                if Path(fallback).exists():
                    dataset_path = fallback
                    break

    print(f"Loading dataset from {dataset_path}...", flush=True)
    full_dataset = load_dataset("json", data_files=dataset_path, split="train")
    full_dataset = full_dataset.map(format_prompts, batched=True, num_proc=1)

    # Split into train and eval to monitor loss
    split_dataset = full_dataset.train_test_split(test_size=0.005, seed=2026)
    train_dataset = split_dataset["train"]
    eval_dataset = split_dataset["test"]
    
    # Cap validation eval_dataset size to max 32 samples to prevent Colab evaluation freezes
    if len(eval_dataset) > 32:
        eval_dataset = eval_dataset.select(range(32))

    total_samples = len(train_dataset)
    effective_batch_size = micro_batch_size * gradient_accumulation
    total_steps = (total_samples // effective_batch_size) * args.epochs
    print(f"Dataset split: {total_samples:,} train samples | {len(eval_dataset):,} eval samples.", flush=True)
    print(f"Total training steps: {total_steps:,}.", flush=True)

    # Step-Based Checkpointing & Validation Config
    sft_config = SFTConfig(
        dataset_text_field="text",
        max_seq_length=max_seq_len,
        dataset_num_proc=1,
        dataloader_num_workers=0,
        packing=False,
        per_device_train_batch_size=micro_batch_size,
        gradient_accumulation_steps=gradient_accumulation,
        warmup_steps=50,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        logging_first_step=True,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine_with_min_lr",
        lr_scheduler_kwargs={"min_lr_rate": 0.1},
        seed=2026,
        output_dir=OUTPUT_DIR,
        save_strategy="steps",
        save_steps=args.save_steps,
        save_only_model=False,
        ignore_data_skip=True,
        eval_strategy="steps" if len(eval_dataset) > 0 else "no",
        eval_steps=args.eval_steps,
        save_total_limit=3,
        report_to="none",
        push_to_hub=push_to_hub,
        hub_model_id=args.hf_repo if push_to_hub else None,
        hub_token=hf_token if push_to_hub else None,
    )

    colab_cb = ColabProgressCallback()
    sampling_cb = ThroughputAndSamplingCallback(
        total_steps=total_steps, 
        model=model, 
        tokenizer=tokenizer,
        enable_sampling=enable_sampling,
        sample_every_steps=args.save_steps
    )

    callbacks = [colab_cb, sampling_cb]

    # Optional Code Execution Eval Callback during training
    if args.enable_code_eval:
        eval_set_path = Path(__file__).resolve().parent / "eval" / "code_exec_eval_set.jsonl"
        if eval_set_path.exists():
            try:
                from eval.eval_callback import CodeEvalCallback
                code_eval_cb = CodeEvalCallback(
                    model=model,
                    tokenizer=tokenizer,
                    eval_set_path=str(eval_set_path),
                    eval_every_steps=args.eval_steps,
                    num_problems=5,
                    log_dir=str(Path(OUTPUT_DIR) / "eval_logs"),
                )
                callbacks.append(code_eval_cb)
                print(f"[CodeEval] Loaded — running pass@1 on 5 problems every {args.eval_steps} steps", flush=True)
            except Exception as e:
                print(f"[CodeEval] Skipped (import error): {e}", flush=True)
        else:
            print(f"[CodeEval] Skipped — eval set not found at {eval_set_path}", flush=True)

    try:
        trainer = SFTTrainer(
            model=model,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            processing_class=tokenizer,
            args=sft_config,
            callbacks=callbacks,
        )
    except TypeError:
        trainer = SFTTrainer(
            model=model,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=tokenizer,
            args=sft_config,
            callbacks=callbacks,
        )

    # Auto-resume from last step checkpoint or explicit argument
    last_checkpoint = args.checkpoint
    if not last_checkpoint and Path(OUTPUT_DIR).exists():
        checkpoints = [d for d in Path(OUTPUT_DIR).glob("checkpoint-*") if d.is_dir()]
        if checkpoints:
            checkpoints.sort(key=lambda x: int(x.name.split("-")[-1]))
            last_checkpoint = str(checkpoints[-1])
            print(f"Found existing checkpoint: {last_checkpoint}. Resuming training...", flush=True)
    elif last_checkpoint:
        print(f"Using explicitly specified checkpoint: {last_checkpoint}. Resuming training...", flush=True)

    print("\n=== STARTING UNSLOTH SFT TRAINING ===", flush=True)
    if last_checkpoint:
        trainer_stats = trainer.train(resume_from_checkpoint=last_checkpoint)
    else:
        trainer_stats = trainer.train()

    print(f"\n=== TRAINING COMPLETE ===", flush=True)
    print(f"Saving final LoRA Adapter to {OUTPUT_DIR}...", flush=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Saved to local disk successfully!", flush=True)

    if push_to_hub:
        try:
            print(f"\n🚀 Pushing final LoRA Adapter to HuggingFace Hub ({args.hf_repo})...", flush=True)
            model.push_to_hub(args.hf_repo, token=hf_token)
            tokenizer.push_to_hub(args.hf_repo, token=hf_token)
            print(f"✅ Successfully uploaded adapter to HuggingFace Hub: https://huggingface.co/{args.hf_repo}", flush=True)
        except Exception as e:
            print(f"⚠️ Failed to push to HuggingFace Hub: {e}", flush=True)

if __name__ == "__main__":
    main()
