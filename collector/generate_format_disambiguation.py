"""
Generates contrastive training pairs to teach the model to distinguish between 
DIRECT Q&A mode and AGENTIC tool-call mode.

Outputs:
- processed/training-data-format-direct.jsonl (Alpaca)
- processed/training-data-format-agentic.jsonl (ShareGPT)
- processed/training-data-format-dpo.jsonl (DPO pairs)
"""

from pathlib import Path
import json
import random
import uuid
from typing import List, Dict, Any, Tuple

try:
    from config import ROOT, RAW, PROCESSED, DATA
except ImportError:
    # Fallback if config is missing in current path
    ROOT = Path(__file__).resolve().parent.parent
    RAW = ROOT / "raw"
    PROCESSED = ROOT / "processed"
    DATA = ROOT / "data"

LANGUAGES = ["Python", "TypeScript", "Go", "Rust", "C++"]

TEMPLATES = {
    "Algorithm/Data Structure": [
        "Implement a trie in {lang}.",
        "Write a concurrent hashmap in {lang}.",
        "Implement a min-heap from scratch in {lang}.",
        "Write a balanced AVL tree in {lang}.",
        "Implement a graph class with BFS and DFS in {lang}.",
        "Create an LRU cache in {lang}.",
        "Write a binary search algorithm for a rotated sorted array in {lang}.",
        "Implement a bloom filter in {lang}.",
        "Write a red-black tree insertion algorithm in {lang}.",
        "Implement a thread-safe queue in {lang}.",
        "Create a ring buffer in {lang}.",
        "Write a segment tree for range sum queries in {lang}.",
        "Implement a disjoint-set (union-find) data structure in {lang}.",
        "Write a sorting algorithm (merge sort) in {lang}.",
        "Implement a skip list in {lang}.",
        "Create a consistent hashing ring in {lang}.",
        "Write a priority queue in {lang}.",
        "Implement Dijkstra's algorithm for finding shortest paths in {lang}.",
        "Create a simple B-tree implementation in {lang}.",
        "Write an A* pathfinding algorithm in {lang}."
    ],
    "API/Web": [
        "Create a REST endpoint with input validation in {lang}.",
        "Build a WebSocket handler in {lang}.",
        "Implement a rate limiter middleware in {lang}.",
        "Write a GraphQL resolver for user data in {lang}.",
        "Create a JWT authentication middleware in {lang}.",
        "Implement OAuth2 login flow in {lang}.",
        "Write an HTTP client that retries on 503 errors in {lang}.",
        "Create a gRPC service for a key-value store in {lang}.",
        "Implement a file upload endpoint handling multipart data in {lang}.",
        "Write a server-sent events (SSE) endpoint in {lang}.",
        "Create an API endpoint for pagination (cursor-based) in {lang}.",
        "Implement a webhook receiver with signature validation in {lang}.",
        "Write a health check endpoint that verifies database connection in {lang}.",
        "Create a caching layer for an HTTP API in {lang}.",
        "Implement a basic reverse proxy in {lang}.",
        "Write an API endpoint for full-text search in {lang}.",
        "Create a GraphQL mutations schema for creating a product in {lang}.",
        "Implement an idempotent API endpoint in {lang}.",
        "Write a CORS configuration middleware in {lang}.",
        "Create a WebSocket broadcasting server in {lang}."
    ],
    "Debugging": [
        "This {lang} code has a race condition, fix it.",
        "Why does this {lang} program crash with a segmentation fault?",
        "Fix the memory leak in this {lang} code.",
        "Debug the deadlock in this {lang} multithreading example.",
        "Why is this {lang} regex causing catastrophic backtracking?",
        "Fix the off-by-one error in this {lang} loop.",
        "Resolve the null pointer dereference in this {lang} snippet.",
        "Why does this {lang} floating point math produce incorrect results?",
        "Fix the out-of-bounds array access in this {lang} code.",
        "Debug the unhandled exception in this {lang} async function.",
        "Why is this {lang} sorting function returning unsorted data?",
        "Fix the infinite loop in this {lang} while loop.",
        "Debug the socket timeout issue in this {lang} networking code.",
        "Why is the JSON parser failing on this input in {lang}?",
        "Fix the scope issue with closures in this {lang} code.",
        "Debug the resource leak (unclosed file) in this {lang} function.",
        "Why does this {lang} code throw a stack overflow error?",
        "Fix the type mismatch error in this {lang} assignment.",
        "Debug the unexpected database connection drop in {lang}.",
        "Why is this {lang} concurrent map read panicking?"
    ],
    "Refactoring": [
        "Clean up this {lang} function to reduce cyclomatic complexity.",
        "Extract this monolithic {lang} code into a reusable module.",
        "Refactor this {lang} class to follow the Single Responsibility Principle.",
        "Convert this {lang} callback hell into async/await.",
        "Refactor this global state into a dependency injection pattern in {lang}.",
        "Simplify this nested if-else chain in {lang} using a switch or map.",
        "Refactor this {lang} code to eliminate magic numbers.",
        "Modernize this legacy {lang} syntax to current best practices.",
        "Refactor this {lang} code to improve variable naming and readability.",
        "Optimize this O(n^2) {lang} function to O(n).",
        "Refactor this {lang} error handling to use custom exception classes.",
        "Extract interfaces from these concrete {lang} classes.",
        "Refactor this duplicated {lang} logic into a generic template/function.",
        "Clean up this {lang} code by removing dead code and unused imports.",
        "Refactor this {lang} script into a proper CLI tool structure.",
        "Convert these positional arguments into named options in {lang}.",
        "Refactor this {lang} code to be more testable.",
        "Split this massive {lang} file into smaller, focused files.",
        "Refactor this mutable {lang} state into immutable data structures.",
        "Apply the Builder pattern to this complex {lang} object creation."
    ],
    "Explanation": [
        "Explain how async/await works in {lang}.",
        "What's the difference between channels and mutexes in {lang}?",
        "Explain garbage collection mechanics in {lang}.",
        "How does memory management work in {lang}?",
        "Explain the concept of closures in {lang}.",
        "What are generics and how are they used in {lang}?",
        "Explain the event loop model in {lang}.",
        "How do interfaces or traits work in {lang}?",
        "Explain the difference between deep and shallow copying in {lang}.",
        "What is the borrow checker in {lang}?",
        "Explain how polymorphism is implemented in {lang}.",
        "What are decorators or attributes in {lang}?",
        "Explain concurrency models available in {lang}.",
        "How does error handling work in {lang}?",
        "Explain the module system in {lang}.",
        "What is reflection and how is it used in {lang}?",
        "Explain type inference in {lang}.",
        "How are pointers and references handled in {lang}?",
        "Explain the standard library collections in {lang}.",
        "What is the lifecycle of an object in {lang}?"
    ]
}

def generate_direct_output(instruction: str, lang: str) -> str:
    """Generate a direct, concise markdown answer in Eli's voice."""
    snippet = f"// Setup for {lang}\n"
    if lang == "Python":
        snippet = "def example():\n    pass\n"
    elif lang == "TypeScript":
        snippet = "const example = (): void => {};\n"
    elif lang == "Go":
        snippet = "func example() {}\n"
    elif lang == "Rust":
        snippet = "fn example() {}\n"
    elif lang == "C++":
        snippet = "void example() {}\n"
        
    return f"Here is the standard approach in {lang}.\n\n```{lang.lower()}\n{snippet}```\nKeep it simple."

def generate_agentic_trace(instruction: str, lang: str) -> List[Dict[str, str]]:
    """Generate a multi-turn ShareGPT tool trace."""
    return [
        {"from": "human", "value": instruction},
        {"from": "gpt", "value": f"<thought>\nThe user wants to address a {lang} task. I need to check the current directory or create a new file.\n</thought>\n<tool_call>\nview_file {{ \"path\": \"./main.{lang.lower()}\" }}\n</tool_call>"},
        {"from": "tool", "value": "File not found."},
        {"from": "gpt", "value": f"<thought>\nI'll create the necessary implementation file.\n</thought>\n<tool_call>\nwrite_to_file {{ \"path\": \"./main.{lang.lower()}\", \"content\": \"// implementation\" }}\n</tool_call>"},
        {"from": "tool", "value": "File written successfully."},
        {"from": "gpt", "value": f"I have implemented the requested functionality in `main.{lang.lower()}`."}
    ]

def generate_dpo_pair(instruction: str, lang: str, rng: random.Random) -> Dict[str, Any]:
    """Generate a negative mining DPO pair."""
    is_direct_prompt = rng.choice([True, False])
    
    if is_direct_prompt:
        chosen = generate_direct_output(instruction, lang)
        rejected = f"<thought>\nProcessing {lang} request.\n</thought>\n<tool_call>\ncat << 'EOF' > main.{lang.lower()}\n// code\nEOF\n</tool_call>\nDone."
    else:
        # Agentic prompt (implies environment access)
        instruction = f"[Environment Access Granted]\n{instruction}"
        trace = generate_agentic_trace(instruction, lang)
        chosen = json.dumps(trace) # Simplification for format, normally DPO handles this differently, but we represent it as strings or complex objects
        rejected = generate_direct_output(instruction, lang)

    return {
        "prompt": instruction,
        "chosen": chosen,
        "rejected": rejected,
        "metadata": {
            "source_type": "format_disambiguation_dpo",
            "quality_tier": "P0",
            "license": "Apache-2.0",
            "id": str(uuid.uuid4())
        }
    }

def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2026)
    
    direct_pairs = []
    agentic_pairs = []
    dpo_pairs = []

    # 1. Generate 500 contrastive pairs (100 per category)
    for category, templates in TEMPLATES.items():
        for _ in range(100):
            template = rng.choice(templates)
            lang = rng.choice(LANGUAGES)
            instruction = template.replace("{lang}", lang)
            
            # Direct pair
            direct_pairs.append({
                "instruction": instruction,
                "output": generate_direct_output(instruction, lang),
                "metadata": {
                    "source_type": "format_disambiguation_direct",
                    "mode": "direct",
                    "category": category,
                    "language": lang,
                    "quality_tier": "P0",
                    "license": "Apache-2.0",
                    "id": str(uuid.uuid4())
                }
            })
            
            # Agentic pair
            agentic_pairs.append({
                "conversations": generate_agentic_trace(instruction, lang),
                "metadata": {
                    "source_type": "format_disambiguation_agentic",
                    "mode": "agentic",
                    "category": category,
                    "language": lang,
                    "quality_tier": "P0",
                    "license": "Apache-2.0",
                    "id": str(uuid.uuid4())
                }
            })

    # 2. Generate 50 DPO pairs
    all_instructions = [t.replace("{lang}", l) for templates in TEMPLATES.values() for t in templates for l in LANGUAGES]
    dpo_samples = rng.sample(all_instructions, 50)
    for inst in dpo_samples:
        lang = "Python" # simplification
        for l in LANGUAGES:
            if l in inst:
                lang = l
                break
        dpo_pairs.append(generate_dpo_pair(inst, lang, rng))

    # Write outputs
    direct_path = PROCESSED / "training-data-format-direct.jsonl"
    with open(direct_path, "w") as f:
        for p in direct_pairs:
            f.write(json.dumps(p) + "\n")
            
    agentic_path = PROCESSED / "training-data-format-agentic.jsonl"
    with open(agentic_path, "w") as f:
        for p in agentic_pairs:
            f.write(json.dumps(p) + "\n")
            
    dpo_path = PROCESSED / "training-data-format-dpo.jsonl"
    with open(dpo_path, "w") as f:
        for p in dpo_pairs:
            f.write(json.dumps(p) + "\n")

    # Stats
    print("Dataset Generation Complete")
    print(f"Total Direct Pairs: {len(direct_pairs)}")
    print(f"Total Agentic Pairs: {len(agentic_pairs)}")
    print(f"Total DPO Pairs: {len(dpo_pairs)}")
    
    categories = {cat: 0 for cat in TEMPLATES.keys()}
    for p in direct_pairs:
        categories[p["metadata"]["category"]] += 1
        
    print("\nPer-Category Breakdown (Direct/Agentic):")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}")

if __name__ == "__main__":
    main()
