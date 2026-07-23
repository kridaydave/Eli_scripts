# Epoch Model Suite 1 — Albert Local-First Story

---

## Thesis

Ship Albert at every quantization. Let hardware decide.

Calibrate at Q8 — but offer FP16, Q8, Q6, Q4, and Q1 so every user gets a version their machine can run.

## Quantization Options

| Quant | Size (approx) | Hardware |
|-------|--------------|----------|
| FP16 / BF16 | ~72 GB | Multi-GPU / server |
| Q8 | ~36 GB | Mac Ultra, dual GPU |
| Q6 | ~28 GB | RTX 5090 |
| Q4 | ~18 GB | RTX 4090 |
| Q1 | ~4 GB | Consumer laptops, edge |

## Principles
- Calibrate at Q8; don't train crippled
- Offer the full spectrum — no user is locked out
- Q4+ on the download page with a recommendation ladder

## Status
**Resolved.** Albert ships local-first for whatever hardware the user has.

---

*Epoch Model Suite 1 · Albert Local Story · 2026-07-21*
