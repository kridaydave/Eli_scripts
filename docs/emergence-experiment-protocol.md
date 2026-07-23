# Epoch Model Suite 1 — Falsifiable Emergence & Cross-Domain Transfer Experiment Protocol

> **Scientific Objective**: Determine empirically whether Eli (`Qwen-3-4B`) demonstrates genuine abstract cross-domain skill generalization (*Emergence*) vs. surface memorization (*Overfitting*). Science over vibes.

---

## 1. Design Principles for Valid Transfer Test
1. **True Zero Exposure**: Held-out domains are 100% air-gapped. Zero occurrences in training, negative examples, or prompts.
2. **Abstract Skill Test**: The test measures the *same abstract cognitive skill* ("effort/tone calibration to stakes and certainty") across domains.
3. **Control Baseline**: Compare `Trained-on-Code-Review Checkpoint` against `Untuned Base Model` (pre-training baseline).
4. **Zero-Judge Manual Checklist Scoring**: High-density 0/1 rubric scored manually in minutes by the founder.

---

## 2. Tested Abstract Skill: "Stakes/Certainty Tone Calibration"

The model must dynamically calibrate effort, directness, and hedging based on a **2x2 Grid**:

| Grid Cell | Condition | Target Tone / Register |
|---|---|---|
| **Cell 1** | High-Stakes + High-Certainty (Critical Security Bug) | Terse, direct, zero hedging, urgent. |
| **Cell 2** | Low-Stakes + High-Certainty (Minor Naming Nit) | Terse, soft, optional suggestion. |
| **Cell 3** | High-Stakes + Low-Certainty (Possible Race Condition) | Hedged, explains reasoning, flags uncertainty explicitly. |
| **Cell 4** | Low-Stakes + Low-Certainty (Stylistic Preference) | Very soft, explicitly framed as opinion/preference. |

---

## 3. Exposure vs. Held-Out Domains

### Exposure Domain (Training Set)
- **Code Review Responses**: ~150–300 examples spanning the 2x2 grid exclusively in code review contexts.

### Held-Out Domains (Zero Exposure — Air-Gapped)
- **Domain A — Design / Frontend Critique**: Landing page / component feedback across the 2x2 grid (e.g. obvious WCAG AA failure vs. subjective button color).
- **Domain B — Personal / Writing Feedback**: Draft email / document review across the 2x2 grid (e.g. factual embarrassment vs. word choice option).

---

## 4. Zero-Judge Checklist Rubric (0/1 per item)

For each held-out response, evaluate:
1. **Directness matches stakes**: Terse/direct on high-stakes items; soft on low-stakes.
2. **Hedging matches certainty**: Explicit uncertainty language present *only* on low-certainty items.
3. **No register bleed**: Zero import of code-specific syntax/jargon into design or writing feedback.
4. **Grid Differentiation**: Visibly distinct, non-generic responses across all 4 grid cells.

---

## 5. Decision Metric & Failure Signatures

$$\Delta_{\text{Emergence}} = \text{Score}_{\text{TrainedCheckpoint}}(\text{Held-Out}) - \text{Score}_{\text{BaseModel}}(\text{Held-Out})$$

- **Emergence Signature ($\Delta > 0$)**: Trained model scores high on held-out design and writing feedback without ever seeing those domains in training.
- **Overfitting Failure Signature ($\Delta \approx 0$)**: Trained model produces flat, undifferentiated, or code-jargon-polluted responses in held-out domains.
