"""
Target-Weighted SFT Master Dataset Builder (`collector/build_simple_sft_train_jsonl.py`)
Epoch Model Suite 1 — Eli (4B)

Fixes Persona/Voice upweighting (155 core QA pairs x 20 = 3,100 pairs, 12.5% batch mix).

Unified Dataset Composition (24,792 total pairs):
- Mined Stack v2 Code (1x): 7,292 pairs (29.4%)
- FABLE 5 CoT Traces (1x): 8,530 pairs (34.4%)
- Repaired Wiseness (5x): 3,410 pairs (13.8%)
- Persona / Voice (20x): 3,100 pairs (12.5%)
- Cross-Axis Emergence (6x): 2,460 pairs (9.9%)
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
    print("Loading user's custom written answers (eli-custom-answers.md, personality-questions-eli.md)...")
    custom_pairs = []
    seen_prompts = set()

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
    return custom_pairs

def build_target_weighted_sft_train():
    rng = random.Random(2026)
    print("=== BUILDING TARGET-WEIGHTED INTERLEAVED ELI SFT TRAIN DATASET ===")

    build_standalone_code_review_train()

    # 1. Mined Stack v2 Code (1x - Target: ~30%)
    stack_v2_file = PROCESSED_DIR / "raw_stack_v2_mined.jsonl"
    mined_code_pairs = []
    if stack_v2_file.exists():
        with open(stack_v2_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    mined_code_pairs.append(json.loads(line))
    print(f"  [1/5] Stack v2 Code Base (1x): {len(mined_code_pairs):,} pairs")

    # 2. FABLE 5 CoT Traces (1x - Target: ~35%)
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
                            "conversations": convs,
                            "metadata": {
                                "source_type": "fable5_crownelius_traces",
                                "pillar": "cot_reasoning",
                                "license": "Apache-2.0",
                                "is_cross_axis": True
                            }
                        })
    print(f"  [2/5] FABLE 5 CoT Traces (1x): {len(fable_cot_pairs):,} pairs")

    # 3. Persona / Voice QA Pairs (Upsampled 20x - Target: ~12.5%)
    raw_user_custom = load_user_custom_answers()
    user_custom_pairs = []
    registers = ["light-personality", "pure-direct", "maximal-wit"]
    for rep in range(20):
        for idx, item in enumerate(raw_user_custom):
            item_copy = json.loads(json.dumps(item))
            item_copy["metadata"]["register"] = registers[(idx + rep) % len(registers)]
            user_custom_pairs.append(item_copy)
    print(f"  [3/5] Persona/Voice Pairs (Upsampled 20x): {len(user_custom_pairs):,} pairs (from {len(raw_user_custom)} unique)")

    # 4. Repaired Wiseness Data (Upsampled 5x - Target: ~14%)
    wiseness_file = PROCESSED_DIR / "training-data-eli-wiseness.jsonl"
    raw_wiseness_pairs = []
    if wiseness_file.exists():
        with open(wiseness_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    raw_wiseness_pairs.append(json.loads(line))
    
    upsampled_wiseness = []
    for rep in range(5):
        for item in raw_wiseness_pairs:
            item_copy = json.loads(json.dumps(item))
            upsampled_wiseness.append(item_copy)
    print(f"  [4/5] Repaired Wiseness Data (Upsampled 5x): {len(upsampled_wiseness):,} pairs (from {len(raw_wiseness_pairs)} unique)")

    # 5. Cross-Axis Emergence & Pushback (Upsampled 6x - Target: ~10%)
    cross_axis_file = PROCESSED_DIR / "training-data-eli-cross-axis.jsonl"
    raw_cross_axis_pairs = []
    if cross_axis_file.exists():
        with open(cross_axis_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    raw_cross_axis_pairs.append(json.loads(line))

    upsampled_cross_axis = []
    for rep in range(6):
        for item in raw_cross_axis_pairs:
            item_copy = json.loads(json.dumps(item))
            upsampled_cross_axis.append(item_copy)
    print(f"  [5/5] Cross-Axis Emergence Data (Upsampled 6x): {len(upsampled_cross_axis):,} pairs (from {len(raw_cross_axis_pairs)} unique)")

    # Combine all modules into unified dataset
    all_pairs = mined_code_pairs + fable_cot_pairs + user_custom_pairs + upsampled_wiseness + upsampled_cross_axis
    total_len = len(all_pairs)

    print("\n=== FINAL TARGET-WEIGHTED DATASET COMPOSITION ===")
    print(f"  - Mined Stack v2 Code:     {len(mined_code_pairs):,}\t({len(mined_code_pairs)/total_len*100:.1f}%)")
    print(f"  - FABLE 5 CoT Traces:      {len(fable_cot_pairs):,}\t({len(fable_cot_pairs)/total_len*100:.1f}%)")
    print(f"  - Persona / Voice:         {len(user_custom_pairs):,}\t({len(user_custom_pairs)/total_len*100:.1f}%)")
    print(f"  - Repaired Wiseness:       {len(upsampled_wiseness):,}\t({len(upsampled_wiseness)/total_len*100:.1f}%)")
    print(f"  - Cross-Axis & Pushback:   {len(upsampled_cross_axis):,}\t({len(upsampled_cross_axis)/total_len*100:.1f}%)")
    print(f"  TOTAL UNIFIED SFT SAMPLES: {total_len:,} pairs")

    # Example-level shuffling across whole dataset for uniform interleaving from Epoch 1
    rng.shuffle(all_pairs)

    # 1. Write Alpaca format (`processed/eli-sft-train.jsonl`)
    with open(OUTPUT_SFT_TRAIN, "w", encoding="utf-8") as f:
        for item in all_pairs:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # 2. Write ShareGPT / ChatML formatted dataset (`processed/eli-sft-train-formatted.jsonl`)
    formatted_records = []
    for idx, item in enumerate(all_pairs):
        meta = item.get("metadata", {})
        if "conversations" in item:
            convs = item["conversations"]
        else:
            inst = item.get("instruction", "")
            out = item.get("output", "")
            convs = [
                {"from": "human", "value": inst},
                {"from": "gpt", "value": out}
            ]
        
        formatted_records.append({
            "id": f"eli_sft_{idx:06d}",
            "conversations": convs,
            "metadata": meta
        })

    with open(OUTPUT_SFT_TRAIN_FORMATTED, "w", encoding="utf-8") as f:
        for rec in formatted_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nSuccessfully generated master target-weighted dataset files:")
    print(f"  - Main SFT Train File (Alpaca):  {OUTPUT_SFT_TRAIN} ({OUTPUT_SFT_TRAIN.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"  - Formatted SFT File (ShareGPT): {OUTPUT_SFT_TRAIN_FORMATTED} ({OUTPUT_SFT_TRAIN_FORMATTED.stat().st_size / 1024 / 1024:.2f} MB)")

    inject_script = PROJECT_ROOT / "collector" / "inject_chat_data.py"
    if inject_script.exists():
        print("\n=== AUTO-INJECTING CHAT, REFUSAL, TASTE & AGENTIC SESSIONS ===")
        import subprocess, sys
        subprocess.run([sys.executable, str(inject_script)], check=True)

if __name__ == "__main__":
    build_target_weighted_sft_train()

