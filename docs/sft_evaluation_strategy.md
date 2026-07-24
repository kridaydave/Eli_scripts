# Eli SFT Fine-Tuning Diagnostic & Evaluation Strategy

## Executive Summary
This document establishes the empirical evaluation framework, root-cause diagnostic findings, decision matrix, and dataset rebalancing strategy for fine-tuning **Eli** (`unsloth/Qwen3-4B-Instruct-2507`).

---

## 1. Initial Diagnostic & Root-Cause Analysis (Step 500 Checkpoint)

During initial training inspection at Step 500:
* **Training Loss**: Decreased smoothly from `2.295` (Step 20) to `0.912` (Step 500).
* **Validation Loss**: `eval_loss = 1.216` at Step 250.
* **Pass@1 Score**: `0% (0/10)` on periodic execution eval.

### Root-Cause Diagnosis
1. **Format Mismatch**: 7/10 failures were caused by `CODE_EXTRACTION_FAILED`, not algorithmic execution errors.
2. **Tool-Call Dominance**: FABLE 5 agentic traces comprise **34.4% (8,530 pairs)** of the total 24,792 SFT dataset. Prompts like `"write a python script..."` caused the model to reach for agentic bash tool wrappers (e.g., `Action (Bash): cat > /tmp/script.py << 'EOF'...`).
3. **Regex Extraction Limitation**: The original eval extraction function strictly expected fenced ` ```python ` blocks or top-level `def function_name` definitions, missing code escaped inside JSON/heredoc strings.

---

## 2. Updated Code Extractor & Diagnostic Tracking

The evaluation runner ([eval/run_code_eval.py](file:///home/kriday/Desktop/epoch-1/eval/run_code_eval.py)) and callback ([eval/eval_callback.py](file:///home/kriday/Desktop/epoch-1/eval/eval_callback.py)) were updated to return both extracted code and a format categorization badge:

* **`direct_code`**: Fenced Python blocks or top-level `def` statements matching standard direct assistant responses.
* **`tool_call_wrapped`**: Code embedded inside JSON string blocks or shell heredocs (`cat << 'EOF'`).
* **`raw_unwrapped` / `extraction_failed`**: Fallbacks or failed extractions.

---

## 3. Decision Matrix for Intermediate Checkpoints (Steps 1,000 – 2,000)

| Pass@1 \ Direct Code Ratio | Direct Code Ratio < 30% | Direct Code Ratio 30% - 70% | Direct Code Ratio > 70% |
| :--- | :--- | :--- | :--- |
| **Pass@1 > 40%** | **Stop & Rebalance**<br>*(Scenario B: High code capability, format locked in tool calls)* | **Re-evaluate @ Step 2000**<br>*(Trajectory moving towards direct format)* | **Continue Training**<br>*(Scenario A: Target convergence achieved)* |
| **Pass@1 15% - 40%** | **Re-evaluate @ Step 2000**<br>*(Capability & format both in transition)* | **Continue Training**<br>*(Both capability & format progressing)* | **Continue Training**<br>*(Capability learning; format already aligned)* |
| **Pass@1 < 15%** | **Stop & Rebalance**<br>*(Scenario C: Low capability & poor format)* | **Stop & Rebalance**<br>*(Format progressing, but coding logic stagnant)* | **Continue to Step 2000**<br>*(Format aligned; allow parameter updates to catch up)* |

---

## 4. Dataset Rebalance & System Tagging Specification

If a rebalance run is triggered (Scenario B or C):

### System Prompt Intent Markers
* **`[DIRECT_QA]`**: Prepended to standard code generation, code review, and wiseness QA pairs to enforce direct text/code output without tool wrapping.
* **`[AGENTIC_TASK]`**: Prepended to multi-step execution traces (FABLE 5) to isolate agentic tool-calling behavior.

### Target Weight Re-balancing
1. **Down-weight FABLE 5 Traces**: Reduce from 8,530 pairs to ~1,500–2,000 pairs (or strictly gate behind `[AGENTIC_TASK]`).
2. **Upsample Direct Code & Review**: Increase Stack v2 and Standalone Code Review weight so direct code responses comprise $>70\%$ of code-related training batches.
