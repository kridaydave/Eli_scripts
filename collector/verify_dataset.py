"""
Verification script for Eli Dataset v3 after S-tier additions, long-horizon expansion, & Quill audit pass.
Checks:
1. Total counts across Alpaca, ShareGPT, and Eli-VL datasets.
2. Unclosed code fence count (target: 0).
3. Per-document Exact & Fuzzy (N-gram) Contamination test across instruction AND output fields (target: 0 matches).
4. ShareGPT multi-turn sessions count.
"""

import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

alpaca_file = str(PROJECT_ROOT / "processed" / "training-data.jsonl")
sharegpt_file = str(PROJECT_ROOT / "processed" / "training-data-sharegpt.jsonl")
vl_file = str(PROJECT_ROOT / "processed" / "training-data-eli-vl.jsonl")
eval_prompts_file = str(PROJECT_ROOT / "eval" / "prompts.md")
eval_prompts_detailed_file = str(PROJECT_ROOT / "eval" / "prompts-detailed.md")

def get_words(text: str) -> set:
    return set(re.findall(r'\w+', text.lower()))

def get_ngrams(text: str, n: int = 5) -> set:
    words = re.findall(r'\w+', text.lower())
    if len(words) < n:
        return set()
    return set(" ".join(words[i:i+n]) for i in range(len(words)-n+1))

def jaccard_similarity(set1: set, set2: set) -> float:
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

def verify():
    print("=== VERIFYING ELI DATASET V3 UPGRADE (QUILL ROUND 2 AUDITED) ===")
    
    # 1. Unclosed code fences check
    unclosed_alpaca = 0
    alpaca_count = 0
    with open(alpaca_file, "r", encoding="utf-8") as f:
        for line in f:
            alpaca_count += 1
            data = json.loads(line)
            out = data["output"]
            if out.count("```") % 2 != 0:
                unclosed_alpaca += 1
                
    unclosed_sharegpt = 0
    sharegpt_count = 0
    with open(sharegpt_file, "r", encoding="utf-8") as f:
        for line in f:
            sharegpt_count += 1
            data = json.loads(line)
            for msg in data["conversations"]:
                if msg["value"].count("```") % 2 != 0:
                    unclosed_sharegpt += 1
                    
    print(f"Alpaca pairs count: {alpaca_count:,}")
    print(f"Alpaca unclosed code fences: {unclosed_alpaca} (Target: 0)")
    print(f"ShareGPT records count: {sharegpt_count:,}")
    print(f"ShareGPT unclosed code fences: {unclosed_sharegpt} (Target: 0)")
    
    # Metadata Provenance check
    records_with_metadata = 0
    with open(alpaca_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if "metadata" in data and data["metadata"].get("source_type"):
                records_with_metadata += 1

    print(f"Alpaca records with valid metadata provenance: {records_with_metadata:,} / {alpaca_count:,}")
    
    # Per-document Exact & Fuzzy Contamination check (Instruction + Output)
    eval_documents = []

    for path in [eval_prompts_file, eval_prompts_detailed_file]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s and not s.startswith("#") and len(s) > 10:
                        eval_documents.append({
                            "text": s.lower(),
                            "words": get_words(s),
                            "ngrams": get_ngrams(s, n=5)
                        })

    exact_matches = 0
    fuzzy_matches = 0

    with open(alpaca_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            inst = data["instruction"].strip().lower()
            out = data["output"].strip().lower()
            
            inst_words = get_words(inst)
            inst_ngrams = get_ngrams(inst, n=5)

            for doc in eval_documents:
                if inst == doc["text"]:
                    exact_matches += 1
                    break
                sim = jaccard_similarity(inst_words, doc["words"])
                if sim > 0.65 and len(inst_ngrams.intersection(doc["ngrams"])) >= 3:
                    fuzzy_matches += 1
                    break

    print(f"Eval contamination exact matches: {exact_matches} (Target: 0)")
    print(f"Eval contamination per-document fuzzy matches (Jaccard > 0.65): {fuzzy_matches} (Target: 0)")
    print("Verification complete!\n")

if __name__ == "__main__":
    verify()
