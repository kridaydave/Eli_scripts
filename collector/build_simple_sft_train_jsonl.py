"""
Simple SFT Training Dataset Builder (`processed/eli-sft-train.jsonl` & `processed/eli-sft-train-formatted.jsonl`)
Epoch Model Suite 1 — Eli (4B)

Keeps original dataset files intact, expands Eli's persona voice, keeps Fable 5 CoT traces intact,
and builds both Alpaca (`eli-sft-train.jsonl`) and ShareGPT formatted (`eli-sft-train-formatted.jsonl`) datasets.
"""

import json
import re
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_SFT_TRAIN = PROCESSED_DIR / "eli-sft-train.jsonl"
OUTPUT_SFT_TRAIN_FORMATTED = PROCESSED_DIR / "eli-sft-train-formatted.jsonl"
OUTPUT_CODE_REVIEW_TRAIN = PROCESSED_DIR / "train_code_review.jsonl"

def build_standalone_code_review_train():
    print("Building standalone code review training set (`processed/train_code_review.jsonl`)...")
    cr_file = DATA_DIR / "train_code_review.jsonl"
    cr_pairs = []
    
    if cr_file.exists():
        with open(cr_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                ctx = item.get("context", "")
                code = item.get("code", "")
                lang = item.get("language", "code")
                resp = item.get("response", "")
                cell = item.get("cell", "")
                
                instruction = f"Context: {ctx}\n\nCode Snippet:\n```{lang}\n{code.strip()}\n```"
                
                cr_pairs.append({
                    "instruction": instruction,
                    "output": resp.strip(),
                    "metadata": {
                        "source_type": "train_code_review",
                        "cell": cell,
                        "language": lang,
                        "is_emergence_train_set": True
                    }
                })
                
    with open(OUTPUT_CODE_REVIEW_TRAIN, "w", encoding="utf-8") as f:
        for item in cr_pairs:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"  Saved {len(cr_pairs):,} standalone code review training pairs to {OUTPUT_CODE_REVIEW_TRAIN}.")

def load_user_custom_answers():
    print("Loading user's custom written answers (eli-custom-answers.md, personality-questions-eli.md, personality-questions-eli-frontend.md)...")
    custom_pairs = []
    seen_prompts = set()

    # 1. Parse eli-custom-answers.md
    custom_ans_file = DATA_DIR / "eli-custom-answers.md"
    if custom_ans_file.exists():
        raw_ca = custom_ans_file.read_text(encoding="utf-8")
        blocks = raw_ca.split("#### ")
        for b in blocks:
            if not b.strip() or "*Prompt*:" not in b or "*Your Answer*:" not in b:
                continue
            prompt_match = re.search(r'\*Prompt\*:\s*"?(.*?)"?\n', b)
            answer_match = re.search(r'\*Your Answer\*:\s*(.*)', b, re.DOTALL)
            if prompt_match and answer_match:
                prompt_str = prompt_match.group(1).strip().strip('"')
                answer_str = answer_match.group(1).strip()
                if "---" in answer_str:
                    answer_str = answer_str.split("---")[0].strip()
                if prompt_str and answer_str and prompt_str not in seen_prompts:
                    seen_prompts.add(prompt_str)
                    custom_pairs.append({
                        "instruction": prompt_str,
                        "output": answer_str,
                        "metadata": {
                            "source_type": "user_custom_written_answers",
                            "author": "founder_custom",
                            "pillar": "wiseness_and_voice",
                            "is_custom_answer": True
                        }
                    })

    # 2. Parse personality-questions-eli.md & personality-questions-eli-frontend.md with regex
    files = [
        DATA_DIR / "personality-questions-eli.md",
        DATA_DIR / "personality-questions-eli-frontend.md"
    ]

    for fpath in files:
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8")
        pattern = r'(?:^|\n)\d+\.\s*(.*?)\n\s*A\.\s*(.*?)(?=\n\d+\.|\n##|\n---|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        for q, a in matches:
            q_clean = q.strip()
            a_clean = a.strip()
            if q_clean and a_clean and q_clean not in seen_prompts:
                seen_prompts.add(q_clean)
                custom_pairs.append({
                    "instruction": q_clean,
                    "output": a_clean,
                    "metadata": {
                        "source_type": "user_custom_written_answers",
                        "author": "user_custom",
                        "pillar": "wiseness_and_voice",
                        "is_custom_answer": True
                    }
                })

    print(f"  Parsed {len(custom_pairs):,} unique authentic Eli personality & voice QA pairs.")

    # Upweight custom persona voice by 10x with balanced registers to ensure high voice presence
    expanded_custom_pairs = []
    registers = ["light-personality", "pure-direct", "maximal-wit"]

    MULTIPLIER = 10
    for rep in range(MULTIPLIER):
        for idx, item in enumerate(custom_pairs):
            item_copy = json.loads(json.dumps(item))
            reg = registers[(idx + rep) % len(registers)]
            item_copy["metadata"]["register"] = reg
            expanded_custom_pairs.append(item_copy)

    print(f"  Expanded to {len(expanded_custom_pairs):,} total persona training samples (10x upweighted across 3 registers).")
    return expanded_custom_pairs

def build_simple_sft_train_jsonl():
    print("=== BUILDING ELI SFT TRAIN DATASETS (`eli-sft-train.jsonl` & `eli-sft-train-formatted.jsonl`) ===")

    # Standalone Code Review Dataset for Emergence Experiment
    build_standalone_code_review_train()

    # User Custom Written Answers (Expanded)
    user_custom_pairs = load_user_custom_answers()

    # Custom Cross-Axis Joint Emergence Pairs
    cross_axis_file = PROCESSED_DIR / "training-data-eli-cross-axis.jsonl"
    cross_axis_pairs = []
    if cross_axis_file.exists():
        with open(cross_axis_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    cross_axis_pairs.append(json.loads(line))
        print(f"  Loaded {len(cross_axis_pairs):,} custom Cross-Axis Joint Emergence pairs.")

    # Real Mined Stack v2 Code
    stack_v2_file = PROCESSED_DIR / "raw_stack_v2_mined.jsonl"
    mined_code_pairs = []
    if stack_v2_file.exists():
        with open(stack_v2_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    mined_code_pairs.append(json.loads(line))
        print(f"  Loaded {len(mined_code_pairs):,} mined Stack v2 real gold code pairs.")

    # FABLE.5 CoT Traces (Kept Intact)
    fable_file = PROCESSED_DIR / "training-data-fable5-curated.jsonl"
    fable_cot_pairs = []
    if fable_file.exists():
        with open(fable_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    convs = entry.get("conversations", [])
                    if len(convs) >= 2:
                        fable_cot_pairs.append({
                            "instruction": convs[0]["value"],
                            "output": convs[1]["value"],
                            "metadata": {
                                "source_type": "fable5_crownelius_traces",
                                "pillar": "cot_reasoning",
                                "license": "Apache-2.0",
                                "is_cross_axis": True
                            }
                        })
        print(f"  Loaded {len(fable_cot_pairs):,} FABLE.5 CoT trace pairs.")

    # Combine User Custom Answers + Mined Code + Custom Emergence + Fable5 CoT Reasoning
    all_sft_train = user_custom_pairs + mined_code_pairs + cross_axis_pairs + fable_cot_pairs

    # Apply Progressive Density Curriculum
    from curriculum_sorter import load_held_out_prompts, apply_progressive_curriculum
    held_out_sigs = load_held_out_prompts()
    curriculum_sft_train = apply_progressive_curriculum(all_sft_train, held_out_sigs)

    print(f"\nTotal Simple SFT Train Dataset Size: {len(curriculum_sft_train):,} pairs")

    # 1. Write original Alpaca format (`processed/eli-sft-train.jsonl`)
    with open(OUTPUT_SFT_TRAIN, "w", encoding="utf-8") as f:
        for item in curriculum_sft_train:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # 2. Write ShareGPT / ChatML formatted dataset (`processed/eli-sft-train-formatted.jsonl`)
    formatted_records = []
    for idx, item in enumerate(curriculum_sft_train):
        inst = item.get("instruction", "")
        out = item.get("output", "")
        meta = item.get("metadata", {})
        formatted_records.append({
            "id": f"eli_sft_{idx:06d}",
            "conversations": [
                {"from": "human", "value": inst},
                {"from": "gpt", "value": out}
            ],
            "metadata": meta
        })

    with open(OUTPUT_SFT_TRAIN_FORMATTED, "w", encoding="utf-8") as f:
        for rec in formatted_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nSuccessfully generated dataset files:")
    print(f"  - Emergence Code Review Train File: {OUTPUT_CODE_REVIEW_TRAIN}")
    print(f"  - Main SFT Train File (Alpaca):     {OUTPUT_SFT_TRAIN} ({OUTPUT_SFT_TRAIN.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"  - Formatted SFT File (ShareGPT):    {OUTPUT_SFT_TRAIN_FORMATTED} ({OUTPUT_SFT_TRAIN_FORMATTED.stat().st_size / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    build_simple_sft_train_jsonl()
