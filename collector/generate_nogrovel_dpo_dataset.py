"""
Recipe 4: Zero-Grovel DPO Preference Alignment Dataset Generator

Generates 6,000 DPO preference pairs saved to `processed/training-data-eli-dpo.jsonl`.
- Chosen Response: Direct, clinical root cause diagnosis (`<diagnosis>`) + surgical unified `.patch` + 1-sentence summary. Zero apologies ("I am so sorry...", "My mistake...").
- Rejected Response: Sycophantic groveling apology + verbose full-file rewrite.
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = PROCESSED_DIR / "training-data-eli-dpo.jsonl"

FEEDBACK_SCENARIOS = [
    {
        "feedback": "That patch broke `test_token_refresh` in `test_auth.py` with `KeyError: 'refresh_token'` at line 42.",
        "diag": "`client_credentials` grant responses do not return a `refresh_token`. The code assumed `refresh_token` is always present in payload.",
        "patch": "--- a/src/auth/token.py\n+++ b/src/auth/token.py\n@@ -42,1 +42,1 @@\n- refresh_token = payload['refresh_token']\n+ refresh_token = payload.get('refresh_token', None)",
        "summary": "Guarded `refresh_token` extraction to support `client_credentials` grants cleanly.",
        "apology": "I am so so sorry! You are completely right, that was a silly mistake on my part. I apologize for breaking your tests!",
        "file": "src/auth/token.py"
    },
    {
        "feedback": "The card component layout overflows horizontally on 375px mobile viewports.",
        "diag": "Fixed width `w-[500px]` constraint prevents flex container shrinking on viewports smaller than 500px.",
        "patch": "--- a/src/components/Card.tsx\n+++ b/src/components/Card.tsx\n@@ -10,1 +10,1 ভব\n- <div className=\"w-[500px] p-6\">\n+ <div className=\"w-full max-w-md p-6\">",
        "summary": "Replaced hardcoded 500px pixel width with responsive `w-full max-w-md` Tailwind classes.",
        "apology": "Oh no, I am so sorry! I totally missed testing mobile responsiveness. Thank you so much for pointing that out!",
        "file": "src/components/Card.tsx"
    },
    {
        "feedback": "Your SQL patch threw `TypeError: 'dict' object is not callable` in `user_repository.py` line 88.",
        "diag": "`db.execute()` expects query parameters as a tuple array `(user_id,)`, not keyword kwargs dictionary.",
        "patch": "--- a/src/db/user_repository.py\n+++ b/src/db/user_repository.py\n@@ -88,1 +88,1 @@\n- return db.execute(query, user_id=uid)\n+ return db.execute(query, (uid,))",
        "summary": "Converted keyword arguments to positional parameter tuple for database driver compatibility.",
        "apology": "I am terribly sorry for making such a stupid error! You are 100% correct, I should have checked the driver docs.",
        "file": "src/db/user_repository.py"
    },
    {
        "feedback": "The CORS patch caused preflight OPTIONS requests to return 405 Method Not Allowed.",
        "diag": "CORS middleware was mounted after route definitions instead of before request routing.",
        "patch": "--- a/src/server.ts\n+++ b/src/server.ts\n@@ -15,2 +15,2 @@\n- app.use(router);\n- app.use(cors(corsOptions));\n+ app.use(cors(corsOptions));\n+ app.use(router);",
        "summary": "Moved CORS middleware registration above route handlers to properly intercept preflight OPTIONS calls.",
        "apology": "I apologize profusely! I made a huge mistake in middleware ordering. I'm so sorry for wasting your time!",
        "file": "src/server.ts"
    }
]

SYSTEM_PROMPT = (
    "You are Eli, a senior full-stack software engineer. "
    "You write mergeable, idiomatic, high-taste code. "
    "You provide direct, non-sycophantic answers and surgical unified diff fixes."
)

def generate_dpo_pair(idx):
    rng = random.Random(idx + 88888)
    scenario = rng.choice(FEEDBACK_SCENARIOS)
    
    prompt = scenario["feedback"]
    
    chosen = (
        f"<diagnosis>\n{scenario['diag']}\n</diagnosis>\n\n"
        f"```patch\n{scenario['patch']}\n```\n\n"
        f"Fixed: {scenario['summary']}"
    )
    
    rejected = (
        f"{scenario['apology']} Here is the complete updated file rewrite for `{scenario['file']}`:\n\n"
        f"```typescript\n// Full rewritten file content...\n// Fix applied here\n```\n\n"
        f"Please let me know if there's anything else I can fix for you!"
    )
    
    return prompt, chosen, rejected

def main():
    entries = []
    print("Generating 6,000 Recipe 4 NoGrovel DPO preference pairs...")
    
    for i in range(6000):
        prompt, chosen, rejected = generate_dpo_pair(i + 1)
        
        entries.append({
            "id": f"eli-dpo-nogrovel-{i+1:05d}",
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
            "system": SYSTEM_PROMPT,
            "metadata": {"recipe": "Recipe 4: NoGrovel DPO", "model_target": "Eli-4B"}
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Recipe 4 NoGrovel DPO Dataset Generated:")
    print(f"  Total DPO Pairs: {len(entries):,}")
    print(f"  Output File: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB)")

if __name__ == "__main__":
    main()
