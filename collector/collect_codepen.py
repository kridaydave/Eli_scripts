"""
Collect CodePen pens from top creators and trending feeds.

Two modes:
  --mode api       Fetch via CodePen API (public, no key needed for user pens)
  --mode apify     Use Apify CodePen Scraper actor (requires APIFY_TOKEN)

Output: raw/codepen/<creator>.json — pen HTML/CSS/JS per creator

Usage:
  python collect_codepen.py --mode api                  # 22 known creators
  python collect_codepen.py --mode api --trending 200    # trending pens
  python collect_codepen.py --mode apify --trending 500  # via Apify (needs token)
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CODEPEN

CREATORS = [
    "thebabydino", "ivorjetski", "jh3y", "sdras", "terabaud",
    "yuanchuan", "argyleink", "davidkpiano", "shubniggurath",
    "michellebarker", "alvaromontoro", "cassie-codes", "ste-vg",
    "cobra_winfrey", "hexagoncircle", "lynnandtonic", "ilithya",
    "Mamboleoo", "DonKarlssonSan", "rachsmith", "tmrDevelops",
    "jakealbaugh", "hakimel", "sashatsit",
]


def extract_pen_data(raw: dict) -> dict:
    """Extract relevant fields from a CodePen API response."""
    return {
        "id": raw.get("id"),
        "title": raw.get("title", ""),
        "html": raw.get("html", ""),
        "css": raw.get("css", ""),
        "js": raw.get("js", ""),
        "tags": raw.get("tags", []),
        "hearts": raw.get("hearts", 0),
        "views": raw.get("views", 0),
        "comments": raw.get("comments", 0),
        "created_at": raw.get("created_at", ""),
        "url": raw.get("url", ""),
    }


async def fetch_user_pens(client: httpx.AsyncClient, username: str, limit: int = 100) -> list[dict]:
    """Fetch public pens for a user via CodePen API."""
    pens = []
    page = 1
    while len(pens) < limit:
        url = f"https://cpv2api.com/pens/public/{username}?page={page}&limit=25"
        try:
            resp = await client.get(url, timeout=30)
            if resp.status_code != 200:
                break
            data = resp.json()
            batch = data.get("data", [])
            if not batch:
                break
            for pen in batch:
                pens.append(extract_pen_data(pen))
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break
    return pens[:limit]


async def fetch_trending_from_apify(client: httpx.AsyncClient, count: int = 500, token: str = "") -> list[dict]:
    """Fetch trending pens via Apify CodePen Scraper."""
    if not token:
        print("  No APIFY_TOKEN set. Skipping Apify trending.")
        return []

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "searchType": "trending",
        "maxItems": count,
        "proxyConfiguration": {"useApifyProxy": True},
    }
    try:
        resp = await client.post(
            "https://api.apify.com/v2/acts/motty~codepen-scraper/runs",
            headers=headers, json=payload, timeout=60
        )
        if resp.status_code != 201:
            print(f"  Apify run failed: {resp.text[:200]}")
            return []
        run_data = resp.json()
        run_id = run_data.get("data", {}).get("id")
        if not run_id:
            return []
        print(f"  Apify run started: {run_id}")

        for _ in range(60):
            time.sleep(10)
            status_resp = await client.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}",
                headers=headers, timeout=30
            )
            status = status_resp.json().get("data", {}).get("status", "")
            if status == "SUCCEEDED":
                break
            elif status in ("FAILED", "TIMED-OUT", "ABORTED"):
                print(f"  Apify run {status}")
                return []

        dataset_resp = await client.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
            headers=headers, timeout=60
        )
        items = dataset_resp.json()
        return [extract_pen_data(item) for item in items]
    except Exception as e:
        print(f"  Apify error: {e}")
        return []


def save_pens(username: str, pens: list[dict]):
    out_file = CODEPEN / f"{username}.json"
    with open(out_file, "w") as f:
        json.dump({"username": username, "count": len(pens), "pens": pens}, f, indent=2)
    print(f"  Saved {len(pens)} pens to {out_file.name}")


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["api", "apify"], default="api")
    parser.add_argument("--trending", type=int, default=0, help="Fetch N trending pens")
    parser.add_argument("--token", default="", help="Apify API token")
    args = parser.parse_args()

    import os
    token = args.token or os.environ.get("APIFY_TOKEN", "")

    CODEPEN.mkdir(parents=True, exist_ok=True)

    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(limits=limits, timeout=30) as client:
        for username in CREATORS:
            print(f"[{username}] Fetching up to 100 pens...")
            pens = await fetch_user_pens(client, username, limit=100)
            if pens:
                save_pens(username, pens)
            else:
                print(f"  No pens found, saving empty")

        if args.trending > 0:
            print(f"\n[trending] Fetching {args.trending} pens via {args.mode}...")
            if args.mode == "apify" and token:
                trending = await fetch_trending_from_apify(client, args.trending, token)
            else:
                trending = await fetch_user_pens(client, "codepen", limit=args.trending)
            if trending:
                save_pens("trending", trending)

        manifest = {
            "collected_at": datetime.utcnow().isoformat(),
            "mode": args.mode,
            "creators_count": len(CREATORS),
            "trending_count": args.trending,
        }
        with open(CODEPEN / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

    print("\nDone.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
