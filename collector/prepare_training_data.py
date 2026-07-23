"""
Dataset Preparation Script for Eli (Qwen 3-4B / 2.5-Coder) Training
Converts data/train_code_review.jsonl into ChatML format for Unsloth / SFTTrainer.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_ROOT / "data" / "train_code_review.jsonl"
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = PROCESSED_DIR / "eli-sft-train.jsonl"

SYSTEM_PROMPT = (
    "You are Eli, a senior full-stack software engineer. "
    "You provide surgical code reviews, carefully calibrating your directness, tone, "
    "and uncertainty based on the stakes and confidence of the issue."
)

def format_code_review_prompt(context: str, code: str, language: str) -> str:
    return (
        f"Please review the following {language} snippet:\n\n"
        f"Context: {context}\n"
        f"```{language}\n"
        f"{code.strip()}\n"
        f"```"
    )

def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {RAW_FILE}")

    processed_count = 0
    records = []

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)

            user_msg = format_code_review_prompt(
                context=item["context"],
                code=item["code"],
                language=item["language"]
            )
            assistant_msg = item["response"]

            chatml_entry = {
                "id": item["id"],
                "cell": item["cell"],
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg}
                ]
            }
            records.append(chatml_entry)
            processed_count += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in records:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"=== DATASET PREPARATION COMPLETE ===")
    print(f"  Source File: {RAW_FILE}")
    print(f"  Output File: {OUTPUT_FILE}")
    print(f"  Total Processed Examples: {processed_count}")

if __name__ == "__main__":
    main()
