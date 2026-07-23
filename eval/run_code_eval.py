"""
Execution-Based Code Evaluation Runner for Eli
================================================
Measures actual code correctness via pass@1 on held-out coding problems.

This is the eval that matters: training loss going down doesn't guarantee
the model writes correct, runnable code. This script:

1. Loads the eval set (code_exec_eval_set.jsonl)
2. Generates code from each prompt using the model
3. Extracts the function from the model's response
4. Runs the test cases in a sandboxed subprocess with timeout
5. Reports pass@1, per-difficulty breakdown, and per-tag breakdown

Usage:
    # Eval base model
    python eval/run_code_eval.py --base_model unsloth/Qwen3-4B-Instruct-2507

    # Eval LoRA checkpoint
    python eval/run_code_eval.py --base_model unsloth/Qwen3-4B-Instruct-2507 --lora_path ./models/eli-tone-lora

    # Eval a specific checkpoint during training
    python eval/run_code_eval.py --lora_path ./models/eli-tone-lora/checkpoint-500

    # Quick smoke test (5 problems)
    python eval/run_code_eval.py --lora_path ./models/eli-tone-lora --quick

    # Save results to specific file
    python eval/run_code_eval.py --lora_path ./models/eli-tone-lora --output results.json
"""

import json
import os
import re
import sys
import time
import signal
import subprocess
import tempfile
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_SET_PATH = Path(__file__).resolve().parent / "code_exec_eval_set.jsonl"

SYSTEM_PROMPT = (
    "You are Eli, a senior full-stack software engineer. "
    "Write clean, correct, production-quality code. "
    "Respond with the implementation directly."
)

# ──────────────────────────────────────────────────────────────────────
# Code Extraction
# ──────────────────────────────────────────────────────────────────────

def extract_code_from_response(response: str, function_name: str, language: str = "python") -> str | None:
    """
    Extract executable code from model response.
    Handles: bare code, fenced code blocks, markdown, etc.
    Returns the extracted code string or None if extraction fails.
    """
    # Strategy 1: Extract from fenced code blocks (```python ... ``` or ``` ... ```)
    code_block_patterns = [
        rf'```(?:python|py)\s*\n(.*?)```',     # ```python ... ```
        rf'```\s*\n(.*?)```',                     # ``` ... ```
    ]
    for pattern in code_block_patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        for match in matches:
            if function_name in match and f"def {function_name}" in match:
                return match.strip()

    # Strategy 2: Find the function definition directly in the response
    # Look for def function_name(...): and grab everything from there
    func_pattern = rf'((?:(?:import|from)\s+\S+.*\n)*\s*def\s+{re.escape(function_name)}\s*\(.*$(?:\n(?:[ \t]+.*|[ \t]*$))*)'
    match = re.search(func_pattern, response, re.MULTILINE)
    if match:
        return match.group(0).strip()

    # Strategy 3: If there are code blocks, return the longest one that contains 'def '
    all_blocks = re.findall(r'```(?:\w*)\s*\n(.*?)```', response, re.DOTALL)
    code_blocks_with_def = [b for b in all_blocks if 'def ' in b]
    if code_blocks_with_def:
        return max(code_blocks_with_def, key=len).strip()

    # Strategy 4: Last resort — if the entire response looks like code, use it
    lines = response.strip().split('\n')
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
    if code_lines and any(f'def {function_name}' in l for l in code_lines):
        return response.strip()

    return None


# ──────────────────────────────────────────────────────────────────────
# Sandboxed Execution
# ──────────────────────────────────────────────────────────────────────

def run_tests_sandboxed(code: str, test_code: str, function_name: str, timeout: int = 10) -> dict:
    """
    Run tests in an isolated subprocess with timeout.
    Returns: {"passed": bool, "error": str | None, "runtime_ms": float}
    """
    # Build the full test script
    test_script = f"""\
import sys
import signal

# Hard timeout inside the subprocess too
def _timeout_handler(signum, frame):
    raise TimeoutError("Execution timed out")

signal.signal(signal.SIGALRM, _timeout_handler)
signal.alarm({timeout})

try:
    # Execute the candidate solution
{_indent(code, 4)}

    # Execute the test harness
{_indent(test_code, 4)}

    # Run check() with the candidate function
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
            timeout=timeout + 2,  # Extra buffer for subprocess overhead
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


def _indent(code: str, spaces: int) -> str:
    """Indent every line of code by the given number of spaces."""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in code.split("\n"))


# ──────────────────────────────────────────────────────────────────────
# Model Inference
# ──────────────────────────────────────────────────────────────────────

def load_model(base_model: str, lora_path: str | None = None):
    """Load model + tokenizer via Unsloth (preferred) or plain transformers."""
    import torch

    try:
        from unsloth import FastLanguageModel
        has_unsloth = True
    except ImportError:
        has_unsloth = False

    lora_loaded = False
    if has_unsloth:
        model_to_load = lora_path if (lora_path and Path(lora_path).exists()) else base_model
        if lora_path and Path(lora_path).exists():
            lora_loaded = True
        print(f"Loading {'LoRA' if lora_loaded else 'base'} model via Unsloth: {model_to_load}")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_to_load,
            max_seq_length=4096,  # Short context is fine for eval
            dtype=None,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)
    else:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from peft import PeftModel

        print(f"Loading base model: {base_model}")
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )
        if lora_path and Path(lora_path).exists():
            print(f"Loading LoRA adapter: {lora_path}")
            model = PeftModel.from_pretrained(model, lora_path)
            lora_loaded = True

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer, lora_loaded


def generate_code(model, tokenizer, prompt: str, temperature: float = 0.2) -> str:
    """Generate code from prompt using the model."""
    import torch

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    input_text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

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

    response = tokenizer.decode(
        outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True
    )
    return response.strip()


# ──────────────────────────────────────────────────────────────────────
# Eval Orchestration
# ──────────────────────────────────────────────────────────────────────

def load_eval_set(eval_path: str | Path = EVAL_SET_PATH) -> list[dict]:
    """Load eval set from JSONL."""
    items = []
    with open(eval_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def run_eval(
    model,
    tokenizer,
    eval_items: list[dict],
    temperature: float = 0.2,
    timeout: int = 10,
    verbose: bool = True,
) -> dict:
    """
    Run the full eval pipeline.
    Returns a results dict with pass@1, per-difficulty, per-tag breakdowns.
    """
    results = []
    pass_count = 0
    difficulty_stats = defaultdict(lambda: {"total": 0, "passed": 0})
    tag_stats = defaultdict(lambda: {"total": 0, "passed": 0})

    for i, item in enumerate(eval_items):
        problem_id = item["id"]
        function_name = item["function_name"]
        difficulty = item.get("difficulty", "unknown")
        tags = item.get("tags", [])

        if verbose:
            print(f"\n[{i+1}/{len(eval_items)}] {problem_id} ({difficulty}) ", end="", flush=True)

        # 1. Generate code
        gen_start = time.time()
        response = generate_code(model, tokenizer, item["prompt"], temperature=temperature)
        gen_time = time.time() - gen_start

        # 2. Extract function
        extracted = extract_code_from_response(response, function_name, item.get("language", "python"))

        if extracted is None:
            result = {
                "id": problem_id,
                "difficulty": difficulty,
                "tags": tags,
                "passed": False,
                "error": "CODE_EXTRACTION_FAILED",
                "raw_response_len": len(response),
                "generation_time_s": gen_time,
            }
            if verbose:
                print("✗ (extraction failed)")
        else:
            # 3. Run tests
            test_result = run_tests_sandboxed(
                extracted, item["test_code"], function_name, timeout=timeout
            )
            passed = test_result["passed"]
            if passed:
                pass_count += 1

            result = {
                "id": problem_id,
                "difficulty": difficulty,
                "tags": tags,
                "passed": passed,
                "error": test_result.get("error"),
                "runtime_ms": test_result.get("runtime_ms"),
                "generation_time_s": gen_time,
                "extracted_code_preview": extracted[:300] if extracted else None,
            }
            if verbose:
                print("✓" if passed else f"✗ ({test_result.get('error', '')[:60]})")

        results.append(result)

        # Update stats
        difficulty_stats[difficulty]["total"] += 1
        if result["passed"]:
            difficulty_stats[difficulty]["passed"] += 1
        for tag in tags:
            tag_stats[tag]["total"] += 1
            if result["passed"]:
                tag_stats[tag]["passed"] += 1

    # Compute summary
    total = len(eval_items)
    pass_at_1 = pass_count / total if total > 0 else 0.0

    summary = {
        "pass_at_1": round(pass_at_1, 4),
        "passed": pass_count,
        "total": total,
        "by_difficulty": {
            k: {
                "passed": v["passed"],
                "total": v["total"],
                "rate": round(v["passed"] / v["total"], 4) if v["total"] > 0 else 0.0,
            }
            for k, v in sorted(difficulty_stats.items())
        },
        "by_tag": {
            k: {
                "passed": v["passed"],
                "total": v["total"],
                "rate": round(v["passed"] / v["total"], 4) if v["total"] > 0 else 0.0,
            }
            for k, v in sorted(tag_stats.items(), key=lambda x: x[1]["total"], reverse=True)
        },
    }

    return {"summary": summary, "results": results}


def run_eval_canonical(eval_items: list[dict], timeout: int = 10) -> dict:
    """
    Run canonical solutions against their own tests to validate the eval set.
    This is a self-check — every canonical solution should pass.
    """
    print("\n=== VALIDATING EVAL SET (canonical solutions) ===")
    failures = []
    for i, item in enumerate(eval_items):
        result = run_tests_sandboxed(
            item["canonical_solution"],
            item["test_code"],
            item["function_name"],
            timeout=timeout,
        )
        status = "✓" if result["passed"] else "✗"
        print(f"  [{i+1}/{len(eval_items)}] {item['id']} {status}", end="")
        if not result["passed"]:
            print(f" — {result.get('error', '')[:80]}")
            failures.append({"id": item["id"], "error": result.get("error")})
        else:
            print()

    if failures:
        print(f"\n⚠ {len(failures)}/{len(eval_items)} canonical solutions FAILED their own tests!")
        for f in failures:
            print(f"  - {f['id']}: {f['error'][:100]}")
    else:
        print(f"\n✓ All {len(eval_items)} canonical solutions pass their tests.")

    return {"total": len(eval_items), "failures": failures}


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Execution-based code eval for Eli (pass@1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--base_model", type=str, default="unsloth/Qwen3-4B-Instruct-2507")
    parser.add_argument("--lora_path", type=str, default="./models/eli-tone-lora")
    parser.add_argument("--eval_set", type=str, default=str(EVAL_SET_PATH))
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=10, help="Per-problem timeout in seconds")
    parser.add_argument("--quick", action="store_true", help="Run only 5 problems (smoke test)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Only validate canonical solutions (no model needed)")
    parser.add_argument("--verbose", action="store_true", default=True)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.quiet:
        args.verbose = False

    # Load eval set
    eval_items = load_eval_set(args.eval_set)
    print(f"Loaded {len(eval_items)} eval problems from {args.eval_set}")

    if args.quick:
        # Pick a spread: 2 easy, 2 medium, 1 hard
        by_diff = defaultdict(list)
        for item in eval_items:
            by_diff[item.get("difficulty", "medium")].append(item)
        eval_items = (
            by_diff.get("easy", [])[:2]
            + by_diff.get("medium", [])[:2]
            + by_diff.get("hard", [])[:1]
        )
        print(f"Quick mode: running {len(eval_items)} problems")

    # Validate-only mode: just check canonical solutions
    if args.validate_only:
        validation = run_eval_canonical(eval_items, timeout=args.timeout)
        if validation["failures"]:
            sys.exit(1)
        sys.exit(0)

    # Load model and run eval
    model, tokenizer, lora_loaded = load_model(args.base_model, args.lora_path)

    print(f"\n=== RUNNING CODE EXECUTION EVAL ===")
    print(f"Model: {'LoRA @ ' + args.lora_path if lora_loaded else args.base_model}")
    print(f"Problems: {len(eval_items)} | Temperature: {args.temperature} | Timeout: {args.timeout}s")

    eval_output = run_eval(
        model, tokenizer, eval_items,
        temperature=args.temperature,
        timeout=args.timeout,
        verbose=args.verbose,
    )

    # Add metadata
    eval_output["metadata"] = {
        "timestamp": datetime.now().isoformat(),
        "base_model": args.base_model,
        "lora_path": args.lora_path if lora_loaded else None,
        "lora_loaded": lora_loaded,
        "temperature": args.temperature,
        "eval_set": args.eval_set,
        "num_problems": len(eval_items),
    }

    # Print summary
    s = eval_output["summary"]
    print(f"\n{'='*60}")
    print(f"  PASS@1: {s['pass_at_1']:.1%}  ({s['passed']}/{s['total']})")
    print(f"{'='*60}")
    print(f"\n  By Difficulty:")
    for diff, stats in s["by_difficulty"].items():
        bar = "█" * int(stats["rate"] * 20) + "░" * (20 - int(stats["rate"] * 20))
        print(f"    {diff:8s} {bar} {stats['rate']:.0%}  ({stats['passed']}/{stats['total']})")
    print(f"\n  By Tag (top 10):")
    for tag, stats in list(s["by_tag"].items())[:10]:
        bar = "█" * int(stats["rate"] * 15) + "░" * (15 - int(stats["rate"] * 15))
        print(f"    {tag:22s} {bar} {stats['rate']:.0%}  ({stats['passed']}/{stats['total']})")

    # Save results
    if args.output:
        output_path = Path(args.output)
    else:
        suffix = "lora" if lora_loaded else "base"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = PROJECT_ROOT / "processed" / f"code_eval_{suffix}_{timestamp}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(eval_output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
