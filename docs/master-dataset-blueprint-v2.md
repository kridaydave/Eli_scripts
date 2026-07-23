# Epoch Model Suite 1 — Eli (4B) Master Data & Fine-Tuning Specification (v2 - Cross-Axis Emergence Edition)

> **Core Model**: Eli (`Qwen-3-4B Pure Dense Transformer`)  
> **Core Identity**: Fast, direct, high-taste, senior full-stack pair programmer with calibrated wit and surgical execution.  
> **Core Architecture**: **70% SINGLE-AXIS BASE + 30% CROSS-AXIS JOINT EXAMPLES**.  
> Interleaving prevents forgetting, but **Cross-Axis Joint Examples** (examples requiring Code + Writing + Wiseness simultaneously) force a memory-constrained 4B model to build **shared latent circuits**.

---

## Executive Architecture & 4-Pillar Progression

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│              4-PILLAR DATA CURATION & ALIGNMENT (ZERO AI JUDGES)                  │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
     ┌───────────────────┬───────────────┴───────────────┬───────────────────┐
     ▼                   ▼                               ▼                   ▼
┌─────────┐         ┌─────────┐                     ┌─────────┐         ┌─────────┐
│ Pillar 1│         │ Pillar 2│                     │ Pillar 3│         │ Pillar 4│
│  Code   │ ───────►│ Frontend│ ───────────────────►│ Writing │ ───────►│Wiseness │
│(Linter/ │         │(Play-   │                     │(Founder │         │(Founder │
│ Pytest) │         │ wright) │                     │ Curation│         │ Register│
└─────────┘         └─────────┘                     └─────────┘         └─────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│             15% - 30% CROSS-AXIS JOINT EXAMPLES (EMERGENCE ENGINE)               │
│    Single prompts requiring Code + Frontend + Writing + Wiseness simultaneously   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. The 70/30 Data Split
- **70%–85% Single-Axis Base**: Provides clean, diagnosable per-axis evaluation curves and solid ground-truth baseline capabilities (Stack v2 code, Radix UI components, white-listed technical writing).
- **15%–30% Cross-Axis Joint Data**: Hand-curated by the founder. Prompts where there is no code-only or writing-only path to a correct answer (e.g. Code Review with register-matched tone, UI component with voice-calibrated microcopy).

---

## 2. Falsifiable Emergence Test Protocol

Before training, define the **Held-Out Cross-Domain Transfer Test**:
1. Train register-matching wiseness *only* on code-review prompts. Hold out 100% of frontend critique prompts.
2. Evaluate zero-shot whether register-matching tone transfers unprompted to frontend critiques.
3. Measure $\text{Emergence Delta} = \text{Score}_{\text{Joint}} - \text{Expected}_{\text{LinearSum}}$.

---

## Document Index
- 📄 [step-1-code-spec.md](file:///home/kriday/Desktop/epoch-1/docs/step-1-code-spec.md)
- 📄 [step-2-frontend-spec.md](file:///home/kriday/Desktop/epoch-1/docs/step-2-frontend-spec.md)
- 📄 [step-3-writing-spec.md](file:///home/kriday/Desktop/epoch-1/docs/step-3-writing-spec.md)
- 📄 [step-4-wiseness-spec.md](file:///home/kriday/Desktop/epoch-1/docs/step-4-wiseness-spec.md)
- 📄 [emergence-and-cross-axis-spec.md](file:///home/kriday/Desktop/epoch-1/docs/emergence-and-cross-axis-spec.md)
- 📄 [master-dataset-blueprint-v2.md](file:///home/kriday/Desktop/epoch-1/docs/master-dataset-blueprint-v2.md)
