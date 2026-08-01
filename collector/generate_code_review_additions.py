"""
Generate additional code review pairs to scale from 116 to 150+
for the emergence experiment exposure domain.
Follows the exact schema of data/train_code_review.jsonl.
"""
import json
import random
from pathlib import Path

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

# ------------------------------------------------------------------ #
# Security Audit Sub-Lane  (P0)
# PR-diff + review-comment pairs: input is a diff carrying a security
# vulnerability, output is a severity-tagged review comment with a fix.
# Written to processed/training-data-code-review-security.jsonl.
# ------------------------------------------------------------------ #
SECURITY_SAMPLES = [
    {
        "id": "SEC_AUDIT_001", "language": "python", "framework": "FastAPI",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,7 +1,7 @@\n"
            " import os\n"
            " from fastapi import FastAPI\n"
            " \n"
            " app = FastAPI()\n"
            "-SECRET_KEY = os.environ.get('APP_SECRET')\n"
            "+SECRET_KEY = 'sup3r-s3cret-please-dont-leak'\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: Hardcoded `SECRET_KEY` in `settings.py` (line 4). Anyone with repo "
            "access can mint forged session/JWT tokens. Rotate immediately and move the value "
            "to an env var / secret manager. See fix:\n\n"
            "```python\n"
            "SECRET_KEY = os.environ['APP_SECRET']\n"
            "```"
        ),
    },
    {
        "id": "SEC_AUDIT_002", "language": "python", "framework": "FastAPI",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,6 +1,6 @@\n"
            " from fastapi.middleware.cors import CORSMiddleware\n"
            " \n"
            " app.add_middleware(\n"
            "     CORSMiddleware,\n"
            "-    allow_origins=ALLOWED_ORIGINS,\n"
            "+    allow_origins=[\"*\"],\n"
            "     allow_credentials=True,\n"
            " )\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: `allow_origins=[\"*\"]` combined with `allow_credentials=True` is "
            "invalid and dangerous - any origin can send credentialed (cookie) requests, i.e. "
            "CSRF. Use an explicit allowlist of your own origins (never `*` with credentials)."
        ),
    },
    {
        "id": "SEC_AUDIT_003", "language": "python", "framework": "FastAPI",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,5 +1,5 @@\n"
            " import requests\n"
            " response = requests.get(\n"
            "     'https://payment-gw.internal/charge',\n"
            "-    verify=CA_BUNDLE,\n"
            "+    verify=False,\n"
            "     timeout=5,\n"
            " )\n"
            "```"
        ),
        "output": (
            "🟠 MAJOR: `verify=False` disables TLS certificate validation on the payment call "
            "(line 3) - enables MITM and credential/PAN theft. Remove it and always verify "
            "against a real CA bundle."
        ),
    },
    {
        "id": "SEC_AUDIT_004", "language": "python", "framework": "FastAPI",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " def search(user_input):\n"
            "-    query = \"SELECT * FROM items WHERE name = %s\"\n"
            "-    cursor.execute(query, (user_input,))\n"
            "+    query = \"SELECT * FROM items WHERE name = '\" + user_input + \"'\"\n"
            "+    cursor.execute(query)\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: SQL string concatenation with raw `user_input` (lines 3-4) reintroduces "
            "SQL injection. Restore parameterized queries - never interpolate user data: "
            "`cursor.execute(\"SELECT * FROM items WHERE name = %s\", (user_input,))`."
        ),
    },
    {
        "id": "SEC_AUDIT_005", "language": "python", "framework": "FastAPI",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " def calculate(expr):\n"
            "-    return eval(expr)\n"
            "+    return eval(sanitize(expr))\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: wrapping `eval()` in a `sanitize()` helper does not fix arbitrary code "
            "execution - `eval`/`exec` on any user-influenced string is RCE. Replace with "
            "`ast.literal_eval()` or a real expression parser and allowlist of operators."
        ),
    },



    {
        "id": "SEC_AUDIT_006", "language": "javascript", "framework": "Express",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " const jwt = require('jsonwebtoken');\n"
            " const token = jwt.sign(payload, secret, {\n"
            "-  algorithm: 'HS256',\n"
            "+  algorithm: 'none',\n"
            " });\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: JWT `algorithm: 'none'` means tokens carry no signature at all - "
            "anyone can forge arbitrary identities. Remove it (default to HS256/RS256) and "
            "deny `alg: none` on the verify path."
        ),
    },
    {
        "id": "SEC_AUDIT_007", "language": "javascript", "framework": "Express",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,5 +1,5 @@\n"
            " const express = require('express');\n"
            " const helmet = require('helmet');\n"
            " const app = express();\n"
            "-app.use(helmet());\n"
            "+// app.use(helmet());  // disabled while debugging\n"
            " app.use(express.json());\n"
            "```"
        ),
        "output": (
            "🟠 MAJOR: `helmet()` (SecurityHeaders, XSS filter, HSTS, etc.) is commented out - "
            "every default security header is now off in prod. Re-enable it (or the specific "
            "headers you need) and remove the debug comment."
        ),
    },
    {
        "id": "SEC_AUDIT_008", "language": "javascript", "framework": "Express",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " app.post('/api/user', (req, res) => {\n"
            "-  const user = clean(req.body);\n"
            "+  const user = Object.assign({}, req.body);\n"
            "   db.save(user);\n"
            " });\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: `Object.assign({}, req.body)` copies attacker-controlled keys onto the "
            "object - prototype pollution when `req.body` contains `__proto__`/`constructor`, "
            "plus mass-assignment of internal fields. Whitelist the exact keys you save and "
            "guard against `__proto__`."
        ),
    },
    {
        "id": "SEC_AUDIT_009", "language": "javascript", "framework": "Express",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,5 +1,5 @@\n"
            " // POST /login\n"
            " async function login(req, res) {\n"
            "   const ok = await checkCreds(req.body);\n"
            "   if (ok) {\n"
            "-    console.log('login ok');\n"
            "+    // rate limiter TODO\n"
            "     res.json({ token: sign({ user: req.body.user }) });\n"
            "   }\n"
            " }\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER (auth): no rate limiter on the login endpoint - attackers can brute "
            "force / credential-stuff indefinitely, and the placeholder comment shows it was "
            "deferred. Add `express-rate-limit` (or an API gateway limit) and lockout on the "
            "auth route before merging."
        ),
    },
    {
        "id": "SEC_AUDIT_010", "language": "go", "framework": "net/http",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            "-import \"html/template\"\n"
            "+import \"text/template\"\n"
            " \n"
            " t, err := template.ParseFiles(\"user.html\")\n"
            " t.Execute(w, userInput)\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: switching to `text/template` for an HTML response disables all "
            "auto-escaping - reflected `userInput` is rendered raw, opening stored/reflected "
            "XSS. Revert to `html/template` which escapes context-appropriately."
        ),
    },
    {
        "id": "SEC_AUDIT_011", "language": "go", "framework": "database/sql",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,5 +1,5 @@\n"
            " func listUsers() ([]User, error) {\n"
            "     rows, err := db.Query(\"SELECT * FROM users\")\n"
            "     if err != nil { return nil, err }\n"
            "-    defer rows.Close()\n"
            "     var us []User\n"
            "     for rows.Next() { ... }\n"
            "     return us, rows.Err()\n"
            " }\n"
            "```"
        ),
        "output": (
            "🟠 MAJOR: the `defer rows.Close()` was dropped - the connection stays in the pool "
            "until GC, leaking sockets under load and eventually exhausting the DB pool. "
            "Restore `defer rows.Close()` immediately after the error check."
        ),
    },
    {
        "id": "SEC_AUDIT_012", "language": "go", "framework": "database/sql",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,5 +1,5 @@\n"
            " func openDB() *sql.DB {\n"
            "-    dsn := os.Getenv(\"DB_DSN\")\n"
            "+    dsn := \"postgres://admin:S3cretPass@10.10.0.5/prod\"\n"
            "     db, _ := sql.Open(\"postgres\", dsn)\n"
            "     return db\n"
            " }\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: hardcoded DB connection string with credentials at line 3 - leaks prod "
            "DB password to anyone with repo access. Read from env/secret store and rotate the "
            "password immediately."
        ),
    },
    {
        "id": "SEC_AUDIT_013", "language": "go", "framework": "net/http",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " func fetch(req Request) ([]byte, error) {\n"
            "-    ctx, cancel := context.WithTimeout(req.Context(), 5*time.Second)\n"
            "-    defer cancel()\n"
            "     httpReq, _ := http.NewRequest(\"GET\", url, nil)\n"
            "     resp, err := http.DefaultClient.Do(httpReq)\n"
            "```"
        ),
        "output": (
            "🟠 MAJOR: the `context.WithTimeout` wrapper was removed - the outbound HTTP call "
            "now has no deadline, so a hung upstream can stall the goroutine/connection forever. "
            "Re-add the timeout context and pass it to `NewRequestWithContext`."
        ),
    },


    {
        "id": "SEC_AUDIT_014", "language": "python", "framework": "general",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " def restore(state):\n"
            "-    state = json.loads(state)\n"
            "+    state = pickle.loads(state)\n"
            "     return state\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: `pickle.loads` on any data that could be attacker-controlled is "
            "arbitrary code execution - pickles run `__reduce__` during unpickling. Never "
            "unpickle untrusted input; use JSON or a signed serialization format."
        ),
    },
    {
        "id": "SEC_AUDIT_015", "language": "python", "framework": "FastAPI",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,5 +1,5 @@\n"
            " import subprocess\n"
            " def run(cmd):\n"
            "-    parts = shlex.split(cmd)\n"
            "-    return subprocess.run(parts, check=True)\n"
            "+    parts = shlex.split(cmd)\n"
            "+    return subprocess.run(cmd, shell=True, check=True)\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: `shell=True` on a string that originates from user input is command "
            "injection even after `shlex.split` (the raw string reaches the shell). Use the "
            "argument-list form without `shell=True`, or validate against an allowlist first."
        ),
    },
    {
        "id": "SEC_AUDIT_016", "language": "javascript", "framework": "Express",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " async function verifyPassword(user, supplied) {\n"
            "-  const ok = await bcrypt.compare(supplied, user.hash);\n"
            "+  const ok = bcrypt.compare(supplied, user.hash);\n"
            "   return ok;\n"
            " }\n"
            "```"
        ),
        "output": (
            "🟠 MAJOR: dropping `await` on `bcrypt.compare(...)` returns a pending Promise - "
            "auth will always evaluate truthy and let anyone log in, and it defeats the "
            "comparison's timing safety. Keep `await` and handle the rejection path."
        ),
    },
    {
        "id": "SEC_AUDIT_017", "language": "go", "framework": "database/sql",
        "severity": "🔴 BLOCKER",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " func find(id string) (Item, error) {\n"
            "-    row := db.QueryRow(\"SELECT * FROM items WHERE id = ?\", id)\n"
            "+    row := db.QueryRow(\"SELECT * FROM items WHERE id = '\" + id + \"'\")\n"
            "     return scan(row)\n"
            " }\n"
            "```"
        ),
        "output": (
            "🔴 BLOCKER: concatenating `id` into the SQL string reopens SQL injection. One "
            "parameterized query is the fix - `db.QueryRow(\"SELECT * FROM items WHERE id = ?\", id)`."
        ),
    },

    {
        "id": "SEC_AUDIT_018", "language": "python", "framework": "FastAPI",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,5 +1,5 @@\n"
            " @app.post(\"/render\")\n"
            " def render(tpl: str):\n"
            "-    out = template_env.from_string(tpl).render(user=current_user)\n"
            "+    out = open(f\"/templates/{tpl}.html\").read()\n"
            "     return HTMLResponse(out)\n"
            "```"
        ),
        "output": (
            "🟠 MAJOR: path joining with `tpl` unchecked enables directory traversal "
            "(`../../etc/passwd.html`) and loses template sandboxing. Use a Jinja loader with "
            "an allowlist and never raw `open()` on a user-controlled filename."
        ),
    },
    {
        "id": "SEC_AUDIT_019", "language": "javascript", "framework": "Express",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " app.get('/search', (req, res) => {\n"
            "-  const q = escapeHtml(req.query.q);\n"
            "+  const q = req.query.q.replace(/[<>]/g, '');\n"
            "   res.send(`<div>${q}</div>`);\n"
            " });\n"
            "```"
        ),
        "output": (
            "🟠 MAJOR: stripping only `<`/`>` is a fragile XSS defense - encodings and attribute "
            "contexts still escape. Use a proper output-encoding helper (`escapeHtml` or the "
            "template engine's escaping) so `q` can't break out of context."
        ),
    },
    {
        "id": "SEC_AUDIT_020", "language": "python", "framework": "general",
        "severity": "🟠 MAJOR",
        "instruction": (
            "Review this diff:\n\n"
            "```diff\n"
            "@@ -1,4 +1,4 @@\n"
            " def fetch_avatar(url):\n"
            "-    parsed = urlparse(url)\n"
            "-    if parsed.scheme not in ('http', 'https'): raise ValueError()\n"
            "+    res = requests.get(url, timeout=5)\n"
            "     return res.content\n"
            "```"
        ),
        "output": (
            "🟠 MAJOR: the scheme/domain validation was removed - `url` now reaches "
            "`requests.get` unchecked, re-enabling SSRF against internal metadata/loopback. "
            "Re-add the scheme + hostname allowlist and reject private ranges."
        ),
    },
]

def generate_security_audit_samples() -> list:
    """Return the security-audit PR-diff + review-comment pairs as plain dicts.

    Each entry has an `instruction` (the vulnerable diff) and an `output`
    (a severity-tagged review comment with a concrete fix), so callers can
    write it straight to a training JSONL without mutation.
    """
    return [dict(s) for s in SECURITY_SAMPLES]


def append_additional_pairs(output_path: str) -> int:
    """Append ADDITIONAL_PAIRS to the existing code-review set, skipping any
    id already present so the script stays idempotent on re-runs."""
    # Load existing ids (if the file exists)
    existing_ids = set()
    _existing_lines = []
    if Path(output_path).exists():
        with open(output_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                _existing_lines.append(line)
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict) and item.get("id"):
                    existing_ids.add(item["id"])

    added = 0
    for pair in ADDITIONAL_PAIRS:
        if pair["id"] in existing_ids:
            continue
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(pair) + "\n")
        existing_ids.add(pair["id"])
        added += 1

    new_total = len(_existing_lines) + added
    print(f"Code-review additions: appended {added} new (skipped duplicates). "
          f"Total now: {new_total}")
    return added


def main() -> None:
    # 1) Preserve existing behavior: append the classic 4-cell pairs.
    append_additional_pairs("data/train_code_review.jsonl")

    # 2) New: write the security-audit sub-lane (PR-diff + review-comment pairs).
    out_dir = Path(__file__).resolve().parent.parent / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "training-data-code-review-security.jsonl"

    samples = generate_security_audit_samples()
    with open(out_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"Security-audit sub-lane: {len(samples)} samples -> {out_path}")
    by_sev = {}
    for s in samples:
        by_sev[s["severity"]] = by_sev.get(s["severity"], 0) + 1
    print(f"By severity: {by_sev}")


if __name__ == "__main__":
    main()


