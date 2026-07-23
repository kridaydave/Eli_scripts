"""
Sorts eval/responses.md by score descending so 9s and 10s appear at the top.
Adds a summary table of 9s and 10s at the top of the file.
"""

import re
from pathlib import Path

RESPONSES_FILE = Path(__file__).resolve().parent / "responses.md"

def parse_score(section_text: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)/10", section_text)
    if match:
        return float(match.group(1))
    return 0.0

def main():
    content = RESPONSES_FILE.read_text(encoding="utf-8")
    
    # Split into header and sections
    parts = re.split(r"\n(?=## \d+\.)", content)
    header = parts[0].strip()
    raw_sections = parts[1:]
    
    parsed_sections = []
    for sec in raw_sections:
        sec = sec.strip()
        if not sec:
            continue
        first_line = sec.splitlines()[0]
        score = parse_score(sec)
        parsed_sections.append({
            "first_line": first_line,
            "score": score,
            "content": sec
        })
        
    # Sort by score descending, preserving relative original order for ties
    parsed_sections.sort(key=lambda x: x["score"], reverse=True)
    
    # Build S-Tier Summary Table (scores >= 9.0)
    stier_entries = [s for s in parsed_sections if s["score"] >= 9.0]
    
    summary_md = "# Eli Taste Eval — Sorted by Score (S-Tier First)\n\n"
    summary_md += f"Total Evaluated Prompts: {len(parsed_sections)}\n"
    summary_md += f"S-Tier Gold (9.0–10.0/10): {len(stier_entries)} Prompts\n\n"
    
    summary_md += "## S-Tier Highlights (9.0 - 10.0 / 10)\n\n"
    summary_md += "| Score | Prompt Title | Summary / Highlight |\n"
    summary_md += "| :---: | :--- | :--- |\n"
    
    for item in stier_entries:
        title = item["first_line"].replace("## ", "").strip()
        # Extract first line of Eli response
        eli_match = re.search(r"\*\*Eli:\*\*\s*(.*)", item["content"])
        snippet = eli_match.group(1)[:90] + "..." if eli_match else ""
        summary_md += f"| **{item['score']}/10** | {title} | {snippet} |\n"
        
    summary_md += "\n---\n\n## Full Prompts (Ranked Descending)\n\n"
    
    section_texts = [item["content"] for item in parsed_sections]
    full_md = summary_md + "\n\n".join(section_texts) + "\n"
    
    RESPONSES_FILE.write_text(full_md, encoding="utf-8")
    print(f"Successfully sorted {len(parsed_sections)} prompts in {RESPONSES_FILE} (S-Tier at the top).")

if __name__ == "__main__":
    main()
