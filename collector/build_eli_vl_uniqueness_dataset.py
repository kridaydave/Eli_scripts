import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
ANNOTATIONS_FILE = PROCESSED_DIR / "vision_taste_annotations.json"
OUTPUT_DATASET = PROCESSED_DIR / "training-data-eli-vl-uniqueness.jsonl"

UNIQUENESS_PROMPTS = [
    "<image>\nWhat specific design choices make this UI stand out as unique and high-taste rather than looking like a generic template?",
    "<image>\nAnalyze the unique design signature and micro-details of this interface.",
    "<image>\nIf a developer wanted to replicate the unique visual aesthetic and personality of this screenshot, what key visual rules should they follow?",
    "<image>\nDeconstruct what elevates this design beyond a generic Bootstrap/Tailwind component kit into a bespoke interface."
]

CREATIVE_ANGLES = [
    "ASYMMETRY & DYNAMIC GRID: Rejects symmetrical grid rigidity. Uses unexpected whitespace offsets and dynamic component alignment.",
    "OKLCH HIGH-TASTE PALETTE: Uses curated OKLCH color spaces with low-chroma dark slate backgrounds (`#09090b`) contrasted against high-chroma electric accent highlights.",
    "GLASSMORPHISM & DEPTH: Multi-layered spatial hierarchy with `backdrop-blur-md`, 1px inner highlight rings (`ring-1 ring-white/10`), and soft directional ambient shadows.",
    "TYPOGRAPHIC IDENTITY: Pairs bold display headings (`tracking-tight font-extrabold`) with high-legibility monospace metadata labels and fluid optical scaling.",
    "MICRO-INTERACTION INTENTION: Built with tactile feedback cues—active state downscaling (`active:scale-[0.98]`), customized accessibility focus rings, and skeleton loading matrix."
]

def main():
    if not ANNOTATIONS_FILE.exists():
        print("Error: annotations file missing")
        return

    raw_annotations = json.loads(ANNOTATIONS_FILE.read_text())
    uniqueness_entries = []

    for idx, (img_path, base_answer) in enumerate(raw_annotations.items(), 1):
        rng = random.Random(idx + 42)
        prompt = rng.choice(UNIQUENESS_PROMPTS)
        angle_sample = rng.sample(CREATIVE_ANGLES, 3)

        response = (
            f"**Unique Design Signature & Aesthetic Analysis:**\n\n"
            f"**1. Core Impression:**\n{base_answer}\n\n"
            f"**2. What Makes It Stand Out (Uniqueness Pillars):**\n"
            f"- **{angle_sample[0]}**\n"
            f"- **{angle_sample[1]}**\n"
            f"- **{angle_sample[2]}**\n\n"
            f"**3. Senior Pair-Programmer Rule of Thumb:**\n"
            f"To maintain this unique visual identity, avoid generic unstyled components. Implement exact 8pt padding, custom contrast ratios, and tailored micro-interactions."
        )

        entry = {
            "id": f"eli-vl-unique-{idx:04d}",
            "image": f"references/{img_path}",
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": response}
            ],
            "metadata": {
                "task": "design_uniqueness_and_aesthetic_signature",
                "target_model": "Eli-VL (Qwen-3-4B-Coder + Vision Adapter)"
            }
        }
        uniqueness_entries.append(entry)

    with open(OUTPUT_DATASET, "w", encoding="utf-8") as f:
        for item in uniqueness_entries:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nCreated Eli-VL Uniqueness Dataset:")
    print(f"  Total Multimodal Uniqueness Pairs: {len(uniqueness_entries)}")
    print(f"  Output Dataset File: {OUTPUT_DATASET}")
    print(f"  File Size: {OUTPUT_DATASET.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
