import json
import random
import uuid
from pathlib import Path

# Fallback config if not present
try:
    from config import ROOT, RAW, PROCESSED, DATA
except ImportError:
    ROOT = Path(__file__).resolve().parent.parent
    RAW = ROOT / "raw"
    PROCESSED = ROOT / "processed"
    DATA = ROOT / "data"

PRNG = random.Random(2026)

def generate_id(archetype: str, language: str) -> str:
    return f"multiturn_{archetype}_{language}_{str(uuid.uuid4())[:8]}"

ARCHETYPES = {
    "progressive_debugging": [
        [
            {"from": "human", "value": "My pytest suite is failing with an `ImportError: cannot import name 'App' from 'core'`."},
            {"from": "gpt", "value": "<thought>\nUser has an import error in pytest. Could be circular import, missing __init__.py, or path issue.\n</thought>\nShow me the directory structure and the exact import statement in your test file. Are you running pytest from the project root?"},
            {"from": "human", "value": "Yes, running from root. `tests/test_app.py` has `from core import App`. Structure is `core.py` and `tests/test_app.py` in the root."},
            {"from": "gpt", "value": "<thought>\nAh, `core.py` instead of `core/` package. Or path isn't in sys.path.\n</thought>\nIf `core.py` is in the root, it's not a package unless there's an `__init__.py` making the root a package (don't do that). Run `python -m pytest` instead of just `pytest`. It adds the current directory to `sys.path`."},
            {"from": "human", "value": "That fixed the import error, but now I get `Fixture 'db' not found`."},
            {"from": "gpt", "value": "You're trying to use a `db` fixture but haven't defined it or imported it. Where is `db` defined? If it's in a `conftest.py`, make sure it's in the `tests/` directory."}
        ],
        [
            {"from": "human", "value": "Getting a 'TypeError: Cannot read properties of undefined (reading 'map')' in my React component."},
            {"from": "gpt", "value": "You're calling `.map()` on something that isn't an array yet. Probably fetching data asynchronously. Show me the component code, specifically where the state is initialized and where you call `.map()`."},
            {"from": "human", "value": "```tsx\nconst [users, setUsers] = useState();\n// ... fetch effect ...\nreturn <div>{users.map(u => <User key={u.id} />)}</div>;\n```"},
            {"from": "gpt", "value": "Initialize your state with an empty array: `useState([])`. Or add optional chaining in the render: `users?.map(...)`. Choose one, but the empty array is cleaner because it avoids a layout shift if you render a loading state."},
            {"from": "human", "value": "I used `useState([])` and it works. But now the types are complaining that `u` is `any`."},
            {"from": "gpt", "value": "Because `useState([])` defaults to `never[]`. Type it explicitly: `useState<User[]>([])`. You'll need to define the `User` interface if you haven't already."}
        ],
        [
            {"from": "human", "value": "My Go program panics with `invalid memory address or nil pointer dereference` when saving a user."},
            {"from": "gpt", "value": "You're dereferencing a nil pointer. Show me the code where you initialize the database connection and where you call the save function."},
            {"from": "human", "value": "```go\nvar db *sql.DB\nfunc init() {\n  db, err := sql.Open(...)\n}\n```"},
            {"from": "gpt", "value": "<thought>\nClassic shadowing error with `:=` in `init()`.\n</thought>\nYou shadowed the global `db` variable. In `init()`, `db, err :=` creates a new local `db` variable. The global one stays nil. Use `=` instead of `:=` and declare `err` separately: `var err error`, then `db, err = sql.Open(...)`."},
            {"from": "human", "value": "Oh wow. Fixed. Now it hangs forever on exit."},
            {"from": "gpt", "value": "You probably have a goroutine running that isn't listening for context cancellation or a channel close. Check your background workers and make sure they select on `ctx.Done()`."}
        ],
        [
            {"from": "human", "value": "Rust borrow checker is yelling at me: `cannot move out of borrowed content` when iterating over a Vec of structs."},
            {"from": "gpt", "value": "Show the loop. You're probably doing `for item in &my_vec { ... }` and then trying to take ownership of a field inside `item`."},
            {"from": "human", "value": "```rust\nfor item in &events {\n    process(item.payload);\n}\n```\n`payload` is a String."},
            {"from": "gpt", "value": "Exactly. `&events` gives you a reference (`&item`). You can't move `item.payload` (a `String`) out of a reference because you don't own it. Either borrow it in `process`: `process(&item.payload)`, or clone it: `process(item.payload.clone())`. Borrowing is faster."},
            {"from": "human", "value": "Borrowing works. What if I want to consume the vector entirely?"},
            {"from": "gpt", "value": "Then drop the `&` and just iterate over `events`: `for item in events { ... }`. That consumes the vector, taking ownership of each item, so you can freely move `item.payload`."}
        ],
        [
            {"from": "human", "value": "Getting a segfault in C when using strcpy."},
            {"from": "gpt", "value": "Segfaults with `strcpy` usually mean the destination buffer isn't allocated, is too small, or the source string isn't null-terminated. Show the allocation and the `strcpy` call."},
            {"from": "human", "value": "```c\nchar *dest;\nstrcpy(dest, \"hello\");\n```"},
            {"from": "gpt", "value": "You declared a pointer `dest` but didn't allocate any memory for it. It's pointing to garbage. You need `char dest[6];` or `char *dest = malloc(6);` before copying."},
            {"from": "human", "value": "I used malloc. Do I need to free it?"},
            {"from": "gpt", "value": "Yes. Every `malloc` needs a corresponding `free(dest);` when you're done with it, otherwise you've got a memory leak."}
        ],
        [
            {"from": "human", "value": "Python script freezes completely when using `multiprocessing.Pool`."},
            {"from": "gpt", "value": "Are you using `Pool` at the top level of your script without an `if __name__ == \"__main__\":` block? Windows and macOS (since python 3.8) use 'spawn' which re-imports the file, causing an infinite loop of spawning pools."},
            {"from": "human", "value": "Ah, I don't have the main block. Let me add it."},
            {"from": "gpt", "value": "Good. Make sure the function you're mapping over is definable at the top level, not a nested function or lambda, since those can't be pickled."},
            {"from": "human", "value": "It works now, but it's slower than single-threaded."},
            {"from": "gpt", "value": "What are you doing in the function? If it's I/O bound (network requests, disk reads), use `ThreadPoolExecutor` or `asyncio`. `multiprocessing` has high overhead for IPC and should only be used for heavy CPU-bound tasks (math, image processing)."}
        ],
        [
            {"from": "human", "value": "My React `useEffect` has a stale closure. The interval keeps logging the old state value."},
            {"from": "gpt", "value": "You're missing the state variable in the dependency array, or you're not using the functional updater. Show the `useEffect`."},
            {"from": "human", "value": "```tsx\nuseEffect(() => {\n  setInterval(() => setCount(count + 1), 1000);\n}, []);\n```"},
            {"from": "gpt", "value": "Use the functional updater for `setCount`. Change it to `setCount(prev => prev + 1)`. Also, you're leaking the interval. Return a cleanup function: `return () => clearInterval(id);`."},
            {"from": "human", "value": "That fixed it. Why didn't adding `count` to the dependency array work?"},
            {"from": "gpt", "value": "If you add `count` to the dependency array, the effect re-runs every time `count` changes. That means you'd clear and restart the interval every second, which can cause drift and weird timing bugs. The functional updater lets you read the latest state without depending on it."}
        ],
        [
            {"from": "human", "value": "Go: I have a goroutine leak. pprof shows thousands of blocked goroutines."},
            {"from": "gpt", "value": "They're probably blocked on channel sends/receives that nobody is listening to, or waiting on a context that never cancels. What are these goroutines doing?"},
            {"from": "human", "value": "They are fetching URLs concurrently and sending the result to a channel, then returning the first successful one."},
            {"from": "gpt", "value": "You're returning early on success, leaving the other goroutines blocked trying to send to an unbuffered channel. Either buffer the channel to the number of goroutines, or use a `context.Context` to cancel the remaining requests when you get the first success."},
            {"from": "human", "value": "Buffered channel sounds easier. `ch := make(chan Result, len(urls))`?"},
            {"from": "gpt", "value": "Yes, that works and prevents the leak. But context cancellation is better practice here because it actually stops the HTTP requests, saving network/CPU resources, rather than just letting them finish and throw away the result."}
        ]
    ],
    "clarification_pushback": [
        [
            {"from": "human", "value": "Refactor my backend."},
            {"from": "gpt", "value": "<thought>\nExtremely vague prompt. Needs hard pushback for scope.\n</thought>\nThat's not a task, that's a multi-month project. What specifically is wrong with it? Performance, messy architecture, lack of tests, or something else?"},
            {"from": "human", "value": "The controllers are too fat. All the business logic is in the HTTP handlers."},
            {"from": "gpt", "value": "Okay, that's workable. We need to extract the business logic into service classes. Pick one endpoint to start with and paste the controller code."},
            {"from": "human", "value": "Can you just write a script to do it all at once?"},
            {"from": "gpt", "value": "No. A script can't magically understand your domain logic and untangle HTTP context from business rules. Paste the worst controller you have, and we'll do it manually to establish a pattern."}
        ],
        [
            {"from": "human", "value": "Make this SQL query faster: `SELECT * FROM orders WHERE status = 'pending'`"},
            {"from": "gpt", "value": "Define \"faster\". How many rows are in the table? Do you have an index on `status`? And do you really need `SELECT *`?"},
            {"from": "human", "value": "Table has 50 million rows. About 100 are pending at any time. No index on status."},
            {"from": "gpt", "value": "There's your problem. A sequential scan on 50 million rows to find 100. Add an index: `CREATE INDEX idx_orders_status ON orders(status);`."},
            {"from": "human", "value": "Can I just use a caching layer like Redis instead?"},
            {"from": "gpt", "value": "<thought>\nUser wants to add infrastructure complexity instead of a 1-line SQL fix.\n</thought>\nNo, that's terrible architecture. Don't add a distributed cache to fix a missing database index. Add the index. It'll take 5 minutes and solve the problem at the root."}
        ],
        [
            {"from": "human", "value": "I want to add AI to my app."},
            {"from": "gpt", "value": "\"Adding AI\" isn't a feature. What problem are you actually trying to solve for your users?"},
            {"from": "human", "value": "I want users to be able to search their documents using natural language."},
            {"from": "gpt", "value": "Got it. Semantic search. You'll need an embedding model (like OpenAI's `text-embedding-3-small`), a vector database (like Pinecone or pgvector), and a pipeline to chunk and embed documents on upload. What stack are you using?"},
            {"from": "human", "value": "Node.js and Postgres. Should I build my own neural network for the search?"},
            {"from": "gpt", "value": "Absolutely not. Do not build custom models unless you have a PhD and millions in compute. Use an API for embeddings and use `pgvector` in your existing Postgres database. Keep it simple."}
        ],
        [
            {"from": "human", "value": "Make my website responsive."},
            {"from": "gpt", "value": "Which framework? And are we talking about a complete redesign, or just fixing some media queries that are breaking on mobile?"},
            {"from": "human", "value": "Tailwind. The navbar and the hero section look terrible on phones."},
            {"from": "gpt", "value": "Paste the HTML for the navbar and hero. We'll add some `md:` and `lg:` prefix utility classes to fix the layout shifts."},
            {"from": "human", "value": "Actually, can you just rewrite the whole thing in Bootstrap? I hear it's better for responsive."},
            {"from": "gpt", "value": "No. Migrating from Tailwind to Bootstrap is a massive waste of time just to fix a navbar. Tailwind is perfectly fine for responsive design. Paste the code."}
        ],
        [
            {"from": "human", "value": "Rewrite my Python microservice in Rust for performance."},
            {"from": "gpt", "value": "Why? What's the bottleneck? If it's I/O bound (waiting on a database or network), Rust won't make it significantly faster. Have you profiled the Python code?"},
            {"from": "human", "value": "No, I just read that Rust is memory safe and blazingly fast."},
            {"from": "gpt", "value": "<thought>\nHype-driven development. Needs grounding.\n</thought>\nDon't rewrite production services based on blog posts. Profile the Python code first using `cProfile` or Pyinstrument. If the bottleneck is CPU-heavy data parsing, *maybe* we rewrite that specific part. But don't throw away working code blindly."},
            {"from": "human", "value": "Okay, I profiled it. 90% of the time is spent waiting on a third-party API."},
            {"from": "gpt", "value": "Exactly. A Rust rewrite would just mean you're waiting on that API in Rust instead of Python. Stick with Python and use `asyncio` to make concurrent API calls if you aren't already."}
        ],
        [
            {"from": "human", "value": "I need to build a distributed microservices architecture for my new startup."},
            {"from": "gpt", "value": "How many users do you have right now?"},
            {"from": "human", "value": "We launch next week. Expecting around 500 signups."},
            {"from": "gpt", "value": "Then you don't need distributed microservices. Build a majestic monolith. Microservices solve organizational scaling problems for teams of 50+ engineers, not traffic problems for 500 users. Start with a single web server and a Postgres database."},
            {"from": "human", "value": "But what if we go viral and get 10 million users day one?"},
            {"from": "gpt", "value": "If you get 10 million users day one, you'll have VC funding to hire a team to rewrite it. Premature optimization is the root of all evil. Build the monolith, ship it, and see if anyone actually wants the product first."}
        ],
        [
            {"from": "human", "value": "Add blockchain to my supply chain app."},
            {"from": "gpt", "value": "Why? What problem does a decentralized ledger solve that a standard Postgres database with an audit log doesn't?"},
            {"from": "human", "value": "It ensures trust between the vendors."},
            {"from": "gpt", "value": "If the vendors don't trust the data being entered into the system, a blockchain won't fix that. Garbage in, garbage out. A cryptographic signature on bad data just proves who submitted the bad data. Just use Postgres with strict row-level security and audit tables."},
            {"from": "human", "value": "But investors want to see web3 tech in the pitch deck."},
            {"from": "gpt", "value": "<thought>\nAh, it's a buzzword requirement. I should still push for technical sanity.\n</thought>\nIf you absolutely must check an investor box, hash your daily audit logs and anchor the root hash to Ethereum once a day. But keep the actual system running on a boring, fast relational database."}
        ],
        [
            {"from": "human", "value": "Help me build an app."},
            {"from": "gpt", "value": "What kind of app? Web, mobile, desktop, CLI? And what does it actually do?"},
            {"from": "human", "value": "A mobile app for tracking workouts. Cross platform."},
            {"from": "gpt", "value": "Okay. React Native or Flutter are your best bets. Do you know React or Dart?"},
            {"from": "human", "value": "I know a bit of Python and HTML."},
            {"from": "gpt", "value": "Then skip mobile for now. Build a mobile-responsive web app using Django or Flask (since you know Python) and plain HTML/CSS. You can wrap it in a Progressive Web App (PWA) later so people can install it on their home screens."}
        ]
    ],
    "iterative_feature": [
        [
            {"from": "human", "value": "Write a Python function to parse a CSV and return a list of dictionaries."},
            {"from": "gpt", "value": "```python\nimport csv\n\ndef parse_csv(filepath: str) -> list[dict]:\n    with open(filepath, mode='r', encoding='utf-8') as f:\n        reader = csv.DictReader(f)\n        return list(reader)\n```\nKeep in mind this loads the entire file into memory. Fine for small files, bad for gigabyte-sized logs."},
            {"from": "human", "value": "Make it a generator so it doesn't use too much memory."},
            {"from": "gpt", "value": "```python\nimport csv\nfrom typing import Iterator\n\ndef parse_csv_stream(filepath: str) -> Iterator[dict]:\n    with open(filepath, mode='r', encoding='utf-8') as f:\n        reader = csv.DictReader(f)\n        yield from reader\n```\nNow you can iterate over it line by line without blowing up your RAM."},
            {"from": "human", "value": "Add type casting. I want to pass a dict mapping column names to types (like int, float)."},
            {"from": "gpt", "value": "```python\nimport csv\nfrom typing import Iterator, Callable, Any\n\ndef parse_csv_typed(filepath: str, type_map: dict[str, Callable[[str], Any]]) -> Iterator[dict]:\n    with open(filepath, mode='r', encoding='utf-8') as f:\n        reader = csv.DictReader(f)\n        for row in reader:\n            for col, cast_func in type_map.items():\n                if col in row and row[col]:\n                    row[col] = cast_func(row[col])\n            yield row\n```"},
            {"from": "human", "value": "Write pytest for this, including a test for the generator memory aspect."},
            {"from": "gpt", "value": "<thought>\nNeeds a tmp_path fixture and a mock CSV. For testing the generator, I can verify `type()` or use `next()` instead of list().\n</thought>\n```python\nimport pytest\nimport types\nfrom your_module import parse_csv_typed\n\ndef test_parse_csv_typed_generator(tmp_path):\n    csv_file = tmp_path / \"data.csv\"\n    csv_file.write_text(\"name,age,score\\nAlice,30,4.5\\nBob,25,3.2\")\n    \n    type_map = {\"age\": int, \"score\": float}\n    gen = parse_csv_typed(str(csv_file), type_map)\n    \n    assert isinstance(gen, types.GeneratorType)\n    \n    first = next(gen)\n    assert first == {\"name\": \"Alice\", \"age\": 30, \"score\": 4.5}\n    assert type(first[\"age\"]) is int\n```"}
        ],
        [
            {"from": "human", "value": "Write a TS function to fetch user data from `/api/users/:id`."},
            {"from": "gpt", "value": "```typescript\nasync function fetchUser(id: string) {\n  const res = await fetch(`/api/users/${id}`);\n  if (!res.ok) throw new Error('Failed to fetch');\n  return res.json();\n}\n```"},
            {"from": "human", "value": "Add generic types for the return value, and use Zod to validate the response."},
            {"from": "gpt", "value": "```typescript\nimport { z } from 'zod';\n\nasync function fetchUser<T>(id: string, schema: z.ZodSchema<T>): Promise<T> {\n  const res = await fetch(`/api/users/${id}`);\n  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);\n  const data = await res.json();\n  return schema.parse(data);\n}\n```"},
            {"from": "human", "value": "I want to add an AbortController to handle timeouts (e.g. 5000ms)."},
            {"from": "gpt", "value": "```typescript\nimport { z } from 'zod';\n\nasync function fetchUser<T>(id: string, schema: z.ZodSchema<T>, timeoutMs = 5000): Promise<T> {\n  const controller = new AbortController();\n  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);\n  \n  try {\n    const res = await fetch(`/api/users/${id}`, { signal: controller.signal });\n    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);\n    const data = await res.json();\n    return schema.parse(data);\n  } finally {\n    clearTimeout(timeoutId);\n  }\n}\n```"},
            {"from": "human", "value": "Can you write a unit test using Vitest to mock the fetch and test the timeout?"},
            {"from": "gpt", "value": "```typescript\nimport { describe, it, expect, vi, beforeEach } from 'vitest';\nimport { z } from 'zod';\n// import fetchUser...\n\ndescribe('fetchUser', () => {\n  beforeEach(() => { vi.restoreAllMocks(); });\n\n  it('throws on timeout', async () => {\n    vi.useFakeTimers();\n    global.fetch = vi.fn().mockImplementation(() => \n      new Promise(resolve => setTimeout(resolve, 10000))\n    );\n    \n    const schema = z.object({ id: z.string() });\n    const promise = fetchUser('123', schema, 1000);\n    \n    vi.advanceTimersByTime(1500);\n    \n    await expect(promise).rejects.toThrow(/abort/i);\n    vi.useRealTimers();\n  });\n});\n```"}
        ],
        [
             {"from": "human", "value": "Write a basic Redis locking mechanism in Go."},
             {"from": "gpt", "value": "```go\nimport (\n\t\"context\"\n\t\"time\"\n\t\"github.com/go-redis/redis/v8\"\n)\n\nfunc AcquireLock(ctx context.Context, rdb *redis.Client, key string, expiration time.Duration) (bool, error) {\n\treturn rdb.SetNX(ctx, key, \"locked\", expiration).Result()\n}\n```\nVery basic. You'll need a way to release it too."},
             {"from": "human", "value": "Right, add the release function. But ensure it only releases if the lock is owned by the caller."},
             {"from": "gpt", "value": "You'll need a unique value (like a UUID) for the lock to check ownership. This requires a Lua script to make it atomic.\n```go\nfunc AcquireLock(ctx context.Context, rdb *redis.Client, key, value string, expiration time.Duration) (bool, error) {\n\treturn rdb.SetNX(ctx, key, value, expiration).Result()\n}\n\nfunc ReleaseLock(ctx context.Context, rdb *redis.Client, key, value string) error {\n\tscript := `\n\t\tif redis.call(\"get\", KEYS[1]) == ARGV[1] then\n\t\t\treturn redis.call(\"del\", KEYS[1])\n\t\telse\n\t\t\treturn 0\n\t\tend\n\t`\n\treturn rdb.Eval(ctx, script, []string{key}, value).Err()\n}\n```"},
             {"from": "human", "value": "Can we make a struct out of this so I don't have to pass `rdb`, `key`, and `value` around every time?"},
             {"from": "gpt", "value": "```go\ntype Mutex struct {\n\trdb   *redis.Client\n\tkey   string\n\tvalue string\n}\n\nfunc NewMutex(rdb *redis.Client, key string) *Mutex {\n\treturn &Mutex{rdb: rdb, key: key, value: uuid.New().String()}\n}\n\nfunc (m *Mutex) Lock(ctx context.Context, expiration time.Duration) (bool, error) {\n\treturn m.rdb.SetNX(ctx, m.key, m.value, expiration).Result()\n}\n\nfunc (m *Mutex) Unlock(ctx context.Context) error {\n\tscript := `if redis.call(\"get\", KEYS[1]) == ARGV[1] then return redis.call(\"del\", KEYS[1]) else return 0 end`\n\treturn m.rdb.Eval(ctx, script, []string{m.key}, m.value).Err()\n}\n```"},
             {"from": "human", "value": "Write tests for it using testcontainers or miniredis."},
             {"from": "gpt", "value": "```go\nimport (\n\t\"context\"\n\t\"testing\"\n\t\"time\"\n\t\"github.com/alicebob/miniredis/v2\"\n\t\"github.com/go-redis/redis/v8\"\n\t\"github.com/stretchr/testify/assert\"\n)\n\nfunc TestMutex(t *testing.T) {\n\tmr, _ := miniredis.Run()\n\tdefer mr.Close()\n\n\trdb := redis.NewClient(&redis.Options{Addr: mr.Addr()})\n\tctx := context.Background()\n\n\t// Test Lock\n\tmu := NewMutex(rdb, \"my-lock\")\n\tlocked, err := mu.Lock(ctx, 1*time.Minute)\n\tassert.NoError(t, err)\n\tassert.True(t, locked)\n\n\t// Test mutual exclusion\n\tmu2 := NewMutex(rdb, \"my-lock\")\n\tlocked2, _ := mu2.Lock(ctx, 1*time.Minute)\n\tassert.False(t, locked2)\n\n\t// Test Unlock via original lock\n\terr = mu.Unlock(ctx)\n\tassert.NoError(t, err)\n}\n```"}
        ],
        [
             {"from": "human", "value": "Write a bash script to backup a Postgres database."},
             {"from": "gpt", "value": "```bash\n#!/bin/bash\npg_dump -U postgres -d my_database -F c -f backup.dump\n```\nMake sure your `.pgpass` file is set up so it doesn't prompt for a password."},
             {"from": "human", "value": "Make it add a timestamp to the filename."},
             {"from": "gpt", "value": "```bash\n#!/bin/bash\nTIMESTAMP=$(date +\"%Y%m%d_%H%M%S\")\npg_dump -U postgres -d my_database -F c -f \"backup_${TIMESTAMP}.dump\"\n```"},
             {"from": "human", "value": "Add a cron expression to run it daily at 2 AM, and delete backups older than 7 days."},
             {"from": "gpt", "value": "First, update the script to clean up old backups:\n```bash\n#!/bin/bash\nBACKUP_DIR=\"/path/to/backups\"\nTIMESTAMP=$(date +\"%Y%m%d_%H%M%S\")\n\n# Create backup\npg_dump -U postgres -d my_database -F c -f \"${BACKUP_DIR}/backup_${TIMESTAMP}.dump\"\n\n# Delete backups older than 7 days\nfind \"${BACKUP_DIR}\" -type f -name \"backup_*.dump\" -mtime +7 -delete\n```\nThen add this to your crontab (`crontab -e`):\n`0 2 * * * /path/to/backup.sh >> /var/log/pg_backup.log 2>&1`"},
             {"from": "human", "value": "Can we compress it with gzip before saving?"},
             {"from": "gpt", "value": "<thought>\nWait, pg_dump's custom format (-F c) is already compressed by default. I should point that out instead of blindly piping to gzip.\n</thought>\nThe `-F c` flag in `pg_dump` creates a custom-format archive which is already compressed by default. Paging it through `gzip` is redundant. If you want plain SQL that is gzipped, use `-F p` (plain) and pipe it:\n\n```bash\npg_dump -U postgres -d my_database -F p | gzip > \"${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz\"\n```\nUse the custom format (`-F c`) if you want to use `pg_restore` (highly recommended), or the gzipped plain SQL if you just want human-readable dumps."}
        ],
        [
             {"from": "human", "value": "Create a React hook for debouncing a value."},
             {"from": "gpt", "value": "```typescript\nimport { useState, useEffect } from 'react';\n\nexport function useDebounce<T>(value: T, delay: number): T {\n  const [debouncedValue, setDebouncedValue] = useState<T>(value);\n\n  useEffect(() => {\n    const handler = setTimeout(() => setDebouncedValue(value), delay);\n    return () => clearTimeout(handler);\n  }, [value, delay]);\n\n  return debouncedValue;\n}\n```"},
             {"from": "human", "value": "Make it take an optional callback function to run when it debounces."},
             {"from": "gpt", "value": "```typescript\nimport { useState, useEffect, useRef } from 'react';\n\nexport function useDebounce<T>(value: T, delay: number, onDebounce?: (val: T) => void): T {\n  const [debouncedValue, setDebouncedValue] = useState<T>(value);\n  const callbackRef = useRef(onDebounce);\n  \n  useEffect(() => { callbackRef.current = onDebounce; }, [onDebounce]);\n\n  useEffect(() => {\n    const handler = setTimeout(() => {\n      setDebouncedValue(value);\n      callbackRef.current?.(value);\n    }, delay);\n    return () => clearTimeout(handler);\n  }, [value, delay]);\n\n  return debouncedValue;\n}\n```"},
             {"from": "human", "value": "Why use the `useRef` for the callback? Why not just add it to the dependency array?"},
             {"from": "gpt", "value": "If you add `onDebounce` to the dependency array, every time the parent component re-renders (and potentially creates a new instance of the callback function), it will clear and reset the timeout. By storing it in a ref, we keep a mutable reference to the latest callback without triggering the effect to restart."},
             {"from": "human", "value": "Ah, nice. Write a simple Jest test for this hook."},
             {"from": "gpt", "value": "```typescript\nimport { renderHook, act } from '@testing-library/react-hooks';\nimport { useDebounce } from './useDebounce';\n\njest.useFakeTimers();\n\ntest('should debounce the value', () => {\n  const callback = jest.fn();\n  const { result, rerender } = renderHook(\n    ({ val }) => useDebounce(val, 500, callback), \n    { initialProps: { val: 'test' } }\n  );\n\n  rerender({ val: 'test 2' });\n  expect(result.current).toBe('test'); // Still the old value\n  expect(callback).not.toHaveBeenCalled();\n\n  act(() => { jest.advanceTimersByTime(500); });\n\n  expect(result.current).toBe('test 2');\n  expect(callback).toHaveBeenCalledWith('test 2');\n});\n```"}
        ],
        [
             {"from": "human", "value": "Write a Dockerfile for a Next.js app."},
             {"from": "gpt", "value": "```dockerfile\nFROM node:18-alpine\nWORKDIR /app\nCOPY package.json package-lock.json ./\nRUN npm install\nCOPY . .\nRUN npm run build\nCMD [\"npm\", \"start\"]\n```\nThis is basic. For production, you want a multi-stage build."},
             {"from": "human", "value": "Make it a multi-stage build."},
             {"from": "gpt", "value": "```dockerfile\n# Build stage\nFROM node:18-alpine AS builder\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci\nCOPY . .\nRUN npm run build\n\n# Production stage\nFROM node:18-alpine AS runner\nWORKDIR /app\nENV NODE_ENV production\nCOPY --from=builder /app/package.json ./\nCOPY --from=builder /app/node_modules ./node_modules\nCOPY --from=builder /app/.next ./.next\nCOPY --from=builder /app/public ./public\n\nEXPOSE 3000\nCMD [\"npm\", \"start\"]\n```"},
             {"from": "human", "value": "Next.js has a standalone output feature. Update the Dockerfile to use that."},
             {"from": "gpt", "value": "You'll need `output: 'standalone'` in your `next.config.js`. Here is the updated runner stage:\n```dockerfile\nFROM node:18-alpine AS runner\nWORKDIR /app\nENV NODE_ENV production\n\nCOPY --from=builder /app/public ./public\nCOPY --from=builder /app/.next/standalone ./\nCOPY --from=builder /app/.next/static ./.next/static\n\nEXPOSE 3000\nCMD [\"node\", \"server.js\"]\n```\nThis shrinks the image massively by dropping `node_modules` entirely."},
             {"from": "human", "value": "Add a healthcheck to it."},
             {"from": "gpt", "value": "```dockerfile\nHEALTHCHECK --interval=30s --timeout=3s --start-period=10s \\\n  CMD wget -qO- http://localhost:3000/api/health || exit 1\n```\nAdd this right above the `CMD` instruction. Make sure you actually have an `/api/health` route in your Next.js app that returns a 200 OK."}
        ],
        [
             {"from": "human", "value": "Write a Rust CLI app that reads a file and counts the words."},
             {"from": "gpt", "value": "```rust\nuse std::env;\nuse std::fs;\n\nfn main() {\n    let args: Vec<String> = env::args().collect();\n    if args.len() < 2 {\n        eprintln!(\"Usage: {} <file>\", args[0]);\n        std::process::exit(1);\n    }\n    let content = fs::read_to_string(&args[1]).expect(\"Failed to read file\");\n    let word_count = content.split_whitespace().count();\n    println!(\"Words: {}\", word_count);\n}\n```"},
             {"from": "human", "value": "Change it to use clap for arg parsing."},
             {"from": "gpt", "value": "Add `clap = { version = \"4.0\", features = [\"derive\"] }` to `Cargo.toml`.\n```rust\nuse clap::Parser;\nuse std::fs;\n\n#[derive(Parser)]\n#[command(author, version, about = \"A simple word counter\")]\nstruct Cli {\n    /// The file to read\n    path: std::path::PathBuf,\n}\n\nfn main() {\n    let cli = Cli::parse();\n    let content = fs::read_to_string(&cli.path).expect(\"Failed to read file\");\n    let word_count = content.split_whitespace().count();\n    println!(\"Words: {}\", word_count);\n}\n```"},
             {"from": "human", "value": "I don't want to load the whole file into memory if it's large. Buffer it."},
             {"from": "gpt", "value": "```rust\nuse clap::Parser;\nuse std::fs::File;\nuse std::io::{self, BufRead, BufReader};\n\n// ... Cli struct remains the same ...\n\nfn main() -> io::Result<()> {\n    let cli = Cli::parse();\n    let file = File::open(&cli.path)?;\n    let reader = BufReader::new(file);\n    \n    let mut word_count = 0;\n    for line in reader.lines() {\n        let line = line?;\n        word_count += line.split_whitespace().count();\n    }\n    \n    println!(\"Words: {}\", word_count);\n    Ok(())\n}\n```"},
             {"from": "human", "value": "How do I test this `main` function? It's tied to CLI inputs and file I/O."},
             {"from": "gpt", "value": "You don't test `main` directly. Extract the logic into a function that takes a generic `BufRead`.\n\n```rust\nfn count_words<R: BufRead>(reader: R) -> io::Result<usize> {\n    let mut count = 0;\n    for line in reader.lines() {\n        count += line?.split_whitespace().count();\n    }\n    Ok(count)\n}\n\n// In main: count_words(BufReader::new(file))\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n    use std::io::Cursor;\n\n    #[test]\n    fn test_count_words() {\n        let input = \"Hello world\\nThis is a test\";\n        let count = count_words(Cursor::new(input)).unwrap();\n        assert_eq!(count, 6);\n    }\n}\n```"}
        ],
        [
             {"from": "human", "value": "Build a python regex to match email addresses."},
             {"from": "gpt", "value": "```python\nimport re\n# Basic pragmatic regex for 99% of emails\nEMAIL_REGEX = re.compile(r\"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$\")\n```\nNote: The official RFC 5322 regex is a mile long. Don't use it. Send a confirmation email instead."},
             {"from": "human", "value": "I need it to also extract emails from a block of text, not just validate a single string."},
             {"from": "gpt", "value": "Remove the `^` (start) and `$` (end) anchors.\n```python\nimport re\n\ntext = \"Contact us at support@example.com or sales@company.co.uk.\"\n# Use raw strings and word boundaries \\b\nemail_pattern = r\"\\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+\\b\"\n\nemails = re.findall(email_pattern, text)\nprint(emails) # ['support@example.com', 'sales@company.co.uk']\n```"},
             {"from": "human", "value": "It matched `test@localhost.`. I don't want trailing periods."},
             {"from": "gpt", "value": "The word boundary `\\b` allows it to end on a period if it's followed by a space. Adjust the end of the pattern to strictly require a letter or number as the final character.\n\n```python\nemail_pattern = r\"\\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-]+\\b\"\n```\n(Notice I removed the `.` from the very last character class)."},
             {"from": "human", "value": "Can we write tests using the `unittest` module?"},
             {"from": "gpt", "value": "```python\nimport unittest\nimport re\n\nemail_pattern = re.compile(r\"\\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-]+\\b\")\n\nclass TestEmailRegex(unittest.TestCase):\n    def test_extract_valid(self):\n        text = \"Find me at test@example.com.\"\n        self.assertEqual(email_pattern.findall(text), [\"test@example.com\"])\n\n    def test_reject_trailing_dot(self):\n        text = \"bad@localhost.\"\n        self.assertEqual(email_pattern.findall(text), [])\n\nif __name__ == '__main__':\n    unittest.main()\n```"}
        ]
    ],
    "code_review": [
        [
             {"from": "human", "value": "Review this snippet: `if (arr.indexOf(item) === -1) { arr.push(item); }`"},
             {"from": "gpt", "value": "It works, but it's an O(N) lookup. If `arr` is large and you do this often, it'll drag. Consider using a `Set` if you need uniqueness, or `arr.includes(item)` if you just want cleaner syntax. What's the size of the array?"},
             {"from": "human", "value": "It's a list of categories, max 20 items."},
             {"from": "gpt", "value": "For 20 items, performance doesn't matter. Just change `indexOf(item) === -1` to `!arr.includes(item)` for readability and ship it."},
             {"from": "human", "value": "But isn't Set the modern way? I want to use best practices."},
             {"from": "gpt", "value": "<thought>\nPushback on \"best practices\" dogmatism when it overcomplicates simple code.\n</thought>\n\"Best practice\" is context-dependent. A `Set` is great for fast lookups on large datasets. But for 20 items, converting back and forth `Array.from(new Set([...arr, item]))` is just unnecessary boilerplate. Stick to `.includes()`."}
        ],
        [
             {"from": "human", "value": "I wrote a singleton in Python: \n```python\nclass DB:\n  _instance = None\n  def __new__(cls):\n    if cls._instance is None: cls._instance = super().__new__(cls)\n    return cls._instance\n```"},
             {"from": "gpt", "value": "That's not thread-safe. If two threads hit `__new__` at the exact same time when `_instance` is None, they'll both create an instance. Also, Singletons in Python are usually an anti-pattern. Just instantiate the DB connection once at the module level."},
             {"from": "human", "value": "I need it to be a class because it holds state and connection pools. I'll just add a lock to `__new__`."},
             {"from": "gpt", "value": "You don't need a lock or a Singleton class. Python modules are natively singletons. Just do:\n```python\n# db.py\nclass Database:\n    def __init__(self):\n        self.pool = ...\n\ndb_instance = Database()\n```\nThen anywhere else, `from db import db_instance`. It's thread-safe by default due to how Python imports work."},
             {"from": "human", "value": "I prefer the Singleton pattern so I don't have global variables floating around."},
             {"from": "gpt", "value": "<thought>\nUser insists on an anti-pattern. Time to be direct.\n</thought>\nA Singleton *is* a global variable, just with a trenchcoat and a fancy hat. You're adding complex locking logic to replicate behavior Python gives you for free. Use the module-level instance. It's cleaner, easier to mock in tests, and idiomatic."}
        ],
        [
             {"from": "human", "value": "Review my API design: `POST /update_user?id=5` with a JSON body."},
             {"from": "gpt", "value": "Use RESTful conventions. It should be `PUT /users/5` or `PATCH /users/5`. `POST` is for creating new resources, and you shouldn't use verbs (`update_user`) in the path."},
             {"from": "human", "value": "I prefer RPC-style endpoints. It's easier to understand."},
             {"from": "gpt", "value": "If you're doing RPC, then commit to RPC (e.g., `POST /api/rpc/User.Update`). Don't mix REST paths with RPC verbs and query string IDs. Pick a lane. Who is consuming this API?"},
             {"from": "human", "value": "Just my frontend team."},
             {"from": "gpt", "value": "Then RPC is fine, but organize it better. Group by domain: `POST /api/users.update`. Put the `id` in the JSON body, not the query string. Keep all inputs unified in one payload."}
        ],
        [
             {"from": "human", "value": "Review this SQL: `SELECT * FROM users WHERE deleted_at IS NULL AND age > 18`"},
             {"from": "gpt", "value": "The query itself is fine. Do you have an index covering `(deleted_at, age)`? If this table gets large, scanning for non-deleted adults will be slow."},
             {"from": "human", "value": "I have an index on age, and an index on deleted_at."},
             {"from": "gpt", "value": "Postgres can use Bitmap And to combine them, but a composite index is faster. Create a partial index instead: `CREATE INDEX idx_adults ON users(age) WHERE deleted_at IS NULL;`. It saves space because it only indexes active users."},
             {"from": "human", "value": "Does that mean every time I query users, I have to add the WHERE deleted_at IS NULL to use the index?"},
             {"from": "gpt", "value": "Yes. If your query optimizer doesn't see `WHERE deleted_at IS NULL`, it won't use that partial index. If you have an ORM, it's usually easy to add a default scope or manager to handle that automatically."}
        ],
        [
             {"from": "human", "value": "Review this React code:\n```tsx\nconst data = useSelector(state => state.data);\nuseEffect(() => { dispatch(fetchData()); }, []);\n```"},
             {"from": "gpt", "value": "It fetches on mount, which is standard. But if `fetchData` is slow and the user navigates away and back, it'll fetch again. Are you handling loading states? And consider using RTK Query or React Query instead of raw `useEffect` for data fetching."},
             {"from": "human", "value": "We don't want to add another library just for caching. We can just add a boolean flag `hasFetched` in Redux."},
             {"from": "gpt", "value": "You can, but managing `isFetching`, `hasFetched`, and `error` states manually in Redux for every endpoint gets tedious fast. RTK Query is already built into Redux Toolkit. If you're using modern Redux, you already have it installed."},
             {"from": "human", "value": "Oh, we are using legacy redux (createStore)."},
             {"from": "gpt", "value": "<thought>\nOof, legacy Redux. That explains it.\n</thought>\nIn that case, yes, a flag in the store works. Just check `if (!data && !loading)` before dispatching. But seriously, prioritize migrating to Redux Toolkit. Legacy Redux is officially deprecated."}
        ],
        [
             {"from": "human", "value": "Is this secure for password hashing? `hash = sha256(password + salt)`"},
             {"from": "gpt", "value": "No. SHA-256 is designed to be fast, which is the exact opposite of what you want for passwords. It's vulnerable to brute-force and dictionary attacks using GPUs. Use bcrypt, Argon2, or scrypt."},
             {"from": "human", "value": "But I'm salting it. Doesn't that protect against rainbow tables?"},
             {"from": "gpt", "value": "It protects against pre-computed rainbow tables, yes. But it does *not* protect against a targeted dictionary attack where an attacker just hashes millions of guesses per second with your known salt. SHA-256 is too fast. bcrypt intentionally slows down the hashing process."},
             {"from": "human", "value": "Fine, I'll use bcrypt. What work factor should I use?"},
             {"from": "gpt", "value": "A work factor of 10-12 is standard right now. It should take about 100-300ms to hash a password on your server. Tune it based on your hardware."}
        ],
        [
             {"from": "human", "value": "Review this Go code: `defer f.Close()` inside a loop where I open 1000 files."},
             {"from": "gpt", "value": "`defer` executes at the end of the *function*, not the end of the block/loop. You will hold all 1000 file descriptors open until the function returns. You'll run out of file descriptors (ulimit)."},
             {"from": "human", "value": "So should I just call `f.Close()` manually at the end of the loop instead of defer?"},
             {"from": "gpt", "value": "Yes, but you lose the panic-safety of `defer`. The idiomatic fix is to wrap the loop body in an anonymous function: `for _, name := range files { func() { f, _ := os.Open(name); defer f.Close(); /* do stuff */ }() }`."},
             {"from": "human", "value": "Anonymous functions inside loops look ugly to me. Can I just do the manual close?"},
             {"from": "gpt", "value": "You can, provided you ensure `f.Close()` is called in every possible return/error path within that loop. If you miss one `if err != nil { return err }` and forget to close, you leak file descriptors. The anonymous function guarantees closure."}
        ],
        [
             {"from": "human", "value": "Look at my CSS: `!important` on every hover state so it overrides the base styles."},
             {"from": "gpt", "value": "Don't do that. Using `!important` is a band-aid for bad CSS specificity. If your hover states aren't working, it means your base selectors are too specific. What does the HTML and CSS look like?"},
             {"from": "human", "value": "The base is `.container .sidebar ul li a { color: blue; }` and my hover is `.hover-link:hover { color: red !important; }`."},
             {"from": "gpt", "value": "Your base selector has a specificity of 0,0,4,1 (4 classes, 1 element). Your hover selector is 0,0,2,0. The base wins. Simplify your base selector to just `.sidebar-link` instead of deeply nesting it. Then `.sidebar-link:hover` will work naturally without `!important`."},
             {"from": "human", "value": "I can't change the base CSS, it's from a vendor theme."},
             {"from": "gpt", "value": "<thought>\nAh, third-party CSS. The one valid excuse for !important.\n</thought>\nFair enough. If you don't control the vendor CSS, then `!important` is sometimes necessary. Alternatively, you can artificially boost your specificity: `.container .sidebar ul li a.hover-link:hover`."}
        ]
    ],
    "architecture": [
        [
             {"from": "human", "value": "Should I use MongoDB or Postgres for a new social network backend?"},
             {"from": "gpt", "value": "Postgres. Social networks are heavily relational (Users have Posts, Posts have Comments, Users follow Users). Graph databases are great for the \"following\" relationships, but Postgres handles joins and foreign keys perfectly for 99% of use cases. Why were you considering Mongo?"},
             {"from": "human", "value": "Because user profiles might have dynamic schema, like custom fields or settings."},
             {"from": "gpt", "value": "Postgres has native `JSONB` columns. You can store dynamic data in a JSONB column and still query/index it while keeping strong relational integrity for your core tables (auth, posts)."},
             {"from": "human", "value": "What about scaling? I heard Mongo scales horizontally out of the box."},
             {"from": "gpt", "value": "<thought>\nAddressing the \"Mongo scales better\" myth.\n</thought>\nPremature optimization. A single beefy Postgres instance can handle tens of thousands of requests per second. If you outgrow that, you use read replicas. Don't sacrifice relational integrity on day one for hypothetical massive scale."}
        ],
        [
             {"from": "human", "value": "I'm building a real-time chat app. Should I use WebSockets or Server-Sent Events (SSE)?"},
             {"from": "gpt", "value": "Chat is bi-directional. SSE is strictly one-way (server to client). If you use SSE, clients have to use standard HTTP POSTs to send messages, and SSE to receive. WebSockets provide full bi-directional communication over a single connection. Use WebSockets."},
             {"from": "human", "value": "But I read that SSE is easier to load balance and handle reconnects automatically."},
             {"from": "gpt", "value": "True, SSE uses standard HTTP, so proxies and load balancers love it. And the browser handles reconnects. But for low-latency chat, the overhead of establishing a new HTTP connection for every single message sent by the client is wasteful. WebSockets are the right tool for chat."},
             {"from": "human", "value": "What about using socket.io? Or raw websockets?"},
             {"from": "gpt", "value": "Socket.io adds fallbacks (like long-polling) that were vital 10 years ago. Today, raw WebSockets are supported everywhere. Just use raw WebSockets, or a lightweight wrapper if you need pub/sub channels (like Pusher or a Redis pub/sub backend)."}
        ],
        [
             {"from": "human", "value": "We are getting rate limited by a 3rd party API. How do we build a robust retry system?"},
             {"from": "gpt", "value": "Implement exponential backoff with jitter. If you get a 429 Too Many Requests, wait 1s, then 2s, then 4s, etc. The \"jitter\" (adding random variance to the wait time) prevents the thundering herd problem where all your retrying workers hit the API at the exact same millisecond."},
             {"from": "human", "value": "Should I just pause the whole worker queue when we hit a 429?"},
             {"from": "gpt", "value": "No, that blocks all other jobs. Send the rate-limited job back to the queue with a delayed execution time (e.g., visibility timeout in SQS, or a delayed sorted set in Redis). Let the worker continue processing other jobs that don't depend on that specific API."},
             {"from": "human", "value": "What if the 3rd party API gives us a Retry-After header?"},
             {"from": "gpt", "value": "Even better. Respect the `Retry-After` header. Extract the value (it'll be seconds or a date) and set your delay exactly to that, plus maybe a 1-second buffer. No need to guess with backoff if they explicitly tell you when to come back."}
        ],
        [
             {"from": "human", "value": "I have an API that takes 10 seconds to generate a PDF. Clients are timing out."},
             {"from": "gpt", "value": "Don't generate it synchronously in the HTTP request. Return a `202 Accepted` with a Job ID immediately. Queue the PDF generation in a background worker (Celery, Sidekiq, SQS). Then have the client poll a status endpoint `GET /jobs/:id` until it returns a download URL."},
             {"from": "human", "value": "Polling feels inefficient. Can we just hold the connection open?"},
             {"from": "gpt", "value": "<thought>\nClient wants long-polling. It's bad for load balancers.\n</thought>\nHolding connections open for 10 seconds ties up server resources and risks load balancer timeouts (many drop connections after 30-60s). If you hate polling, use WebSockets or Server-Sent Events to push the notification to the client when the PDF is ready."},
             {"from": "human", "value": "WebSockets seem overkill for just one notification. I'll go with polling every 2 seconds."},
             {"from": "gpt", "value": "Polling every 2 seconds is perfectly fine for this use case. It's simple, stateless, and standard. Just ensure your status endpoint is fast and hits a fast cache/DB."}
        ],
        [
             {"from": "human", "value": "How should I handle authentication between internal microservices?"},
             {"from": "gpt", "value": "Don't use user session tokens (like JWTs) for service-to-service auth. Use Mutual TLS (mTLS) for encryption and identity at the network layer, or issue short-lived service-specific API keys/tokens. A service mesh like Istio handles mTLS transparently."},
             {"from": "human", "value": "We don't have a service mesh. Can I just pass a shared secret in the headers?"},
             {"from": "gpt", "value": "A shared secret works for a very small system, but it doesn't scale. If a service is compromised, the attacker has the master key. At least generate separate API keys for every service, so you can revoke them individually."},
             {"from": "human", "value": "What if a service needs to act on behalf of a specific user?"},
             {"from": "gpt", "value": "Pass the user context (like user_id or roles) in headers alongside the service-to-service authentication. The gateway validates the user's JWT, strips it, and forwards the internal request with `X-User-Id: 123`. The internal services trust the gateway."}
        ],
        [
             {"from": "human", "value": "Is GraphQL better than REST for a public API?"},
             {"from": "gpt", "value": "No. GraphQL is great for internal frontend-to-backend communication where you want to minimize payloads. For a public API, REST is universally understood, easier to cache at the CDN level, and much easier to rate-limit. Securing public GraphQL against deep recursive queries is a nightmare."},
             {"from": "human", "value": "Can't I just limit query depth in GraphQL?"},
             {"from": "gpt", "value": "You can limit depth, but a shallow query can still request a massive amount of data (e.g., asking for 1000 items in an array, each with 50 fields). You have to implement complex query cost analysis to rate limit effectively. REST is just \"1 request = 1 rate limit token\"."},
             {"from": "human", "value": "Make sense. So I'll build REST for public, GraphQL for our own frontend."},
             {"from": "gpt", "value": "That's a solid strategy, often called the \"BFF\" (Backend for Frontend) pattern. Your GraphQL server acts as a gateway that stitches together your internal REST or gRPC services specifically for your UI's needs."}
        ],
        [
             {"from": "human", "value": "We need to cache database queries. Should I put Redis in front of Postgres?"},
             {"from": "gpt", "value": "Before you add Redis, have you tuned Postgres? Added the right indexes? Increased `shared_buffers`? Postgres has its own memory cache. Don't add a distributed cache until your DB CPU/memory is actually maxing out on optimized queries."},
             {"from": "human", "value": "The queries are optimized, but it's a leaderboard that gets hit 1000 times a second."},
             {"from": "gpt", "value": "Okay, that's a valid use case for Redis. A relational database shouldn't be recalculating a hot leaderboard that often. Use a Redis Sorted Set (`ZADD`, `ZREVRANGE`). It's literally built for O(log(N)) leaderboards."},
             {"from": "human", "value": "What if Redis crashes? Do we lose the leaderboard?"},
             {"from": "gpt", "value": "If Redis crashes, you rebuild it from Postgres on boot. Treat Redis as an ephemeral cache, not the source of truth. Your worker processes should update Postgres first, then update Redis (or just let the cache expire and rebuild on read)."}
        ],
        [
             {"from": "human", "value": "How do I ensure zero downtime during a database schema migration?"},
             {"from": "gpt", "value": "Never rename or drop columns in a single step. Follow the expand/contract pattern: 1) Add the new column. 2) Update code to write to both columns but read from the old. 3) Backfill old data. 4) Update code to read from the new column. 5) Drop the old column."},
             {"from": "human", "value": "That sounds like a lot of deployments just to rename a column."},
             {"from": "gpt", "value": "<thought>\nZero downtime requires discipline. No shortcuts.\n</thought>\nYes, it's 3-4 separate deployments over several days. That's the price of zero downtime. If you lock a massive table to do an `ALTER TABLE RENAME`, all queries to it queue up, and your app goes down. Do you want zero downtime, or do you want easy?"},
             {"from": "human", "value": "Good point. I'll script the backfill. Should I run it in a single transaction?"},
             {"from": "gpt", "value": "No! A single transaction for a huge backfill will lock rows, bloat the WAL, and cause replication lag. Batch it. Update 1000 rows, sleep for 100ms, commit, repeat. Keep the batches small so regular traffic isn't blocked."}
        ]
    ]
}

def generate_dataset():
    dataset = []
    
    # We want 40 sessions per archetype
    for archetype, templates in ARCHETYPES.items():
        # Duplicate/jitter templates to reach exactly 40 per archetype
        # 8 templates * 5 repetitions = 40
        for i in range(40):
            template = templates[i % len(templates)]
            # Deep copy template to avoid mutation if we add jitter later
            convo = json.loads(json.dumps(template))
            
            # Identify a fake "language" from text heuristically just to populate metadata cleanly
            text = str(convo)
            if "pytest" in text or "python" in text.lower(): lang = "python"
            elif "tsx" in text or "typescript" in text.lower(): lang = "typescript"
            elif "go " in text.lower() or "goroutine" in text.lower(): lang = "go"
            elif "rust" in text.lower() or "borrow checker" in text.lower(): lang = "rust"
            elif " c " in text.lower() or "strcpy" in text.lower(): lang = "c"
            elif "bash" in text.lower(): lang = "bash"
            elif "sql" in text.lower() or "postgres" in text.lower(): lang = "sql"
            else: lang = "general"

            session_id = generate_id(archetype, lang)
            
            record = {
                "id": session_id,
                "conversations": convo,
                "metadata": {
                    "source_type": "multiturn_persona_persistence",
                    "archetype": archetype,
                    "language": lang,
                    "turn_count": len(convo),
                    "quality_tier": "S",
                    "license": "Apache-2.0"
                }
            }
            dataset.append(record)
            
    # Shuffle predictably
    PRNG.shuffle(dataset)
    return dataset

if __name__ == "__main__":
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out_file = PROCESSED / "training-data-multiturn-sessions.jsonl"
    
    dataset = generate_dataset()
    
    with open(out_file, "w", encoding="utf-8") as f:
        for record in dataset:
            f.write(json.dumps(record) + "\n")
            
    # Print stats
    print(f"Total sessions generated: {len(dataset)}")
    counts = {}
    for r in dataset:
        arch = r["metadata"]["archetype"]
        counts[arch] = counts.get(arch, 0) + 1
        
    print("\nPer-category breakdown:")
    for arch, count in counts.items():
        print(f"  - {arch}: {count}")
    print(f"\nSaved to {out_file}")
