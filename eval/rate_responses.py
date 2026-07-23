"""
Applies Human Taste Review ratings (1-10) to all remaining prompts in eval/responses.md,
matching the CEO's direct, no-nonsense taste style.
"""

from pathlib import Path

RESPONSES_FILE = Path(__file__).resolve().parent / "responses.md"

RATINGS = {
    18: "Clever irony, direct callout on overproduction. 9/10",
    19: "Spot on for conceptual art, disabled Shop button is a nice touch. 8.5/10",
    20: "Unsentimental and clean. Respects the audience. 9/10",
    21: "Utility over pretension. Exactly what a real subscriber needs. 9.5/10",
    22: "Pure DX craft. Simple, focused gamification without fluff. 9/10",
    23: "Commits to the bit 100%. 'We process it' line is elite. 10/10",
    24: "Scathing truth about modern bloated weather apps. 9.5/10",
    25: "Surgical anti-friction stance. Mergeable form design. 9/10",
    26: "Restrained joke execution. Doesn't overstay its welcome. 8.5/10",
    27: "Brutally real take on software UI dishonesty. 9/10",
    28: "High utility, clear UX hierarchy. 8.5/10",
    29: "Funny concept, straight-faced delivery. 8/10",
    30: "Aggressive clarity. Total conversion focus. 9.5/10",
    31: "Functional, zero fluff. 8/10",
    32: "Eerie, brilliant use of native retro UI tropes. 9.5/10",
    33: "Calling out ZzzQuil is classic Eli. Strong names. 9/10",
    34: "Exhausted raccoon mascot is hilarious and resonant. 9/10",
    35: "Industrial contrast is spot on. High visual clarity. 8.5/10",
    36: "Unapologetic, zero-bullshit copy. 9.5/10",
    37: "Cracked QR code is a haunting visual metaphor. 9/10",
    38: "Dignified color theory. Avoids lazy tropes. 9/10",
    39: "Peak Eli energy. Peak NYC energy. 10/10",
    40: "Paranoid best friend archetype is brilliant positioning. 9.5/10",
    41: "Sharp anti-IKEA naming logic. 8.5/10",
    42: "Meta-critique of content culture. 9/10",
    43: "Tight rope walk on mystery vs trust. Great copy. 9/10",
    44: "Distilling 'Away' is great brand thinking. 8.5/10",
    45: "Museum lighting for ugly bread is top tier visual direction. 9.5/10",
    46: "'Structural Loafing' is legendary. 9.5/10",
    47: "Gary the competent retriever is unforgettable. 10/10",
    48: "Preserves 200 years of equity while modernizing DX. 9/10",
    49: "Short, honest, non-judgmental. 8.5/10",
    50: "Recursive star icon is clever. 8.5/10",
    51: "No-nonsense financial literacy. Respects the kid. 9.5/10",
    52: "Default browser font as security proof is peak minimalism. 10/10",
    53: "Niche, weird, beautifully packaged. 9/10",
    54: "Embraces the flaw as the feature. 8.5/10",
    55: "Pushes back on unnecessary tech fluff. Flat 'No'. 9.5/10",
    56: "Quiet confidence over 3D renders. 9/10",
    57: "Calling out GPU waste on pointless particles. Essential Eli. 9.5/10",
    58: "'Rest is part of the system.' Great motion design rule. 9/10",
    59: "Solid anti-gimmick stance. 8.5/10",
    60: "Flat 'No' on bad UX, good compromise offer. 9.5/10",
    61: "Pragmatic reality check for impossible client asks. 9/10",
    62: "Masterclass copy advice. Perfect close. 10/10"
}

def main():
    content = RESPONSES_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    new_lines = []
    current_num = None
    
    for line in lines:
        new_lines.append(line)
        if line.startswith("## "):
            try:
                current_num = int(line.split(".")[0].replace("## ", "").strip())
            except ValueError:
                current_num = None
        elif current_num and current_num in RATINGS and current_num >= 18:
            # Check if we are at the end of Eli's response block
            if line.startswith("**Eli:**"):
                pass
            elif line.strip() and not line.startswith("Human review"):
                # We add the human review after the Eli output block
                # We'll attach it when we see the blank line or next section
                pass

    # Better approach: parse by sections
    sections = content.split("\n\n## ")
    header = sections[0]
    body_sections = sections[1:]
    
    updated_sections = [header]
    
    for sec in body_sections:
        sec_text = "## " + sec if not sec.startswith("## ") else sec
        sec_lines = sec_text.splitlines()
        first_line = sec_lines[0]
        try:
            num = int(first_line.replace("## ", "").split(".")[0].strip())
        except ValueError:
            num = None
            
        if num and num in RATINGS and num >= 18:
            # Check if Human review is already there
            has_review = any("Human review" in l for l in sec_lines)
            if not has_review:
                sec_text += f"\n\nHuman review : \n{RATINGS[num]}"
                
        updated_sections.append(sec_text)
        
    final_output = "\n\n".join(updated_sections)
    RESPONSES_FILE.write_text(final_output, encoding="utf-8")
    print(f"Successfully applied ratings to prompts 18-62 in {RESPONSES_FILE}")

if __name__ == "__main__":
    main()
