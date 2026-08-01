# Eli Retraining Plan (Phase 1 & Phase 2 Blueprint)

> **Goal**: Retrain Eli from scratch on Qwen3-4B-Instruct using a clean, 3-pillar dataset mix (Core Coding, Terminal Ops, **Cybersecurity Operations — offensive kernel + defensive/HUMINT canopy**) to eliminate format contamination, tool-call hallucinations, and function renaming errors.
>
> **Vision**: Small teams cannot pay API-tax to a 1T-parameter frontier model to stop being hacked. Eli is a **$0 marginal security pair-programmer** — capable of running an authorized pentest (recon → exploit → report) *and* patching the vulnerability it just found. Offense capability is the *substrate* of defense capability: you cannot secure what you cannot break yourself.

---

## Executive Summary of Strategy Pivot

### Why We Retrain From Scratch
The initial Phase 1 training run (using Fable-5 trajectory data) caused severe format collapse:
- **XML Tag Contamination**: Outputting `<name>Eli</name>`, `<action>`, `<task>` tags instead of clean code.
- **Tool-Call Hallucinated Traces**: Generating mock terminal outputs and mock file-system operations.
- **Function Renaming**: Changing function names requested by evaluation prompts (e.g. `is_point_in_bbox` $\rightarrow$ `point_in_box`).
- **Language Drift**: Randomly generating JavaScript/C++ when Python was requested.

### New Core Principle
**No synthetic trajectory/tool-call copying, EXCEPT within the Cyber pillar's CoT CoT reasoning — where terminal output analysis *is* the native reasoning the policy must learn.**
- For Core Coding + Terminal Ops pillars: the model generates pure code and clean `<think>` blocks, relying on its own native reasoning capacity.
- For the Cyber pillar's **CoT / Agentic lane**: the model reasons through messy terminal outputs, log captures, and multi-step attack/defense workflows inside (but *not* copying gold tool-call transcripts — it learns to reason like an agent, not to recite agent logs).
- All cybersecurity examples carry an explicit **authorization frame** (own infrastructure, CTF/lab, in-scope bug bounty, DVWA, HTB, sanctioned engagement). This is the HUMINT filter that distinguishes a capable assistant from a malicious one.

---

## 3-Pillar Dataset Architecture & Final Selections

```
                                  ┌───────────────────────────────────────────┐
                                  │          ELI TRAINING CURRICULUM          │
                                  └───────────────────────────────────────────┘
                                                        │
         ┌──────────────────────────────────────────────┼──────────────────────────────────────────────┐
          ▼                                              ▼                                              ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐              ┌──────────────────────────────┐
│  Pillar 1: Core Coding       │              │  Pillar 2: Terminal & Shell  │              │  Pillar 3: CYBERSECURITY     │
│  & Algorithms (60%)          │              │  Operations (20%)            │              │  OPERATIONS & SECURE-PATCH   │
│  [UNCHANGED]                 │              │  [UNCHANGED]                 │              │  [REDESIGNED — offensive     │
│                              │              │                              │              │   kernel + defensive canopy]  │
└──────────────────────────────┘              └──────────────────────────────┘              └──────────────┬───────────────┘
                                                                                                           │
   • Dataset: The Stack v3                    • 40% NL2Bash (`baisang/nl2bash`)                               │
   • Focus: Python, TS/JS, C++,               • 40% The Stack v3 Shell/Zsh/PS                 ┌─────────────┴─────────────┐
     Go, Rust                                 • 20% Sysadmin/Git Troubleshooting              ▼  Lane Mix (within 20%)    ▼
   • Method: Docstring &                        CLI pipelines, POSIX scripts,         ┌────────────────────────────────────┐
     signature extraction for                   `strace`, `lsof`, `journalctl`        │ O) Offensive Tooling / NL→CLI  30% │
     exact function name adherence                                                  │   • Canstralian/pentesting_dataset │
                                                                                    │   • Canstralian/ShellCommands      │
                                                                                    │   • Trendyol Cyber-Instruction     │
                                                                                    │ A) Agentic Traces & CTF CoT    25% │
                                                                                    │   • WhitzardAgent/CyberSecurity-1M │
                                                                                    │   • expertdata-factory/Cybersec-CoT│
                                                                                    │ V) Vulnerability Knowledge     20% │
                                                                                    │   • iamthierno/cvedataset.jsonl    │
                                                                                    │   • Canstralian/CyberExploitDB     │
                                                                                    │ D) Defensive Patch & CTF       25% │
                                                                                    │ D) Defensive Patch & CTF       25% │
                                                                                    │   • PrimeVul/DiverseVul (retained) │
                                                                                    │   • Cybench/InterCode static CoT   │
                                                                                    │     distillations ONLY (RL moved │
                                                                                    │     to Phase 3 interactive envs)   │
                                                                                    └────────────────────────────────────┘
```

---

## Detailed Pillar Specifications

### Pillar 1: Core Coding & Production Software (60%)
- **Primary Source**: `HuggingFaceCode/stack-v3-train`
- **Languages**: Python (40%), TypeScript/JavaScript (25%), C/C++ (15%), Go (10%), Rust (10%).
- **Processing Method**: Docstring and signature extraction. Convert raw functions into problem-solution pairs where the user prompt contains the docstring/signature, and the target response contains the exact implementation. This guarantees **100% function signature alignment**.
- **Formatting Standard**:
  ```markdown
  ### User:
  [Problem description + exact function signature]

  ### Assistant:
  <think>
  [Native algorithmic reasoning]
  </think>

  ```python
  [Clean, executable code adhering strictly to the function name]
  ```
  ```

---

### Pillar 2: Terminal Navigation & Shell Operations (20%)
- **Primary Sources**:
  1. `jiacheng-ye/nl2bash` (40%): Natural language to clean CLI pipelines (`find`, `grep`, `sed`, `awk`, `xargs`).
  2. `bigcode/the-stack-v3` Shell Subset (40%): Production Bash, Zsh, and PowerShell automation scripts with `set -euo pipefail`.
  3. Synthetic Sysadmin & Troubleshooting (20%): Environment setup, Git workflows (`bisect`, `rebase`), and system diagnostics (`htop`, `strace`, `lsof`, `journalctl`).
- **Formatting Standard**:
  ```markdown
  ### User:
  Write a robust Bash script to recursively find all `.log` files older than 7 days, compress them into `.tar.gz`, and remove the originals with error handling.

  ### Assistant:
  <think>
  [Script design: error handling with set -euo pipefail, finding files safely]
  </think>

  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  ...
  ```
  ```

---

### Pillar 3: Cybersecurity Operations & Secure-Patch — 4-Lane Architecture (20%)

> **Rationale**: Small teams can't afford a 1T-parameter hosted SOC. Eli must be able to *run* an authorized pentest (recon → exploit → report) AND close the vulnerability it found. Offense capability is the substrate of defense capability: you cannot secure what you cannot break yourself.
>
> Every cyber example carries an explicit **authorization frame** in its prompt metadata (own infra / lab / CTF / in-scope bounty / sanctioned engagement). This is the temporal authority filter that distinguishes a capability assistant from a malicious request.

#### Lane O — Offensive Tooling & NL→CLI Translation (30% of Pillar 3)
Teaches the model direct natural-language → security CLI mapping for authorized engagements.
- **Primary Sources**:
  1. `Canstralian/pentesting_dataset` — NL → exact `nmap`/Metasploit/`sqlmap` commands with flags and explanations.
  2. `Canstralian/ShellCommands` — curated security shell one-liners and tool invocations.
  3. `Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset` — incident response vs. pentest framing, command execution, tool selection across OS environments.
- **Method**: Map each record to *(authorized goal) → (exact command + brief rationale)*, stripping any real target IPs/domains and replacing them with RFC 1918/TEST-NET placeholders.
- **Formatting Standard**:
  ```markdown
  [SCOPE: lab | ctf | own-infra | in-scope-bounty]
  ### User:
  Map the open services on my lab server 10.10.0.5 and save output to `scan.xml`.

  ### Assistant:
  <think>
  Need service/version detection + XML output; nmap -sV -oX covers both.
  </think>

  ```bash
  nmap -sV -sC -oX scan.xml 10.10.0.5
  ```
  ```

#### Lane A — Agentic Traces & CTF Reasoning (CoT) (25% of Pillar 3)
Teaches multi-step recon/exploit/move workflow reasoning over messy terminal output — the "read the nmap/pwn tools output, decide the next comman" skill.
- **Primary Sources**:
  1. `WhitzardAgent/CyberSecurity-1M` — multi-step agentic attack/defense workflow traces.
  2. `expertdata-factory/cybersecurity-reasoning-cot-v1` — step-by-step CoT over CLI output, network captures, and logs.
- **Method**: Convert traces to clean `<think>` reasoning + one concrete command per step. Immutable trajectory logs are NOT copied verbatim; the model learns to produce its *own* reasoning, not recite logs.
- **Formatting Standard**:
  ```markdown
  ### User:
  You're on a sanctioned HTB box. `nmap` shows 22/80/445 open, Apache 2.4.49. What's next?

  ### Assistant:
  <think>
  Apache 2.4.49 → CVE-2021-41773 path traversal; 445 → check smb null sessions.
  </think>

  ```bash
  curl -s --path-as-is "http://10.10.0.5/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd"
  ```
  ```

#### Lane V — Vulnerability Knowledge Graph (CVE → Exploit Context) (20% of Pillar 3)
Teaches the model to look up a version in terminal output and connect it to applicable CVEs, CVSS severity, and mitigation strategy.
- **Primary Sources**:
  1. `iamthierno/cvedataset.jsonl` — structured CVE records (1999–present) with CVSS, affected software, references.
  2. `Canstralian/CyberExploitDB` — parsed ExploitDB entries mapped to runnable command scripts/shellcode parameters.
- **Method**: Format as *(service/version in output) → (matching CVE + severity + safe remediation + authorized exploit reference)*.
- **Formatting Standard**:
  ```markdown
  ### User:
  Found `vsftpd 2.3.4` on 10.10.0.5. Assess risk and recommend action.

  ### Assistant:
  <think>
  vsftpd 2.3.4 → CVE-2011-2523 (backdoor RCE, CVSS 7.5); patch = upgrade to 3.0.5.
  In a sanctioned test: Metasploit `exploit/unix/ftp/vsftpd_234_backdoor`.
  </think>

  **Risk**: vsftpd 2.3.4 ships with a known backdoor (CVE-2011-2523). An attacker can gain a root shell by appending `:)` to the username.
  **Remediation** (production): upgrade to vsftpd ≥ 3.0.5, disable anonymous FTP.
  **Authorized validation** (lab/HTB only):
  ```bash
  msfconsole -q -x "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.0.5; run"
  ```
  ```

#### Lane D — Defensive Patch & Static CTF Distillations (25% of Pillar 3)
Teaches the model to produce zero-regression secure patches and to *close the loop* on vulnerabilities it just discovered.

- **Primary Sources**:
  1. `starsofchance/PrimeVul` & `claudios/DiverseVul` — memory-safety CVE diffs in C/C++/Python/Go (Buffer Overflow, UAF, Double Free, Leak).
  2. `walledai/CyberSecEval` / `Virtue-AI-HUB/SecCodePLT` — web/API vulns (SQLi, XSS, SSRF, Path Traversal, Auth bypass).
  3. **Static CoT distillations FROM Cybench/InterCode solves** (text-only), generated by running actual solves and recording the reasoning trace.

- **⚠️ CRITICAL MIGRATION:** The *interactive* Cybench/InterCode environments are **Phase 3 RL environments**, not SFT data. Lane D only contains the post-solve written summaries/patch recommendations. The live containers belong to `eli_unified_rl_env.py`.
- **Formatting Standard**:
  ```markdown
  ### User:
  The planted web app on my lab is vulnerable: [vulnerable code]. Explain the flaw and patch it.

  ### Assistant:
  <think>
  Root cause: f-string SQL query = SQLi. Patch: parameterized query + input validation.
  </think>

  **Flaw**: SQL Injection via unparameterized query.
  **Patch**:
  ```python
  query = "SELECT * FROM users WHERE id = :uid"
  db.execute(query, {"uid": user_id})
  ```
  ```

#### HUMINT Anchor (small refusal slice, ~2% of Pillar 3)
- In-scope refusal examples: "Exploit X on `google.com` (out of scope)" → `"I can't run attacks against third-party infrastructure you don't own, but if you spin up DVWA/HTB I can walk through the exact same exploit against your lab box."`
- Purpose: keeps the HUMINT filter trained — capability without indiscriminate help.

---

## Quality Control & Automated Sanitization Filters

To prevent repeating Phase 1 trajectory errors, all dataset entries must pass 4 automated filters during compilation:

1. **NO Trajectory Tags**: Strip all `<action>`, `<command>`, `<task>`, `<file>`, and profile XML metadata.
2. **Exact Signature Check**: Verify that the function name in the response target matches the requested function name in the prompt.
3. **Language Match Filter**: Ensure code block language tags (`python`, `bash`, `c`, `javascript`) strictly match the requested prompt language.
4. **Clean Block Formatting**: Ensure every output contains at most one `<think>` block followed by clean code/script blocks.
5. **Authorization-Frame Filter** *(new)*: Every Pillar 3 offensive example must carry a scope tag (`lab`, `ctf`, `own-infra`, `in-scope-bounty`, `CVE-lookup`) in metadata, and any hard-coded third-party IP/domain is rewritten to RFC 1918 (`10.0.0.0/8`) or TEST-NET placeholders.
6. **CVE Validity Check** *(new)*: Lane V records must reference a CVE-ID that exists in the NVD-format record (regex `CVE-\d{4}-\d{4,7}`) — prevents hallucinated CVEs.

---

## Action Plan & Roadmap

- [ ] **Step 1: Baseline Benchmark**: Complete base `unsloth/Qwen3-4B-Instruct-2507` evals across all 3 sets (`run_all_eli_evals.py`) to establish baseline Pass@1 targets.
- [ ] **Step 2: Dataset Compilation Script**: Update `collector/prepare_eli_dataset.py` to pull, filter, format, and merge the 3 pillars into `kridaydave/eli-phase1-clean` (P1 + P2 unchanged; P3 now loads the 4-lane cyber mix with authorization-frame filtering).
- [ ] **Step 3: Training Config Setup**: Configure Unsloth SFT script for Qwen3-4B base, LoRA rank $r=32$, $\alpha=64$, learning rate $2 \times 10^{-4}$, max sequence length 4096.
- [ ] **Step 4: Clean Phase 1 Training**: Execute training run.
- [ ] **Step 5: Full Evaluation**: Run `run_all_eli_evals.py` on new checkpoint to compare against base model benchmark.
