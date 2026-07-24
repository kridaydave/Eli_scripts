---
name: sft-dataset-and-trainer-guardrails
description: Best practices for fine-tuning LLMs with SFTTrainer and Unsloth. Covers dataset length auditing, ignore_data_skip resumption, VRAM defragmentation, and checkpoint frequency.
---

# SFT Dataset & Trainer Guardrails

When configuring SFT fine-tuning scripts (e.g., with Unsloth or Hugging Face TRL):

## 1. Dataset Length & Quality Auditing
- **Percentile-Based Context Capping**: Compute sequence length percentiles (p50, p90, p95, p99) before training. Cap `MAX_SEQ_LENGTH` at p99.9 (e.g., 16,384 tokens) to prevent VRAM memory spikes from extreme outlier samples (>30,000 tokens) during multi-step gradient accumulation.
- **Dataset Sanity Checks**: Audit dataset files for unrendered internal generator notes (e.g., `"[Review the diagram...]"`), missing root `"id"` fields, or raw `<thought>` tag leakage before starting training.

## 2. Checkpoint Resumption & RAM Leak Prevention
- **`ignore_data_skip=True`**: Always set `ignore_data_skip=True` in `SFTConfig` / `TrainingArguments` when resuming training from a checkpoint. Without this, Hugging Face `SFTTrainer` fast-forwards thousands of batches through CPU RAM on startup, causing system RAM exhaustion and SIGKILL (`^C`) process kills.

## 3. Cloud Notebook Reliability & Defragmentation
- **Granular Save Intervals**: Use `save_steps=50` for frequent checkpointing in preemptible or interactive cloud notebook environments (Google Colab / Kaggle).
- **Proactive CUDA Cache Cleanup**: Trigger `torch.cuda.empty_cache()` and `gc.collect()` every 10 steps in custom `TrainerCallback` instances to prevent VRAM fragmentation accumulation.
