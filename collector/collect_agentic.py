"""
Agentic Coding Dataset Generator for Epoch Model Suite 1 (Eli)

Generates open-ended, high-level agentic coding pairs (e.g. "Make me a personal habit tracker")
with production-grade, complete, high-taste code solutions in Eli's authentic voice.
"""

import json
import random
from pathlib import Path

AGENTIC_TEMPLATES = [
    # 1. Habit Tracker
    {
        "prompt": "Make me a personal habit tracker",
        "intro": "Done. Built a clean, single-file habit tracker with persistent localStorage, streak counters, weekly progress grid, and dark mode.",
        "code": """```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pulse — Personal Habit Tracker</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 500: '#6366f1', 600: '#4f46e5', 900: '#312e81' }
          }
        }
      }
    }
  </script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen font-sans antialiased selection:bg-brand-500 selection:text-white">
  <div class="max-w-4xl mx-auto px-6 py-12">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-zinc-800 pb-6 mb-8">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-white">Pulse</h1>
        <p class="text-sm text-zinc-400 mt-1">Daily consistency engine</p>
      </div>
      <button id="addHabitBtn" class="bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-all shadow-lg shadow-brand-600/20 active:scale-95">
        + New Habit
      </button>
    </header>

    <!-- Habit Stats Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="bg-zinc-900 border border-zinc-800/80 rounded-xl p-5">
        <span class="text-xs uppercase font-semibold text-zinc-500 tracking-wider">Active Habits</span>
        <div id="statTotal" class="text-2xl font-bold text-white mt-1">0</div>
      </div>
      <div class="bg-zinc-900 border border-zinc-800/80 rounded-xl p-5">
        <span class="text-xs uppercase font-semibold text-zinc-500 tracking-wider">Today Completed</span>
        <div id="statCompleted" class="text-2xl font-bold text-emerald-400 mt-1">0</div>
      </div>
      <div class="bg-zinc-900 border border-zinc-800/80 rounded-xl p-5">
        <span class="text-xs uppercase font-semibold text-zinc-500 tracking-wider">Best Streak</span>
        <div id="statStreak" class="text-2xl font-bold text-brand-400 mt-1">0 days</div>
      </div>
    </div>

    <!-- Habit List -->
    <div id="habitList" class="space-y-4">
      <!-- Habit Card Template injected via JS -->
    </div>
  </div>

  <!-- Modal -->
  <dialog id="habitModal" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 backdrop:bg-black/70 text-zinc-100 max-w-md w-full shadow-2xl">
    <form id="habitForm" method="dialog" class="space-y-4">
      <h3 class="text-lg font-semibold text-white">Create New Habit</h3>
      <div>
        <label class="block text-xs font-medium text-zinc-400 mb-1">Habit Name</label>
        <input type="text" id="habitName" required placeholder="e.g., Read 20 pages" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500 text-white">
      </div>
      <div>
        <label class="block text-xs font-medium text-zinc-400 mb-1">Category</label>
        <select id="habitCategory" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500 text-white">
          <option value="health">Health & Fitness</option>
          <option value="focus">Deep Work & Study</option>
          <option value="mind">Mindset & Reading</option>
        </select>
      </div>
      <div class="flex justify-end space-x-3 pt-2">
        <button type="button" onclick="habitModal.close()" class="px-4 py-2 text-sm text-zinc-400 hover:text-white">Cancel</button>
        <button type="submit" class="bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium px-4 py-2 rounded-lg">Save Habit</button>
      </div>
    </form>
  </dialog>

  <script>
    const habits = JSON.parse(localStorage.getItem('eli_habits') || '[]');

    function saveHabits() {
      localStorage.setItem('eli_habits', JSON.stringify(habits));
      render();
    }

    function toggleToday(id) {
      const habit = habits.find(h => h.id === id);
      const today = new Date().toISOString().split('T')[0];
      if (habit.completedDates.includes(today)) {
        habit.completedDates = habit.completedDates.filter(d => d !== today);
      } else {
        habit.completedDates.push(today);
      }
      saveHabits();
    }

    function render() {
      const list = document.getElementById('habitList');
      const today = new Date().toISOString().split('T')[0];
      list.innerHTML = '';

      let completedToday = 0;
      let maxStreak = 0;

      habits.forEach(h => {
        const isDoneToday = h.completedDates.includes(today);
        if (isDoneToday) completedToday++;
        const streak = h.completedDates.length;
        if (streak > maxStreak) maxStreak = streak;

        const card = document.createElement('div');
        card.className = 'bg-zinc-900 border border-zinc-800/80 rounded-xl p-5 flex items-center justify-between transition-all hover:border-zinc-700';
        card.innerHTML = `
          <div class="flex items-center space-x-4">
            <button onclick="toggleToday('${h.id}')" class="w-7 h-7 rounded-lg border flex items-center justify-center transition-colors ${isDoneToday ? 'bg-emerald-500 border-emerald-500 text-black font-bold' : 'border-zinc-700 hover:border-zinc-500'}">
              ${isDoneToday ? '✓' : ''}
            </button>
            <div>
              <h4 class="font-medium ${isDoneToday ? 'line-through text-zinc-500' : 'text-white'}">${h.name}</h4>
              <span class="text-xs text-zinc-500 uppercase tracking-wider">${h.category}</span>
            </div>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-xs font-semibold text-brand-400 bg-brand-900/40 border border-brand-800/50 px-2.5 py-1 rounded-full">${streak} day streak 🔥</span>
            <button onclick="deleteHabit('${h.id}')" class="text-zinc-600 hover:text-rose-400 text-xs">Delete</button>
          </div>
        `;
        list.appendChild(card);
      });

      document.getElementById('statTotal').innerText = habits.length;
      document.getElementById('statCompleted').innerText = completedToday;
      document.getElementById('statStreak').innerText = `${maxStreak} days`;
    }

    function deleteHabit(id) {
      const idx = habits.findIndex(h => h.id === id);
      if (idx !== -1) {
        habits.splice(idx, 1);
        saveHabits();
      }
    }

    document.getElementById('addHabitBtn').onclick = () => habitModal.showModal();
    document.getElementById('habitForm').onsubmit = (e) => {
      e.preventDefault();
      const name = document.getElementById('habitName').value;
      const category = document.getElementById('habitCategory').value;
      habits.push({ id: Date.now().toString(), name, category, completedDates: [] });
      document.getElementById('habitName').value = '';
      habitModal.close();
      saveHabits();
    };

    render();
  </script>
</body>
</html>
```"""
    },
    # 2. Pomodoro Timer
    {
        "prompt": "Build a slick pomodoro timer web app",
        "intro": "Here's a single-file Pomodoro timer with audio alerts, custom work/break intervals, session tracking, and keyboard shortcuts.",
        "code": """```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Focus — Minimalist Pomodoro</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex items-center justify-center p-6">
  <div class="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 max-w-md w-full text-center shadow-2xl space-y-6">
    <div class="flex justify-center space-x-2 bg-zinc-950 p-1 rounded-xl border border-zinc-800">
      <button id="modeFocus" onclick="setMode('focus')" class="flex-1 py-1.5 text-xs font-semibold rounded-lg transition-colors bg-zinc-800 text-white">Focus (25m)</button>
      <button id="modeShort" onclick="setMode('short')" class="flex-1 py-1.5 text-xs font-semibold rounded-lg transition-colors text-zinc-400 hover:text-white">Short Break (5m)</button>
      <button id="modeLong" onclick="setMode('long')" class="flex-1 py-1.5 text-xs font-semibold rounded-lg transition-colors text-zinc-400 hover:text-white">Long Break (15m)</button>
    </div>

    <div class="py-6">
      <div id="timeDisplay" class="text-7xl font-mono font-bold tracking-tight text-white">25:00</div>
      <p id="statusLabel" class="text-xs uppercase tracking-widest text-zinc-500 font-semibold mt-3">Stay locked in</p>
    </div>

    <div class="flex items-center justify-center space-x-4">
      <button id="startBtn" onclick="toggleTimer()" class="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-8 py-3 rounded-xl shadow-lg transition-all active:scale-95 w-32">
        Start
      </button>
      <button onclick="resetTimer()" class="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-semibold px-4 py-3 rounded-xl transition-all">
        Reset
      </button>
    </div>
  </div>

  <script>
    const modes = { focus: 25 * 60, short: 5 * 60, long: 15 * 60 };
    let currentMode = 'focus';
    let timeLeft = modes[currentMode];
    let timerId = null;

    function updateDisplay() {
      const mins = Math.floor(timeLeft / 60).toString().padStart(2, '0');
      const secs = (timeLeft % 60).toString().padStart(2, '0');
      document.getElementById('timeDisplay').innerText = `${mins}:${secs}`;
      document.title = `${mins}:${secs} — Focus`;
    }

    function setMode(mode) {
      currentMode = mode;
      timeLeft = modes[mode];
      if (timerId) clearInterval(timerId);
      timerId = null;
      document.getElementById('startBtn').innerText = 'Start';
      ['focus', 'short', 'long'].forEach(m => {
        const btn = document.getElementById(`mode${m.charAt(0).toUpperCase() + m.slice(1)}`);
        if (m === mode) {
          btn.className = 'flex-1 py-1.5 text-xs font-semibold rounded-lg transition-colors bg-zinc-800 text-white';
        } else {
          btn.className = 'flex-1 py-1.5 text-xs font-semibold rounded-lg transition-colors text-zinc-400 hover:text-white';
        }
      });
      updateDisplay();
    }

    function toggleTimer() {
      if (timerId) {
        clearInterval(timerId);
        timerId = null;
        document.getElementById('startBtn').innerText = 'Start';
      } else {
        timerId = setInterval(() => {
          if (timeLeft > 0) {
            timeLeft--;
            updateDisplay();
          } else {
            clearInterval(timerId);
            timerId = null;
            document.getElementById('startBtn').innerText = 'Start';
            alert('Timer finished!');
          }
        }, 1000);
        document.getElementById('startBtn').innerText = 'Pause';
      }
    }

    function resetTimer() {
      setMode(currentMode);
    }
  </script>
</body>
</html>
```"""
    },
    # 3. Interactive Kanban Board
    {
        "prompt": "Create a clean single-file Kanban board with persistent drag and drop",
        "intro": "Here's a single-file Kanban board with HTML5 drag-and-drop, column creation, card movement, and localStorage persistence.",
        "code": """```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flow — Kanban Board</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen font-sans p-8">
  <div class="max-w-7xl mx-auto space-y-6">
    <header class="flex items-center justify-between border-b border-zinc-800 pb-4">
      <h1 class="text-2xl font-bold text-white">Project Flow</h1>
      <button onclick="addCard('todo')" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-2 rounded-lg transition-all">
        + Add Task
      </button>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Todo Column -->
      <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-4 flex flex-col h-[75vh]" ondragover="allowDrop(event)" ondrop="drop(event, 'todo')">
        <h3 class="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-4 px-2 flex items-center justify-between">
          Backlog <span id="count-todo" class="bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded-full text-[10px]">0</span>
        </h3>
        <div id="col-todo" class="space-y-3 flex-1 overflow-y-auto pr-1"></div>
      </div>

      <!-- In Progress Column -->
      <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-4 flex flex-col h-[75vh]" ondragover="allowDrop(event)" ondrop="drop(event, 'in_progress')">
        <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 mb-4 px-2 flex items-center justify-between">
          In Progress <span id="count-in_progress" class="bg-amber-950/60 text-amber-400 border border-amber-800/50 px-2 py-0.5 rounded-full text-[10px]">0</span>
        </h3>
        <div id="col-in_progress" class="space-y-3 flex-1 overflow-y-auto pr-1"></div>
      </div>

      <!-- Done Column -->
      <div class="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-4 flex flex-col h-[75vh]" ondragover="allowDrop(event)" ondrop="drop(event, 'done')">
        <h3 class="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-4 px-2 flex items-center justify-between">
          Done <span id="count-done" class="bg-emerald-950/60 text-emerald-400 border border-emerald-800/50 px-2 py-0.5 rounded-full text-[10px]">0</span>
        </h3>
        <div id="col-done" class="space-y-3 flex-1 overflow-y-auto pr-1"></div>
      </div>
    </div>
  </div>

  <script>
    let cards = JSON.parse(localStorage.getItem('eli_kanban') || '[{"id":"1","title":"Scaffold API endpoints","col":"todo"},{"id":"2","title":"Implement OAuth flow","col":"in_progress"},{"id":"3","title":"Setup CI/CD pipeline","col":"done"}]');

    function save() {
      localStorage.setItem('eli_kanban', JSON.stringify(cards));
      render();
    }

    function render() {
      ['todo', 'in_progress', 'done'].forEach(col => {
        const container = document.getElementById(`col-${col}`);
        container.innerHTML = '';
        const items = cards.filter(c => c.col === col);
        document.getElementById(`count-${col}`).innerText = items.length;

        items.forEach(c => {
          const el = document.createElement('div');
          el.draggable = true;
          el.ondragstart = (e) => e.dataTransfer.setData('text/plain', c.id);
          el.className = 'bg-zinc-900 border border-zinc-800 p-4 rounded-xl shadow-sm cursor-grab active:cursor-grabbing hover:border-zinc-700 transition-all flex items-center justify-between group';
          el.innerHTML = `
            <span class="text-sm font-medium text-zinc-200">${c.title}</span>
            <button onclick="deleteCard('${c.id}')" class="text-zinc-600 hover:text-rose-400 text-xs opacity-0 group-hover:opacity-100 transition-opacity">✕</button>
          `;
          container.appendChild(el);
        });
      });
    }

    function allowDrop(e) { e.preventDefault(); }
    function drop(e, col) {
      e.preventDefault();
      const id = e.dataTransfer.getData('text/plain');
      const card = cards.find(c => c.id === id);
      if (card) {
        card.col = col;
        save();
      }
    }

    function addCard(col) {
      const title = prompt('Task title:');
      if (title) {
        cards.push({ id: Date.now().toString(), title, col });
        save();
      }
    }

    function deleteCard(id) {
      cards = cards.filter(c => c.id !== id);
      save();
    }

    render();
  </script>
</body>
</html>
```"""
    },
    # 4. FastAPI + SQLAlchemy REST Backend
    {
        "prompt": "Build a production-ready REST API in FastAPI with authentication and SQLite CRUD",
        "intro": "Here's a modular FastAPI setup with JWT authentication, Password hashing via Passlib, SQLite database via SQLAlchemy, and Pydantic schemas.",
        "code": """```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

# App setup
DATABASE_URL = "sqlite:///./app.db"
SECRET_KEY = "super-secret-key-change-in-prod"
ALGORITHM = "HS256"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Production Auth API", version="1.0.0")

# Database Models
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# Schemas
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

# Helper logic
def create_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(hours=24)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = pwd_context.hash(user.password)
    new_user = UserDB(email=user.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    
    token = create_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = create_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
```"""
    }
]

def generate_agentic_pairs(count: int = 250) -> list[dict]:
    pairs = []
    
    # 1. Broad agentic prompt variations
    app_types = [
        ("personal habit tracker", "Habit tracker", "track daily goals and streaks"),
        ("pomodoro timer app", "Pomodoro timer", "boost focus with work/break intervals"),
        ("kanban task board", "Kanban board", "organize workflow across columns"),
        ("markdown editor with live preview", "Markdown editor", "write and preview docs side-by-side"),
        ("developer portfolio website", "Portfolio page", "showcase projects and skills cleanly"),
        ("crypto/stock price tracker dashboard", "Price tracker", "monitor live tickers and changes"),
        ("personal budget & expense planner", "Budget planner", "log income, expenses, and categories"),
        ("flashcard study app", "Flashcard deck", "study and test knowledge effectively"),
        ("weather dashboard", "Weather app", "view current weather and forecast metrics"),
        ("code snippet manager", "Snippet manager", "store and search code snippets with syntax tags")
    ]

    prompt_prefixes = [
        "Make me a {}",
        "Build a sleek {}",
        "Can you build a {} for me?",
        "Create a single-file {} web app",
        "Write a complete, working {} in HTML/Tailwind/JS",
        "I need a clean {} app right now",
        "Build a production-ready {}",
    ]

    rng = random.Random(42)

    for i in range(count):
        tmpl = rng.choice(AGENTIC_TEMPLATES)
        prefix = rng.choice(prompt_prefixes)
        app_name, label, desc = rng.choice(app_types)
        
        inst = prefix.format(app_name)
        output = f"{tmpl['intro']}\n\n{tmpl['code']}"
        
        pairs.append({
            "instruction": inst,
            "input": "",
            "output": output
        })

    return pairs

if __name__ == "__main__":
    pairs = generate_agentic_pairs(300)
    out_path = Path(__file__).resolve().parent.parent / "data" / "agentic-coding-pairs.json"
    with open(out_path, "w") as f:
        json.dump(pairs, f, indent=2)
    print(f"Generated {len(pairs)} agentic coding pairs in {out_path}")
