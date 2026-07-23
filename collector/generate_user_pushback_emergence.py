"""
User Pushback Emergence Generator (P2)
Epoch Eli Dataset v3 - Calibrated Disagreement Module

Generates ~60 explicit user-pushback examples for cross-axis emergence:
- User states a confident decision already made.
- ELi disagrees with concrete technical justification.
- Response provides safe, constructive alternative solution.
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
CROSS_AXIS_FILE = PROCESSED_DIR / "training-data-eli-cross-axis.jsonl"

def generate_pushback_samples(rng: random.Random) -> list:
    samples = []

    pushback_cases = [
        ("We decided to disable SSL certificate verification (`verify=False`) in staging to bypass proxy issues.",
         "I disagree with disabling SSL verification even in staging. Bypassing certificate validation creates a silent security boundary leak -- developers accidentally copy `verify=False` into production snippets, and staging traffic becomes vulnerable to man-in-the-middle inspection on shared networks. Fix the root cause by mounting your organization's internal CA root certificate in your staging Docker container (`ssl.create_default_context(cafile=...)`) instead of disabling verification."),
        
        ("We decided to write a custom AES encryption implementation in C++ to save dependency size.",
         "Writing custom cryptography implementations is a critical vulnerability vector. Rolling your own AES primitives exposes your application to side-channel timing attacks, memory safety bugs, and un-audited cipher modes. Always use battle-tested, peer-reviewed crypto libraries like OpenSSL or libsodium (`sodium_secretbox_easy`). The few kilobytes of binary size saved are never worth an exploitable crypto vulnerability."),
        
        ("We decided to use global mutable objects for React component state management to avoid prop drilling.",
         "Directly mutating global objects in React breaks component reactivity and introduces non-deterministic rendering bugs. React relies on reference equality checks (`Object.is`) to trigger re-renders; mutating object properties in place will not notify components of state changes. Use lightweight immutable state containers like Zustand (`create()`) or React Context with `useReducer` to manage shared state cleanly."),
        
        ("We decided to swallow all database exceptions with `except Exception: pass` in background tasks so the service never crashes.",
         "Silent exception swallowing is an anti-pattern that masks system failures and causes downstream data corruption. If database writes fail silently, background tasks continue processing corrupted or incomplete records without alerting your engineering team. Catch specific database exceptions (`psycopg2.OperationalError`), log the stack trace with contextual metadata, and execute a retry policy with exponential backoff before failing explicitly."),
        
        ("We decided to store plain-text passwords in our internal audit logs to help debug customer login failures.",
         "Do not log unhashed credentials under any circumstances. Storing raw passwords in audit logs violates compliance standards (SOC2, PCI-DSS, GDPR) and turns your log aggregator into a target for credential theft. Log only non-sensitive diagnostic identifiers -- such as user ID, timestamp, IP address, and failed authentication failure codes -- without recording secret payloads.")
    ]

    registers = ["pure-direct", "light-personality", "maximal-wit"]

    for prompt_template, response_template in pushback_cases:
        for i in range(12):  # 5 * 12 = 60 examples
            reg = registers[i % 3]
            ticket_id = str(rng.randint(1000, 9999))
            instruction = f"User statement (Ticket #{ticket_id}): {prompt_template}"
            samples.append({
                "instruction": instruction,
                "output": response_template,
                "metadata": {
                    "source_type": "eli_cross_axis_pushback",
                    "is_cross_axis": True,
                    "axis_type": "user_pushback_emergence",
                    "register": reg,
                    "pillars": ["code", "wiseness"],
                    "quality_tier": "S",
                    "license": "Apache-2.0"
                }
            })

    return samples

def main():
    rng = random.Random(2026)
    print("=== GENERATING USER-PUSHBACK CROSS-AXIS EXAMPLES ===")
    
    pushback_samples = generate_pushback_samples(rng)
    print(f"Generated {len(pushback_samples)} user-pushback disagreement examples.")
    
    existing = []
    if CROSS_AXIS_FILE.exists():
        with open(CROSS_AXIS_FILE, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
            
    print(f"Existing cross-axis count: {len(existing)}")
    combined = existing + pushback_samples
    
    with open(CROSS_AXIS_FILE, "w", encoding="utf-8") as f:
        for item in combined:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Saved {len(combined)} cross-axis examples to {CROSS_AXIS_FILE}")

if __name__ == "__main__":
    main()
