import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
BRAND_ANNOTATIONS_FILE = PROCESSED_DIR / "brand_uniqueness_annotations.json"
OUTPUT_DATASET = PROCESSED_DIR / "training-data-eli-vl-uniqueness-user.jsonl"

UNIQUENESS_PROMPTS = [
    "<image>\nAnalyze the visual brand identity and design choices shown in this image. Why does it feel unique and high-taste rather than looking like a generic template?",
    "<image>\nDeconstruct the aesthetic signature, branding decisions, and micro-details of this visual design.",
    "<image>\nIf a senior frontend designer wanted to capture the exact personality and artistic direction of this asset, what key design choices should they focus on?",
    "<image>\nWhat specific visual, typographic, or layout details elevate this design exploration beyond boilerplate design templates?"
]

def main():
    if not BRAND_ANNOTATIONS_FILE.exists():
        print(f"Error: {BRAND_ANNOTATIONS_FILE} not found.")
        return

    annotations = json.loads(BRAND_ANNOTATIONS_FILE.read_text())
    dataset_entries = []

    for idx, (img_name, user_answer) in enumerate(annotations.items(), 1):
        rng = random.Random(idx + 1337)
        prompt = rng.choice(UNIQUENESS_PROMPTS)

        entry = {
            "id": f"eli-vl-unique-user-{idx:03d}",
            "image": f"references/{img_name}",
            "conversations": [
                {
                    "from": "human",
                    "value": prompt
                },
                {
                    "from": "gpt",
                    "value": user_answer
                }
            ],
            "metadata": {
                "source": "user_authentic_manual_annotations",
                "task": "brand_identity_and_design_uniqueness",
                "target_model": "Eli-VL (Qwen-3-4B-Coder + Vision Adapter)"
            }
        }
        dataset_entries.append(entry)

    with open(OUTPUT_DATASET, "w", encoding="utf-8") as f:
        for item in dataset_entries:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nSuccessfully compiled User Authentic Uniqueness Dataset:")
    print(f"  Total Multimodal Pairs: {len(dataset_entries)}")
    print(f"  Dataset File: {OUTPUT_DATASET}")
    print(f"  File Size: {OUTPUT_DATASET.stat().st_size / 1024:.2f} KB")

if __name__ == "__main__":
    main()
