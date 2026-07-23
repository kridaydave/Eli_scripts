import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = PROJECT_ROOT / "references"
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
BRAND_FILE = PROCESSED_DIR / "brand_uniqueness_annotations.json"
PORT = 5050

IMAGE_EXTS = {".webp", ".png", ".jpg", ".jpeg"}

# Filter specifically for brand explorations, logos, creative design assets
def get_brand_images():
    labels_path = REFERENCES_DIR / "labels.json"
    brand_files = set()
    if labels_path.exists():
        labels = json.loads(labels_path.read_text())
        for item in labels:
            cat = item.get("category", "")
            desc = item.get("description", "").lower()
            fname = item.get("file", "")
            if cat in ("brand-identity", "generative-art", "design-mockup", "hero-section") or "logo" in desc or "brand" in desc or "exploration" in desc:
                brand_files.add(fname)
    
    images = []
    for f in sorted(REFERENCES_DIR.glob("*")):
        if f.suffix.lower() in IMAGE_EXTS and f.is_file():
            if f.name in brand_files or "brand" in f.name.lower() or "logo" in f.name.lower():
                images.append({
                    "id": f.name,
                    "url": f"/img/{f.name}",
                    "rel_path": f.name,
                    "source": "brand_design_explorations"
                })
                
    if not images:
        for f in sorted(REFERENCES_DIR.glob("*"))[:40]:
            if f.suffix.lower() in IMAGE_EXTS and f.is_file():
                images.append({
                    "id": f.name,
                    "url": f"/img/{f.name}",
                    "rel_path": f.name,
                    "source": "main_references"
                })
    return images

def load_brand_annotations():
    if BRAND_FILE.exists():
        try:
            return json.loads(BRAND_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_brand_annotations(data):
    BRAND_FILE.write_text(json.dumps(data, indent=2))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="h-full bg-zinc-950 text-zinc-100">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Eli Brand & Design Identity Studio</title>
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
      <div class="w-3 h-3 rounded-full bg-amber-500 animate-pulse"></div>
      <h1 class="font-bold text-lg text-white tracking-tight">Eli Brand & Design Identity Studio</h1>
      <span class="text-xs bg-zinc-800 text-amber-400 px-2.5 py-1 rounded-full font-mono border border-amber-900/50" id="counter">0 / 0</span>
    </div>
    
    <div class="flex items-center gap-4">
      <button id="prevBtn" onclick="navigate(-1)" class="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold rounded-lg border border-zinc-700 transition">
        ← Previous (Key: ←)
      </button>
      <button id="nextBtn" onclick="navigate(1)" class="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold rounded-lg border border-zinc-700 transition">
        Next (Key: →) →
      </button>
      <button onclick="saveCurrent()" class="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-xs font-bold text-white rounded-lg transition shadow-lg shadow-amber-900/40">
        Save Brand Answer (Ctrl+Enter)
      </button>
    </div>
  </header>

  <!-- Main Workspace -->
  <main class="flex-1 relative flex overflow-hidden">
    
    <!-- Full-Screen Image Viewport -->
    <div class="flex-1 flex items-center justify-center p-4 relative bg-black/70 overflow-auto no-scrollbar">
      <img id="activeImg" src="" alt="Brand Asset" class="max-h-[calc(100vh-4rem)] max-w-full object-contain rounded-lg shadow-2xl transition-all duration-200">
    </div>

    <!-- Sidebar Annotation Panel -->
    <div class="w-[480px] bg-zinc-900/95 border-l border-zinc-800 p-6 flex flex-col justify-between z-10 backdrop-blur-lg">
      <div class="space-y-4 flex-1 flex flex-col">
        <div>
          <span id="imgSource" class="text-[10px] font-mono uppercase tracking-wider text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/50">Brand & Design Asset</span>
          <h2 id="imgTitle" class="text-sm font-medium text-zinc-300 mt-2 truncate">Image File</h2>
        </div>

        <div class="flex-1 flex flex-col space-y-2">
          <label class="text-xs font-bold text-amber-300 flex items-center justify-between">
            <span>Brand & Design Uniqueness Critique:</span>
          </label>
          <p class="text-[11px] text-zinc-400 leading-normal">
            Explain what makes this brand/design exploration unique (e.g., logo geometry, color palette harmony, typography balance, creative direction vs generic templates).
          </p>
          <textarea id="answerText" 
            placeholder="Type your brand & design identity critique here...&#10;&#10;E.g., The logo uses an asymmetrical 9x9 grid layout with deep indigo backdrop, creating high-contrast brand recognition..." 
            class="flex-1 w-full bg-zinc-950 border border-amber-900/50 rounded-xl p-4 text-xs font-mono text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 resize-none transition-all leading-relaxed"></textarea>
        </div>
      </div>

      <!-- Action Footer -->
      <div class="pt-4 border-t border-zinc-800/80 flex items-center justify-between">
        <span id="saveStatus" class="text-xs text-zinc-400 font-mono">Ready</span>
        <button onclick="saveCurrent()" class="px-5 py-2 bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white rounded-lg transition">
          Save & Next
        </button>
      </div>
    </div>
  </main>

  <script>
    let images = [];
    let annotations = {};
    let currentIndex = 0;

    async function init() {
      const resp = await fetch('/api/data');
      const data = await resp.json();
      images = data.images;
      annotations = data.annotations;
      
      if (images.length > 0) {
        renderImage(0);
      }
    }

    function renderImage(index) {
      if (index < 0 || index >= images.length) return;
      currentIndex = index;
      const img = images[currentIndex];
      
      document.getElementById('activeImg').src = encodeURI(img.url);
      document.getElementById('imgTitle').innerText = img.rel_path;
      document.getElementById('imgSource').innerText = img.source;
      document.getElementById('counter').innerText = `${currentIndex + 1} / ${images.length}`;
      
      const savedAnswer = annotations[img.id] || "";
      document.getElementById('answerText').value = savedAnswer;
      document.getElementById('saveStatus').innerText = savedAnswer ? "✓ Saved Brand Critique" : "Unannotated";
      document.getElementById('saveStatus').className = savedAnswer ? "text-xs text-amber-400 font-mono font-semibold" : "text-xs text-zinc-500 font-mono";
    }

    async function saveCurrent() {
      const img = images[currentIndex];
      const answer = document.getElementById('answerText').value;
      
      document.getElementById('saveStatus').innerText = "Saving...";
      
      const resp = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: img.id, answer: answer })
      });
      
      if (resp.ok) {
        annotations[img.id] = answer;
        document.getElementById('saveStatus').innerText = "✓ Saved!";
        document.getElementById('saveStatus').className = "text-xs text-amber-400 font-mono font-semibold";
        setTimeout(() => navigate(1), 300);
      } else {
        document.getElementById('saveStatus').innerText = "Error saving";
      }
    }

    function navigate(delta) {
      const nextIndex = currentIndex + delta;
      if (nextIndex >= 0 && nextIndex < images.length) {
        renderImage(nextIndex);
      }
    }

    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'TEXTAREA') {
        if (e.ctrlKey && e.key === 'Enter') {
          e.preventDefault();
          saveCurrent();
        }
        return;
      }
      if (e.key === 'ArrowLeft') {
        navigate(-1);
      } else if (e.key === 'ArrowRight') {
        navigate(1);
      }
    });

    init();
  </script>
</body>
</html>
"""

class TasteStudioHandler(http.server.BaseHTTPRequestHandler):
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
            res = json.dumps({
                "images": get_brand_images(),
                "annotations": load_brand_annotations()
            })
            self.wfile.write(res.encode("utf-8"))
        elif parsed.path.startswith("/img/"):
            from urllib.parse import unquote
            rel_img = unquote(parsed.path.replace("/img/", ""))
            target_path = REFERENCES_DIR / rel_img
            if target_path.exists() and target_path.is_file():
                self.send_response(200)
                ext = target_path.suffix.lower()
                mime = "image/webp" if ext == ".webp" else ("image/png" if ext == ".png" else "image/jpeg")
                self.send_header("Content-Type", mime)
                self.end_headers()
                self.wfile.write(target_path.read_bytes())
            else:
                self.send_error(404, "Image not found")
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/save":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode("utf-8"))
            
            img_id = req.get("id")
            answer = req.get("answer", "").strip()
            
            annotations = load_brand_annotations()
            if answer:
                annotations[img_id] = answer
            elif img_id in annotations:
                del annotations[img_id]
                
            save_brand_annotations(annotations)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            res = json.dumps({"status": "success", "total_annotated": len(annotations)})
            self.wfile.write(res.encode("utf-8"))
        else:
            self.send_error(404, "Not found")

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ReusableTCPServer(("0.0.0.0", PORT), TasteStudioHandler) as httpd:
        print(f"Eli Brand & Design Identity Studio running at http://localhost:{PORT}")
        httpd.serve_forever()
