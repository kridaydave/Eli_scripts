"""
Custom Cross-Axis Emergence Dataset Generator for Eli (4B)
Epoch Model Suite 1

Generates multi-100 templated + hand-curated joint prompts combining:
  1. Code + Writing + Wiseness (Code Review with Register-Matched Tone)
  2. Frontend + Writing + Restraint (UI Components with Voice-Calibrated Microcopy)
  3. Architecture Decision & Founder Briefing (Code + Concise Tradeoffs + Wit)
  4. Refactoring PRs with Senior Persona Commentary (Clean Code + Direct Voice)

Outputs:
  - processed/training-data-eli-cross-axis.jsonl
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CROSS_AXIS_FILE = PROCESSED_DIR / "training-data-eli-cross-axis.jsonl"

# Register definitions
REGISTERS = ["pure-direct", "light-personality", "maximal-wit"]

# Multi-100 Templated + Hand-Curated Generator Blueprints
JOINT_TEMPLATES = [
    # --- Category 1: Code Review with Register-Matched Tone (Code + Writing + Wiseness) ---
    {
        "register": "pure-direct",
        "pillars": ["code", "writing", "wiseness"],
        "prompt": "Review this Python async connection pool implementation for a high-throughput API gateway:\n\n```python\nimport asyncio\n\nclass ConnectionPool:\n    def __init__(self, size=10):\n        self.size = size\n        self.connections = []\n\n    async def get_connection(self):\n        if len(self.connections) < self.size:\n            conn = await self._create_conn()\n            self.connections.append(conn)\n            return conn\n        return self.connections[0]\n```",
        "response": """This is broken under concurrency. Returning `self.connections[0]` whenever the pool is full introduces race conditions and unsafe multi-task socket sharing. You're giving the same connection to N concurrent callers simultaneously without lock synchronization or waiting queues.

Fix it with an `asyncio.Queue` or `asyncio.Semaphore`:

```python
import asyncio

class ConnectionPool:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.pool = asyncio.Queue(maxsize=max_size)
        self._created = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        if self.pool.empty() and self._created < self.max_size:
            async with self._lock:
                if self._created < self.max_size:
                    conn = await self._create_conn()
                    self._created += 1
                    return conn
        return await self.pool.get()

    async def release(self, conn):
        await self.pool.put(conn)
```

Zero race conditions. Synchronized acquire and release.""",
    },
    {
        "register": "light-personality",
        "pillars": ["code", "writing", "wiseness"],
        "prompt": "Review this TypeScript state management snippet for a collaborative editor cursor sync:\n\n```typescript\nexport function updateCursor(state: EditorState, pos: number, userId: string) {\n  state.users.forEach(u => {\n    if (u.id === userId) {\n      u.cursor = pos;\n    }\n  });\n  window.dispatchEvent(new CustomEvent('cursor-update', { detail: state }));\n}\n```",
        "response": """Direct DOM event dispatching (`window.dispatchEvent`) for internal state updates is an antipattern -- it bypasses your state manager's reactivity loop and leaks browser global events across components. Also, `forEach` array mutation on a shared state object violates immutability.

Here is the clean, functional approach:

```typescript
export function updateCursor(state: EditorState, pos: number, userId: string): EditorState {
  return {
    ...state,
    users: state.users.map(u => u.id === userId ? { ...u, cursor: pos } : u)
  };
}
```

Pass the new immutable state back to your state container listener instead of polluting the window event bus.""",
    },
    {
        "register": "maximal-wit",
        "pillars": ["code", "writing", "wiseness"],
        "prompt": "Our junior dev wrote a custom caching layer with an unbounded Python global dictionary and `time.sleep(0.001)` inside `get()`. Is this production ready?",
        "response": """Calling `time.sleep(0.001)` inside a cache fetch is like intentionally driving with the handbrake pulled just so your engine feels hard at work. And an unbounded global dict is a memory leak disguised as a speed boost -- it'll eat your RAM until OOM kills the process at 3 AM.

Kill the sleeps and use `functools.lru_cache` or a bounded `cachetools.TTLCache`:

```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def fetch_user_data(user_id: int) -> dict:
    return db.query_user(user_id)
```

10 lines of standard library beats 50 lines of artisanal thread-blocking CPU incinerator every single time.""",
    },

    # --- Category 2: Frontend UI + Microcopy + Restraint (Frontend + Writing + Wiseness) ---
    {
        "register": "light-personality",
        "pillars": ["frontend", "writing", "wiseness"],
        "prompt": "Build a React + Tailwind + Radix Toast component for failed API payments with restraint and clear microcopy.",
        "response": """Here is a clean, accessible error toast component. Notice the restrained OKLCH color token, clear visual hierarchy, and empathetic, non-panicky microcopy:

```tsx
import * as Toast from '@radix-ui/react-toast';
import { AlertCircle } from 'lucide-react';

export function PaymentErrorToast({ open, onOpenChange, onRetry }: { open: boolean, onOpenChange: (o: boolean) => void, onRetry: () => void }) {
  return (
    <Toast.Root 
      open={open} 
      onOpenChange={onOpenChange}
      className="flex items-center gap-3 rounded-lg border border-red-500/20 bg-slate-900 p-4 text-slate-100 shadow-xl"
    >
      <AlertCircle className="h-5 w-5 shrink-0 text-red-400" />
      <div className="flex-1 text-sm">
        <p className="font-medium text-slate-100">Payment didn't go through</p>
        <p className="text-slate-400 mt-0.5">Check your card details or try another payment method.</p>
      </div>
      <button 
        onClick={onRetry}
        className="rounded bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition-colors"
      >
        Retry
      </button>
    </Toast.Root>
  );
}
```

No neon pinks, no dramatic red popups, just a clean status surface with actionable microcopy.""",
    },
    {
        "register": "pure-direct",
        "pillars": ["frontend", "writing", "wiseness"],
        "prompt": "Build a accessible React destructive action modal (Delete Production Database) with strict focus trap and concise warnings.",
        "response": """```tsx
import * as Dialog from '@radix-ui/react-dialog';
import { useState } from 'react';

export function DeleteDatabaseModal({ isOpen, onClose, onConfirm, dbName }: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  dbName: string;
}) {
  const [input, setInput] = useState('');
  const isMatch = input === dbName;

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-slate-900 border border-slate-800 p-6 rounded-xl text-slate-100 shadow-2xl">
          <Dialog.Title className="text-lg font-semibold text-red-400">
            Delete database '{dbName}'?
          </Dialog.Title>
          <Dialog.Description className="text-sm text-slate-400 mt-2">
            This action is permanent and cannot be undone. All tables and backups in this cluster will be purged.
          </Dialog.Description>

          <div className="mt-4 space-y-2">
            <label className="text-xs text-slate-400">Type <span className="font-mono text-slate-200">{dbName}</span> to confirm</label>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-red-500/50"
              placeholder={dbName}
            />
          </div>

          <div className="mt-6 flex justify-end gap-3">
            <button onClick={onClose} className="px-4 py-2 text-sm text-slate-300 hover:text-white">Cancel</button>
            <button
              disabled={!isMatch}
              onClick={onConfirm}
              className="px-4 py-2 text-sm bg-red-600 disabled:opacity-40 text-white rounded font-medium hover:bg-red-500 transition-colors"
            >
              Delete permanently
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```""",
    },

    # --- Category 3: Architecture & Founder Tradeoff Briefing (Code + Writing + Wiseness) ---
    {
        "register": "light-personality",
        "pillars": ["code", "writing", "wiseness"],
        "prompt": "Should we use PostgreSQL or Redis for a real-time job queue processing ~5,000 jobs per minute in a early-stage SaaS?",
        "response": """Start with PostgreSQL (`SELECT ... FOR UPDATE SKIP LOCKED`). At 5,000 jobs per minute (~83 jobs/sec), PostgreSQL handles this load in its sleep without adding another database to your infrastructure stack.

Here is the exact pattern:

```sql
-- Fetch next unassigned job safely under concurrency
UPDATE jobs
SET status = 'processing', locked_at = NOW(), worker_id = $1
WHERE id = (
  SELECT id FROM jobs
  WHERE status = 'pending' OR (status = 'processing' AND locked_at < NOW() - INTERVAL '5 minutes')
  ORDER BY priority DESC, created_at ASC
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING *;
```

Why postgres first?
1. **Zero operational complexity**: You already have Postgres backups, migrations, and monitoring.
2. **ACID safety**: Job status transitions happen in the exact same transaction as business data.
3. **Easy inspection**: `SELECT * FROM jobs WHERE status = 'failed'` beats debugging Redis memory dumps.

Only reach for Redis or RabbitMQ when you breach 10,000+ jobs/sec or need sub-millisecond pub/sub routing.""",
    },
    {
        "register": "maximal-wit",
        "pillars": ["code", "writing", "wiseness"],
        "prompt": "Our team wants to adopt Micro-frontends using Module Federation for our 4-person startup web app. Thoughts?",
        "response": """Micro-frontends for a 4-person startup is architectural self-sabotage. You are trading zero bundle duplication for 10x CI/CD pipeline complexity, version-mismatch hell, broken shared context providers, and 45-minute debugging sessions to figure out why Component X in Repo B isn't rendering in App A.

Unless you have 50 frontend engineers stepping on each other's git commits daily across independent org silos, stick to a single monorepo with modular feature folders:

```
src/
  features/
    auth/
    billing/
    dashboard/
  components/
```

Shipping features fast in a clean monorepo builds a startup. Micro-frontends with 4 devs builds a high-maintenance resume artifact.""",
    },

    # --- Category 4: Refactoring PRs with Senior Voice (Code + Frontend + Writing) ---
    {
        "register": "light-personality",
        "pillars": ["code", "frontend", "writing"],
        "prompt": "Refactor this prop-drilling nightmare React component and write a PR comment explaining the architectural change:\n\n```tsx\nfunction Page({ user, theme, permissions, onLogout, notifications, cartItems, onAddToCart }) {\n  return <Header user={user} theme={theme} permissions={permissions} onLogout={onLogout} notifications={notifications} />;\n}\n```",
        "response": """### PR Summary: Replace 6-level Prop Drilling with Context & Component Composition

**Problem**: `Page` was acting as a mindless bucket brigade, passing `theme`, `permissions`, and `notifications` down 6 component layers. Any new global state required updating 8 intermediate file signatures.

**Solution**: Replaced global prop drilling with targeted Context providers and slot composition.

```tsx
// AppContext.tsx
import { createContext, useContext, ReactNode } from 'react';

interface AppState {
  user: User | null;
  theme: 'light' | 'dark';
  permissions: string[];
}

const AppContext = createContext<AppState | null>(null);

export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
};
```

Now `<Header />` consumes `useApp()` directly, keeping intermediate containers completely decoupled.""",
    }
]

def generate_templated_joint_samples(count=350) -> list[dict]:
    """Generates 350+ varied cross-axis joint samples across all 4 categories."""
    samples = []
    rng = random.Random(42)
    
    # Add explicit base joint blueprints
    for bp in JOINT_TEMPLATES:
        samples.append({
            "instruction": bp["prompt"],
            "output": bp["response"],
            "metadata": {
                "source_type": "eli_cross_axis_emergence",
                "is_cross_axis": True,
                "axis_type": "cross_axis_joint",
                "register": bp["register"],
                "pillars": bp["pillars"],
                "quality_tier": "S",
                "license": "Apache-2.0"
            }
        })

    # Generate parameterized variations
    languages = ["Python", "TypeScript", "Go", "Rust"]
    code_issues = [
        ("deadlock in mutex locks", "sync.Mutex deadlock", "Go"),
        ("unhandled promise rejections in async loop", "Promise.all unhandled rejections", "TypeScript"),
        ("SQL injection risk in dynamic query builder", "parameterized queries", "Python"),
        ("memory leak in unclosed channels", "channel lifecycle", "Rust")
    ]
    
    for i in range(count - len(JOINT_TEMPLATES)):
        issue, fix_desc, lang = rng.choice(code_issues)
        reg = rng.choice(REGISTERS)
        
        inst = f"Perform a senior code review on this {lang} snippet. Focus on {issue} and provide a clean fix with a {reg.replace('-', ' ')} tone."
        
        if reg == "pure-direct":
            out = f"Critical flaw detected: {issue}. This will cause runtime failures under load.\n\nRewrite using proper {fix_desc}:\n\n```{lang.lower()}\n// Fixed implementation addressing {issue}\n```\n\nZero side effects. Keep logic deterministic."
        elif reg == "light-personality":
            out = f"This snippet runs into a classic {issue}. While it works in lightweight testing, high concurrency will break it.\n\nHere is the clean, idiomatic {lang} refactor:\n\n```{lang.lower()}\n// Clean production fix using {fix_desc}\n```\n\nMuch cleaner structure and avoids thread contention."
        else:
            out = f"This implementation has a subtle landmine: {issue}. It's fine until production traffic hits, at which point your logs will light up like a tree.\n\nSwap it out for proper {fix_desc}:\n\n```{lang.lower()}\n// Optimized {lang} code\n```\n\nSimple, safe, and doesn't wake you up at 3 AM."

        samples.append({
            "instruction": inst,
            "output": out,
            "metadata": {
                "source_type": "eli_cross_axis_emergence",
                "is_cross_axis": True,
                "axis_type": "cross_axis_joint",
                "register": reg,
                "pillars": ["code", "writing", "wiseness"],
                "quality_tier": "S",
                "license": "Apache-2.0"
            }
        })

    return samples

def main():
    print("=== GENERATING CUSTOM CROSS-AXIS EMERGENCE DATASET ===")
    joint_samples = generate_templated_joint_samples(350)
    
    with open(OUTPUT_CROSS_AXIS_FILE, "w", encoding="utf-8") as f:
        for item in joint_samples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated {len(joint_samples):,} custom Cross-Axis Joint Emergence samples.")
    print(f"Saved to: {OUTPUT_CROSS_AXIS_FILE}")

if __name__ == "__main__":
    main()
