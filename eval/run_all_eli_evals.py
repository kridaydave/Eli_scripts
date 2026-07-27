#!/usr/bin/env python3
"""
All-in-One Eli Master Evaluation Runner
========================================
Batched generation & evaluation across all 3 evaluation sets:
1. Standard Code Exec Eval (code_exec_eval_set.jsonl)
2. Out-of-Distribution Benchmark (ood_coding_eval_set.jsonl)
3. Nightmare Benchmark (nightmare_eval_set.jsonl)

Features:
- Batched generation (--batch-size) for fast inference
- Accepts --BASE (base model repo/path) and --ELI (LoRA path or HF repo)
- Extracts raw model response, thinking blocks (<think>...</think>), and extracted executable code
- Sandboxed test execution with pass@1 reporting
- Per-dataset summary breakdown and consolidated JSON export

Usage:
  # Eval Base Qwen3-4B
  python eval/run_all_eli_evals.py --BASE unsloth/Qwen3-4B-Instruct-2507 --batch-size 8

  # Eval Eli LoRA adapter (from HF repo or local directory)
  python eval/run_all_eli_evals.py --BASE unsloth/Qwen3-4B-Instruct-2507 --ELI kridaydave/eli-tone-lora --batch-size 8
"""

import json
import os
import re
import sys
import time
import tempfile
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent

SYSTEM_PROMPT = (
    "You are Eli, a senior full-stack software engineer. "
    "Write clean, correct, production-quality code. "
    "Respond with the implementation directly."
)

EVAL_SETS = {
    "standard": EVAL_DIR / "code_exec_eval_set.jsonl",
    "ood": EVAL_DIR / "ood_coding_eval_set.jsonl",
    "nightmare": EVAL_DIR / "nightmare_eval_set.jsonl",
}

# ──────────────────────────────────────────────────────────────────────
# Extraction Utilities
# ──────────────────────────────────────────────────────────────────────

def extract_think_and_response(raw_response: str) -> tuple[str | None, str]:
    """
    Extracts raw think block (<think>...</think>) and clean response text.
    Returns (think_content, clean_response_text).
    """
    think_match = re.search(r'<think>(.*?)</think>', raw_response, flags=re.DOTALL)
    think_content = think_match.group(1).strip() if think_match else None
    clean_text = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
    return think_content, clean_text


def extract_code_from_response(response: str, function_name: str, language: str = "python") -> tuple[str | None, str]:
    """
    Extract executable code from clean response text.
    Returns (extracted_code_string or None, format_type).
    """
    clean_resp = response.strip()

    # 1. Direct code block matching
    code_block_patterns = [
        rf'```(?:python|py)\s*\n(.*?)```',
        rf'```\s*\n(.*?)```',
    ]
    for pattern in code_block_patterns:
        matches = re.findall(pattern, clean_resp, re.DOTALL)
        for match in matches:
            if function_name in match and (f"def {function_name}" in match or f"class {function_name}" in match):
                return match.strip(), "direct_code"

    # 2. Regex function or class def match
    func_pattern = rf'((?:(?:import|from)\s+\S+.*\n)*\s*(?:def|class)\s+{re.escape(function_name)}\b.*$(?:\n(?:[ \t]+.*|[ \t]*$))*)'
    match = re.search(func_pattern, clean_resp, re.MULTILINE)
    if match:
        return match.group(0).strip(), "direct_code"

    # 3. Fallback unescaped check
    unescaped = clean_resp.replace("\\n", "\n").replace('\\"', '"')
    match = re.search(func_pattern, unescaped, re.MULTILINE)
    if match:
        return match.group(0).strip(), "tool_call_wrapped"

    # 4. Longest code block containing def or class
    all_blocks = re.findall(r'```(?:\w*)\s*\n(.*?)```', clean_resp, re.DOTALL)
    code_blocks_with_def = [b for b in all_blocks if 'def ' in b or 'class ' in b]
    if code_blocks_with_def:
        return max(code_blocks_with_def, key=len).strip(), "raw_unwrapped"

    return None, "extraction_failed"


# ──────────────────────────────────────────────────────────────────────
# Sandboxed Test Runner
# ──────────────────────────────────────────────────────────────────────

def _indent(code: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line for line in code.split("\n"))


def run_tests_sandboxed(code: str, test_code: str, function_name: str, timeout: int = 10) -> dict:
    """Run tests in isolated subprocess."""
    test_script = f"""\
import sys
import signal

def _timeout_handler(signum, frame):
    raise TimeoutError("Execution timed out")

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm({timeout})

try:
{_indent(code, 4)}

{_indent(test_code, 4)}

    check({function_name})
    print("ALL_TESTS_PASSED")
except AssertionError as e:
    print(f"ASSERTION_FAILED: {{e}}", file=sys.stderr)
    sys.exit(1)
except TimeoutError as e:
    print(f"TIMEOUT: {{e}}", file=sys.stderr)
    sys.exit(2)
except Exception as e:
    print(f"RUNTIME_ERROR: {{type(e).__name__}}: {{e}}", file=sys.stderr)
    sys.exit(3)
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        temp_path = f.name

    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout + 2,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        runtime_ms = (time.time() - start_time) * 1000

        if result.returncode == 0 and "ALL_TESTS_PASSED" in result.stdout:
            return {"passed": True, "error": None, "runtime_ms": runtime_ms}
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return {"passed": False, "error": error_msg[:500], "runtime_ms": runtime_ms}

    except subprocess.TimeoutExpired:
        runtime_ms = (time.time() - start_time) * 1000
        return {"passed": False, "error": "Process timed out", "runtime_ms": runtime_ms}
    except Exception as e:
        runtime_ms = (time.time() - start_time) * 1000
        return {"passed": False, "error": f"Execution error: {e}", "runtime_ms": runtime_ms}
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


# ──────────────────────────────────────────────────────────────────────
# Model Loading & Batched Inference
# ──────────────────────────────────────────────────────────────────────

def load_model(base_model: str, lora_path: str | None = None):
    """Loads base model + optional LoRA via Unsloth or PEFT/Transformers."""
    import torch
    from peft import PeftModel

    try:
        from unsloth import FastLanguageModel
        has_unsloth = True
    except ImportError:
        has_unsloth = False

    lora_loaded = False
    if has_unsloth:
        print(f"🚀 Loading Base model via Unsloth: {base_model}")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=base_model,
            max_seq_length=4096,
            dtype=None,
            load_in_4bit=True,
        )
        if lora_path:
            print(f"📌 Attaching LoRA adapter: {lora_path}")
            model = PeftModel.from_pretrained(model, lora_path)
            lora_loaded = True
        FastLanguageModel.for_inference(model)
    else:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        print(f"🚀 Loading Base model: {base_model}")
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )
        if lora_path:
            print(f"📌 Attaching LoRA adapter: {lora_path}")
            model = PeftModel.from_pretrained(model, lora_path)
            lora_loaded = True

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"  # Required for batched generation

    return model, tokenizer, lora_loaded


def batch_generate(model, tokenizer, prompts: list[str], temperature: float = 0.2, batch_size: int = 8) -> list[str]:
    """Runs batched generation over prompts."""
    import torch
    responses = []

    for i in range(0, len(prompts), batch_size):
        batch_prompts = prompts[i:i + batch_size]
        batch_inputs = []

        for p in batch_prompts:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": p},
            ]
            formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            batch_inputs.append(formatted)

        inputs = tokenizer(batch_inputs, return_tensors="pt", padding=True).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=temperature,
                top_p=0.95,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        input_lengths = [inputs.input_ids.shape[1]] * len(batch_prompts)
        for j, out in enumerate(outputs):
            seq = out[input_lengths[j]:]
            decoded = tokenizer.decode(seq, skip_special_tokens=True).strip()
            responses.append(decoded)

    return responses


# ──────────────────────────────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────────────────────────────

def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def main():
    parser = argparse.ArgumentParser(description="All-in-One Eli Evaluation Harness")
    parser.add_argument("--BASE", type=str, default="unsloth/Qwen3-4B-Instruct-2507", help="Base model HF repo or path")
    parser.add_argument("--ELI", type=str, default=None, help="Eli LoRA adapter HF repo or path (optional)")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for model generation")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature")
    parser.add_argument("--timeout", type=int, default=10, help="Per-problem timeout (seconds)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--quick", action="store_true", help="Quick mode (3 problems per set)")
    args = parser.parse_args()

    # Load Model
    model, tokenizer, lora_loaded = load_model(args.BASE, args.ELI)

    overall_results = {}
    master_summary = {}

    print(f"\n============================================================")
    print(f"  MASTER ELI EVALUATION SUITE")
    print(f"  Target: {'Eli LoRA @ ' + args.ELI if lora_loaded else 'Base Model (' + args.BASE + ')'}")
    print(f"  Batch Size: {args.batch_size} | Temp: {args.temperature} | Timeout: {args.timeout}s")
    print(f"============================================================\n")

    start_eval_time = time.time()

    for set_name, set_path in EVAL_SETS.items():
        if not set_path.exists():
            print(f"⚠️ Warning: Dataset file missing: {set_path}")
            continue

        items = load_jsonl(set_path)
        if args.quick:
            items = items[:3]

        print(f"── Running [{set_name.upper()}] Evaluation ({len(items)} problems) ──")
        prompts = [item["prompt"] for item in items]

        # Batched Generation
        gen_start = time.time()
        raw_responses = batch_generate(model, tokenizer, prompts, temperature=args.temperature, batch_size=args.batch_size)
        gen_time = time.time() - gen_start
        print(f"  ✓ Generated {len(raw_responses)} responses in {gen_time:.2f}s ({gen_time/len(items):.2f}s/item)")

        # Evaluation Pass
        set_results = []
        passed_count = 0
        diff_stats = defaultdict(lambda: {"total": 0, "passed": 0})
        cat_stats = defaultdict(lambda: {"total": 0, "passed": 0})

        for i, item in enumerate(items):
            problem_id = item["id"]
            function_name = item["function_name"]
            difficulty = item.get("difficulty", "unknown")
            category = item.get("ood_category") or item.get("nightmare_category") or "general"
            raw_resp = raw_responses[i]

            # 1. Extract Think & Clean Output
            think_block, clean_resp = extract_think_and_response(raw_resp)

            # 2. Extract Code
            extracted_code, format_type = extract_code_from_response(clean_resp, function_name, item.get("language", "python"))

            # 3. Sandboxed Execution
            if extracted_code is None:
                passed = False
                error_msg = "CODE_EXTRACTION_FAILED"
                runtime_ms = 0.0
            else:
                test_res = run_tests_sandboxed(extracted_code, item["test_code"], function_name, timeout=args.timeout)
                passed = test_res["passed"]
                error_msg = test_res.get("error")
                runtime_ms = test_res.get("runtime_ms", 0.0)

            if passed:
                passed_count += 1

            # Stats aggregation
            diff_stats[difficulty]["total"] += 1
            if passed: diff_stats[difficulty]["passed"] += 1

            cat_stats[category]["total"] += 1
            if passed: cat_stats[category]["passed"] += 1

            status_icon = "✓" if passed else "✗"
            print(f"  [{i+1}/{len(items)}] {problem_id} ({difficulty}) {status_icon}")

            set_results.append({
                "id": problem_id,
                "function_name": function_name,
                "difficulty": difficulty,
                "category": category,
                "passed": passed,
                "error": error_msg,
                "format_type": format_type,
                "runtime_ms": runtime_ms,
                "think_block": think_block,         # Extracted <think> block
                "raw_response": raw_resp,          # Full raw output
                "clean_response": clean_resp,      # Response without think tags
                "extracted_code": extracted_code,  # Extracted code
            })

        pass_rate = round(passed_count / len(items), 4) if items else 0.0
        set_summary = {
            "passed": passed_count,
            "total": len(items),
            "pass_at_1": pass_rate,
            "by_difficulty": {
                k: {"passed": v["passed"], "total": v["total"], "rate": round(v["passed"]/v["total"], 4)}
                for k, v in diff_stats.items()
            },
            "by_category": {
                k: {"passed": v["passed"], "total": v["total"], "rate": round(v["passed"]/v["total"], 4)}
                for k, v in cat_stats.items()
            }
        }

        master_summary[set_name] = set_summary
        overall_results[set_name] = {
            "summary": set_summary,
            "results": set_results
        }

        print(f"  ── [{set_name.upper()}] PASS@1: {pass_rate:.1%} ({passed_count}/{len(items)})\n")

    total_eval_time = time.time() - start_eval_time

    # Consolidated Report Output
    final_output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "base_model": args.BASE,
            "eli_adapter": args.ELI if lora_loaded else None,
            "lora_loaded": lora_loaded,
            "batch_size": args.batch_size,
            "temperature": args.temperature,
            "eval_duration_seconds": round(total_eval_time, 2)
        },
        "summary": master_summary,
        "eval_sets": overall_results
    }

    # Print Final Summary Dashboard
    print(f"\n============================================================")
    print(f"  FINAL SUMMARY DASHBOARD ({'Eli LoRA' if lora_loaded else 'Base Model'})")
    print(f"============================================================")
    for s_name, s_data in master_summary.items():
        print(f"  • {s_name.upper():12s}: {s_data['pass_at_1']:.1%} ({s_data['passed']}/{s_data['total']})")
    print(f"============================================================")

    # Save to JSON
    if args.output:
        out_path = Path(args.output)
    else:
        model_tag = "eli" if lora_loaded else "base"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = PROJECT_ROOT / "processed" / f"master_eval_{model_tag}_{ts}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Full detailed results (with raw responses & think blocks) saved to: {out_path}\n")


if __name__ == "__main__":
    main()
