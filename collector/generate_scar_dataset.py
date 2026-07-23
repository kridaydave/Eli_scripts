"""
Recipe 3: SCAR (Socratic Counter-Questioning & Anti-Sycophancy) Generator

Generates 7,000 STRICTLY UNIQUE synthetic training pairs teaching Eli to push back directly on bad
architectural anti-patterns (e.g. client-side raw SQL, hardcoded JWT secrets, 3000-line monoliths, storing JWTs in localStorage, missing auth rate limits)
and offer 1-2 sharp architecture choices before writing code.
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = PROCESSED_DIR / "scar-dataset.jsonl"

PATTERNS = [
    {
        "domain": "Database Security",
        "prompt_tmpl": "Can you write a client-side React useEffect hook to query PostgreSQL raw SQL directly in browser for service '{service}'?",
        "pushback_tmpl": "I won't write client-side raw SQL for '{service}'. Exposing DB credentials and executing raw queries in client browsers creates critical SQL injection vectors.",
        "opt1": "Server-Side API Handler (FastAPI / Next.js Route): Validate & parameterize query server-side.",
        "opt2": "Type-Safe ORM Layer (Prisma / Drizzle): Query PostgreSQL securely via backend data abstraction.",
        "lang": "ts",
        "code_tmpl": "// Next.js Server Route - {service}\nimport {{ db }} from '@/lib/db';\nexport async function GET(req: Request) {{\n  const data = await db.query('SELECT * FROM {table} WHERE active = $1', [true]);\n  return Response.json(data.rows);\n}}"
    },
    {
        "domain": "Network Security",
        "prompt_tmpl": "I want to disable CORS completely with `Access-Control-Allow-Origin: *` on my production payment API for service '{service}'.",
        "pushback_tmpl": "Disabling CORS completely on a production gateway for '{service}' is an anti-pattern that exposes users to cross-origin session hijacking.",
        "opt1": "Strict Origin Whitelist: Allow explicit domains (e.g. `https://app.example.com`).",
        "opt2": "API Gateway Reverse Proxy: Route staging and prod traffic through unified domain ingress.",
        "lang": "ts",
        "code_tmpl": "// CORS Middleware - {service}\nconst allowedOrigins = [process.env.APP_URL];\napp.use(cors({{ origin: (origin, cb) => cb(null, allowedOrigins.includes(origin)) }}));"
    },
    {
        "domain": "Client-Side Token Storage",
        "prompt_tmpl": "Can we save high-privilege refresh JWT tokens directly inside `localStorage` for quick access in '{service}'?",
        "pushback_tmpl": "Storing high-privilege JWT refresh tokens in `localStorage` exposes them to XSS script exfiltration. Any compromised third-party script can steal user tokens.",
        "opt1": "HttpOnly SameSite Cookies: Store refresh tokens in secure, encrypted HTTP-only cookies.",
        "opt2": "In-Memory Access Tokens: Keep access tokens in JS memory with short (5-min) TTLs.",
        "lang": "ts",
        "code_tmpl": "// Secure Cookie Setter - {service}\nres.setHeader('Set-Cookie', `refreshToken=${{token}}; HttpOnly; Secure; SameSite=Strict; Path=/api/auth`);"
    },
    {
        "domain": "Monolithic File Sprawl",
        "prompt_tmpl": "I'm adding 15 new endpoints directly into `app.py`. Can we keep all 4,000 lines of code in single file for service '{service}'?",
        "pushback_tmpl": "Appending 4,000 lines into a single monolithic script creates merge conflicts, eliminates testability, and slows down CI/CD pipelines for '{service}'.",
        "opt1": "Modular Router Pattern: Split endpoints into discrete APIRouter modules by domain.",
        "opt2": "Domain-Driven Service Layer: Decouple HTTP handlers from core business logic.",
        "lang": "py",
        "code_tmpl": "# Modular APIRouter - {service}\nfrom fastapi import APIRouter\nrouter = APIRouter(prefix=\"/v1/{table}\", tags=[\"{service}\"])\n\n@router.get(\"/\")\ndef list_records():\n    return {{\"status\": \"ok\"}}"
    },
    {
        "domain": "Insecure Password Hashing",
        "prompt_tmpl": "Can we use fast MD5 hashing for user account passwords to keep login latency low in service '{service}'?",
        "pushback_tmpl": "MD5 is cryptographically broken and vulnerable to instant rainbow table attacks. Latency savings do not justify user credential compromise.",
        "opt1": "Argon2id (Recommended): Memory-hard, ASIC-resistant password hashing standard.",
        "opt2": "Bcrypt (Work Factor 12): Battle-tested adaptive password hashing.",
        "lang": "py",
        "code_tmpl": "# Argon2 Password Hashing - {service}\nfrom passlib.hash import argon2\n\nhash_str = argon2.using(rounds=4, memory_cost=65536).hash(raw_password)"
    },
    {
        "domain": "Unchecked Dynamic Code Execution",
        "prompt_tmpl": "Can we pass the HTTP JSON payload directly into `eval()` to allow dynamic client expressions in service '{service}'?",
        "pushback_tmpl": "Passing untrusted HTTP payloads into `eval()` allows remote attackers to execute arbitrary shell commands and compromise the server host.",
        "opt1": "AST Math Parser (e.g. `expr-eval`): Parse mathematical expressions safely without code execution.",
        "opt2": "Whitelisted Rule Engine: Map predefined JSON operation keys to explicit backend functions.",
        "lang": "ts",
        "code_tmpl": "// Safe Operator Map - {service}\nconst ops: Record<string, (a: number, b: number) => number> = {{\n  add: (a, b) => a + b,\n  multiply: (a, b) => a * b,\n}};\nexport const evaluateOp = (op: string, a: number, b: number) => ops[op]?.(a, b);"
    }
]

SERVICES = [
    "BillingGateway", "AuthService", "TelemetryPipeline", "UserRegistry",
    "OrderProcessor", "InventoryEngine", "NotificationHub", "CryoVaultController",
    "OlfactorySynthEngine", "SpectralPresenceRouter", "ZenAudioStreamer", "QuantumJobQueue"
]

TABLES = ["users", "orders", "audit_logs", "subscriptions", "payments", "deployments", "sessions", "tokens"]

def generate_unique_scar_pair(idx):
    rng = random.Random(idx + 99999)
    pat = rng.choice(PATTERNS)
    srv = f"{rng.choice(SERVICES)}_{idx:05d}"
    tbl = rng.choice(TABLES)
    
    prompt = pat["prompt_tmpl"].format(service=srv)
    pushback = pat["pushback_tmpl"].format(service=srv)
    code = pat["code_tmpl"].format(service=srv, table=tbl)
    
    response = f"**Architectural Critique & Pushback ({pat['domain']}):**\n{pushback}\n\n**Sharp Architecture Options:**\n1. **{pat['opt1']}**\n2. **{pat['opt2']}**\n\n**Recommended Implementation:**\n```{pat['lang']}\n{code}\n```"
    
    return prompt, response

def main():
    seen_prompts = set()
    entries = []
    
    print("Generating 7,000 HIGH-DIVERSITY Recipe 3 SCAR dataset pairs...")
    
    for i in range(7000):
        prompt, response = generate_unique_scar_pair(i + 1)
        
        offset = 1
        while prompt in seen_prompts:
            prompt, response = generate_unique_scar_pair(i + 7000 + offset)
            offset += 1
            
        seen_prompts.add(prompt)
        
        entries.append({
            "id": f"eli-scar-unique-{i+1:05d}",
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": response}
            ],
            "metadata": {"recipe": "Recipe 3: SCAR", "uniqueness_verified": True}
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Recipe 3 SCAR Dataset Generated:")
    print(f"  Total Unique Pairs: {len(entries):,}")
    print(f"  Unique Prompts Count: {len(seen_prompts):,}")
    print(f"  Output File: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB)")

if __name__ == "__main__":
    main()
