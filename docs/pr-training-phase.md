# Closed PR Training Phase (Phase 2 Specification)

---

## Executive Summary

This specification defines **Phase 2: Closed PR Training**, a core component of Epoch's data pipeline. This phase trains models on real-world merged GitHub Pull Requests to bridge the gap between synthetic single-turn code generation and real-world software engineering (surgical edits, repo navigation, edge-case handling, and architectural cohesion).

---

## 1. Anti-Cheating & Integrity Safeguards

### A. Runtime Tool-Use Anti-Cheating
To prevent the agent from querying repository commit history during training/inference:
- **`.git` Directory Removal:** Strip all `.git`, `.github`, and `.gitmodules` directories from the target workspace before mounting it into the model execution sandbox.
- **Git Metadata Purge:** Remove commit history logs, `CHANGELOG.md` unmerged stubs, and inline commit hashes from the repository sandbox so execution tools (`bash`, `view_file`, `grep_search`) cannot inspect past commits or merged PR diffs.

### B. Pre-Training Memorization Prevention (Eval Set Isolation)
- Base models (Qwen-3, Llama 3) have scraped public GitHub prior to their training cutoff.
- **Eval Set Protocol:** All evaluation benchmark PRs must be sourced exclusively from PRs merged **after the base model's pre-training cutoff date** (or from private, held-out repositories) to prevent memorized retrieval leakage.

---

## 2. PR Sourcing & Quality Filters

Raw merged PRs are heavily contaminated with trivial edits, dependency bumps, and noisy refactors. The pipeline enforces 4 automated quality filters:

### Tier 1 — Exclusion Criteria (Drop Sample)
- ❌ **Automated / Bot PRs:** Author is a bot (Dependabot, Renovate, Snyk).
- ❌ **Trivial Edits:** Changes touch only `.md`, `.txt`, `.gitignore`, `LICENSE`, or `package-lock.json`.
- ❌ **Mega-PRs:** Touches $> 10$ files or $> 300$ total modified lines (causes context blowup and teaches sloppy diffs).
- ❌ **Zero-Context PRs:** PR description + linked issue contains $< 15$ words of descriptive text or consists solely of `"wip"`, `"fixes"`, or `"pr review fixes"`.

### Tier 2 — Acceptance Criteria (Gold Sample)
- ✅ **Surgical Scope:** 1 to 5 files modified; 15 to 150 lines changed.
- ✅ **Test Inclusion:** PR includes changes/additions to test files (`*.spec.ts`, `test_*.py`, `*_test.go`, etc.).
- ✅ **Clear Issue Context:** Includes issue description, expected vs actual behavior, or reproduction steps.

---

## 3. Context Packaging & Sandbox Structure

Each training pair is constructed by restoring the repository to its **`base_commit` state** (the commit immediately preceding the PR merge):

```
                       ┌────────────────────────┐
                       │  Repository Snapshot   │
                       │    at base_commit      │
                       └───────────┬────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │  Strip .git & Metadata      │
                    └──────────────┬──────────────┘
                                   │
   ┌───────────────────────────────┴───────────────────────────────┐
   │                                                               │
   ▼                                                               ▼
[Prompt Packaging]                                         [Target Output]
- Issue / PR Description                                   - Surgical Unified Diff (.patch)
- File Tree at base_commit                                  OR
- Relevant Source File Snippets                             - Multi-turn Tool Traces (ShareGPT)
```

---

## 4. Dual Training Formats

PR data is ingested into two distinct formats:

### Format A: Direct Unified Diff SFT (Alpaca Single-Turn)
- **Instruction:** Problem description + target file path & current snippet.
- **Output:** Clean, compilable `.patch` diff block.

### Format B: Agentic Multi-Turn Tool Trace (ShareGPT Multi-Turn)
- **Turn 1 (User):** Issue description.
- **Turn 2 (Assistant):** `<tool_call: grep_search("error_handler")>`
- **Turn 3 (Tool):** File locations returned.
- **Turn 4 (Assistant):** `<tool_call: view_file("src/server.ts")>`
- **Turn 5 (Tool):** File content at `base_commit`.
- **Turn 6 (Assistant):** `<tool_call: replace_file_content(...)>` (Applying surgical patch).

---

## 5. Execution Verification (CI Test Pass)

Before inclusion in the final training dataset:
1. Run pre-PR test suite on `base_commit` snapshot $\rightarrow$ **Assert failure** (reproves the bug).
2. Apply candidate PR patch $\rightarrow$ Run test suite $\rightarrow$ **Assert green pass** (verifies fix correctness).
3. Only green-verified PR transitions are serialized into `processed/training-data-pr-phase.jsonl`.

---

*Epoch Model Suite 1 · Closed PR Training Phase Specification · 2026-07-22*
