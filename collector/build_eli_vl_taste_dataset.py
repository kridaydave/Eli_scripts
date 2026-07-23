import json
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = PROJECT_ROOT / "references"
PROCESSED_DIR = PROJECT_ROOT / "processed"
ANNOTATIONS_FILE = PROCESSED_DIR / "vision_taste_annotations.json"
OUTPUT_DATASET = PROCESSED_DIR / "training-data-eli-vl-taste.jsonl"

def main():
    if not ANNOTATIONS_FILE.exists():
        print(f"Error: {ANNOTATIONS_FILE} not found.")
        return

    annotations = json.loads(ANNOTATIONS_FILE.read_text())
    dataset_entries = []

    for idx, (img_path, answer) in enumerate(annotations.items(), 1):
        rel_img_path = f"references/{img_path}"
        entry = {
            "id": f"eli-vl-taste-{idx:04d}",
            "image": rel_img_path,
            "conversations": [
                {
                    "from": "human",
                    "value": "<image>\nWhy is this design good, and what makes it unique?"
                },
                {
                    "from": "gpt",
                    "value": answer
                }
            ],
            "metadata": {
                "task": "visual_design_taste_critique",
                "target_model": "Eli-VL (Qwen-3-4B-Coder + Vision Adapter)"
            }
        }
        dataset_entries.append(entry)

    with open(OUTPUT_DATASET, "w", encoding="utf-8") as f:
        for item in dataset_entries:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nCreated Eli-VL Taste Multimodal Dataset:")
    print(f"  Total Multimodal Pairs: {len(dataset_entries)}")
    print(f"  Dataset File: {OUTPUT_DATASET}")
    print(f"  File Size: {OUTPUT_DATASET.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
