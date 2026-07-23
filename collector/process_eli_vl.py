"""
Eli-VL Vision-Language Dataset Processor for Epoch Model Suite 1

Converts visual reference images and metadata from `references/` into
Qwen-VL / Eli-VL compatible multimodal instruction pairs.
"""

import json
import random
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = PROJECT_ROOT / "references"
PROCESSED_DIR = PROJECT_ROOT / "processed"

LABEL_DESCRIPTIONS = {
    "hero-section": "A modern hero section with high-contrast call-to-action buttons, bold typography, and visual assets.",
    "dashboard-ui": "A sleek analytics dashboard interface with data grid widgets, cards, and metric visualizations.",
    "generative-art": "A creative canvas background with radial gradients and dynamic visual elements.",
    "standard_web_component": "A clean, accessible UI web component following modern design system specifications.",
    "dark_dashboard": "A polished dark-mode SaaS dashboard with metric cards, sidebar navigation, and subtle borders.",
    "minimal_icon_asset": "A minimal UI asset with clean geometry and focused focal points.",
}

PROMPT_TEMPLATES = [
    "Scaffold a responsive frontend component matching the layout and design elements shown in this UI screenshot.",
    "Analyze the visual hierarchy, color palette, and component structure of this interface image.",
    "Convert this {category} layout into clean, accessible HTML/CSS with modern styling tokens.",
    "How would a senior frontend engineer implement the design shown in this screenshot? Provide the structural layout and styling rationale.",
]

def load_references_labels():
    labels_path = REFERENCES_DIR / "labels.json"
    if not labels_path.exists():
        return []
    try:
        return json.loads(labels_path.read_text())
    except Exception:
        return []

def load_eli_frontend_ui_labels():
    labels_jsonl = REFERENCES_DIR / "eli-frontend-ui" / "labels.jsonl"
    items = []
    if not labels_jsonl.exists():
        return items
    for line in labels_jsonl.read_text().splitlines():
        if line.strip():
            try:
                items.append(json.loads(line))
            except Exception:
                pass
    return items

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    vl_pairs = []
    
    ref_labels = load_references_labels()
    ui_labels = load_eli_frontend_ui_labels()
    
    print(f"Loaded {len(ref_labels)} main reference labels and {len(ui_labels)} Eli UI dataset labels.")
    
    # Process main reference images
    for idx, item in enumerate(ref_labels):
        img_name = item.get("file")
        img_path = REFERENCES_DIR / img_name
        if not img_path.exists():
            continue
        
        category = item.get("category", "web-interface")
        desc = item.get("description", LABEL_DESCRIPTIONS.get(category, "A clean web interface design."))
        dim = item.get("dimensions", "1024x768")
        
        rng = random.Random(hash(img_name))
        prompt_tmpl = rng.choice(PROMPT_TEMPLATES)
        prompt = prompt_tmpl.format(category=category.replace("-", " "))
        
        assistant_reply = f"""**Design Rationale & Visual Breakdown:**
- **Category:** {category.title()}
- **Dimensions:** {dim}
- **Visual Features:** {desc}

```html
<!-- Structural HTML Representation -->
<section class="{category.lower()} container mx-auto p-6 flex flex-col items-center justify-center">
  <div class="w-full max-w-4xl bg-slate-900 text-slate-100 rounded-xl shadow-2xl p-8 border border-slate-800">
    <h1 class="text-3xl font-bold tracking-tight mb-4">{desc.split('.')[0]}</h1>
    <p class="text-slate-400 mb-6 font-medium">Rendered layout following modern taste standards.</p>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-4 bg-slate-800/50 rounded-lg border border-slate-700/50">Widget Alpha</div>
      <div class="p-4 bg-slate-800/50 rounded-lg border border-slate-700/50">Widget Beta</div>
      <div class="p-4 bg-slate-800/50 rounded-lg border border-slate-700/50">Widget Gamma</div>
    </div>
  </div>
</section>
```"""

        vl_pairs.append({
            "id": f"eli-vl-ref-{idx+1:03d}",
            "image": f"references/{img_name}",
            "conversations": [
                {"from": "human", "value": f"<image>\n{prompt}"},
                {"from": "gpt", "value": assistant_reply}
            ],
            "metadata": {
                "source": "references/labels.json",
                "category": category,
                "dimensions": dim,
                "size_kb": item.get("size_kb", 0.0)
            }
        })

    # Process Eli Frontend UI webp set
    for item in ui_labels:
        rel_path = item.get("relative_path")
        img_path = REFERENCES_DIR / "eli-frontend-ui" / rel_path
        if not img_path.exists():
            continue
        
        ui_cat = item.get("ui_category", "standard_web_component")
        theme = item.get("theme", "neutral")
        tier = item.get("tier", "tier1_high_suitability")
        dim_dict = item.get("dimensions", {"width": 1024, "height": 768})
        dim_str = f"{dim_dict.get('width', 1024)}x{dim_dict.get('height', 768)}"
        
        rng = random.Random(hash(item.get("id")))
        prompt_tmpl = rng.choice(PROMPT_TEMPLATES)
        prompt = prompt_tmpl.format(category=ui_cat.replace("_", " "))
        
        desc = LABEL_DESCRIPTIONS.get(ui_cat, f"A {theme}-themed UI component ({ui_cat.replace('_', ' ')}) with clean proportions.")
        
        assistant_reply = f"""**Eli-VL Design Breakdown & Component Specification:**
- **Tier:** {tier} ({item.get('suitability', 'optimal')})
- **Theme:** {theme.title()} mode (Lightness score: {item.get('lightness_score', 128.0):.1f})
- **Edge Density:** {item.get('edge_density', 10.0):.1f}
- **Category:** {ui_cat}

```tsx
// Modern React / Tailwind Component Scaffold
import React from 'react';

export default function UIComponent() {{
  return (
    <div className="{ 'bg-zinc-950 text-white' if theme == 'dark' else 'bg-white text-zinc-900' } min-h-screen p-8 antialiased">
      <header className="max-w-5xl mx-auto border-b border-zinc-200 dark:border-zinc-800 pb-4 mb-8">
        <h2 className="text-xl font-semibold tracking-tight">{ui_cat.replace('_', ' ').title()}</h2>
      </header>
      <main className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 shadow-sm">
          <p className="text-sm font-medium">{desc}</p>
        </div>
      </main>
    </div>
  );
}}
```"""

        vl_pairs.append({
            "id": f"eli-vl-ui-{item.get('id')}",
            "image": f"references/eli-frontend-ui/{rel_path}",
            "conversations": [
                {"from": "human", "value": f"<image>\n{prompt}"},
                {"from": "gpt", "value": assistant_reply}
            ],
            "metadata": {
                "source": "references/eli-frontend-ui",
                "category": ui_cat,
                "theme": theme,
                "tier": tier,
                "dimensions": dim_str,
                "size_bytes": item.get("size_bytes", 0)
            }
        })

    vl_file = PROCESSED_DIR / "training-data-eli-vl.jsonl"
    with open(vl_file, "w", encoding="utf-8") as f:
        for entry in vl_pairs:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    manifest = {
        "dataset_name": "Eli-VL Vision-Language Multimodal Dataset",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_model": "Eli-VL (Qwen-VL / Qwen3-VL LoRA Adapter)",
        "total_multimodal_pairs": len(vl_pairs),
        "source_counts": {
            "references_main": len(ref_labels),
            "eli_frontend_ui_webp": len(ui_labels)
        },
        "output_file": str(vl_file),
        "file_size_kb": round(vl_file.stat().st_size / 1024, 2)
    }
    
    manifest_path = PROCESSED_DIR / "eli-vl-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    print(f"\nEli-VL Multimodal Dataset Generation Complete:")
    print(f"  Pairs Generated: {len(vl_pairs)}")
    print(f"  Dataset File: {vl_file} ({vl_file.stat().st_size / 1024:.1f} KB)")
    print(f"  Manifest File: {manifest_path}")

if __name__ == "__main__":
    main()
