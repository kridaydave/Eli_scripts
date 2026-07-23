# Epoch Model Suite 1 — Step 2: Frontend Specification

**Goal**: Visual taste + code that produces it. Hardest axis — no shortcut dataset exists, you have to build the render→judge loop yourself.

## Sourcing

- **Component source**: `shadcn/ui`, `Radix primitives`, well-regarded design-system OSS (Vercel, etc.) rather than generic tutorial React
- **Curated showcases**: Awwwards-adjacent, curated CodePen collections — scrape underlying code where licensing allows

## Filtering Pipeline

- **Render every candidate headlessly (Playwright/Puppeteer screenshot)**: Non-negotiable, code alone can't be judged for this axis
- **Judge scores the image**: spacing consistency, color restraint, hierarchy, "template vs decision" test
- **Cross-check code quality against visual quality**: mismatches (clean code/bad render or vice versa) are useful contrastive signal — don't discard them, use them
- **Internal Tooling**: Build this render-judge loop as a small internal tool early since you'll iterate on it constantly

## SFT vs DPO Split

- **SFT**: components that pass both code-clean and visually-clean bars
- **DPO**: pairs generated from your own model at different "restraint dials" (minimal / default / over-decorated), ranked by the image judge — natural self-distillation setup by varying prompting on your own checkpoint and letting the render+judge pick winners
