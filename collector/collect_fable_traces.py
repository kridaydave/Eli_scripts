"""
Multi-Turn Agent Trajectory & Single-Turn Extractor for Fable-5 Traces
Epoch Model Suite 1 (Eli)

Extracts both:
1. Multi-turn ShareGPT conversations (for mid-session tool execution, observations, & multi-step CoT reasoning)
2. Clean single-turn Alpaca pairs (for quick single-prompt SFT)

Includes full sanitization to strip raw path truncation markers (`…[truncated]`, `…[earlier truncated]`).
"""

import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

HF_URL = "https://huggingface.co/datasets/Glint-Research/Fable-5-traces/resolve/main/fable5_cot_merged.jsonl"

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    # Strip truncation markers and trailing noise
    text = re.sub(r'…\[earlier truncated\]|…\[truncated\]|\.\.\.\[truncated\]|\.\.\.\[earlier truncated\]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def download_and_extract_fable_sessions():
    print("=== Streaming & Building Multi-Turn Fable-5 Agent Trajectories ===")
    req = urllib.request.Request(HF_URL, headers={"User-Agent": "Mozilla/5.0"})
    
    sessions = defaultdict(list)

    try:
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                try:
                    row = json.loads(line.decode("utf-8"))
                    sess_id = row.get("session")
                    if sess_id:
                        sessions[sess_id].append(row)
                except Exception:
                    continue
    except Exception as e:
        print(f"Error streaming Fable-5 dataset: {e}")
        return [], []

    print(f"Loaded {len(sessions)} unique long-horizon agentic coding sessions.")

    multi_turn_sessions = []
    single_turn_pairs = []

    for sess_id, rows in sessions.items():
        conv = []
        root_prompt = None

        for r in rows:
            ctx = r.get("context", "")
            cot = r.get("cot", "").strip()
            out_type = r.get("output_type", "")
            output = r.get("output", "")
            comp = r.get("completion", "").strip()

            # Parse last human message (initial user prompt or tool result observation)
            user_matches = re.findall(r"USER:\s*(.*)", ctx, re.DOTALL)
            if user_matches:
                last_user_msg = sanitize_text(user_matches[-1])
            else:
                last_user_msg = "Continue session execution"

            # Capture root prompt for the session
            if not root_prompt and len(last_user_msg) > 15 and not last_user_msg.startswith("…") and not last_user_msg.startswith("<"):
                root_prompt = last_user_msg

            # Clean CoT reasoning
            cot_clean = cot.replace("Alright, ", "").replace("Okay, ", "").strip() if cot else ""
            cot_clean = sanitize_text(cot_clean)
            
            assist_val = ""
            if cot_clean:
                assist_val += f"<thought>\n{cot_clean}\n</thought>\n\n"

            if out_type == "tool_use" and isinstance(output, dict):
                t_name = output.get("tool", "")
                t_in = output.get("input", {})
                comp_clean = sanitize_text(comp)
                assist_val += f"**Tool Action ({t_name})**:\n```json\n{json.dumps(t_in, indent=2)}\n```\n\n{comp_clean}"
            else:
                assist_val += sanitize_text(comp)

            assist_val = sanitize_text(assist_val)

            if assist_val.strip() and last_user_msg.strip():
                conv.append({"from": "human", "value": last_user_msg})
                conv.append({"from": "gpt", "value": assist_val})

                if root_prompt:
                    single_turn_pairs.append({
                        "instruction": root_prompt,
                        "input": "",
                        "output": assist_val,
                        "source": "fable5_agent_traces"
                    })

        if len(conv) >= 4:
            multi_turn_sessions.append({
                "session_id": sess_id,
                "conversations": conv
            })

    print(f"Extracted {len(multi_turn_sessions)} multi-turn agentic trajectories and {len(single_turn_pairs)} single-turn pairs.")
    return multi_turn_sessions, single_turn_pairs

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    multi_file = out_dir / "fable-5-multi-turn-sessions.json"
    single_file = out_dir / "fable-5-agent-pairs.json"

    multi_turn, single_turn = download_and_extract_fable_sessions()
    
    with open(multi_file, "w", encoding="utf-8") as f:
        json.dump(multi_turn, f, indent=2, ensure_ascii=False)
        
    with open(single_file, "w", encoding="utf-8") as f:
        json.dump(single_turn[:1500], f, indent=2, ensure_ascii=False)

    print(f"Saved {len(multi_turn)} multi-turn trajectories to {multi_file}")
    print(f"Saved {min(len(single_turn), 1500)} single-turn pairs to {single_file}")
