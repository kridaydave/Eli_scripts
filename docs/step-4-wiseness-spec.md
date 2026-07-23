# Epoch Model Suite 1 — Step 4: Wiseness (Wit + Judgment) Specification (Zero-Model / Human-Tuned)

**Goal**: The meta-skill sitting on top of code, frontend, and writing — knowing which register a given prompt calls for (when to dial cleverness up or down).

## Core Constraint & Principle
**NO MODEL JUDGES / NO LLM SCORERS**. No AI model understands when to dial cleverness up or down for Eli's persona. Register calibration is driven **100% by human founder judgment** and **deterministic test execution**.

---

## 1. Prompt Ingress & Register Variants

- **Real User Prompts**: Gather real user-style prompts across varying urgency and domains (production outages, technical queries, creative architecture, casual chat).
- **Manual Register Writing**: Human founder creates or approves 2–3 response variants per prompt across explicit registers:
  - `pure-direct` (zero fluff, pure code/patch for urgent debugging)
  - `light-personality` (concise senior engineer tone)
  - `maximal-wit` (playful, sharp tone for casual or open-ended prompts)

---

## 2. Founder Register Matching (No AI Judges)

- **Direct Founder Selection**: The founder selects the single correct register for each prompt.
- **Sycophancy Prevention**: Eliminates AI reward-hacking entirely. No AI model is allowed to score or rank responses, preventing the model from over-rewarding wit when plain utility was required.

---

## SFT vs DPO Split (Zero Models)

- **SFT**: Modest set of clearly labeled, founder-approved register examples (~300–500 pairs).
- **DPO**: DPO preference pairs constructed directly from founder-ranked register variants (`chosen`: founder-selected register, `rejected`: wrong-register variant).

---

## Core Pipeline Architecture Rules

1. **Sequence Dependency**: `Code → Frontend → Writing → Wiseness` matches increasing difficulty-to-verify order. Get verifiable axes (code, functional frontend) locked down first.
2. **Zero-AI Judge Policy**: Ground truth comes from deterministic tool execution (pytest/linter exit codes, Playwright screenshot renders) and direct founder curation. No AI models used as judges.
