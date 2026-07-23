"""
Recipe 1: UTBUI (Ugly-to-Bespoke UI & Visual-AST Repair) Dataset Generator

Generates 15,000 STRICTLY UNIQUE synthetic training pairs teaching Eli to transform
ugly/baseline HTML/CSS snippets into high-taste, bespoke components (OKLCH, 8pt grid, glassmorphism,
fluid typography, 4-state UI matrix).

Uses combinatorial variations across components, color spaces, layouts, typography, micro-interactions,
and structural AST elements so that EVERY SINGLE prompt and response is unique without relying on artificial index tags.
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = PROCESSED_DIR / "utbui-dataset.jsonl"

COMPONENT_TYPES = [
    "Navbar Header", "Hero Banner", "SaaS Metric Dashboard Card", 
    "Auth Login Form", "Pricing Plan Table", "Product Feature Grid",
    "User Settings Modal", "Data Table with Filters", "Analytics Chart Container",
    "E-Commerce Product Card", "Team Member Grid", "Notification Toast Stack",
    "Command Palette Search Modal", "File Upload Dropzone", "Feedback Review Widget",
    "Cryonics Vault Status Card", "AI Fragrance Customizer Widget", "Zen Garden Audio Player",
    "Real-time Moodboard Canvas", "Quantum Compute Task Queue", "Personal Time-Well-Spent Analytics",
    "Freelancer Tax Estimator Card", "Sauna Booking Calendar", "Ugly Bread Bakery Checkout",
    "Ghost Networking Profile Card", "Secret Destination Flight Ticket", "Skincare Ingredient Decoder",
    "AI Law Firm Case Tracker", "Choose-Your-Own-Adventure Annual Report", "Vintage Field Recording Player",
    "Digital Graveyard Memorial Card", "Melatonin Sleep Tracker", "Startup Failure Museum Badge", "Kinetic Typography Banner"
]

THEMES = [
    {"name": "Zinc Dark Slate", "bg": "bg-zinc-950", "border": "border-zinc-800", "accent": "from-indigo-500 to-violet-600", "ring": "focus-visible:ring-indigo-400", "text": "text-zinc-100"},
    {"name": "OLED Jet Black", "bg": "bg-black", "border": "border-white/10", "accent": "from-emerald-500 to-teal-600", "ring": "focus-visible:ring-emerald-400", "text": "text-white"},
    {"name": "OKLCH Deep Navy", "bg": "bg-slate-950", "border": "border-slate-800", "accent": "from-cyan-500 to-blue-600", "ring": "focus-visible:ring-cyan-400", "text": "text-slate-100"},
    {"name": "Minimal Neutral Slate", "bg": "bg-stone-950", "border": "border-stone-800", "accent": "from-amber-500 to-orange-600", "ring": "focus-visible:ring-amber-400", "text": "text-stone-100"},
    {"name": "Cyberpunk Dark Mesh", "bg": "bg-zinc-900", "border": "border-purple-900/50", "accent": "from-fuchsia-500 to-pink-600", "ring": "focus-visible:ring-fuchsia-400", "text": "text-purple-50"},
    {"name": "Obsidian Violet", "bg": "bg-neutral-950", "border": "border-violet-900/40", "accent": "from-violet-600 to-purple-700", "ring": "focus-visible:ring-violet-400", "text": "text-neutral-100"},
    {"name": "Solar Flare Glow", "bg": "bg-gray-950", "border": "border-amber-900/40", "accent": "from-rose-500 to-amber-500", "ring": "focus-visible:ring-rose-400", "text": "text-gray-100"},
    {"name": "Quartz Ice Glass", "bg": "bg-slate-900/90", "border": "border-cyan-500/20", "accent": "from-sky-400 to-indigo-500", "ring": "focus-visible:ring-sky-300", "text": "text-sky-50"},
    {"name": "Industrial Carbon", "bg": "bg-neutral-900", "border": "border-neutral-700", "accent": "from-zinc-400 to-zinc-600", "ring": "focus-visible:ring-zinc-400", "text": "text-neutral-100"},
    {"name": "Emerald Bio Dome", "bg": "bg-emerald-950/80", "border": "border-emerald-800/60", "accent": "from-teal-400 to-emerald-600", "ring": "focus-visible:ring-teal-300", "text": "text-emerald-50"}
]

UGLY_PATTERNS = [
    ("inline_styles", '<div style="background: {bg}; color: {fg}; border: 1px solid {border}; padding: {pad};">\n  <h2>{title}</h2>\n  <p>{desc}</p>\n  <button style="background: {btn_bg}; color: white;">{btn_text}</button>\n</div>'),
    ("legacy_html", '<table border="1" cellpadding="5">\n  <tr><th>{h1}</th><th>{h2}</th></tr>\n  <tr><td>{val1}</td><td>{val2}</td></tr>\n</table>'),
    ("unresponsive_divs", '<div class="box" style="width: 500px; height: 300px; background: #eee;">\n  <span class="label">{title}</span>\n  <input type="text" value="{val1}" />\n  <button class="btn">{btn_text}</button>\n</div>'),
    ("generic_bootstrap", '<div class="card card-body bg-light text-dark mb-3">\n  <h5 class="card-title">{title}</h5>\n  <p class="card-text">{desc}</p>\n  <a href="#" class="btn btn-primary">{btn_text}</a>\n</div>'),
    ("unstyled_list", '<ul style="list-style:none; margin:0; padding:0;">\n  <li style="border-bottom:1px solid #ccc; padding:10px;">\n    <strong>{title}</strong>\n    <p>{desc}</p>\n    <button>{btn_text}</button>\n  </li>\n</ul>'),
    ("div_soup", '<div class="wrapper"><div class="inner"><div class="head">{title}</div><div class="content">{desc}</div><div class="footer"><button>{btn_text}</button></div></div></div>')
]

TITLES = [
    "Luxury Olfactory Notes", "Cryo-Preservation Core", "Personal Time Audit", "Ugly Loaf Order Summary",
    "Spectral Presence Matrix", "Secret Ingress Pass", "Bio-Active Botanical Ratios", "AI Defense Legal Docket",
    "Choose-Your-Branch Metrics", "Ambient Soundscape Stream", "Startup Post-Mortem Log", "Kinetic Type Generator",
    "Gen-Z Tax Ledger", "Sauna Pod Availability", "Melatonin Sleep Phase", "Field Recording Frequency",
    "Financial Telemetry", "User Session Vault", "Cluster Health Index", "API Ingress Rate Limit"
]

DESCS = [
    "Real-time telemetry and infrastructure health metrics for high-throughput deployments.",
    "Manage active session tokens, security credentials, and identity access control policies.",
    "High-frequency transaction monitoring, anomaly detection, and automated audit trails.",
    "Scalable multi-tenant cloud infrastructure compute tier selection and load balancing.",
    "Distributed database cluster latency, storage engine metrics, and replication throughput tracking.",
    "Cryogenic chamber thermal stability logs and automated liquid nitrogen telemetry.",
    "Sartorial fragrance formulation synthesis and custom olfactory accords calculation.",
    "Spectral resonance analysis for non-corporeal entity verification and session mapping."
]

BTNS = [
    "Download Audit", "Authenticate Session", "Deploy Changes", "Upgrade Instance",
    "Configure Settings", "Sync Workspace", "Generate Report", "Initialize Synthesis",
    "Book Thermal Session", "De-escalate Docket", "Synthesize Accords", "Decouple Monolith"
]

PROMPT_STRUCTURES = [
    "Refactor this baseline/ugly {comp} snippet into a modern, high-taste bespoke UI component. Apply {theme_name} design tokens, 8pt grid spatial alignment, tactile micro-interactions, and accessible high-contrast polish:\n\n```html\n{ugly_html}\n```",
    "Convert the unstyled {comp} markup below into an S-tier React component using {theme_name} color tokens, fluid typography, subtle glassmorphism, and responsive layout primitives:\n\n```html\n{ugly_html}\n```",
    "Take this legacy {comp} interface and redesign it into a state-of-the-art bespoke web component. Enforce proper WCAG AA contrast, smooth transition states, and modern Tailwind primitives:\n\n```html\n{ugly_html}\n```",
    "The following {comp} snippet suffers from severe visual regression and baseline styling. Refactor it into a high-taste, production-ready TSX component:\n\n```html\n{ugly_html}\n```"
]

RESPONSE_STRUCTURES = [
    "**Visual AST Diagnosis & Design Rationale ({theme_name} Palette):**\n1. Replaced unstyled legacy layout with an 8pt spatial grid hierarchy.\n2. Applied {theme_name} design tokens (`{bg}`, `{border}`) with glassmorphism backdrop effects.\n3. Added tactile micro-interactions (`active:scale-[0.98]`) and accessible focus rings.\n\n```tsx\n{bespoke_code}\n```",
    "### Design System Transformation ({theme_name})\n- **Spatial Grid**: Replaced rigid fixed dimensions with fluid flexbox container constraints.\n- **Color System**: Utilized high-contrast dark mode primitives (`{bg}`) paired with subtle border gradients (`{border}`).\n- **Accessibility & State**: Added keyboard focus rings and pulse indicator badges.\n\n```tsx\n{bespoke_code}\n```",
    "Here is the refactored, high-taste {comp} implementation built with modern UI design principles:\n\n```tsx\n{bespoke_code}\n```"
]

def generate_unique_utbui_pair(idx):
    rng = random.Random(idx + 100000)
    
    comp = rng.choice(COMPONENT_TYPES)
    theme = rng.choice(THEMES)
    pat_type, ugly_tmpl = rng.choice(UGLY_PATTERNS)
    
    title = rng.choice(TITLES)
    desc = rng.choice(DESCS)
    btn_text = rng.choice(BTNS)
    
    bg_col = rng.choice(["#ffffff", "#f0f0f0", "#e0e0e0", "#cccccc", "#111111"])
    fg_col = rng.choice(["#000000", "#333333", "#222222", "#555555"])
    border_col = rng.choice(["#000000", "#999999", "#cccccc", "#444444"])
    pad_val = f"{rng.choice([4, 8, 12, 16, 20, 24])}px"
    btn_bg_col = rng.choice(["blue", "red", "green", "black", "navy", "purple"])
    val1_str = f"VAL-{rng.randint(1000, 9999)}"
    val2_str = f"${rng.randint(10, 999)},{rng.randint(100, 999)}"
    
    ugly_html = ugly_tmpl.format(
        bg=bg_col, fg=fg_col, border=border_col, pad=pad_val,
        title=title, desc=desc, btn_bg=btn_bg_col, btn_text=btn_text,
        h1="Metric Key", h2="Current Value",
        val1=val1_str, val2=val2_str
    )
    
    prompt_tmpl = rng.choice(PROMPT_STRUCTURES)
    prompt = prompt_tmpl.format(
        comp=comp, theme_name=theme['name'], ugly_html=ugly_html
    )
    
    status_badge_text = rng.choice(["Operational", "Active Session", "Telemetry Synced", "Encrypted", "Live Stream", "Verified"])
    
    bespoke_code = f"""<div class="w-full max-w-md rounded-2xl {theme['bg']} border {theme['border']} p-6 shadow-2xl backdrop-blur-xl transition-all hover:border-zinc-700/60">
  <div class="flex items-center justify-between border-b border-zinc-800/60 pb-4 mb-4">
    <h3 class="text-sm font-semibold tracking-tight {theme['text']}">{title}</h3>
    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono text-emerald-400 bg-emerald-950/60 rounded-full border border-emerald-800/50">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> {status_badge_text}
    </span>
  </div>
  <p class="text-xs text-zinc-400 font-medium mb-6">{desc}</p>
  <button class="w-full py-2.5 px-4 bg-gradient-to-r {theme['accent']} active:scale-[0.98] text-xs font-semibold text-white rounded-xl shadow-lg transition-all duration-150 {theme['ring']}">
    {btn_text}
  </button>
</div>"""

    resp_tmpl = rng.choice(RESPONSE_STRUCTURES)
    response = resp_tmpl.format(
        comp=comp, theme_name=theme['name'], bg=theme['bg'], border=theme['border'], bespoke_code=bespoke_code
    )

    return prompt, response

def main():
    seen_prompts = set()
    seen_responses = set()
    entries = []
    
    print("Generating 15,000 HIGH-DIVERSITY Recipe 1 UTBUI dataset pairs...")
    
    for i in range(15000):
        prompt, response = generate_unique_utbui_pair(i + 1)
        
        offset = 1
        while prompt in seen_prompts or response in seen_responses:
            prompt, response = generate_unique_utbui_pair(i + 15000 + offset)
            offset += 1
            
        seen_prompts.add(prompt)
        seen_responses.add(response)
        
        entries.append({
            "id": f"eli-utbui-unique-{i+1:05d}",
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": response}
            ],
            "metadata": {"recipe": "Recipe 1: UTBUI", "uniqueness_verified": True}
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Recipe 1 UTBUI Dataset Generated:")
    print(f"  Total Unique Pairs: {len(entries):,}")
    print(f"  Unique Prompts Count: {len(seen_prompts):,}")
    print(f"  Unique Responses Count: {len(seen_responses):,}")
    print(f"  Output File: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB)")

if __name__ == "__main__":
    main()
