"""
Frontend Code Eval Runner for Eli
===================================
Validates HTML/JS output by loading it in a headless browser and running DOM checks.

Requires: playwright (pip install playwright && python -m playwright install chromium)

Usage:
    # Run full eval
    python eval/run_frontend_eval.py --lora_path ./models/eli-tone-lora

    # Quick smoke test
    python eval/run_frontend_eval.py --lora_path ./models/eli-tone-lora --quick

    # Validate-only mode (check the eval set itself with hand-written HTML)
    python eval/run_frontend_eval.py --validate-only
"""

import json
import re
import sys
import time
import asyncio
import tempfile
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_SET_PATH = Path(__file__).resolve().parent / "frontend_exec_eval_set.jsonl"

SYSTEM_PROMPT = (
    "You are Eli, a senior full-stack software engineer with strong frontend taste. "
    "Write clean, semantic HTML with embedded CSS and JavaScript. "
    "Respond with the complete HTML file."
)


def extract_html_from_response(response: str) -> str | None:
    """Extract HTML from model response (handles code blocks, bare HTML, etc.)"""
    # Strategy 1: Fenced HTML code block
    match = re.search(r'```(?:html)\s*\n(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Strategy 2: Any fenced block that starts with <!DOCTYPE or <html
    match = re.search(r'```\w*\s*\n(<!DOCTYPE.*?)```', response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Strategy 3: Bare HTML in response
    match = re.search(r'(<!DOCTYPE\s+html>.*</html>)', response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Strategy 4: HTML without doctype
    match = re.search(r'(<html[^>]*>.*</html>)', response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


async def validate_html_in_browser(html_content: str, checks: list[dict], timeout: int = 10000) -> list[dict]:
    """
    Load HTML in headless Chromium and run validation checks.
    Returns list of check results with pass/fail status.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && python -m playwright install chromium")
        sys.exit(1)

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Write HTML to temp file and load it
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_path = f.name

        try:
            await page.goto(f'file://{temp_path}', wait_until='domcontentloaded', timeout=timeout)
            await page.wait_for_timeout(500)  # Let JS initialize

            for check in checks:
                check_result = {"description": check["description"], "passed": False, "error": None}
                check_type = check["check_type"]

                try:
                    if check_type == "element_exists":
                        el = await page.query_selector(check["selector"])
                        actual = el is not None
                        check_result["passed"] = actual == check["expected"]
                        if not check_result["passed"]:
                            check_result["error"] = f"Selector '{check['selector']}' {'found' if actual else 'not found'}, expected {'exists' if check['expected'] else 'not exists'}"

                    elif check_type == "element_count":
                        els = await page.query_selector_all(check["selector"])
                        actual = len(els)
                        expected = check["expected"]
                        if isinstance(expected, str) and expected.startswith(">="):
                            check_result["passed"] = actual >= int(expected[2:])
                        elif isinstance(expected, str) and expected.startswith("<="):
                            check_result["passed"] = actual <= int(expected[2:])
                        else:
                            check_result["passed"] = actual == int(expected)
                        if not check_result["passed"]:
                            check_result["error"] = f"Found {actual} elements for '{check['selector']}', expected {expected}"

                    elif check_type == "text_content":
                        el = await page.query_selector(check["selector"])
                        if el:
                            text = await el.text_content()
                            check_result["passed"] = check["expected"].lower() in (text or "").lower()
                        else:
                            check_result["error"] = f"Element not found: {check['selector']}"

                    elif check_type == "attribute_check":
                        el = await page.query_selector(check["selector"])
                        if el:
                            attr_val = await el.get_attribute(check["attribute"])
                            if check["expected"] is True:
                                check_result["passed"] = attr_val is not None
                            elif check["expected"] is False:
                                check_result["passed"] = attr_val is None
                            else:
                                check_result["passed"] = attr_val == str(check["expected"])
                        else:
                            check_result["error"] = f"Element not found: {check['selector']}"

                    elif check_type == "js_eval":
                        result_val = await page.evaluate(check["expression"])
                        check_result["passed"] = result_val == check["expected"]
                        if not check_result["passed"]:
                            check_result["error"] = f"JS eval returned {result_val}, expected {check['expected']}"

                    elif check_type == "computed_style":
                        el = await page.query_selector(check["selector"])
                        if el:
                            style_val = await page.evaluate(
                                f"(el) => getComputedStyle(el).{check['property']}",
                                el
                            )
                            check_result["passed"] = str(style_val) == str(check["expected"])
                        else:
                            check_result["error"] = f"Element not found: {check['selector']}"

                    else:
                        check_result["error"] = f"Unknown check type: {check_type}"

                except Exception as e:
                    check_result["error"] = f"{type(e).__name__}: {str(e)[:200]}"

                results.append(check_result)

        finally:
            await browser.close()
            try:
                import os
                os.unlink(temp_path)
            except OSError:
                pass

    return results


def load_eval_set(path: str | Path = EVAL_SET_PATH) -> list[dict]:
    items = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


async def run_frontend_eval(
    model,
    tokenizer,
    eval_items: list[dict],
    temperature: float = 0.3,
    verbose: bool = True,
) -> dict:
    """Run frontend eval: generate HTML, load in browser, run DOM checks."""
    # Import here to keep the module loadable without torch
    from eval.run_code_eval import generate_code

    results = []
    pass_count = 0
    difficulty_stats = defaultdict(lambda: {"total": 0, "passed": 0})
    tag_stats = defaultdict(lambda: {"total": 0, "passed": 0})

    for i, item in enumerate(eval_items):
        difficulty = item.get("difficulty", "medium")
        tags = item.get("tags", [])

        if verbose:
            print(f"\n[{i+1}/{len(eval_items)}] {item['id']} ({difficulty}) ", end="", flush=True)

        # Generate HTML
        response = generate_code(model, tokenizer, item["prompt"], temperature=temperature)
        html = extract_html_from_response(response)

        if html is None:
            result_entry = {
                "id": item["id"],
                "difficulty": difficulty,
                "passed": False,
                "checks_passed": 0,
                "checks_total": len(item.get("validation_checks", [])),
                "error": "HTML_EXTRACTION_FAILED",
            }
            if verbose:
                print("✗ (extraction failed)")
        else:
            # Run browser validation
            check_results = await validate_html_in_browser(html, item.get("validation_checks", []))
            checks_passed = sum(1 for c in check_results if c["passed"])
            checks_total = len(check_results)
            # Pass if >= 70% of checks pass (allow some tolerance for styling differences)
            passed = checks_passed >= max(1, int(checks_total * 0.7))

            if passed:
                pass_count += 1

            result_entry = {
                "id": item["id"],
                "difficulty": difficulty,
                "passed": passed,
                "checks_passed": checks_passed,
                "checks_total": checks_total,
                "check_details": check_results,
            }

            if verbose:
                pct = checks_passed / checks_total * 100 if checks_total > 0 else 0
                status = "✓" if passed else "✗"
                print(f"{status} ({checks_passed}/{checks_total} checks = {pct:.0f}%)")

        results.append(result_entry)
        difficulty_stats[difficulty]["total"] += 1
        if result_entry["passed"]:
            difficulty_stats[difficulty]["passed"] += 1
        for tag in tags:
            tag_stats[tag]["total"] += 1
            if result_entry["passed"]:
                tag_stats[tag]["passed"] += 1

    total = len(eval_items)
    pass_at_1 = pass_count / total if total > 0 else 0.0

    summary = {
        "pass_at_1": round(pass_at_1, 4),
        "passed": pass_count,
        "total": total,
        "by_difficulty": {
            k: {"passed": v["passed"], "total": v["total"],
                "rate": round(v["passed"] / v["total"], 4) if v["total"] > 0 else 0.0}
            for k, v in sorted(difficulty_stats.items())
        },
        "by_tag": {
            k: {"passed": v["passed"], "total": v["total"],
                "rate": round(v["passed"] / v["total"], 4) if v["total"] > 0 else 0.0}
            for k, v in sorted(tag_stats.items(), key=lambda x: x[1]["total"], reverse=True)
        },
    }

    return {"summary": summary, "results": results}


def main():
    parser = argparse.ArgumentParser(description="Frontend HTML/JS execution eval for Eli")
    parser.add_argument("--base_model", type=str, default="unsloth/Qwen3-4B-Instruct-2507")
    parser.add_argument("--lora_path", type=str, default="./models/eli-tone-lora")
    parser.add_argument("--eval_set", type=str, default=str(EVAL_SET_PATH))
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--quick", action="store_true", help="Run 5 problems")
    parser.add_argument("--validate-only", action="store_true", help="Just check eval set loads")
    args = parser.parse_args()

    eval_items = load_eval_set(args.eval_set)
    print(f"Loaded {len(eval_items)} frontend eval problems")

    if args.validate_only:
        print("Eval set loaded successfully. Validation checks per problem:")
        for item in eval_items:
            print(f"  {item['id']} ({item['difficulty']}): {len(item.get('validation_checks', []))} checks")
        sys.exit(0)

    if args.quick:
        by_diff = defaultdict(list)
        for item in eval_items:
            by_diff[item.get("difficulty", "medium")].append(item)
        eval_items = by_diff.get("easy", [])[:2] + by_diff.get("medium", [])[:2] + by_diff.get("hard", [])[:1]
        print(f"Quick mode: {len(eval_items)} problems")

    from eval.run_code_eval import load_model
    model, tokenizer, lora_loaded = load_model(args.base_model, args.lora_path)

    print(f"\n=== RUNNING FRONTEND EVAL ===")
    eval_output = asyncio.run(run_frontend_eval(model, tokenizer, eval_items, temperature=args.temperature))

    # Print summary
    s = eval_output["summary"]
    print(f"\n{'='*60}")
    print(f"  FRONTEND PASS@1: {s['pass_at_1']:.1%}  ({s['passed']}/{s['total']})")
    print(f"{'='*60}")
    for diff, stats in s["by_difficulty"].items():
        bar = "█" * int(stats["rate"] * 20) + "░" * (20 - int(stats["rate"] * 20))
        print(f"    {diff:8s} {bar} {stats['rate']:.0%}  ({stats['passed']}/{stats['total']})")

    # Save
    if args.output:
        output_path = Path(args.output)
    else:
        suffix = "lora" if lora_loaded else "base"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = PROJECT_ROOT / "processed" / f"frontend_eval_{suffix}_{timestamp}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(eval_output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
