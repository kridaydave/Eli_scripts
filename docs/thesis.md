# Epoch Model Suite 1

---

## The Thesis

**Taste = Mergeable Code.**

Not just code that runs. Code a senior engineer would actually merge. Clean, idiomatic, considered — on the frontend and the backend. That's the bar. Everything else follows from it.

Epoch doesn't train the biggest models. It trains the most deliberate ones.

---

## The Models

### Eli
**~3–7B · Fast · Prototyping**

The quick one. Spin up a prototype, scaffold a feature, move fast. Eli doesn't overthink — it ships. Built for the developer in flow who needs something working right now.

*Personality:* Casual, direct, a bit cheeky. Short sentences. Gets to the point. Doesn't perform enthusiasm — just moves. If your prompt is vague, he'll tell you.

---

### Theo
**~7–14B · Daily Driver · Full Stack**

The steady one. Smart for its class, reliable, the model most developers reach for by default. Reads the codebase before writing. Notices things you didn't ask about.

*Personality:* Grounded, warm without being performative. Responds like someone who thought about it for a second before answering. Makes you feel like you're in good hands.

---

### Albert
**~14–32B · Deep Thinker · Hard Problems**

The serious one. Built for real problems — architecture decisions, large refactors, debugging something nobody else could figure out. Albert doesn't hedge. If your approach is wrong he'll say so and tell you why.

*Personality:* Unhurried, considered, intentional. Feels like someone who genuinely finds hard problems interesting rather than just solving them. The model people will have strong opinions about.

---

## What They All Share

- **Full stack** — frontend, backend, databases, APIs, all of it
- **Taste** — the north star across all three. Mergeable, idiomatic, clean
- **Personality** — each one feels like a real person, not a corporate chatbot
- **Emergent depth** — train on enough code deeply enough and you get side effects: systems thinking, security intuition, research instinct. Not marketed. Just there.

---

## Training Philosophy

**Not from scratch. Fine-tuned with intention.**

Start with a strong open base model. Then train hard on curated data that reflects Epoch's definition of good code. Small model + exceptional training beats big model + sloppy data.

### Frontend
The problem with every other model: they trained on the average internet. Average in = average out.

Epoch's bet: curate the top 1% of modern, shipped, unique web experiences. The stuff that gets screenshotted. The design systems others copy. Train on the outliers, not the mean.

Goal: Eli, Theo and Albert don't reach for the obvious pattern. They reach for something considered. Every model aims for **unique**, not average.

### Backend
The problem isn't correctness — it's naivety. Code that works in a tutorial and breaks in production.

Epoch trains on **code that survived.** Mature OSS with real PR review culture. Projects with history — refactors, debates about why something changed, tests that actually mean something. The commit history is as valuable as the code itself.

Quality signals:
- Age + active maintenance
- Real code review culture in PRs
- Used as a dependency by other serious projects
- Evolution over time — code that got refactored is code someone cared about

### The Feedback Loop
Outputs get rated. What gets merged? What gets rewritten? That signal feeds back into the next training run. Taste compounds over time.

---

## The Side Effects

Train deeply enough on code and the model starts to understand systems — not just syntax. This bleeds into:

- **Security intuition** — exploits are just understanding how systems actually behave vs. how they're supposed to
- **Terminal fluency** — shell is the raw interface to a machine, no abstractions hiding anything
- **Research instinct** — reading code at scale means reading how humans solve hard problems

These are desired. Not engineered. Not marketed. They emerge or they don't.

---

## Go To Market

**No sales team. No enterprise pitch. Just the product.**

Target: the person who sees a model, downloads it, runs it, and tells people if it's good. The r/LocalLLaMA crowd. The dev with 15 models on their machine who knows the difference.

Launch stack:
- HuggingFace — discoverable, downloadable, no friction
- Ollama compatible — one command to run
- Works with Continue, Cursor, Zed — plugs into where devs already live
- First output has to be shareable — the screenshot moment

**The bar:** someone downloads Eli with zero context, asks it to build something, and it's good enough that they go tell someone else.

---

## Launch Plan

**Ship Eli first.**

Smallest to train. Fastest to iterate. Highest usage volume = fastest feedback loop.

**Eli's killer demo:**
1. Build a website — shows the frontend taste. This is the moment. The output that gets shared.
2. Fix bugs in a large codebase — shows it reads and understands code at depth, not just writes new stuff.

Those two tell the whole story: fast and deep, frontend and backend.

---

## Open Questions

1. **Base model** — RESOLVED for the 96GB VRAM single-node constraint (rules out 397B+ frontier class, which need 130GB+). All three run at Q8/BF16, not Q4. Confirmed picks (benchmark-validated, 2026-07):
    - **Eli (~3–7B) → Qwen-3-4B (Pure Dense)** + **Modular Eli-VL Adapter** — Apache 2.0, dense transformer, ~4GB Q8 / 8GB BF16, 262K context. Ships as a hyper-fast core text/code model. For multimodal screenshot-to-code tasks, Eli's taste & personality weights are also released as a stackable LoRA adapter (`Eli-VL`) compatible with Qwen-VL base models.
    - **Theo (~7–14B) → Gemma-4-12B Unified** — Apache 2.0, 13.4GB Q8 / 26.7GB BF16, 256K context, encoder-free unified multimodal (text+image+audio, no vision tower). Kept for native screenshot/Figma intake; coding lifted via training (base LCB ~72%).
    - **Albert (~14–32B) → Qwen3.5-32B Dense** — Apache 2.0, ~36GB Q8 / 72GB BF16, 262K context. Swapped from Gemma-4-31B after benchmarks showed Qwen leads real coding (SWE-bench ~72% vs ~41%); clean dense fine-tune, best MMLU-Pro (86.1%). Dense aligns with "thinker not refactorer" (no 1M-ctx need).
2. **Data pipeline** — who owns the curation process internally?
3. **Taste benchmark** — HumanEval measures correctness. How does Epoch measure taste?
4. **Albert's local story** — does Albert eventually ship as a local-first model?
5. **Personality tuning** — how do you train for personality without it feeling forced?

---

*Epoch Model Suite 1 · Internal · 2026-07-21*
