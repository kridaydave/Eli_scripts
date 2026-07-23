"""
Periodic Code Execution Eval Callback for Eli Training
=======================================================
Integrates into SFTTrainer to run pass@1 code eval every N steps.
Logs results alongside training loss so you can correlate:
  "loss went down but did code quality actually improve?"

Usage in train_eli_colab.py:
    from eval.eval_callback import CodeEvalCallback

    eval_cb = CodeEvalCallback(
        model=model,
        tokenizer=tokenizer,
        eval_every_steps=500,
        num_problems=10,   # Quick eval: subset for speed
    )
    trainer = SFTTrainer(..., callbacks=[eval_cb])
"""

import json
import time
import torch
from pathlib import Path
from datetime import datetime
from transformers import TrainerCallback


class CodeEvalCallback(TrainerCallback):
    """
    Runs a subset of the code execution eval during training.
    Lightweight: defaults to 10 problems every 500 steps (~2-3 min overhead).
    """

    def __init__(
        self,
        model,
        tokenizer,
        eval_set_path: str | None = None,
        eval_every_steps: int = 500,
        num_problems: int = 10,
        timeout: int = 10,
        temperature: float = 0.2,
        log_dir: str = "./models/eli-tone-lora/eval_logs",
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.eval_every_steps = eval_every_steps
        self.num_problems = num_problems
        self.timeout = timeout
        self.temperature = temperature
        self.log_dir = Path(log_dir)
        self.eval_history = []

        # Locate eval set
        if eval_set_path:
            self.eval_set_path = Path(eval_set_path)
        else:
            self.eval_set_path = Path(__file__).resolve().parent / "code_exec_eval_set.jsonl"

        # Pre-load and sample problems (balanced by difficulty)
        self._load_eval_subset()

    def _load_eval_subset(self):
        """Load a balanced subset of problems."""
        from collections import defaultdict

        all_items = []
        with open(self.eval_set_path, 'r') as f:
            for line in f:
                if line.strip():
                    all_items.append(json.loads(line))

        # Stratified sample: proportional to difficulty
        by_diff = defaultdict(list)
        for item in all_items:
            by_diff[item.get("difficulty", "medium")].append(item)

        self.eval_items = []
        remaining = self.num_problems
        for diff in ["easy", "medium", "hard"]:
            items = by_diff.get(diff, [])
            n_take = max(1, int(len(items) / len(all_items) * self.num_problems))
            n_take = min(n_take, remaining, len(items))
            self.eval_items.extend(items[:n_take])
            remaining -= n_take

        # Fill remainder if needed
        taken_ids = {item["id"] for item in self.eval_items}
        for item in all_items:
            if remaining <= 0:
                break
            if item["id"] not in taken_ids:
                self.eval_items.append(item)
                remaining -= 1

        print(f"[CodeEvalCallback] Loaded {len(self.eval_items)} problems "
              f"(from {len(all_items)} total) for periodic eval every {self.eval_every_steps} steps")

    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step == 0:
            return
        if state.global_step % self.eval_every_steps != 0:
            return

        print(f"\n{'='*60}")
        print(f"  [CODE EVAL @ Step {state.global_step}] Running pass@1 on {len(self.eval_items)} problems...")
        print(f"{'='*60}")

        # Import here to avoid circular imports
        from eval.run_code_eval import (
            generate_code,
            extract_code_from_response,
            run_tests_sandboxed,
        )

        # Unsloth: switch to inference mode
        try:
            from unsloth import FastLanguageModel
            FastLanguageModel.for_inference(self.model)
            has_unsloth = True
        except ImportError:
            has_unsloth = False

        passed = 0
        total = len(self.eval_items)
        per_problem = []

        for i, item in enumerate(self.eval_items):
            response = generate_code(
                self.model, self.tokenizer, item["prompt"],
                temperature=self.temperature,
            )
            extracted = extract_code_from_response(
                response, item["function_name"], item.get("language", "python")
            )

            if extracted is None:
                per_problem.append({"id": item["id"], "passed": False, "error": "extraction_failed"})
                print(f"  [{i+1}/{total}] {item['id']}: ✗ (extraction)")
            else:
                result = run_tests_sandboxed(
                    extracted, item["test_code"], item["function_name"],
                    timeout=self.timeout,
                )
                per_problem.append({
                    "id": item["id"],
                    "passed": result["passed"],
                    "error": result.get("error"),
                })
                if result["passed"]:
                    passed += 1
                    print(f"  [{i+1}/{total}] {item['id']}: ✓")
                else:
                    print(f"  [{i+1}/{total}] {item['id']}: ✗ ({result.get('error', '')[:50]})")

        pass_at_1 = passed / total if total > 0 else 0.0

        # Log entry
        entry = {
            "step": state.global_step,
            "timestamp": datetime.now().isoformat(),
            "pass_at_1": round(pass_at_1, 4),
            "passed": passed,
            "total": total,
            "train_loss": state.log_history[-1].get("loss") if state.log_history else None,
            "problems": per_problem,
        }
        self.eval_history.append(entry)

        # Print summary
        bar = "█" * int(pass_at_1 * 20) + "░" * (20 - int(pass_at_1 * 20))
        print(f"\n  Step {state.global_step} | pass@1: {bar} {pass_at_1:.0%} ({passed}/{total})")
        if state.log_history:
            loss = state.log_history[-1].get("loss", "?")
            print(f"  Current train loss: {loss}")

        # Show trend if we have history
        if len(self.eval_history) > 1:
            prev = self.eval_history[-2]
            delta = entry["pass_at_1"] - prev["pass_at_1"]
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
            print(f"  Trend: {arrow} {delta:+.1%} from step {prev['step']}")

        print(f"{'='*60}\n")

        # Save eval log to disk
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / "code_eval_history.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        # Switch back to training mode
        if has_unsloth:
            FastLanguageModel.for_training(self.model)

    def on_train_end(self, args, state, control, **kwargs):
        """Print final eval summary at end of training."""
        if not self.eval_history:
            return

        print(f"\n{'='*60}")
        print(f"  CODE EVAL TRAJECTORY (across training)")
        print(f"{'='*60}")
        for entry in self.eval_history:
            loss_str = f"loss={entry['train_loss']:.4f}" if entry['train_loss'] else "loss=?"
            bar = "█" * int(entry["pass_at_1"] * 15) + "░" * (15 - int(entry["pass_at_1"] * 15))
            print(f"  Step {entry['step']:6d} | {bar} {entry['pass_at_1']:.0%} | {loss_str}")
        print(f"{'='*60}\n")
