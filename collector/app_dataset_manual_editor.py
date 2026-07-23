import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MASTER_DATASET_FILE = PROCESSED_DIR / "training-data-eli-curated.jsonl"
PORT = 5050

# Load master dataset into memory for manual reviewing/editing
def load_dataset():
    records = []
    if MASTER_DATASET_FILE.exists():
        with open(MASTER_DATASET_FILE, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    try:
                        obj = json.loads(line)
                        records.append({
                            "idx": idx,
                            "id": obj.get("id", f"record-{idx}"),
                            "data": obj
                        })
                    except Exception:
                        pass
    return records

def save_dataset(records):
    with open(MASTER_DATASET_FILE, "w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item["data"], ensure_ascii=False) + "\n")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="h-full bg-zinc-950 text-zinc-100">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Eli Dataset Manual Editor Studio</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
  </style>
</head>
<body class="h-full flex flex-col overflow-hidden bg-zinc-950">

  <!-- Top Bar Header -->
  <header class="h-14 bg-zinc-900/90 border-b border-zinc-800 flex items-center justify-between px-6 z-20 backdrop-blur-md">
    <div class="flex items-center gap-3">
      <div class="w-3 h-3 rounded-full bg-indigo-500 animate-pulse"></div>
      <h1 class="font-bold text-lg text-white tracking-tight">Eli Dataset Manual Studio</h1>
      <span class="text-xs bg-zinc-800 text-indigo-400 px-2.5 py-1 rounded-full font-mono border border-indigo-900/50" id="counter">0 / 0</span>
    </div>
    
    <div class="flex items-center gap-4">
      <button onclick="navigate(-1)" class="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold rounded-lg border border-zinc-700 transition">
        ← Previous (Key: ←)
      </button>
      <button onclick="navigate(1)" class="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold rounded-lg border border-zinc-700 transition">
        Next (Key: →) →
      </button>
      <button onclick="saveCurrentRecord()" class="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white rounded-lg transition shadow-lg shadow-indigo-950">
        Save Changes (Ctrl+Enter)
      </button>
    </div>
  </header>

  <!-- Main Workspace -->
  <main class="flex-1 flex overflow-hidden">
    
    <!-- User Prompt Column -->
    <div class="flex-1 border-r border-zinc-800 p-6 flex flex-col space-y-3 bg-zinc-950">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">Human Prompt</span>
        <span id="recordMeta" class="text-[10px] font-mono text-zinc-500">Metadata</span>
      </div>
      <textarea id="humanInput" class="flex-1 w-full bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-xs font-mono text-zinc-100 focus:outline-none focus:border-indigo-500 resize-none transition leading-relaxed"></textarea>
    </div>

    <!-- GPT Assistant Response Column -->
    <div class="flex-1 p-6 flex flex-col space-y-3 bg-zinc-950">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">GPT Assistant Response (Clean `_000X` suffixes / boilerplate here)</span>
        <span id="saveStatus" class="text-xs text-zinc-500 font-mono">Ready</span>
      </div>
      <textarea id="gptOutput" class="flex-1 w-full bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-xs font-mono text-zinc-100 focus:outline-none focus:border-emerald-500 resize-none transition leading-relaxed"></textarea>
    </div>
  </main>

  <script>
    let records = [];
    let currentIndex = 0;

    async function init() {
      const resp = await fetch('/api/data');
      records = await resp.json();
      if (records.length > 0) {
        renderRecord(0);
      }
    }

    function renderRecord(index) {
      if (index < 0 || index >= records.length) return;
      currentIndex = index;
      const rec = records[currentIndex];
      const convs = rec.data.conversations || [];
      
      let humanVal = "";
      let gptVal = "";
      
      convs.forEach(c => {
        if (c.from === "human" || c.role === "user") humanVal = c.value || c.content || "";
        if (c.from === "gpt" || c.role === "assistant") gptVal = c.value || c.content || "";
      });
      
      document.getElementById('humanInput').value = humanVal;
      document.getElementById('gptOutput').value = gptVal;
      document.getElementById('counter').innerText = `${currentIndex + 1} / ${records.length}`;
      document.getElementById('recordMeta').innerText = `ID: ${rec.id}`;
      document.getElementById('saveStatus').innerText = "Ready";
      document.getElementById('saveStatus').className = "text-xs text-zinc-500 font-mono";
    }

    async function saveCurrentRecord() {
      const rec = records[currentIndex];
      const humanVal = document.getElementById('humanInput').value;
      const gptVal = document.getElementById('gptOutput').value;
      
      document.getElementById('saveStatus').innerText = "Saving...";
      
      const resp = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idx: rec.idx,
          human: humanVal,
          gpt: gptVal
        })
      });
      
      if (resp.ok) {
        document.getElementById('saveStatus').innerText = "✓ Saved!";
        document.getElementById('saveStatus').className = "text-xs text-emerald-400 font-mono font-semibold";
        setTimeout(() => navigate(1), 300);
      } else {
        document.getElementById('saveStatus').innerText = "Error saving";
      }
    }

    function navigate(delta) {
      const nextIndex = currentIndex + delta;
      if (nextIndex >= 0 && nextIndex < records.length) {
        renderRecord(nextIndex);
      }
    }

    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        saveCurrentRecord();
      } else if (e.target.tagName !== 'TEXTAREA') {
        if (e.key === 'ArrowLeft') navigate(-1);
        if (e.key === 'ArrowRight') navigate(1);
      }
    });

    init();
  </script>
</body>
</html>
"""

class ManualEditorHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            records = load_dataset()
            self.wfile.write(json.dumps(records).encode("utf-8"))
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/save":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode("utf-8"))
            
            idx = req.get("idx")
            human_val = req.get("human", "").strip()
            gpt_val = req.get("gpt", "").strip()
            
            records = load_dataset()
            for r in records:
                if r["idx"] == idx:
                    r["data"]["conversations"] = [
                        {"role": "user", "content": human_val},
                        {"role": "assistant", "content": gpt_val}
                    ]
                    break
            save_dataset(records)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode("utf-8"))
        else:
            self.send_error(404, "Not found")

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ReusableTCPServer(("0.0.0.0", PORT), ManualEditorHandler) as httpd:
        print(f"Eli Manual Dataset Editor running at http://localhost:{PORT}")
        httpd.serve_forever()
