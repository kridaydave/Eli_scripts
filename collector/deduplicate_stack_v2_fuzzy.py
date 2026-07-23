"""
Fast Stack v2 Fuzzy Near-Duplicate Pruner (P4 Resolution)
Epoch Eli Dataset v3 - Near-Duplicate Cleanup

Uses fast 4-gram hashing with sliding window (window size: 100)
threshold = 0.70 to strip near-duplicate boilerplate from raw_stack_v2_mined.jsonl.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
STACK_V2_FILE = PROCESSED_DIR / "raw_stack_v2_mined.jsonl"

def get_ngram_hashes(text: str, n: int = 4) -> set:
    words = text.split()
    if len(words) < n:
        return {hash(text)}
    return {hash(" ".join(words[i:i+n])) for i in range(min(len(words) - n + 1, 200))}

def jaccard_similarity(set1: set, set2: set) -> float:
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def fuzzy_deduplicate(threshold: float = 0.70):
    print(f"=== FAST FUZZY DEDUPLICATING STACK V2 MINED CODE (Threshold: {threshold}) ===")
    
    if not STACK_V2_FILE.exists():
        print("Stack v2 file does not exist.")
        return

    records = []
    with open(STACK_V2_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Initial Stack v2 count: {len(records):,}")

    unique_records = []
    seen_ngram_sets = []
    pruned_count = 0

    for idx, rec in enumerate(records):
        output_text = rec.get("output", "")
        ngrams = get_ngram_hashes(output_text, n=4)
        
        is_near_dup = False
        check_window = seen_ngram_sets[-150:]
        for existing_ngrams in check_window:
            sim = jaccard_similarity(ngrams, existing_ngrams)
            if sim >= threshold:
                is_near_dup = True
                break
                
        if is_near_dup:
            pruned_count += 1
        else:
            unique_records.append(rec)
            seen_ngram_sets.append(ngrams)

    print(f"\nFuzzy Deduplication Complete!")
    print(f"  - Initial Records: {len(records):,}")
    print(f"  - Near-Duplicates Pruned: {pruned_count:,}")
    print(f"  - Final Clean Stack v2 Records: {len(unique_records):,}")

    with open(STACK_V2_FILE, "w", encoding="utf-8") as f:
        for rec in unique_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    fuzzy_deduplicate(threshold=0.70)
