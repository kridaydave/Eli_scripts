"""
Stream Pillar 2 (Terminal & Shell Operations) real data from HF sources.

Sources:
  - jiacheng-ye/nl2bash           (NL → Bash command pairs)
  - bigcode/the-stack-v3 Shell     (shell scripts, filtered for quality)
  - Synthetic sysadmin/github flows (append to existing)

Writes: processed/pillar2-terminal-ops.jsonl
"""

import json
import random
import re
from pathlib import Path
from datasets import load_dataset

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "processed"
OUT_FILE = PROCESSED_DIR / "pillar2-terminal-ops.jsonl"
TARGET_NL2BASH = 6_000         # NL → Bash command mappings
TARGET_STACK_SHELL = 6_000     # Production shell scripts
TARGET_SYNTHETIC = 1_000       # Sysadmin/git/trouble-shoot pairs

rng = random.Random(2026)


def sanitize_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<(action|command|task|file|profile|step)[^>]*>.*?</\1>", "", text, flags=re.DOTALL)
    text = re.sub(r"</?(action|command|task|file|profile|step)[^>]*>", "", text)
    return text.strip()


def stream_nl2bash(limit: int = TARGET_NL2BASH):
    """NL → Bash command pairs from jiacheng-ye/nl2bash."""
    print(f"  Streaming NL2Bash (target: {limit})...")
    try:
        ds = load_dataset("jiacheng-ye/nl2bash", split="train", streaming=True)
    except Exception as e:
        print(f"    [WARN] Failed: {e}. Skipping.")
        return []

    records = []
    for i, row in enumerate(ds):
        if i >= limit:
            break
        # nl2bash has 'nl' (natural language) and 'bash' fields
        nl = row.get("nl") or row.get("text") or row.get("input", "")
        bash = row.get("bash") or row.get("output") or row.get("target", "")
        nl = sanitize_text(str(nl))
        bash = sanitize_text(str(bash))
        if len(nl) < 20 or len(bash) < 15:
            continue
        # Filter out plain echoed text
        if bash.lower() in nl.lower():
            continue
        records.append({
            "instruction": f"Convert this security task description into the single precise bash command:\n\n{nl}",
            "output": f"```bash\n{bash}\n```",
            "metadata": {
                "pillar": "Pillar 2: Terminal Ops",
                "source": "jiacheng-ye/nl2bash",
                "source_type": "nl_to_bash",
                "language": "bash",
            },
        })
        if (i + 1) % 1000 == 0:
            print(f"    {i+1:,} processed → {len(records):,} kept")
    print(f"  NL2Bash: {len(records):,} pairs")
    return records


def stream_stack_shell(limit: int = TARGET_STACK_SHELL):
    """Production shell scripts from the-stack-v3."""
    print(f"  Streaming Stack-v3 Shell (target: {limit})...")
    try:
        # Try the-stack-v3-smol for local test (smaller)
        ds = load_dataset("bigcode/the-stack-smol", data_dir="data/shell", split="train", streaming=True)
    except Exception as e:
        print(f"    [WARN] Failed: {e}. Skipping.")
        return []

    records = []
    quality_count = 0
    for i, row in enumerate(ds):
        if i >= limit * 3:  # over-sample since we filter hard
            break
        content = row.get("content", "")
        if not isinstance(content, str) or len(content) < 100 or len(content) > 5000:
            continue
        if "#!/" not in content:  # must have shebang
            continue
        # Must have actual logic (loops, conditionals, pipes)
        if not re.search(r"(if |while |for |\| )", content):
            continue
        quality_count += 1
        # Generate a "reverse engineer this script" pair
        records.append({
            "instruction": f"Analyze this Bash script and explain what it accomplishes, then summarize the key commands it uses:\n\n```bash\n{content[:1500]}\n```",
            "output": f"The script uses shell scripting patterns including conditional logic and command pipelines. Key commands appear to include: {extract_key_commands(content)}.\n\n```bash\n{content[:800]}\n```",
            "metadata": {
                "pillar": "Pillar 2: Terminal Ops",
                "source": "bigcode/the-stack-shell",
                "source_type": "shell_script_analysis",
                "language": "bash",
                "script_length": len(content),
            },
        })
        if len(records) >= limit:
            break
    print(f"  Stack Shell: {len(records):,} pairs (from {quality_count:,} quality scripts)")
    return records


def extract_key_commands(content: str) -> str:
    """Extract notable commands from a shell script."""
    cmds = re.findall(r"(?:^|\s)(curl|wget|grep|awk|sed|find|xargs|tar|gzip|ssh|scp|rsync|docker|git|systemctl|journalctl|chown|chmod|kill|ps|netstat|ss|top|htop|df|du)\s", content)
    seen = []
    for c in cmds:
        if c not in seen:
            seen.append(c)
    return ", ".join(seen[:5]) or "shell utilities"


def generate_synthetic_sysadmin(n: int = TARGET_SYNTHETIC):
    """Synthetic sysadmin/git/troubleshooting pairs."""
    print(f"  Generating synthetic sysadmin pairs (target: {n})...")
    scenarios = [
        ("find all .log files older than 7 days and compress them", "find /var/log -name '*.log' -mtime +7 -exec gzip {} \\;"),
        ("check which process is using port 8080", "lsof -i :8080"),
        ("show last 20 lines of system journal for nginx", "journalctl -u nginx -n 20 --no-pager"),
        ("find the top 5 memory consuming processes", "ps aux --sort=-%mem | head -6"),
        ("count failed SSH attempts by IP", "grep 'Failed password' /var/log/auth.log | awk '{print $NF}' | sort | uniq -c | sort -rn | head"),
        ("recover deleted file from git history", "git log --all --full-history --oneline -- '*/deleted_file.py'"),
        ("find files modified in last 30 minutes", "find / -mmin -30 -type f 2>/dev/null"),
        ("show disk usage in human readable format", "df -h"),
        ("monitor a file for new appended lines", "tail -f /var/log/app.log"),
        ("kill all processes matching 'worker'", "pkill -f worker"),
        ("list all listening TCP ports with process names", "ss -tlnp"),
        ("find all files with SUID bit set", "find / -perm /4000 -type f 2>/dev/null"),
        ("check systemd service status and recent logs", "systemctl status nginx --no-pager -l"),
        ("sync local directory to remote server via ssh", "rsync -avz --progress /local/path/ user@remote:/remote/path/"),
        ("show network connections to external hosts", "netstat -tunapl 2>/dev/null | ESTABLISHED"),
        ("find which package owns a file", "dpkg -S /usr/bin/awk 2>/dev/null || rpm -qf /usr/bin/awk"),
        ("create a self-signed TLS certificate", "openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem"),
        ("extract specific columns from CSV using awk", "awk -F',' '{print $1, $3}' file.csv"),
        ("watch memory usage in real-time", "watch -n 1 free -m"),
        ("backup mysql database with compression", "mysqldump -u root -p mydb | gzip > backup_$(date +%Y%m%d).sql.gz"),
    ]
    records = []
    for i in range(n):
        q, a = scenarios[i % len(scenarios)]
        records.append({
            "instruction": q[0].upper() + q[1:] + "?",
            "output": f"```bash\n{a}\n```",
            "metadata": {
                "pillar": "Pillar 2: Terminal Ops",
                "source": "synthetic_sysadmin",
                "source_type": "cli_troubleshooting",
                "language": "bash",
            },
        })
    print(f"  Synthetic: {len(records):,} pairs")
    return records


def main():
    print("=== STREAMING PILLAR 2: TERMINAL & SHELL OPERATIONS ===")
    all_records = []
    all_records.extend(stream_nl2bash())
    all_records.extend(stream_stack_shell())
    all_records.extend(generate_synthetic_sysadmin())

    rng.shuffle(all_records)
    print(f"\nTotal Pillar 2: {len(all_records):,}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved to {OUT_FILE}")


if __name__ == "__main__":
    main()
