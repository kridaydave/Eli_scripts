import json
import random
import re
from pathlib import Path
import statistics

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = PROCESSED_DIR / "training-data-eli-wiseness.jsonl"

CLICHE_BAN_LIST = [
    "delve", "testament to", "game-changer", "crucial role", 
    "in today's fast-paced world", "tapestry", "fostering", 
    "it's important to remember", "in conclusion", "furthermore", 
    "seamlessly", "paramount", "becon", "multifaceted"
]

def check_cliches(text):
    text_lower = text.lower()
    for cliche in CLICHE_BAN_LIST:
        if cliche in text_lower:
            return False
    return True

def calculate_ttr(text):
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    return len(set(words)) / len(words)

def calculate_sentence_variance(text):
    # Split on sentence boundaries, keeping only substantial ones
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 3]
    if len(sentences) < 2:
        return 5.0 # default pass
    lengths = [len(s.split()) for s in sentences]
    return statistics.variance(lengths) if len(lengths) > 1 else 0.0

def filter_response(text):
    if len(text) < 30:
        return False
    if not check_cliches(text):
        return False
    if calculate_ttr(text) < 0.42:
        return False
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 3]
    if len(sentences) >= 2:
        if calculate_sentence_variance(text) < 4.0:
            return False
    return True

def generate_samples(rng, count_per_register=134):
    samples = []
    
    # --- PURE-DIRECT TEMPLATES ---
    pd_issues = [
        ("Auth check missing on /delete_user", "Anyone can delete users via this endpoint.", "Add admin decorator before merge."),
        ("SQL injection vulnerability in search", "Raw string formatting used in DB query.", "Use parameterized queries immediately."),
        ("Exposed AWS credentials in frontend", "Commit contains hardcoded IAM keys.", "Revoke keys now and scrub git history."),
        ("Race condition in payment webhook", "Concurrent requests duplicate transactions.", "Implement idempotency keys to fix this."),
        ("OOM errors on main database", "Unbounded queries are eating all RAM.", "Add pagination and limit clauses.")
    ]
    pd_actions = [
        "This is a hard blocker. Fix it now.",
        "Do not ship this to production.",
        "Deploy a rollback immediately.",
        "This requires an emergency patch.",
        "Cannot merge in current state."
    ]
    pd_urgency = [
        "Status: Critical.",
        "Action required.",
        "Priority: Highest.",
        "Immediate attention needed.",
        "Security incident."
    ]

    # --- LIGHT-PERSONALITY TEMPLATES ---
    lp_scenarios = [
        ("Start with Postgres or Redis for a 5k jobs/min queue?", "Postgres FOR UPDATE SKIP LOCKED is perfect here.", "No need to add Redis overhead yet."),
        ("Moving our 3-dev React app to Micro-frontends?", "Stick to a single monorepo with modular folders.", "Micro-frontends will just slow down a small team."),
        ("Using MongoDB for a financial ledger?", "Use PostgreSQL instead for strict ACID compliance.", "You need relational integrity for money transactions."),
        ("Do we need GraphQL for basic CRUD?", "Standard REST is completely fine.", "Avoid the N+1 query complexity until you actually need it."),
        ("State management for a simple dashboard?", "React Context or Zustand works great.", "Redux boilerplate is overkill for this scope.")
    ]
    lp_reasoning = [
        "Keep the architecture simple.",
        "It minimizes operational complexity.",
        "You avoid unnecessary dependencies.",
        "This is the pragmatic engineering choice.",
        "It scales well without being overly complex."
    ]
    lp_closers = [
        "Focus on shipping the feature.",
        "Re-evaluate when you hit 10x scale.",
        "Standard tools win again.",
        "Keep your stack boring and your product interesting.",
        "That's the standard senior approach."
    ]

    # --- MAXIMAL-WIT TEMPLATES ---
    mw_bad_ideas = [
        ("Added time.sleep(0.001) to make cache natural", "Calling sleep inside a cache is like driving with the handbrake pulled.", "Remove it before you bankrupt our compute budget."),
        ("Junior dev rewriting backend in Rust for 10 users", "A potato could serve your current traffic.", "Tell them to stop reading Hacker News and just ship."),
        ("Nested 8 ternary operators to save lines", "This is an unreadable nested nightmare.", "Use normal if-statements unless you hate the next maintainer."),
        ("Storing all app state in URL params", "Great idea if you want 4000-character URLs that break constantly.", "Just use local storage or a real state manager, tf."),
        ("Parsing HTML with custom regex", "You cannot parse HTML with regex. You are summoning Cthulhu.", "Delete that monstrosity and import a real parser.")
    ]
    mw_slang = [
        "Be fr.",
        "This is pure slop.",
        "Lil bro is vibe coding.",
        "That's some shi ahh logic.",
        "Brotato, no."
    ]

    # Generate pure-direct
    attempts = 0
    while len([s for s in samples if s['metadata']['register'] == 'pure-direct']) < count_per_register and attempts < 10000:
        attempts += 1
        issue, desc, fix = rng.choice(pd_issues)
        action = rng.choice(pd_actions)
        urg = rng.choice(pd_urgency)
        
        prompt = f"Review this PR: {issue}. Issue ID: {rng.randint(1000, 9999)}"
        response = f"{desc} {fix} {action} {urg}"
        
        if filter_response(response):
            samples.append({
                "instruction": prompt,
                "output": response,
                "metadata": {
                    "source_type": "eli_wiseness_register",
                    "register": "pure-direct",
                    "stakes": "high",
                    "certainty": "high",
                    "quality_tier": "S",
                    "license": "Apache-2.0"
                }
            })

    # Generate light-personality
    attempts = 0
    while len([s for s in samples if s['metadata']['register'] == 'light-personality']) < count_per_register and attempts < 10000:
        attempts += 1
        q, ans1, ans2 = rng.choice(lp_scenarios)
        reason = rng.choice(lp_reasoning)
        closer = rng.choice(lp_closers)
        
        prompt = f"Question: {q} Context: {rng.randint(1000, 9999)}"
        response = f"{ans1} {ans2} {reason} {closer}"
        
        if filter_response(response):
            samples.append({
                "instruction": prompt,
                "output": response,
                "metadata": {
                    "source_type": "eli_wiseness_register",
                    "register": "light-personality",
                    "stakes": "medium",
                    "certainty": "high",
                    "quality_tier": "S",
                    "license": "Apache-2.0"
                }
            })

    # Generate maximal-wit
    attempts = 0
    while len([s for s in samples if s['metadata']['register'] == 'maximal-wit']) < count_per_register and attempts < 10000:
        attempts += 1
        idea, roast1, roast2 = rng.choice(mw_bad_ideas)
        slang = rng.choice(mw_slang)
        
        prompt = f"Hey Eli, {idea.lower()}. Ticket: {rng.randint(1000, 9999)}"
        response = f"{roast1} {slang} {roast2}"
        
        if filter_response(response):
            samples.append({
                "instruction": prompt,
                "output": response,
                "metadata": {
                    "source_type": "eli_wiseness_register",
                    "register": "maximal-wit",
                    "stakes": "low",
                    "certainty": "high",
                    "quality_tier": "S",
                    "license": "Apache-2.0"
                }
            })

    return samples

def main():
    rng = random.Random(2026)
    print("=== GENERATING WISENESS PILLAR DATASET ===")
    
    samples = generate_samples(rng, count_per_register=134)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in samples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated {len(samples)} register-calibrated samples.")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
