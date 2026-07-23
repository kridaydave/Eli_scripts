# Epoch Model Suite 1 — Step 3: Writing & Wit Specification (Zero-Model / Pure Curation Edition)

**Goal**: Voice, brevity, knowing when not to perform.

## Core Constraint & Principle
**NO MODEL JUDGES / NO LLM SCORERS**. No AI model (proprietary or local 7B) understands the founder's taste or vision for Eli's voice. All quality guarantees must come from **direct human curation** and **deterministic mechanical rules**.

---

## 1. Pure Source Whitelisting (100% Human-Curated Ingress)

Instead of scraping broad text and relying on an AI model to filter it:
- **Whitelisted Author List Only**: Ingest text *only* from explicit, hand-selected engineering blogs, essays, and technical documentation written by proven authors (e.g. Dan Luu, Julia Evans, Brandur Leach, antirez, Martin Fowler, Stripe Engineering Blog).
- **Zero Raw Web Scrapes**: Completely ban indiscriminate web crawling or broad Q&A site dumps.

---

## 2. Deterministic Mechanical & Heuristic Filters ($0 Compute, 0 Models)

Run fast, pure Python deterministic heuristics to filter out structural slop:
- **AI-Slop Cliché Banning**: Hard-coded dictionary ban for generic corporate AI phrasing (`in today's fast-paced world`, `delve`, `tapestry`, `testament to`, `game-changer`, `crucial role`, `it's important to remember`).
- **Sentence-Length Variance $\sigma^2(L_{\text{sent}})$**: Monotonous rhythm (every sentence having identical word count) is rejected automatically via standard deviation math.
- **Lexical Diversity & Repetition**: Measure N-gram redundancy ratios and type-token ratios deterministically.

---

## 3. Human-in-the-Loop Gold Selection

- **Small, Pristine Dataset Size**: Keep the writing corpus tightly constrained to **low hundreds to low thousands** (~500–1,500 pairs).
- **Direct Founder Audit**: Because no model can judge taste, the founder manually reviews and approves every prompt/response pair in the writing pool.

---

## SFT vs DPO Split (Zero Models)

- **SFT**: Hand-selected, founder-approved writing pairs from white-listed engineering sources.
- **DPO**: Pairs created by pairing founder-approved chosen responses against mechanically degraded / cliché-injected rejected responses.
