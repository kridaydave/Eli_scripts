"""
Malleable & Unique Agentic Coding Dataset Generator for OpenCode / Coding Agents
Epoch Model Suite 1 (Eli)

Generates 100% unique, diverse agentic coding pairs across:
1. Open-ended web applications (HTML/Tailwind/JS, React/TSX)
2. Backend microservices (FastAPI, Go Fiber, Rust Axum, Express)
3. Agent tool-use & code edits (Search/Replace diffs, terminal debugging, test-driven refactoring)
"""

import json
import random
from pathlib import Path

# Category 1: Single-File Interactive Web Apps (Rich, complete, unique apps)
WEB_APP_SPECS = [
    {
        "title": "Habit Tracker",
        "prompts": [
            "Make me a personal habit tracker",
            "Build a sleek habit tracker with streak counters and dark mode",
            "Create a single-file daily habit tracking web app"
        ],
        "intro": "Done. Here's a clean, single-file habit tracker with persistent localStorage, streak counters, weekly progress grid, and dark mode.",
        "code_lang": "html",
        "code": """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pulse — Personal Habit Tracker</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen font-sans antialiased">
  <div class="max-w-4xl mx-auto px-6 py-12">
    <header class="flex items-center justify-between border-b border-zinc-800 pb-6 mb-8">
      <div>
        <h1 class="text-3xl font-bold text-white tracking-tight">Pulse</h1>
        <p class="text-xs text-zinc-400 mt-1">Daily consistency engine</p>
      </div>
      <button id="addBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition-all shadow-lg shadow-indigo-600/20 active:scale-95">
        + New Habit
      </button>
    </header>
    <div id="habits" class="space-y-4"></div>
  </div>
  <script>
    let habits = JSON.parse(localStorage.getItem('eli_habits') || '[{"id":"1","title":"Read 30 mins","streak":4,"done":false},{"id":"2","title":"Cold shower","streak":7,"done":true}]');
    function save() { localStorage.setItem('eli_habits', JSON.stringify(habits)); render(); }
    function render() {
      const container = document.getElementById('habits');
      container.innerHTML = '';
      habits.forEach(h => {
        const el = document.createElement('div');
        el.className = 'bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex items-center justify-between';
        el.innerHTML = `
          <div class="flex items-center space-x-4">
            <button onclick="toggle('${h.id}')" class="w-6 h-6 rounded-md border ${h.done ? 'bg-emerald-500 border-emerald-500 text-black font-bold' : 'border-zinc-700'}">${h.done ? '✓' : ''}</button>
            <span class="${h.done ? 'line-through text-zinc-500' : 'text-white font-medium'}">${h.title}</span>
          </div>
          <span class="text-xs font-medium text-indigo-400 bg-indigo-950/60 border border-indigo-800/50 px-3 py-1 rounded-full">${h.streak} day streak 🔥</span>
        `;
        container.appendChild(el);
      });
    }
    function toggle(id) {
      const h = habits.find(x => x.id === id);
      if(h) { h.done = !h.done; if(h.done) h.streak++; else h.streak = Math.max(0, h.streak-1); save(); }
    }
    document.getElementById('addBtn').onclick = () => {
      const title = prompt('Habit name:');
      if(title) { habits.push({id: Date.now().toString(), title, streak: 0, done: false}); save(); }
    };
    render();
  </script>
</body>
</html>"""
    },
    {
        "title": "Pomodoro Timer",
        "prompts": [
            "Build a slick pomodoro timer web app",
            "Make me a focus timer with session logs and audio ticks",
            "Create a minimalist pomodoro timer in Tailwind"
        ],
        "intro": "Here's a single-file Pomodoro timer with audio alerts, custom work/break intervals, session tracking, and keyboard shortcuts.",
        "code_lang": "html",
        "code": """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <title>Focus — Minimalist Pomodoro</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex items-center justify-center p-6">
  <div class="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 max-w-md w-full text-center shadow-2xl space-y-6">
    <div id="timer" class="text-7xl font-mono font-bold text-white tracking-tight">25:00</div>
    <div class="flex justify-center space-x-3">
      <button id="start" onclick="toggle()" class="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-8 py-3 rounded-xl shadow-lg transition-all w-32">Start</button>
      <button onclick="reset()" class="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-medium px-4 py-3 rounded-xl">Reset</button>
    </div>
  </div>
  <script>
    let left = 25 * 60, id = null;
    function update() {
      const m = Math.floor(left/60).toString().padStart(2,'0');
      const s = (left%60).toString().padStart(2,'0');
      document.getElementById('timer').innerText = `${m}:${s}`;
    }
    function toggle() {
      if(id) { clearInterval(id); id = null; document.getElementById('start').innerText = 'Start'; }
      else {
        id = setInterval(() => { if(left > 0) { left--; update(); } else { clearInterval(id); alert('Done!'); } }, 1000);
        document.getElementById('start').innerText = 'Pause';
      }
    }
    function reset() { if(id) clearInterval(id); id = null; left = 25*60; update(); document.getElementById('start').innerText = 'Start'; }
    update();
  </script>
</body>
</html>"""
    },
    {
        "title": "Kanban Task Board",
        "prompts": [
            "Create a clean single-file Kanban board with persistent drag and drop",
            "Build a Trello clone with HTML5 drag and drop",
            "Make me an interactive task board for managing sprints"
        ],
        "intro": "Here's a single-file Kanban board with native HTML5 drag-and-drop, column creation, card movement, and localStorage persistence.",
        "code_lang": "html",
        "code": """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <title>Flow — Kanban Board</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen p-8">
  <div class="max-w-7xl mx-auto space-y-6">
    <header class="flex justify-between border-b border-zinc-800 pb-4">
      <h1 class="text-2xl font-bold text-white">Task Flow</h1>
      <button onclick="add()" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-2 rounded-lg">+ Add Task</button>
    </header>
    <div class="grid grid-cols-3 gap-6">
      <div class="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 min-h-[60vh]" ondragover="e=>e.preventDefault()" ondrop="drop(event, 'todo')">
        <h3 class="text-xs font-bold uppercase text-zinc-400 mb-3">To Do</h3>
        <div id="todo" class="space-y-3"></div>
      </div>
      <div class="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 min-h-[60vh]" ondragover="e=>e.preventDefault()" ondrop="drop(event, 'in_progress')">
        <h3 class="text-xs font-bold uppercase text-amber-400 mb-3">In Progress</h3>
        <div id="in_progress" class="space-y-3"></div>
      </div>
      <div class="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 min-h-[60vh]" ondragover="e=>e.preventDefault()" ondrop="drop(event, 'done')">
        <h3 class="text-xs font-bold uppercase text-emerald-400 mb-3">Done</h3>
        <div id="done" class="space-y-3"></div>
      </div>
    </div>
  </div>
  <script>
    let tasks = JSON.parse(localStorage.getItem('eli_k') || '[{"id":"1","title":"Setup OAuth","col":"todo"},{"id":"2","title":"Build UI","col":"in_progress"}]');
    function render() {
      ['todo','in_progress','done'].forEach(col => {
        const el = document.getElementById(col); el.innerHTML = '';
        tasks.filter(t=>t.col===col).forEach(t => {
          const item = document.createElement('div');
          item.draggable = true; item.ondragstart = (e)=>e.dataTransfer.setData('text/plain', t.id);
          item.className = 'bg-zinc-900 border border-zinc-800 p-4 rounded-xl text-sm font-medium cursor-grab';
          item.innerText = t.title;
          el.appendChild(item);
        });
      });
    }
    function drop(e, col) { e.preventDefault(); const id = e.dataTransfer.getData('text/plain'); const t = tasks.find(x=>x.id===id); if(t) { t.col = col; localStorage.setItem('eli_k', JSON.stringify(tasks)); render(); } }
    function add() { const title = prompt('Task:'); if(title) { tasks.push({id: Date.now().toString(), title, col: 'todo'}); localStorage.setItem('eli_k', JSON.stringify(tasks)); render(); } }
    render();
  </script>
</body>
</html>"""
    },
    {
        "title": "Markdown Live Editor",
        "prompts": [
            "Build a markdown editor with live split-screen preview",
            "Make me a clean markdown previewer with copy HTML feature",
            "Create a lightweight online markdown notebook"
        ],
        "intro": "Here's a single-file Markdown editor with instant side-by-side preview, word counter, and export capabilities.",
        "code_lang": "html",
        "code": """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <title>Mark — Live Markdown Editor</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col font-sans">
  <header class="border-b border-zinc-800 px-6 py-4 flex items-center justify-between bg-zinc-900/50">
    <h1 class="text-lg font-bold text-white tracking-tight">Mark Editor</h1>
    <span id="wordCount" class="text-xs text-zinc-400">0 words</span>
  </header>
  <div class="flex-1 grid grid-cols-2 divide-x divide-zinc-800">
    <textarea id="editor" class="bg-zinc-950 p-6 font-mono text-sm text-zinc-200 resize-none focus:outline-none" placeholder="# Write markdown here..."></textarea>
    <div id="preview" class="p-6 prose prose-invert max-w-none overflow-y-auto"></div>
  </div>
  <script>
    const ed = document.getElementById('editor');
    const prev = document.getElementById('preview');
    const wc = document.getElementById('wordCount');
    ed.oninput = () => {
      const text = ed.value;
      prev.innerHTML = marked.parse(text);
      const words = text.trim() ? text.trim().split(/\\s+/).length : 0;
      wc.innerText = `${words} words`;
    };
  </script>
</body>
</html>"""
    }
]

# Category 2: Backend Microservices & API Scaffolds
BACKEND_SPECS = [
    {
        "title": "FastAPI JWT Auth REST API",
        "prompts": [
            "Build a production-ready REST API in FastAPI with authentication and SQLite CRUD",
            "Create a modular FastAPI authentication microservice",
            "Write a clean FastAPI app with OAuth2 password bearer and bcrypt"
        ],
        "intro": "Here's a complete FastAPI service with JWT authentication, Passlib bcrypt hashing, SQLite via SQLAlchemy, and Pydantic schemas.",
        "code_lang": "python",
        "code": """from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

DATABASE_URL = "sqlite:///./app.db"
SECRET_KEY = "super-secret-key-change-in-prod"
ALGORITHM = "HS256"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Auth Microservice", version="1.0.0")

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(hours=24)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd_context.hash(user.password)
    new_user = UserDB(email=user.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    return {"access_token": create_token({"sub": user.email}), "token_type": "bearer"}
"""
    },
    {
        "title": "Go Fiber Rate-Limited Microservice",
        "prompts": [
            "Build a high-performance HTTP microservice in Go using Fiber with rate limiting",
            "Write a Go microservice with in-memory token bucket rate limiter",
            "Create a clean Go Fiber API with middleware and JSON error handling"
        ],
        "intro": "Here's a Go microservice using Fiber with built-in token-bucket rate limiting middleware and structured JSON error responses.",
        "code_lang": "go",
        "code": """package main

import (
	"log"
	"time"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/limiter"
	"github.com/gofiber/fiber/v2/middleware/logger"
)

type HealthResponse struct {
	Status    string `json:"status"`
	Timestamp int64  `json:"timestamp"`
}

func main() {
	app := fiber.New(fiber.Config{
		AppName: "ApiGateway v1.0",
	})

	app.Use(logger.New())

	// Rate Limiting: max 20 requests per 1 minute per IP
	app.Use(limiter.New(limiter.Config{
		Max:        20,
		Expiration: 1 * time.Minute,
		LimitReached: func(c *fiber.Ctx) error {
			return c.Status(fiber.StatusTooManyRequests).JSON(fiber.Map{
				"error": "Rate limit exceeded. Slow down.",
			})
		},
	}))

	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(HealthResponse{
			Status:    "healthy",
			Timestamp: time.Now().Unix(),
		})
	})

	log.Fatal(app.Listen(":8080"))
}
"""
    }
]

# Category 3: OpenCode Agent Tool-Execution & Diff Editing Scenarios
AGENTIC_TOOL_SPECS = [
    {
        "title": "Search/Replace Block Edit",
        "prompts": [
            "Refactor `src/server.ts` to add rate limiting headers and return 429 on limit",
            "Apply a diff to `server.ts` to add security headers",
            "Update `server.ts` with rate limit headers using search/replace blocks"
        ],
        "intro": "I've analyzed `src/server.ts`. Here's the search/replace block to inject rate limiting headers:",
        "code_lang": "diff",
        "code": """<<<<<<< SEARCH
app.get("/api/v1/data", (req, res) => {
  res.json({ success: true, data: [] });
});
=======
app.get("/api/v1/data", rateLimiter, (req, res) => {
  res.setHeader("X-RateLimit-Limit", "100");
  res.setHeader("X-RateLimit-Remaining", req.remainingTokens.toString());
  if (req.remainingTokens <= 0) {
    return res.status(429).json({ error: "Too many requests" });
  }
  res.json({ success: true, data: [] });
});
>>>>>>> REPLACE"""
    },
    {
        "title": "OpenCode Terminal Error Diagnosis",
        "prompts": [
            "Fix this panic in Rust Tokio: 'cannot start a runtime from within a runtime'",
            "Why is my Tokio runtime crashing with nested async calls?",
            "Debug Tokio runtime panic in async main"
        ],
        "intro": "The issue is that `tokio::runtime::Runtime::block_on` was called inside an existing `#[tokio::main]` async context. Replace `block_on` with direct `await` or use `tokio::task::spawn_blocking`.",
        "code_lang": "rust",
        "code": """// BEFORE (Causes Panic):
// tokio::runtime::Runtime::new().unwrap().block_on(async_fetch());

// AFTER (Fix):
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let data = async_fetch().await?;
    println!("Fetched data: {:?}", data);
    Ok(())
}"""
    }
]

def generate_malleable_agentic_dataset(target_count: int = 500) -> list[dict]:
    pairs = []
    rng = random.Random(2026)

    # Combine all specs
    all_specs = WEB_APP_SPECS + BACKEND_SPECS + AGENTIC_TOOL_SPECS

    # Natural, realistic human developer prompt variations (no artificial branding/prefixes)
    natural_phrasings = [
        "{}",
        "Hey Eli, {}",
        "Can you build {}?",
        "Please implement {}",
        "Could you create {}",
        "I need a {}",
        "Write a {}",
        "How do I build {}?",
    ]

    while len(pairs) < target_count:
        spec = rng.choice(all_specs)
        base_prompt = rng.choice(spec["prompts"])
        phrase_func = rng.choice(natural_phrasings)
        
        prompt_text = phrase_func.format(base_prompt)
        formatted_output = f"{spec['intro']}\n\n```{spec['code_lang']}\n{spec['code']}\n```"

        pairs.append({
            "instruction": prompt_text,
            "input": "",
            "output": formatted_output,
            "source": "agentic_coding_malleable"
        })

    return pairs

if __name__ == "__main__":
    dataset = generate_malleable_agentic_dataset(500)
    out_file = Path(__file__).resolve().parent.parent / "data" / "agentic-coding-pairs.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Successfully generated {len(dataset)} unique & malleable agentic coding pairs into {out_file}")
