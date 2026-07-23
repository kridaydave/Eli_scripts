"""
Generate additional code review pairs to scale from 116 to 150+
for the emergence experiment exposure domain.
Follows the exact schema of data/train_code_review.jsonl.
"""
import json
import random

rng = random.Random(2026)

# Additional code review pairs spanning all 4 cells and multiple languages
ADDITIONAL_PAIRS = [
    # HS_HC - High Stakes, High Certainty (blocking bugs)
    {"id": "HS_HC_034", "cell": "HS_HC", "language": "typescript", "context": "JWT secret hardcoded in source",
     "code": "const JWT_SECRET = \"supersecret123\";\nconst token = jwt.sign(payload, JWT_SECRET);",
     "response": "JWT secret is hardcoded. Anyone with repo access can forge tokens. Move to env var and rotate immediately. Blocker.", "notes": ""},
    {"id": "HS_HC_035", "cell": "HS_HC", "language": "python", "context": "race condition in balance update",
     "code": "def withdraw(user_id, amount):\n    balance = db.get_balance(user_id)\n    if balance >= amount:\n        db.set_balance(user_id, balance - amount)\n        return True\n    return False",
     "response": "TOCTOU race. Two concurrent withdrawals both read the same balance and both succeed. Use SELECT FOR UPDATE or an atomic decrement. Real money on the line here.", "notes": ""},
    {"id": "HS_HC_036", "cell": "HS_HC", "language": "go", "context": "nil pointer dereference on error path",
     "code": "resp, err := http.Get(url)\ndefer resp.Body.Close()\nif err != nil {\n    return err\n}",
     "response": "If http.Get fails, resp is nil and the defer panics. Move the defer after the error check. This will crash in production on any network failure.", "notes": ""},
    {"id": "HS_HC_037", "cell": "HS_HC", "language": "rust", "context": "unwrap on user input parsing",
     "code": "let port: u16 = args[1].parse().unwrap();\nlet addr = format!(\"0.0.0.0:{}\", port);",
     "response": "unwrap on user input. If someone passes 'abc' or '99999', this panics. Use .parse().unwrap_or(8080) or proper error handling. Servers shouldn't crash on bad CLI args.", "notes": ""},
    {"id": "HS_HC_038", "cell": "HS_HC", "language": "python", "context": "eval on user-supplied expression",
     "code": "def calculate(expression):\n    return eval(expression)",
     "response": "eval() on user input is remote code execution. Someone sends __import__('os').system('rm -rf /') and you're done. Use ast.literal_eval() or a proper parser. Hard block.", "notes": ""},
    {"id": "HS_HC_039", "cell": "HS_HC", "language": "javascript", "context": "innerHTML with unsanitized user data",
     "code": "function renderComment(comment) {\n  document.getElementById('comments').innerHTML += `<div>${comment.text}</div>`;\n}",
     "response": "XSS via innerHTML. If comment.text contains <script>alert(1)</script>, it runs. Use textContent or sanitize. This is a security hole.", "notes": ""},
    {"id": "HS_HC_040", "cell": "HS_HC", "language": "go", "context": "mutex not unlocked on early return",
     "code": "func (s *Store) Get(key string) (string, error) {\n    s.mu.Lock()\n    val, ok := s.data[key]\n    if !ok {\n        return \"\", errors.New(\"not found\")\n    }\n    s.mu.Unlock()\n    return val, nil\n}",
     "response": "Mutex is never unlocked on the error path. Every missing key permanently locks the store. Use defer s.mu.Unlock() right after Lock(). This will deadlock in production.", "notes": ""},
    {"id": "HS_HC_041", "cell": "HS_HC", "language": "typescript", "context": "API key exposed in client bundle",
     "code": "const STRIPE_SECRET = process.env.NEXT_PUBLIC_STRIPE_SECRET_KEY;\nconst charge = await stripe(STRIPE_SECRET).charges.create({amount});",
     "response": "NEXT_PUBLIC_ prefix exposes this to the client bundle. Anyone opening DevTools can see your Stripe secret key. Remove the prefix and move this to a server action. Critical.", "notes": ""},

    # HS_LC - High Stakes, Low Certainty (potential issues needing investigation)
    {"id": "HS_LC_027", "cell": "HS_LC", "language": "python", "context": "possible memory leak in long-running worker",
     "code": "class Worker:\n    def __init__(self):\n        self.results = []\n    def process(self, item):\n        result = expensive_compute(item)\n        self.results.append(result)\n        return result",
     "response": "self.results grows unbounded. If this worker runs for hours, it could OOM. Depends on whether results are consumed elsewhere. Worth checking if anything drains this list, or if you need a bounded deque instead.", "notes": ""},
    {"id": "HS_LC_028", "cell": "HS_LC", "language": "go", "context": "context not propagated to downstream call",
     "code": "func HandleRequest(ctx context.Context, req Request) Response {\n    result := db.Query(\"SELECT * FROM users WHERE id = ?\", req.ID)\n    return Response{Data: result}\n}",
     "response": "ctx isn't passed to db.Query. If the client disconnects, the query keeps running. Might not matter for fast queries, but if this hits a slow table scan, you're burning DB connections on abandoned requests. Worth passing ctx through.", "notes": ""},
    {"id": "HS_LC_029", "cell": "HS_LC", "language": "typescript", "context": "possible stale closure in useEffect",
     "code": "useEffect(() => {\n  const interval = setInterval(() => {\n    setCount(count + 1);\n  }, 1000);\n  return () => clearInterval(interval);\n}, []);",
     "response": "count is captured in the closure but not in the dependency array. The interval always reads the initial value. Might be intentional if you want it to only increment once, but I suspect you want setCount(c => c + 1) instead. Double check.", "notes": ""},
    {"id": "HS_LC_030", "cell": "HS_LC", "language": "java", "context": "unchecked cast in generic deserialization",
     "code": "@SuppressWarnings(\"unchecked\")\npublic <T> T deserialize(byte[] data) {\n    return (T) objectMapper.readValue(data, Object.class);\n}",
     "response": "This cast is unchecked and will ClassCastException at the call site, not here. Depends on what T actually is at runtime. If callers always pass the right type it works, but it's fragile. Consider passing Class<T> explicitly.", "notes": ""},
    {"id": "HS_LC_031", "cell": "HS_LC", "language": "python", "context": "float comparison for currency",
     "code": "def apply_discount(price, discount_pct):\n    discount = price * (discount_pct / 100)\n    return price - discount",
     "response": "Float math on currency. 0.1 + 0.2 != 0.3 in IEEE 754. For a checkout flow this could mean charging $9.999999 instead of $10.00. Might be fine for display, but if this touches billing, use Decimal. Worth confirming the use case.", "notes": ""},
    {"id": "HS_LC_032", "cell": "HS_LC", "language": "rust", "context": "clone inside hot loop",
     "code": "fn process_batch(items: &[Item]) -> Vec<Result> {\n    items.iter().map(|item| {\n        let config = get_config().clone();\n        transform(item, &config)\n    }).collect()\n}",
     "response": "Cloning config on every iteration. If get_config() returns something large and items has millions of entries, this could be slow. Hoist the clone outside the loop. Unless config changes per-item, which I doubt but can't confirm from this snippet.", "notes": ""},

    # LS_HC - Low Stakes, High Certainty (minor nits, clear fix)
    {"id": "LS_HC_029", "cell": "LS_HC", "language": "python", "context": "unused import",
     "code": "import os\nimport sys\nimport json\n\ndef parse_config(path):\n    with open(path) as f:\n        return json.load(f)",
     "response": "os and sys are imported but unused. Minor, but clean them up. Won't affect runtime.", "notes": ""},
    {"id": "LS_HC_030", "cell": "LS_HC", "language": "typescript", "context": "console.log left in component",
     "code": "export function UserCard({ user }: Props) {\n  console.log('rendering user', user.id);\n  return <div>{user.name}</div>;\n}",
     "response": "Debug log left in. Remove before merge. Not harmful but clutters the console in production.", "notes": ""},
    {"id": "LS_HC_031", "cell": "LS_HC", "language": "go", "context": "error variable shadowed",
     "code": "err := doFirst()\nif err != nil {\n    err := doSecond()\n    log.Println(err)\n}",
     "response": "Inner err shadows the outer one. := creates a new variable in the if scope. Use = if you want to reassign. Linter would catch this. Not urgent but fix for clarity.", "notes": ""},
    {"id": "LS_HC_032", "cell": "LS_HC", "language": "python", "context": "mutable default argument",
     "code": "def add_item(item, items=[]):\n    items.append(item)\n    return items",
     "response": "Mutable default argument. The list persists across calls. Classic Python gotcha. Use items=None and items = items or [] inside. Low priority but will confuse someone eventually.", "notes": ""},
    {"id": "LS_HC_033", "cell": "LS_HC", "language": "javascript", "context": "== instead of ===",
     "code": "if (status == '200') {\n  handleSuccess();\n}",
     "response": "Use === instead of ==. Type coercion here means 200 == '200' is true, which might be what you want, but it's ambiguous. Be explicit.", "notes": ""},
    {"id": "LS_HC_034", "cell": "LS_HC", "language": "rust", "context": "redundant clone on Copy type",
     "code": "let x: i32 = 42;\nlet y = x.clone();",
     "response": "i32 implements Copy, so .clone() is redundant. Just let y = x. Clippy would flag this. Harmless but noisy.", "notes": ""},
    {"id": "LS_HC_035", "cell": "LS_HC", "language": "typescript", "context": "any type used where interface exists",
     "code": "function processUser(user: any) {\n  return `${user.firstName} ${user.lastName}`;\n}",
     "response": "Using any defeats the point of TypeScript. If you have a User type, use it. If you don't, define one. Takes 30 seconds and saves hours of debugging.", "notes": ""},

    # LS_LC - Low Stakes, Low Certainty (subjective style preferences)
    {"id": "LS_LC_030", "cell": "LS_LC", "language": "python", "context": "list comprehension vs explicit loop",
     "code": "result = []\nfor item in items:\n    if item.active:\n        result.append(item.name)",
     "response": "Could be a list comprehension: [i.name for i in items if i.active]. Both are fine. The comprehension is more Pythonic but the loop is more readable if you're adding complexity later. Personal preference.", "notes": ""},
    {"id": "LS_LC_031", "cell": "LS_LC", "language": "typescript", "context": "named export vs default export",
     "code": "export default function UserProfile() {\n  return <div>Profile</div>;\n}",
     "response": "Default exports make refactoring harder since imports can use any name. Named exports are more grep-friendly. Not a hill I'd die on though.", "notes": ""},
    {"id": "LS_LC_032", "cell": "LS_LC", "language": "go", "context": "receiver name convention",
     "code": "func (self *Server) Start() error {\n    return self.listener.Accept()\n}",
     "response": "Go convention is short receiver names (s for Server, not self). It's a style thing. Won't break anything, but reviewers will mention it.", "notes": ""},
    {"id": "LS_LC_033", "cell": "LS_LC", "language": "python", "context": "f-string vs format()",
     "code": "msg = 'Hello, {}. You have {} messages.'.format(name, count)",
     "response": "f-strings are cleaner: f'Hello, {name}. You have {count} messages.' But .format() works fine. Readability call.", "notes": ""},
    {"id": "LS_LC_034", "cell": "LS_LC", "language": "javascript", "context": "arrow function vs function declaration",
     "code": "const handleClick = (e) => {\n  e.preventDefault();\n  submit();\n};",
     "response": "Arrow vs function declaration is mostly style. Arrows don't have their own this, which matters in class components but not in hooks. Either works here.", "notes": ""},
    {"id": "LS_LC_035", "cell": "LS_LC", "language": "rust", "context": "match vs if let for single arm",
     "code": "match result {\n    Ok(val) => process(val),\n    Err(_) => {},\n}",
     "response": "if let Ok(val) = result { process(val) } is cleaner for single-arm matches. But match is fine too if you expect to add more arms later. Taste call.", "notes": ""},
    {"id": "LS_LC_036", "cell": "LS_LC", "language": "typescript", "context": "enum vs union type",
     "code": "enum Status {\n  Active = 'active',\n  Inactive = 'inactive',\n  Pending = 'pending',\n}",
     "response": "Some prefer type Status = 'active' | 'inactive' | 'pending' since it's simpler and doesn't generate runtime code. Enums give you reverse mapping though. Depends on whether you need that.", "notes": ""},
]

# Write the additional pairs
output_path = "data/train_code_review.jsonl"

# Read existing
with open(output_path) as f:
    existing = [line.strip() for line in f if line.strip()]

# Append new
with open(output_path, "a") as f:
    for pair in ADDITIONAL_PAIRS:
        f.write(json.dumps(pair) + "\n")

total = len(existing) + len(ADDITIONAL_PAIRS)
print(f"Added {len(ADDITIONAL_PAIRS)} code review pairs. Total: {total}")

# Count cells
cells = {}
for pair in ADDITIONAL_PAIRS:
    cells[pair["cell"]] = cells.get(pair["cell"], 0) + 1
print(f"New pairs by cell: {json.dumps(cells, indent=2)}")
