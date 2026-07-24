# Phase 2: Closed PR & Multimodal UI/UX Training Specification

---

## Executive Summary

Phase 2 expands the ELi model suite from single-turn text/code reasoning to **real-world multi-language software engineering and native multimodal UI/UX design taste**. 

This phase trains models on real-world merged GitHub Pull Requests across 5 core programming languages and integrates Google DeepMind's **SigLIP 2** Vision Encoder for visual UI/UX criticism and screenshot-to-code generation.

---

## 1. Multi-Language Scope & Whitelisted Repositories

Mining targets ~60 curated, high-star open-source repositories across 5 primary ecosystems:

| Language | Ecosystem / Libraries | Test Runner | Whitelisted Example Repositories |
|---|---|---|---|
| **Python** | `FastAPI`, `Pydantic`, `Flask`, `Requests` | `pytest` | `fastapi`, `pydantic`, `requests`, `flask`, `scikit-learn`, `httpx`, `rich`, `click`, `sqlalchemy`, `celery`, `pytest`, `transformers` |
| **TypeScript / JS** | `React`, `Next.js`, `Zod`, `Express` | `jest` / `vitest` | `next.js`, `react`, `zod`, `axios`, `express`, `tailwindcss`, `trpc`, `tanstack-table`, `prisma`, `nestjs`, `lucide` |
| **Go** | `gin`, `cobra`, `chi`, `fiber` | `go test` | `gin`, `cobra`, `chi`, `fiber`, `gorm`, `zap`, `cli`, `moby`, `net`, `logrus` |
| **Rust** | `tokio`, `axum`, `serde`, `clap` | `cargo test` | `tokio`, `axum`, `serde`, `clap`, `hyper`, `reqwest`, `ripgrep`, `actix-web`, `tauri`, `sqlx` |
| **C / C++** | `Linux Kernel`, `LLVM`, `Llama` | `KUnit` / `ctest` / `gtest` | **`torvalds/linux` (Linux Kernel)**, `llvm-project`, `llama.cpp`, `fmt`, `nlohmann_json`, `spdlog`, `googletest`, `benchmark`, `abseil-cpp`, `protobuf`, `opencv` |

---

## 2. Dataset Formats & Blend Ratio (Option 2)

The master Phase 2 training corpus follows a **30 / 50 / 20** format blend:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Phase 2 Dataset Blend Architecture                   │
├──────────────────────────────────┬─────────────────────────────────────┤
│ 30% Format A: Direct Unified Diff│ Single-turn instruction + snippet   │
│               (Alpaca `.patch`)  │ ──► surgical `.patch` diff output   │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 50% Format B: Agentic Tool Trace │ Multi-turn ShareGPT format modeling │
│               (ShareGPT Traces)  │ grep_search ──► view_file ──► patch │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 20% Format C: Multimodal UI/UX   │ Vision-augmented UI critique &      │
│               (Eli-VL Vision)    │ screenshot inspo ──► TSX + Tailwind │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### Multimodal Format C Details
1. **Visual Taste & Design Critique ("Describe & Why It's Good Taste"):**
   - **Input:** `<image>` screenshot of high-taste dashboard/UI component.
   - **Output:** Structured design explanation analyzing visual hierarchy, OKLCH color tokens, 4px/8px grid alignment, and typography taste.
2. **Screenshot Inspo $\rightarrow$ Executable Code $\rightarrow$ Rendered Page:**
   - **Input:** Design mockup or inspiration screenshot.
   - **Output:** Clean React / TSX + Tailwind component code.
   - **Verification:** Automatically compiled and rendered via Playwright harness, scored against WCAG AA contrast & layout checklist heuristics.

---

## 3. Anti-Cheating & Integrity Safeguards

1. **Runtime Tool-Use Sanitization:**
   - Complete removal of `.git`, `.github`, `.gitmodules`, `CHANGELOG.md`, and inline commit metadata from target workspace snapshots before mounting into model context.
2. **Pre-Training Memorization Prevention (Eval Set Isolation):**
   - Evaluation benchmark PRs are sourced exclusively from PRs merged **after the base model pre-training cutoff date** to guarantee zero data leakage.

---

## 4. Red-to-Green Test Verification Engine (Cloud VM Harness)

For every candidate PR:

```
Restore Repo to base_commit ──► Purge .git Metadata ──► Execute Pre-PR Test Suite (Assert FAIL ❌)
                                                                  │
                                                                  ▼
Apply Candidate PR Patch ──► Re-run Test Suite (Assert PASS ✅) ──► Serialize to JSONL
```

### Cloud VM Execution Strategy (Colab / Kaggle / Linux VM)
- **Engine:** Native VM subprocess execution pool (`concurrent.futures.ProcessPoolExecutor`).
- **Isolation:** Fast temporary directory mounting (`/tmp/epoch_sandbox/pr_XXXX`) with automatic cleanup.
- **Timeout Protection:** 60-second strict process timeout per test execution to prevent hanging suites or infinite loops.
- **Tooling:** Uses `uv` (Python), system `node/npm` (TypeScript), `go` (Go), `cargo` (Rust), and `cmake` (C++).

---

## 5. Vision Encoder Integration Architecture (Eli-VL)

### Selected Encoder: **Google DeepMind `SigLIP 2` (`google/siglip2-so400m`)**
- **NaFlex Engine:** Preserves native aspect ratios ($1920 \times 1080$, $1024 \times 768$) with flexible sequence lengths, eliminating thumbnail distortion.
- **Sub-Pixel Legibility:** Captures fine-grained font typography, subtle borders, and micro-layout elements essential for UI design.
- **Parameters:** 400M params (high throughput, zero latency overhead).

### Projection Adapter Architecture
```python
import torch
import torch.nn as nn

class EliVisionProjector(nn.Module):
    """Projects SigLIP 2 patch tokens (1152-dim) to ELi hidden state (2560-dim)."""
    def __init__(self, vision_dim=1152, llm_dim=2560):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(vision_dim, llm_dim),
            nn.GELU(),
            nn.Linear(llm_dim, llm_dim)
        )
    def forward(self, x):
        return self.proj(x)
```

### 2-Stage Training Protocol
1. **Stage 1 (Projection Alignment - 1.5 hrs):**
   - ❄️ Freeze SigLIP 2 & ELi LLM backbone.
   - 🔥 Train **ONLY** `EliVisionProjector` on 2,000 UI screenshot-caption pairs (`processed/training-data-eli-vl.jsonl`).
2. **Stage 2 (Joint SFT Fine-Tuning):**
   - 🔥 Train `EliVisionProjector` + 🔥 Train ELi LLM LoRA adapters ($r=16, \alpha=32$).
   - Train on Phase 2 Format C dataset (UI taste critiques + Playwright-rendered screenshot-to-code pairs).

---

*Epoch Model Suite 1 · Phase 2 Closed PR & Multimodal Specification · 2026-07-24*
