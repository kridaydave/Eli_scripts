# Eli Retraining Plan (Phase 1 & Phase 2 Blueprint)

> **Goal**: Retrain Eli from scratch on Qwen3-4B-Instruct using a clean, 3-pillar dataset mix (Core Coding, Terminal Ops, Defensive Security) to eliminate format contamination, tool-call hallucinations, and function renaming errors.

---

## Executive Summary of Strategy Pivot

### Why We Retrain From Scratch
The initial Phase 1 training run (using Fable-5 trajectory data) caused severe format collapse:
- **XML Tag Contamination**: Outputting `<name>Eli</name>`, `<action>`, `<task>` tags instead of clean code.
- **Tool-Call Hallucinated Traces**: Generating mock terminal outputs and mock file-system operations.
- **Function Renaming**: Changing function names requested by evaluation prompts (e.g. `is_point_in_bbox` $\rightarrow$ `point_in_box`).
- **Language Drift**: Randomly generating JavaScript/C++ when Python was requested.

### New Core Principle
**No synthetic trajectory/tool-call copying.** The model will generate pure code and clean `<think>` blocks, relying on its own native reasoning capacity.

---

## 3-Pillar Dataset Architecture & Final Selections

```
                                  ┌───────────────────────────────────────────┐
                                  │          ELI TRAINING CURRICULUM          │
                                  └───────────────────────────────────────────┘
                                                        │
         ┌──────────────────────────────────────────────┼──────────────────────────────────────────────┐
         ▼                                              ▼                                              ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐              ┌──────────────────────────────┐
│  Pillar 1: Core Coding       │              │  Pillar 2: Terminal & Shell  │              │  Pillar 3: Defensive Security│
│  & Algorithms (60%)          │              │  Operations (20%)            │              │  & Code Repair (20%)         │
└──────────────────────────────┘              └──────────────────────────────┘              └──────────────────────────────┘
  • Dataset: The Stack v3                       • 40% NL2Bash (`baisang/nl2bash`)              • 50% PrimeVul / Big-Vul
  • Focus: Python, TS/JS, C++,                  • 40% The Stack v3 Shell/Zsh/PS                • 40% SecCodePLT / CyberSecEval
    Go, Rust                                    • 20% Sysadmin/Git Troubleshooting             • 10% Synthetic Threat Auditing
  • Method: Docstring &                           CLI pipelines, POSIX scripts,                  Memory safety & web security
    signature extraction for                      `strace`, `lsof`, `journalctl`                 patches (C/C++, Python, JS, Go)
    exact function name adherence
```

---

## Detailed Pillar Specifications

### Pillar 1: Core Coding & Production Software (60%)
- **Primary Source**: `bigcode/the-stack-v3`
- **Languages**: Python (40%), TypeScript/JavaScript (25%), C/C++ (15%), Go (10%), Rust (10%).
- **Processing Method**: Docstring and signature extraction. Convert raw functions into problem-solution pairs where the user prompt contains the docstring/signature, and the target response contains the exact implementation. This guarantees **100% function signature alignment**.
- **Formatting Standard**:
  ```markdown
  ### User:
  [Problem description + exact function signature]

  ### Assistant:
  <think>
  [Native algorithmic reasoning]
  </think>

  ```python
  [Clean, executable code adhering strictly to the function name]
  ```
  ```

---

### Pillar 2: Terminal Navigation & Shell Operations (20%)
- **Primary Sources**:
  1. `baisang/nl2bash` (40%): Natural language to clean CLI pipelines (`find`, `grep`, `sed`, `awk`, `xargs`).
  2. `bigcode/the-stack-v3` Shell Subset (40%): Production Bash, Zsh, and PowerShell automation scripts with `set -euo pipefail`.
  3. Synthetic Sysadmin & Troubleshooting (20%): Environment setup, Git workflows (`bisect`, `rebase`), and system diagnostics (`htop`, `strace`, `lsof`, `journalctl`).
- **Formatting Standard**:
  ```markdown
  ### User:
  Write a robust Bash script to recursively find all `.log` files older than 7 days, compress them into `.tar.gz`, and remove the originals with error handling.

  ### Assistant:
  <think>
  [Script design: error handling with set -euo pipefail, finding files safely]
  </think>

  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  ...
  ```
  ```

---

### Pillar 3: Defensive Security & Code Repair (20%)
- **Primary Sources**:
  1. `primevul/primevul` & `mEmp/Big-Vul` (50%): Real-world C/C++ CVE commits with before-and-after vulnerability diffs (Buffer Overflows, Use-After-Free, Double Free, Memory Leaks).
  2. `meta-llama/CyberSecEval` / `SecCodePLT` (40%): Web & API security vulnerability pairs (SQLi, XSS, SSRF, Path Traversal, Auth bypass) in Python, JS, C#, and Go.
  3. Synthetic Threat Modeling & Auditing (10%): Code review prompts ("Audit this code for vulnerabilities, explain the flaw, and output a secure zero-regression patch").
- **Formatting Standard**:
  ```markdown
  ### User:
  Analyze the following function for security vulnerabilities, explain the flaw, and provide a secure patched version.

  [Vulnerable Code Snippet]

  ### Assistant:
  <think>
  1. Root cause analysis: Identify vulnerability.
  2. Explain exploit mechanism.
  3. Formulate safe patch preserving original API contract.
  </think>

  [Detailed explanation]

  ```[language]
  [Secure Patched Code]
  ```
  ```

---

## Quality Control & Automated Sanitization Filters

To prevent repeating Phase 1 trajectory errors, all dataset entries must pass 4 automated filters during compilation:

1. **NO Trajectory Tags**: Strip all `<action>`, `<command>`, `<task>`, `<file>`, and profile XML metadata.
2. **Exact Signature Check**: Verify that the function name in the response target matches the requested function name in the prompt.
3. **Language Match Filter**: Ensure code block language tags (`python`, `bash`, `c`, `javascript`) strictly match the requested prompt language.
4. **Clean Block Formatting**: Ensure every output contains at most one `<think>` block followed by clean code/script blocks.

---

## Action Plan & Roadmap

- [ ] **Step 1: Baseline Benchmark**: Complete base `unsloth/Qwen3-4B-Instruct-2507` evals across all 3 sets (`run_all_eli_evals.py`) to establish baseline Pass@1 targets.
- [ ] **Step 2: Dataset Compilation Script**: Develop `scripts/prepare_eli_dataset.py` to pull, filter, format, and merge the 3 pillars into `kridaydave/eli-phase1-clean`.
- [ ] **Step 3: Training Config Setup**: Configure Unsloth SFT script for Qwen3-4B base, LoRA rank $r=32$, $\alpha=64$, learning rate $2 \times 10^{-4}$, max sequence length 4096.
- [ ] **Step 4: Clean Phase 1 Training**: Execute training run.
- [ ] **Step 5: Full Evaluation**: Run `run_all_eli_evals.py` on new checkpoint to compare against base model benchmark.
