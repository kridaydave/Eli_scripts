import json
import os
import re
import glob
from pathlib import Path
from collections import Counter, defaultdict

PROJECT_ROOT = Path("/home/kriday/Desktop/epoch-1")
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = PROJECT_ROOT / "processed"
EVAL_DIR = PROJECT_ROOT / "eval"

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

def audit_jsonl(file_path):
    stats = {
        "file_name": file_path.name,
        "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
        "total_lines": 0,
        "parse_errors": 0,
        "empty_fields": 0,
        "unclosed_code_fences": 0,
        "exact_duplicates": 0,
        "prompt_lengths": [],
        "output_lengths": [],
        "sources": Counter(),
        "pillars": Counter(),
        "sample_keys": set(),
        "dpo_chosen_equals_rejected": 0,
        "vision_missing_images": 0,
        "has_images_count": 0
    }
    
    seen_prompts = set()
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            stats["total_lines"] += 1
            try:
                data = json.loads(line)
            except Exception:
                stats["parse_errors"] += 1
                continue
            
            if isinstance(data, dict):
                stats["sample_keys"].update(data.keys())
                
                prompt = ""
                output = ""
                
                if "instruction" in data:
                    prompt = data.get("instruction") or ""
                    output = data.get("output") or ""
                elif "conversations" in data:
                    convs = data.get("conversations", [])
                    if isinstance(convs, list) and len(convs) > 0:
                        prompt = convs[0].get("value", "")
                        output = " ".join([str(c.get("value", "")) for c in convs[1:]])
                elif "messages" in data:
                    msgs = data.get("messages", [])
                    if isinstance(msgs, list) and len(msgs) > 0:
                        prompt = msgs[0].get("content", "")
                        output = " ".join([str(m.get("content", "")) for m in msgs[1:]])
                elif "prompt" in data and ("chosen" in data or "response" in data):
                    prompt = data.get("prompt", "")
                    output = data.get("chosen", "") or data.get("response", "")
                    if "rejected" in data and data.get("chosen") == data.get("rejected"):
                        stats["dpo_chosen_equals_rejected"] += 1
                
                if not prompt or not output:
                    stats["empty_fields"] += 1
                    
                if prompt in seen_prompts:
                    stats["exact_duplicates"] += 1
                else:
                    seen_prompts.add(prompt)
                    
                # Code fences check
                combined_text = str(prompt) + "\n" + str(output)
                if combined_text.count("```") % 2 != 0:
                    stats["unclosed_code_fences"] += 1
                    
                # Lengths in tokens (approx word count)
                p_words = len(re.findall(r'\w+', str(prompt)))
                o_words = len(re.findall(r'\w+', str(output)))
                stats["prompt_lengths"].append(p_words)
                stats["output_lengths"].append(o_words)
                
                # Metadata
                meta = data.get("metadata", {})
                if isinstance(meta, dict):
                    src = meta.get("source_type") or meta.get("source") or "unknown"
                    pil = meta.get("pillar") or "unspecified"
                    stats["sources"][src] += 1
                    stats["pillars"][pil] += 1
                
                # Vision check
                images = data.get("images") or data.get("image") or (meta.get("images") if isinstance(meta, dict) else None)
                if images:
                    stats["has_images_count"] += 1
                    if isinstance(images, str):
                        images = [images]
                    for img in images:
                        if isinstance(img, str) and not os.path.exists(img) and not os.path.exists(str(PROJECT_ROOT / img)):
                            stats["vision_missing_images"] += 1
                            
    stats["sample_keys"] = list(stats["sample_keys"])
    return stats

def summarize_lengths(arr):
    if not arr:
        return {"min": 0, "max": 0, "mean": 0, "p50": 0, "p90": 0, "p99": 0}
    s = sorted(arr)
    n = len(s)
    return {
        "min": s[0],
        "max": s[-1],
        "mean": round(sum(s) / n, 1),
        "p50": s[n // 2],
        "p90": s[int(n * 0.90)],
        "p99": s[int(n * 0.99)]
    }

def run_full_audit():
    print("Starting Comprehensive Dataset Audit...")
    
    processed_files = list(PROCESSED_DIR.glob("*.jsonl"))
    data_files = list(DATA_DIR.glob("*.jsonl"))
    all_jsonl_files = sorted(set(processed_files + data_files))
    
    results = {}
    
    for fpath in all_jsonl_files:
        print(f"Auditing JSONL: {fpath.name}...")
        st = audit_jsonl(fpath)
        st["prompt_len_summary"] = summarize_lengths(st["prompt_lengths"])
        st["output_len_summary"] = summarize_lengths(st["output_lengths"])
        del st["prompt_lengths"]
        del st["output_lengths"]
        results[fpath.name] = st

    # Evaluate held out test contamination
    held_out_file = DATA_DIR / "held_out_transfer_test.jsonl"
    eval_prompts_file = EVAL_DIR / "prompts.md"
    eval_prompts_det_file = EVAL_DIR / "prompts-detailed.md"
    
    eval_docs = []
    if held_out_file.exists():
        with open(held_out_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                d = json.loads(line)
                p = d.get("instruction") or (d.get("conversations")[0]["value"] if "conversations" in d and d["conversations"] else "")
                if p:
                    eval_docs.append({"src": "held_out_transfer_test", "text": p.strip().lower(), "words": get_words(p), "ngrams": get_ngrams(p, 5)})
                    
    for ef in [eval_prompts_file, eval_prompts_det_file]:
        if ef.exists():
            with open(ef, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s and not s.startswith("#") and len(s) > 10:
                        eval_docs.append({"src": ef.name, "text": s.lower(), "words": get_words(s), "ngrams": get_ngrams(s, 5)})
                        
    print(f"\nTotal test/eval documents collected for contamination audit: {len(eval_docs)}")
    
    # Check contamination in key training sets
    key_train_sets = ["eli-sft-train.jsonl", "eli-sft-train-formatted.jsonl", "training-data.jsonl", "training-data-fable5-curated.jsonl", "raw_stack_v2_mined.jsonl"]
    contamination_report = {}
    
    for t_name in key_train_sets:
        t_path = PROCESSED_DIR / t_name
        if not t_path.exists():
            continue
        print(f"Checking contamination in {t_name}...")
        exact_matches = 0
        fuzzy_matches = 0
        with open(t_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                except Exception: continue
                inst = data.get("instruction", "")
                if not inst and "conversations" in data and data["conversations"]:
                    inst = data["conversations"][0].get("value", "")
                inst_clean = inst.strip().lower()
                if not inst_clean: continue
                
                inst_words = get_words(inst_clean)
                inst_ngrams = get_ngrams(inst_clean, 5)
                
                for doc in eval_docs:
                    if inst_clean == doc["text"]:
                        exact_matches += 1
                        break
                    sim = jaccard_similarity(inst_words, doc["words"])
                    if sim > 0.70 and len(inst_ngrams.intersection(doc["ngrams"])) >= 3:
                        fuzzy_matches += 1
                        break
                        
        contamination_report[t_name] = {
            "exact_matches": exact_matches,
            "fuzzy_matches": fuzzy_matches
        }
        
    audit_summary = {
        "files_audited": results,
        "contamination": contamination_report
    }
    
    out_file = PROJECT_ROOT / "processed" / "audit_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2, default=str)
    print(f"\nFull audit report saved to {out_file}")

if __name__ == "__main__":
    run_full_audit()
