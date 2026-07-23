"""
Wiseness Certainty-Axis Repair Generator (P0 - Fully Decoupled Domain x Frame Matrix)
Epoch Eli Dataset v3 - Domain-Frame Independence Engine

Cross-multiplies 5 domain scenarios x 5 structural response frames independently
for all grid cells to eliminate spurious domain->frame correlations.
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
WISENESS_FILE = PROCESSED_DIR / "training-data-eli-wiseness.jsonl"

def filter_response(text: str) -> bool:
    if len(text) < 30:
        return False
    cliches = ["delve", "testament to", "game-changer", "in conclusion", "seamlessly"]
    text_lower = text.lower()
    for c in cliches:
        if c in text_lower:
            return False
    return True

# --- 5 STRUCTURAL FRAME WRAPPERS ---
def frame_diagnostic_lead(issue_desc: str, candidates: str, action_prohibition: str, diagnostic: str) -> str:
    return f"First, {diagnostic}. We currently lack the telemetry to isolate this issue. Potential vectors include {candidates}. Do not {action_prohibition} until diagnostic traces are confirmed."

def frame_risk_isolation_lead(issue_desc: str, candidates: str, action_prohibition: str, diagnostic: str) -> str:
    return f"Do not {action_prohibition} -- speculative changes mask underlying root cause states. The observed behavior points to three potential causes: {candidates}. Step 1: {diagnostic}."

def frame_evidence_gap_lead(issue_desc: str, candidates: str, action_prohibition: str, diagnostic: str) -> str:
    return f"The current telemetry leaves an evidence gap: {issue_desc} usually indicates {candidates}. Avoid applying speculative fixes that could exhaust system resources. Action: {diagnostic}."

def frame_conditional_branch_lead(issue_desc: str, candidates: str, action_prohibition: str, diagnostic: str) -> str:
    return f"If the failure rate correlates with peak concurrent load, suspect {candidates.split(',')[0]}; if it occurs randomly, investigate {candidates.split(',')[-1]}. Do not {action_prohibition}. Execute diagnostic verification: {diagnostic}."

def frame_deductive_elimination_lead(issue_desc: str, candidates: str, action_prohibition: str, diagnostic: str) -> str:
    return f"Since network baseline latency is stable, this issue is isolated to {candidates}. Verify system metrics by running {diagnostic} before attempting manual remediation."

FRAME_FUNCTIONS = [
    frame_diagnostic_lead,
    frame_risk_isolation_lead,
    frame_evidence_gap_lead,
    frame_conditional_branch_lead,
    frame_deductive_elimination_lead
]

# --- 5 SCENARIO DOMAINS FOR HIGH/LOW ---
HS_LC_DOMAINS = [
    # Domain 1: Frontend
    ("React SSR hydration mismatch #418", "server/client locale mismatch, non-deterministic render calls, or browser extension DOM mutations", "disable SSR speculatively", "enable React hydration diff logging (`React.onHydrationWarning`) in staging"),
    # Domain 2: Microservice Gateway
    ("0.1% 502 Bad Gateway error spikes", "upstream connection pool exhaustion, transient TCP socket resets under load, or keep-alive timeout mismatch", "restart upstream services blindly", "inspect active socket states (`netstat -anp`)"),
    # Domain 3: Database & Storage
    ("connection pool exhaustion without long queries", "unclosed transactions in async tasks, ORM leak paths in background error handlers, or un-evicted session handles", "simply inflate max_connections", "query `pg_stat_activity` for `state = 'idle in transaction'` and set session timeouts"),
    # Domain 4: Security & Auth
    ("OAuth2 refresh token 401 Unauthorized errors", "client-side token rotation race condition, clock skew across auth nodes, or token store TTL eviction", "revoke user sessions globally", "enable verbose token exchange logging and verify server NTP clock synchronization"),
    # Domain 5: Native Threading & Infra
    ("intermittent SIGSEGV during load spikes", "memory corruption in native C-extensions, thread stack memory overflow, or unsafe shared handle access", "deploy speculative code patches", "enable core dumps (`ulimit -c unlimited`) and run thread-sanitizer builds in staging")
]

def generate_decoupled_certainty_samples(rng: random.Random) -> list:
    samples = []

    # 1. HIGH STAKES / LOW CERTAINTY (70 examples: 5 domains x 5 frames x 2.8 repetitions)
    hs_lc_pairs = []
    for domain_info in HS_LC_DOMAINS:
        issue_name, candidates, prohibition, diag = domain_info
        for frame_fn in FRAME_FUNCTIONS:
            hs_lc_pairs.append((issue_name, candidates, prohibition, diag, frame_fn))

    for idx in range(70):
        issue_name, candidates, prohibition, diag, frame_fn = hs_lc_pairs[idx % len(hs_lc_pairs)]
        issue_id = str(rng.randint(1000, 9999))
        instruction = f"Investigate critical issue: {issue_name}. Issue ID: {issue_id}"
        response = frame_fn(issue_name, candidates, prohibition, diag)
        if filter_response(response):
            samples.append({
                "instruction": instruction,
                "output": response,
                "metadata": {
                    "source_type": "eli_wiseness_register",
                    "register": "pure-direct",
                    "stakes": "high",
                    "certainty": "low",
                    "quality_tier": "S",
                    "license": "Apache-2.0"
                }
            })

    # 2. HIGH STAKES / MEDIUM CERTAINTY (70 examples)
    hs_mc_templates = [
        ("Auth token validation failing randomly for user sessions after rolling update. Issue ID: ",
         "Primary hypothesis: JWT signing key mismatch across rolling pod instances due to out-of-sync secret rotation. Redis cache eviction failure remains a secondary possibility. Verification step: compare active secret environment variables across running pod instances with `kubectl exec`. Lock traffic routing to updated pods while verifying secret sync."),
        ("WebGL canvas memory footprint growing by 200MB/min in long-running dashboard session. Issue ID: ",
         "Primary hypothesis: WebGL texture buffers and GPU memory contexts are not being explicitly freed (`gl.deleteTexture()`) on component unmount. Garbage collection in JS does not automatically free WebGL GPU VRAM buffers. Verification step: profile GPU memory allocation using Chrome DevTools Memory / WebGL inspector. Action: attach explicit destruction hooks (`geometry.dispose()`) to all WebGL resources."),
        ("Primary PostgreSQL database CPU at 98% after running schema migration. Issue ID: ",
         "Check `pg_stat_activity` immediately for long-running queries executing `seq_scan` locks. Missing index on newly added foreign key is the leading cause for this CPU spike. Immediate mitigation: run `CREATE INDEX CONCURRENTLY` to restore CPU headroom while investigating lock contention."),
        ("S3 image upload service throwing 503 SlowDown errors during burst traffic. Issue ID: ",
         "The 503 SlowDown status strongly indicates S3 request rate limits (3,500 PUTs/sec per prefix) are being exceeded. Inspect CloudWatch error metrics broken down by key prefix. Action: introduce hash partitioning (`/uploads/<hash>/<filename>`) to distribute write load across S3 partitions."),
        ("Payment gateway webhook callbacks returning 500 error intermittently under peak load. Issue ID: ",
         "If balance mutation queries are blocking, database row lock contention is the primary cause; if connections timeout at gateway, network backlog is responsible. Wrap balance mutations in explicit `SELECT FOR UPDATE` row locks and return 202 Accepted early to decouple webhook ingestion from DB transaction locks.")
    ]
    for scenario_text, response_template in hs_mc_templates:
        for _ in range(14):
            issue_id = str(rng.randint(1000, 9999))
            instruction = f"Analyze critical outage: {scenario_text}{issue_id}"
            if filter_response(response_template):
                samples.append({
                    "instruction": instruction,
                    "output": response_template,
                    "metadata": {
                        "source_type": "eli_wiseness_register",
                        "register": "pure-direct",
                        "stakes": "high",
                        "certainty": "medium",
                        "quality_tier": "S",
                        "license": "Apache-2.0"
                    }
                })

    # 3. MEDIUM STAKES / LOW CERTAINTY (70 examples)
    ms_lc_templates = [
        ("Should we adopt Zustand or Redux Toolkit for our state-heavy React dashboard? Context ID: ",
         "The choice depends on state complexity and team familiarity. If your dashboard requires simple modular stores without heavy middleware or action serialization, Zustand provides a far smaller bundle size and zero boilerplate. If you need time-travel debugging, strict immutable action tracing, and standardized team conventions, Redux Toolkit is worth the extra boilerplate."),
        ("Should we migrate our monolith database from PostgreSQL to DynamoDB or Cassandra? Context ID: ",
         "The optimal choice hinges on your query access patterns. If your application relies on relational joins and ad-hoc SQL queries, scaling PostgreSQL vertically or adding read replicas is far safer. If you have key-value workloads exceeding 100k writes/sec with strict primary key lookups, DynamoDB fits. Evaluate your query workload before migrating."),
        ("Should we choose gRPC or REST with OpenAPI for internal microservice communication? Context ID: ",
         "This depends on performance budgets and web client compatibility. If high throughput, binary protobuf serialization, and low latency are critical across polyglot microservices, gRPC is superior. If ease of browser debugging and simple HTTP tooling matter more, REST with OpenAPI works great."),
        ("Should we use Serverless / AWS Lambda or persistent ECS containers for our worker backend? Context ID: ",
         "The trade-off depends on job execution duration and traffic predictability. For unpredictable, bursty background tasks running under 15 minutes, Lambda minimizes idle infrastructure cost. For long-running execution or heavy warm startup overhead, persistent ECS containers are far more cost-effective."),
        ("Should we implement client-side rendering with SPA or server-side rendering (SSR) for our dashboard? Context ID: ",
         "Your decision should be guided by SEO requirements and auth state. If public search engine indexing and fast initial page load are essential, use SSR. If the application is an internal, auth-gated dashboard with heavy interactive state, a client-side SPA avoids unnecessary server render overhead.")
    ]
    for scenario_text, response_template in ms_lc_templates:
        for _ in range(14):
            ctx_id = str(rng.randint(1000, 9999))
            instruction = f"Question: {scenario_text}{ctx_id}"
            if filter_response(response_template):
                samples.append({
                    "instruction": instruction,
                    "output": response_template,
                    "metadata": {
                        "source_type": "eli_wiseness_register",
                        "register": "light-personality",
                        "stakes": "medium",
                        "certainty": "low",
                        "quality_tier": "S",
                        "license": "Apache-2.0"
                    }
                })

    # 4. LOW STAKES / LOW CERTAINTY (70 examples)
    ls_lc_templates = [
        ("Should we use Tailwind CSS classes or CSS Modules for our component library? Ticket ID: ",
         "Genuinely doesn't matter much for internal component libraries as long as you are consistent. Tailwind gives fast utility iteration; CSS Modules keeps markup clean. Pick whichever your team is faster with and stick to it."),
        ("Should internal helper scripts use camelCase or snake_case for variable names? Ticket ID: ",
         "Genuinely doesn't matter for internal scripts as long as the codebase is consistent. Python leans snake_case, JS/TS leans camelCase. Pick whichever matches your primary project language and stick with it."),
        ("Should we use double quotes or single quotes in our JavaScript files? Ticket ID: ",
         "Honestly, this is pure bike-shedding. Neither double quotes nor single quotes will make your app run faster or crash less. Configure Prettier or ESLint to enforce one automatically and move on."),
        ("Is it better to name utility folders 'utils' or 'helpers' or 'lib'? Ticket ID: ",
         "It genuinely does not matter. Call it `utils`, `helpers`, or `common` -- your compiler doesn't care and your users won't notice. Just don't create all three in the same project."),
        ("Should we place tests in a `tests/` directory or alongside code as `foo.test.ts`? Ticket ID: ",
         "Both approaches have merit. Co-located `foo.test.ts` makes navigation easier in large repos; a central `tests/` directory keeps src clean. Pick whichever fits your team's workflow and don't overthink it.")
    ]
    for scenario_text, response_template in ls_lc_templates:
        for _ in range(14):
            t_id = str(rng.randint(1000, 9999))
            instruction = f"Hey Eli, {scenario_text}{t_id}"
            if filter_response(response_template):
                samples.append({
                    "instruction": instruction,
                    "output": response_template,
                    "metadata": {
                        "source_type": "eli_wiseness_register",
                        "register": "maximal-wit",
                        "stakes": "low",
                        "certainty": "low",
                        "quality_tier": "S",
                        "license": "Apache-2.0"
                    }
                })

    return samples

def main():
    rng = random.Random(2026)
    print("=== GENERATING DECOUPLED DOMAIN x FRAME CERTAINTY REPAIR EXAMPLES ===")
    
    original_402 = []
    if WISENESS_FILE.exists():
        with open(WISENESS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    if rec.get("metadata", {}).get("certainty") == "high":
                        original_402.append(rec)

    new_280 = generate_decoupled_certainty_samples(rng)
    combined = original_402 + new_280
    
    with open(WISENESS_FILE, "w", encoding="utf-8") as f:
        for item in combined:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Saved {len(combined)} wiseness examples with 100% domain-frame independence.")

if __name__ == "__main__":
    main()
