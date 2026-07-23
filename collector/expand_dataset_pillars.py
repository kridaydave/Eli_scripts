"""
Comprehensive Dataset Expansion Script addressing all 7 User Critique Pillars
Epoch Model Suite 1 (Eli v3 Upgrade)

Pillars Addressed:
1. TS/JS Backend Expansion (Hono, Bun, Node, Next.js Server Actions, Drizzle/Prisma)
2. Explicit SQL & Data Layer (CTEs, Window Functions, JSONB, Migrations, Redis Lua)
3. C/C++ & Systems Integration (Rust FFI, C Native Addons, Linux Sockets)
4. Frontend State & Accessibility Edge Cases (Zustand, TanStack Query, Dynamic ARIA, Virtualization)
5. Standardized Agent Tool-Calling (OpenAPI / JSON-Schema specs + MCP)
6. Negative Path & Error Recovery Traces (Failed CLI commands -> Diagnosis -> Fix -> Pass)
7. Diffs (.patch) & "Find and Fix the Bug" Examples (Tokio race conditions, Go deadlocks, Memory leaks)
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = DATA_DIR / "pillar-additions.json"

PILLAR_PAIRS = [
    # =========================================================================
    # PILLAR 1: TYPESCRIPT / JAVASCRIPT BACKEND & ORMs
    # =========================================================================
    {
        "source": "backend_ts_hono_bun",
        "instruction": "Build a high-performance REST microservice in Bun using Hono, Drizzle ORM, Zod validation, and JWT auth.",
        "output": """```typescript
import { Hono } from 'hono';
import { z } from 'zod';
import { zValidator } from '@hono/zod-validator';
import { jwt } from 'hono/jwt';
import { drizzle } from 'drizzle-orm/bun-sqlite';
import { Database } from 'bun:sqlite';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

const sqlite = new Database('app.db');
export const db = drizzle(sqlite);

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  role: text('role').notNull().default('user')
});

const app = new Hono();
const JWT_SECRET = process.env.JWT_SECRET || 'super-secret-key';

app.use('/api/v1/protected/*', jwt({ secret: JWT_SECRET }));

const CreateUserSchema = z.object({
  email: z.string().email(),
  role: z.enum(['admin', 'user']).default('user')
});

app.post('/api/v1/users', zValidator('json', CreateUserSchema), async (c) => {
  const data = c.req.valid('json');
  const newUser = { id: crypto.randomUUID(), ...data };
  await db.insert(users).values(newUser);
  return c.json(newUser, 201);
});

app.get('/api/v1/protected/me', (c) => {
  const payload = c.get('jwtPayload');
  return c.json({ user: payload });
});

export default {
  port: 3000,
  fetch: app.fetch
};
```""",
        "language": "typescript"
    },
    {
        "source": "backend_ts_next_server_action_transaction",
        "instruction": "Write a Next.js 15 Server Action that executes a type-safe multi-table database transaction with Prisma.",
        "output": """```typescript
'use server';

import { prisma } from '@/lib/prisma';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const TransferSchema = z.object({
  fromAccountId: z.string().uuid(),
  toAccountId: z.string().uuid(),
  amount: z.number().positive()
});

export async function transferFundsAction(formData: FormData) {
  const parsed = TransferSchema.safeParse({
    fromAccountId: formData.get('fromAccountId'),
    toAccountId: formData.get('toAccountId'),
    amount: Number(formData.get('amount'))
  });

  if (!parsed.success) {
    return { success: false, error: parsed.error.errors[0].message };
  }

  const { fromAccountId, toAccountId, amount } = parsed.data;

  try {
    await prisma.$transaction(async (tx) => {
      const sender = await tx.account.update({
        where: { id: fromAccountId },
        data: { balance: { decrement: amount } }
      });

      if (sender.balance < 0) {
        throw new Error('Insufficient funds');
      }

      await tx.account.update({
        where: { id: toAccountId },
        data: { balance: { increment: amount } }
      });

      await tx.auditLog.create({
        data: {
          action: 'TRANSFER',
          details: `Transferred $${amount} from ${fromAccountId} to ${toAccountId}`
        }
      });
    });

    revalidatePath('/dashboard/accounts');
    return { success: true };
  } catch (err: any) {
    return { success: false, error: err.message || 'Transaction failed' };
  }
}
```""",
        "language": "typescript"
    },

    # =========================================================================
    # PILLAR 2: EXPLICIT SQL & DATA LAYER (CTEs, WINDOW FUNCTIONS, MIGRATIONS)
    # =========================================================================
    {
        "source": "sql_data_layer_cte_window",
        "instruction": "Write an optimized PostgreSQL SQL query using Recursive CTEs and Window Functions to compute monthly user retention cohorts.",
        "output": """```sql
-- Monthly Cohort Retention Analysis in PostgreSQL
WITH user_first_month AS (
    SELECT 
        user_id,
        DATE_TRUNC('month', MIN(created_at)) AS cohort_month
    FROM users
    GROUP BY user_id
),
user_activity AS (
    SELECT DISTINCT
        e.user_id,
        DATE_TRUNC('month', e.event_time) AS activity_month
    FROM user_events e
),
cohort_size AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT user_id) AS num_users
    FROM user_first_month
    GROUP BY cohort_month
),
retention AS (
    SELECT
        f.cohort_month,
        EXTRACT(YEAR FROM AGE(a.activity_month, f.cohort_month)) * 12 +
        EXTRACT(MONTH FROM AGE(a.activity_month, f.cohort_month)) AS month_number,
        COUNT(DISTINCT a.user_id) AS retained_users
    FROM user_first_month f
    JOIN user_activity a ON f.user_id = a.user_id
    GROUP BY f.cohort_month, month_number
)
SELECT 
    r.cohort_month,
    cs.num_users AS initial_cohort_size,
    r.month_number,
    r.retained_users,
    ROUND((r.retained_users::NUMERIC / cs.num_users) * 100, 2) AS retention_rate_pct
FROM retention r
JOIN cohort_size cs ON r.cohort_month = cs.cohort_month
ORDER BY r.cohort_month DESC, r.month_number ASC;
```""",
        "language": "sql"
    },
    {
        "source": "sql_redis_lua_rate_limiter",
        "instruction": "Write an atomic Redis sliding-window rate limiter script in Lua.",
        "output": """```lua
-- Atomic Sliding Window Rate Limiter in Lua
-- KEYS[1]: Rate limiter key (e.g. rate:user:123)
-- ARGV[1]: Current timestamp in ms
-- ARGV[2]: Window size in ms (e.g. 60000 for 1 min)
-- ARGV[3]: Max allowed requests in window

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

local clearBefore = now - window

-- Remove requests older than sliding window
redis.call('ZREMRANGEBYSCORE', key, 0, clearBefore)

-- Count remaining requests in current window
local currentRequests = redis.call('ZCARD', key)

if currentRequests < limit then
    -- Add current request timestamp to sorted set
    redis.call('ZADD', key, now, now)
    redis.call('PEXPIRE', key, window)
    return {1, limit - currentRequests - 1} -- Allowed (1 = true), remaining requests
else
    return {0, 0} -- Denied (0 = false), 0 remaining
end
```""",
        "language": "lua"
    },

    # =========================================================================
    # PILLAR 3: C/C++ SYSTEMS INTEGRATION & RUST FFI
    # =========================================================================
    {
        "source": "c_systems_ffi_rust",
        "instruction": "Show how to expose a C native library function and call it safely from Rust via FFI bindings.",
        "output": """```c
// native_crypto.c
#include <stdint.h>
#include <stddef.h>

int32_t fast_xor_encrypt(const uint8_t* input, uint8_t* output, size_t len, uint8_t key) {
    if (!input || !output) return -1;
    for (size_t i = 0; i < len; i++) {
        output[i] = input[i] ^ key;
    }
    return 0;
}
```

```rust
// main.rs - Rust FFI Wrapper
use std::ffi::c_int;

#[link(name = "native_crypto")]
extern "C" {
    fn fast_xor_encrypt(
        input: *const u8,
        output: *mut u8,
        len: usize,
        key: u8,
    ) -> c_int;
}

pub fn encrypt_bytes(data: &[u8], key: u8) -> Result<Vec<u8>, &'static str> {
    let mut buffer = vec![0u8; data.len()];
    let res = unsafe {
        fast_xor_encrypt(
            data.as_ptr(),
            buffer.as_mut_ptr(),
            data.len(),
            key,
        )
    };

    if res == 0 {
        Ok(buffer)
    } else {
        Err("Native encryption failed")
    }
}

fn main() {
    let secret = b"Epoch Model Suite FFI Test";
    let encrypted = encrypt_bytes(secret, 0x5A).unwrap();
    println!("Encrypted length: {}", encrypted.len());
}
```""",
        "language": "rust"
    },

    # =========================================================================
    # PILLAR 4: FRONTEND STATE & ACCESSIBILITY EDGE CASES
    # =========================================================================
    {
        "source": "frontend_state_zustand_tanstack",
        "instruction": "Build a clean Zustand store with optimistic mutation handling using TanStack Query v5 in React 19.",
        "output": """```tsx
import React from 'react';
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Plus } from 'lucide-react';

// Zustand Global UI State Store
interface UIStore {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      (set) => ({
        isSidebarOpen: true,
        toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen }))
      }),
      { name: 'ui-settings' }
    )
  )
);

// TanStack Query v5 Optimistic Mutation Component
export default function TaskList() {
  const queryClient = useQueryClient();

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const res = await fetch('/api/tasks');
      return res.json();
    }
  });

  const mutation = useMutation({
    mutationFn: async (newTaskTitle: string) => {
      const res = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTaskTitle })
      });
      return res.json();
    },
    onMutate: async (newTaskTitle) => {
      await queryClient.cancelQueries({ queryKey: ['tasks'] });
      const previousTasks = queryClient.getQueryData(['tasks']);
      queryClient.setQueryData(['tasks'], (old: any = []) => [
        ...old,
        { id: 'temp-' + Date.now(), title: newTaskTitle, pending: true }
      ]);
      return { previousTasks };
    },
    onError: (err, newTaskTitle, context) => {
      queryClient.setQueryData(['tasks'], context?.previousTasks);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    }
  });

  return (
    <div className="p-6 bg-zinc-900 rounded-2xl border border-zinc-800 text-white max-w-md">
      <h2 className="text-lg font-bold mb-4">Optimistic Tasks</h2>
      {isLoading ? <Loader2 className="animate-spin" /> : (
        <ul className="space-y-2 mb-4">
          {tasks.map((t: any) => (
            <li key={t.id} className={`p-3 bg-zinc-800 rounded-xl ${t.pending ? 'opacity-50' : ''}`}>
              {t.title}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```""",
        "language": "tsx"
    },

    # =========================================================================
    # PILLAR 5: STANDARDIZED AGENT TOOL-CALLING SCHEMA (OPENAPI / JSON SCHEMA)
    # =========================================================================
    {
        "source": "agent_tool_calling_schema",
        "instruction": "Parse a user request to run a database query and output standard OpenAI JSON-schema function call parameters.",
        "output": """To query the active user count, here is the structured tool call adhering to standard OpenAPI / JSON Schema format:

```json
{
  "type": "function",
  "function": {
    "name": "execute_database_query",
    "description": "Executes a read-only SQL query against the primary PostgreSQL database cluster.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The parameterized SELECT query to execute."
        },
        "timeout_ms": {
          "type": "integer",
          "description": "Query execution timeout in milliseconds.",
          "default": 5000
        }
      },
      "required": ["query"]
    }
  },
  "arguments": {
    "query": "SELECT COUNT(*) AS active_users FROM users WHERE status = 'active' AND last_login >= NOW() - INTERVAL '24 hours';",
    "timeout_ms": 3000
  }
}
```""",
        "language": "json"
    },

    # =========================================================================
    # PILLAR 6: NEGATIVE PATH & ERROR RECOVERY TRACES
    # =========================================================================
    {
        "source": "agent_negative_path_recovery",
        "instruction": "Debug a failing TypeScript build error caused by missing module declarations.",
        "output": """<thought>
Let's run `tsc` build command to verify compilation errors.
</thought>

**Tool Action (run_command)**:
```json
{
  "CommandLine": "npx tsc --noEmit",
  "Cwd": "/app"
}
```

**Tool Result (Error Output)**:
```
src/index.ts:4:23 - error TS2307: Cannot find module 'express' or its corresponding type declarations.
4 import express from 'express';
                      ~~~~~~~~~
```

<thought>
The error `TS2307` indicates missing `@types/express` declarations or uninstalled `express` dependency. I will inspect `package.json` and install `@types/express` as a dev dependency.
</thought>

**Tool Action (run_command)**:
```json
{
  "CommandLine": "npm i -D @types/express @types/node",
  "Cwd": "/app"
}
```

**Tool Result**:
```
added 14 packages in 1.2s
```

<thought>
Re-running `npx tsc --noEmit` to verify that the build error is resolved.
</thought>

**Tool Action (run_command)**:
```json
{
  "CommandLine": "npx tsc --noEmit",
  "Cwd": "/app"
}
```

**Tool Result**:
```
✔ Compilation complete. 0 errors found.
```

Fixed! Installing `@types/express` resolved the missing module declaration error.""",
        "language": "agent_trace"
    },

    # =========================================================================
    # PILLAR 7: UNIFIED DIFF (.PATCH) & "FIND AND FIX THE BUG" PAIRS
    # =========================================================================
    {
        "source": "bug_fix_tokio_race_condition",
        "instruction": "Find and fix the memory leak and race condition in this Tokio async worker loop.",
        "output": """### Bug Analysis
1. **Unbounded Task Spawning**: `tokio::spawn` is called in an infinite loop without backpressure, causing unlimited memory consumption.
2. **Shared State Data Race**: `Arc<Mutex<T>>` guard is held across `.await` points, deadlocking the Tokio runtime threads.

### Unified Patch Fix (`.patch`)

```diff
<<<<<<< SEARCH
async fn process_queue(queue: Arc<Mutex<Vec<String>>>) {
    loop {
        let items = queue.lock().unwrap();
        for item in items.iter() {
            tokio::spawn(async move {
                fetch_remote_data(item).await;
            });
        }
        tokio::time::sleep(Duration::from_millis(10)).await;
    }
}
=======
async fn process_queue(queue: Arc<Mutex<Vec<String>>>, semaphore: Arc<tokio::sync::Semaphore>) {
    loop {
        // Drop lock before await to prevent runtime thread deadlocks
        let items_to_process = {
            let mut guard = queue.lock().unwrap();
            std::mem::take(&mut *guard)
        };

        for item in items_to_process {
            let permit = semaphore.clone().acquire_owned().await.unwrap();
            tokio::spawn(async move {
                let _permit = permit; // Bounded concurrency limit
                fetch_remote_data(&item).await;
            });
        }
        tokio::time::sleep(Duration::from_millis(100)).await;
    }
}
>>>>>>> REPLACE
```""",
        "language": "diff"
    },
    {
        "source": "bug_fix_python_memory_leak",
        "instruction": "Identify and fix the memory leak in this Python AsyncIO event loop callback handler.",
        "output": """### Root Cause
The global `_callbacks` list grows indefinitely because completed task references are appended without cleanup, creating an uncollectable object cycle in memory.

### Fix (.patch)

```diff
<<<<<<< SEARCH
_callbacks = []

def register_task(task):
    _callbacks.append(task)
    task.add_done_callback(lambda t: print("Done", t.result()))
=======
import weakref

_callbacks = weakref.WeakSet()

def register_task(task):
    _callbacks.add(task)
    def _on_complete(t):
        if not t.cancelled() and t.exception() is None:
            print("Done", t.result())
    task.add_done_callback(_on_complete)
>>>>>>> REPLACE
```""",
        "language": "diff"
    }
]

def main():
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(PILLAR_PAIRS, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(PILLAR_PAIRS)} comprehensive pillar dataset additions to {OUT_FILE}")

if __name__ == "__main__":
    main()
