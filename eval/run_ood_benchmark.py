#!/usr/bin/env python3
"""
OOD Coding Benchmark Runner for Eli vs Base Qwen3-4B
======================================================
Measures coding ability degradation on Out-Of-Distribution tasks.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add project root to sys.path so we can import from eval.run_code_eval
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eval.run_code_eval import (
    extract_code_from_response,
    run_tests_sandboxed,
    load_model,
    generate_code,
    _indent,
    run_eval_canonical
)

def load_eval_set(eval_path: str) -> list[dict]:
    items = []
    with open(eval_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items

def evaluate_model(model, tokenizer, eval_items, temperature, timeout, verbose):
    results = []
    pass_count = 0
    format_stats = defaultdict(int)
    
    for i, item in enumerate(eval_items):
        problem_id = item["id"]
        function_name = item["function_name"]
        
        if verbose:
            print(f"[{i+1}/{len(eval_items)}] {problem_id} ", end="", flush=True)
            
        response = generate_code(model, tokenizer, item["prompt"], temperature=temperature)
        extracted, format_type = extract_code_from_response(response, function_name, item.get("language", "python"))
        
        format_stats[format_type] += 1
        
        if extracted is None:
            passed = False
            error = "CODE_EXTRACTION_FAILED"
            if verbose:
                print("✗ (extraction failed)")
        else:
            test_result = run_tests_sandboxed(extracted, item["test_code"], function_name, timeout=timeout)
            passed = test_result["passed"]
            error = test_result.get("error")
            if passed:
                pass_count += 1
            if verbose:
                print("✓" if passed else f"✗ ({str(error)[:60]})")
                
        results.append({
            "id": problem_id,
            "passed": passed,
            "error": error,
            "format": format_type,
            "difficulty": item.get("difficulty", "unknown"),
            "ood_category": item.get("ood_category", "unknown")
        })
        
    return {
        "pass_count": pass_count,
        "total": len(eval_items),
        "results": results,
        "format_stats": dict(format_stats)
    }

def print_comparison(base_res, lora_res):
    print("\n" + "="*80)
    print(f"OOD BENCHMARK COMPARISON REPORT")
    print("="*80)
    
    base_pass = base_res["pass_count"] / base_res["total"]
    lora_pass = lora_res["pass_count"] / lora_res["total"]
    delta_pass = lora_pass - base_pass
    
    print(f"\nOVERALL PASS@1")
    print(f"Base Qwen3-4B: {base_pass:.1%} ({base_res['pass_count']}/{base_res['total']})")
    print(f"LoRA Fine-tune: {lora_pass:.1%} ({lora_res['pass_count']}/{lora_res['total']})")
    print(f"Delta: {delta_pass:+.1%}")
    
    # Format Health
    print(f"\nFORMAT HEALTH (direct_code vs tool_call_wrapped vs extraction_failed)")
    print(f"Base: {base_res['format_stats']}")
    print(f"LoRA: {lora_res['format_stats']}")
    
    # Breakdown by difficulty
    diff_stats = defaultdict(lambda: {"base_pass": 0, "lora_pass": 0, "total": 0})
    for r in base_res["results"]:
        diff_stats[r["difficulty"]]["total"] += 1
        if r["passed"]: diff_stats[r["difficulty"]]["base_pass"] += 1
    for r in lora_res["results"]:
        if r["passed"]: diff_stats[r["difficulty"]]["lora_pass"] += 1
        
    print("\nBY DIFFICULTY")
    print(f"{'Difficulty':<12} | {'Total':<6} | {'Base':<12} | {'LoRA':<12} | {'Delta':<10}")
    print("-" * 60)
    for diff, stats in sorted(diff_stats.items()):
        b_p = stats["base_pass"] / stats["total"] if stats["total"] else 0
        l_p = stats["lora_pass"] / stats["total"] if stats["total"] else 0
        d_p = l_p - b_p
        print(f"{diff:<12} | {stats['total']:<6} | {b_p:6.1%} ({stats['base_pass']}) | {l_p:6.1%} ({stats['lora_pass']}) | {d_p:+6.1%}")
        
    # Breakdown by OOD category
    cat_stats = defaultdict(lambda: {"base_pass": 0, "lora_pass": 0, "total": 0})
    for r in base_res["results"]:
        cat_stats[r["ood_category"]]["total"] += 1
        if r["passed"]: cat_stats[r["ood_category"]]["base_pass"] += 1
    for r in lora_res["results"]:
        if r["passed"]: cat_stats[r["ood_category"]]["lora_pass"] += 1
        
    print("\nBY OOD CATEGORY")
    print(f"{'Category':<25} | {'Total':<6} | {'Base':<12} | {'LoRA':<12} | {'Delta':<10}")
    print("-" * 75)
    for cat, stats in sorted(cat_stats.items()):
        b_p = stats["base_pass"] / stats["total"] if stats["total"] else 0
        l_p = stats["lora_pass"] / stats["total"] if stats["total"] else 0
        d_p = l_p - b_p
        print(f"{cat:<25} | {stats['total']:<6} | {b_p:6.1%} ({stats['base_pass']}) | {l_p:6.1%} ({stats['lora_pass']}) | {d_p:+6.1%}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, default="unsloth/Qwen3-4B-Instruct-2507")
    parser.add_argument("--lora_path", type=str, required=True)
    parser.add_argument("--eval_set", type=str, default=str(PROJECT_ROOT / "eval" / "ood_coding_eval_set.jsonl"))
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--verbose", action="store_true", default=True)
    args = parser.parse_args()
    
    eval_items = load_eval_set(args.eval_set)
    print(f"Loaded {len(eval_items)} items from {args.eval_set}")
    
    if args.quick:
        eval_items = eval_items[:5]
        
    if args.validate_only:
        validation = run_eval_canonical(eval_items, timeout=args.timeout)
        sys.exit(1 if validation["failures"] else 0)
        
    # Validate first
    print("\n--- Pre-flight check: Validating Canonical Solutions ---")
    validation = run_eval_canonical(eval_items, timeout=args.timeout)
    if validation["failures"]:
        print("\nERROR: Canonical solutions failed. Fix them before benchmarking.")
        sys.exit(1)
        
    print("\n--- Evaluating Base Model ---")
    base_model, base_tok, _ = load_model(args.base_model, None)
    base_results = evaluate_model(base_model, base_tok, eval_items, args.temperature, args.timeout, args.verbose)
    
    # Free memory
    del base_model
    del base_tok
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    print("\n--- Evaluating LoRA Model ---")
    lora_model, lora_tok, _ = load_model(args.base_model, args.lora_path)
    lora_results = evaluate_model(lora_model, lora_tok, eval_items, args.temperature, args.timeout, args.verbose)
    
    print_comparison(base_results, lora_results)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = PROJECT_ROOT / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"ood_benchmark_results_{timestamp}.json"
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "base_model": args.base_model,
                "lora_path": args.lora_path,
                "timestamp": timestamp,
                "temperature": args.temperature,
                "total_problems": len(eval_items)
            },
            "base_results": base_results,
            "lora_results": lora_results
        }, f, indent=2)
    print(f"\nSaved results to {out_path}")

if __name__ == "__main__":
    main()
