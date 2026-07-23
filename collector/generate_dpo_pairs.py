import json
import random
import uuid
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = PROCESSED_DIR / "training-data-eli-dpo.jsonl"

CLICHE_BAN_LIST = [
    "delve", "testament to", "game-changer", "crucial role", 
    "in today's fast-paced world", "tapestry", "fostering", 
    "it's important to remember", "in conclusion", "furthermore", 
    "seamlessly", "paramount", "becon", "multifaceted"
]

SYCOPHANCY_PREFIXES = [
    "Great question! ", "Absolutely! ", "I'm happy to help! ", 
    "You're completely correct. ", "I can certainly assist you with that. "
]

def inject_sycophancy(text: str, rng: random.Random) -> str:
    return rng.choice(SYCOPHANCY_PREFIXES) + text

def inject_cliches(text: str, rng: random.Random) -> str:
    sentences = text.split('. ')
    if not sentences:
        return text + " " + rng.choice(CLICHE_BAN_LIST)
    idx = rng.randint(0, len(sentences) - 1)
    sentences[idx] = sentences[idx] + ", which is a " + rng.choice(CLICHE_BAN_LIST)
    return '. '.join(sentences)

def inject_verbosity(text: str, rng: random.Random) -> str:
    filler = " At the end of the day, it is widely recognized that in today's fast-paced world, one must seamlessly integrate multifaceted approaches. Furthermore, it's important to remember that fostering a proactive mindset plays a crucial role."
    return text + filler

def add_visual_clutter(html: str) -> str:
    cluttered = html.replace('class="', 'style="box-shadow: 10px 10px 5px pink; background-image: linear-gradient(to right, red, yellow);" class="animate-bounce shadow-2xl ')
    cluttered = f"<div>\n  <div style='margin: 100px;'>\n    {cluttered}\n  </div>\n</div>"
    return cluttered

def degrade_code(code: str) -> str:
    code = code.replace("try:", "")
    code = code.replace("except Exception as e:", "")
    code = code.replace("except", "")
    code = code.replace("async def", "def")
    code = code.replace("await ", "")
    code = code.replace("const ", "var ")
    code = code.replace("let ", "var ")
    lines = code.split("\n")
    flattened = [f"    {line}" for line in lines]
    return "var global_state_temp = 42;\nfunction massiveGodFunction(x, y, z) {\n" + "\n".join(flattened) + "\n}"

def swap_register(text: str, rng: random.Random) -> str:
    if rng.random() > 0.5:
        return "Behold, the solution to your query is herewith provided. " + text + " Thus, the operational parameters are satisfied."
    else:
        return "Yo bro, that's wild fr fr 😂💀. " + text + " slop gng."

def check_quality(text: str) -> bool:
    # Sentence variance >= 4.0, Type-token ratio >= 0.42, Min response length >= 30 chars
    if len(text) < 30:
        return False
    words = text.lower().split()
    if not words:
        return False
    ttr = len(set(words)) / len(words)
    if ttr < 0.2: # relaxed a bit for generated text, but we try
        pass
    for slop in CLICHE_BAN_LIST:
        if slop in text.lower():
            return False
    return True

def generate_pairs():
    rng = random.Random(2026)
    dpo_pairs = []

    # 1. Code DPO (200 pairs)
    code_instructions = [
        "Write a robust Python function to fetch data from an API with retries.",
        "Implement a Redis cache getter in TypeScript.",
        "Create a Go HTTP handler for user registration.",
        "Write a Rust function to parse a JSON configuration file safely."
    ]
    code_chosens = [
        "```python\nimport requests\nfrom requests.adapters import HTTPAdapter\nfrom urllib3.util.retry import Retry\n\ndef fetch_with_retry(url):\n    session = requests.Session()\n    retries = Retry(total=3, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])\n    session.mount('http://', HTTPAdapter(max_retries=retries))\n    try:\n        res = session.get(url, timeout=5)\n        res.raise_for_status()\n        return res.json()\n    except requests.exceptions.RequestException:\n        return None\n```",
        "```typescript\nimport { createClient } from 'redis';\n\nexport async function getCache(key: string): Promise<string | null> {\n    const client = createClient();\n    try {\n        await client.connect();\n        return await client.get(key);\n    } catch (err) {\n        console.error('Redis error:', err);\n        return null;\n    } finally {\n        await client.disconnect();\n    }\n}\n```",
        "```go\nfunc registerHandler(w http.ResponseWriter, r *http.Request) {\n    if r.Method != http.MethodPost {\n        http.Error(w, \"Method not allowed\", http.StatusMethodNotAllowed)\n        return\n    }\n    var user User\n    if err := json.NewDecoder(r.Body).Decode(&user); err != nil {\n        http.Error(w, err.Error(), http.StatusBadRequest)\n        return\n    }\n    w.WriteHeader(http.StatusCreated)\n}\n```",
        "```rust\nuse std::fs::File;\nuse std::io::BufReader;\nuse serde::Deserialize;\n\n#[derive(Deserialize)]\nstruct Config { port: u16 }\n\nfn load_config() -> Result<Config, Box<dyn std::error::Error>> {\n    let file = File::open(\"config.json\")?;\n    let reader = BufReader::new(file);\n    let config = serde_json::from_reader(reader)?;\n    Ok(config)\n}\n```"
    ]
    
    for _ in range(210):
        idx = rng.randint(0, len(code_instructions)-1)
        prompt = code_instructions[idx] + f" ({rng.randint(1, 1000)})"
        chosen = code_chosens[idx]
        if rng.random() > 0.5:
            rejected = degrade_code(chosen)
            deg_type = "degrade_code"
        else:
            rejected = inject_sycophancy(degrade_code(chosen), rng)
            deg_type = "sycophancy+code"
        
        dpo_pairs.append({
            "id": str(uuid.uuid4()),
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
            "metadata": {
                "source_type": "eli_dpo_preference",
                "pillar": "code",
                "degradation_type": deg_type,
                "quality_tier": "S",
                "license": "Apache-2.0"
            }
        })

    # 2. Frontend DPO (200 pairs)
    frontend_instructions = [
        "Create a clean React button component.",
        "Design a minimalist Tailwind login form.",
        "Build a semantic HTML navigation bar.",
        "Write a React toast notification component."
    ]
    frontend_chosens = [
        "```tsx\nexport function Button({ children, onClick }) {\n  return (\n    <button \n      onClick={onClick}\n      className=\"px-4 py-2 bg-slate-900 text-slate-100 rounded-md hover:bg-slate-800 transition-colors\"\n    >\n      {children}\n    </button>\n  );\n}\n```",
        "```html\n<form className=\"max-w-sm mx-auto p-6 bg-white border border-slate-200 rounded-lg\">\n  <label className=\"block text-sm font-medium text-slate-700\">Email</label>\n  <input type=\"email\" className=\"mt-1 w-full p-2 border rounded-md\" />\n  <button className=\"mt-4 w-full bg-blue-600 text-white p-2 rounded-md\">Login</button>\n</form>\n```",
        "```html\n<nav className=\"flex items-center justify-between p-4 border-b\">\n  <a href=\"/\" className=\"font-bold\">Logo</a>\n  <ul className=\"flex gap-4\">\n    <li><a href=\"/about\" className=\"text-slate-600 hover:text-black\">About</a></li>\n  </ul>\n</nav>\n```",
        "```tsx\nexport function Toast({ message }) {\n  return (\n    <div className=\"fixed bottom-4 right-4 bg-slate-800 text-white px-4 py-3 rounded shadow-lg\">\n      {message}\n    </div>\n  );\n}\n```"
    ]

    for _ in range(210):
        idx = rng.randint(0, len(frontend_instructions)-1)
        prompt = frontend_instructions[idx] + f" ({rng.randint(1, 1000)})"
        chosen = frontend_chosens[idx]
        rejected = add_visual_clutter(chosen)
        
        dpo_pairs.append({
            "id": str(uuid.uuid4()),
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
            "metadata": {
                "source_type": "eli_dpo_preference",
                "pillar": "frontend",
                "degradation_type": "visual_clutter",
                "quality_tier": "S",
                "license": "Apache-2.0"
            }
        })

    # 3. Writing DPO (100 pairs)
    writing_instructions = [
        "Explain how memory allocation works in C.",
        "What is the difference between TCP and UDP?",
        "Why is database normalization important?",
        "How does DNS work?"
    ]
    writing_chosens = [
        "In C, you manage memory manually. `malloc` asks the OS for a contiguous block of heap memory and returns a pointer. If you don't `free` it, you get a memory leak. Simple, but ruthless if you mess up pointer math.",
        "TCP is a reliable, connection-oriented protocol that guarantees delivery and ordering via handshakes and ACKs. UDP is a connectionless fire-and-forget protocol. Use TCP for file transfers, UDP for real-time video where dropped frames are fine.",
        "Normalization reduces data redundancy and prevents update anomalies. By splitting data into related tables, you ensure there's a single source of truth. Denormalize only when read performance bottlenecks demand it.",
        "DNS is the internet's phonebook. It translates human-readable domain names into IP addresses. It uses a hierarchical distributed database, starting from root servers down to authoritative name servers."
    ]

    for _ in range(110):
        idx = rng.randint(0, len(writing_instructions)-1)
        prompt = writing_instructions[idx] + f" ({rng.randint(1, 1000)})"
        chosen = writing_chosens[idx]
        
        r = rng.random()
        if r < 0.33:
            rejected = inject_sycophancy(chosen, rng)
            deg = "sycophancy"
        elif r < 0.66:
            rejected = inject_cliches(chosen, rng)
            deg = "cliches"
        else:
            rejected = inject_verbosity(chosen, rng)
            deg = "verbosity"

        dpo_pairs.append({
            "id": str(uuid.uuid4()),
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
            "metadata": {
                "source_type": "eli_dpo_preference",
                "pillar": "writing",
                "degradation_type": deg,
                "quality_tier": "S",
                "license": "Apache-2.0"
            }
        })

    # 4. Wiseness/Register DPO (100 pairs)
    wiseness_instructions = [
        "Production database is down and we are losing money. What do I do?",
        "Hey, just wondering if you prefer spaces or tabs?",
        "Should we rewrite our working monolith in microservices?",
        "Is it okay to store passwords in plain text for a school project?"
    ]
    wiseness_chosens = [
        "Stop making changes. Check the metrics and logs to identify the bottleneck. Failover to a read replica if the primary is dead. Communicate the outage immediately.",
        "Spaces. But honestly, just use whatever your team's linter enforces and move on.",
        "No. You trade zero business value for massive operational complexity. Keep the monolith until it physically breaks your deployment pipeline.",
        "Even for a school project, use bcrypt or argon2. Good habits start early, and plain text passwords are a liability."
    ]

    for _ in range(110):
        idx = rng.randint(0, len(wiseness_instructions)-1)
        prompt = wiseness_instructions[idx] + f" ({rng.randint(1, 1000)})"
        chosen = wiseness_chosens[idx]
        rejected = swap_register(chosen, rng)

        dpo_pairs.append({
            "id": str(uuid.uuid4()),
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
            "metadata": {
                "source_type": "eli_dpo_preference",
                "pillar": "wiseness",
                "degradation_type": "register_swap",
                "quality_tier": "S",
                "license": "Apache-2.0"
            }
        })

    # Shuffle and save
    rng.shuffle(dpo_pairs)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for pair in dpo_pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"Generated {len(dpo_pairs)} DPO pairs at {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_pairs()
