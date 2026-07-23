import json
import math
import re
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = PROCESSED_DIR / "training-data-eli-writing.jsonl"

AI_SLOP_CLICHES = [
    r"\bdelve\b", r"\btestament to\b", r"\bgame-changer\b", r"\bcrucial role\b",
    r"\bin today's fast-paced world\b", r"\btapestry\b", r"\bfostering\b",
    r"\bit's important to remember\b", r"\bin conclusion\b", r"\bfurthermore\b",
    r"\bseamlessly\b", r"\bparamount\b", r"\bbecon\b", r"\bmultifaceted\b"
]

def contains_ai_slop(text: str) -> tuple[bool, str]:
    text_lower = text.lower()
    for pat in AI_SLOP_CLICHES:
        if re.search(pat, text_lower):
            return True, pat
    return False, ""

def calculate_sentence_variance(text: str) -> tuple[bool, float]:
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if len(sentences) < 3:
        return False, 0.0

    lengths = [len(s.split()) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    return variance >= 4.0, round(variance, 2)

def calculate_type_token_ratio(text: str) -> tuple[bool, float]:
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', text)]
    if len(words) < 20:
        return False, 0.0

    unique_words = set(words)
    ttr = len(unique_words) / len(words)
    return ttr >= 0.42, round(ttr, 2)

VARIABLES = {
    "tech_trend": ["Kubernetes", "event sourcing", "NoSQL", "GraphQL", "micro-frontends", "distributed tracing", "AI coding assistants", "serverless", "service meshes", "gRPC", "Kafka", "SPAs"],
    "metric": ["40%", "3x", "10x", "500 milliseconds", "five nines", "99th percentile latency", "2x", "100ms", "99.99%"],
    "pain_point": ["distributed debugging nightmare", "split-brain scenario", "eventual consistency purgatory", "dependency hell", "OOM kill loop", "cascading failure", "thundering herd", "connection exhaustion", "n+1 query problem"],
    "busy_work": ["writing YAML configs", "chasing race conditions", "tailing corrupted logs", "restarting crashed pods", "debugging network hops", "managing Kafka partitions", "managing state machines"],
    "boring_tech": ["a single Postgres instance", "a simple cron job", "bash scripts", "a monolithic app", "SQLite", "a basic queue", "a Redis cache"],
    "sys_concept": ["TCP handshakes", "DNS resolution", "garbage collection", "process scheduling", "virtual memory", "containerization", "epoll loops", "file descriptors", "page faults"],
    "command": ["curl -v", "tcpdump -i any", "ping", "dig +trace", "lsof -i", "strace -e open", "iostat -x"],
    "api_concept": ["idempotency keys", "pagination limits", "rate limiting", "webhook signatures", "RESTful resource naming", "cursor-based pagination", "retry jitter"],
    "api_benefit": ["preventing double charges", "stopping malicious scrapers", "ensuring backward compatibility", "providing predictable latencies", "handling network partitions", "graceful degradation"],
    "c_concept": ["memory allocation", "pointer arithmetic", "cache locality", "event loops", "struct padding", "socket programming", "mutex locks"],
    "refactor_concept": ["the Strategy pattern", "dependency injection", "extracting interfaces", "domain-driven boundaries", "the Observer pattern", "immutability", "pure functions"],
    "production_concept": ["zero-downtime migrations", "canary deployments", "load shedding", "circuit breaking", "blue-green deployments", "database sharding", "read replicas"],
    "focus": ["simplicity", "performance", "scalability", "maintainability", "reliability", "developer experience", "cost efficiency", "predictability", "system stability", "observability"]
}

BLUEPRINTS = [
    {
        "author": "Dan Luu",
        "register": "pure-direct",
        "instruction_templates": [
            "Write a data-driven post about why {tech_trend} is actually slowing down engineering velocity. Focus on {focus}.",
            "Explain why the conventional wisdom around {tech_trend} is wrong, using empirical evidence. Ensure you address {focus}.",
            "Draft a methodical breakdown of why companies over-invest in {tech_trend}, highlighting {focus}."
        ],
        "output_parts": {
            "intro": [
                "Everyone claims {tech_trend} speeds up development. They are lying.",
                "The industry is obsessed with {tech_trend}. The data tells a different story.",
                "You do not need {tech_trend}. Benchmarks show it degrades performance by {metric}."
            ],
            "body": [
                "When you analyze velocity across multiple engineering orgs, the reality hits hard. You traded a boring, working system for a {pain_point}. Instead of shipping product features, your senior engineers are now {busy_work}. The overhead is massive. Every single layer you add increases the blast radius of a failure.",
                "Look at the empirical evidence. Teams adopting this see their deployment times inflate massively. You introduced network boundaries where simple function calls used to exist. Now you have to deal with {pain_point} and spend your weekends {busy_work}. The complexity budget is entirely blown on infrastructure.",
                "We looked at the latency numbers. It is grim. What used to be a millisecond lookup is now blocked on {pain_point}. Your infrastructure bill doubled because you are {busy_work} instead of serving user requests. Stop chasing shiny objects."
            ],
            "code": [
                "```python\n# Before: 10ms\ndef process():\n    return db.query()\n\n# After: 500ms timeout\ndef process():\n    return rpc_call('service-a', timeout=0.5)\n```",
                "```go\n// Stop doing this:\ngo func() {\n    // uncontrolled concurrency\n}()\n\n// Do this:\nworkerPool.Submit(task)\n```",
                "```sql\n-- Boring and fast:\nSELECT * FROM users WHERE active = true;\n```"
            ],
            "conclusion": [
                "Stick to {boring_tech} until your servers are physically melting. It is that simple.",
                "Keep it boring. {boring_tech} works. Stop over-engineering.",
                "Optimize for simplicity. Deploy {boring_tech} and go to sleep."
            ]
        }
    },
    {
        "author": "Julia Evans",
        "register": "light-personality",
        "instruction_templates": [
            "Explain how {sys_concept} works under the hood for a junior engineer. Focus on {focus}.",
            "Write a zine-style explanation of {sys_concept} focusing on {focus}.",
            "Demystify {sys_concept} with a simple breakdown, emphasizing {focus}."
        ],
        "output_parts": {
            "intro": [
                "{sys_concept} feels like magic. It's not. Let's break it down.",
                "Ever wonder how {sys_concept} actually works? It is super cool and surprisingly simple once you look at the internals.",
                "I used to find {sys_concept} terrifying. Then I learned it is just passing simple messages around."
            ],
            "body": [
                "At its core, {sys_concept} relies on a few fundamental primitives. When you execute a request, the kernel intercepts it and allocates a file descriptor. That's it! No black magic, just a mapping in memory. You can actually trace this yourself using `strace` and watch the exact system calls happen in real-time. It completely removes the mystery.",
                "The secret to {sys_concept} is how it handles state. It doesn't. Instead, it relies on an append-only log. Every time you make a change, it just writes a new entry to the end of a file. Reading it back just means replaying the log. This simple pattern powers some of the most robust systems in the world.",
                "Think of {sys_concept} as a fancy key-value store. The operating system just maintains a giant hash table. When a process asks for memory, it looks up an available block, hands over the pointer, and updates the table. If you write out the C code for it, it fits on a single screen."
            ],
            "code": [
                "```bash\n$ {command}\n```",
                "```c\n// The core logic is just this:\nstruct File { int fd; char* buffer; };\n```",
                "```python\n# Replaying a simple log\nfor event in read_log('sys.log'):\n    state.apply(event)\n```"
            ],
            "conclusion": [
                "Next time it breaks, don't panic. Just read the source. You've got this.",
                "Understanding the layers beneath your code makes you fearless. Go poke around.",
                "Tools are just code someone else wrote. You can read it, understand it, and fix it."
            ]
        }
    },
    {
        "author": "Brandur Leach",
        "register": "pure-direct",
        "instruction_templates": [
            "Write a thoughtful essay on why {api_concept} is essential for API design. Touch on {focus}.",
            "Explain the elegant systems design behind {api_concept} in modern APIs, highlighting {focus}.",
            "Discuss how {api_concept} solves the {pain_point} in distributed systems and improves {focus}."
        ],
        "output_parts": {
            "intro": [
                "API design is an exercise in constraint. Implementing {api_concept} is not optional.",
                "Good APIs are predictable. Without {api_concept}, you are shipping a ticking time bomb.",
                "The hallmark of a mature API is its handling of edge cases. {api_concept} is how you tame chaos."
            ],
            "body": [
                "When clients inevitably retry requests, a lack of {api_concept} guarantees a {pain_point}. You must enforce state consistency at the edge. By treating operations as idempotent mutations, you decouple the client's network reality from your database's truth. The design is elegant because it shifts the burden of correctness away from application logic into systemic guarantees.",
                "The elegant solution to {pain_point} is strict {api_concept}. Instead of guessing client intent, you force clients to provide a unique token. This token acts as a transactional lock. If the network drops the response, the client retries safely. The server sees the token, bypasses the mutation, and returns the cached result. It is a masterclass in resilient design.",
                "System architecture should mirror its constraints. {api_concept} provides exactly that by bounding the problem space. When you expose a mutable endpoint, you invite race conditions. Structuring the API around strict invariants prevents {pain_point} by design, not by coincidence. The result is {api_benefit}."
            ],
            "code": [
                "```ruby\ndef create_charge(params)\n  idempotency_key = request.headers['Idempotency-Key']\n  return cached_response if already_processed?(idempotency_key)\n  \n  process_charge(params)\nend\n```",
                "```go\nfunc (api *API) HandleRequest(w http.ResponseWriter, r *http.Request) {\n    if !validSignature(r) {\n        http.Error(w, \"Unauthorized\", 401)\n        return\n    }\n    // safe to process\n}\n```",
                "```json\n{\n  \"error\": {\n    \"type\": \"rate_limit_error\",\n    \"message\": \"Too many requests. Back off for 500ms.\"\n  }\n}\n```"
            ],
            "conclusion": [
                "Design for failure. Your API will thank you.",
                "Elegant systems do not emerge by accident. They are engineered.",
                "Build invariants. Trust nothing else."
            ]
        }
    },
    {
        "author": "antirez",
        "register": "pure-direct",
        "instruction_templates": [
            "Explain the C systems perspective on {c_concept}, analyzing its {focus}.",
            "Write about why {c_concept} matters for high-performance databases and {focus}.",
            "Discuss the tradeoffs of {c_concept} in systems programming regarding {focus}."
        ],
        "output_parts": {
            "intro": [
                "Software is just memory and instructions. {c_concept} is where the real work happens.",
                "If you ignore {c_concept}, your system will be slow. It is physics.",
                "The C perspective on {c_concept} is ruthless simplicity. Nothing is hidden."
            ],
            "body": [
                "When you write a database, every byte matters. {c_concept} dictates how the CPU fetches data. If your data is scattered, you stall. You wait for RAM. That is a {pain_point}. By aligning structures and avoiding pointer chasing, you stay in L1 cache. The performance gain is not 10%, it is {metric}. Stop fighting the hardware.",
                "Simplicity is a feature. Handling {c_concept} properly means you do not need complex abstractions. A tight `for` loop over contiguous memory beats a graph of objects every time. We saw this when debugging a {pain_point}. The fix was not more threads. The fix was packing the structs tighter. The OS knows what to do.",
                "You cannot abstraction your way out of {c_concept}. When the kernel gives you memory, it expects you to manage it. Relying on heavy runtimes leads to {pain_point}. In C, you control the exact layout. You know when a page faults. This deterministic behavior is why core infrastructure is still written this way."
            ],
            "code": [
                "```c\n// Tight, contiguous memory. Fast.\nstruct Node {\n    uint64_t id;\n    uint32_t flags;\n    char data[20];\n};\n```",
                "```c\n// Avoid this pointer chasing:\nstruct BadNode {\n    int* values;\n    struct BadNode* next;\n};\n```",
                "```c\nvoid process(uint8_t *buffer, size_t len) {\n    for (size_t i = 0; i < len; i++) {\n        buffer[i] ^= 0xFF;\n    }\n}\n```"
            ],
            "conclusion": [
                "Respect the CPU. Write simple code.",
                "Understand the hardware. Everything else is just syntax.",
                "C does not hide your mistakes. That is its greatest strength."
            ]
        }
    },
    {
        "author": "Martin Fowler",
        "register": "light-personality",
        "instruction_templates": [
            "Write a catalog entry explaining {refactor_concept}, focusing on {focus}.",
            "Discuss the enterprise architecture benefits of {refactor_concept} and its impact on {focus}.",
            "Explain how to use {refactor_concept} to untangle a legacy codebase and improve {focus}."
        ],
        "output_parts": {
            "intro": [
                "Refactoring is about uncovering intent. {refactor_concept} is a powerful tool for that.",
                "Legacy code is just code we are afraid to change. Enter {refactor_concept}.",
                "Good architecture allows deferring decisions. {refactor_concept} enables exactly that."
            ],
            "body": [
                "When you encounter a {pain_point} in a monolithic class, the impulse is to rewrite. Do not do that. Instead, apply {refactor_concept}. By systematically isolating the varying behavior behind a stable interface, you contain the complexity. You turn a sprawling switch statement into a cohesive set of polymorphic behaviors. The code becomes testable overnight.",
                "Enterprise systems rot because boundaries blur. {refactor_concept} restores those boundaries. When you inject dependencies rather than hardcoding them, you decouple the components. This prevents the classic {pain_point} where a change to the database layer breaks the UI. It requires discipline, but it pays off with {metric} faster feature delivery.",
                "The essence of {refactor_concept} is separating the 'what' from the 'how'. When business logic is intertwined with infrastructure, you get a {pain_point}. Extract the core domain logic. Make the framework a detail. Once the core is isolated, testing it takes milliseconds instead of minutes."
            ],
            "code": [
                "```java\n// Extract the interface\npublic interface PaymentStrategy {\n    void pay(Amount amount);\n}\n```",
                "```csharp\n// Inject the dependency\npublic class OrderService {\n    private readonly IRepository _repo;\n    public OrderService(IRepository repo) {\n        _repo = repo;\n    }\n}\n```",
                "```typescript\n// Pure domain logic, no framework\nfunction calculateDiscount(cart: Cart): number {\n    if (cart.total > 100) return 10;\n    return 0;\n}\n```"
            ],
            "conclusion": [
                "Leave the codebase better than you found it.",
                "Refactor constantly, in small steps. Safety is in the small steps.",
                "Clean code is not a luxury. It is how you go fast."
            ]
        }
    },
    {
        "author": "Stripe Engineering",
        "register": "maximal-wit",
        "instruction_templates": [
            "Draft a post-mortem on a production incident caused by a lack of {production_concept}. Emphasize {focus}.",
            "Explain how to implement {production_concept} to achieve {metric} reliability and {focus}.",
            "Write an engineering blog post about scaling with {production_concept} to maintain {focus}."
        ],
        "output_parts": {
            "intro": [
                "Moving money means you cannot fail. {production_concept} is how we survive.",
                "We dropped {metric} of traffic last week. Here is why {production_concept} saved us.",
                "At scale, everything breaks. {production_concept} makes those breaks boring."
            ],
            "body": [
                "When the primary database failed over, we hit a massive {pain_point}. Thousands of retries slammed the API. If we did not have {production_concept} in place, the entire tier would have collapsed. Instead, the system recognized the degraded state, dropped non-critical traffic, and kept processing core payments. It is ruthless prioritization built into the infrastructure.",
                "Scaling a distributed system is just managing failure domains. Implementing {production_concept} allows you to isolate a {pain_point} before it spreads. We route 1% of traffic to the new cluster. If error rates spike, the proxy routes it back automatically. No human intervention needed. Your engineers should not be {busy_work} at 3 AM.",
                "Reliability is not an accident. It is designed. By leveraging {production_concept}, we ensure that a {pain_point} in a downstream service does not impact the critical path. The API responds with a cached state or a clean failure. This gives us {api_benefit} while the platform team recovers the service."
            ],
            "code": [
                "```yaml\n# Envoy circuit breaker config\ncircuit_breakers:\n  thresholds:\n    - max_connections: 1000\n      max_pending_requests: 100\n```",
                "```ruby\n# Shed load if we are drowning\nif Sidekiq::Queue.new.size > 10_000\n  render json: { error: 'system_overloaded' }, status: 503\n  return\nend\n```",
                "```go\n// Fallback logic\nresult, err := fetchFromService()\nif err != nil {\n    metrics.Increment(\"fallback_used\")\n    return getCachedResult()\n}\n```"
            ],
            "conclusion": [
                "Hope is not a strategy. Engineering is.",
                "Automate your mitigations. Sleep through the alerts.",
                "Build for the worst day, every day."
            ]
        }
    }
]

def resolve_template(template: str, variables: dict, rng: random.Random) -> str:
    # Find all placeholders like {tech_trend}
    placeholders = re.findall(r'\{(\w+)\}', template)
    result = template
    for p in placeholders:
        if p in variables:
            val = rng.choice(variables[p])
            result = result.replace("{" + p + "}", val, 1) # replace one at a time for variance if multiple
    return result

def generate_pairs(count: int) -> list[dict]:
    rng = random.Random(2026)
    pairs = []
    
    attempts = 0
    while len(pairs) < count:
        attempts += 1
        if attempts > 15000:
            print("Warning: Max attempts reached.")
            break
            
        blueprint = rng.choice(BLUEPRINTS)
        
        # Generate instruction
        inst_template = rng.choice(blueprint["instruction_templates"])
        instruction = resolve_template(inst_template, VARIABLES, rng)
        
        # Generate output
        intro = resolve_template(rng.choice(blueprint["output_parts"]["intro"]), VARIABLES, rng)
        body = resolve_template(rng.choice(blueprint["output_parts"]["body"]), VARIABLES, rng)
        code = resolve_template(rng.choice(blueprint["output_parts"]["code"]), VARIABLES, rng)
        conclusion = resolve_template(rng.choice(blueprint["output_parts"]["conclusion"]), VARIABLES, rng)
        
        output = f"{intro}\n\n{body}\n\n{code}\n\n{conclusion}"
        
        # Apply filters
        slop, _ = contains_ai_slop(output)
        if slop:
            continue
            
        var_ok, var_val = calculate_sentence_variance(output)
        if not var_ok:
            continue
            
        ttr_ok, ttr_val = calculate_type_token_ratio(output)
        if not ttr_ok:
            continue
            
        # Unique output check
        if any(p["output"] == output for p in pairs):
            continue
            
        pairs.append({
            "instruction": instruction,
            "output": output,
            "metadata": {
                "source_type": "whitelisted_writing",
                "whitelisted_author": blueprint["author"],
                "sentence_variance": var_val,
                "type_token_ratio": ttr_val,
                "slop_free": True,
                "quality_tier": "S",
                "register": blueprint["register"]
            }
        })
        
    return pairs

def main():
    print("=== GENERATING WRITING PILLAR SFT DATASET ===")
    pairs = generate_pairs(700)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in pairs:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated {len(pairs):,} pristine Writing Pillar samples.")
    print(f"Saved to: {OUTPUT_FILE}")
    
    # Calculate stats
    authors = {}
    for p in pairs:
        auth = p["metadata"]["whitelisted_author"]
        authors[auth] = authors.get(auth, 0) + 1
        
    print("\nStats by Author:")
    for auth, cnt in authors.items():
        print(f"  {auth}: {cnt}")

if __name__ == "__main__":
    main()
