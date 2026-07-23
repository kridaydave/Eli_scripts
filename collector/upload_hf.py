"""
Hugging Face Dataset Uploader for Epoch Model Suite 1 (Eli)
User: kridaydave

Uploads processed training files to Hugging Face Dataset Hub: kridaydave/eli-dataset-v3
"""

import os
import json
import sys
from pathlib import Path

HF_TOKEN = os.environ.get("HF_TOKEN")
REPO_ID = "kridaydave/eli-dataset-v3"
ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "processed"

DATASET_README = """---
license: apache-2.0
pretty_name: Epoch Eli Dataset v3 — S-Tier Coding & Agentic Fine-Tuning Corpus
language:
- en
task_categories:
- text-generation
tags:
- code
- agentic-coding
- sharegpt
- alpaca
- vision-language
- qwen
- epoch
---

# Epoch Model Suite 1 — Eli Dataset v3

Dataset curated for fine-tuning **Eli** (~3-7B dense coding model, based on Qwen 3-4B).

## Dataset Composition

- **Total S-Tier Samples**: 23,138 pairs
- **Backend Code (40.5%)**: 9,360 clean pairs across Linux, Kubernetes, Tokio, FastAPI, Hyper, Gin.
- **Frontend Code & Design Systems (22.9%)**: 5,290 pairs across shadcn/ui, Radix, Mantine, Tailwind, Stripe, Vercel, Apple HIG specs.
- **Eli Personality (30.2%)**: 6,988 pairs (1,747 unique Q&As oversampled 4x) capturing Eli's casual, direct, fluff-free persona.
- **Fable-5 Pi Agent Traces (4.3%)**: 1,000 real agentic execution traces (CoT reasoning, Bash/Read/Edit actions).
- **Agentic Open-Ended Apps (2.2%)**: 500 unique single-file apps and microservices.
- **Eli-VL Multimodal**: 192 UI WebP screenshot-to-code pairs (`training-data-eli-vl.jsonl`).

## Files Included

- `training-data.jsonl`: Alpaca format (`instruction`, `output`).
- `training-data-sharegpt.jsonl`: ShareGPT / ChatML format (`conversations`).
- `training-data-eli-vl.jsonl`: Multimodal screenshot-to-code pairs.
- `dataset-stats.json`: Automated statistical breakdown.
"""

def upload_to_hf():
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("Installing huggingface_hub...")
        os.system(f"{sys.executable} -m pip install -q huggingface_hub")
        from huggingface_hub import HfApi, create_repo

    api = HfApi(token=HF_TOKEN)

    print(f"=== Creating/Verifying Dataset Repo: {REPO_ID} ===")
    try:
        create_repo(repo_id=REPO_ID, repo_type="dataset", private=False, token=HF_TOKEN, exist_ok=True)
        print(f"Repo {REPO_ID} is ready.")
    except Exception as e:
        print(f"Note on create_repo: {e}")

    # Write README.md into processed folder
    readme_path = PROCESSED / "README.md"
    readme_path.write_text(DATASET_README, encoding="utf-8")

    files_to_upload = [
        ("training-data.jsonl", "training-data.jsonl"),
        ("training-data-sharegpt.jsonl", "training-data-sharegpt.jsonl"),
        ("training-data-eli-vl.jsonl", "training-data-eli-vl.jsonl"),
        ("eli-vl-manifest.json", "eli-vl-manifest.json"),
        ("dataset-stats.json", "dataset-stats.json"),
        ("README.md", "README.md"),
    ]

    print("\n=== Uploading Files to Hugging Face Hub ===")
    for local_name, remote_name in files_to_upload:
        local_file = PROCESSED / local_name
        if local_file.exists():
            print(f"  Uploading {local_name} ({local_file.stat().st_size / 1e6:.2f} MB)...")
            api.upload_file(
                path_or_fileobj=str(local_file),
                path_in_repo=remote_name,
                repo_id=REPO_ID,
                repo_type="dataset",
            )
            print(f"  ✓ {remote_name} uploaded successfully.")
        else:
            print(f"  Warning: {local_file} not found, skipping.")

    print(f"\n🚀 Dataset successfully published to Hugging Face!")
    print(f"👉 Dataset URL: https://huggingface.co/datasets/{REPO_ID}")

if __name__ == "__main__":
    upload_to_hf()
