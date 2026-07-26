# Phase 2 Expansion: Preference Alignment, Format Routing & Capability Extensions

---

## Executive Summary

This specification extends the [Phase 2 PR Training Spec](./pr-training-phase.md) with **14 additional training workstreams** addressing documented gaps from Phase 1. The three highest-priority items are:

1. **DPO/SimPO Preference Alignment** — teaching taste vs. correctness
2. **Format Disambiguation** — fixing the FABLE 5 tool-wrapper bleed that tanked Pass@1 to 0%
3. **Multi-Turn Persona Persistence** — eliminating Eli's personality drift across conversation turns

Combined with the existing Phase 2 corpus (PR diffs + agentic traces + multimodal UI/UX), these expansions produce a complete post-training pipeline covering both SFT and preference alignment.

---

## 1. DPO/SimPO Preference Alignment Pipeline

### 1.1 Motivation

Phase 1 was pure SFT. SFT teaches the model *what* to output, but not *what to prefer*. The thesis ("Taste = Mergeable Code") requires the model to distinguish between correct-but-ugly and correct-and-tasteful solutions — a distinction only preference optimization can enforce.

### 1.2 Dataset Architecture (1,200 Pairs)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DPO v2 Preference Pair Architecture                   │
├──────────────┬────────┬──────────────────────┬──────────────────────────┤
│ Axis         │ Pairs  │ Chosen Signal        │ Rejected Degradation     │
├──────────────┼────────┼──────────────────────┼──────────────────────────┤
│ Code         │ 300    │ Idiomatic, right      │ Over-engineered, god     │
│ (Multi-lang) │        │ abstraction level     │ functions, no error      │
│              │        │                      │ handling, var→const      │
├──────────────┼────────┼──────────────────────┼──────────────────────────┤
│ Frontend     │ 200    │ Restrained Tailwind,  │ Visual clutter, inline   │
│              │        │ clean React, a11y     │ styles, div-soup         │
├──────────────┼────────┼──────────────────────┼──────────────────────────┤
│ Writing      │ 150    │ Concise, direct, zero │ Sycophantic, cliché,     │
│              │        │ banned phrases        │ passive voice, fluff     │
├──────────────┼────────┼──────────────────────┼──────────────────────────┤
│ Register     │ 150    │ Correct stakes/cert   │ Wrong register (casual   │
│              │        │ grid match            │ on outage, formal chat)  │
├──────────────┼────────┼──────────────────────┼──────────────────────────┤
│ Code Review  │ 200    │ Structured, specific, │ Vague "LGTM", missing    │
│ (NEW)        │        │ actionable feedback   │ severity, no examples    │
├──────────────┼────────┼──────────────────────┼──────────────────────────┤
│ Debugging    │ 200    │ Root-cause diagnosis   │ Symptom treatment,       │
│ (NEW)        │        │ with targeted fix     │ unrelated SO paste       │
└──────────────┴────────┴──────────────────────┴──────────────────────────┘
```

### 1.3 Degradation Functions (Expanded)

Building on v1's `inject_sycophancy`, `inject_cliches`, `inject_verbosity`, `degrade_code`, `add_visual_clutter`, and `swap_register`, v2 adds:

| Function | Description | Target Axis |
|---|---|---|
| `inject_overengineering(code)` | Unnecessary factory patterns, DI containers, abstraction layers for simple tasks | Code |
| `inject_tutorial_code(code)` | Excessive comments, obvious variable names, zero edge-case handling | Code |
| `inject_stackoverflow_paste(code)` | Irrelevant imports, commented-out code, mismatched variable names | Code, Debugging |
| `inject_vague_review(review)` | Strips specifics ("this could be better" with no concrete suggestion) | Code Review |
| `inject_symptom_treatment(diagnosis)` | Suggests fixes addressing symptoms not root causes | Debugging |
| `inject_div_soup(html)` | Replaces semantic HTML (`<nav>`, `<section>`) with nested `<div>` wrappers | Frontend |

### 1.4 Training Protocol

- **Method:** SimPO (reference-free, simpler than DPO, +6.4 on AlpacaEval 2.0)
- **Sequence:** Run *after* Phase 2 SFT completes
- **$\beta$:** Start at 2.5, sweep $\{1.0, 2.0, 2.5, 5.0\}$
- **Learning rate:** $5 \times 10^{-7}$ (10× lower than SFT)
- **Epochs:** 1 (preference alignment is sensitive to overfitting)

### 1.5 Output

- **Collector:** `collector/generate_dpo_pairs_v2.py`
- **Output file:** `processed/training-data-eli-dpo-v2.jsonl`
- **Schema:** Matches existing DPO schema from v1 (`id`, `prompt`, `chosen`, `rejected`, `metadata`)

---

## 2. Format Disambiguation Training

### 2.1 Problem Statement

The SFT evaluation at Step 500 ([sft_evaluation_strategy.md](./sft_evaluation_strategy.md)) revealed that 34.4% FABLE 5 agentic CoT data contaminated direct Q&A outputs. The model emits tool-call wrappers (`cat << 'EOF'`, `grep_search`, `view_file`) even when the user asks a simple question in chat.

### 2.2 Solution: Contrastive Format Routing

Train on **500 matched pairs** where the identical technical question is answered in both formats:

```
┌───────────────────────────────────────────────────────────────────────┐
│                    Format Disambiguation Architecture                  │
├───────────────────────────────┬────────────────────────────────────────┤
│ Direct Mode (Alpaca)          │ Agentic Mode (ShareGPT Multi-Turn)    │
├───────────────────────────────┼────────────────────────────────────────┤
│ Clean markdown code block     │ <thought> reasoning </thought>        │
│ No tool wrappers              │ grep_search ──► view_file ──► patch   │
│ Concise explanation + code    │ Full tool-call trace with outputs     │
│ Single-turn instruction       │ Multi-turn assistant-tool-result loop │
└───────────────────────────────┴────────────────────────────────────────┘
```

### 2.3 Question Categories (100 per category)

| Category | Example Prompts |
|---|---|
| Algorithm / DS | "Implement a trie in Python", "Write a concurrent hashmap in Go" |
| API / Web | "Create a REST endpoint with input validation", "Build a WebSocket handler" |
| Debugging | "This code has a race condition, fix it", "Why does this segfault?" |
| Refactoring | "Clean up this function", "Extract this into a reusable module" |
| Explanation | "How does async/await work in Rust?", "Channels vs mutexes?" |

### 2.4 Negative Mining DPO Pairs (50 pairs)

Explicitly mine wrong-format outputs as DPO rejected signals:

```
Wrong Format A: Tool-wrapper bleed on direct Q&A
  prompt: "Write a binary search in Python"
  chosen: "```python\ndef binary_search(arr, target):..."     (direct ✅)
  rejected: "cat << 'EOF' > solution.py\ndef binary_search..." (tool bleed ❌)

Wrong Format B: Raw code dump on agentic task  
  prompt: "[AGENTIC_TASK] Fix the failing test in auth.py"
  chosen: "<thought> Need to inspect the test... </thought>\ngrep_search..." (agentic ✅)
  rejected: "```python\ndef test_auth():..."                  (raw dump ❌)
```

### 2.5 Context-Based Routing (Zero System Prompt)

Per [personality.md](./personality.md)'s zero-system-prompt ethos, the model should infer mode from conversational context rather than `[DIRECT_QA]` / `[AGENTIC_TASK]` tags:

- **Chat context** (user asking a question) → direct mode
- **Agent loop context** (tool results in conversation history) → agentic mode
- **Ambiguous** → default to direct mode (safer)

### 2.6 Output

- **Collector:** `collector/generate_format_disambiguation.py`
- **Output files:**
  - `processed/training-data-format-direct.jsonl` (500 direct-mode Alpaca pairs)
  - `processed/training-data-format-agentic.jsonl` (500 agentic-mode ShareGPT pairs)
  - `processed/training-data-format-dpo.jsonl` (50 DPO negative-mining pairs)

---

## 3. Multi-Turn Persona Persistence

### 3.1 Gap

Phase 1 trained exclusively on single-turn pairs. [personality.md](./personality.md) flags multi-turn persona drift as a documented risk. Without dedicated multi-turn data, Eli's cheeky, direct personality degrades to generic assistant tone by turn 4-5.

### 3.2 Session Archetypes (200 Sessions × 5-8 Turns)

| Archetype | Count | Tests | Eli Behavior |
|---|---|---|---|
| Progressive Debugging | 40 | Diagnosis narrowing across turns | Gets more terse as root cause clarifies |
| Clarification & Pushback | 40 | Constructive pushback on vague prompts | "Better how? Performance? Readability?" |
| Iterative Feature Building | 40 | Long-range context coherence | References turn 2 context in turn 6 |
| Code Review Dialogue | 40 | Stakes/certainty register consistency | Defends or concedes points gracefully |
| Architecture Discussion | 40 | Tradeoff reasoning across turns | Asks probing questions, adapts proposals |

### 3.3 Persona Consistency Invariants

Every `gpt` turn across all 200 sessions MUST maintain:

1. **Contractions** — "don't", "won't", "that's" (not "do not", "will not", "that is")
2. **Short sentences** — average sentence length ≤ 15 words
3. **Zero sycophancy** — never starts with "Great question!", "I'd be happy to help!"
4. **Constructive pushback** — challenges bad ideas directly but respectfully
5. **Register calibration** — more terse under high-stakes, slightly playful under low-stakes

### 3.4 Long-Range Coherence Verification

For each Iterative Feature Building session, programmatically verify that information introduced in turn $t_i$ is correctly referenced in turn $t_{i+k}$ where $k \geq 3$:

$$\text{Coherence}(s) = \frac{|\{(t_i, t_{i+k}) : \text{ref}(t_{i+k}, t_i) = 1, k \geq 3\}|}{|\text{reference\_opportunities}(s)|}$$

Target: $\text{Coherence}(s) \geq 0.8$ for all sessions.

### 3.5 Output

- **Collector:** `collector/generate_multiturn_sessions.py`
- **Output file:** `processed/training-data-multiturn-sessions.jsonl`
- **Schema:** ShareGPT format matching `session_arcs.py` conventions

---

## 4. Code Review Critique Training (Inverse Task)

### 4.1 Motivation

The Phase 2 core spec trains Eli to **write** PRs. The inverse — **reviewing** PRs — is equally important. If the model truly has taste, it should critique bad taste, not just produce good output.

### 4.2 Dataset (400 Review Pairs)

Source from whitelisted repos' actual PR review threads:

```
Input:  Diff/patch + surrounding file context (3-file window)
Output: Structured code review with:
        - Severity classification (blocker / major / minor / nit)
        - Specific line references
        - Concrete fix suggestions with code
        - Approval verdict (approve / request-changes / comment)
```

### 4.3 2×2 Coverage Matrix

Reuse the Stakes/Certainty grid from [emergence-experiment-protocol.md](./emergence-experiment-protocol.md):

| | High Certainty | Low Certainty |
|---|---|---|
| **High Stakes** | Hardcoded secrets, SQL injection, race conditions → **Blocker, terse, immediate** | Memory leaks in long-running workers → **Flag with reasoning, request investigation** |
| **Low Stakes** | Unused imports, stray `console.log` → **Nit, optional** | Style preferences (tabs vs spaces) → **Soft suggestion, frame as opinion** |

### 4.4 Output

- **Collector:** `collector/generate_code_review_critique.py`
- **Output file:** `processed/training-data-code-review-critique.jsonl`

---

## 5. Debugging & Error Diagnosis Training

### 5.1 Dataset (300 Triples)

```
Stack Trace / Error Message  ──►  Root-Cause Diagnosis  ──►  Targeted Fix
```

Coverage across Phase 2 languages:

| Language | Error Categories |
|---|---|
| Python | `ImportError`, `TypeError`, `asyncio` deadlocks, `pytest` failures, OOM |
| TypeScript | Type narrowing failures, runtime `undefined`, Next.js hydration mismatch |
| Go | Nil pointer dereference, goroutine leaks, context cancellation, race detector |
| Rust | Borrow checker violations, lifetime mismatches, `tokio` runtime panics |
| C/C++ | Segfaults, buffer overflows, use-after-free, undefined behavior |

### 5.2 DPO Pairs (150 pairs)

- **Chosen:** Root-cause diagnosis → targeted fix
- **Rejected:** Symptom treatment → band-aid fix (e.g., wrapping in `try/except: pass`)

---

## 6. Test-Writing Training

### 6.1 Motivation

Phase 2 uses tests as *verification* (red-to-green engine) but doesn't train the model to *write* tests. Writing good tests is a core senior engineering skill.

### 6.2 Dataset (250 Pairs)

- **Input:** Function/module + specification
- **Output:** Comprehensive test suite covering happy path, edge cases, error conditions
- **Source:** Extract test files from whitelisted repos, pair with the code they test
- **Verification:** Generated tests must actually pass against the real implementation

### 6.3 Test Quality Criteria

Each generated test suite must include:

1. At least 1 happy-path test
2. At least 2 edge-case tests (empty input, boundary values, concurrent access)
3. At least 1 error-condition test (invalid input, network failure, timeout)
4. Proper test isolation (no shared mutable state between tests)
5. Descriptive test names (`test_returns_empty_list_when_no_results_found`)

---

## 7. Refactoring & Migration Training

### 7.1 Dataset (200 Pairs)

Source from whitelisted repos' refactoring PRs (filter commit messages for `refactor`, `cleanup`, `rewrite`, `migrate`):

| Category | Examples |
|---|---|
| **Extract & Simplify** | God function → well-named helper functions |
| **Modernize** | Class components → hooks, callbacks → async/await, `var` → `const`/`let` |
| **Dependency Upgrade** | Express 4 → 5, React Router 5 → 6, SQLAlchemy 1.x → 2.0 |
| **Pattern Application** | Inline logic → strategy pattern, switch → polymorphism (only when warranted) |

---

## 8. Long-Form Technical Writing

### 8.1 Gap

[step-3-writing-spec.md](./step-3-writing-spec.md) focused on short Q&A pairs (500–1,500 pairs). Real engineering requires longer-form documents.

### 8.2 Dataset (150 Pairs)

| Format | Count | Target Length |
|---|---|---|
| RFC / Design Document | 40 | 1,000–3,000 words |
| Architecture Decision Record (ADR) | 30 | 500–1,000 words |
| README Generation | 40 | 500–1,500 words |
| Post-Mortem Report | 20 | 800–2,000 words |
| Inline Documentation | 20 | Function/class-level docstrings |

### 8.3 Quality Criteria

All long-form outputs pass [step-3-writing-spec.md](./step-3-writing-spec.md) deterministic heuristics:
- Banned phrase dictionary (`delve`, `tapestry`, `game-changer`, etc.)
- Sentence-length variance $\sigma^2(L_{\text{sent}}) > 0$ (no monotonous rhythm)
- N-gram redundancy filtering

---

## 9. Terminal / CLI Fluency

### 9.1 Dataset (200 Pairs)

| Category | Examples |
|---|---|
| **Shell One-Liners** | `find`, `grep`, `awk`, `sed`, `jq` pipelines |
| **Git Mastery** | Interactive rebase, cherry-pick, bisect, reflog recovery |
| **Docker Debugging** | Reading logs, exec into containers, networking diagnosis |
| **Build Systems** | `make`, `cmake`, `cargo`, `go build` flags and troubleshooting |

---

## 10. Security-Aware Code Generation

### 10.1 Dataset (200 Pairs)

| Category | Count | Examples |
|---|---|---|
| Vulnerability → Fix | 80 | CVE-based SQL injection, XSS, SSRF, path traversal fixes |
| Secure-by-Default | 60 | Input validation, parameterized queries, proper auth flows |
| "Spot the Vulnerability" | 60 | Given code, identify and explain security issues |

### 10.2 DPO Pairs (100 pairs)

- **Chosen:** Secure implementation (parameterized query, proper escaping)
- **Rejected:** Insecure implementation (string concatenation in SQL, `eval()`, `innerHTML`)

---

## 11. API & Schema Design Training

### 11.1 Dataset (150 Pairs)

- **REST/GraphQL API design** — given requirements, produce well-structured endpoints
- **Database schema design** — normalized schema with appropriate indices and constraints
- **Advanced type system** — TypeScript generics, Rust trait bounds, Go interfaces

---

## 12. Interactive UI Evaluation Extension

Extends Format C from [pr-training-phase.md](./pr-training-phase.md):

| Evaluation Layer | Method | Current Coverage |
|---|---|---|
| Static Layout | Screenshot + WCAG AA scoring | ✅ Covered |
| Responsive Layout | Render at 3 viewports (375px, 768px, 1440px) | 🆕 New |
| Accessibility | ARIA tree extraction via Playwright | 🆕 New |
| Interaction | Click/type/navigate sequence validation | 🆕 New |
| Animation | Video capture + motion design heuristics | 🆕 Future |

---

## 13. Theo & Albert Portfolio Scaling

| Model | Base | Phase 2 Adaptation |
|---|---|---|
| **Eli** (4B) | Qwen3-4B-Instruct | Current Phase 2 target (all specs apply) |
| **Theo** (12B) | Gemma-4-12B-Unified | Same data, larger context window (32k), less aggressive dedup |
| **Albert** (32B) | Qwen3.5-32B-Dense | Add repo-level multi-file context, full module dependency graphs |

---

## 14. Emergence Formula Calibration

Fit the weighting coefficients from [emergence-and-cross-axis-spec.md](./emergence-and-cross-axis-spec.md):

$$\text{Emergence Delta} = \text{Score}_{\text{Joint}} - (w_1 \cdot S_{\text{Code}} + w_2 \cdot S_{\text{Writing}} + w_3 \cdot S_{\text{Register}})$$

**Protocol:** Run Phase 2 ablation sweeps (joint-trained vs. single-axis-only) on the held-out 45-prompt suite. Fit $w_1, w_2, w_3$ via least-squares regression on the ablation scores.

---

## Updated Dataset Blend Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│              Phase 2 Expanded Dataset Blend Architecture                   │
├─────────────────────────────────┬──────────────────────────────────────────┤
│ 25% Format A: Direct Unified    │ Single-turn instruction + .patch diff    │
│              Diff (Alpaca)      │                                          │
├─────────────────────────────────┼──────────────────────────────────────────┤
│ 35% Format B: Agentic Tool      │ Multi-turn ShareGPT tool traces         │
│              Traces (ShareGPT)  │ + Format Disambiguation contrastive     │
├─────────────────────────────────┼──────────────────────────────────────────┤
│ 15% Format C: Multimodal UI/UX  │ SigLIP 2 vision critique + screenshot   │
│              (Eli-VL Vision)    │ ──► TSX + Tailwind                      │
├─────────────────────────────────┼──────────────────────────────────────────┤
│ 10% Format D: Multi-Turn        │ Persona persistence sessions +          │
│              Sessions           │ code review dialogues                    │
├─────────────────────────────────┼──────────────────────────────────────────┤
│ 10% Format E: Capability        │ Debugging, test-writing, refactoring,   │
│              Extensions         │ long-form writing, security, CLI        │
├─────────────────────────────────┼──────────────────────────────────────────┤
│  5% Format F: DPO/SimPO         │ Preference pairs across all axes        │
│              Preference         │ (trained post-SFT, not blended in)      │
└─────────────────────────────────┴──────────────────────────────────────────┘
```

> **Note:** Format F (DPO/SimPO) is trained as a separate post-SFT phase, not blended into the SFT corpus. The 5% allocation refers to its relative data volume, not its position in the training sequence.

---

## Collector Script Inventory

| Script | Priority | Pairs | Output File |
|---|---|---|---|
| `generate_dpo_pairs_v2.py` | 🔴 P0 | 1,200 | `processed/training-data-eli-dpo-v2.jsonl` |
| `generate_format_disambiguation.py` | 🔴 P0 | 1,050 | `processed/training-data-format-*.jsonl` |
| `generate_multiturn_sessions.py` | 🔴 P0 | 200 sessions | `processed/training-data-multiturn-sessions.jsonl` |
| `generate_code_review_critique.py` | 🟠 P1 | 400 | `processed/training-data-code-review-critique.jsonl` |
| `generate_debugging_diagnosis.py` | 🟠 P1 | 450 | `processed/training-data-debugging.jsonl` |
| `generate_test_writing.py` | 🟠 P1 | 250 | `processed/training-data-test-writing.jsonl` |
| `generate_refactoring.py` | 🟠 P1 | 200 | `processed/training-data-refactoring.jsonl` |
| `generate_longform_writing.py` | 🟠 P1 | 150 | `processed/training-data-longform.jsonl` |
| `generate_terminal_fluency.py` | 🟡 P2 | 200 | `processed/training-data-terminal.jsonl` |
| `generate_security_training.py` | 🟡 P2 | 300 | `processed/training-data-security.jsonl` |
| `generate_api_design.py` | 🟡 P2 | 150 | `processed/training-data-api-design.jsonl` |

---

*Epoch Model Suite 1 · Phase 2 Expansion Specification · 2026-07-26*
