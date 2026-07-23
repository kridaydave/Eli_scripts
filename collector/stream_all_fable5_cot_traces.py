"""
Fable-5 CoT Master Trajectory Extractor
Epoch Model Suite 1 (Eli v3 Upgrade)

Streams 2,000+ Fable-5 trace files from Glint-Research/Fable-5-traces (Hugging Face)
Extracts:
1. Deep Chain-of-Thought (<thought> ... </thought>) reasoning steps
2. Agentic tool calls (Bash, File Read, File Edit, Search/Replace diffs)
3. Observation tool results
4. Formats into both single-turn CoT Alpaca pairs and multi-turn ShareGPT sessions
"""

import json
import re
import random
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HF_API_URL = "https://huggingface.co/api/datasets/Glint-Research/Fable-5-traces"
HF_BASE_RAW = "https://huggingface.co/datasets/Glint-Research/Fable-5-traces/resolve/main/"

OUT_SINGLE_FILE = DATA_DIR / "fable-5-cot-expanded-pairs.json"
OUT_MULTI_FILE = DATA_DIR / "fable-5-multi-turn-sessions.json"

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'…\[earlier truncated\]|…\[truncated\]|\.\.\.\[truncated\]|\.\.\.\[earlier truncated\]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def fetch_all_trace_files(limit: int = 2500) -> list[str]:
    print("=== Streaming list of all Fable-5 trace files from Hugging Face ===")
    req = urllib.request.Request(HF_API_URL, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            siblings = data.get("siblings", [])
            trace_files = [s["rfilename"] for s in siblings if s["rfilename"].startswith("pi-traces/")]
            print(f"Found {len(trace_files)} total raw Fable-5 trace files on HF.")
            random.seed(2026)
            random.shuffle(trace_files)
            return trace_files[:limit]
    except Exception as e:
        print(f"Error listing trace files: {e}")
        return []

def parse_fable5_trace(filename: str) -> tuple[dict | None, list[dict]]:
    url = f"{HF_BASE_RAW}{filename}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            lines = [json.loads(line.decode("utf-8")) for line in resp]
    except Exception:
        return None, []

    sess_id = filename.split("/")[-1].replace(".jsonl", "")
    convs = []
    single_pairs = []
    root_prompt = None

    for l in lines:
        if l.get("type") != "message":
            continue
        msg = l.get("message", {})
        role = msg.get("role")
        content = msg.get("content", [])

        val_text = ""
        cot_text = ""
        if isinstance(content, str):
            val_text = sanitize_text(content)
            if not root_prompt and role == "user" and len(val_text) > 15:
                root_prompt = val_text
            if val_text:
                convs.append({"from": "human" if role == "user" else "gpt", "value": val_text})
        elif isinstance(content, list):
            part_str = ""
            for part in content:
                p_type = part.get("type")
                if p_type == "text":
                    txt = part.get("text", "")
                    part_str += txt + "\n"
                    if not root_prompt and role == "user" and len(txt) > 15:
                        root_prompt = txt
                elif p_type == "thinking":
                    think_str = part.get("thinking", "").strip()
                    if think_str:
                        cot_text += think_str + "\n"
                        part_str += f"<thought>\n{think_str}\n</thought>\n\n"
                elif p_type == "tool_use":
                    t_name = part.get("name")
                    t_inp = part.get("input")
                    part_str += f"**Tool Action ({t_name})**:\n```json\n{json.dumps(t_inp, indent=2)}\n```\n\n"
                elif p_type == "tool_result":
                    res = part.get("content")
                    if part_str.strip():
                        convs.append({"from": "gpt" if role == "assistant" else "human", "value": sanitize_text(part_str)})
                        part_str = ""
                    convs.append({"from": "human", "value": f"**Tool Result**:\n{res}"})

            if part_str.strip():
                clean_val = sanitize_text(part_str)
                convs.append({"from": "human" if role == "user" else "gpt", "value": clean_val})
                if root_prompt and cot_text and role == "assistant":
                    single_pairs.append({
                        "instruction": root_prompt,
                        "output": clean_val,
                        "source": "fable5_cot_traces",
                        "metadata": {
                            "source_type": "fable5_cot_traces",
                            "source_repo": "Glint-Research/Fable-5-traces",
                            "file_path": filename,
                            "license": "Apache-2.0",
                            "quality_tier": "S",
                            "language": "cot_reasoning",
                            "is_test": False
                        }
                    })

    sess_obj = None
    if len(convs) >= 2:
        sess_obj = {
            "session_id": f"fable5-{sess_id}",
            "conversations": convs,
            "metadata": {
                "source_type": "fable5_cot_traces",
                "turns": len(convs),
                "quality_tier": "S"
            }
        }

    return sess_obj, single_pairs

def stream_all_fable5_traces(limit: int = 2500):
    files = fetch_all_trace_files(limit=limit)
    if not files:
        return

    print(f"Streaming and extracting CoT reasoning from {len(files)} Fable-5 trace files...")
    all_sessions = []
    all_single_pairs = []

    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(parse_fable5_trace, f): f for f in files}
        for future in as_completed(futures):
            sess, pairs = future.result()
            if sess:
                all_sessions.append(sess)
            if pairs:
                all_single_pairs.extend(pairs)

    print(f"\nSuccessfully extracted:")
    print(f"  - {len(all_sessions):,} Fable-5 multi-turn CoT sessions")
    print(f"  - {len(all_single_pairs):,} Fable-5 single-turn CoT pairs")

    # Deduplicate single pairs by instruction
    seen = set()
    unique_single_pairs = []
    for p in all_single_pairs:
        inst = p["instruction"].strip()
        if inst not in seen:
            seen.add(inst)
            unique_single_pairs.append(p)

    print(f"  - {len(unique_single_pairs):,} 100% unique single-turn Fable-5 CoT pairs")

    # Save to data files
    with open(OUT_SINGLE_FILE, "w", encoding="utf-8") as f:
        json.dump(unique_single_pairs, f, indent=2, ensure_ascii=False)

    with open(OUT_MULTI_FILE, "w", encoding="utf-8") as f:
        json.dump(all_sessions, f, indent=2, ensure_ascii=False)

    print(f"Saved to {OUT_SINGLE_FILE} and {OUT_MULTI_FILE}")

if __name__ == "__main__":
    stream_all_fable5_traces(limit=2500)
