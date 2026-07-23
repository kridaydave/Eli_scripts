# ELi v3 Fine-Tuning & Emergence Eval — Next Steps Guide

## Executive Summary & Status

All data repair, certainty calibration, fuzzy deduplication, and target-weighted dataset interleaving tasks (P0–P4) are **100% complete, verified, and sealed**.

The master training corpus is ready for launch on Google Colab or Kaggle.

---

## Completed Dataset Specifications

- **Master SFT Training File (Alpaca):** [processed/eli-sft-train.jsonl](file:///home/kriday/Desktop/epoch-1/processed/eli-sft-train.jsonl) (**24,792 pairs**, 49.39 MB)
- **Formatted SFT File (ShareGPT):** [processed/eli-sft-train-formatted.jsonl](file:///home/kriday/Desktop/epoch-1/processed/eli-sft-train-formatted.jsonl) (**24,792 pairs**, 51.09 MB)
- **Standalone Code Review Train File:** [processed/train_code_review.jsonl](file:///home/kriday/Desktop/epoch-1/processed/train_code_review.jsonl) (**150 pairs**, emergence test set)
- **Wiseness Corpus:** [processed/training-data-eli-wiseness.jsonl](file:///home/kriday/Desktop/epoch-1/processed/training-data-eli-wiseness.jsonl) (**682 pairs**, 4-cell grid, multi-domain & 5 structural frames)
- **Cross-Axis Emergence Corpus:** [processed/training-data-eli-cross-axis.jsonl](file:///home/kriday/Desktop/epoch-1/processed/training-data-eli-cross-axis.jsonl) (**410 pairs**, includes 60 user-pushback calibrated disagreement pairs)
- **Clean Stack v2 Code Corpus:** [processed/raw_stack_v2_mined.jsonl](file:///home/kriday/Desktop/epoch-1/processed/raw_stack_v2_mined.jsonl) (**7,292 pairs**, MinHash 4-gram fuzzy near-duplicates pruned)

### Target-Weighted Batch Composition (Epoch 1 Interleaved)

| Module | Count | Multiplier | Upsampled Count | Batch % | Role |
|---|---|---|---|---|---|
| **Mined Stack v2 Code** | 7,292 | $1\times$ | 7,292 | **29.4%** | Gold single-axis code |
| **FABLE 5 Agentic CoT** | 8,530 | $1\times$ | 8,530 | **34.4%** | Multi-turn reasoning traces |
| **Repaired Wiseness** | 682 | $5\times$ | 3,410 | **13.8%** | Decoupled certainty & register calibration |
| **Persona / Voice** | 155 | $20\times$ | 3,100 | **12.5%** | Authentic founder Q&A voice |
| **Cross-Axis & Pushback** | 410 | $6\times$ | 2,460 | **9.9%** | Multi-pillar emergence & disagreement |
| **Total** | **17,069** | — | **24,792** | **100.0%** | **Uniformly shuffled from Epoch 1** |

---

## Action Plan for New Chat

### Step 5: Model Training Execution (Colab / Kaggle)

Run the one-click launch script on Kaggle or Colab (Nvidia T4 / P100 / L4 GPU):

```bash
bash setup_colab.sh
```

Or run step-by-step:

```bash
# 1. Build master target-weighted dataset
python3 collector/build_simple_sft_train_jsonl.py

# 2. Launch Unsloth fine-tuning (Qwen3-4B-Instruct base, r=16, alpha=32, max_seq_len=49152, save_steps=250)
python3 train_eli_colab.py
```

#### Training Runtime & Checkpointing Mechanics
- **Total Steps:** 9,297 steps (24,792 samples $\div$ 8 effective batch size $\times$ 3 epochs).
- **Context Window:** 49,152 tokens (48k context for long FABLE-5 CoT reasoning traces).
- **Throughput:** ~4.82s / step ($\sim 12.4$ total wall-clock hours).
- **Planned Session Structure (Kaggle):**
  - **Session 1:** Steps 0 $\rightarrow$ ~7,750 (~10.4 hours). Saves checkpoints every 250 steps to `./models/eli-tone-lora/checkpoint-7750`.
  - **Session 2:** Auto-resumes from `checkpoint-7750` $\rightarrow$ step 9,297 (~2 hours).

---

### Step 6: Post-Training Emergence Evaluation

Once training completes and adapter weights are saved to `./models/eli-tone-lora`:

```bash
python3 eval_emergence.py --lora_path ./models/eli-tone-lora
```

This runs inference against the **45 zero-leakage held-out prompts** in `data/held_out_transfer_test.jsonl` and outputs `processed/emergence_eval_results_lora.json`.

#### Checklist Rubric Scoring (4 Fields per Example)
1. `score_directness_matches_stakes`: Does high-stakes output use `pure-direct` (no fluff/jokes)?
2. `score_hedging_matches_certainty`: Does low/medium certainty output offer diagnostic steps / candidate causes rather than single confident fixes?
3. `score_no_register_bleed`: Is snark/wit restricted to low-stakes scenarios?
4. `score_distinguishes_grid_cell`: Does the response accurately reflect the specific $2 \times 2$ grid cell context?
