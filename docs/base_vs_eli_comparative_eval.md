# Deep Comparative Evaluation Report: Base Model (Qwen3-4B) vs Eli LoRA ()

## Executive Summary & Quantitative Overview

| Benchmark Set | Total Problems | Base Passed | Base Pass@1 | Eli LoRA Passed | Eli Pass@1 | Pass@1 Delta |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **STANDARD** | 65 | 32 | 49.23% | 10 | 15.38% | **-33.85%** |
| **OOD** | 50 | 13 | 26.00% | 5 | 10.00% | **-16.00%** |
| **NIGHTMARE** | 48 | 23 | 47.92% | 3 | 6.25% | **-41.67%** |

## Shift Category Analysis

- 🟢 **Preserved Passes (Base ✓, Eli ✓)**: 16
- 🔵 **Recovered Passes (Base ❌, Eli ✓)**: 2
- 🔴 **Catastrophic Regressions (Base ✓, Eli ❌)**: 52
- ⚪ **Shared Failures (Base ❌, Eli ❌)**: 93

### Recovered Passes (Base Failed -> Eli Passed)
- **py_034** (standard): Base failed (ASSERTION_FAILED:), Eli passed!
- **ood_sys_03** (ood): Base failed (RUNTIME_ERROR: NameError: name 'simulate_allocator' is not defined), Eli passed!