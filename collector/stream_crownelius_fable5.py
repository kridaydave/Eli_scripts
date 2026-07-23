"""
Master FABLE.5 Parquet Extractor (Crownelius/Complete-FABLE.5-traces-2M)

Extracts all 16,057 Fable-5 assistant turns, links them with user prompts (via parentUuid lookup or lastPrompt fallback),
formats into ShareGPT ChatML multi-turn sessions, and outputs to `processed/training-data-fable5-curated.jsonl`.
"""

import json
import re
import pyarrow.parquet as pq
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = PROJECT_ROOT / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

PARQUET_PATH = DATA_DIR / "fable5-crownelius.parquet"
OUTPUT_CURATED_JSONL = PROCESSED_DIR / "training-data-fable5-curated.jsonl"

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'…\[earlier truncated\]|…\[truncated\]|\.\.\.\[truncated\]|\.\.\.\[earlier truncated\]', '', text)
    text = re.sub(r'\[[=>-]+\]\s*\d+%', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def main():
    print(f"Loading Parquet from {PARQUET_PATH}...")
    table = pq.read_table(PARQUET_PATH)
    total_rows = len(table)
    print(f"Total Parquet Rows: {total_rows:,}")
    
    # 1. First pass: Index all user prompts by UUID
    uuid_to_prompt = {}
    for i in range(total_rows):
        r_str = table.column("row_json")[i].as_py()
        try:
            p = json.loads(r_str)
            u_id = p.get("uuid")
            msg = p.get("message", {})
            if u_id and msg:
                content = msg.get("content")
                text_val = ""
                if isinstance(content, str):
                    text_val = content.strip()
                elif isinstance(content, list):
                    parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
                    text_val = "\n".join(parts).strip()
                
                if text_val:
                    uuid_to_prompt[u_id] = text_val
        except Exception:
            pass

    print(f"Indexed {len(uuid_to_prompt):,} prompt UUIDs.")

    # 2. Second pass: Extract assistant responses and link prompts
    curated_entries = []
    seen_responses = set()

    for i in range(total_rows):
        r_str = table.column("row_json")[i].as_py()
        try:
            p = json.loads(r_str)
            msg = p.get("message", {})
            if msg.get("role") == "assistant":
                parent_id = p.get("parentUuid")
                user_prompt = uuid_to_prompt.get(parent_id) or p.get("lastPrompt") or "Refactor and optimize the code following agentic execution steps."
                
                content = msg.get("content", [])
                assistant_text = ""
                thought_text = ""
                
                if isinstance(content, str):
                    assistant_text = sanitize_text(content)
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            p_type = part.get("type")
                            if p_type == "text":
                                assistant_text += part.get("text", "") + "\n"
                            elif p_type == "thinking":
                                thought_text += part.get("thinking", "") + "\n"
                            elif p_type == "tool_use":
                                t_name = part.get("name")
                                t_inp = part.get("input")
                                assistant_text += f"\n**Action ({t_name})**:\n```json\n{json.dumps(t_inp, indent=2)}\n```\n"

                full_res = ""
                if thought_text.strip():
                    full_res += f"<thought>\n{thought_text.strip()}\n</thought>\n\n"
                full_res += sanitize_text(assistant_text)
                
                if not full_res.strip() or full_res in seen_responses:
                    continue
                seen_responses.add(full_res)

                entry = {
                    "id": f"fable5-{p.get('uuid', i)}",
                    "conversations": [
                        {"from": "human", "value": user_prompt.strip()},
                        {"from": "gpt", "value": full_res.strip()}
                    ],
                    "metadata": {
                        "source": "Crownelius/Complete-FABLE.5-traces-2M",
                        "has_thought": bool(thought_text.strip()),
                        "session_id": p.get("sessionId", "")
                    }
                }
                curated_entries.append(entry)
        except Exception:
            pass

    print(f"Extracted {len(curated_entries):,} 100% Unique FABLE.5 CoT Traces!")

    with open(OUTPUT_CURATED_JSONL, "w", encoding="utf-8") as f:
        for entry in curated_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Saved Curated Dataset: {OUTPUT_CURATED_JSONL} ({OUTPUT_CURATED_JSONL.stat().st_size / 1024 / 1024:.1f} MB)")

if __name__ == "__main__":
    main()
