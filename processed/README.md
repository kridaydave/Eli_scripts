---
license: apache-2.0
pretty_name: Epoch Eli Dataset v3 — S-Tier Coding & Agentic Fine-Tuning Corpus
language:
- en
task_categories:
- text-generation
tags:
- code
- agentic-coding
- sharegpt
- alpaca
- vision-language
- qwen
- epoch
---

# Epoch Model Suite 1 — Eli Dataset v3

Dataset curated for fine-tuning **Eli** (pure dense 4B Transformer, Qwen 3-4B base).

## Dataset Composition & Breakdown

- **Alpaca Single-Turn Base Dataset (`training-data.jsonl`)**: **15,328** S-Tier pairs
  - **Backend Code (`github_backend`)**: 9,011 pairs (58.8%)
  - **Frontend Code & Design Systems (`github_frontend`)**: 4,906 pairs (32.0%)
  - **Eli Personality & Voice (`eli_personality`)**: 1,738 pairs (11.3%)
  - **Custom Cross-Axis Joint Emergence (`eli_cross_axis_emergence`)**: 350 pairs (2.3%)
- **Master SFT Train Corpus (`eli-sft-train.jsonl`)**: **16,357** curriculum-sorted pairs
  - **Mined Stack v2 Real Gold Code**: 7,451 pairs
  - **FABLE 5 Agentic CoT Reasoning Traces**: 8,530 pairs
  - **Custom Cross-Axis Joint Emergence**: 350 pairs
  - **User Custom Answers & Personality**: 26 pairs
- **Deep Agentic Multi-Turn Sessions (`training-data-sharegpt.jsonl`)**: **1,200** sessions (6–10 turns each)
- **Eli-VL Multimodal (`training-data-eli-vl.jsonl`)**: **192** UI WebP screenshot-to-code pairs
- **Held-Out Emergence Test Suite (`data/held_out_transfer_test.jsonl`)**: **45** zero-leakage evaluation prompts

## Primary Dataset Files

- [training-data.jsonl](file:///home/kriday/Desktop/epoch-1/processed/training-data.jsonl): Single-turn Alpaca format (`instruction`, `output`).
- [eli-sft-train.jsonl](file:///home/kriday/Desktop/epoch-1/processed/eli-sft-train.jsonl): Curriculum-sorted SFT master training set.
- [training-data-sharegpt.jsonl](file:///home/kriday/Desktop/epoch-1/processed/training-data-sharegpt.jsonl): Multi-turn ShareGPT format (`conversations`).
- [training-data-eli-cross-axis.jsonl](file:///home/kriday/Desktop/epoch-1/processed/training-data-eli-cross-axis.jsonl): Multi-pillar joint emergence prompts.
- [dataset-stats.json](file:///home/kriday/Desktop/epoch-1/processed/dataset-stats.json): Automated dataset telemetry.
