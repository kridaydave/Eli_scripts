"""
Clone top backend and frontend repos, extract signal-rich files.

Signals extracted:
  - Commit messages with "refactor", "fix", "review" markers
  - Key source files (non-test, non-vendor, non-generated)
  - PR-like discussion in commit messages
  - Test files for pattern reference

Output:
  raw/github/backend/<repo>/    — source.json + commits.json + files/
  raw/github/frontend/<repo>/   — same structure

Usage:
  python collect_github.py --depth 1    # shallow clones (fast, ~2-5GB)
  python collect_github.py --full        # full history (slow, ~15GB+)
  python collect_github.py --lane backend  # only backend repos
  python collect_github.py --lane frontend # only frontend repos
"""

import json
import sys
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import GITHUB_BACKEND, GITHUB_FRONTEND

BACKEND_REPOS = [
    # C / OS Core (The Gold Standard)
    "https://github.com/torvalds/linux.git",
    # Go
    "https://github.com/kubernetes/kubernetes.git",
    "https://github.com/etcd-io/etcd.git",
    "https://github.com/traefik/traefik.git",
    "https://github.com/hashicorp/consul.git",
    "https://github.com/minio/minio.git",
    "https://github.com/prometheus/prometheus.git",
    "https://github.com/cockroachdb/cockroach.git",
    # Python
    "https://github.com/django/django.git",
    "https://github.com/encode/django-rest-framework.git",
    "https://github.com/tiangolo/fastapi.git",
    "https://github.com/getsentry/sentry.git",
    # Rust
    "https://github.com/tokio-rs/tokio.git",
    "https://github.com/vectordotdev/vector.git",
    "https://github.com/firecracker-microvm/firecracker.git",
    # TypeScript
    "https://github.com/nestjs/nest.git",
    "https://github.com/trpc/trpc.git",
    "https://github.com/calcom/cal.com.git",
    # Java
    "https://github.com/spring-projects/spring-boot.git",
    "https://github.com/elastic/elasticsearch.git",
    "https://github.com/apache/kafka.git",
]

FRONTEND_REPOS = [
    "https://github.com/shadcn-ui/ui.git",
    "https://github.com/radix-ui/primitives.git",
    "https://github.com/mantinedev/mantine.git",
    "https://github.com/ant-design/ant-design.git",
    "https://github.com/chakra-ui/chakra-ui.git",
    "https://github.com/xyflow/xyflow.git",
    "https://github.com/tailwindlabs/tailwindcss.git",
    "https://github.com/adobe/react-spectrum.git",
    "https://github.com/mui/material-ui.git",
    "https://github.com/vercel/geist-font.git",
    "https://github.com/saadeghi/daisyui.git",
    "https://github.com/tremorlabs/tremor.git",
    "https://github.com/storybookjs/storybook.git",
    "https://github.com/radix-ui/themes.git",
]

EXTENSIONS = {
    "backend": {".c", ".h", ".go", ".py", ".rs", ".java", ".ts", ".mod", ".sum"},
    "frontend": {".tsx", ".ts", ".jsx", ".js", ".css", ".scss", ".vue", ".svelte"},
}

SKIP_DIRS = {
    "node_modules", ".git", "vendor", "__pycache__", ".next", "dist",
    "build", "target", ".venv", "venv", "env", ".tox",
}


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if result.returncode != 0:
        print(f"  Warning: {' '.join(cmd[:2])} failed: {result.stderr[:200]}")
    return result.stdout


def get_repo_name(repo_url: str) -> str:
    return repo_url.split("/")[-1].replace(".git", "")


def clone_repo(repo_url: str, dest: Path, depth: int | None = 1) -> bool:
    if (dest / ".git").exists():
        print(f"  Already cloned, pulling...")
        try:
            run(["git", "pull", "--ff-only"], cwd=dest, timeout=300)
        except Exception as e:
            print(f"  Pull timed out or failed: {e}, skipping pull")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone"]
    if depth:
        cmd.extend(["--depth", str(depth)])
    cmd.extend([repo_url, str(dest)])
    print(f"  Cloning...")
    try:
        run(cmd, timeout=600)
        return True
    except Exception as e:
        print(f"  Clone failed: {e}")
        return False


def extract_commits(repo_path: Path, max_count: int = 2000) -> list[dict]:
    """Extract commit messages with relevant keywords."""
    log = run([
        "git", "log", f"--max-count={max_count}",
        "--format=%H|%ai|%an|%s",
        "--no-merges",
    ], cwd=repo_path, timeout=120)

    commits = []
    keywords = {"refactor", "fix", "review", "cleanup", "rewrite", "redesign",
                 "improve", "optimize", "extract", "deduplicate", "simplify"}
    for line in log.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        sha, date, author, msg = parts
        matched = [kw for kw in keywords if kw in msg.lower()]
        if matched:
            commits.append({
                "sha": sha,
                "date": date,
                "author": author,
                "message": msg,
                "tags": matched,
            })

    print(f"  Extracted {len(commits)} signal-rich commits")
    return commits


def extract_source_files(repo_path: Path, lane: str) -> list[dict]:
    """Walk repo and collect non-test, non-vendor source files."""
    exts = EXTENSIONS[lane]
    files = []
    for fpath in repo_path.rglob("*"):
        if fpath.suffix not in exts:
            continue
        rel = fpath.relative_to(repo_path)
        parts = rel.parts
        if any(skip in parts for skip in SKIP_DIRS):
            continue
        if fpath.stat().st_size > 500_000:
            continue
        if "/test" not in str(rel).lower() and "test_" not in rel.name and "_test" not in rel.name:
            files.append({
                "path": str(rel),
                "size": fpath.stat().st_size,
                "ext": fpath.suffix,
            })
        elif "test" in rel.name.lower() or "/test" in str(rel).lower():
            files.append({
                "path": str(rel),
                "size": fpath.stat().st_size,
                "ext": fpath.suffix,
                "is_test": True,
            })
    print(f"  Found {len(files)} source files")
    return files


def process_repo(repo_url: str, lane: str, depth: int | None = 1):
    name = get_repo_name(repo_url)
    dest = (GITHUB_BACKEND if lane == "backend" else GITHUB_FRONTEND) / name
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / "meta.json"

    if out.exists():
        print(f"[{name}] Already processed")

    print(f"[{name}] Starting...")

    if not clone_repo(repo_url, dest / "repo", depth=depth):
        return

    repo_path = dest / "repo"
    commits = extract_commits(repo_path)
    source_files = extract_source_files(repo_path, lane)

    meta = {
        "repo": name,
        "url": repo_url,
        "lane": lane,
        "commits_signal": len(commits),
        "source_files": len(source_files),
        "source_file_list": source_files[:500],
        "commits": commits[:500],
        "test_files": [f for f in source_files if f.get("is_test")][:200],
    }
    with open(out, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[{name}] Done — {len(commits)} signal commits, {len(source_files)} files")
    dest.mkdir(parents=True, exist_ok=True)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=["backend", "frontend", "all"], default="all")
    parser.add_argument("--depth", type=int, default=1, help="Git clone depth (1=shallow)")
    args = parser.parse_args()

    if args.lane in ("backend", "all"):
        print(f"\n=== Backend ({len(BACKEND_REPOS)} repos) ===")
        for repo in BACKEND_REPOS:
            process_repo(repo, "backend", depth=args.depth)

    if args.lane in ("frontend", "all"):
        print(f"\n=== Frontend ({len(FRONTEND_REPOS)} repos) ===")
        for repo in FRONTEND_REPOS:
            process_repo(repo, "frontend", depth=args.depth)

    print("\nDone.")


if __name__ == "__main__":
    main()
