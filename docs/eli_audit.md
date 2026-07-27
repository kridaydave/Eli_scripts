# Diagnostic Failure & Weakness Audit (`eli_audit.md`)

This plan outlines a comprehensive, systematic audit to pinpoint exactly **where, why, and how** Eli fails across standard coding, out-of-distribution (OOD) tasks, and complex algorithmic/system challenges.

---

## Benchmark Matrix & Empirical Execution Auditing
We evaluate performance across all 3 benchmark suites available in `/eval/`:

1. **Standard Code Exec Eval ([code_exec_eval_set.jsonl](file:///home/kriday/Desktop/epoch-1/eval/code_exec_eval_set.jsonl)):**
   - 65 problems (Easy / Medium / Hard).
   - Measures core Python/C/Go function synthesis & parameter matching.
2. **Out-of-Distribution (OOD) Benchmark ([ood_coding_eval_set.jsonl](file:///home/kriday/Desktop/epoch-1/eval/ood_coding_eval_set.jsonl)):**
   - 50 domain-specific & algorithmic problems (Computational Geometry, Bitwise, Systems, Cron, Graph algorithms).
   - Identifies catastrophic forgetting and signature mismatch issues.
3. **Nightmare Hard Benchmark ([nightmare_eval_set.jsonl](file:///home/kriday/Desktop/epoch-1/eval/nightmare_eval_set.jsonl)):**
   - 48 extreme-difficulty problems (Advanced DP, Tarjan SCC, Min-Cost Flow, Segment Trees, CRT, Consistent Hashing).
   - Exposes upper-bound algorithmic reasoning and multi-step state management failures.

---

## Error Taxonomy & Categorization

Every failed test across all benchmark runs is categorized into five primary error buckets to identify root causes:

| Error Category | Diagnostic Criteria | Root Cause Hypothesis |
| :--- | :--- | :--- |
| **1. Extraction / Wrapper Failure** | Model responds in JSON tool-call format, raw un-fenced text, or missing `<think>` block cleanups (`CODE_EXTRACTION_FAILED`). | Tone/Format SFT overfitted to agentic tool-call templates instead of direct code generation. |
| **2. Signature & Name Mismatch** | `NameError` or `TypeError: function missing required positional arguments`. | Prompt-following degradation; model invents custom function/variable names instead of exact prompt entry points. |
| **3. Algorithmic / Logical WA** | Function executes without runtime errors but fails `assert` checks (Wrong Answer). | Pure algorithmic reasoning capacity bottleneck (e.g., incorrect DP state transition, greedy flaw). |
| **4. Edge Case & Boundary Failure** | Passes basic inputs, fails on empty inputs `[]`, single element `[1]`, or boundary values (`0`, `-1`, `MAX_INT`). | Insufficient edge-case coverage in instruction fine-tuning dataset. |
| **5. Time / Memory Limit Exceeded** | `TimeoutError` or Process Timeout (>10s). | Inefficient time complexity ($O(N^2)$ brute force instead of $O(N \log N)$ or $O(N)$). |

---

## Remedial Action & Recommendations

Based on the empirical audit results:

- **Format / Signature Mismatches (Types 1 & 2):**
  - Adjust SYSTEM PROMPT in evaluation harness & inference scripts.
  - Update dataset chat template to enforce standard python markdown code blocks.
- **Logical WA & Edge Cases (Types 3 & 4):**
  - Blend 25% execution-verified algorithmic dataset ([`raw_stack_v2_mined.jsonl`](file:///home/kriday/Desktop/epoch-1/processed/raw_stack_v2_mined.jsonl)) into training.
- **LoRA Regression vs. Base Model:**
  - Reduce LoRA learning rate (`2e-4` $\rightarrow$ `5e-5`).
  - Tune LoRA alpha / target modules to preserve base Qwen3-4B coding knowledge.

---

## Execution Commands

Run the audit suite locally in the project directory:

```bash
# 1. Audit Standard Code Eval
python eval/run_code_eval.py --base_model unsloth/Qwen3-4B-Instruct-2507 --lora_path ./models/eli-tone-lora --eval_set eval/code_exec_eval_set.jsonl --output processed/audit_code_exec.json

# 2. Audit OOD Benchmark
python eval/run_code_eval.py --base_model unsloth/Qwen3-4B-Instruct-2507 --lora_path ./models/eli-tone-lora --eval_set eval/ood_coding_eval_set.jsonl --output processed/audit_ood.json

# 3. Audit Nightmare Benchmark
python eval/run_code_eval.py --base_model unsloth/Qwen3-4B-Instruct-2507 --lora_path ./models/eli-tone-lora --eval_set eval/nightmare_eval_set.jsonl --output processed/audit_nightmare.json
```
