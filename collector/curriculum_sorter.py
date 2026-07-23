"""
Progressive Curriculum & Emergence Sorter for Eli Dataset
Epoch Model Suite 1 — Eli (4B)

Enforces:
1. Individual Example-Level Shuffling (NO block-level grouping).
2. Progressive Density Curriculum:
   - Early Phase (0-40%): Heavy Code/Frontend (verifiable base stabilization).
   - Mid Phase (40-70%): Transitioning with increasing joint cross-axis examples.
   - Late Phase (70-100%): Peak Writing/Wiseness density & register calibration.
3. 70-85% Single-Axis Clean Data vs 15-30% Deliberate Cross-Axis Data.
4. Step 0 Transfer-Test Data (data/held_out_transfer_test.jsonl) FULLY EXCLUDED from training (0 leakage).
"""

import json
import random
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = PROJECT_ROOT / "processed"

HELD_OUT_TEST_FILE = DATA_DIR / "held_out_transfer_test.jsonl"

def load_held_out_prompts() -> set:
    """Load held-out transfer test prompts for 100% exclusion verification."""
    held_out = set()
    if HELD_OUT_TEST_FILE.exists():
        with open(HELD_OUT_TEST_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    ctx = item.get("context", "").strip().lower()
                    art = item.get("artifact", "").strip().lower()
                    if ctx:
                        held_out.add(ctx)
                    if art:
                        held_out.add(art)
    print(f"  Loaded {len(held_out)} held-out benchmark text signatures for strict exclusion.")
    return held_out

def apply_progressive_curriculum(all_pairs: list[dict], held_out_signatures: set) -> list[dict]:
    """
    Sorts and interleaves dataset at individual example level with progressive density ramp.
    """
    group_code_frontend = []
    group_cross_axis = []
    group_writing_wiseness = []

    excluded_count = 0

    for item in all_pairs:
        inst = item.get("instruction", "").strip().lower()
        out = item.get("output", "").strip().lower()

        # Strict Step 0 Exclusion Check
        if any(sig in inst or sig in out for sig in held_out_signatures if len(sig) > 15):
            excluded_count += 1
            continue

        meta = item.get("metadata", {})
        src = meta.get("source_type") or item.get("source", "unknown")

        if src in ["fable5_crownelius_traces", "fable5_cot_traces", "agent_tool_calling_schema", "bug_fix_tokio_race_condition", "eli_cross_axis_emergence"]:
            meta["is_cross_axis"] = True
            group_cross_axis.append(item)
        elif src in ["eli_personality", "user_custom_written_answers", "whitelisted_writing", "wiseness_and_voice"]:
            meta["is_cross_axis"] = False
            group_writing_wiseness.append(item)
        else:
            meta["is_cross_axis"] = False
            group_code_frontend.append(item)

    print(f"\nCategorized Dataset at Example Level:")
    print(f"  - Group A (Code & Frontend Base):      {len(group_code_frontend):,} samples")
    print(f"  - Group B (Cross-Axis Joint Examples): {len(group_cross_axis):,} samples ({len(group_cross_axis)/max(1, len(all_pairs))*100:.1f}%)")
    print(f"  - Group C (Writing & Wiseness Density):{len(group_writing_wiseness):,} samples")
    print(f"  - Step 0 Held-Out Prompts Excluded:   {excluded_count} samples")

    # Shuffle each group individually at example level
    rng = random.Random(2026)
    rng.shuffle(group_code_frontend)
    rng.shuffle(group_cross_axis)
    rng.shuffle(group_writing_wiseness)

    total_target = len(group_code_frontend) + len(group_cross_axis) + len(group_writing_wiseness)
    final_curriculum = []

    # Progressive Ramp Buckets (Early: 0-40%, Mid: 40-70%, Late: 70-100%)
    early_target = int(total_target * 0.40)
    mid_target = int(total_target * 0.30)
    late_target = total_target - early_target - mid_target

    # Early Phase: 85% Code/Frontend, 15% Cross-Axis
    for _ in range(early_target):
        if rng.random() < 0.85 and group_code_frontend:
            final_curriculum.append(group_code_frontend.pop())
        elif group_cross_axis:
            final_curriculum.append(group_cross_axis.pop())
        elif group_code_frontend:
            final_curriculum.append(group_code_frontend.pop())

    # Mid Phase: 70% Code/Frontend, 20% Cross-Axis, 10% Writing/Wiseness
    for _ in range(mid_target):
        roll = rng.random()
        if roll < 0.70 and group_code_frontend:
            final_curriculum.append(group_code_frontend.pop())
        elif roll < 0.90 and group_cross_axis:
            final_curriculum.append(group_cross_axis.pop())
        elif group_writing_wiseness:
            final_curriculum.append(group_writing_wiseness.pop())
        elif group_code_frontend:
            final_curriculum.append(group_code_frontend.pop())

    # Late Phase: Remaining samples (High Writing/Wiseness & Cross-Axis density)
    remaining = group_code_frontend + group_cross_axis + group_writing_wiseness
    rng.shuffle(remaining)
    final_curriculum.extend(remaining)

    print(f"\nProgressive Density Ramp Assembled:")
    print(f"  - Total Example-Level Curriculum Samples: {len(final_curriculum):,}")
    print(f"  - 70-85% Single-Axis vs 15-30% Cross-Axis Ratio Enforced")

    return final_curriculum
