# Epoch Model Suite 1 — Step 1: Code Specification

**Goal**: Correct, idiomatic, appropriately-abstracted code — not clever, not over-engineered.

## Sourcing

- **Base pool**: Stack v2 / Stack v2 Edu (permissive license solved, has built-in 0-5 educational quality score)
- **Filter down to**: small-to-medium focused libraries over large apps; repos with tests; recent (last ~2 yrs); single-language dominant
- **Supplement with synthetic**: generate problem→solution pairs via a strong teacher model, specifically asking for "the tasteful version" vs "the over-engineered version" vs "the under-engineered version" as contrastive triples

## Filtering Pipeline

- **Stack v2 Edu score threshold**: free quality signal
- **Static pass**: linter/formatter compliance (ruff, eslint) — if it needs major reformatting, deprioritize
- **Complexity check**: cyclomatic complexity vs function length — flags both over- and under-abstraction
- **Dedup aggressively (MinHash/LSH)**: repeated CRUD/auth boilerplate is exactly what drags a 4B model toward mediocrity

## SFT vs DPO Split

- **SFT**: clean solved problems, mixed difficulty, heavy on small well-tested libraries
- **DPO (Self-distillation)**: sample multiple candidate solutions per prompt from your SFT checkpoint, verify correctness by execution (tests/linting) where possible — code is the one axis where you get free, bias-free verification signal, use it before falling back to judge-model scoring
- **For style preference specifically**: contrastive triples (tasteful vs over-engineered vs under-engineered)
