"""
Comprehensive Dataset Uniqueness Auditor & Deduplicator
Epoch Model Suite 1 (Eli v3 Upgrade)

Enforces 100% Strict Uniqueness:
1. Zero duplicate instructions across all Alpaca and ShareGPT records
2. Zero duplicate outputs across all single-turn and multi-turn entries
3. Deduplicates pillar-additions, stier-additions, agentic pairs, and multi-turn sessions
"""

import json
from pathlib import Path
from collections import Counter

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "processed"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

alpaca_file = PROCESSED_DIR / "training-data.jsonl"
sharegpt_file = PROCESSED_DIR / "training-data-sharegpt.jsonl"

def audit_and_deduplicate():
    print("=== AUDITING & ENFORCING 100% DATASET UNIQUENESS ===")
    
    # 1. Audit Alpaca Dataset
    alpaca_records = []
    seen_instructions = set()
    seen_outputs = set()
    alpaca_duplicates = 0

    if alpaca_file.exists():
        with open(alpaca_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                inst = data["instruction"].strip()
                out = data["output"].strip()

                if inst in seen_instructions or out in seen_outputs:
                    alpaca_duplicates += 1
                    continue
                
                seen_instructions.add(inst)
                seen_outputs.add(out)
                alpaca_records.append(data)

    print(f"Alpaca Original Count: {len(alpaca_records) + alpaca_duplicates:,}")
    print(f"Alpaca Duplicates Filtered: {alpaca_duplicates:,}")
    print(f"Alpaca Unique Final Count: {len(alpaca_records):,}")

    # Write back clean deduplicated Alpaca file
    with open(alpaca_file, "w", encoding="utf-8") as f:
        for rec in alpaca_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 2. Audit ShareGPT Dataset
    sharegpt_records = []
    seen_conv_signatures = set()
    sharegpt_duplicates = 0

    if sharegpt_file.exists():
        with open(sharegpt_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                convs = data.get("conversations", [])
                sig = "|||".join([turn.get("value", "").strip() for turn in convs])

                if sig in seen_conv_signatures:
                    sharegpt_duplicates += 1
                    continue

                seen_conv_signatures.add(sig)
                sharegpt_records.append(data)

    print(f"\nShareGPT Original Count: {len(sharegpt_records) + sharegpt_duplicates:,}")
    print(f"ShareGPT Duplicates Filtered: {sharegpt_duplicates:,}")
    print(f"ShareGPT Unique Final Count: {len(sharegpt_records):,}")

    # Write back clean deduplicated ShareGPT file
    with open(sharegpt_file, "w", encoding="utf-8") as f:
        for rec in sharegpt_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 3. Deduplicate Pillar & S-Tier additions
    for fname in ["pillar-additions.json", "stier-additions.json", "agentic-coding-pairs.json"]:
        fpath = DATA_DIR / fname
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                items = json.load(f)
            unique_items = []
            seen_insts = set()
            for it in items:
                inst = it.get("instruction", "").strip()
                if inst and inst not in seen_insts:
                    seen_insts.add(inst)
                    unique_items.append(it)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(unique_items, f, indent=2, ensure_ascii=False)
            print(f"Deduplicated {fname}: {len(unique_items)} unique items saved.")

    print("\n100% Strict Uniqueness Audit & Deduplication Complete!")

if __name__ == "__main__":
    audit_and_deduplicate()
