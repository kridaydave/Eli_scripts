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

Dataset curated for fine-tuning **Eli** (~3-7B dense coding model, based on Qwen 3-4B).

## Dataset Composition

- **Total S-Tier Samples**: 23,138 pairs
- **Backend Code (40.5%)**: 9,360 clean pairs across Linux, Kubernetes, Tokio, FastAPI, Hyper, Gin.
- **Frontend Code & Design Systems (22.9%)**: 5,290 pairs across shadcn/ui, Radix, Mantine, Tailwind, Stripe, Vercel, Apple HIG specs.
- **Eli Personality (30.2%)**: 6,988 pairs (1,747 unique Q&As oversampled 4x) capturing Eli's casual, direct, fluff-free persona.
- **Fable-5 Pi Agent Traces (4.3%)**: 1,000 real agentic execution traces (CoT reasoning, Bash/Read/Edit actions).
- **Agentic Open-Ended Apps (2.2%)**: 500 unique single-file apps and microservices.
- **Eli-VL Multimodal**: 192 UI WebP screenshot-to-code pairs (`training-data-eli-vl.jsonl`).

## Files Included

- `training-data.jsonl`: Alpaca format (`instruction`, `output`).
- `training-data-sharegpt.jsonl`: ShareGPT / ChatML format (`conversations`).
- `training-data-eli-vl.jsonl`: Multimodal screenshot-to-code pairs.
- `dataset-stats.json`: Automated statistical breakdown.
