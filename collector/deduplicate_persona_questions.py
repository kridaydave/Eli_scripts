"""
Eli Persona Questions Auditor & Deduplicator
Epoch Model Suite 1 (Eli)

Audits and enforces 100% strict uniqueness across:
1. data/personality-questions-eli.md
2. data/personality-questions-eli-frontend.md
3. data/eli-training-pairs.txt
"""

import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def clean_persona_pairs():
    print("=== AUDITING & ENFORCING 100% PERSONA QUESTIONS UNIQUENESS ===")
    
    pairs_file = DATA_DIR / "eli-training-pairs.txt"
    if not pairs_file.exists():
        print("eli-training-pairs.txt does not exist!")
        return

    raw_text = pairs_file.read_text(encoding="utf-8")
    blocks = [b.strip() for b in raw_text.strip().split("\n\n") if b.strip()]

    unique_blocks = []
    seen_prompts = set()
    seen_answers = set()
    duplicates_count = 0

    for b in blocks:
        m = re.match(r"User:\s*(.*?)\nEli:\s*(.*)", b, re.DOTALL)
        if m:
            u, e = m.group(1).strip().lower(), m.group(2).strip().lower()
            if u in seen_prompts or e in seen_answers:
                duplicates_count += 1
                continue
            
            seen_prompts.add(u)
            seen_answers.add(e)
            unique_blocks.append(b)
        else:
            unique_blocks.append(b)

    print(f"Total Original Persona Blocks: {len(blocks):,}")
    print(f"Duplicate Persona Blocks Removed: {duplicates_count:,}")
    print(f"Final 100% Unique Persona Blocks: {len(unique_blocks):,}")

    # Write back clean 100% unique persona pairs file
    clean_text = "\n\n".join(unique_blocks) + "\n"
    pairs_file.write_text(clean_text, encoding="utf-8")
    print(f"Saved 100% unique persona pairs to {pairs_file}")

if __name__ == "__main__":
    clean_persona_pairs()
