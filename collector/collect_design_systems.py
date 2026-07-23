"""
Scrape design system documentation pages for code examples, usage guidelines,
and design decision docs.

Output: raw/design-systems/<name>/ — HTML + extracted text per page
"""

import json
import sys
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DESIGN_SYSTEMS

SITES = [
    {"name": "vercel-geist", "url": "https://vercel.com/design", "max_pages": 50},
    {"name": "github-primer", "url": "https://primer.style", "max_pages": 30},
    {"name": "atlassian-design", "url": "https://atlassian.design", "max_pages": 30},
    {"name": "adobe-spectrum", "url": "https://spectrum.adobe.com", "max_pages": 30},
    {"name": "shopify-polaris", "url": "https://polaris.shopify.com", "max_pages": 30},
    {"name": "ibm-carbon", "url": "https://carbondesignsystem.com", "max_pages": 30},
    {"name": "microsoft-fluent2", "url": "https://developer.microsoft.com/en-us/fluentui", "max_pages": 30},
    {"name": "twilio-paste", "url": "https://paste.twilio.design", "max_pages": 20},
    {"name": "bbc-gel", "url": "https://bbc.github.io/gel", "max_pages": 20},
    {"name": "govuk", "url": "https://design-system.service.gov.uk", "max_pages": 20},
    {"name": "stackoverflow-stacks", "url": "https://stackoverflow.design", "max_pages": 20},
    {"name": "hashicorp-helios", "url": "https://helios.hashicorp.design", "max_pages": 20},
    {"name": "mozilla-protocol", "url": "https://protocol.mozilla.org", "max_pages": 20},
    {"name": "aws-cloudscape", "url": "https://cloudscape.design", "max_pages": 20},
]


def extract_content(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "lxml")
    for unwanted in soup.select("script, style, nav, footer, header, .sidebar"):
        unwanted.decompose()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if not main:
        return None

    text = main.get_text(separator="\n", strip=True)
    if len(text) < 100:
        return None

    code_blocks = []
    for pre in main.find_all("pre"):
        code = pre.get_text("\n", strip=True)
        if len(code) > 20:
            lang = ""
            code_cls = pre.find_previous("code")
            if code_cls and code_cls.get("class"):
                lang = code_cls["class"][0].replace("language-", "")
            code_blocks.append({"language": lang, "code": code})

    headings = []
    for h in main.find_all(["h1", "h2", "h3"]):
        headings.append(h.get_text(strip=True))

    return {
        "url": url,
        "title": soup.find("title").get_text(strip=True) if soup.find("title") else "",
        "headings": headings,
        "text_length": len(text),
        "text_sample": text[:3000],
        "code_blocks": code_blocks[:20],
    }


async def scrape_site(client: httpx.AsyncClient, site: dict) -> list[dict]:
    name = site["name"]
    base = site["url"]
    out_dir = DESIGN_SYSTEMS / name
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []

    print(f"[{name}] Fetching {base}")
    try:
        resp = await client.get(base, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"[{name}] Failed: {e}")
        return results

    content = extract_content(resp.text, base)
    if content:
        results.append(content)
        with open(out_dir / "index.json", "w") as f:
            json.dump(content, f, indent=2)

    soup = BeautifulSoup(resp.text, "lxml")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base, href)
        if full.startswith(base) and not any(
            skip in full for skip in [".pdf", ".zip", "#", "mailto:"]
        ):
            links.add(full)

    print(f"[{name}] Found {len(links)} internal links, scraping up to {site['max_pages']}")
    count = 0
    for link in sorted(links):
        if count >= site["max_pages"]:
            break
        try:
            resp = await client.get(link, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            content = extract_content(resp.text, link)
            if content:
                results.append(content)
                slug = link.replace(base, "").strip("/").replace("/", "-") or "index"
                with open(out_dir / f"{slug}.json", "w") as f:
                    json.dump(content, f, indent=2)
                count += 1
        except Exception as e:
            continue

    print(f"[{name}] Done — {count} pages")
    return results


async def main():
    import asyncio

    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(limits=limits, timeout=30) as client:
        all_results = []
        for site in SITES:
            results = await scrape_site(client, site)
            all_results.extend(results)

        manifest = {
            "collected_at": datetime.utcnow().isoformat(),
            "sites_count": len(SITES),
            "total_pages": len(all_results),
            "sites": [s["name"] for s in SITES],
        }
        with open(DESIGN_SYSTEMS / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

    print(f"\nDone. Collected {len(all_results)} pages across {len(SITES)} sites.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
