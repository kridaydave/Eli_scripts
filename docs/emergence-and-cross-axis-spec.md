# Epoch Model Suite 1 — Cross-Axis Joint Examples & Emergence Architecture

> **Core Insight**: Interleaving mixed batches is a *mitigation* against catastrophic forgetting, not an active driver of emergence. True emergence in a 4B parameter model occurs when cross-domain transfer is made **structurally necessary** through **Cross-Axis Joint Examples**.

---

## 1. The 4B Shared Circuit Hypothesis

Under strict memory pressure in a 4B dense model, if the network is forced to solve register matching in code and register matching in copy using the same weight matrix, the optimizer has a strong incentive to compress the logic into a **single, unified shared circuit** ("match effort, restraint, and tone to the situation") rather than duplicating redundant domain-specific circuits.

---

## 2. The 70/30 Split Architecture

To balance clean gradient signals with emergence-forcing representations:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    ELI 4B CURATED DATASET COMPOSITION                            │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
┌────────────────────────────────────────┐       ┌────────────────────────────────────────┐
│     70% - 85% SINGLE-AXIS BASE         │       │   15% - 30% CROSS-AXIS JOINT EXAMPLES  │
│  - Clean code (Stack v2)               │       │  - Code + Writing + Wiseness           │
│  - Clean UI components (Radix/Shadcn)  │       │  - Frontend + Writing + Restraint      │
│  - Clean technical essays              │       │  - Hand-curated & scored by Founder    │
│  - Provides diagnosable eval curves    │       │  - Forces shared latent circuit creation│
└────────────────────────────────────────┘       └────────────────────────────────────────┘
```

---

## 3. Concrete Examples of Cross-Axis Joint Data

1. **Code Review Response (Code + Writing + Wiseness)**:
   - *Prompt*: Review a pull request containing a critical race condition alongside minor style nitpicks.
   - *Joint Requirement*: Technical precision on the race condition (**Code**), delivered with a blunt tone for the security issue vs gentle tone for the style nit (**Wiseness**), written in direct, non-corporate voice (**Writing**).
2. **Interactive UI Component (Frontend + Writing + Restraint)**:
   - *Prompt*: Build a checkout error toast component.
   - *Joint Requirement*: Clean visual hierarchy and OKLCH color tokens (**Frontend**), paired with concise, empathetic microcopy (**Writing**), calibrated to zero-slop restraint (**Wiseness**).

---

## 4. Falsifiable Emergence Test (Held-Out Cross-Domain Experiment)

To prove emergence scientifically rather than guessing:

1. **Held-Out Domain Isolation**: Train register-matching wiseness *exclusively* on code-review prompts. Hold out 100% of frontend critique prompts from the wiseness training set.
2. **Zero-Shot Transfer Test**: Evaluate whether the model demonstrates unprompted register matching on held-out frontend critique responses.
3. **Emergence Metric**: Track whether performance on joint cross-axis evals improves **faster than the linear sum of single-axis evaluation curves would predict**:
   $$\text{Emergence Delta} = \text{Score}_{\text{Joint}} - \left(w_1 \cdot \text{Score}_{\text{Code}} + w_2 \cdot \text{Score}_{\text{Writing}}\right)$$
   A positive $\text{Emergence Delta} > 0$ on held-out tasks is the empirical signature of emergent cross-domain circuit creation.
