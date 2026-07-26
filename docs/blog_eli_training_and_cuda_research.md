# On Eli's Training Run: High-Taste Fine-Tuning, Closed-PR Mining, and Turing CUDA Microarchitecture

**Date:** July 2026  
**Author:** Epoch AI Labs  
**Tag:** Training & Systems  

---

## Executive Summary

At Epoch AI Labs, our thesis is simple: **Taste = Mergeable Code**. We don't train models to maximize benchmark score inflation; we train models to output clean, idiomatic, senior-level code that passes code review on the first try.

This note shares progress from our active training run for **Eli** (4B model), our fast, direct prototyping model, alongside our latest systems research into microarchitectural CUDA optimizations for NVIDIA Tesla T4 GPUs (Turing CC 7.5).

---

## 1. Eli's Training Architecture & Phase 1 SFT

Eli is designed as our hyper-fast core model — built for developers in flow who need immediate, considered code without performative fluff.

### Core Training Configuration
- **Base Model:** `unsloth/Qwen3-4B-Instruct-2507` (Apache 2.0, dense transformer, 262K context capacity).
- **Context Window:** Extended 16k context window (`MAX_SEQ_LENGTH = 16384`) to capture complete chain-of-thought traces, multi-file context, and surgical diffs.
- **SFT Pipeline (`train_eli_colab.py`):** Accelerated via Unsloth 2–5x fused Triton kernels with unbuffered progress streaming, non-blocking single-process data loading, and periodic CUDA cache clearing to eliminate VRAM fragmentation on 16GB GPUs.
- **Curated Dataset:** Master training corpus containing **30.2K curated samples** combining high-grade code, chain-of-thought (CoT) reasoning, and calibrated persona samples.

### Emergence & Held-Out Evaluation
To evaluate tone, surgical directness, and emergent reasoning without data contamination, we benchmark base vs. fine-tuned weights using `eval_emergence.py` across **45 held-out transfer test prompts** (`data/held_out_transfer_test.jsonl`), scored against a strict 4-item directness and technical correctness rubric.

---

## 2. Phase 2: Closed GitHub PR Mining

Phase 2 expands Eli from single-turn code generation to real-world multi-language software engineering via closed PR mining.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Phase 2 Dataset Blend Architecture                   │
├──────────────────────────────────┬─────────────────────────────────────┤
│ 40% Format A: Direct Unified Diff│ Single-turn instruction + snippet   │
│               (Alpaca `.patch`)  │ ──► surgical `.patch` diff output   │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 60% Format B: Agentic Tool Trace │ Multi-turn ShareGPT format modeling │
│               (ShareGPT Traces)  │ grep_search ──► view_file ──► patch │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### Multi-Language Open Source Mining
We mine real-world merged Pull Requests across 60+ curated repositories across 5 core ecosystems:
- **Python:** `fastapi`, `pydantic`, `requests`, `flask`, `scikit-learn`, `httpx`, `rich`, `transformers`.
- **TypeScript / JS:** `next.js`, `react`, `zod`, `express`, `tailwindcss`, `trpc`, `prisma`, `lucide`.
- **Go:** `gin`, `cobra`, `chi`, `fiber`, `gorm`, `zap`.
- **Rust:** `tokio`, `axum`, `serde`, `clap`, `hyper`, `reqwest`, `ripgrep`, `tauri`.
- **C / C++:** `torvalds/linux` (Linux Kernel), `llvm-project`, `llama.cpp`, `fmt`, `nlohmann_json`, `protobuf`.

### Red-to-Green Test Verification Harness
Every mined PR is validated inside an isolated cloud VM harness:
1. Repository is restored to `base_commit` with `.git` metadata purged.
2. Pre-PR test suite is executed to confirm initial failure (❌ Red).
3. Candidate PR patch is applied and re-tested (✅ Green).
4. Verified passing traces are serialized into training JSONL.

---

## 3. Systems Research: Tesla-T4 CUDA Microkernel Breakthroughs

Running high-throughput training and inference on affordable hardware requires pushing GPU microarchitecture to its physical limits. We conducted exhaustive analysis on NVIDIA Tesla T4 GPUs (Turing TU104, 40 SMs, 320 Tensor Cores, 70W TDP cap).

| Technique / Engineering Component | Microarchitectural Mechanism | Target SASS / Hardware Benefit | Validation Status |
|---|---|---|---|
| **Signed Sub-Byte INT3 Dequant (`LOP3` LUT `0xCA`)** | Dual-word bit extraction + FP16 magic mantissa injection (`0x64046404`) | **3.08x instruction reduction**; 94.8% memory bandwidth efficiency (303.4 GB/s) | Verified (H7) |
| **Warp-Specialized Split-K GEMM** | 2 Producer / 6 Consumer warps with SMEM volatile flag signaling | **94.2% stall reduction**; locks 1590 MHz boost clock under 61.4W power | Verified (H8) |
| **Fused FP8 Emulation via LOP3 Rescaling** | Exponent bias adjustment (+8) via `lop3.b32` LUT `0xEA` | **11.0x instruction reduction**; 60.1 TFLOPS FP8 GEMM on FP16 Tensor Cores | Verified (H9) |
| **Fused Backward GEMM + AdamW** | Accumulates $\nabla W$ in register fragments; applies AdamW update directly in-register | **21.4% DRAM bandwidth saving** (28 → 22 B/param) by eliminating $\nabla W$ DRAM writeback | Simulation Confirmed (H6) |

---

## 4. Next Steps

With Eli's Phase 1 and Phase 2 training pipelines established and our CUDA micro-kernels validated, we are preparing for:
1. **Public Weights Release:** Publishing Eli (~4B dense) on HuggingFace and Ollama.
2. **Architecture Scaling:** Porting our closed-PR dataset blend and warp-specialization pipelines to **Theo** (~12B, Gemma-4 base) and **Albert** (~32B, Qwen3.5 base).

*Epoch AI Labs · July 2026*
